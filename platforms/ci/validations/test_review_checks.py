"""review_checks.py (KIT-069): the mechanical review steps a reviewer reads instead of redoing by hand — the Red check
(the PR's tests fail on base and pass on head), Files scope with `## Files widened`, the PR body and proof re-run, and
the grep-able DoD lines of a project REVIEW.md, and the re-run of a FEAT's task proofs. The Red classifier follows the
KIT-069 calibration: an assertion failure, or a compile error on a symbol the PR adds, is Red; a test-only PR is exempt;
a runtime error, all tests passing on base and a data-only Red are flagged for the reviewer, not blocked. Each test
builds a throwaway Git repository."""
import os
import subprocess
import sys
import tempfile
import textwrap
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
FAKE_GODOT = "#!/bin/sh\necho 'ERROR: Can\'t load script: tools/build.gd'\nexit 0\n"

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
- No focused or skipped test (`testing` § 2). <!-- grep tests: \\.only\\(|@Disabled|unittest\\.skip -->

## Docs
- No TODO left behind (`code-standards` § 4). <!-- grep: \\bTODO\\b -->
- CHANGELOG `Unreleased` entry (`code-standards` § 9).
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


class ToolCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(Path(self.tmp.name) / "game")
        self.base = self.repo.commit("base", **{"calc.py": CALC, "tests__test_add.py": TEST_ADD,
                                                "README.md": "readme\n"})

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, *argv, path_prefix=None):
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        if path_prefix:
            env["PATH"] = f"{path_prefix}{os.pathsep}{env['PATH']}"
        done = subprocess.run([sys.executable, str(TOOL), "--repo", str(self.repo.root), *argv],
                              capture_output=True, text=True, env=env, timeout=120)
        return done.returncode, done.stdout + done.stderr

    def worktrees(self):
        return git(self.repo.root, "worktree", "list", "--porcelain").count("worktree ")


class RedTest(ToolCase):
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


class ProofTest(ToolCase):
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

    def test_run_without_an_allowlist_is_a_usage_error(self):
        code, out = self.run_tool("proof", "--body", self.body(), "--run")
        self.assertEqual(code, 2, out)


class ProofOutputTest(ToolCase):
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

    def test_project_patterns_extend_the_stack_table(self):
        patterns = Path(self.tmp.name) / "patterns.json"
        patterns.write_text('{"python": {"fail_output": ["DEPRECATED"]}}', encoding="utf-8")
        code, out = self.run_tool("proof", "--body", self.body("python3 -c \"print('DEPRECATED api')\""), "--run",
                                  "--allow", "python3", "--patterns", str(patterns), "--cwd", str(self.repo.root))
        self.assertEqual(code, 1, out)
        self.assertIn("DEPRECATED", out)

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

    def test_rows_filter_runs_only_the_named_rows(self):
        code, out = self.proofs("--rows", "T1")
        self.assertEqual(code, 0, out)
        self.assertIn("feat-proofs: OK", out)
        self.assertNotIn("T2", out)


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

    def test_removed_assertion_is_reported(self):
        head = self.repo.commit("loosen", **{"tests__test_add.py": TEST_ADD.replace(
            "        self.assertEqual(calc.add(0, 0), 0)\n", "")})
        code, out = self.dod(head)
        self.assertEqual(code, 1, out)
        self.assertIn("tests/test_add.py", out)
        self.assertIn("assertion", out)


if __name__ == "__main__":
    unittest.main()
