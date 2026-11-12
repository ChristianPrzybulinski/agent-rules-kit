"""check_kit.py: root files, optional folder READMEs and INDEX.md placement on a throwaway copy (KIT-042)."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
CHECK_KIT = "platforms/ci/validations/check_kit.py"


class CheckKitReadmesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.template = Path(cls.tmp.name) / "template"
        listed = subprocess.run(["git", "-C", str(KIT), "ls-files", "-z", "--cached", "--others",
                                 "--exclude-standard"], capture_output=True, text=True, check=True).stdout
        for rel in filter(None, listed.split("\0")):  # the working tree, so uncommitted edits count
            if (KIT / rel).is_file():
                (cls.template / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(KIT / rel, cls.template / rel)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.kit = Path(tempfile.mkdtemp(dir=self.tmp.name)) / "kit"
        shutil.copytree(self.template, self.kit)

    def check(self):
        return subprocess.run([sys.executable, "-B", str(self.kit / CHECK_KIT)],
                              capture_output=True, text=True, check=False)

    def test_the_copy_passes_and_a_folder_needs_no_readme(self):
        (self.kit / "docs" / "notes").mkdir()
        (self.kit / "docs" / "notes" / "a.md").write_text("# a\n", encoding="utf-8")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_each_violation_is_reported(self):
        (self.kit / "docs" / "INDEX.md").write_text("# docs\n", encoding="utf-8")
        (self.kit / "platforms" / "tools" / "unlisted_tool.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        (self.kit / "CONTRIBUTING.md").unlink()
        result = self.check()
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1)
        self.assertIn("docs/INDEX.md", output)
        self.assertIn("INDEX.md exists only at plugins/<name>/", output)
        self.assertIn("entry 'unlisted_tool.sh' does not appear in the index", output)
        self.assertIn("CONTRIBUTING.md: layout: required path missing", output)

if __name__ == "__main__":
    unittest.main()
