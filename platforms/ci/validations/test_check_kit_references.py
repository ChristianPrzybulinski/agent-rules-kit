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

    def test_the_nested_references_pass(self):
        output = self.check()
        self.assertNotIn("references/godot", output)
        self.assertNotIn("references/java", output)

    def test_nested_reference_needs_frontmatter(self):
        (self.kit / NESTED / "extra.md").write_text("# no frontmatter\n", encoding="utf-8")
        self.add_to_index("extra.md")
        self.assertIn(f"FAIL: {NESTED}/extra.md: missing/invalid frontmatter", self.check())

    def test_nested_reference_keeps_the_line_limit(self):
        (self.kit / NESTED / "long.md").write_text(VALID + "line\n" * 60, encoding="utf-8")
        self.add_to_index("long.md")
        self.assertIn(f"FAIL: {NESTED}/long.md: 66 lines (>60)", self.check())

    def test_nested_folder_needs_a_readme_index(self):
        folder = self.kit / "plugins/guardrails/skills/sdd-plan/references/newstack"
        folder.mkdir()
        (folder / "a.md").write_text(VALID, encoding="utf-8")
        self.assertIn("FAIL: plugins/guardrails/skills/sdd-plan/references/newstack: a nested reference folder needs "
                      "a README.md index", self.check())

    def test_nested_reference_is_listed_in_its_index(self):  # review of PR #261
        (self.kit / NESTED / "unlisted.md").write_text(VALID, encoding="utf-8")
        self.assertIn(f"FAIL: {NESTED}/unlisted.md: not listed in {NESTED}/README.md", self.check())

    def test_deeper_folders_get_every_check(self):  # review of PR #261 (N7): any depth, not one level
        deep = self.kit / NESTED / "deep"
        deep.mkdir()
        (deep / "README.md").write_text("# Deep\n\n- `bare.md`\n- `long.md`\n", encoding="utf-8")
        (deep / "bare.md").write_text("# no frontmatter\n", encoding="utf-8")
        (deep / "long.md").write_text(VALID + "line\n" * 60, encoding="utf-8")
        (deep / "loose.md").write_text(VALID, encoding="utf-8")
        self.add_to_index("deep/README.md")
        bare = deep / "nofolder"
        bare.mkdir()
        (bare / "a.md").write_text(VALID, encoding="utf-8")
        output = self.check()
        self.assertIn(f"FAIL: {NESTED}/deep/bare.md: missing/invalid frontmatter", output)
        self.assertIn(f"FAIL: {NESTED}/deep/long.md: 66 lines (>60)", output)
        self.assertIn(f"FAIL: {NESTED}/deep/loose.md: not listed in {NESTED}/deep/README.md", output)
        self.assertIn(f"FAIL: {NESTED}/deep/nofolder: a nested reference folder needs a README.md index", output)

    def test_deeper_index_is_named_in_its_parent_index(self):  # review of PR #261 (N7)
        deep = self.kit / NESTED / "deep"
        deep.mkdir()
        (deep / "README.md").write_text("# Deep\n\n- `a.md`\n", encoding="utf-8")
        (deep / "a.md").write_text(VALID, encoding="utf-8")
        self.assertIn(f"FAIL: {NESTED}/deep/README.md: 'deep/README.md' not referenced in {NESTED}/README.md",
                      self.check())

    def test_index_name_matches_whole_path_components(self):  # review round 2: "godot/README.md" names no "ot/"
        index = self.kit / NESTED / "README.md"
        self.assertIn("godot/README.md", index.read_text(encoding="utf-8"))
        deep = self.kit / NESTED / "ot"
        deep.mkdir()
        (deep / "README.md").write_text("# Ot\n\n- `a.md`\n", encoding="utf-8")
        (deep / "a.md").write_text(VALID, encoding="utf-8")
        self.assertIn(f"FAIL: {NESTED}/ot/README.md: 'ot/README.md' not referenced in {NESTED}/README.md",
                      self.check())

    def test_a_deeper_path_is_no_listing_of_a_sibling(self):  # review round 2: "deep/tests.md" lists no "tests.md"
        (self.kit / NESTED / "tests.md").write_text(VALID, encoding="utf-8")
        self.add_to_index("deep/tests.md")
        self.assertIn(f"FAIL: {NESTED}/tests.md: not listed in {NESTED}/README.md", self.check())

    def test_nested_index_is_named_in_the_skill(self):
        skill = self.kit / SKILL
        text = skill.read_text(encoding="utf-8")
        self.assertIn("godot/README.md", text)
        skill.write_text(text.replace("godot/README.md", "godot-index"), encoding="utf-8")
        self.assertIn(f"FAIL: {NESTED}/README.md: 'godot/README.md' not referenced in {SKILL}", self.check())


if __name__ == "__main__":
    unittest.main()
