"""check_docs_structure.py (KIT-074): README rules, done/INDEX.md rules, exemptions, parameters from the sdd block."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/check_docs_structure.py", "platforms/ci/validations/check_spec.py")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_docs_structure as cds  # noqa: E402

SCRIPT = HERE / "check_docs_structure.py"
GOOD = "# a/ — a\n\nScope: a.\n\n## What goes here\n\n- a\n\n## What does not go here\n\n- b\n"


class Repo:
    def __init__(self, test):
        self.td = tempfile.TemporaryDirectory()
        test.addCleanup(self.td.cleanup)
        self.path = Path(self.td.name)
        subprocess.run(["git", "-C", self.td.name, "init", "-q"], check=True)

    def write(self, rel, text="x\n", stage=True):
        path = self.path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        if stage:
            subprocess.run(["git", "-C", self.td.name, "add", rel], check=True)

    def run(self, exempt=(), **kwargs):
        return cds.check(self.path, list(exempt), **kwargs)

    def cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(self.path), *args],
                              capture_output=True, text=True, check=False, env=dict(os.environ, CI=""))

    def spec(self, block):
        self.write("docs/spec/spec.md", f"---\nid: SPEC\ntitle: x\nsdd:\n{block}---\n\n# Spec\n")


class ReadmeRules(unittest.TestCase):
    def test_missing_readme_fails(self):
        r = Repo(self)
        r.write("docs/a.md")
        _, fails = r.run()
        self.assertEqual(fails, ["FAIL: docs/ has no README.md"])

    def test_readme_needs_title_and_both_headings(self):
        self.assertEqual(cds.readme_problems(GOOD), [])
        self.assertIn("does not start with a `# ` title", cds.readme_problems("Intro\n" + GOOD))
        self.assertEqual(cds.readme_problems("# a\n\n## What goes here\n"),
                         ["lacks the heading `## What does not go here`"])

    def test_a_heading_may_carry_more_words(self):
        self.assertEqual(cds.readme_problems("# a\n\n## What goes here (and why)\n\n## What does not go here\n"), [])

    def test_the_headings_are_a_parameter(self):
        self.assertEqual(cds.readme_problems("# a\n\n## Purpose\n", headings=("## Purpose",)), [])
        self.assertEqual(cds.readme_problems(GOOD, headings=("## Purpose",)), ["lacks the heading `## Purpose`"])
        self.assertEqual(cds.readme_problems("# a\n", headings=()), [])

    def test_root_is_never_required(self):
        r = Repo(self)
        r.write("README.md", "no headings\n")
        self.assertEqual(r.run(), ([], []))

    def test_exempt_globs(self):
        r = Repo(self)
        r.write("tools/x/tests/fixtures/a.json")
        r.write("tools/x/README.md", GOOD)
        r.write("tools/README.md", GOOD)
        req, fails = r.run(["**/tests", "**/tests/**"])
        self.assertEqual(req, ["tools", "tools/x"])
        self.assertEqual(fails, [])

    def test_slash_star_star_keeps_the_folder_itself_required(self):
        r = Repo(self)
        r.write("game/legacy/client/a.ls")
        r.write("game/README.md", GOOD)
        req, fails = r.run(["game/legacy/**"])
        self.assertEqual(req, ["game", "game/legacy"])
        self.assertEqual(fails, ["FAIL: game/legacy/ has no README.md"])

    def test_the_readme_is_read_from_the_index(self):
        # a sparse checkout has no file on disk; an unstaged edit is not a gate input
        r = Repo(self)
        r.write("docs/README.md", GOOD)
        r.write("docs/README.md", "no title\n", stage=False)
        self.assertEqual(r.run()[1], [])
        (r.path / "docs" / "README.md").unlink()
        self.assertEqual(r.run()[1], [])

    def test_kit_generated_folders_and_dot_github_itself_are_exempt(self):
        # .github/README.md would replace the root README on the repository page, so .github itself is exempt;
        # its subfolders are not
        r = Repo(self)
        r.write(".claude/settings.json", "{}\n")
        r.write(".claude/rules/guardrails-java.md")
        r.write(".claude/skills/testing/SKILL.md")
        r.write(".github/merge-drivers/keyed_csv_merge.py")
        r.write(".github/CODEOWNERS")
        r.write(".github/workflows/ci.yml")
        req, fails = r.run()
        self.assertEqual(req, [".github/workflows"])
        self.assertEqual(fails, ["FAIL: .github/workflows/ has no README.md"])

    def test_a_spec_lint_folder_is_the_projects_since_the_kit_stopped_writing_it(self):
        # KIT-081 stage 1: sync-project.sh no longer generates .github/spec-lint/ and removes the copy it wrote, so a
        # folder still there holds the project's own files and says what belongs in it
        r = Repo(self)
        r.write(".github/spec-lint/pr-gates.json", "{}\n")
        req, fails = r.run()
        self.assertEqual(req, [".github/spec-lint"])
        self.assertEqual(fails, ["FAIL: .github/spec-lint/ has no README.md"])

    def test_a_folder_outside_the_generated_ones_under_claude_is_still_required(self):
        r = Repo(self)
        r.write(".claude/settings.json", "{}\n")
        r.write(".claude/agents/x.md")
        self.assertEqual(r.run()[1], ["FAIL: .claude/agents/ has no README.md"])


class IndexRules(unittest.TestCase):
    def test_done_needs_an_index_listing_every_child(self):
        r = Repo(self)
        r.write("docs/README.md", GOOD)
        r.write("docs/done/README.md", GOOD)
        r.write("docs/done/a.md")
        r.write("docs/done/sub/b.md")
        _, fails = r.run(["**/done/**"])
        self.assertEqual(fails, ["FAIL: docs/done/ has no INDEX.md"])
        r.write("docs/done/INDEX.md", "| [`a.md`](a.md) |\n")
        _, fails = r.run(["**/done/**"])
        self.assertEqual(fails, ["FAIL: docs/done/INDEX.md does not list `sub`"])
        r.write("docs/done/INDEX.md", "| [`a.md`](a.md) |\n| [`sub/`](sub/) |\n")
        self.assertEqual(r.run(["**/done/**"])[1], [])

    def test_done_index_can_be_turned_off(self):
        r = Repo(self)
        r.write("docs/README.md", GOOD)
        r.write("docs/done/README.md", GOOD)
        r.write("docs/done/a.md")
        self.assertEqual(r.run(["**/done/**"], done_index=False)[1], [])

    def test_an_exempt_done_folder_needs_no_index(self):
        r = Repo(self)
        r.write("docs/README.md", GOOD)
        r.write("docs/done/a.md")
        self.assertEqual(r.run(["docs/done"])[1], [])


class ExemptFile(unittest.TestCase):
    LAYER = "unit"  # in-process: no subprocess, no git

    def test_comments_and_blank_lines_are_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "exempt.txt"
            path.write_text("# a comment\n\n**/tests\n  **/tests/**  \n", encoding="utf-8")
            self.assertEqual(cds.load_exempt(path), ["**/tests", "**/tests/**"])

    def test_a_missing_file_exempts_nothing(self):
        self.assertEqual(cds.load_exempt(Path("/nonexistent/exempt.txt")), [])


class Cli(unittest.TestCase):
    def test_without_a_spec_the_check_is_off(self):
        r = Repo(self)
        r.write("docs/a.md")
        result = r.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("doc-structure: off", result.stdout)

    def test_off_by_default_in_the_sdd_block(self):
        r = Repo(self)
        r.spec("  tracker: none\n")
        r.write("tools/a.py")
        result = r.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("doc-structure: off", result.stdout)

    def test_enabled_reports_every_failure_and_exits_1(self):
        r = Repo(self)
        r.spec("  doc_structure:\n    enabled: true\n")
        r.write("docs/README.md", GOOD)
        r.write("docs/spec/README.md", GOOD)
        r.write("tools/a.py")
        r.write("tools/done/README.md", GOOD)
        r.write("tools/done/old.md")
        result = r.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL: tools/ has no README.md", result.stdout)
        self.assertIn("FAIL: tools/done/ has no INDEX.md", result.stdout)
        self.assertIn("doc-structure: 4 authored folders, 2 failure(s)", result.stdout)

    def test_parameters_come_from_the_sdd_block(self):
        r = Repo(self)
        r.spec("  doc_structure:\n    enabled: true\n    exempt: docs/exempt.txt\n"
               "    headings: ['## Purpose']\n    done_index: false\n")
        r.write("docs/README.md", "# docs\n\n## Purpose\n")
        r.write("docs/exempt.txt", "docs/spec\n")
        r.write("docs/done/README.md", "# done\n\n## Purpose\n")
        r.write("docs/done/old.md")
        result = r.cli("--list")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.splitlines()[:2], ["docs", "docs/done"])
        self.assertIn("doc-structure: 2 authored folders, 0 failure(s)", result.stdout)

    def test_a_missing_exempt_file_is_named(self):
        r = Repo(self)
        r.spec("  doc_structure:\n    enabled: true\n    exempt: docs/nope.txt\n")
        r.write("docs/README.md", GOOD)
        result = r.cli()
        self.assertIn("doc-structure: no exempt file at docs/nope.txt", result.stdout)
        self.assertEqual(result.returncode, 1)  # docs/spec has no README and nothing exempts it

    def test_an_invalid_block_is_a_usage_error(self):
        r = Repo(self)
        r.spec("  doc_structure:\n    enabled: true\n    headings: ['What goes here']\n")
        result = r.cli()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("doc_structure.headings", result.stdout + result.stderr)

    def test_resolved_defaults(self):
        r = Repo(self)
        r.spec("  doc_structure:\n    enabled: true\n")
        params = cds.params(r.path / "docs" / "spec")
        self.assertEqual(params, {"enabled": True, "exempt": ".github/doc-structure-exempt.txt",
                                  "headings": ["## What goes here", "## What does not go here"],
                                  "done_index": True})
        json.dumps(params)


if __name__ == "__main__":
    unittest.main()
