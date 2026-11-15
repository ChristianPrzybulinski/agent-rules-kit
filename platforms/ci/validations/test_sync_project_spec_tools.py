"""sync-project.sh vendors the spec tools (KIT-073): row_checks.py and pr_gates.py land in .github/spec-lint/ next
to check_spec.py, run from there, and --check reports a missing or edited copy."""
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent.parent / "tools" / "sync-project.sh"
KIT = SCRIPT.parents[2]

FEAT = """\
---
id: FEAT-001
title: "Fixture"
status: planned
requirements: []
created: "2026-11-15"
---

# FEAT-001

## Tasks

| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Model | Wave | Item |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | Add the tool | `README.md` | `docker exec x ls` | CA-1 | — | todo | Low | small | 0 | — |
"""


class VendoredSpecTools(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        (self.repo / "AGENTS.md").write_text("# x\n")
        (self.repo / "README.md").write_text("# x\n")
        spec = self.repo / "docs" / "spec"
        (spec / "features").mkdir(parents=True)
        (spec / "spec.md").write_text('---\nproject: "x"\nversion: "0.1.0"\nupdated: "2026-11-15"\n---\n')
        (spec / "features" / "FEAT-001.md").write_text(textwrap.dedent(FEAT))
        done = self.sync()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def sync(self, *args):
        return subprocess.run(["bash", str(SCRIPT), *args, str(self.repo)], capture_output=True, text=True,
                              check=False, env=dict(os.environ, CI=""))

    def test_the_tools_are_copied_byte_for_byte(self):
        for name in ("row_checks.py", "pr_gates.py", "check_spec.py"):
            copy = self.repo / ".github" / "spec-lint" / name
            self.assertTrue(copy.is_file(), name)
            self.assertEqual(copy.read_bytes(), (KIT / "platforms/ci/validations" / name).read_bytes(), name)

    def test_the_vendored_row_checks_run_from_the_copy(self):
        done = subprocess.run(["python3", ".github/spec-lint/row_checks.py", "check", "FEAT-001"], cwd=self.repo,
                              capture_output=True, text=True, check=False)
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("FEAT-001 T1: Proof of completion clause 1 'docker exec x ls' (forbidden construct) [e]",
                      done.stdout)

    def test_check_reports_a_missing_or_edited_copy(self):
        self.assertEqual(self.sync("--check").returncode, 0)
        copy = self.repo / ".github" / "spec-lint" / "row_checks.py"
        copy.write_text(copy.read_text() + "\n# edited\n")
        done = self.sync("--check")
        self.assertEqual(done.returncode, 1)
        self.assertIn("row_checks.py diverges from the kit", done.stdout)
        (self.repo / ".github" / "spec-lint" / "pr_gates.py").unlink()
        self.assertIn("pr_gates.py missing", self.sync("--check").stdout)


if __name__ == "__main__":
    unittest.main()
