"""sync-project.sh --check: stale kit path scan on a throwaway repo."""
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent.parent / "tools" / "sync-project.sh"

STALE = "- agent-rules-kit `kits/java-maven/pom-parent.xml` requires [25,26)"


class SyncProjectCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        install = self.run_sync()  # install once: --check diffs the copied files
        self.assertEqual(install.returncode, 0, install.stdout + install.stderr)

    def tearDown(self):
        self.tmp.cleanup()

    def run_sync(self, *args):
        return subprocess.run(["bash", str(SCRIPT), *args, str(self.repo)],
                              capture_output=True, text=True, check=False)

    def write_md(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_clean_repo_passes(self):
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("consistent with kit", result.stdout)

    def test_stale_citation_fails(self):
        self.write_md("docs/spec/decisions/DTEC-001-x.md", "# DTEC-001\n\n" + STALE + "\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("stale kit path: docs/spec/decisions/DTEC-001-x.md:3", result.stdout)

    def test_opt_out_marker_passes(self):
        self.write_md("docs/spec/decisions/DTEC-001-x.md",
                      "# DTEC-001\n\n" + STALE + " <!-- kit-path-ok -->\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_false_positives(self):
        self.write_md("docs/ci.md", "CI runs platforms/kits/github/workflows/spec-lint.yml\n")
        self.write_md("docs/sessions/2026-01-01-x.md", "back then it was agents/skills/\n")
        self.write_md(".claude/skills/x/references/y.md", "a project knowledge/ folder\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_exclusion_matches_path_only(self):
        self.write_md("docs/x.md", "moved out of docs/legacy/ into agents/skills/\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("stale kit path: docs/x.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
