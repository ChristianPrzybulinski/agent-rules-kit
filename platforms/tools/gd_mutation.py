#!/usr/bin/env python3
"""Advisory mutation testing of GDScript functions under gdUnit4, with PIT's default operators (KIT-035).

Usage: gd_mutation.py [--base REF] [--ref REF] [--coverage JSON] [--tests RES_DIR]... [--workers N]
                      [--timeout S] [--timeout-constant S] [--json FILE] [--keep] [FILE...]

`git archive <ref>` (default HEAD) of the Godot project around the current directory goes into a new temporary
folder, as gd_coverage.py makes it; the checkout is never edited. Each asked .gd file of the copy outside addons/,
.godot/ and the test folders is parsed with gdtoolkit (pinned 4.5.0). In a function body (lambdas, match patterns,
annotations and `const` statements are left alone) each place one of PIT 1.30.0's default operators applies gives
one mutant, one text edit placed from the tree's line and column:
- CONDITIONALS_BOUNDARY `<` <-> `<=`, `>` <-> `>=`;
- NEGATE_CONDITIONALS `==` <-> `!=`, `<` -> `>=`, `<=` -> `>`, `>` -> `<=`, `>=` -> `<`, `in` <-> `not in`,
  `is` <-> `is not`, `not`/`!` removed, and `not (C)` around a condition C of an if/elif/while, a match guard or a
  ternary, or around an operand of its and/or, that is not already a comparison or a not, in or is test;
- MATH `+` <-> `-`, `*` <-> `/`, `%` -> `*`, `&` <-> `|`, `^` -> `&`, `<<` <-> `>>`; INCREMENTS `+=` <-> `-=`;
- INVERT_NEGS `-x` -> `x`, not on a number; VOID_METHOD_CALLS a call standing alone as a statement -> `pass`, not
  on print*, push_error, push_warning or assert (PIT leaves logging calls alone);
- the returned expression -> `true` and `false` (TRUE_RETURNS, FALSE_RETURNS) in `-> bool`, `0` or `0.0`
  (PRIMITIVE_RETURNS) in `-> int` or `-> float`, `""`, `&""`, `[]`, `{}` or `PackedXArray()` (EMPTY_RETURNS) for
  those types, and `null` (NULL_RETURNS) with no return type, Variant or a class, never a value type or an enum;
  never the value it already returns. A getter returns its variable's type; a setter and `-> void` return nothing.
A mutant keeps every line number (a removed line break comes back as a blank line) and parses again, or it is
dropped.

Which functions: with FILE every function of those files; otherwise those whose lines changed in
`git diff -U0 <base>...HEAD` (--base, default origin/main), read as complexity.py reads them, and --ref must then
be HEAD. With --coverage JSON (gd_coverage.py --json of the same ref and project) a mutant on a line the report
counts as never run is listed as "no coverage" without a run; a line the report does not measure runs.

Which tests: the gdUnit4 suites under the --tests folders (default res://tests) that name the mutated file's
class_name or its res:// path; a file with none lists its mutants as "no tests". The copy is imported once
(`--import`, under --timeout, default 1800 s); each of --workers N (default 1) gets its own APFS clone (`cp -cR`)
and HOME. Each selection runs once unmutated: it must exit 0 or 101 with one test case or more, or its mutants are
"not run" and the tool exits 2. A mutant is written into its worker's clone, run with the project's gdUnit4 command
(one `-a` per suite, headless, `nice -n 10`, stopped with every process it started after 10 x the selection's
unmutated time plus --timeout-constant, default 30 s) and restored. Its status: timed out; invalid (exit 105, or a
parse or compile error that names the mutated file); killed (exit 100); survived (exit 0 or 101 with one test case
or more); error (anything else); not run when writing or running it raised (godot gone, a full disk), and a worker
that cannot restore its file stops. The score is killed plus timed out over killed, timed out and survived.

stdout holds one survivor per line, `path:line function OPERATOR from → to`; stderr the "no coverage" lines, the
counts, the score and the notices; --json FILE writes every mutant with its status, the unmutated runs and the
score. Exit 0 (advisory); 2 when godot, gdUnit4 or gdtoolkit is missing, a ref or the coverage report is bad, the
import does not finish, an unmutated run fails or a mutant is not run.
"""
import argparse
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import gd_coverage
from complexity import changed_lines
from gd_coverage import (COUNTED_EXITS, EXCLUDED, GD_PARSER, GDUNIT_TOOL, TIMEOUT, end, extract, find_project,
                         git_out, last_line, parse_errors, run_godot, scratch_env, start, test_summary)

try:
    from lark import Token, Tree
except ImportError:  # main() exits 2 before any parse
    Token = Tree = None

NEGATE = {"==": "!=", "!=": "==", "<": ">=", "<=": ">", ">": "<=", ">=": "<",
          "in": "not in", "not in": "in", "is": "is not", "is not": "is"}
BOUNDARY = {"<": "<=", "<=": "<", ">": ">=", ">=": ">"}
MATH = {"+": "-", "-": "+", "*": "/", "/": "*", "%": "*", "&": "|", "|": "&", "^": "&", "<<": ">>", ">>": "<<"}
INCREMENTS = {"+=": "-=", "-=": "+="}
BINARY = {"comparison", "content_test", "type_test", "arith_expr", "mdr_expr", "shift_expr", "bitw_and", "bitw_or",
          "bitw_xor"}
TESTS = {"comparison", "content_test", "type_test", "not_test"}  # a condition these already negate
SKIPPED = {"lambda", "pattern", "annotation", "const_stmt"}
NUMBERS = {"NUMBER", "HEX", "BIN"}
LOGGING = {"print", "printerr", "prints", "printt", "printraw", "print_rich", "print_debug", "print_verbose",
           "push_error", "push_warning", "assert"}
PACKED = {"PackedByteArray", "PackedInt32Array", "PackedInt64Array", "PackedFloat32Array", "PackedFloat64Array",
          "PackedStringArray", "PackedVector2Array", "PackedVector3Array", "PackedVector4Array", "PackedColorArray"}
VALUE_TYPES = PACKED | {"void", "bool", "int", "float", "String", "StringName", "NodePath", "Vector2", "Vector2i",
                        "Vector3", "Vector3i", "Vector4", "Vector4i", "Rect2", "Rect2i", "Transform2D", "Transform3D",
                        "Plane", "Quaternion", "AABB", "Basis", "Projection", "Color", "RID", "Callable", "Signal",
                        "Array", "Dictionary"}
GLOBAL_ENUMS = {"Side", "Corner", "Orientation", "ClockDirection", "HorizontalAlignment", "VerticalAlignment",
                "InlineAlignment", "EulerOrder", "Key", "KeyModifierMask", "KeyLocation", "MouseButton",
                "MouseButtonMask", "JoyButton", "JoyAxis", "MIDIMessage", "Error", "PropertyHint",
                "PropertyUsageFlags", "MethodFlags"}
CLASS_NAME = re.compile(r"^\s*class_name\s+(\w+)", re.M)
INNER_CLASS = re.compile(r"^\s*class\s+(\w+)", re.M)
ENUM = re.compile(r"^\s*enum\s+(\w+)", re.M)
STATUSES = ("killed", "survived", "timed out", "invalid", "error", "no coverage", "no tests", "not run")
SHOWN = 80  # characters of a mutant's from/to text
# A mutant's run is stopped after TIMEOUT_FACTOR x its selection's unmutated time plus --timeout-constant seconds,
# PIT's shape (round(time x timeoutFactor) + timeoutConstant): a Godot start slowed by host load or by workers
# starting together is not proportional to the run's time, and a run stopped too early counts as detected.
TIMEOUT_FACTOR = 10
TIMEOUT_CONSTANT = 30


def notice(text):
    print(f"gd_mutation: {text}", file=sys.stderr)


def read(path):
    with open(path, encoding="utf-8", newline="") as source:
        return source.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as target:
        target.write(text)


def shown(text):
    text = " ".join(text.split())
    return text if len(text) <= SHOWN else text[:SHOWN - 1] + "…"


@dataclass
class Types:
    classes: set
    enums: set


@dataclass
class Mutant:
    path: str  # from the Git top level, as complexity.py and gd_coverage.py name it
    rel: str  # inside the project
    function: str
    line: int
    column: int
    operator: str
    before: str
    after: str
    start: int  # offsets of the edit in the source
    stop: int
    text: str
    status: str = ""
    exit: Optional[int] = None
    seconds: Optional[float] = None
    tests: List[str] = field(default_factory=list)

    def apply(self, source):
        return source[:self.start] + self.text + source[self.stop:]

    def report(self):
        return {"path": self.path, "line": self.line, "column": self.column, "function": self.function,
                "operator": self.operator, "from": self.before, "to": self.after, "status": self.status,
                "exit": self.exit, "seconds": self.seconds, "tests": self.tests}


def kind(node):
    return node.data.replace("asless_", "").replace("actual_", "") if isinstance(node, Tree) else None


def unwrap(node):
    """The expression inside an `expr` tree, which only wraps one."""
    while isinstance(node, Tree) and node.data == "expr" and len(node.children) == 1:
        node = node.children[0]
    return node


def return_values(returns, types):
    """[(operator, value)] a `return` of a function of this return type may become; None: no return mutant."""
    if returns is None or returns == "void":
        return []
    base = returns.split("[", 1)[0]
    if returns == "bool":
        return [("TRUE_RETURNS", "true"), ("FALSE_RETURNS", "false")]
    if returns in ("int", "float"):
        return [("PRIMITIVE_RETURNS", "0" if returns == "int" else "0.0")]
    if returns == "String":
        return [("EMPTY_RETURNS", '""')]
    if returns == "StringName":
        return [("EMPTY_RETURNS", '&""')]
    if base in ("Array", "Dictionary"):
        return [("EMPTY_RETURNS", "[]" if base == "Array" else "{}")]
    if returns in PACKED:
        return [("EMPTY_RETURNS", f"{returns}()")]
    if returns in VALUE_TYPES or returns in GLOBAL_ENUMS or returns in types.enums:
        return []
    if "." in returns and returns.rsplit(".", 1)[1] not in types.classes:
        return []  # an enum of a class, such as Node.ProcessMode
    return [("NULL_RETURNS", "null")]


def same_value(text, value):
    text = "".join(text.split())
    if value in ("0", "0.0"):
        try:
            return float(text.replace("_", "")) == 0
        except ValueError:
            return False
    if value in ('""', '&""'):
        return text in (value, value.replace('"', "'"))
    return text == value


class Generator:
    """Mutants of one source, in tree order, with the (name, first line, last line) of each function."""

    def __init__(self, text, path, rel, types):
        self.text, self.path, self.rel, self.types = text, path, rel, types
        self.line_starts = [0] + [i + 1 for i, c in enumerate(text) if c == "\n"]
        self.mutants, self.functions = [], []
        self.function, self.returns = None, None

    def offset(self, position):
        line, column = position
        return self.line_starts[line - 1] + column - 1

    def span(self, node):
        return self.offset(start(node)), self.offset(end(node))

    def add(self, operator, node, first, stop, text, before, after):
        line, column = start(node)
        text += "\n" * max(self.text.count("\n", first, stop) - text.count("\n"), 0)
        self.mutants.append(Mutant(self.path, self.rel, self.function, line, column, operator, shown(before),
                                   shown(after), first, stop, text))

    def walk_class(self, statements, prefix=""):
        """Functions named as gd_coverage.py names them: Inner.f, var.get, var.set."""
        previous = None
        for node in statements:
            if not isinstance(node, Tree):
                continue
            if node.data in ("func_def", "static_func_def"):
                func = node.children[0] if node.data == "static_func_def" and node.children[0].data == "func_def" \
                    else node
                header = func.children[0]
                hint = next((c for c in header.children if isinstance(c, Token) and c.type == "TYPE_HINT"), None)
                self.add_function(prefix + str(header.children[0]), node, func.children[1:],
                                  "".join(str(hint).split()) if hint is not None else "Variant")
            elif node.data == "class_def":
                self.walk_class(node.children[1:], f"{prefix}{node.children[0]}.")
            elif node.data == "property_body_def" and previous is not None and \
                    previous.data in gd_coverage.VAR_STMTS:
                var = prefix + next(previous.scan_values(lambda v: isinstance(v, Token) and v.type == "NAME"))
                for accessor in node.children:
                    if isinstance(accessor, Tree) and accessor.data in ("property_custom_getter",
                                                                        "property_custom_setter"):
                        body = [c for c in accessor.children if isinstance(c, Tree)
                                and c.data != "property_custom_getter_args"]
                        getter = accessor.data == "property_custom_getter"
                        self.add_function(f"{var}.{'get' if getter else 'set'}", accessor, body,
                                          self.var_type(previous) if getter else "void")
            previous = node

    @staticmethod
    def var_type(statement):
        """A variable's declared type, Variant when untyped, None when inferred (`:=`): unknown to the parser."""
        declared = next(statement.find_pred(lambda t: t.data.startswith("class_var_") and t.data != "class_var_stmt"))
        if declared.data == "class_var_inf":
            return None
        hint = next((c for c in declared.children if isinstance(c, Token) and c.type == "TYPE_HINT"), None)
        return "".join(str(hint).split()) if hint is not None else "Variant"

    def add_function(self, name, node, body, returns):
        self.function, self.returns = name, returns
        self.functions.append((name, node.meta.line, last_line(node)))
        for statement in body:
            self.visit(statement)

    def visit(self, node):
        if not isinstance(node, Tree) or node.data in SKIPPED:
            return
        name = kind(node)
        if name in BINARY:
            self.binary(node)
        elif name in ("if_branch", "elif_branch", "while_stmt"):
            self.condition(node.children[0])
        elif name == "guarded_match_branch":
            self.condition(node.children[1])
        elif name == "test_expr" and len(node.children) == 5:
            self.condition(node.children[2])
        else:
            handler = getattr(self, f"on_{name}", None)
            if handler:
                handler(node)
        for child in node.children:
            self.visit(child)

    def binary(self, node):
        children = node.children
        for index in range(1, len(children) - 1, 2):
            op, left, right = children[index], children[index - 1], children[index + 1]
            first, stop = self.span(op)
            value = " ".join(self.text[first:stop].split())
            whole = self.text[self.offset(start(left)):self.offset(end(right))]
            cut = first - self.offset(start(left)), stop - self.offset(start(left))
            mutations = [("NEGATE_CONDITIONALS", NEGATE.get(value)), ("CONDITIONALS_BOUNDARY", BOUNDARY.get(value))]
            if kind(node) not in ("comparison", "content_test", "type_test"):
                mutations = [("MATH", MATH.get(value))]
            for operator, new in mutations:
                if new:
                    self.add(operator, op, first, stop, new, whole, whole[:cut[0]] + new + whole[cut[1]:])

    def condition(self, node):
        """`not (C)` around a condition C that is not already a test; through and/or and parentheses."""
        node = unwrap(node)
        name = kind(node)
        if name in ("and_test", "or_test"):
            for operand in node.children[0::2]:
                self.condition(operand)
        elif name == "par_expr":
            self.condition(node.children[0])
        elif name not in TESTS and not (isinstance(node, Token) and str(node) in ("true", "false")):
            first, stop = self.span(node)
            original = self.text[first:stop]
            self.add("NEGATE_CONDITIONALS", node, first, stop, f"not ({original})", original, f"not ({original})")

    def on_not_test(self, node):
        token, operand = node.children
        first, stop = self.offset(start(token)), self.offset(start(operand))
        whole = self.text[first:self.offset(end(operand))]
        self.add("NEGATE_CONDITIONALS", token, first, stop, "", whole, whole[stop - first:])

    def on_neg_expr(self, node):
        token, operand = node.children
        if isinstance(operand, Token) and operand.type in NUMBERS:
            return  # `- 1` is a constant, as PIT finds no negation to invert in one
        first, stop = self.offset(start(token)), self.offset(start(operand))
        whole = self.text[first:self.offset(end(operand))]
        self.add("INVERT_NEGS", token, first, stop, "", whole, whole[stop - first:])

    def on_assnmnt_expr(self, node):
        target, op, value = node.children
        new = INCREMENTS.get(str(op))
        if new:
            first, stop = self.span(op)
            whole = self.text[self.offset(start(target)):self.offset(end(value))]
            cut = first - self.offset(start(target))
            self.add("INCREMENTS", op, first, stop, new, whole, whole[:cut] + new + whole[cut + len(str(op)):])

    def on_return_stmt(self, node):
        if not node.children:
            return
        expr = node.children[0]
        first, stop = self.span(expr)
        original = self.text[first:stop]
        for operator, value in return_values(self.returns, self.types):
            if not same_value(original, value):
                self.add(operator, expr, first, stop, value, original, value)

    def on_expr_stmt(self, node):
        call = unwrap(node.children[0])
        if kind(call) == "standalone_call":
            if str(call.children[0]) in LOGGING:
                return
        elif kind(call) != "getattr_call":
            return
        first, stop = self.span(node)
        self.add("VOID_METHOD_CALLS", node, first, stop, "pass", self.text[first:stop], "pass")


def generate(text, path, rel, types):
    """(functions, mutants, dropped): every mutant keeps the line count and parses again, or it is dropped."""
    generator = Generator(text, path, rel, types)
    generator.walk_class(GD_PARSER.parse(text, gather_metadata=True).children)
    seen, kept, dropped = set(), [], 0
    for mutant in generator.mutants:
        key = (mutant.start, mutant.stop, mutant.text)
        if key in seen:
            continue
        seen.add(key)
        mutated = mutant.apply(text)
        try:
            ok = mutated.count("\n") == text.count("\n") and GD_PARSER.parse(mutated) is not None
        except Exception:  # gdtoolkit raises lark's errors on a mutant that does not parse
            ok = False
        if ok:
            kept.append(mutant)
        else:
            dropped += 1
    return generator.functions, kept, dropped


def project_types(copy):
    """Class names (class_name and inner classes) and enum names of the project's own scripts."""
    types = Types(set(), set())
    for path in copy.rglob("*.gd"):
        text = path.read_text(encoding="utf-8", errors="replace")
        types.classes.update(CLASS_NAME.findall(text) + INNER_CLASS.findall(text))
        types.enums.update(ENUM.findall(text))
    return types


def related_tests(copy, folders, rel, text):
    """The gdUnit4 suites under the test folders that name the file's class_name or its res:// path."""
    names = CLASS_NAME.findall(text)
    pattern = re.compile(rf"\b{re.escape(names[0])}\b") if names else None
    found = []
    for folder in folders:
        base = copy / folder[len("res://"):].strip("/")
        for path in sorted(base.rglob("*.gd")) if base.is_dir() else ():
            body = path.read_text(encoding="utf-8", errors="replace")
            if "GdUnitTestSuite" not in body and not path.name.endswith("_test.gd"):
                continue
            if f"res://{rel}" in body or (pattern and pattern.search(body)):
                found.append("res://" + path.relative_to(copy).as_posix())
    return found


def load_coverage(path, sha, prefix):
    """{path: [statement]} of a gd_coverage.py --json report of this ref and project, or None when it is not one."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("tool") != "gd_coverage" or data.get("version") != 1:
            notice(f"{path} is not a gd_coverage.py --json report (version 1)")
            return None
        if data.get("ref") != sha or data.get("project") != (prefix or "."):
            notice(f"{path} measured {str(data.get('ref'))[:12]} of {data.get('project')}; this run mutates "
                   f"{sha[:12]} of {prefix or '.'}")
            return None
        statements = {}
        for function in data["functions"]:
            statements.setdefault(function["path"], []).extend(
                (int(s["line"]), int(s["end"]), s["hits"]) for s in function["statements"])
        return statements
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        notice(f"coverage report {path} not read: {type(error).__name__}: {error}")
        return None


def covered(statements, mutant):
    """True when a statement holding the mutant's line ran, False when every one was measured and none ran, None
    when the report does not measure that line."""
    hits = [h for line, last, h in statements.get(mutant.path, ()) if line <= mutant.line <= last]
    if any(h for h in hits if h is not None):
        return True
    return False if hits and all(h == 0 for h in hits) else None


def classify(code, output, rel):
    if code is None:
        return "timed out"
    if code == 105 or any(f"res://{rel}" in error for error in parse_errors(output)):
        return "invalid"
    if code == 100:
        return "killed"
    summary = test_summary(output)
    if code in COUNTED_EXITS and summary and summary["cases"] >= 1:
        return "survived"
    return "error"


def test_command(folder, tests):
    return ["--path", str(folder), "--headless", "-s", GDUNIT_TOOL] + \
        [arg for t in tests for arg in ("-a", t)] + ["-c", "--ignoreHeadlessMode"]


def clone(source, target):
    """APFS clone of the imported copy (cp -c), or a plain copy where clonefile is not available."""
    if subprocess.run(["cp", "-cR", str(source), str(target)], capture_output=True, check=False).returncode:
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(source, target, symlinks=True)


@dataclass
class Worker:
    folder: Path
    env: dict
    log: Path


def run_mutants(godot, workers, mutants, sources, timeouts):
    """Each worker takes the next mutant, writes it into its clone, runs its tests and restores the file.

    A mutant whose write or run raises is "not run" and the worker takes the next one; a worker that cannot restore
    the file stops, since its clone no longer holds the source. Returns how many mutants are "not run"."""
    jobs = queue.Queue()
    for mutant in mutants:
        jobs.put(mutant)

    def work(worker):
        while True:
            try:
                mutant = jobs.get_nowait()
            except queue.Empty:
                return
            target, original = worker.folder / mutant.rel, sources[mutant.rel]
            try:
                write(target, mutant.apply(original))
                code, output, seconds, _ = run_godot(godot, test_command(worker.folder, mutant.tests), worker.env,
                                                     worker.log, timeouts[tuple(mutant.tests)])
                mutant.exit, mutant.seconds = code, round(seconds, 2)
                mutant.status = classify(code, output, mutant.rel)
            except Exception as error:  # the host failed, not the mutant: no status counts it
                mutant.status = "not run"
                notice(f"{mutant.path}:{mutant.line} {mutant.operator} not run: {type(error).__name__}: {error}")
            try:
                write(target, original)
            except OSError as error:
                notice(f"a worker stops: {target} not restored ({type(error).__name__}: {error})")
                return

    threads = [threading.Thread(target=work, args=(w,)) for w in workers]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    left = [m for m in mutants if not m.status]
    for mutant in left:
        mutant.status = "not run"
    if left:
        notice(f"{len(left)} mutant(s) not run: every worker stopped")
    return sum(1 for m in mutants if m.status == "not run")


def baselines(godot, worker, selections, timeout, constant):
    """{selection: run} of each test selection unmutated, with its mutants' timeout; `ok` is False when it cannot
    measure mutants."""
    runs = {}
    for tests in selections:
        code, output, seconds, _ = run_godot(godot, test_command(worker.folder, tests), worker.env, worker.log,
                                             timeout)
        summary = test_summary(output)
        ok = code in COUNTED_EXITS and summary is not None and summary["cases"] >= 1
        runs[tests] = {"tests": list(tests), "exit": code, "cases": summary["cases"] if summary else None,
                       "seconds": round(seconds, 2), "timeout": round(TIMEOUT_FACTOR * seconds + constant, 2),
                       "ok": ok}
        if not ok:
            notice(f"unmutated run of {', '.join(tests)} exited {code} with "
                   f"{summary['cases'] if summary else 'no'} test case(s); its mutants are not run")
    return runs


def summarize(mutants, args, data):
    for mutant in sorted(mutants, key=lambda m: (m.path, m.line, m.column, m.operator)):
        if mutant.status == "survived":
            print(f"{mutant.path}:{mutant.line} {mutant.function} {mutant.operator} {mutant.before} → {mutant.after}")
    lines = {}
    for mutant in mutants:
        if mutant.status == "no coverage":
            lines.setdefault((mutant.path, mutant.line, mutant.function), []).append(mutant)
    for (path, line, function), found in sorted(lines.items()):
        notice(f"no coverage: {path}:{line} {function} ({len(found)} mutant(s) not run)")
    counts = {s: sum(1 for m in mutants if m.status == s) for s in STATUSES}
    detected = counts["killed"] + counts["timed out"]
    score = round(detected / (detected + counts["survived"]), 4) if detected + counts["survived"] else None
    shown_score = f"{100 * score:.1f} % ({detected}/{detected + counts['survived']})" if score is not None else "none"
    notice(f"{len(mutants)} mutant(s): " + ", ".join(f"{n} {s}" for s, n in counts.items() if n) +
           f"; score {shown_score}")
    if args.json:
        data.update({"score": score, "counts": counts, "mutants": [m.report() for m in mutants]})
        Path(args.json).write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def collect(copy, prefix, sha, wanted, tests):
    """(mutants, sources, dropped) of the wanted functions of the copy."""
    skipped = EXCLUDED + tuple(t[len("res://"):].strip("/") + "/" for t in tests)
    types, mutants, sources, dropped = project_types(copy), [], {}, 0
    for path, lines in sorted(wanted.items()):
        rel = path[len(prefix) + 1:] if prefix and path.startswith(prefix + "/") else (None if prefix else path)
        if rel is None or rel.startswith(skipped) or not (copy / rel).is_file():
            notice(f"{path} is not mutated (a test, an addon, outside the project or not in {sha[:12]})")
            continue
        text = read(copy / rel)
        try:
            functions, found, lost = generate(text, path, rel, types)
        except Exception as error:  # a file gdtoolkit cannot parse is named and left alone
            notice(f"{path} is not mutated: gdtoolkit did not parse it ({type(error).__name__})")
            continue
        chosen = {name for name, first, last in functions
                  if lines is None or any(first <= n <= last for n in lines)}
        sources[rel] = text
        mutants += [m for m in found if m.function in chosen]
        dropped += lost
    return mutants, sources, dropped


def measure(args, prefix, sha, wanted, godot, scratch):
    copy = scratch / "project"
    copy.mkdir()
    filled, missing = extract(sha, prefix, copy)
    if missing:
        notice(f"{missing} LFS object(s) are not in the local store and stay pointers (git lfs fetch)")
    if not (copy / GDUNIT_TOOL).is_file():
        notice(f"{GDUNIT_TOOL} is not in the project at {sha[:12]}; mutants not run")
        return 2
    tests = args.tests or ["res://tests"]
    began = time.monotonic()
    mutants, sources, dropped = collect(copy, prefix, sha, wanted, tests)
    statements = load_coverage(args.coverage, sha, prefix) if args.coverage else {}
    if statements is None:
        return 2
    unmeasured = 0
    selection = {rel: tuple(related_tests(copy, tests, rel, text)) for rel, text in sources.items()}
    for mutant in mutants:
        mutant.tests = list(selection[mutant.rel])
        state = covered(statements, mutant) if args.coverage else None
        unmeasured += args.coverage is not None and state is None
        mutant.status = "no coverage" if state is False else "no tests" if not mutant.tests else ""
    generate_seconds = time.monotonic() - began
    if dropped:
        notice(f"{dropped} mutant(s) dropped: they did not parse again or changed a line number")
    if unmeasured:
        notice(f"{unmeasured} mutant(s) on lines the coverage report does not measure are run")
    data = {"tool": "gd_mutation", "version": 1, "ref": sha, "project": prefix or ".", "godot": None,
            "coverage": args.coverage, "workers": args.workers, "lfs": {"filled": filled, "missing": missing},
            "seconds": {"generate": round(generate_seconds, 2)}, "baselines": []}
    pending = [m for m in mutants if not m.status]
    if not pending:
        summarize(mutants, args, data)
        return 0
    env, log = scratch_env(scratch), scratch / "godot.log"
    data["godot"] = subprocess.run([godot, "--version"], capture_output=True, text=True, env=env,
                                   check=False).stdout.strip()
    code, _, import_seconds, _ = run_godot(godot, ["--path", str(copy), "--headless", "--import"], env, log,
                                           args.timeout)
    if code is None:
        notice(f"mutants not run: the import did not finish in {args.timeout} s")
        return 2
    if code:
        notice(f"import exited {code}")
    workers = []
    for index in range(args.workers):
        folder = scratch / f"w{index}"
        folder.mkdir()
        clone(copy, folder / "project")
        workers.append(Worker(folder / "project", scratch_env(folder), folder / "godot.log"))
    runs = baselines(godot, workers[0], sorted({tuple(m.tests) for m in pending}), args.timeout,
                     args.timeout_constant)
    for mutant in pending:
        if not runs[tuple(mutant.tests)]["ok"]:
            mutant.status = "not run"
    began = time.monotonic()
    failed = run_mutants(godot, workers, [m for m in pending if not m.status], sources,
                         {tests: run["timeout"] for tests, run in runs.items()})
    data["seconds"].update({"import": round(import_seconds, 2), "mutants": round(time.monotonic() - began, 2)})
    data["baselines"] = list(runs.values())
    summarize(mutants, args, data)
    return 2 if failed or any(not run["ok"] for run in runs.values()) else 0


def main():
    ap = argparse.ArgumentParser(description="Advisory mutation testing of GDScript functions under gdUnit4")
    ap.add_argument("files", nargs="*", help="mutate every function of these files")
    ap.add_argument("--base", default="origin/main",
                    help="without FILE, mutate the functions whose lines changed in REF...HEAD (default origin/main)")
    ap.add_argument("--ref", default="HEAD", help="commit whose tree is mutated (default HEAD)")
    ap.add_argument("--coverage", help="gd_coverage.py --json report of the same ref: uncovered lines are not run")
    ap.add_argument("--tests", action="append", help="gdUnit4 test folder, repeatable (default res://tests)")
    ap.add_argument("--workers", type=int, default=1, help="parallel Godot runs, each in its own clone (default 1)")
    ap.add_argument("--timeout", type=int, default=TIMEOUT,
                    help=f"seconds for the import and each unmutated run (default {TIMEOUT})")
    ap.add_argument("--timeout-constant", type=float, default=TIMEOUT_CONSTANT,
                    help=f"seconds added to {TIMEOUT_FACTOR} x the unmutated time to stop a mutant's run "
                         f"(default {TIMEOUT_CONSTANT})")
    ap.add_argument("--json", help="write every mutant and its status to this file")
    ap.add_argument("--keep", action="store_true", help="keep the temporary copy, clones and logs")
    args = ap.parse_args()
    gd_coverage.notice = notice  # the reused helpers report under this tool's name
    if args.workers < 1:
        ap.error("--workers must be 1 or more")
    if args.timeout_constant < 0:
        ap.error("--timeout-constant must be 0 or more")
    files = [os.path.realpath(p) for p in args.files]
    args.json = os.path.abspath(args.json) if args.json else None
    args.coverage = os.path.abspath(args.coverage) if args.coverage else None
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
    if files:
        wanted = {os.path.relpath(p, top): None for p in files}
    elif sha != git_out("rev-parse", "--verify", "HEAD^{commit}"):
        notice(f"--base reads the change of HEAD, not of {args.ref}; check out {args.ref} or name the files")
        return 2
    else:
        wanted = {p: n for p, n in changed_lines(args.base).items() if p.endswith(".gd")}
        if not wanted:
            notice("no changed .gd function to mutate")
            return 0
    if GD_PARSER is None:
        notice("gdtoolkit not available (pip install gdtoolkit==4.5.0); mutants not generated")
        return 2
    godot = os.environ.get("GODOT") or shutil.which("godot")
    if not godot:
        notice("godot not found (set GODOT or put it on PATH); mutants not run")
        return 2
    scratch = Path(tempfile.mkdtemp(prefix="gd-mutation-"))
    try:
        return measure(args, prefix, sha, wanted, godot, scratch)
    finally:
        if args.keep:
            notice(f"kept {scratch}")
        else:
            shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
