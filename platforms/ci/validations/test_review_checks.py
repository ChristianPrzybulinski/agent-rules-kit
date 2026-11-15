"""review_checks.py (KIT-069): the mechanical review steps a reviewer reads instead of redoing by hand — the Red check
(the PR's tests fail on base and pass on head), Files scope with `## Files widened`, the PR body and proof re-run, and
the grep-able DoD lines of a project REVIEW.md. Each test builds a throwaway Git repository."""
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

    def run_tool(self, *argv):
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        done = subprocess.run([sys.executable, str(TOOL), "--repo", str(self.repo.root), *argv],
                              capture_output=True, text=True, env=env, timeout=120)
        return done.returncode, done.stdout + done.stderr

    def worktrees(self):
        return git(self.repo.root, "worktree", "list", "--porcelain").count("worktree ")


class RedTest(ToolCase):
    def red(self, head):
        return self.run_tool("red", "--base", self.base, "--head", head, "--run", RUN)

    def test_new_test_fails_on_base_and_passes_on_head(self):
        head = self.repo.commit("sub", **{"calc.py": CALC_SUB, "tests__test_sub.py": TEST_SUB})
        code, out = self.red(head)
        self.assertEqual(code, 0, out)
        self.assertIn("red: OK", out)
        self.assertIn("tests/test_sub.py", out)
        self.assertIn("has no attribute 'sub'", out)  # the base failure excerpt the reviewer judges

    def test_new_test_that_already_passes_on_base_catches_nothing(self):
        head = self.repo.commit("add twice", **{"tests__test_add_again.py": TEST_ADD.replace("AddTest", "Again")})
        code, out = self.red(head)
        self.assertEqual(code, 1, out)
        self.assertIn("red: FAIL", out)
        self.assertIn("base passed", out)

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
