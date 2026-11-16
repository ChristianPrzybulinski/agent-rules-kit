"""check_kit.py on a throwaway copy (KIT-070): a reference folder nested under a skill's references/ (the stack
indexes such as sdd-implement/references/godot/) gets the same frontmatter, schema and 60-line checks as a flat
reference, at any depth, carries a README.md index that lists each of its files, and its index is named in the
owning SKILL.md (or, one level deeper, in the parent folder's index)."""
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
SKILL = "plugins/guardrails/skills/sdd-implement/SKILL.md"
NESTED = "plugins/guardrails/skills/sdd-implement/references/godot"
VALID = "---\ndescription: A nested fixture reference.\nkind: detail\n---\n\n# Fixture\n"


class CheckKitNestedReferencesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.template = Path(cls.tmp.name) / "template"
        listed = subprocess.run(["git", "-C", str(KIT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                                capture_output=True, text=True, check=True).stdout
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
        result = subprocess.run([sys.executable, "-B", str(self.kit / CHECK_KIT)], capture_output=True, text=True,
                                check=False)
        return result.stdout + result.stderr

    def add_to_index(self, name):
        index = self.kit / NESTED / "README.md"
        index.write_text(index.read_text(encoding="utf-8") + f"\n- `{name}`\n", encoding="utf-8")

    def assert_fails(self, output, expected):
        """Each mutation's own FAIL line and no other: the mutations merged into one check_kit.py run neither mask
        nor add a failure."""
        self.assertEqual(sorted(line for line in output.splitlines() if line.startswith("FAIL: ")),
                         sorted(f"FAIL: {line}" for line in expected), output)

    # The static job's check_kit.py run (.github/workflows/ci.yml) fails on a FAIL line only; the first test keeps the
    # stricter guard that the real nested references print no line at all, WARN included. Each test after it runs
    # check_kit.py once on independent mutations (a mutation of one file or folder never hides another's line).

    def test_the_nested_references_pass(self):
        output = self.check()
        self.assertNotIn("references/godot", output)
        self.assertNotIn("references/java", output)

    def test_nested_references_get_the_flat_checks_at_any_depth(self):
        (self.kit / NESTED / "extra.md").write_text("# no frontmatter\n", encoding="utf-8")
        self.add_to_index("extra.md")
        (self.kit / NESTED / "long.md").write_text(VALID + "line\n" * 60, encoding="utf-8")
        self.add_to_index("long.md")
        (self.kit / NESTED / "unlisted.md").write_text(VALID, encoding="utf-8")  # review of PR #261
        # review round 2: "deep/tests.md" lists no "tests.md"
        (self.kit / NESTED / "tests.md").write_text(VALID, encoding="utf-8")
        self.add_to_index("deep/tests.md")
        deep = self.kit / NESTED / "deep"  # review of PR #261 (N7): any depth, not one level
        deep.mkdir()
        (deep / "README.md").write_text("# Deep\n\n- `bare.md`\n- `long.md`\n", encoding="utf-8")
        (deep / "bare.md").write_text("# no frontmatter\n", encoding="utf-8")
        (deep / "long.md").write_text(VALID + "line\n" * 60, encoding="utf-8")
        (deep / "loose.md").write_text(VALID, encoding="utf-8")
        self.add_to_index("deep/README.md")
        bare = deep / "nofolder"
        bare.mkdir()
        (bare / "a.md").write_text(VALID, encoding="utf-8")
        self.assert_fails(self.check(), [
            f"{NESTED}/extra.md: missing/invalid frontmatter",
            f"{NESTED}/long.md: 66 lines (>60)",
            f"{NESTED}/unlisted.md: not listed in {NESTED}/README.md",
            f"{NESTED}/tests.md: not listed in {NESTED}/README.md",
            f"{NESTED}/deep/bare.md: missing/invalid frontmatter",
            f"{NESTED}/deep/long.md: 66 lines (>60)",
            f"{NESTED}/deep/loose.md: not listed in {NESTED}/deep/README.md",
            f"{NESTED}/deep/nofolder: a nested reference folder needs a README.md index",
        ])

    def test_each_nested_index_is_named_by_its_owner(self):
        folder = self.kit / "plugins/guardrails/skills/sdd-plan/references/newstack"
        folder.mkdir()
        (folder / "a.md").write_text(VALID, encoding="utf-8")
        unnamed = self.kit / NESTED / "unnamed"  # review of PR #261 (N7): a deeper index is named in its parent's
        unnamed.mkdir()
        (unnamed / "README.md").write_text("# Unnamed\n\n- `a.md`\n", encoding="utf-8")
        (unnamed / "a.md").write_text(VALID, encoding="utf-8")
        index = self.kit / NESTED / "README.md"  # review round 2: "godot/README.md" names no "ot/"
        self.assertIn("godot/README.md", index.read_text(encoding="utf-8"))
        deep = self.kit / NESTED / "ot"
        deep.mkdir()
        (deep / "README.md").write_text("# Ot\n\n- `a.md`\n", encoding="utf-8")
        (deep / "a.md").write_text(VALID, encoding="utf-8")
        skill = self.kit / SKILL
        text = skill.read_text(encoding="utf-8")
        self.assertIn("godot/README.md", text)
        skill.write_text(text.replace("godot/README.md", "godot-index"), encoding="utf-8")
        self.assert_fails(self.check(), [
            "plugins/guardrails/skills/sdd-plan/references/newstack: a nested reference folder needs a README.md index",
            f"{NESTED}/unnamed/README.md: 'unnamed/README.md' not referenced in {NESTED}/README.md",
            f"{NESTED}/ot/README.md: 'ot/README.md' not referenced in {NESTED}/README.md",
            f"{NESTED}/README.md: 'godot/README.md' not referenced in {SKILL}",
        ])


if __name__ == "__main__":
    unittest.main()
