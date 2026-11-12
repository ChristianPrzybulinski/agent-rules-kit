#!/usr/bin/env python3
"""Advisory line and branch coverage of GDScript functions under gdUnit4 (KIT-034).

Usage: gd_coverage.py [--base REF] [--ref REF] [--tests RES_DIR]... [--exclude PATH]... [--timeout S]
                      [--json FILE] [--keep] [FILE...]

`git archive <ref>` (default HEAD) of the Godot project around the current directory goes into a new temporary
folder, with its Git LFS pointers filled from the local LFS store; the checkout is never edited. Every .gd file of the
copy outside addons/, .godot/, the test folders and each --exclude path is parsed with gdtoolkit (pinned 4.5.0) and
gets probes, inserted as text without a newline so every line number of the copy is the source's:
- `KitCov.hit(N); ` in front of the first simple statement of a run: a function body, a loop body, a `match` arm, and
  the statement after a compound statement, a `return`, `break`, `continue` or `await`;
- an `if`/`elif`/`while` condition C becomes `KitCov.b(N, C)`, which counts true in slot N and false in N + 1, and an
  `if`/`elif`/`else` arm or `while` body is entered from that count;
- a `for` iterable or `match` subject X outside a run becomes `(X if KitCov.t(N) else X)`, on the first argument of a
  `range(...)` call so the loop variable keeps its inferred type; a multi-line X leaves that line unmeasured.
Lambdas are not entered. The copy gains `kit_cov/kit_cov.gd` (class KitCov) and the autoload
`kit_cov/kit_cov_writer.gd`, which writes the counters of its process to $KIT_COV_OUT/hits-<pid>.json when the run
ends; the counters of every Godot process the tests start in the copy are added to the run's own. It is imported once
and the gdUnit4 suite runs headless under `nice -n 10`, with HOME and the XDG folders inside the temporary folder.
A test that copies an instrumented script into another project runs it there without KitCov: exclude that script.
Each Godot run is stopped, with every process it started, after --timeout seconds (default 1800).

A run counts when it finishes in time, exits 0 or 101 (orphans), its Overall Summary shows one test case or more and
its own counters were written; otherwise the tool says why and exits 2, as it does when godot, gdUnit4 or gdtoolkit
is missing or a ref is bad. stdout holds one `path:line function lines C/T branches C/T` line per function, stderr
the notices; --json FILE writes every reported function with its statements and branch outcomes. Without FILE or
--base every instrumented function is reported; with FILE those files; with --base REF the functions whose lines
changed in `git diff -U0 <REF>...HEAD`, read as complexity.py reads them. Exit 0 otherwise: the numbers are advisory.
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

from complexity import changed_lines  # one definition of a changed line for every advisory tool

try:
    from gdtoolkit.parser import parser as GD_PARSER
    from lark import Token, Tree
except ImportError:  # fail closed in main(): coverage needs the parser
    GD_PARSER = None

EXCLUDED = ("addons/", ".godot/", "kit_cov/")  # third-party plugins, the import cache, the probes themselves
SIMPLE = {"pass_stmt", "return_stmt", "func_var_stmt", "break_stmt", "breakpoint_stmt", "continue_stmt",
          "expr_stmt", "const_stmt"}
ENDS_RUN = {"return_stmt", "break_stmt", "continue_stmt"}
VAR_STMTS = {"class_var_stmt", "static_class_var_stmt"}
GDUNIT_TOOL = "addons/gdUnit4/bin/GdUnitCmdTool.gd"
TIMEOUT = 1800  # seconds for one Godot run
COUNTED_EXITS = (0, 101)  # gdUnit4: 0 passed, 101 passed with orphan nodes; 100 failures, 105 discovery errors
SUMMARY = re.compile(r"(\d+) test cases \| (\d+) errors \| (\d+) failures \| (\d+) flaky \| (\d+) skipped \| "
                     r"(\d+) orphans")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
LFS_POINTER = b"version https://git-lfs.github.com/spec/v1"
LFS_OID = re.compile(rb"^oid sha256:([0-9a-f]{64})$", re.M)
sys.setrecursionlimit(20000)  # deep expression trees

KIT_COV = """@tool
class_name KitCov
extends RefCounted
## Probe counters of a copy instrumented by ai-kit gd_coverage.py (KIT-034); never part of a source tree.

const SIZE := @SIZE@
static var hits := PackedInt64Array()


static func _static_init() -> void:
\thits.resize(SIZE)


## Counts the entry of a run of statements.
static func hit(slot: int) -> void:
\thits[slot] += 1


## Counts a `for` or `match` entry; always true, so `(x if KitCov.t(n) else x)` is x, typed as x.
static func t(slot: int) -> bool:
\thits[slot] += 1
\treturn true


## Counts a condition's outcome, true in slot and false in slot + 1, and returns the value unchanged.
static func b(slot: int, value: Variant) -> Variant:
\tif value:
\t\thits[slot] += 1
\telse:
\t\thits[slot + 1] += 1
\treturn value
"""

KIT_COV_WRITER = """extends Node
## Writes this process's KitCov counters to $KIT_COV_OUT/hits-<pid>.json once, when the run ends
## (ai-kit gd_coverage.py, KIT-034).

var _written := false


func _exit_tree() -> void:
\t_write("exit_tree")


func _notification(what: int) -> void:
\tif what == NOTIFICATION_PREDELETE:
\t\t_write("predelete")


func _write(reason: String) -> void:
\tif _written:
\t\treturn
\t_written = true
\tvar folder := OS.get_environment("KIT_COV_OUT")
\tif folder.is_empty():
\t\tpush_error("KitCov: KIT_COV_OUT is not set")
\t\treturn
\tvar path := folder.path_join("hits-%d.json" % OS.get_process_id())
\tvar file := FileAccess.open(path, FileAccess.WRITE)
\tif file == null:
\t\tpush_error("KitCov: cannot write %s: %s" % [path, error_string(FileAccess.get_open_error())])
\t\treturn
\tfile.store_string(JSON.stringify({"reason": reason, "hits": Array(KitCov.hits)}))
\tfile.close()
"""
AUTOLOAD = 'KitCovWriter="*res://kit_cov/kit_cov_writer.gd"'


@dataclass
class Statement:
    line: int
    end: int  # last line of the statement, or of the condition, iterable or subject of a compound one
    counter: Optional[Tuple[int, ...]]  # slots whose sum is how often it ran; None: not measured


@dataclass
class Branch:
    line: int
    kind: str  # if, elif, while, match
    outcome: str  # true or false; arm for a match arm
    counter: Optional[Tuple[int, ...]]


@dataclass
class Function:
    path: str
    name: str
    start: int
    end: int
    statements: list = field(default_factory=list)
    branches: list = field(default_factory=list)


def notice(text):
    print(f"gd_coverage: {text}", file=sys.stderr)


def start(node):
    """(line, column) where a token or tree starts, both 1-based."""
    if isinstance(node, Token):
        return node.line, node.column
    return node.meta.line, node.meta.column


def end(node):
    """(line, column) right after a token or tree; a tree's span holds the brackets the parser drops."""
    if isinstance(node, Token):
        return node.end_line, node.end_column
    if getattr(node.meta, "end_column", None) is not None:
        return node.meta.end_line, node.meta.end_column
    last = max(node.scan_values(lambda v: isinstance(v, Token)), key=lambda t: (t.end_line, t.end_column))
    return last.end_line, last.end_column


def last_line(node):
    """Line of the last token; a tree's own end runs past trailing blank lines."""
    lines = [t.end_line for t in node.scan_values(lambda v: isinstance(v, Token))]
    return max(lines) if lines else node.meta.end_line


def awaits(node):
    """Whether a statement awaits outside a lambda: the code after it may never resume."""
    stack = [node]
    while stack:
        item = stack.pop()
        if isinstance(item, Tree):
            if item.data == "await_expr":
                return True
            if item.data != "lambda":
                stack.extend(item.children)
    return False


def range_argument(expr):
    """First argument of `range(...)` when expr is that call: wrapping the call itself loses its int inference."""
    call = expr.children[0] if len(expr.children) == 1 else None
    if isinstance(call, Tree) and call.data == "standalone_call" and len(call.children) > 1 \
            and isinstance(call.children[0], Token) and call.children[0] == "range":
        return call.children[1]
    return None


class Instrumenter:
    """Probes of one source. Slots start at first_slot, so one KitCov array serves every file of a run."""

    def __init__(self, text, path, first_slot=0):
        self.source = text.split("\n")
        self.path = path
        self.next_slot = first_slot
        self.edits = {}  # line: [(index, closing first, order, text)]
        self.order = 0
        self.functions = []
        self.probes = {"hit": 0, "b": 0, "t": 0, "unmeasured": 0}
        self.function = None

    def slot(self, count=1):
        first = self.next_slot
        self.next_slot += count
        return first

    def insert(self, line, column, text, closing=False):
        self.order += 1
        self.edits.setdefault(line, []).append((column - 1, 0 if closing else 1, self.order, text))

    def text(self):
        out = []
        for number, line in enumerate(self.source, 1):
            pieces, last = [], 0
            for index, _, _, text in sorted(self.edits.get(number, ())):
                pieces += [line[last:index], text]
                last = index
            out.append("".join(pieces) + line[last:])
        return "\n".join(out)

    def record(self, line, last, counter):
        self.function.statements.append(Statement(line, last, counter))

    def walk_class(self, statements, prefix=""):
        previous = None
        for node in statements:
            if not isinstance(node, Tree):
                continue
            if node.data in ("func_def", "static_func_def"):
                func = node.children[0] if node.data == "static_func_def" and node.children[0].data == "func_def" \
                    else node
                self.add_function(prefix + str(func.children[0].children[0]), node, func.children[1:])
            elif node.data == "class_def":
                self.walk_class(node.children[1:], f"{prefix}{node.children[0]}.")
            elif node.data == "property_body_def" and previous is not None and previous.data in VAR_STMTS:
                var = prefix + next(previous.scan_values(lambda v: isinstance(v, Token) and v.type == "NAME"))
                for accessor in node.children:
                    if isinstance(accessor, Tree) and accessor.data in ("property_custom_getter",
                                                                        "property_custom_setter"):
                        body = [c for c in accessor.children if isinstance(c, Tree)
                                and c.data != "property_custom_getter_args"]
                        self.add_function(f"{var}.{accessor.data.rsplit('_', 1)[1][:3]}", accessor, body)
            previous = node

    def add_function(self, name, node, body):
        self.function = Function(self.path, name, node.meta.line, last_line(node))
        self.block(body, None)
        self.function.end = max([self.function.end] + [s.end for s in self.function.statements])
        self.functions.append(self.function)

    def block(self, statements, current):
        """Instrument one block entered with counter `current` (None: a new run); return its first entry counter."""
        entry, first, lead = None, True, None
        for node in statements:
            if not isinstance(node, Tree):
                continue
            if node.data == "annotation":
                lead = node
                continue
            if node.data in SIMPLE:
                if current is None and lead is None:
                    current = (self.slot(),)
                    self.insert(*start(node), f"KitCov.hit({current[0]}); ")
                    self.probes["hit"] += 1
                counter = current
                if current is None:  # a probe in front of an annotation does not parse, after it takes the annotation
                    self.probes["unmeasured"] += 1
                self.record(node.meta.line, last_line(node), counter)
                if node.data in ENDS_RUN or awaits(node):
                    current = None
            elif node.data == "if_stmt":
                counter, current = self.if_stmt(node), None
            elif node.data == "while_stmt":
                n = self.condition(node.children[0], "while", node.meta.line)
                self.block(node.children[1:], (n,))
                counter, current = (n, n + 1), None  # evaluations, not entries: > 0 whenever it was reached
            elif node.data in ("for_stmt", "for_stmt_typed"):
                index = next(i for i, c in enumerate(node.children) if isinstance(c, Tree) and c.data == "expr")
                counter = self.entry(node, node.children[index], current)
                self.block(node.children[index + 1:], None)
                current = None
            elif node.data == "match_stmt":
                counter = self.entry(node, node.children[0], current)
                for arm in node.children[1:]:
                    if isinstance(arm, Tree):
                        body = arm.children[2:] if arm.data == "guarded_match_branch" else arm.children[1:]
                        self.function.branches.append(Branch(arm.meta.line, "match", "arm", self.block(body, None)))
                current = None
            else:
                lead = None
                continue
            if first:
                entry, first = counter, False
            lead = None
        return entry

    def if_stmt(self, node):
        entry, false = None, None
        for arm in node.children:
            if not isinstance(arm, Tree):
                continue
            if arm.data == "else_branch":
                self.block(arm.children, (false,))
                continue
            n = self.condition(arm.children[0], arm.data[:-len("_branch")], arm.meta.line)
            self.block(arm.children[1:], (n,))
            entry, false = entry or (n, n + 1), n + 1
        return entry

    def condition(self, expr, kind, line):
        n = self.slot(2)
        self.insert(*start(expr), f"KitCov.b({n}, ")
        self.insert(*end(expr), ")", closing=True)
        self.probes["b"] += 1
        self.record(line, end(expr)[0], (n, n + 1))
        self.function.branches += [Branch(line, kind, "true", (n,)), Branch(line, kind, "false", (n + 1,))]
        return n

    def entry(self, node, subject, current):
        """Counter of a `for` or `match` line: the run it is in, else a probe on its iterable or subject."""
        line, last = node.meta.line, end(subject)[0]
        if current is None:
            target = range_argument(subject) or subject
            (line0, column0), (line1, column1) = start(target), end(target)
            if line0 != line1:  # copying it would add lines
                self.probes["unmeasured"] += 1
                self.record(line, last, None)
                return None
            n = self.slot()
            text = self.source[line0 - 1][column0 - 1:column1 - 1]
            self.insert(line0, column0, "(")
            self.insert(line1, column1, f" if KitCov.t({n}) else {text})", closing=True)
            self.probes["t"] += 1
            current = (n,)
        self.record(line, last, current)
        return current


def instrument(text, path, first_slot=0):
    """Instrumenter of one source with its output in `.output`; raises when the source or the output does not parse."""
    probes = Instrumenter(text, path, first_slot)
    probes.walk_class(GD_PARSER.parse(text, gather_metadata=True).children)
    probes.output = probes.text()
    if probes.output.count("\n") != text.count("\n"):
        raise ValueError("instrumentation changed the line count")
    GD_PARSER.parse(probes.output)
    return probes


def report(function, hits):
    """Coverage of one function from the slot counts of a run."""
    def count(counter):
        return None if counter is None else sum(hits[s] for s in counter)

    covered, unmeasured, statements, outcomes = {}, set(), [], []
    for statement in function.statements:
        n = count(statement.counter)
        statements.append({"line": statement.line, "end": statement.end, "hits": n})
        if n is None:
            unmeasured.add(statement.line)
        else:
            covered[statement.line] = covered.get(statement.line, False) or n > 0
    for branch in function.branches:
        outcomes.append({"line": branch.line, "kind": branch.kind, "outcome": branch.outcome,
                         "hits": count(branch.counter)})
    measured = [o["hits"] for o in outcomes if o["hits"] is not None]
    return {"path": function.path, "name": function.name, "start": function.start, "end": function.end,
            "lines": {"covered": sum(covered.values()), "total": len(covered)},
            "branches": {"covered": sum(1 for n in measured if n), "total": len(measured)},
            "uncovered_lines": sorted(n for n, hit in covered.items() if not hit),
            "unmeasured_lines": sorted(unmeasured - covered.keys()),
            "statements": statements, "outcomes": outcomes}


def add_autoload(text):
    """project.godot text with the writer as the first autoload: it leaves the tree last, after the others ran."""
    lines = text.splitlines()
    header = next((i for i, line in enumerate(lines) if line.strip() == "[autoload]"), None)
    if header is None:
        lines += ["", "[autoload]", "", AUTOLOAD]
    else:
        lines.insert(header + 1, AUTOLOAD)
    return "\n".join(lines) + "\n"


def test_summary(output):
    """Counts of gdUnit4's last Overall Summary, or None when the run printed none."""
    parts = ANSI.sub("", output).rsplit("Overall Summary:", 1)
    match = SUMMARY.search(parts[1]) if len(parts) == 2 else None
    keys = ("cases", "errors", "failures", "flaky", "skipped", "orphans")
    return dict(zip(keys, map(int, match.groups()))) if match else None


def git_out(*args):
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode:
        notice(f"git {args[0]} failed: {result.stderr.strip()}")
        sys.exit(2)
    return result.stdout.strip()


def find_project(folder):
    for candidate in (folder, *folder.parents):
        if (candidate / "project.godot").is_file():
            return candidate
    return None


def extract(sha, prefix, copy):
    """git archive of the project at sha into copy, its LFS pointers filled from the local store; (filled, missing)."""
    archive = subprocess.Popen(["git", "archive", "--format=tar", f"{sha}:{prefix}" if prefix else sha],
                               stdout=subprocess.PIPE)
    untar = subprocess.run(["tar", "-x", "-f", "-", "-C", str(copy)], stdin=archive.stdout, check=False)
    archive.stdout.close()
    if archive.wait() or untar.returncode:
        notice(f"git archive of {sha} failed")
        sys.exit(2)
    store = Path(git_out("rev-parse", "--path-format=absolute", "--git-common-dir"), "lfs", "objects")
    filled = missing = 0
    for path in copy.rglob("*"):
        if not path.is_file() or path.stat().st_size > 1024:
            continue
        data = path.read_bytes()
        match = LFS_OID.search(data) if data.startswith(LFS_POINTER) else None
        if match:
            oid = match.group(1).decode()
            source = store / oid[:2] / oid[2:4] / oid
            if source.is_file():
                shutil.copyfile(source, path)
                filled += 1
            else:
                missing += 1
    return filled, missing


def run_godot(godot, args, env, log, timeout):
    """(exit code or None when stopped at the timeout, output, seconds, pid) of one Godot run at low priority.

    The run gets its own process group, so the timeout also stops the Godot processes its tests started; `nice` execs
    Godot, so pid is Godot's own. The output goes to the log too."""
    nice = shutil.which("nice")
    command = ([nice, "-n", "10"] if nice else []) + [godot, *args]
    began = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
                               start_new_session=True)
    try:
        data, _ = process.communicate(timeout=timeout)
        code = process.returncode
    except subprocess.TimeoutExpired:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        data, _ = process.communicate()
        code = None
    output = data.decode("utf-8", "replace")
    with open(log, "a", encoding="utf-8") as out:
        out.write("$ " + " ".join(command) + "\n" + output)
    return code, output, time.monotonic() - began, process.pid


def scratch_env(scratch):
    home = scratch / "home"
    folders = {"HOME": home, "XDG_DATA_HOME": home / ".local" / "share", "XDG_CONFIG_HOME": home / ".config",
               "XDG_CACHE_HOME": home / ".cache"}
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    (scratch / "hits").mkdir(exist_ok=True)
    return {**os.environ, **{k: str(v) for k, v in folders.items()}, "KIT_COV_OUT": str(scratch / "hits")}


def load_hits(path, slots):
    try:
        hits = [int(n) for n in json.loads(path.read_text(encoding="utf-8"))["hits"]]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return hits if len(hits) >= slots else None


def read_hits(folder, pid, slots):
    """(counters of the run plus those of every Godot process it started, how many others), or (None, 0) when the
    run's own were not written: another process's file never stands in for them."""
    total = load_hits(folder / f"hits-{pid}.json", slots)
    if total is None:
        return None, 0
    others = [load_hits(p, slots) for p in sorted(folder.glob("hits-*.json")) if p.name != f"hits-{pid}.json"]
    others = [h for h in others if h is not None and len(h) == len(total)]
    for hits in others:
        total = [a + b for a, b in zip(total, hits)]
    return total, len(others)


def excluded(rel, paths):
    return any(rel == p or rel.startswith(p.rstrip("/") + "/") for p in paths)


def parse_errors(output):
    """Godot's script errors that name a file, one line each: an instrumented file that does not compile shows here."""
    lines = ANSI.sub("", output).splitlines()
    found = []
    for index, line in enumerate(lines):
        if "Parse Error" in line or "Compile Error" in line:
            where = lines[index + 1].strip() if index + 1 < len(lines) else ""
            found.append(f"{line.strip()} {where}".strip())
    return found


def measure(args, prefix, sha, wanted, godot, scratch):
    copy = scratch / "project"
    copy.mkdir()
    filled, missing = extract(sha, prefix, copy)
    if missing:
        notice(f"{missing} LFS object(s) are not in the local store and stay pointers (git lfs fetch)")
    if not (copy / GDUNIT_TOOL).is_file():
        notice(f"{GDUNIT_TOOL} is not in the project at {sha[:12]}; coverage not measured")
        return 2
    tests = args.tests or ["res://tests"]
    skipped = EXCLUDED + tuple(t[len("res://"):].strip("/") + "/" for t in tests)
    every = [p for p in sorted(q.relative_to(copy).as_posix() for q in copy.rglob("*.gd")) if not p.startswith(skipped)]
    exclude = [os.path.normpath(e[len("res://"):] if e.startswith("res://") else e) for e in args.exclude]
    sources = [p for p in every if not excluded(p, exclude)]
    left_out = [f"{prefix}/{p}" if prefix else p for p in every if excluded(p, exclude)]
    began, functions, failed, slots = time.monotonic(), [], [], 0
    probes = {"hit": 0, "b": 0, "t": 0, "unmeasured": 0}
    for rel in sources:
        path, shown = copy / rel, f"{prefix}/{rel}" if prefix else rel
        try:
            done = instrument(path.read_text(encoding="utf-8"), shown, slots)
        except Exception as error:  # a file gdtoolkit cannot parse runs uninstrumented, named
            failed.append(f"{shown}: {type(error).__name__}")
            continue
        path.write_text(done.output, encoding="utf-8")
        slots, functions = done.next_slot, functions + done.functions
        probes = {k: probes[k] + done.probes[k] for k in probes}
    instrument_seconds = time.monotonic() - began
    (copy / "kit_cov").mkdir()
    (copy / "kit_cov" / "kit_cov.gd").write_text(KIT_COV.replace("@SIZE@", str(max(slots, 1))), encoding="utf-8")
    (copy / "kit_cov" / "kit_cov_writer.gd").write_text(KIT_COV_WRITER, encoding="utf-8")
    project = copy / "project.godot"
    project.write_text(add_autoload(project.read_text(encoding="utf-8")), encoding="utf-8")
    for text in failed[:3]:
        notice(f"not instrumented: {text}")
    env, log = scratch_env(scratch), scratch / "godot.log"
    version = subprocess.run([godot, "--version"], capture_output=True, text=True, env=env, check=False).stdout.strip()
    code, output, import_seconds, _ = run_godot(godot, ["--path", str(copy), "--headless", "--import"], env, log,
                                                args.timeout)
    errors = parse_errors(output)
    if code is None:
        notice(f"coverage not counted: the import did not finish in {args.timeout} s")
        return 2
    if code:
        notice(f"import exited {code}")
    command = ["--path", str(copy), "--headless", "-s", GDUNIT_TOOL]
    command += [arg for t in tests for arg in ("-a", t)] + ["-c", "--ignoreHeadlessMode"]
    code, output, test_seconds, pid = run_godot(godot, command, env, log, args.timeout)
    errors += parse_errors(output)
    for text in errors[:3]:
        notice(f"godot: {text}")
    summary = test_summary(output)
    hits, others = read_hits(scratch / "hits", pid, slots)
    why = None
    if code is None:
        why = (f"the suite did not finish in {args.timeout} s (a test that runs a copy of an instrumented script "
               "outside the copy waits on it: --exclude that script)")
    elif code not in COUNTED_EXITS:
        why = f"the suite exited {code}"
    elif summary is None or summary["cases"] < 1:
        why = "no test case ran"
    elif hits is None:
        why = f"the counters were not written to {scratch / 'hits' / f'hits-{pid}.json'}"
    if why:
        notice(f"coverage not counted: {why}; last lines of the log:")
        for line in ANSI.sub("", output).splitlines()[-15:]:
            print(f"  {line}", file=sys.stderr)
        return 2
    reports = [report(f, hits) for f in functions if wanted is None or (
        f.path in wanted and (wanted[f.path] is None or any(f.start <= n <= f.end for n in wanted[f.path])))]
    for item in reports:
        print(f"{item['path']}:{item['start']} {item['name']} lines {item['lines']['covered']}/"
              f"{item['lines']['total']} branches {item['branches']['covered']}/{item['branches']['total']}")
    if wanted is not None:
        instrumented = {f.path for f in functions}
        for path in sorted(p for p in wanted if p.endswith(".gd") and p not in instrumented):
            notice(f"{path} is not instrumented (a test, an addon, excluded, not in {sha[:12]} or not parsed)")
    totals = {k: [sum(r[k]["covered"] for r in reports), sum(r[k]["total"] for r in reports)]
              for k in ("lines", "branches")}
    notice(f"{len(reports)} function(s): lines {totals['lines'][0]}/{totals['lines'][1]}, branches "
           f"{totals['branches'][0]}/{totals['branches'][1]}; {summary['cases']} test case(s) in {test_seconds:.1f} s "
           f"(exit {code}); {len(sources) - len(failed)} file(s) instrumented in {instrument_seconds:.1f} s, "
           f"{len(failed)} not, {len(left_out)} excluded; import {import_seconds:.1f} s; counters of {others} "
           "other Godot process(es) added")
    if args.json:
        data = {"tool": "gd_coverage", "version": 1, "ref": sha, "project": prefix or ".", "godot": version,
                "tests": {**summary, "exit": code, "seconds": round(test_seconds, 1), "other_processes": others},
                "seconds": {"instrument": round(instrument_seconds, 1), "import": round(import_seconds, 1)},
                "files": {"instrumented": len(sources) - len(failed), "failed": failed, "excluded": left_out},
                "lfs": {"filled": filled, "missing": missing}, "probes": probes, "slots": slots,
                "functions": reports}
        Path(args.json).write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Advisory line and branch coverage of GDScript functions under gdUnit4")
    ap.add_argument("files", nargs="*", help="report every function of these files")
    ap.add_argument("--base", help="report the functions whose lines changed in REF...HEAD")
    ap.add_argument("--ref", default="HEAD", help="commit whose tree is measured (default HEAD)")
    ap.add_argument("--tests", action="append", help="gdUnit4 test folder, repeatable (default res://tests)")
    ap.add_argument("--exclude", action="append", default=[],
                    help="project path of a .gd file or folder left without probes, repeatable")
    ap.add_argument("--timeout", type=int, default=TIMEOUT, help=f"seconds for one Godot run (default {TIMEOUT})")
    ap.add_argument("--json", help="write the full report to this file")
    ap.add_argument("--keep", action="store_true", help="keep the temporary copy, its log and counters")
    args = ap.parse_args()
    files = [os.path.realpath(p) for p in args.files]
    args.json = os.path.abspath(args.json) if args.json else None
    project = find_project(Path.cwd())
    if project is None:
        notice("no project.godot in the current directory or above")
        return 2
    os.chdir(project)
    top = Path(git_out("rev-parse", "--show-toplevel")).resolve()
    prefix = project.resolve().relative_to(top).as_posix()
    prefix = "" if prefix == "." else prefix
    os.chdir(top)
    sha = git_out("rev-parse", "--verify", f"{args.ref}^{{commit}}")
    wanted = None
    if files:
        wanted = {os.path.relpath(p, top): None for p in files}
    elif args.base:
        wanted = {p: n for p, n in changed_lines(args.base).items() if p.endswith(".gd")}
        if not wanted:
            notice("no changed .gd function to measure")
            return 0
    if GD_PARSER is None:
        notice("gdtoolkit not available (pip install gdtoolkit==4.5.0); coverage not measured")
        return 2
    godot = os.environ.get("GODOT") or shutil.which("godot")
    if not godot:
        notice("godot not found (set GODOT or put it on PATH); coverage not measured")
        return 2
    scratch = Path(tempfile.mkdtemp(prefix="gd-coverage-"))
    try:
        return measure(args, prefix, sha, wanted, godot, scratch)
    finally:
        if args.keep:
            notice(f"kept {scratch}")
        else:
            shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
