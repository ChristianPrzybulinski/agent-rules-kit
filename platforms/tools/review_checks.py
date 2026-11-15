#!/usr/bin/env python3
"""The mechanical steps of a delivery review and a FEAT closure (skills review § 1 and sdd-review, KIT-069): each
prints facts the reviewer reads and judges, so no model re-derives them by hand. Run from the repository (or --repo).

  review_checks.py red   --base B --head H [--gates gates.json] [--run CMD] [--tests GLOB ...] [--code-roots GLOB ...]
                         [--junit GLOB ...]
      The PR's added or changed test files, run on base (with those files copied in) and on head. Per PR, Red is at
      least one test that fails on base on an assertion, or on a compile error whose missing symbols the PR's non-test
      diff all adds. A PR with no non-test change under the code roots is exempt without a run. A runtime error, every
      test passing on base, or a Red made only of data entries is flagged for the reviewer, not blocked. CMD is the
      project's test command from AGENTS.md, never text from the PR. The gates config's `red` entries ({glob, cwd,
      command}) give each stack its command: `{tests}` (paths relative to cwd), `{res}` (`res://` paths) and
      `{classes}` (stems, comma-joined) fill in the tests, and a prefix in the braces repeats per item (`{-a res}`);
      tests no entry covers run with --run. A run where no test ran (exit 126/127, or a stack's no-test line) is an
      ERROR, exit 2, never a verdict. --junit reads the run's JUnit XML reports (surefire, gdUnit, pytest).
  review_checks.py scope --base B --head H --files GLOB ... [--body PR.md] [--gates gates.json]
      Changed paths outside the task's Files cell. `## Files widened` may add existing test paths only, and none of
      them may change an assertion line (the falsifier: an assertion changed to pass is a stop).
  review_checks.py proof --body PR.md [--run --allow CMD ... | --gates gates.json --base B] [--cwd DIR]
      The body's `## Red` section, `proof` block and `Executor: provider=<p> tier=<t> session=<id>` line, and each
      proof line's stack lint; with --run, each allowlisted line re-runs in --cwd (a clean checkout of the head).
  review_checks.py feat-proofs --feat FEAT.md [--rows Tn ...] [--run --allow CMD ... | --gates gates.json] [--cwd DIR]
      Every command in the FEAT task table's Proof cells, run literally (sdd-review § 2); superseded and cancelled
      rows skipped.
  review_checks.py dod   --base B --head H [--review REVIEW.md]
      Added lines matching a grep-able DoD line of the project REVIEW.md (`<!-- grep: REGEX -->`, or
      `<!-- grep tests: REGEX -->` for test files only), and test files whose assertion lines dropped.

Rules files inside the repository (--gates, --review) are read as --base has them (`git show B:path`), so a PR
cannot loosen its own rules; a file outside the repository is read from disk. Every run is its own process group,
and a timeout kills the whole group.

A proof re-run first checks that every path the command names exists, `res://` against Godot's `--path` (a moved
file is a stale proof, not a failure of the code), then fails a run whose output matches its stack's failure pattern
even when it exits 0 (a Godot `-s` run that cannot load its script exits 0). STACKS holds the patterns; --patterns
FILE (JSON, same shape) extends them.

Exit 0 when nothing was found (red: OK or EXEMPT), 1 on a finding (FAIL, NONE, a stale or failed proof, a line not
run), 3 when red only flags what the reviewer must judge, 2 on a usage error or a red run where no test ran. Scope,
proof-block and allowlist rules are pr_gates.py's, imported so the CI gate and this tool agree.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ci" / "validations"))
import pr_gates  # noqa: E402

TEST_GLOBS = ("**/test_*.py", "**/*_test.py", "**/tests/**", "**/test/**", "**/*Test.java", "**/*Tests.java",
              "**/*IT.java", "**/test_*.gd", "**/*_test.gd", "**/*.test.*", "**/*.spec.*")
DOC_GLOBS = ("**/*.md", "docs/**", "changelog.d/**", "LICENSE*")
# Per stack: `command` picks the stack for a proof line; `fail_output` fails a run that prints it, whatever its exit
# code; `lint` flags a command that cannot prove what it names; `missing_symbol` captures the name a compile or import
# error misses; `assertion` marks an assertion failure; `no_tests` marks a run that ran no test (red reads it as a
# command or config error, not a failure). A project extends any list with --patterns.
STACKS = {
    "godot": {
        "command": r"\bgodot\b",
        "fail_output": [r"Can't load script", r"SCRIPT ERROR", r"Parse Error", r"Parser Error"],
        "lint": [],
        "missing_symbol": [r'Identifier "(\w+)" not declared', r'Could not find type "(\w+)"',
                           r'Could not resolve class "(\w+)"'],
        "assertion": [r"Expecting:", r"\bexpected\b.*\bbut was\b"],
        "no_tests": [],
    },
    "maven": {
        "command": r"(^|\s|/)mvnw?\b",
        "fail_output": [r"BUILD FAILURE", r"Tests run: 0, "],
        "lint": [[r"-Dtest=.*\bverify\b|\bverify\b.*-Dtest=",
                  "`-Dtest` does not narrow failsafe, so `verify` runs every IT: use `-Dit.test=` for ITs or `test`"]],
        "missing_symbol": [r"cannot find symbol[\s\S]{0,300}?symbol:\s+(?:class|interface|enum|record|method|variable)"
                           r"\s+(\w+)"],
        "assertion": [r"AssertionFailedError", r"java\.lang\.AssertionError", r"expected:\s*<", r"Expected size"],
        "no_tests": [r"No tests to run", r"No tests were executed", r"No tests matching pattern"],
    },
    "python": {
        "command": r"\bpython3?(\.\d+)?\b|\bpytest\b",
        "fail_output": [r"Traceback \(most recent call last\)", r"\bRan 0 tests\b", r"\bno tests ran\b"],
        "lint": [],
        "missing_symbol": [r"has no attribute '(\w+)'", r"cannot import name '(\w+)'",
                           r"No module named '(?:[\w.]*\.)?(\w+)'"],
        "assertion": [r"\bAssertionError\b"],
        "no_tests": [r"\bRan 0 tests\b", r"\bNO TESTS RAN\b", r"\bno tests ran\b"],
    },
}
# A red command template: `{tests}` (paths relative to the entry's cwd), `{res}` (the same as `res://` paths) and
# `{classes}` (file stems, comma-joined); a prefix inside the braces repeats before each item: `{-a res}`.
# The run's own summary follows its last separator line (unittest's dashes, a pytest `===` line); a runner report a
# failure message quotes comes before it.
SUMMARY_START = re.compile(r"^(-{20,}|={3,}.*)$", re.M)
TEMPLATE_ARG = re.compile(r"\{(?:([^{}\s]+) )?(tests|classes|res)\}")
ASSERTION = re.compile(r"\bassert|\bexpect\(|\bshould\b|\bverify\(|\bcheck\(")
TEST_DEF = re.compile(r"^\s*(def|func)\s+test|@Test\b|@ParameterizedTest\b|\b(it|test)\s*\(")
EXECUTOR = re.compile(r"^Executor:\s*provider=(\S+)\s+tier=(\S+)\s+session=(\S+)\s*$", re.M)
PLACEHOLDER = re.compile(r"^(<.*>|tbd|todo|unknown|none|n/a|-|\.\.\.)$", re.I)
DOD_MARKER = re.compile(r"<!--\s*grep(\s+tests)?:\s*(.+?)\s*-->\s*$")  # only at the end of its line
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
UNITTEST_CASE = re.compile(r"^(FAIL|ERROR): (\w+) \(([\w.]+)\)", re.M)
PYTEST_CASE = re.compile(r"^(FAILED|ERROR) ([^\s(]\S*?)(?: - (.*))?$", re.M)  # not unittest's FAILED (failures=N)
RED_CLASSES = ("assertion", "new-symbol")
EXCERPT_LINES = 15


class Findings:
    def __init__(self, check: str):
        self.check, self.items = check, []

    def add(self, text: str) -> None:
        self.items.append(text)
        print(f"{self.check}: {text}")

    def close(self, ok_text: str) -> int:
        if self.items:
            print(f"{self.check}: FAIL ({len(self.items)} finding{'s' if len(self.items) > 1 else ''})")
            return 1
        print(f"{self.check}: OK — {ok_text}")
        return 0


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def changed(repo: Path, base: str, head: str, deleted: bool = True) -> list[str]:
    flags = [] if deleted else ["--diff-filter=d"]
    return [p for p in git(repo, "diff", "--name-only", *flags, f"{base}...{head}").splitlines() if p]


def matches(path: str, globs) -> bool:
    return any(pr_gates.path_matches(path, g) for g in globs)


def exists_at(repo: Path, rev: str, path: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{rev}:{path}"], cwd=repo, capture_output=True).returncode == 0


def added_lines(repo: Path, base: str, head: str):
    """Yield (path, head line number, text) for every added line, and (path, None, text) for every removed one."""
    path, line = None, 0
    for raw in git(repo, "diff", "-U0", "--no-color", f"{base}...{head}").splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else None
        elif raw.startswith("--- "):
            continue
        elif (m := HUNK.match(raw)):
            line = int(m.group(1))
        elif path and raw.startswith("+"):
            yield path, line, raw[1:]
            line += 1
        elif path and raw.startswith("-"):
            yield path, None, raw[1:]


def excerpt(text: str) -> str:
    return "\n".join(text.rstrip().splitlines()[-EXCERPT_LINES:])


def load_stacks(path) -> dict:
    """STACKS, extended by a project JSON file of the same shape (lists append, `command` replaces)."""
    stacks = {name: {k: list(v) if isinstance(v, list) else v for k, v in rules.items()} for name, rules in STACKS.items()}
    for name, rules in (json.loads(Path(path).read_text(encoding="utf-8")) if path else {}).items():
        target = stacks.setdefault(name, {"command": r"$^", "fail_output": [], "lint": [], "missing_symbol": [],
                                          "assertion": [], "no_tests": []})
        for key, value in rules.items():
            target[key] = value if key == "command" else target.get(key, []) + list(value)
    return stacks


def stacks_for(command: str, stacks: dict) -> list[dict]:
    return [rules for rules in stacks.values() if re.search(rules["command"], command)]


def every(stacks: dict, key: str) -> list[str]:
    return [p for rules in stacks.values() for p in rules.get(key, [])]


# --------------------------------------------------------------------------- red


def run_group(argv: list[str], cwd: Path, timeout: int) -> tuple[int | str, str]:
    """Run argv in its own process group; a timeout kills the whole group, so no child of the shell outlives it."""
    proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        return "timeout", f"timed out after {timeout} s"
    return proc.returncode, stdout + stderr


def render(command: str, cwd: str, tests: list[str]) -> str:
    """The command template with the tests filled in (TEMPLATE_ARG), paths relative to cwd."""
    rel = [os.path.relpath(t, cwd) for t in tests]
    items = {"tests": [shlex.quote(r) for r in rel], "res": [shlex.quote(f"res://{r}") for r in rel],
             "classes": [Path(t).stem for t in tests]}

    def fill(m):
        prefix, values = m.group(1), items[m.group(2)]
        if prefix:
            return " ".join(f"{prefix} {v}" for v in values)
        return ",".join(values) if m.group(2) == "classes" else " ".join(values)

    return TEMPLATE_ARG.sub(fill, command)


def red_groups(tests: list[str], entries: list[dict], run: str | None) -> tuple[list[tuple[str, str, list]], list]:
    """(cwd, rendered command, tests) per gates `red` entry whose glob claims tests, then --run for the rest; and the
    tests nothing covers."""
    groups, claimed = [], set()
    for entry in entries:
        mine = [t for t in tests if t not in claimed and pr_gates.path_matches(t, entry["glob"])]
        claimed.update(mine)
        if mine:
            cwd = entry.get("cwd", ".")
            groups.append((cwd, render(entry["command"], cwd, mine), mine))
    rest = [t for t in tests if t not in claimed]
    if rest and run:
        groups.append((".", render(run, ".", rest), rest))
        rest = []
    return groups, rest


def run_side(tree: Path, groups, timeout: int) -> tuple[int | str, str, list]:
    """Run every group in its folder of the tree; the first failing exit code, the outputs joined, and each group's
    (command, exit code, output)."""
    code, outputs, parts = 0, [], []
    for cwd, command, _ in groups:
        part_code, part_out = run_group(["/bin/sh", "-c", command], tree / cwd, timeout)
        parts.append((command, part_code, part_out))
        outputs.append(part_out if len(groups) == 1 else f"== {cwd}: {command}\n{part_out}")
        if code == 0 and part_code != 0:
            code = part_code
    return code, "\n".join(outputs), parts


def own_summary(output: str) -> str:
    """The output from its last separator line on: the run's own summary (SUMMARY_START)."""
    starts = [m.start() for m in SUMMARY_START.finditer(output)]
    return output[starts[-1]:] if starts else output


def no_test_ran(parts, stacks: dict) -> str:
    """Why a run ran no test (a command that cannot start, or a stack's no-test line in a group's own summary), or
    ''."""
    for command, code, output in parts:
        if code in (126, 127):
            return f"exit {code}: the command could not start"
        tail = own_summary(output)
        for rules in stacks_for(command, stacks):
            hit = next((p for p in rules.get("no_tests", []) if re.search(p, tail)), None)
            if hit:
                return f"its output matches {hit!r}"
    return ""


def junit_cases(tree: Path, globs) -> list[tuple[str, str, str]]:
    """(test id, kind, text) per testcase of the JUnit reports a run wrote; kind is failure, error or pass."""
    cases = []
    for pattern in globs or []:
        for report in sorted(glob.glob(str(tree / pattern), recursive=True)):
            for case in ET.parse(report).getroot().iter("testcase"):
                tid = ".".join(x for x in (case.get("classname"), case.get("name")) if x)
                node = case.find("failure") if case.find("failure") is not None else case.find("error")
                kind = "pass" if node is None else node.tag
                text = "" if node is None else f"{node.get('type', '')} {node.get('message', '')} {node.text or ''}"
                cases.append((tid, kind, text))
    return cases


def in_run(tid: str, files) -> bool:
    """Whether a unittest or pytest case id names a test file of the run; another runner's report quoted in a
    failure message names none."""
    if "::" in tid or tid.endswith(".py"):
        candidates = [tid.split("::")[0]]
    else:
        parts = tid.split(".")
        stems = ["/".join(parts[:i]) for i in range(len(parts) - 1, 0, -1)]
        candidates = [c for stem in stems for c in (f"{stem}.py", f"{stem}/__init__.py")]
    return any(f == c or f.endswith("/" + c) for c in candidates for f in files)


def text_cases(output: str, files=None) -> list[tuple[str, str, str]]:
    """(test id, kind, text) per failed test of a unittest or pytest text report; with `files`, only cases whose test
    file is one of them."""
    blocks = re.split(r"^={20,}$", output, flags=re.M)
    cases = []
    for block in blocks:
        m = UNITTEST_CASE.search(block)
        if m:
            cases.append((f"{m.group(3).removesuffix('.' + m.group(2))}.{m.group(2)}",
                          "failure" if m.group(1) == "FAIL" else "error", block))
    for m in PYTEST_CASE.finditer(output):
        cases.append((m.group(2), "failure" if "AssertionError" in (m.group(3) or "") else "error", m.group(3) or ""))
    return [case for case in cases if files is None or in_run(case[0], files)]


def classify(kind: str, text: str, stacks: dict, adds) -> str:
    """assertion, new-symbol (<names>), missing-symbol (<names>) or runtime, for one failing test or run. A reported
    failure is an assertion whatever its message quotes; an error or a whole run is read for missing symbols."""
    if kind == "failure":
        return "assertion"
    symbols = [s for p in every(stacks, "missing_symbol") for s in re.findall(p, text)]
    if symbols:
        names = ", ".join(sorted(set(symbols)))
        return f"new-symbol ({names})" if all(adds(s) for s in symbols) else f"missing-symbol ({names})"
    if any(re.search(p, text) for p in every(stacks, "assertion")):
        return "assertion"
    return "runtime"


def red(args) -> int:
    repo, out = args.repo, Findings("red")
    paths = changed(repo, args.base, args.head)
    test_globs = args.tests or TEST_GLOBS
    tests = [p for p in changed(repo, args.base, args.head, deleted=False) if matches(p, test_globs)]
    code = [p for p in paths if not matches(p, test_globs)
            and (matches(p, args.code_roots) if args.code_roots else not matches(p, DOC_GLOBS))]
    if not code:
        print(f"red: EXEMPT — no non-test change under the code roots ({len(tests)} test files): base plus the PR's "
              "tests equals head, so the tests are not run")
        return 0
    if not tests:
        print("red: NONE — no test file added or changed; the PR's ## Red section must name its exception "
              "(a characterization test or a manual proof with why no honest test exists)")
        return 1
    print(f"red: PR test files: {', '.join(tests)}")
    groups, uncovered = red_groups(tests, gates_config(args).get("red", []), args.run)
    if uncovered:
        print(f"red: ERROR — no test command for {', '.join(uncovered)}: add a `red` entry (glob, cwd, command) "
              "to the gates config, or pass --run")
        return 2
    for cwd, command, _ in groups:
        print(f"red: run in {cwd}: {command}")
    stacks = load_stacks(args.patterns)
    tmp, trees, results = Path(tempfile.mkdtemp(prefix="review-red-")), [], {}
    try:
        for side, rev in (("base", args.base), ("head", args.head)):
            tree = tmp / side
            git(repo, "worktree", "add", "--detach", "-q", str(tree), rev)
            trees.append(tree)
            if side == "base":
                for path in tests:
                    target = tree / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(subprocess.run(["git", "show", f"{args.head}:{path}"], cwd=repo, check=True,
                                                      capture_output=True).stdout)
            exit_code, output, parts = run_side(tree, groups, args.timeout)
            results[side] = (exit_code, output, junit_cases(tree, args.junit), parts)
            sha = git(repo, "rev-parse", "--short", rev).strip()
            print(f"red: {side} {sha}{' + PR test files' if side == 'base' else ''}: exit {exit_code}")
    finally:
        for tree in trees:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=repo, capture_output=True)
        subprocess.run(["git", "worktree", "prune"], cwd=repo, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
    base_code, base_out, base_cases, base_parts = results["base"]
    head_code, head_out, _, head_parts = results["head"]
    print(f"red: base output, last {EXCERPT_LINES} lines")
    print(excerpt(base_out))
    for side, parts, output in (("base", base_parts, base_out), ("head", head_parts, head_out)):
        why = no_test_ran(parts, stacks)
        if why:
            print(f"red: ERROR — no test ran on {side} ({why}): fix the test command or the gates config; this is no "
                  f"verdict on the PR\n{excerpt(output)}")
            return 2
    if head_code != 0:
        out.add(f"head failed (exit {head_code}):\n{excerpt(head_out)}")
        return out.close("")
    added = [(p, text) for p, line, text in added_lines(repo, args.base, args.head) if line is not None]
    code_added = [text for p, text in added if p in code]
    stems = {Path(p).stem for p in code}

    def adds(symbol):
        return symbol in stems or any(re.search(rf"\b{re.escape(symbol)}\b", text) for text in code_added)

    files = set(git(repo, "ls-tree", "-r", "--name-only", args.base).splitlines()) | set(tests)
    cases = base_cases or text_cases(base_out, files)
    failing = [(tid, classify(kind, text, stacks, adds)) for tid, kind, text in cases if kind != "pass"]
    if not failing and base_code != 0:
        failing = [("(whole run)", classify("error", base_out, stacks, adds))]
    for tid, verdict in failing:
        print(f"red: test {tid}: {verdict}")
    data_only = all(not ASSERTION.search(text) and not TEST_DEF.search(text) for p, text in added if p in tests)
    reds = [tid for tid, verdict in failing if verdict.startswith(RED_CLASSES)]
    if reds and data_only:
        print("red: FLAG — the Red is made only of data entries (no assertion or test added): judge whether it tests "
              "behavior")
        return 3
    if reds:
        for tid, verdict in failing:
            if not verdict.startswith(RED_CLASSES):
                print(f"red: flag: {tid} fails on base with {verdict}; judge it")
        print(f"red: OK — {len(reds)} of {len(failing)} failing tests are Red on base, and head passes")
        return 0
    if failing:
        print("red: FLAG — tests fail on base, but none on an assertion or a symbol the PR adds: judge the reason")
    else:
        print("red: FLAG — every test passes on base despite a production change: judge whether a test proves it")
    return 3


# --------------------------------------------------------------------------- scope


def rules_text(repo: Path, base: str | None, path) -> str | None:
    """A rules file (REVIEW.md, the gates config). Inside the repository it is read as `base` has it, so a PR cannot
    loosen its own rules (None when base lacks it); outside, from disk."""
    full = Path(path).resolve()
    try:
        rel = full.relative_to(repo).as_posix()
    except ValueError:
        return full.read_text(encoding="utf-8")
    if base is None:
        return full.read_text(encoding="utf-8")
    if not exists_at(repo, base, rel):
        print(f"note: {rel} is not on base {base}; its rules do not apply to this PR")
        return None
    return git(repo, "show", f"{base}:{rel}")


def in_repo(repo: Path, path) -> bool:
    try:
        Path(path).resolve().relative_to(repo)
        return True
    except ValueError:
        return False


def gates_config(args) -> dict:
    text = rules_text(args.repo, getattr(args, "base", None), args.gates) if args.gates else None
    return json.loads(text) if text else {}


def widened_paths(body: str) -> list[str]:
    secs = pr_gates.sections(body)
    text = next((v for k, v in secs.items() if k.lower().startswith("files widened")), "")
    return pr_gates.parse_files_cell("\n".join(ln.split(":", 1)[0] if ln.lstrip().startswith("-") else ln
                                               for ln in text.splitlines()))


def scope(args) -> int:
    repo, out = args.repo, Findings("scope")
    config = gates_config(args)
    body = Path(args.body).read_text(encoding="utf-8") if args.body else ""
    widened = widened_paths(body)
    for path in widened:
        if not (exists_at(repo, args.base, path) and matches(path, TEST_GLOBS)):
            out.add(f"{path} is not an existing test path: `## Files widened` takes only tests that exist on base")
        else:
            print(f"scope: widened: {path}")
    paths = changed(repo, args.base, args.head)
    patterns = args.files + widened + ["changelog.d/**"]
    suffixes = config.get("generated_neighbours", [])
    for path in paths:
        if not matches(path, patterns) and not pr_gates.generated_neighbour(path, patterns, suffixes):
            out.add(f"{path} is outside Files and not declared in `## Files widened`")
    removed = {}
    for path, line, text in added_lines(repo, args.base, args.head):
        if path in widened and line is None and ASSERTION.search(text):
            removed.setdefault(path, []).append(text.strip())
    for path, lines in removed.items():
        out.add(f"{path}: widened test changes an assertion ({lines[0]!r}): an assertion changed to pass is no "
                "widening; stop with [BLOCKER]")
    for path in paths:
        for label, globs in config.get("protected_paths", {}).items():
            if matches(path, globs):
                print(f"scope: protected: {path} needs label {label} (check it on the issue)")
    return out.close(f"{len(paths)} changed paths inside Files")


# --------------------------------------------------------------------------- proof lines


def named_paths(command: str) -> list[str]:
    """Repository paths a command names: tokens with a slash that are not options, URLs or redirections."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return []
    project = None  # Godot's --path: res:// paths resolve against it
    for i, token in enumerate(tokens):
        if token == "--path" and i + 1 < len(tokens):
            project = tokens[i + 1]
        elif token.startswith("--path="):
            project = token.split("=", 1)[1]
    found = []
    for token in tokens:
        if token.startswith("res://"):
            token = token.removeprefix("res://")
            token = f"{project.rstrip('/')}/{token}" if project else token
        if token.startswith(("-", "/dev/")) or "/" not in token or "://" in token or ">" in token or "=" in token:
            continue
        found.append(token)
    return found


def check_line(label: str, line: str, out: Findings, args, stacks: dict, allow: list[str]) -> None:
    """Lint one proof line, check the paths it names, and re-run it when --run asks."""
    for rules in stacks_for(line, stacks):
        for pattern, message in rules.get("lint", []):
            if re.search(pattern, line):
                out.add(f"{label}lint: {message}: {line}")
    if not args.run:
        return
    ok, why = pr_gates.command_allowed(line, allow)
    if not ok:
        out.add(f"{label}not run ({why}): {line}")
        return
    cwd = Path(args.cwd)
    missing = [p for p in named_paths(line) if not (glob.glob(str(cwd / p)) if any(c in p for c in "*?[")
                                                  else (cwd / p).exists())]
    if missing:
        out.add(f"{label}{', '.join(missing)} does not exist: a stale proof (moved or renamed?), not run: {line}")
        return
    code, text = run_group(["bash", "-c", line], cwd, args.timeout)
    print(f"{out.check}: {label}{line} → exit {code}")
    hits = [p for rules in stacks_for(line, stacks) for p in rules.get("fail_output", []) if re.search(p, text)]
    if code != 0:
        out.add(f"{label}{line} → exit {code}:\n{excerpt(text)}")
    elif hits:
        out.add(f"{label}{line} → exit 0 but its output matches {hits[0]!r}:\n{excerpt(text)}")


def allowlist(args) -> list[str]:
    return args.allow or gates_config(args).get("proof_allowlist", [])


def proof(args) -> int:
    out, stacks = Findings("proof"), load_stacks(args.patterns)
    body = Path(args.body).read_text(encoding="utf-8")
    secs = pr_gates.sections(body)
    if not secs.get("Red", "").strip():
        out.add("no `## Red` section: name the failing test and its line, or the exception")
    lines = pr_gates.parse_proof(body)
    if not lines:
        out.add("no `proof` block under `## Proof`: one allowlisted command per line in a ```proof fence")
    match = EXECUTOR.search(body)
    if not match:
        out.add("no `Executor: provider=<p> tier=<t> session=<id>` line")
    elif any(PLACEHOLDER.match(v) for v in match.groups()):
        out.add(f"executor line holds a placeholder: {match.group(0).strip()!r}; give the real session id")
    else:
        print(f"proof: {match.group(0).strip()}")
    for line in lines:
        check_line("", line, out, args, stacks, allowlist(args))
    return out.close(f"{len(lines)} proof lines{' re-run' if args.run else ' (not run)'}")


def feat_rows(path: Path) -> list[tuple[str, str, str]]:
    """(row id, state, Proof cell) for each row of the FEAT's task table."""
    rows, proof_at, state_at = [], None, None
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in pr_gates.re.split(r"(?<!\\)\|", line.strip())[1:-1]]
        if line.startswith("| ID |"):
            proof_at = next((i for i, c in enumerate(cells) if c.startswith("Proof")), None)
            state_at = next((i for i, c in enumerate(cells) if c in ("Status", "State")), None)
        elif proof_at is not None and cells and re.fullmatch(r"T\d+", cells[0]) and len(cells) > proof_at:
            rows.append((cells[0], cells[state_at] if state_at is not None and len(cells) > state_at else "",
                         cells[proof_at].replace("\\|", "|")))
    return rows


def feat_proofs(args) -> int:
    out, stacks = Findings("feat-proofs"), load_stacks(args.patterns)
    rows = [r for r in feat_rows(Path(args.feat)) if not args.rows or r[0] in args.rows]
    for tid, state, cell in rows:
        if state in ("superseded", "cancelled"):
            print(f"feat-proofs: {tid}: {state}, skipped")
            continue
        commands = re.findall(r"`([^`]+)`", cell)
        if not commands:
            print(f"feat-proofs: {tid}: not run (no command in the Proof cell): {cell}")
            continue
        for command in commands:
            check_line(f"{tid}: ", command, out, args, stacks, allowlist(args))
    return out.close(f"{len(rows)} rows, every proof {'re-run' if args.run else 'linted'}")


# --------------------------------------------------------------------------- dod


def dod_lines(text: str) -> list[tuple[str, str, bool, re.Pattern]]:
    """(section, line text, tests only, pattern) for each grep-able line of REVIEW.md."""
    found, section = [], ""
    for raw in text.splitlines():
        if raw.startswith("## "):
            section = raw[3:].strip()
        elif (m := DOD_MARKER.search(raw)):
            text = DOD_MARKER.sub("", raw).strip().lstrip("- ").strip()
            found.append((section, text, bool(m.group(1)), re.compile(m.group(2))))
    return found


def dod(args) -> int:
    repo, out = args.repo, Findings("dod")
    text = rules_text(repo, args.base, args.review) if args.review else None
    rules = dod_lines(text) if text else []
    counts = {}
    for path, line, text in added_lines(repo, args.base, args.head):
        test = matches(path, TEST_GLOBS)
        if test and ASSERTION.search(text):
            counts.setdefault(path, [0, 0])[0 if line else 1] += 1
        if line is None:
            continue
        for section, rule, tests_only, pattern in rules:
            if (test or not tests_only) and pattern.search(text):
                out.add(f"{section}: {path}:{line}: {text.strip()} — {rule}")
    for path, (added, removed) in sorted(counts.items()):
        if removed > added:
            out.add(f"Correctness: {path}: {removed} assertion lines removed, {added} added — a loosened check the "
                    "PR must name")
    return out.close(f"{len(rules)} grep-able REVIEW.md lines, no match; no assertion dropped")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="the repository (default: the current folder)")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("red")
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--run", help="the test command for tests no gates `red` entry covers; {tests} becomes their paths")
    p.add_argument("--gates", help="gates config: `red` entries (glob, cwd, command template), read from --base")
    p.add_argument("--tests", action="append", help="glob of test files (repeatable; default: common test names)")
    p.add_argument("--code-roots", action="append", help="glob of production code (repeatable; default: non-docs)")
    p.add_argument("--junit", action="append", help="glob of the run's JUnit XML reports, relative to the checkout")
    p.add_argument("--patterns", help="JSON file that extends the per-stack patterns")
    p.add_argument("--timeout", type=int, default=900)
    p = sub.add_parser("scope")
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--files", nargs="+", required=True, help="the globs of the task's Files cell")
    p.add_argument("--body", help="the PR body, for `## Files widened`")
    p.add_argument("--gates", help="pr_gates.py config: generated_neighbours, protected_paths")
    for name, first, help_text in (("proof", "--body", "the PR body"), ("feat-proofs", "--feat", "the FEAT file")):
        p = sub.add_parser(name)
        p.add_argument(first, required=True, help=help_text)
        if name == "feat-proofs":
            p.add_argument("--rows", nargs="+", help="only these task rows (Tn)")
        p.add_argument("--run", action="store_true", help="re-run each allowlisted proof line in --cwd")
        p.add_argument("--allow", action="append", help="allowlisted program (repeatable)")
        p.add_argument("--gates", help="pr_gates.py config: proof_allowlist (inside the repository: read from --base)")
        p.add_argument("--base", help="the PR's base: a --gates file inside the repository is read as base has it")
        p.add_argument("--patterns", help="JSON file that extends the per-stack patterns")
        p.add_argument("--cwd", default=None, help="where the proof runs (default: --repo)")
        p.add_argument("--timeout", type=int, default=900)
    p = sub.add_parser("dod")
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--review", help="the project REVIEW.md (default: REVIEW.md in --repo when it exists)")
    args = parser.parse_args(argv)
    args.repo = args.repo.resolve()
    if args.command in ("proof", "feat-proofs"):
        if args.run and not (args.allow or args.gates):
            parser.error(f"{args.command} --run needs --allow or --gates (the project's proof allowlist)")
        if args.command == "proof" and args.gates and in_repo(args.repo, args.gates) and not args.base:
            parser.error("proof --gates inside the repository needs --base: the allowlist is read as the base has it, "
                         "never from the PR head")
        args.cwd = args.cwd or str(args.repo)
        return proof(args) if args.command == "proof" else feat_proofs(args)
    if args.command == "dod" and not args.review and (args.repo / "REVIEW.md").is_file():
        args.review = str(args.repo / "REVIEW.md")
    return {"red": red, "scope": scope, "dod": dod}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
