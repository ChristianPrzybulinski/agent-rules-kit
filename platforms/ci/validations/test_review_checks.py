"""review_checks.py (KIT-069): the mechanical review steps a reviewer reads instead of redoing by hand — the Red check
(the PR's tests fail on base and pass on head), Files scope with `## Files widened`, the PR body and proof re-run, and
the grep-able DoD lines of a project REVIEW.md, and the re-run of a FEAT's task proofs. The Red classifier follows the
KIT-069 calibration: an assertion failure, or a compile error on a symbol the PR adds, is Red; a test-only PR is exempt;
a runtime error, all tests passing on base and a data-only Red are flagged for the reviewer, not blocked. Each test
builds a throwaway Git repository."""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent.parent / "tools" / "review_checks.py"
RUN = f"{sys.executable} -B -m unittest -q {{tests}}"

CALC = "def add(a, b):\n    return a + b\n"
CALC_SUB = CALC + "\n\ndef sub(a, b):\n    return a - b\n"
TEST_ADD = """\
import unittest
import calc


class AddTest(unittest.TestCase):
    def test_add(self):
        self.assertEqual(calc.add(2, 3), 5)
        self.assertEqual(calc.add(0, 0), 0)
"""
TEST_SUB = """\
import unittest
import calc


class SubTest(unittest.TestCase):
    def test_sub(self):
        self.assertEqual(calc.sub(5, 3), 2)
"""

CALC_MUL_BUG = CALC + "\n\ndef mul(a, b):\n    return a + b\n"
CALC_MUL = CALC + "\n\ndef mul(a, b):\n    return a * b\n"
TEST_MUL = """\
import unittest
import calc


class MulTest(unittest.TestCase):
    def test_mul(self):
        self.assertEqual(calc.mul(2, 3), 6)
"""
# A failure message that carries another runner's report, as a test of a CLI tool does: its separator, case header,
# missing-symbol line and summary belong to no test of this run.
TEST_MUL_NESTED = """\
import unittest
import calc

INNER = (
    "======================================================================\\n"
    "ERROR: test_ghost (ghosts.test_ghost.GhostTest)\\n"
    "----------------------------------------------------------------------\\n"
    "AttributeError: module 'calc' has no attribute 'ghost'\\n"
    "\\n"
    "FAILED (errors=1)\\n"
)


class MulTest(unittest.TestCase):
    def test_mul(self):
        self.assertEqual(calc.mul(2, 3), 6, INNER)
"""
CALC_FIRST_BUG = CALC + "\n\ndef first(xs):\n    return xs[1]\n"
CALC_FIRST = CALC + "\n\ndef first(xs):\n    return xs[0]\n"
TEST_FIRST = """\
import unittest
import calc


class FirstTest(unittest.TestCase):
    def test_first(self):
        self.assertEqual(calc.first([7]), 7)
"""
KNOWN = "KNOWN = {{{names}}}\n\n\ndef known(name):\n    return name in KNOWN\n"
TEST_NAMES = """\
import unittest
import known

NAMES = [{names}]


class NamesTest(unittest.TestCase):
    def test_names(self):
        for name in NAMES:
            self.assertTrue(known.known(name), name)
"""
# A stand-in build: it fails to compile the test until the PR's class exists, then passes.
BUILD = """\
import pathlib
import sys
if not pathlib.Path("src/Widget.java").exists():
    print("[ERROR] src/test/WidgetTest.java:[3,8] cannot find symbol")
    print("  symbol:   class {symbol}")
    print("  location: class WidgetTest")
    sys.exit(1)
print("Tests run: 1, Failures: 0")
"""
# A stand-in runner that writes a JUnit report: one assertion failure and one error on base, both pass on head.
JUNIT_RUN = """\
import pathlib
import sys
ok = pathlib.Path("src/Widget.java").exists()
failed = ('<testcase classname="WidgetTest" name="sums"><failure message="expected: 3 but was: 2" '
          'type="org.opentest4j.AssertionFailedError">at WidgetTest.sums</failure></testcase>'
          '<testcase classname="WidgetTest" name="loads"><error message="boom" '
          'type="java.lang.NullPointerException">at WidgetTest.loads</error></testcase>')
passed = '<testcase classname="WidgetTest" name="sums"/><testcase classname="WidgetTest" name="loads"/>'
reports = pathlib.Path("reports")
reports.mkdir(exist_ok=True)
(reports / "TEST-WidgetTest.xml").write_text('<testsuite name="WidgetTest">' + (passed if ok else failed) + '</testsuite>')
sys.exit(0 if ok else 1)
"""
WIDGET_TEST = "class WidgetTest { @Test void sums() { assertEquals(3, new Widget().sum()); } }\n"
# Stand-ins for a Maven and a gdUnit run from the gates config's `red` entries: each prints the arguments and folder it
# got, then fails to compile until the PR's class exists.
MVN_STUB = """\
#!/usr/bin/env python3
import pathlib
import sys
print("args: " + " ".join(sys.argv[1:]))
print("cwd: " + pathlib.Path.cwd().name)
if not pathlib.Path("src/main/Widget.java").exists():
    print("[ERROR] src/test/WidgetTest.java:[3,8] cannot find symbol")
    print("  symbol:   class Widget")
    sys.exit(1)
print("Tests run: 2, Failures: 0")
"""
GODOT_STUB = """\
#!/usr/bin/env python3
import pathlib
import sys
print("args: " + " ".join(sys.argv[1:]))
if not pathlib.Path("scripts/widget.gd").exists():
    print('SCRIPT ERROR: Parse Error: Identifier "Widget" not declared in the current scope.')
    sys.exit(1)
print("2 tests passed")
"""
GD_TEST = "extends GdUnitTestSuite\n\n\nfunc test_{name}():\n\tassert_that(Widget.new()).is_not_null()\n"
FAKE_GODOT = "#!/bin/sh\necho \"ERROR: Can't load script: tools/build.gd\"\nexit 0\n"

BODY = """\
## What

Adds sub.

## Red

`tests/test_sub.py::test_sub` failed on base: `AttributeError: module 'calc' has no attribute 'sub'`.

## Proof

```proof
{proof}
```

Executor: provider=codex tier=high session={session}
"""

REVIEW = """\
# Review instructions

## Correctness
- No focused or skipped test (rule `tests`). <!-- grep tests: \\.only\\(|@Disabled|unittest\\.skip -->

## Docs
- No TODO left behind (rule `code`). <!-- grep: \\bTODO\\b -->
- CHANGELOG `Unreleased` entry (`sdd-implement` reference `living-docs.md`).
"""


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()


class Repo:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True)
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.email", "fixture@example.invalid")
        git(root, "config", "user.name", "fixture")
        git(root, "config", "commit.gpgsign", "false")

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, message, **files):
        for rel, text in files.items():
            self.write(rel.replace("__", "/"), text)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", message)
        return git(self.root, "rev-parse", "HEAD")


def symlink_commit(repo, rel, target, message, **files):
    """Commit `rel` replaced by a symlink to `target` (None deletes it), plus `files`."""
    path = repo.root / rel
    path.unlink()
    if target is not None:
        os.symlink(target, path)
    return repo.commit(message, **files)


def link_folder_commit(repo, rel, target, message, **files):
    """Commit the folder `rel` replaced by a symlink to `target`, plus `files`."""
    shutil.rmtree(repo.root / rel)
    os.symlink(target, repo.root / rel)
    return repo.commit(message, **files)


class ToolCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(Path(self.tmp.name) / "game")
        self.base = self.repo.commit("base", **{"calc.py": CALC, "tests__test_add.py": TEST_ADD,
                                                "README.md": "readme\n"})

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, *argv, path_prefix=None, repo=None, cwd=None, env_extra=None):
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env_extra or {})}
        if path_prefix:
            env["PATH"] = f"{path_prefix}{os.pathsep}{env['PATH']}"
        done = subprocess.run([sys.executable, str(TOOL), "--repo", repo or str(self.repo.root), *argv],
                              capture_output=True, text=True, env=env, timeout=120, cwd=cwd)
        return done.returncode, done.stdout + done.stderr

    def worktrees(self):
        return git(self.repo.root, "worktree", "list", "--porcelain").count("worktree ")


class StubCase(ToolCase):
    def stub(self, name, text):
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir(exist_ok=True)
        (bin_dir / name).write_text(text, encoding="utf-8")
        (bin_dir / name).chmod(0o755)
        return str(bin_dir)

    def gates(self, config, name="gates.json"):
        path = Path(self.tmp.name) / name
        path.write_text(json.dumps(config), encoding="utf-8")
        return str(path)


class RedTest(StubCase):
    def red(self, head, *extra, base=None, run=RUN):
        return self.run_tool("red", "--base", base or self.base, "--head", head, "--run", run, *extra)

    def test_missing_symbol_the_pr_adds_is_red(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB, "tests__test_sub.py": TEST_SUB})
        code, out = self.red(head)
        self.assertEqual(code, 0, out)
        self.assertIn("red: OK", out)
        self.assertIn("tests/test_sub.py", out)
        self.assertIn("new-symbol (sub)", out)
        self.assertIn("has no attribute 'sub'", out)  # the base excerpt the reviewer reads

    def test_assertion_failure_on_base_is_red(self):
        base = self.repo.commit("mul bug", **{"calc.py": CALC_MUL_BUG})
        head = self.repo.commit("mul fix", **{"calc.py": CALC_MUL, "tests__test_mul.py": TEST_MUL})
        code, out = self.red(head, base=base)
        self.assertEqual(code, 0, out)
        self.assertIn("red: OK", out)
        self.assertIn("test_mul", out)
        self.assertIn("assertion", out)

    def test_unittest_summary_line_is_not_read_as_a_test(self):
        base = self.repo.commit("mul bug", **{"calc.py": CALC_MUL_BUG})
        head = self.repo.commit("mul fix", **{"calc.py": CALC_MUL, "tests__test_mul.py": TEST_MUL})
        code, out = self.red(head, base=base)
        self.assertEqual(code, 0, out)
        self.assertIn("FAILED (failures=1)", out)  # the base excerpt still shows it
        self.assertNotIn("red: test (failures=1)", out)
        self.assertIn("red: OK — 1 of 1 failing tests", out)

    def nested(self):
        base = self.repo.commit("mul bug", **{"calc.py": CALC_MUL_BUG})
        head = self.repo.commit("mul fix", **{"calc.py": CALC_MUL, "tests__test_mul.py": TEST_MUL_NESTED})
        return self.red(head, base=base)

    def test_failure_is_classed_by_its_assertion_not_by_text_in_its_message(self):
        code, out = self.nested()
        self.assertEqual(code, 0, out)
        self.assertIn("MulTest.test_mul: assertion", out)
        self.assertNotIn("missing-symbol (ghost)", out)

    def test_another_runner_report_inside_a_message_adds_no_test(self):
        code, out = self.nested()
        self.assertEqual(code, 0, out)
        self.assertNotIn("red: test ghosts.", out)
        self.assertNotIn("red: test (errors=1)", out)
        self.assertIn("red: OK — 1 of 1 failing tests", out)

    def red_gates(self, head, gates, *extra, path_prefix=None):
        return self.run_tool("red", "--base", self.base, "--head", head, "--gates", gates, *extra,
                             path_prefix=path_prefix)

    def test_classes_placeholder_runs_maven_from_its_folder_with_comma_joined_names(self):
        bin_dir = self.stub("fakemvn", MVN_STUB)
        gates = self.gates({"red": [{"glob": "server/src/test/**/*Test.java", "cwd": "server",
                                     "command": "fakemvn -q test -Dtest={classes}"}]})
        head = self.repo.commit("widget", **{
            "server__src__main__Widget.java": "public class Widget { int sum() { return 3; } }\n",
            "server__src__test__WidgetTest.java": WIDGET_TEST,
            "server__src__test__GadgetTest.java": WIDGET_TEST.replace("WidgetTest", "GadgetTest")})
        code, out = self.red_gates(head, gates, path_prefix=bin_dir)
        self.assertIn("args: -q test -Dtest=GadgetTest,WidgetTest", out)
        self.assertIn("cwd: server", out)
        self.assertEqual(code, 0, out)
        self.assertIn("new-symbol (Widget)", out)

    def test_class_names_are_shell_quoted(self):
        bin_dir = self.stub("fakemvn", MVN_STUB)
        gates = self.gates({"red": [{"glob": "server/src/test/**/*Test.java", "cwd": "server",
                                     "command": "fakemvn -q test -Dtest={classes}"}]})
        head = self.repo.commit("widget", **{
            "server__src__main__Widget.java": "public class Widget { int sum() { return 3; } }\n",
            "server__src__test__Widget$CaseTest.java": WIDGET_TEST.replace("WidgetTest", "Widget$CaseTest")})
        code, out = self.red_gates(head, gates, path_prefix=bin_dir)
        self.assertIn("args: -q test -Dtest=Widget$CaseTest", out)
        self.assertEqual(code, 0, out)

    def test_prefixed_res_placeholder_gives_gdunit_one_flag_per_file(self):
        bin_dir = self.stub("fakegodot", GODOT_STUB)
        gates = self.gates({"red": [{"glob": "client/test/**/*_test.gd", "cwd": "client",
                                     "command": "fakegodot --headless --path . {-a res}"}]})
        head = self.repo.commit("widget", **{
            "client__scripts__widget.gd": "class_name Widget\nextends RefCounted\n",
            "client__test__a_test.gd": GD_TEST.format(name="a"),
            "client__test__b_test.gd": GD_TEST.format(name="b")})
        code, out = self.red_gates(head, gates, path_prefix=bin_dir)
        self.assertIn("args: --headless --path . -a res://test/a_test.gd -a res://test/b_test.gd", out)
        self.assertEqual(code, 0, out)
        self.assertIn("new-symbol (Widget)", out)

    def test_a_no_test_line_quoted_in_a_failure_message_is_not_the_run_s_own(self):
        """Dogfood on 8535425: a test of a runner quotes the inner run's `Ran 0 tests` in its assertion message."""
        quoted = TEST_MUL_NESTED.replace('"FAILED (errors=1)\\n"', '"Ran 0 tests in 0.000s\\n\\nOK\\n"')
        base = self.repo.commit("mul bug", **{"calc.py": CALC_MUL_BUG})
        head = self.repo.commit("mul fix", **{"calc.py": CALC_MUL, "tests__test_mul.py": quoted})
        code, out = self.red(head, base=base)
        self.assertIn("Ran 0 tests", out)  # the quoted line is in the base excerpt
        self.assertNotIn("red: ERROR", out)
        self.assertEqual(code, 0, out)
        self.assertIn("MulTest.test_mul: assertion", out)

    def test_tests_no_red_entry_covers_need_run(self):
        gates = self.gates({"red": [{"glob": "server/**/*Test.java", "cwd": "server", "command": "fakemvn {classes}"}]})
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB, "tests__test_sub.py": TEST_SUB})
        code, out = self.red_gates(head, gates)
        self.assertEqual(code, 2, out)
        self.assertIn("tests/test_sub.py", out)
        self.assertIn("--run", out)

    def test_a_command_that_cannot_start_is_an_error_not_a_head_failure(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB, "tests__test_sub.py": TEST_SUB})
        code, out = self.red(head, run="no-such-runner {tests}")
        self.assertEqual(code, 2, out)
        self.assertIn("red: ERROR", out)
        self.assertIn("no test ran", out)
        self.assertNotIn("head failed", out)

    def test_a_run_that_collects_no_test_is_an_error(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB, "tests__test_sub.py": TEST_SUB})
        code, out = self.red(head, run=f"{sys.executable} -B -m unittest -q -k no_such_test {{tests}}")
        self.assertEqual(code, 2, out)
        self.assertIn("red: ERROR", out)
        self.assertIn("no test ran", out)

    def test_runtime_error_only_is_flagged_not_blocked(self):
        base = self.repo.commit("first bug", **{"calc.py": CALC_FIRST_BUG})
        head = self.repo.commit("first fix", **{"calc.py": CALC_FIRST, "tests__test_first.py": TEST_FIRST})
        code, out = self.red(head, base=base)
        self.assertEqual(code, 3, out)
        self.assertIn("red: FLAG", out)
        self.assertIn("runtime", out)

    def test_every_test_passing_on_base_despite_a_production_change_is_flagged(self):
        head = self.repo.commit("sub, add test only", **{
            "calc.py": CALC_SUB, "tests__test_add_again.py": TEST_ADD.replace("AddTest", "Again")})
        code, out = self.red(head)
        self.assertEqual(code, 3, out)
        self.assertIn("red: FLAG", out)
        self.assertIn("every test passes on base", out)

    def test_red_made_only_of_data_entries_is_flagged(self):
        base = self.repo.commit("names", **{"known.py": KNOWN.format(names="'a', 'b'"),
                                             "tests__test_names.py": TEST_NAMES.format(names="'a', 'b'")})
        head = self.repo.commit("add c", **{"known.py": KNOWN.format(names="'a', 'b', 'c'"),
                                             "tests__test_names.py": TEST_NAMES.format(names="'a', 'b', 'c'")})
        code, out = self.red(head, base=base)
        self.assertEqual(code, 3, out)
        self.assertIn("red: FLAG", out)
        self.assertIn("data", out)

    def test_test_only_pr_is_exempt_without_a_run(self):
        before = self.worktrees()
        head = self.repo.commit("more tests", **{"tests__test_add_again.py": TEST_ADD.replace("AddTest", "Again")})
        code, out = self.red(head)
        self.assertEqual(code, 0, out)
        self.assertIn("red: EXEMPT", out)
        self.assertIn("not run", out)
        self.assertEqual(self.worktrees(), before)

    def test_compile_error_on_a_symbol_the_pr_adds_is_red(self):
        base = self.repo.commit("build", **{"build.py": BUILD.format(symbol="Widget")})
        head = self.repo.commit("widget", **{"src__Widget.java": "public class Widget { int sum() { return 3; } }\n",
                                              "src__test__WidgetTest.java": WIDGET_TEST})
        code, out = self.red(head, base=base, run=f"{sys.executable} build.py")
        self.assertEqual(code, 0, out)
        self.assertIn("new-symbol (Widget)", out)

    def test_compile_error_on_a_symbol_the_pr_does_not_add_is_flagged(self):
        base = self.repo.commit("build", **{"build.py": BUILD.format(symbol="Gadget")})
        head = self.repo.commit("widget", **{"src__Widget.java": "public class Widget { int sum() { return 3; } }\n",
                                              "src__test__WidgetTest.java": WIDGET_TEST})
        code, out = self.red(head, base=base, run=f"{sys.executable} build.py")
        self.assertEqual(code, 3, out)
        self.assertIn("missing-symbol (Gadget)", out)

    def test_junit_reports_give_a_class_per_test(self):
        base = self.repo.commit("runner", **{"junit_run.py": JUNIT_RUN})
        head = self.repo.commit("widget", **{"src__Widget.java": "public class Widget { int sum() { return 3; } }\n",
                                              "src__test__WidgetTest.java": WIDGET_TEST})
        code, out = self.red(head, "--junit", "reports/*.xml", base=base, run=f"{sys.executable} junit_run.py")
        self.assertEqual(code, 0, out)
        self.assertIn("WidgetTest.sums: assertion", out)
        self.assertIn("WidgetTest.loads: runtime", out)

    def test_new_test_that_fails_on_head_is_reported(self):
        head = self.repo.commit("wrong sub", **{"calc.py": CALC_SUB.replace("a - b", "a + b"),
                                                 "tests__test_sub.py": TEST_SUB})
        code, out = self.red(head)
        self.assertEqual(code, 1, out)
        self.assertIn("head failed", out)

    def test_no_test_file_changed_asks_for_the_red_exception(self):
        head = self.repo.commit("code only", **{"calc.py": CALC_SUB})
        code, out = self.red(head)
        self.assertEqual(code, 1, out)
        self.assertIn("red: NONE", out)
        self.assertIn("## Red", out)

    def test_worktrees_are_removed_even_when_the_check_fails(self):
        head = self.repo.commit("wrong sub", **{"calc.py": CALC_SUB.replace("a - b", "a + b"),
                                                 "tests__test_sub.py": TEST_SUB})
        before = self.worktrees()
        self.red(head)
        self.assertEqual(self.worktrees(), before)

    def test_a_deleted_test_file_is_not_run_on_base(self):
        self.repo.commit("drop add test", **{"calc.py": CALC_SUB, "tests__test_sub.py": TEST_SUB})
        git(self.repo.root, "rm", "-q", "tests/test_add.py")
        git(self.repo.root, "commit", "-q", "-m", "rm")
        code, out = self.red(git(self.repo.root, "rev-parse", "HEAD"))
        self.assertEqual(code, 0, out)
        self.assertIn("red: OK", out)
        self.assertNotIn("test_add.py", out)


class ScopeTest(ToolCase):
    def scope(self, head, *extra):
        return self.run_tool("scope", "--base", self.base, "--head", head,
                             "--files", "calc.py", "tests/test_sub.py", *extra)

    def body(self, text):
        path = Path(self.tmp.name) / "body.md"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_paths_inside_files_pass(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB, "tests__test_sub.py": TEST_SUB,
                                          "changelog.d__sub.added.md": "- sub\n"})
        code, out = self.scope(head)
        self.assertEqual(code, 0, out)
        self.assertIn("scope: OK", out)

    def test_a_path_outside_files_fails(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB, "README.md": "changed\n"})
        code, out = self.scope(head)
        self.assertEqual(code, 1, out)
        self.assertIn("scope: FAIL", out)
        self.assertIn("README.md", out)

    def loosened_scope(self, target):
        """The base config names `.uid` as a generated suffix; the head replaces it and adds `calc.py.bak`."""
        base = self.repo.commit("gates", **{"gates.json": json.dumps({"generated_neighbours": [".uid"]})})
        head = symlink_commit(self.repo, "gates.json", target, "gates", **{"calc.py": CALC_SUB, "calc.py.bak": CALC})
        return self.run_tool("scope", "--base", base, "--head", head, "--files", "calc.py", "gates.json",
                             "--gates", str(self.repo.root / "gates.json"))

    def assert_base_gates_apply(self, code, out):
        self.assertEqual(code, 1, out)
        self.assertIn("calc.py.bak is outside Files", out)

    def test_a_deleted_gates_file_still_applies_its_base_rules(self):
        self.assert_base_gates_apply(*self.loosened_scope(None))

    def test_a_gates_file_linked_to_dev_null_still_applies_its_base_rules(self):
        self.assert_base_gates_apply(*self.loosened_scope("/dev/null"))

    def test_a_gates_file_linked_outside_the_repo_cannot_loosen_scope(self):
        loose = Path(self.tmp.name) / "loose.json"
        loose.write_text(json.dumps({"generated_neighbours": [".bak"]}), encoding="utf-8")
        self.assert_base_gates_apply(*self.loosened_scope(str(loose)))

    def test_a_move_out_of_a_protected_folder_fails_scope_and_names_the_old_path(self):
        base = self.repo.commit("core", **{"protected__core.py": CALC})
        (self.repo.root / "allowed").mkdir()
        (self.repo.root / "protected/core.py").rename(self.repo.root / "allowed/core.py")
        head = self.repo.commit("move core")
        gates = Path(self.tmp.name) / "gates.json"
        gates.write_text(json.dumps({"protected_paths": {"core-change": ["protected/**"]}}), encoding="utf-8")
        code, out = self.run_tool("scope", "--base", base, "--head", head, "--files", "allowed/**", "--gates", str(gates))
        self.assertEqual(code, 1, out)
        self.assertIn("protected/core.py is outside Files", out)
        self.assertIn("protected: protected/core.py needs label core-change", out)

    def test_a_widened_test_moved_into_files_with_a_changed_assertion_goes_back_to_a_stop(self):
        (self.repo.root / "tests/test_add.py").unlink()
        head = self.repo.commit("move and loosen", **{"calc.py": CALC_SUB, "tests__test_add_more.py":
                                                      TEST_ADD.replace("(0, 0), 0", "(0, 0), 1")})
        body = self.body("## Files widened\n\n- `tests/test_add.py`: imports calc, which changed\n")
        code, out = self.run_tool("scope", "--base", self.base, "--head", head, "--files", "calc.py",
                                  "tests/test_add_more.py", "--body", body)
        self.assertEqual(code, 1, out)
        self.assertIn("tests/test_add.py: widened test changes an assertion", out)

    def test_widened_existing_test_path_passes(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB,
                                          "tests__test_add.py": TEST_ADD + "\n# reads calc.sub too\n"})
        body = self.body("## Files widened\n\n- `tests/test_add.py`: imports calc, which changed\n")
        code, out = self.scope(head, "--body", body)
        self.assertEqual(code, 0, out)
        self.assertIn("widened: tests/test_add.py", out)

    def test_widening_a_path_that_is_not_an_existing_test_fails(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB, "README.md": "changed\n"})
        body = self.body("## Files widened\n\n- `README.md`: mentions sub\n")
        code, out = self.scope(head, "--body", body)
        self.assertEqual(code, 1, out)
        self.assertIn("README.md is not an existing test path", out)

    def test_widened_test_with_a_changed_assertion_goes_back_to_a_stop(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB,
                                          "tests__test_add.py": TEST_ADD.replace("(0, 0), 0", "(0, 0), 1")})
        body = self.body("## Files widened\n\n- `tests/test_add.py`: imports calc\n")
        code, out = self.scope(head, "--body", body)
        self.assertEqual(code, 1, out)
        self.assertIn("assertion", out)
        self.assertIn("tests/test_add.py", out)


class ProofTest(StubCase):
    def body(self, proof="python3 -c \"print('ok')\"", session="019a2b3c-4d5e"):
        path = Path(self.tmp.name) / "body.md"
        path.write_text(BODY.format(proof=proof, session=session), encoding="utf-8")
        return str(path)

    def test_complete_body_passes_without_running(self):
        code, out = self.run_tool("proof", "--body", self.body())
        self.assertEqual(code, 0, out)
        self.assertIn("proof: OK", out)
        self.assertIn("provider=codex", out)

    def test_missing_executor_line_fails(self):
        path = Path(self.body())
        path.write_text(path.read_text().replace("Executor: provider=codex tier=high session=019a2b3c-4d5e", ""))
        code, out = self.run_tool("proof", "--body", str(path))
        self.assertEqual(code, 1, out)
        self.assertIn("Executor:", out)

    def test_placeholder_session_fails(self):
        code, out = self.run_tool("proof", "--body", self.body(session="<session-id>"))
        self.assertEqual(code, 1, out)
        self.assertIn("session", out)

    def test_missing_red_section_fails(self):
        path = Path(self.body())
        path.write_text(path.read_text().replace("## Red", "## Notes"))
        code, out = self.run_tool("proof", "--body", str(path))
        self.assertEqual(code, 1, out)
        self.assertIn("## Red", out)

    def test_run_reruns_each_allowlisted_line(self):
        proof = "python3 -c \"print('first')\"\npython3 -c \"import sys; sys.exit(3)\""
        code, out = self.run_tool("proof", "--body", self.body(proof), "--run", "--allow", "python3",
                                  "--cwd", str(self.repo.root))
        self.assertEqual(code, 1, out)
        self.assertIn("exit 0", out)
        self.assertIn("exit 3", out)

    def test_run_skips_a_line_outside_the_allowlist(self):
        proof = "ls -la"
        code, out = self.run_tool("proof", "--body", self.body(proof), "--run", "--allow", "python3")
        self.assertEqual(code, 1, out)
        self.assertIn("not run", out)
        self.assertIn("'ls' not in allowlist", out)

    def test_a_single_ampersand_separates_commands(self):
        code, out = self.run_tool("proof", "--body", self.body("python3 -c \"print(1)\" & uname -n"), "--run",
                                  "--allow", "python3", "--cwd", str(self.repo.root))
        self.assertEqual(code, 1, out)
        self.assertIn("'uname' not in allowlist", out)
        self.assertNotIn("→ exit", out)

    def test_the_head_cannot_widen_its_own_allowlist(self):
        base = self.repo.commit("gates", **{"gates.json": json.dumps({"proof_allowlist": ["python3"]})})
        self.repo.commit("widen", **{"gates.json": json.dumps({"proof_allowlist": ["python3", "uname"]})})
        gates = str(self.repo.root / "gates.json")
        code, out = self.run_tool("proof", "--body", self.body("uname -n"), "--run", "--gates", gates, "--base", base,
                                  "--cwd", str(self.repo.root))
        self.assertEqual(code, 1, out)
        self.assertIn("'uname' not in allowlist", out)
        code, out = self.run_tool("proof", "--body", self.body("uname -n"), "--run", "--gates", gates)
        self.assertEqual(code, 2, out)  # a rules file inside the repository needs --base
        self.assertIn("--base", out)

    def test_timeout_kills_the_shell_and_its_children(self):
        proof = "sh -c 'sleep 30 & echo $! > child.pid; wait'"
        code, out = self.run_tool("proof", "--body", self.body(proof), "--run", "--allow", "sh", "--timeout", "1",
                                  "--cwd", str(self.repo.root))
        self.assertEqual(code, 1, out)
        self.assertIn("timeout", out)
        pid = int((self.repo.root / "child.pid").read_text())
        alive, deadline = True, time.time() + 5
        while alive and time.time() < deadline:
            try:
                os.kill(pid, 0)
                time.sleep(0.1)
            except ProcessLookupError:
                alive = False
        if alive:
            os.kill(pid, 9)
        self.assertFalse(alive, "the shell's child outlived the timeout")

    def signalled(self, sig):
        """Send `sig` to the tool while its proof run's shell waits on a child; (tool exit, child still alive)."""
        proof = "sh -c 'sleep 30 & echo $! > child.pid; wait'"
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        tool = subprocess.Popen([sys.executable, str(TOOL), "--repo", str(self.repo.root), "proof", "--body",
                                 self.body(proof), "--run", "--allow", "sh", "--timeout", "60",
                                 "--cwd", str(self.repo.root)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                env=env)
        pid_file, deadline = self.repo.root / "child.pid", time.time() + 20
        while not (pid_file.exists() and pid_file.read_text().strip()) and time.time() < deadline:
            time.sleep(0.1)
        pid = int(pid_file.read_text())
        pid_file.unlink()
        tool.send_signal(sig)
        tool.communicate(timeout=20)
        alive, deadline = True, time.time() + 5
        while alive and time.time() < deadline:
            try:
                os.kill(pid, 0)
                time.sleep(0.1)
            except ProcessLookupError:
                alive = False
        if alive:
            os.kill(pid, 9)
        return tool.returncode, alive

    def test_an_interrupt_kills_the_shell_and_its_children(self):
        _, alive = self.signalled(signal.SIGINT)
        self.assertFalse(alive, "the shell's child outlived the interrupt")

    def test_a_supervisor_s_terminate_or_hangup_kills_the_shell_and_its_children(self):
        """A loop timeout kills the tool's group, which no longer holds the run (it has its own session)."""
        for sig in (signal.SIGTERM, signal.SIGHUP):
            with self.subTest(signal=sig.name):
                code, alive = self.signalled(sig)
                self.assertFalse(alive, f"the shell's child outlived {sig.name}")
                self.assertEqual(code, 128 + sig)

    def test_output_that_is_not_utf8_is_read_not_a_crash(self):
        code, out = self.run_tool("proof", "--body",
                                  self.body('python3 -c "import sys; sys.stdout.buffer.write(bytes([255, 10]))"'),
                                  "--run", "--allow", "python3", "--cwd", str(self.repo.root))
        self.assertNotIn("Traceback", out)
        self.assertEqual(code, 0, out)
        self.assertIn("→ exit 0", out)

    def test_a_quiet_redirect_of_both_streams_is_allowed(self):
        code, out = self.run_tool("proof", "--body", self.body("python3 -c \"print('quiet')\" &>/dev/null"), "--run",
                                  "--allow", "python3", "--cwd", str(self.repo.root))
        self.assertEqual(code, 0, out)
        self.assertIn("→ exit 0", out)

    def test_run_without_an_allowlist_is_a_usage_error(self):
        code, out = self.run_tool("proof", "--body", self.body(), "--run")
        self.assertEqual(code, 2, out)


class ProofOutputTest(StubCase):
    """Proof re-run checks shared by `proof --run` and `feat-proofs`: paths exist before the run, a stack's output
    pattern fails a run that exits 0, a stack lint flags a command that cannot prove what it names."""

    def body(self, proof):
        path = Path(self.tmp.name) / "body.md"
        path.write_text(BODY.format(proof=proof, session="019a2b3c-4d5e"), encoding="utf-8")
        return str(path)

    def test_missing_path_is_reported_and_not_run(self):
        code, out = self.run_tool("proof", "--body", self.body("python3 tools/content-projection/check.py"),
                                  "--run", "--allow", "python3", "--cwd", str(self.repo.root))
        self.assertEqual(code, 1, out)
        self.assertIn("tools/content-projection/check.py does not exist", out)
        self.assertNotIn("exit 2", out)

    def test_godot_output_pattern_fails_a_run_that_exits_0(self):
        self.repo.commit("tool", **{"tools__build.gd": "extends SceneTree\n"})
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir()
        (bin_dir / "godot").write_text(FAKE_GODOT)
        (bin_dir / "godot").chmod(0o755)
        code, out = self.run_tool("proof", "--body", self.body("godot --headless --path . -s tools/build.gd"),
                                  "--run", "--allow", "godot", "--cwd", str(self.repo.root), path_prefix=str(bin_dir))
        self.assertEqual(code, 1, out)
        self.assertIn("exit 0", out)
        self.assertIn("Can't load script", out)

    def test_res_path_resolves_against_the_godot_project_folder(self):
        self.repo.commit("tool", **{"godotproj__tools__build.gd": "extends SceneTree\n"})
        bin_dir = self.stub("godot", "#!/bin/sh\necho built\nexit 0\n")
        proof = ("godot --headless --path godotproj -s res://tools/build.gd\n"
                 "godot --headless --path=godotproj -s res://tools/missing.gd")
        code, out = self.run_tool("proof", "--body", self.body(proof), "--run", "--allow", "godot",
                                  "--cwd", str(self.repo.root), path_prefix=bin_dir)
        self.assertEqual(code, 1, out)
        self.assertIn("res://tools/build.gd → exit 0", out)
        self.assertIn("godotproj/tools/missing.gd does not exist", out)
        self.assertNotIn("tools/build.gd does not exist", out)

    def test_project_patterns_extend_the_stack_table(self):
        patterns = Path(self.tmp.name) / "patterns.json"
        patterns.write_text('{"python": {"fail_output": ["DEPRECATED"]}}', encoding="utf-8")
        code, out = self.run_tool("proof", "--body", self.body("python3 -c \"print('DEPRECATED api')\""), "--run",
                                  "--allow", "python3", "--patterns", str(patterns), "--cwd", str(self.repo.root))
        self.assertEqual(code, 1, out)
        self.assertIn("DEPRECATED", out)

    def test_a_head_edit_to_an_in_repo_patterns_file_is_ignored(self):
        """The patterns file is a rules file: the head turning off the python stack must not hide a Traceback."""
        base = self.repo.commit("patterns", **{"patterns.json": '{"python": {"fail_output": ["NEVER-PRINTED"]}}'})
        head = self.repo.commit("loosen", **{"patterns.json": '{"python": {"command": "$^"}}'})
        argv = ["proof", "--body", self.body("python3 -c \"print('Traceback (most recent call last):')\""), "--run",
                "--allow", "python3", "--patterns", str(self.repo.root / "patterns.json"), "--cwd", str(self.repo.root)]
        code, out = self.run_tool(*argv, "--base", base)
        self.assertEqual(code, 1, out)
        self.assertIn("Traceback", out)
        code, out = self.run_tool(*argv)  # no base to read it from: refused, never read from the head
        self.assertEqual(code, 2, out)
        self.assertIn("--patterns inside the repository needs --base", out)
        self.assertEqual(head, git(self.repo.root, "rev-parse", "HEAD"))

    def test_maven_dtest_with_verify_is_linted_without_running(self):
        code, out = self.run_tool("proof", "--body", self.body("./mvnw -B -ntp -Dtest=HaircutBuyIT verify"))
        self.assertEqual(code, 1, out)
        self.assertIn("-Dtest", out)
        self.assertIn("verify", out)


FEAT_PROOFS = """\
---
id: FEAT-001
title: "Fixture feature"
status: in-progress
requirements: []
created: "2026-11-01"
---

# FEAT-001

## Tasks

| ID | Task | Files | Proof of completion | Status |
|---|---|---|---|---|
| T1 | adds sub | `calc.py` | `python3 -c "import calc; assert calc.sub(3, 1) == 2"` | done |
| T2 | old importer | `tools/**` | `python3 tools/projection/check.py` | done |
| T3 | screen | `ui/**` | evidence: screen shop-haircut, owner approves | done |
| T4 | replaced | `x/**` | `python3 -c "import sys; sys.exit(1)"` | superseded |
"""


class FeatProofsTest(ToolCase):
    def setUp(self):
        super().setUp()
        self.repo.commit("sub", **{"calc.py": CALC_SUB})
        self.feat = Path(self.tmp.name) / "FEAT-001.md"
        self.feat.write_text(FEAT_PROOFS, encoding="utf-8")

    def proofs(self, *extra):
        return self.run_tool("feat-proofs", "--feat", str(self.feat), "--run", "--allow", "python3",
                             "--cwd", str(self.repo.root), *extra)

    def test_each_row_proof_reruns_and_stale_ones_are_found(self):
        code, out = self.proofs()
        self.assertEqual(code, 1, out)
        self.assertIn("T1", out)
        self.assertIn("exit 0", out)
        self.assertIn("T2: tools/projection/check.py does not exist", out)
        self.assertIn("T3: not run (no command", out)
        self.assertIn("T4: superseded", out)
        self.assertNotIn("exit 1", out)

    def test_cancelled_row_is_skipped_like_a_superseded_one(self):
        cancelled = "| T5 | dropped | `y/**` | `python3 -c \"import sys; sys.exit(1)\"` | cancelled |\n"
        self.feat.write_text(FEAT_PROOFS + cancelled, encoding="utf-8")
        code, out = self.proofs("--rows", "T5")
        self.assertEqual(code, 0, out)
        self.assertIn("T5: cancelled, skipped", out)

    def test_rows_filter_runs_only_the_named_rows(self):
        code, out = self.proofs("--rows", "T1")
        self.assertEqual(code, 0, out)
        self.assertIn("feat-proofs: OK", out)
        self.assertNotIn("T2", out)


class RulesFromBaseTest(ToolCase):
    """A rules file inside the repository is read as base has it however its path is spelled (an alias folder, a
    relative or `../` path) and whatever the head did to it (edited, deleted, a link to /dev/null or outside); a file
    outside the repository is read from disk; a file base lacks applies no rule. One matrix for `dod` and `scope`."""
    STRICT_REVIEW, LOOSE_REVIEW = REVIEW, REVIEW.replace(" <!-- grep: \\bTODO\\b -->", "")
    STRICT_GATES, LOOSE_GATES = json.dumps({"generated_neighbours": [".uid"]}), json.dumps({"generated_neighbours": [".bak"]})
    KINDS = {  # kind: rules file, base text, loosened text, the head's code change, the base rules' outcome
        "dod": ("REVIEW.md", STRICT_REVIEW, LOOSE_REVIEW, {"calc.py": CALC_SUB + "\n# TODO: handle overflow\n"},
                (1, "No TODO left behind")),
        "scope": ("gates.json", STRICT_GATES, LOOSE_GATES, {"calc.py": CALC_SUB, "calc.py.bak": CALC},
                  (1, "calc.py.bak is outside Files")),
    }
    CASES = ("alias", "alias-deleted", "relative", "dotdot", "leaf-dev-null", "leaf-outside", "deleted", "edit",
             "outside", "first-pr", "parent-outside", "parent-in-repo", "parent-absent", "grandparent")

    def run_case(self, kind, case):
        rules, strict, loose, code, _ = self.KINDS[kind]
        tmp = Path(self.tmp.name)
        self.repo = Repo(tmp / f"{kind}-{case}")
        root = self.repo.root
        # a file outside the repository: the loosened rules, except for `outside`, where its rules must show
        outside = tmp / f"{kind}-{case}-{rules}"
        outside.write_text((strict if kind == "dod" else loose) if case == "outside" else loose, encoding="utf-8")
        # the parent cases keep the rules in a folder the head relinks: outside, to a looser in-repo folder, to a folder
        # base lacks, or one level up (the grandparent)
        nested = case.startswith(("parent", "grandparent"))
        rel = f"conf/sub/{rules}" if case == "grandparent" else f"conf/{rules}" if nested else rules
        folder = tmp / f"{kind}-{case}-folder"
        (folder / "sub").mkdir(parents=True)
        (folder / rules).write_text(loose, encoding="utf-8")
        (folder / "sub" / rules).write_text(loose, encoding="utf-8")
        base_files = {"calc.py": CALC, "tests__test_add.py": TEST_ADD}
        if case not in ("outside", "first-pr"):
            base_files[rel] = strict
        if case == "parent-in-repo":
            base_files[f"looser/{rules}"] = loose
        base = self.repo.commit("base", **base_files)
        links = {"leaf-dev-null": "/dev/null", "leaf-outside": str(outside), "deleted": None, "alias-deleted": None}
        folders = {"parent-outside": str(folder), "parent-in-repo": "looser", "parent-absent": "fresh",
                   "grandparent": str(folder)}
        if case in folders:
            extra = {f"fresh/{rules}": loose} if case == "parent-absent" else {}
            head = link_folder_commit(self.repo, "conf", folders[case], case, **extra, **code)
        elif case in links:
            head = symlink_commit(self.repo, rules, links[case], case, **code)
        elif case == "outside":
            head = self.repo.commit(case, **code)
        else:  # the head writes the rules that would flip the outcome if the tool read them
            flip = strict if (case == "first-pr" and kind == "dod") else loose
            head = self.repo.commit(case, **{rules: flip}, **code)
        repo, cwd, path = str(root), None, str(root / rel)
        if case.startswith("alias"):
            alias = tmp / f"{case}-{kind}"
            os.symlink(tmp, alias)
            repo, cwd, path = ".", str(root), str(alias / root.name / rules)
        elif case == "relative":
            repo, cwd, path = ".", str(root), rules
        elif case == "dotdot":
            repo, cwd, path = "..", str(root / "tests"), f"../{rules}"
        elif case == "outside":
            path = str(outside)
        argv = (["dod", "--base", base, "--head", head, "--review", path] if kind == "dod" else
                ["scope", "--base", base, "--head", head, "--files", "calc.py", rel, "conf", "conf/**", "fresh/**",
                 "--gates", path])
        return self.run_tool(*argv, repo=repo, cwd=cwd)

    def expected(self, kind, case):
        if case == "outside":
            return (1, "No TODO left behind") if kind == "dod" else (0, "scope: OK")
        if case == "first-pr":
            return (0, "is not on base") if kind == "dod" else (1, "calc.py.bak is outside Files")
        return self.KINDS[kind][4]

    def check_matrix(self, kind):
        for case in self.CASES:
            with self.subTest(kind=kind, case=case):
                code, out = self.run_case(kind, case)
                self.assertNotIn("Traceback", out)
                want_code, want_text = self.expected(kind, case)
                self.assertEqual(code, want_code, out)
                self.assertIn(want_text, out)

    def test_dod_reads_its_rules_as_base_has_them(self):
        self.check_matrix("dod")

    def test_scope_reads_its_rules_as_base_has_them(self):
        self.check_matrix("scope")

    def test_a_rules_path_that_names_a_folder_is_a_usage_error(self):
        base = self.repo.commit("conf", **{"conf/keep.txt": "kept\n"})
        head = self.repo.commit("todo", **{"calc.py": CALC_SUB + "\n# TODO: handle overflow\n"})
        elsewhere = Path(self.tmp.name) / "elsewhere"
        elsewhere.mkdir()
        for name, path in (("in-repo", str(self.repo.root / "conf")), ("outside", str(elsewhere))):
            for argv in (["dod", "--review", path], ["scope", "--files", "calc.py", "--gates", path]):
                with self.subTest(folder=name, command=argv[0]):
                    code, out = self.run_tool(argv[0], "--base", base, "--head", head, *argv[1:])
                    self.assertNotIn("Traceback", out)
                    self.assertEqual(code, 2, out)


class RulesErrorTest(ToolCase):
    """A rules file base holds but the tool cannot read is a usage error (exit 2), never a crash read as a finding."""

    def proof_body(self, proof):
        body = Path(self.tmp.name) / "proof-body.md"
        body.write_text(BODY.format(proof=proof, session="019a2b3c-4d5e"), encoding="utf-8")
        return str(body)

    def test_a_base_that_is_not_a_commit_is_a_usage_error_for_gates(self):
        self.repo.commit("gates", **{"r__gates.json": json.dumps({"proof_allowlist": ["python3"]})})
        code, out = self.run_tool("proof", "--body", self.proof_body("python3 -c \"print('ok')\""), "--run",
                                  "--gates", str(self.repo.root / "r/gates.json"), "--base", "no-such-ref",
                                  "--cwd", str(self.repo.root))
        self.assertEqual(code, 2, out)
        self.assertIn("no-such-ref", out)
        self.assertNotIn("is not on base", out)

    def test_a_base_that_is_not_a_commit_never_drops_the_patterns(self):
        """A shallow CI clone without the base commit must not run the proof without base's fail_output."""
        self.repo.commit("patterns", **{"patterns.json": json.dumps({"python": {"fail_output": ["SENTINEL"]}})})
        code, out = self.run_tool("proof", "--body", self.proof_body("python3 -c \"print('SENTINEL')\""), "--run",
                                  "--allow", "python3", "--patterns", str(self.repo.root / "patterns.json"),
                                  "--base", "no-such-ref", "--cwd", str(self.repo.root))
        self.assertEqual(code, 2, out)
        self.assertIn("no-such-ref", out)

    def test_a_repo_that_is_not_a_git_repository_is_a_usage_error(self):
        plain = Path(self.tmp.name) / "plain"
        plain.mkdir()
        (plain / "gates.json").write_text(json.dumps({"proof_allowlist": ["python3"]}), encoding="utf-8")
        code, out = self.run_tool("proof", "--body", self.proof_body("python3 -c \"print('ok')\""), "--run",
                                  "--gates", str(plain / "gates.json"), "--base", "1a2b3c4", "--cwd", str(plain),
                                  repo=str(plain))
        self.assertEqual(code, 2, out)
        self.assertIn("not a git repository", out)
    CASES = {  # case: rules file, its text at base, the command that reads it
        "gates-not-json": ("gates.json", "{bad", "scope"),
        "gates-not-an-object": ("gates.json", "[]", "scope"),
        "review-bad-pattern": ("REVIEW.md", "## Docs\n- Broken. <!-- grep: ( -->\n", "dod"),
        "patterns-not-json": ("patterns.json", "{bad", "proof"),
        "patterns-stack-not-an-object": ("patterns.json", '{"python": []}', "proof"),
    }

    def test_a_malformed_base_rules_file_is_a_usage_error(self):
        body = Path(self.tmp.name) / "body.md"
        body.write_text(BODY.format(proof="python3 -c \"print('ok')\"", session="019a2b3c-4d5e"), encoding="utf-8")
        for name, (rel, text, command) in self.CASES.items():
            with self.subTest(case=name):
                self.repo = Repo(Path(self.tmp.name) / name)
                base = self.repo.commit("base", **{"calc.py": CALC, rel: text})
                head = self.repo.commit("head", **{"calc.py": CALC_SUB})
                path = str(self.repo.root / rel)
                argv = {"scope": ["scope", "--base", base, "--head", head, "--files", "calc.py", "--gates", path],
                        "dod": ["dod", "--base", base, "--head", head, "--review", path],
                        "proof": ["proof", "--body", str(body), "--run", "--allow", "python3", "--base", base,
                                  "--patterns", path, "--cwd", str(self.repo.root)]}[command]
                code, out = self.run_tool(*argv)
                self.assertNotIn("Traceback", out)
                self.assertEqual(code, 2, out)


class ConfigShapeTest(ToolCase):
    """A base config value of the wrong type is no finding: the tool exits 2 (a usage error, or a crash caught at the
    top), never the finding code 1."""
    CASES = {  # case: rules file, its JSON at base, how the command reads it
        "protected_paths-a-list": ("gates.json", {"protected_paths": []}, "scope"),
        "generated_neighbours-a-number": ("gates.json", {"generated_neighbours": 5}, "scope"),  # pr_gates.py
        "red-an-object": ("gates.json", {"red": {"glob": "tests/**"}}, "red"),
        "red-entry-without-glob": ("gates.json", {"red": [{"command": "true"}]}, "red"),
        "proof_allowlist-a-number": ("gates.json", {"proof_allowlist": 5}, "proof-gates"),
        "fail_output-a-number": ("patterns.json", {"python": {"fail_output": 5}}, "proof-patterns"),
        "fail_output-not-a-regex": ("patterns.json", {"python": {"fail_output": ["("]}}, "proof-patterns"),
        "lint-not-a-pair": ("patterns.json", {"python": {"lint": ["x"]}}, "proof-patterns"),
    }

    def test_a_base_config_value_of_the_wrong_type_exits_2(self):
        body = Path(self.tmp.name) / "body.md"
        body.write_text(BODY.format(proof="python3 -c \"print('ok')\"", session="019a2b3c-4d5e"), encoding="utf-8")
        for name, (rel, data, how) in self.CASES.items():
            with self.subTest(case=name):
                self.repo = Repo(Path(self.tmp.name) / name)
                base = self.repo.commit("base", **{"calc.py": CALC, "tests__test_add.py": TEST_ADD,
                                                   rel: json.dumps(data)})
                head = self.repo.commit("head", **{"calc.py": CALC_SUB, "tests__test_add.py": TEST_ADD
                                                   + "        self.assertEqual(calc.add(1, 1), 2)\n"})
                path, root = str(self.repo.root / rel), str(self.repo.root)
                # scope: tests/test_add.py is outside Files, so pr_gates.generated_neighbour reads the suffixes
                argv = {"scope": ["scope", "--base", base, "--head", head, "--files", "calc.py", "--gates", path],
                        "red": ["red", "--base", base, "--head", head, "--gates", path, "--run", "true"],
                        "proof-gates": ["proof", "--body", str(body), "--run", "--gates", path, "--base", base,
                                        "--cwd", root],
                        "proof-patterns": ["proof", "--body", str(body), "--run", "--allow", "python3", "--base", base,
                                           "--patterns", path, "--cwd", root]}[how]
                code, out = self.run_tool(*argv)
                self.assertEqual(code, 2, out)


class DiffVisibilityTest(ToolCase):
    """The head cannot decide what the checks see in the diff: an unusual file name, a diff attribute or a deletion."""

    def review(self):
        path = Path(self.tmp.name) / "REVIEW.md"
        path.write_text(REVIEW, encoding="utf-8")
        return str(path)

    def test_a_todo_in_a_file_with_an_unusual_name_fails_dod(self):
        names = ('a"b.py', "tab\tname.py", "ünï.py", "my file.py")
        for name in names:
            (self.repo.root / name).write_text("# TODO: decide the default\n", encoding="utf-8")
        head = self.repo.commit("odd names")
        code, out = self.run_tool("dod", "--base", self.base, "--head", head, "--review", self.review())
        self.assertEqual(code, 1, out)
        for name in names:
            with self.subTest(name=name):
                self.assertIn(f"Docs: {name}:1:", out)

    def test_a_diff_attribute_cannot_hide_lines_from_dod(self):
        for where in ("head", "base"):
            for attribute in ("*.py -diff", "*.py binary"):
                with self.subTest(where=where, attribute=attribute):
                    self.repo = Repo(Path(self.tmp.name) / f"{where}-{attribute.split()[1]}")
                    base_files = {"calc.py": CALC, "tests__test_add.py": TEST_ADD}
                    head_files = {"calc.py": CALC_SUB + "\n# TODO: handle overflow\n"}
                    (base_files if where == "base" else head_files)[".gitattributes"] = attribute + "\n"
                    base = self.repo.commit("base", **base_files)
                    head = self.repo.commit("todo", **head_files)
                    code, out = self.run_tool("dod", "--base", base, "--head", head, "--review", self.review())
                    self.assertEqual(code, 1, out)
                    self.assertIn("No TODO left behind", out)

    def test_a_diff_attribute_cannot_hide_a_changed_assertion_from_scope(self):
        base = self.repo.commit("attributes", **{".gitattributes": "*.py -diff\n"})
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB,
                                          "tests__test_add.py": TEST_ADD.replace("(0, 0), 0", "(0, 0), 1")})
        body = Path(self.tmp.name) / "body.md"
        body.write_text("## Files widened\n\n- `tests/test_add.py`: imports calc\n", encoding="utf-8")
        code, out = self.run_tool("scope", "--base", base, "--head", head, "--files", "calc.py", "--body", str(body))
        self.assertEqual(code, 1, out)
        self.assertIn("assertion", out)
        self.assertIn("tests/test_add.py", out)

    def test_an_added_line_that_looks_like_a_file_header_hides_nothing(self):
        """`++ x` added shows as `+++ x` in the diff: only the lines after `diff --git` are file headers."""
        head = self.repo.commit("notes", **{"notes.md": "++ hidden\n# TODO: decide the default\n"})
        code, out = self.run_tool("dod", "--base", self.base, "--head", head, "--review", self.review())
        self.assertEqual(code, 1, out)
        self.assertIn("Docs: notes.md:2:", out)

    def test_deleting_a_test_file_drops_its_assertions(self):
        head = symlink_commit(self.repo, "tests/test_add.py", None, "drop the test")
        code, out = self.run_tool("dod", "--base", self.base, "--head", head, "--review", self.review())
        self.assertEqual(code, 1, out)
        self.assertIn("tests/test_add.py: 2 assertion lines removed, 0 added", out)

    def test_renaming_a_test_file_keeps_its_assertions(self):
        (self.repo.root / "tests/test_add.py").rename(self.repo.root / "tests/test_plus.py")
        head = self.repo.commit("rename the test")
        code, out = self.run_tool("dod", "--base", self.base, "--head", head, "--review", self.review())
        self.assertEqual(code, 0, out)
        self.assertIn("dod: OK", out)

    def test_moving_a_test_file_out_of_the_test_globs_drops_its_assertions(self):
        (self.repo.root / "attic").mkdir()
        (self.repo.root / "tests/test_add.py").rename(self.repo.root / "attic/add_cases.py")
        head = self.repo.commit("move the test away")
        code, out = self.run_tool("dod", "--base", self.base, "--head", head, "--review", self.review())
        self.assertEqual(code, 1, out)
        self.assertIn("tests/test_add.py: 2 assertion lines removed, 0 added", out)

    def moved_away_while_base_moves_on(self, base_change):
        """The PR moves tests/test_add.py out of the test globs; base, after the fork, deletes or edits it."""
        git(self.repo.root, "checkout", "-q", "-b", "pr")
        (self.repo.root / "attic").mkdir()
        (self.repo.root / "tests/test_add.py").rename(self.repo.root / "attic/add_cases.py")
        head = self.repo.commit("move the test away")
        git(self.repo.root, "checkout", "-q", "main")
        if base_change == "deleted":
            (self.repo.root / "tests/test_add.py").unlink()
            base = self.repo.commit("base drops the test")
        else:
            base = self.repo.commit("base adds 2 assertions", **{"tests__test_add.py": TEST_ADD
                                    + "        self.assertEqual(calc.add(1, 1), 2)\n        self.assertTrue(calc.add)\n"})
        return self.run_tool("dod", "--base", base, "--head", head, "--review", self.review())

    def test_a_move_out_of_the_test_globs_reads_the_old_file_at_the_fork_when_base_deleted_it(self):
        code, out = self.moved_away_while_base_moves_on("deleted")
        self.assertNotIn("Traceback", out)
        self.assertEqual(code, 1, out)
        self.assertIn("tests/test_add.py: 2 assertion lines removed, 0 added", out)

    def test_a_move_out_of_the_test_globs_counts_the_old_file_at_the_fork_when_base_edited_it(self):
        code, out = self.moved_away_while_base_moves_on("edited")
        self.assertEqual(code, 1, out)
        self.assertIn("tests/test_add.py: 2 assertion lines removed, 0 added", out)

    def test_a_rule_anchored_at_the_line_end_sees_a_crlf_line(self):
        """Stratics' server files are CRLF: a rule ending in `$` must match the added line without its CR."""
        for number, rule in enumerate((r"TODO$", r"TODO[ \t]*$", r"^# TODO$")):
            with self.subTest(rule=rule):
                self.repo = Repo(Path(self.tmp.name) / f"crlf-{number}")
                (self.repo.root / "Server.java").write_bytes(b"int x = 1;\r\n")
                base = self.repo.commit("base")
                (self.repo.root / "Server.java").write_bytes(b"int x = 1;\r\n# TODO\r\n")
                head = self.repo.commit("todo")
                review = Path(self.tmp.name) / f"anchored-{number}.md"
                review.write_text(f"## Docs\n- No TODO left behind. <!-- grep: {rule} -->\n", encoding="utf-8")
                code, out = self.run_tool("dod", "--base", base, "--head", head, "--review", str(review))
                self.assertEqual(code, 1, out)
                self.assertIn("Docs: Server.java:2:", out)

    def test_a_cr_only_review_file_on_base_keeps_each_rule(self):
        rules = ("# Review\r\r## Docs\r- No TODO left behind. <!-- grep: \\bTODO\\b -->\r\r## Correctness\r"
                 "- No skipped test. <!-- grep tests: unittest\\.skip -->\r")
        base = self.repo.commit("cr-only rules", **{"REVIEW.md": rules})
        head = self.repo.commit("todo", **{"calc.py": CALC_SUB + "\n# TODO: handle overflow\n"})
        code, out = self.run_tool("dod", "--base", base, "--head", head, "--review", str(self.repo.root / "REVIEW.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("Docs: calc.py:", out)

    SEPARATORS = {"CR": "\r", "FF": "\x0c", "U+2028": "\u2028"}
    INJECTION = "x = 2  # {sep}diff --git a/n b/n"

    def injected(self, name, **head_files):
        """A fresh repository whose head adds a line holding a line separator then a fake diff header."""
        self.repo = Repo(Path(self.tmp.name) / name)
        base = self.repo.commit("base", **{"calc.py": CALC, "tests__test_add.py": TEST_ADD})
        return base, self.repo.commit("injected", **head_files)

    def test_a_line_separator_inside_an_added_line_hides_no_todo(self):
        for name, sep in self.SEPARATORS.items():
            with self.subTest(separator=name):
                base, head = self.injected(f"todo-{name}", **{"calc.py": CALC_SUB + "\n" + self.INJECTION.format(sep=sep)
                                                               + "\n# TODO: handle overflow\n"})
                code, out = self.run_tool("dod", "--base", base, "--head", head, "--review", self.review())
                self.assertEqual(code, 1, out)
                self.assertIn("No TODO left behind", out)

    def test_a_line_separator_inside_an_added_line_hides_no_dropped_assertion(self):
        for name, sep in self.SEPARATORS.items():
            with self.subTest(separator=name):
                test = TEST_ADD.replace("import calc\n", "import calc\n" + self.INJECTION.format(sep=sep) + "\n")
                test = test.replace("        self.assertEqual(calc.add(0, 0), 0)\n", "")
                base, head = self.injected(f"assert-{name}", **{"tests__test_add.py": test})
                code, out = self.run_tool("dod", "--base", base, "--head", head, "--review", self.review())
                self.assertEqual(code, 1, out)
                self.assertIn("tests/test_add.py: 1 assertion lines removed, 0 added", out)

    def test_a_line_separator_inside_an_added_line_hides_no_widened_assertion_from_scope(self):
        body = Path(self.tmp.name) / "body.md"
        body.write_text("## Files widened\n\n- `tests/test_add.py`: imports calc\n", encoding="utf-8")
        for name, sep in self.SEPARATORS.items():
            with self.subTest(separator=name):
                test = TEST_ADD.replace("import calc\n", "import calc\n" + self.INJECTION.format(sep=sep) + "\n")
                base, head = self.injected(f"scope-{name}", **{"tests__test_add.py": test.replace("(0, 0), 0", "(0, 0), 1")})
                code, out = self.run_tool("scope", "--base", base, "--head", head, "--files", "calc.py",
                                          "--body", str(body))
                self.assertEqual(code, 1, out)
                self.assertIn("widened test changes an assertion", out)

    def test_a_todo_in_a_cr_only_file_fails_dod(self):
        """Legacy files end lines with CR only (Stratics' client `.ls`): git sees one line, the TODO is in it."""
        (self.repo.root / "legacy.ls").write_bytes(b"first\rsecond\r# TODO: decide the default\r")
        head = self.repo.commit("legacy file")
        code, out = self.run_tool("dod", "--base", self.base, "--head", head, "--review", self.review())
        self.assertEqual(code, 1, out)
        self.assertIn("Docs: legacy.ls:1:", out)

    def test_a_reviewer_s_diff_prefix_config_hides_nothing(self):
        body = Path(self.tmp.name) / "body.md"
        body.write_text("## Files widened\n\n- `tests/test_add.py`: imports calc\n", encoding="utf-8")
        head = self.repo.commit("todo and a changed assertion", **{
            "calc.py": CALC_SUB + "\n# TODO: handle overflow\n",
            "tests__test_add.py": TEST_ADD.replace("(0, 0), 0", "(0, 0), 1")})
        for name, config in (("noprefix", "[diff]\n\tnoprefix = true\n"),
                             ("prefixes", "[diff]\n\tsrcPrefix = old/\n\tdstPrefix = new/\n")):
            with self.subTest(config=name):
                global_config = Path(self.tmp.name) / f"{name}.gitconfig"
                global_config.write_text(config, encoding="utf-8")
                env = {"GIT_CONFIG_GLOBAL": str(global_config)}
                code, out = self.run_tool("dod", "--base", self.base, "--head", head, "--review", self.review(),
                                          env_extra=env)
                self.assertEqual(code, 1, out)
                self.assertIn("No TODO left behind", out)
                code, out = self.run_tool("scope", "--base", self.base, "--head", head, "--files", "calc.py",
                                          "--body", str(body), env_extra=env)
                self.assertEqual(code, 1, out)
                self.assertIn("widened test changes an assertion", out)


class DiffDecodingTest(ToolCase):
    def test_a_diff_line_that_is_not_utf8_is_read_not_a_crash(self):
        (self.repo.root / "notes.txt").write_bytes(b"caf\xe9 TODO: decide the default\n")
        head = self.repo.commit("latin-1 notes")
        review = Path(self.tmp.name) / "REVIEW.md"
        review.write_text(REVIEW, encoding="utf-8")
        code, out = self.run_tool("dod", "--base", self.base, "--head", head, "--review", str(review))
        self.assertNotIn("Traceback", out)
        self.assertEqual(code, 1, out)
        self.assertIn("No TODO left behind", out)
        code, out = self.run_tool("scope", "--base", self.base, "--head", head, "--files", "notes.txt")
        self.assertNotIn("Traceback", out)
        self.assertEqual(code, 0, out)


class DodTest(ToolCase):
    def dod(self, head):
        review = Path(self.tmp.name) / "REVIEW.md"
        review.write_text(REVIEW, encoding="utf-8")
        return self.run_tool("dod", "--base", self.base, "--head", head, "--review", str(review))

    def test_clean_diff_has_no_finding(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB, "tests__test_sub.py": TEST_SUB})
        code, out = self.dod(head)
        self.assertEqual(code, 0, out)
        self.assertIn("dod: OK", out)

    def test_skipped_test_matches_its_review_line_with_section_and_line(self):
        skipped = TEST_SUB.replace("    def test_sub", "    @unittest.skip('later')\n    def test_sub")
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB, "tests__test_sub.py": skipped})
        code, out = self.dod(head)
        self.assertEqual(code, 1, out)
        self.assertIn("Correctness", out)
        self.assertIn("tests/test_sub.py:6", out)
        self.assertIn("No focused or skipped test", out)

    def test_tests_marker_ignores_production_files(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB + "\nNOTE = 'x.only(y)'\n"})
        code, out = self.dod(head)
        self.assertEqual(code, 0, out)

    def test_any_file_marker_fires_on_production_code(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB + "\n# TODO: handle overflow\n"})
        code, out = self.dod(head)
        self.assertEqual(code, 1, out)
        self.assertIn("Docs", out)
        self.assertIn("calc.py:", out)

    def test_the_head_cannot_loosen_its_own_review_rules(self):
        base = self.repo.commit("rules", **{"REVIEW.md": REVIEW})
        head = self.repo.commit("loosen", **{"REVIEW.md": REVIEW.replace(" <!-- grep: \\bTODO\\b -->", ""),
                                             "calc.py": CALC_SUB + "\n# TODO: handle overflow\n"})
        code, out = self.run_tool("dod", "--base", base, "--head", head, "--review", str(self.repo.root / "REVIEW.md"))
        self.assertEqual(code, 1, out)
        self.assertIn("calc.py:", out)
        self.assertIn("No TODO left behind", out)

    def rules_base(self):
        return self.repo.commit("rules", **{"REVIEW.md": REVIEW})

    def test_a_deleted_review_file_still_applies_its_base_rules(self):
        base = self.rules_base()
        head = symlink_commit(self.repo, "REVIEW.md", None, "drop rules",
                              **{"calc.py": CALC_SUB + "\n# TODO: handle overflow\n"})
        code, out = self.run_tool("dod", "--base", base, "--head", head)
        self.assertEqual(code, 1, out)
        self.assertIn("No TODO left behind", out)

    def test_a_review_file_linked_to_dev_null_still_applies_its_base_rules(self):
        base = self.rules_base()
        head = symlink_commit(self.repo, "REVIEW.md", "/dev/null", "null rules",
                              **{"calc.py": CALC_SUB + "\n# TODO: handle overflow\n"})
        for extra in ((), ("--review", str(self.repo.root / "REVIEW.md"))):
            with self.subTest(review=extra):
                code, out = self.run_tool("dod", "--base", base, "--head", head, *extra)
                self.assertEqual(code, 1, out)
                self.assertIn("No TODO left behind", out)

    def test_the_kit_review_template_has_no_rule_in_its_explanatory_sentence(self):
        template = Path(__file__).resolve().parents[2] / "kits" / "github" / "REVIEW.md"
        head = self.repo.commit("word", **{"calc.py": CALC_SUB + "\nPATTERN = 'REGEX'\n"})
        code, out = self.run_tool("dod", "--base", self.base, "--head", head, "--review", str(template))
        self.assertEqual(code, 0, out)
        markers = [line for line in template.read_text(encoding="utf-8").splitlines()
                   if re.search(r"<!--\s*grep(\s+tests)?:.*-->\s*$", line)]
        self.assertEqual(len(markers), 1)  # the Correctness line; the sentence that explains the marker is none
        self.assertIn("1 grep-able REVIEW.md lines", out)

    def test_removed_assertion_is_reported(self):
        head = self.repo.commit("loosen", **{"tests__test_add.py": TEST_ADD.replace(
            "        self.assertEqual(calc.add(0, 0), 0)\n", "")})
        code, out = self.dod(head)
        self.assertEqual(code, 1, out)
        self.assertIn("tests/test_add.py", out)
        self.assertIn("assertion", out)



# --------------------------------------------------------------------------- KIT-075: the #246 review follow-ups


def renamed_commit(repo, old, new, message, **files):
    """Commit `old` moved to `new` (content kept), plus `files`."""
    target = repo.root / new
    target.parent.mkdir(parents=True, exist_ok=True)
    (repo.root / old).rename(target)
    return repo.commit(message, **files)


class DodDiscoveryTest(StubCase):
    """#248: a test renamed out of its runner's discovery pattern (the gates `red` globs) keeps no assertion, even
    when the new name stays inside the broad test globs (`tests/**`)."""

    def dod(self, head, gates=None):
        review = Path(self.tmp.name) / "REVIEW.md"
        review.write_text(REVIEW, encoding="utf-8")
        gates = gates or self.gates({"red": [{"glob": "tests/test_*.py", "command": RUN}]})
        return self.run_tool("dod", "--base", self.base, "--head", head, "--review", str(review), "--gates", gates)

    def test_a_rename_the_runner_no_longer_collects_drops_its_assertions(self):
        head = renamed_commit(self.repo, "tests/test_add.py", "tests/test_add.py.off", "park the test")
        code, out = self.dod(head)
        self.assertEqual(code, 1, out)
        self.assertIn("tests/test_add.py: 2 assertion lines removed", out)

    def test_a_rename_that_stays_discoverable_drops_nothing(self):
        head = renamed_commit(self.repo, "tests/test_add.py", "tests/unit/test_add.py", "move the test")
        code, out = self.dod(head, self.gates({"red": [{"glob": "tests/**/test_*.py", "command": RUN}]}))
        self.assertEqual(code, 0, out)
        self.assertIn("no assertion dropped", out)


class FeatProofsHeadTest(ToolCase):
    """#249, the decision kept: `feat-proofs` runs on `main` after the merge, where HEAD is the trusted ref, so an
    in-repo --gates without --base is read as HEAD has it, never from the checkout."""

    def test_an_in_repo_gates_file_is_read_as_head_has_it(self):
        self.repo.commit("rules", **{"gates.json": json.dumps({"proof_allowlist": ["python3"]}), "calc.py": CALC_SUB})
        self.repo.write("gates.json", json.dumps({"proof_allowlist": ["grep"]}))  # an uncommitted edit
        feat = Path(self.tmp.name) / "FEAT-001.md"
        feat.write_text(FEAT_PROOFS, encoding="utf-8")
        code, out = self.run_tool("feat-proofs", "--feat", str(feat), "--rows", "T1", "--run",
                                  "--gates", str(self.repo.root / "gates.json"), "--cwd", str(self.repo.root))
        self.assertEqual(code, 0, out)
        self.assertIn("exit 0", out)


class FeatRowSeparatorTest(ToolCase):
    """#250: only "\n" ends a task row, so FF, NEL or U+2028 inside a cell keeps the row and its proof runs."""

    def test_a_row_holding_an_extra_separator_still_runs_its_proof(self):
        for sep in ("\x0c", "\x85", " "):
            with self.subTest(sep=repr(sep)):
                feat = Path(self.tmp.name) / "FEAT-001.md"
                row = f'| T1 | adds{sep}sub | `calc.py` | `python3 -c "import sys; sys.exit(1)"` | done |\n'
                feat.write_text(FEAT_PROOFS.split("| T1 |")[0] + row, encoding="utf-8")
                code, out = self.run_tool("feat-proofs", "--feat", str(feat), "--run", "--allow", "python3",
                                          "--cwd", str(self.repo.root))
                self.assertEqual(code, 1, out)
                self.assertIn("T1: ", out)
                self.assertIn("exit 1", out)


class BodyLineEndingTest(ToolCase):
    """#251: a PR body splits only on CommonMark line endings, so U+2028 cannot start a `## Files widened` heading
    GitHub does not render."""

    def test_a_heading_after_a_unicode_separator_widens_nothing(self):
        head = self.repo.commit("touch", **{"calc.py": CALC_SUB, "tests__test_add.py": TEST_ADD + "\n# touched\n"})
        for sep in (" ", "\x85", "\x0c"):
            with self.subTest(sep=repr(sep)):
                body = Path(self.tmp.name) / "body.md"
                body.write_text(f"## Notes{sep}## Files widened\n\n- `tests/test_add.py`: imports calc\n",
                                encoding="utf-8")
                code, out = self.run_tool("scope", "--base", self.base, "--head", head, "--files", "calc.py",
                                          "--body", str(body))
                self.assertEqual(code, 1, out)
                self.assertIn("tests/test_add.py is outside Files", out)


class ConfigTypeTest(ToolCase):
    """#252: a gates value of the wrong type that is still iterable (a string where a list belongs) exits 2 naming
    the key, instead of being read per character."""
    CASES = {  # case: gates JSON at base, how the command reads it, the key the message names
        "protected_paths-label-a-string": ({"protected_paths": {"core": "protected/**"}}, "scope", "protected_paths"),
        "generated_neighbours-a-string": ({"generated_neighbours": ".uid"}, "scope", "generated_neighbours"),
        "proof_allowlist-a-string": ({"proof_allowlist": "python3"}, "proof", "proof_allowlist"),
        "red-glob-a-list": ({"red": [{"glob": ["tests/**"], "command": "true"}]}, "red", "red"),
        "red-cwd-a-number": ({"red": [{"glob": "tests/**", "command": "true", "cwd": 5}]}, "red", "red"),
    }

    def test_a_wrong_but_iterable_value_exits_2_naming_its_key(self):
        body = Path(self.tmp.name) / "body.md"
        body.write_text(BODY.format(proof="python3 -c \"print('ok')\"", session="019a2b3c-4d5e"), encoding="utf-8")
        for name, (data, how, key) in self.CASES.items():
            with self.subTest(case=name):
                self.repo = Repo(Path(self.tmp.name) / name)
                base = self.repo.commit("base", **{"calc.py": CALC, "tests__test_add.py": TEST_ADD,
                                                   "gates.json": json.dumps(data)})
                head = self.repo.commit("head", **{"calc.py": CALC_SUB, "tests__test_add.py": TEST_ADD
                                                   + "        self.assertEqual(calc.add(1, 1), 2)\n"})
                path, root = str(self.repo.root / "gates.json"), str(self.repo.root)
                argv = {"scope": ["scope", "--base", base, "--head", head, "--files", "calc.py", "--gates", path],
                        "red": ["red", "--base", base, "--head", head, "--gates", path, "--run", "true"],
                        "proof": ["proof", "--body", str(body), "--run", "--gates", path, "--base", base,
                                  "--cwd", root]}[how]
                code, out = self.run_tool(*argv)
                self.assertEqual(code, 2, out)
                self.assertIn(key, out)
                self.assertNotIn("Traceback", out)


class PrInputFindingTest(StubCase):
    """#253: a failure the PR's own content causes is a finding naming the path (exit 1), not a crash (exit 2)."""

    def test_a_proof_path_too_long_for_the_file_system_is_a_finding(self):
        body = Path(self.tmp.name) / "body.md"
        long_path = f"tests/{'a' * 300}/check.py"
        body.write_text(BODY.format(proof=f"python3 {long_path}", session="019a2b3c-4d5e"), encoding="utf-8")
        code, out = self.run_tool("proof", "--body", str(body), "--run", "--allow", "python3",
                                  "--cwd", str(self.repo.root))
        self.assertEqual(code, 1, out)
        self.assertIn(long_path, out)
        self.assertNotIn("Traceback", out)

    def test_a_pr_test_under_a_path_that_is_a_file_on_base_is_a_finding(self):
        base = self.repo.commit("fixture file", **{"tests__fixtures": "data\n"})
        (self.repo.root / "tests" / "fixtures").unlink()
        head = self.repo.commit("fixture folder", **{"calc.py": CALC_SUB, "tests__fixtures__test_sub.py": TEST_SUB})
        code, out = self.run_tool("red", "--base", base, "--head", head, "--run", RUN)
        self.assertEqual(code, 1, out)
        self.assertIn("tests/fixtures/test_sub.py", out)
        self.assertNotIn("Traceback", out)
        self.assertEqual(self.worktrees(), 1)


class DodCrOnlyTest(ToolCase):
    """#254: a CR-only test file is one diff line, so its assertions are counted per CR line."""

    def test_an_assertion_dropped_from_a_cr_only_test_file_is_reported(self):
        cr = TEST_ADD.replace("\n", "\r")
        base = self.repo.commit("cr test", **{"tests__test_cr.py": cr})
        head = self.repo.commit("loosen", **{"tests__test_cr.py": cr.replace(
            "        self.assertEqual(calc.add(0, 0), 0)\r", "")})
        review = Path(self.tmp.name) / "REVIEW.md"
        review.write_text(REVIEW, encoding="utf-8")
        code, out = self.run_tool("dod", "--base", base, "--head", head, "--review", str(review))
        self.assertEqual(code, 1, out)
        self.assertIn("tests/test_cr.py: 2 assertion lines removed, 1 added", out)


class StartupErrorTest(ToolCase):
    """#255: a broken install and a non-positive --timeout are usage errors (exit 2), never the finding code 1."""

    def test_a_copy_without_pr_gates_exits_2(self):
        lone = Path(self.tmp.name) / "lone" / "tools"
        lone.mkdir(parents=True)
        shutil.copy(TOOL, lone / "review_checks.py")
        done = subprocess.run([sys.executable, "-I", "-B", str(lone / "review_checks.py"), "--repo",
                               str(self.repo.root), "dod", "--base", self.base, "--head", self.base],
                              capture_output=True, text=True, timeout=60, cwd=str(lone))
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertIn("pr_gates", done.stderr)
        self.assertNotIn("Traceback", done.stderr)

    def test_a_timeout_below_one_second_is_a_usage_error(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB, "tests__test_sub.py": TEST_SUB})
        for value in ("0", "-5"):
            with self.subTest(timeout=value):
                code, out = self.run_tool("red", "--base", self.base, "--head", head, "--run", RUN,
                                          "--timeout", value)
                self.assertEqual(code, 2, out)
                self.assertIn("--timeout", out)


if __name__ == "__main__":
    unittest.main()
