"""check_kit.py on a throwaway copy: root files, optional folder READMEs and INDEX.md placement (KIT-042),
links that leave the plugin and skill descriptions without 'Not for' (KIT-052), shell scripts the bash on
PATH cannot parse (KIT-060), and a sync profile map line that names a skill or misses a rule (KIT-083)."""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/check_kit.py",)

KIT = Path(__file__).resolve().parents[3]
CHECK_KIT = "platforms/ci/validations/check_kit.py"
DOCTOR = "platforms/tools/doctor.sh"
PROFILE_MAP = "plugins/guardrails/hooks/sync-profiles.txt"  # KIT-081 stage 3: next to the rules
SESSION = "plugins/guardrails/skills/session/SKILL.md"
# A synthetic description with its 'Use when' and without 'Not for', so the test keys on no wording of the real one.
NO_NOT_FOR = "A fixture description for the check. Use when a test rewrites the frontmatter."
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

    def test_a_link_out_of_the_plugin_a_missing_not_for_and_a_script_bash_cannot_parse_fail_alone(self):
        """One run for independent violations, each on a FAIL line of its own and nothing else: a folder needs no
        README (KIT-042), a link leaves the plugin and a description lacks 'Not for' (KIT-052), and a script bash
        cannot parse (KIT-060), with every script counted. The real kit passing is the static job's check_kit.py run
        (.github/workflows/ci.yml)."""
        (self.kit / "docs" / "notes").mkdir()
        (self.kit / "docs" / "notes" / "a.md").write_text("# a\n", encoding="utf-8")
        skill = self.kit / SESSION
        text = skill.read_text(encoding="utf-8")
        new = re.sub(r"^description: .*$", f"description: {NO_NOT_FOR}", text, count=1, flags=re.M)
        self.assertNotEqual(new, text)
        skill.write_text(new, encoding="utf-8")
        (skill.parent / "fixture-link.md").write_text("See [the README](../../../../README.md).\n", encoding="utf-8")
        expected = [f"{SESSION.replace('SKILL.md', 'fixture-link.md')}: path escapes plugin root: ../../../../README.md",
                    f"{SESSION}: description lacks literal 'Not for'"]
        bash = shutil.which("bash") is not None
        if bash:
            script = self.kit / DOCTOR
            script.write_text(script.read_text(encoding="utf-8") + "\nif true; then\n", encoding="utf-8")
            expected.append(f"{DOCTOR}: bash -n failed under ")
        result = self.check()
        output = result.stdout + result.stderr
        lines = [line for line in output.splitlines() if line.startswith("FAIL: ")]
        self.assertEqual(result.returncode, 1)
        for want in expected:
            with self.subTest(want=want):
                self.assertEqual(sum(want in line for line in lines), 1, output)
        self.assertEqual(output.count("FAIL:"), len(expected), output)
        if bash:
            self.assertIn(f", {len(list(self.kit.rglob('*.sh')))} shell scripts)", result.stdout)

    def test_each_violation_is_reported(self):
        (self.kit / "docs" / "INDEX.md").write_text("# docs\n", encoding="utf-8")
        (self.kit / "platforms" / "tools" / "unlisted_tool.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        (self.kit / ".github" / "CONTRIBUTING.md").unlink()
        # KIT-083: the profile map names the rules each profile receives; a skill line has no reader since KIT-081
        # stage 2b, so one fails, and a rule without its line still fails.
        profile_map = self.kit / PROFILE_MAP
        lines = [line for line in profile_map.read_text(encoding="utf-8").splitlines(keepends=True)
                 if not line.startswith("rules/spec.md ")]
        if not any(line.startswith("skills/session ") for line in lines):
            lines.append("skills/session          | -\n")
        profile_map.write_text("".join(lines), encoding="utf-8")
        result = self.check()
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1)
        self.assertIn("docs/INDEX.md", output)
        self.assertIn("INDEX.md exists only at plugins/<name>/", output)
        self.assertIn("entry 'unlisted_tool.sh' does not appear in the index", output)
        self.assertIn(".github/CONTRIBUTING.md: layout: required path missing", output)
        self.assertIn(f"{PROFILE_MAP}: 'skills/session' is not a rule of plugins/guardrails", output)
        self.assertIn(f"{PROFILE_MAP}: no line for rules/spec.md; every kit rule needs one", output)

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


class NoVendoringToolTest(unittest.TestCase):
    """KIT-083: the kit vendors no third-party skill (the lock held no entry since KIT-070 removed `grilling`), so it
    ships no vendoring tool, lock or lock schema, and no file names them; the CHANGELOG and the KIT records keep the
    history."""
    LAYER = "contract"  # the kit's own files, read in-process

    GONE = ("platforms/tools/vendor.sh", "platforms/kits/third-party", "platforms/ci/schemas/skills-lock.schema.json")
    NAMES = ("vendor.sh", "skills.lock", "skills-lock")

    def test_no_vendoring_tool_is_left_or_named(self):
        for rel in self.GONE:
            self.assertFalse((KIT / rel).exists(), rel)
        roots = [KIT / "README.md", KIT / ".github", KIT / "platforms", KIT / "plugins", KIT / "docs"]
        files = []
        for root in roots:
            files += [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]
        named = []
        for path in files:
            rel = path.relative_to(KIT).as_posix()
            if "__pycache__" in path.parts or path == Path(__file__).resolve() or re.match(r"docs/features/KIT-", rel):
                continue
            text = path.read_bytes().decode("utf-8", errors="replace")
            named += [f"{rel}: {name}" for name in self.NAMES if name in text]
        self.assertEqual(named, [])


if __name__ == "__main__":
    unittest.main()
