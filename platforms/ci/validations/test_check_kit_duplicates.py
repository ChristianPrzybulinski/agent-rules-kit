"""Paragraph duplication exempts only one template's kind variants (KIT-089, #442)."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"
COVERS = ("platforms/ci/validations/check_kit.py",)

KIT = Path(__file__).resolve().parents[3]
CHECK_KIT = "platforms/ci/validations/check_kit.py"
PLUGIN = "plugins/guardrails"
VARIANTS = tuple(f"templates/spec-index-{kind}.md" for kind in ("business", "game", "tooling"))
PARAGRAPH = "A fixture paragraph shared across these files to exercise the duplication warning. " * 2


class CheckKitDuplicatesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.template = Path(cls.tmp.name) / "template"
        listed = subprocess.run(["git", "-C", str(KIT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                                capture_output=True, text=True, check=True).stdout
        for rel in filter(None, listed.split("\0")):
            if (KIT / rel).is_file():
                (cls.template / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(KIT / rel, cls.template / rel)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.kit = Path(tempfile.mkdtemp(dir=self.tmp.name)) / "kit"
        shutil.copytree(self.template, self.kit)

    def append(self, path, paragraph=PARAGRAPH):
        file = self.kit / PLUGIN / path
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open("a", encoding="utf-8") as stream:
            stream.write(f"\n\n{paragraph}\n")

    def duplicates(self):
        result = subprocess.run([sys.executable, "-B", str(self.kit / CHECK_KIT)], capture_output=True,
                                text=True, check=False)
        output = result.stdout + result.stderr
        self.assertNotIn("Traceback", output)
        self.assertIn("check:", output)
        return [line for line in output.splitlines() if "duplicated from" in line]

    def test_two_kind_variants_do_not_warn(self):
        for path in VARIANTS[:2]:
            self.append(path)
        self.assertEqual(self.duplicates(), [])

    def test_all_kind_variants_do_not_warn(self):
        for path in VARIANTS:
            self.append(path)
        self.assertEqual(self.duplicates(), [])

    def test_the_same_paragraph_twice_in_one_variant_warns(self):
        """A copy pasted twice into one variant is not a variant-to-variant share: it still warns."""
        self.append(VARIANTS[1])
        self.append(VARIANTS[1])
        warnings = self.duplicates()
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("spec-index-game.md", warnings[0])

    def test_a_future_spec_index_name_is_not_a_kind_variant(self):
        for path in (VARIANTS[0], "templates/spec-index-extra.md"):
            self.append(path)
        self.assertEqual(len(self.duplicates()), 1)

    def test_copy_in_another_template_warns_before_or_after_variants(self):
        for other in ("templates/other.md", "templates/z-other.md"):
            with self.subTest(other=other):
                paragraph = PARAGRAPH + other
                for path in VARIANTS[:2]:
                    self.append(path, paragraph)
                self.append(other, paragraph)
                warnings = self.duplicates()
                self.assertTrue(any(f"{PLUGIN}/{other}" in line for line in warnings), warnings)

    def test_copy_in_a_skill_warns(self):
        for path in VARIANTS[:2]:
            self.append(path)
        skill = "skills/sdd-implement/SKILL.md"
        self.append(skill)
        warnings = self.duplicates()
        self.assertIn(f"WARN: {PLUGIN}/{VARIANTS[0]}: paragraph duplicated from {PLUGIN}/{skill}", warnings)
        self.assertIn(f"WARN: {PLUGIN}/{VARIANTS[1]}: paragraph duplicated from {PLUGIN}/{skill}", warnings)

    def test_unrelated_template_variants_still_warn(self):
        first, second = "templates/spec-other-business.md", "templates/spec-other-game.md"
        for path in (first, second):
            self.append(path)
        self.assertIn(f"WARN: {PLUGIN}/{second}: paragraph duplicated from {PLUGIN}/{first}", self.duplicates())

    def test_paragraph_threshold_stays_at_120_characters(self):
        for length in (119, 120):
            with self.subTest(length=length):
                first, second = (f"templates/doc-threshold-{length}-{suffix}.md" for suffix in ("a", "b"))
                for path in (first, second):
                    self.append(path, "x" * length)
                warning = f"WARN: {PLUGIN}/{second}: paragraph duplicated from {PLUGIN}/{first}"
                self.assertEqual(warning in self.duplicates(), length == 120)


if __name__ == "__main__":
    unittest.main()
