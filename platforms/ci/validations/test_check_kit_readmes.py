"""check_kit.py on a throwaway copy: root files, optional folder READMEs and INDEX.md placement (KIT-042),
links that leave the plugin and skill descriptions without 'Not for' (KIT-052), and shell scripts the bash on
PATH cannot parse (KIT-060)."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
CHECK_KIT = "platforms/ci/validations/check_kit.py"
DOCTOR = "platforms/tools/doctor.sh"
# The heredoc doctor.sh feeds to python3 inside "$(...)" (KIT-010).
DOCTOR_HEREDOC = "\"$AUTO_COMPACT_WINDOW\" <<'PY'\n"


def bash_major():
    if shutil.which("bash") is None:
        return None
    result = subprocess.run(["bash", "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True, text=True, check=False)
    return int(result.stdout.strip()) if result.stdout.strip().isdigit() else None


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
        if shutil.which("bash") is not None:
            self.assertIn(f", {len(list(self.kit.rglob('*.sh')))} shell scripts)", result.stdout)

    def test_each_violation_is_reported(self):
        (self.kit / "docs" / "INDEX.md").write_text("# docs\n", encoding="utf-8")
        (self.kit / "platforms" / "tools" / "unlisted_tool.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        (self.kit / ".github" / "CONTRIBUTING.md").unlink()
        result = self.check()
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1)
        self.assertIn("docs/INDEX.md", output)
        self.assertIn("INDEX.md exists only at plugins/<name>/", output)
        self.assertIn("entry 'unlisted_tool.sh' does not appear in the index", output)
        self.assertIn(".github/CONTRIBUTING.md: layout: required path missing", output)

    def test_a_link_out_of_the_plugin_and_a_missing_not_for_fail(self):
        skill = self.kit / "plugins" / "guardrails" / "skills" / "session" / "SKILL.md"
        text = skill.read_text(encoding="utf-8").replace("Not for parallelism", "Never parallelism", 1)
        skill.write_text(text + "\nSee [design](../../../../docs/design.md).\n", encoding="utf-8")
        result = self.check()
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1)
        self.assertIn("session/SKILL.md: path escapes plugin root: ../../../../docs/design.md", output)
        self.assertIn("session/SKILL.md: description lacks literal 'Not for'", output)
        self.assertEqual(output.count("FAIL:"), 2, output)

    @unittest.skipIf(shutil.which("bash") is None, "bash not in PATH")
    def test_a_shell_script_bash_cannot_parse_fails(self):
        script = self.kit / DOCTOR
        script.write_text(script.read_text(encoding="utf-8") + "\nif true; then\n", encoding="utf-8")
        result = self.check()
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"{DOCTOR}: bash -n failed under ", output)
        self.assertEqual(output.count("FAIL:"), 1, output)

    @unittest.skipUnless(bash_major() == 3, "the trap is specific to bash 3.x, the macOS /bin/bash")
    def test_an_odd_apostrophe_in_a_heredoc_inside_command_substitution_fails_under_bash_3(self):
        # The comment that broke doctor.sh during agent-rules-kit#207; shellcheck 0.11.0 accepts it.
        script = self.kit / DOCTOR
        text = script.read_text(encoding="utf-8")
        self.assertEqual(text.count(DOCTOR_HEREDOC), 1)
        script.write_text(text.replace(DOCTOR_HEREDOC, DOCTOR_HEREDOC + "# Claude Code's schema\n"), encoding="utf-8")
        result = self.check()
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"{DOCTOR}: bash -n failed under ", output)
        self.assertIn("unexpected EOF while looking for matching", output)
        self.assertEqual(output.count("FAIL:"), 1, output)


if __name__ == "__main__":
    unittest.main()
