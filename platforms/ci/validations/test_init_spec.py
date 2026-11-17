"""init-spec.sh: the spec.md template follows the profile's project.kind (KIT-089)."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/kits/sdd/init-spec.sh", "plugins/guardrails/templates/spec-index-*.md",
          "platforms/tools/profile.py")

KIT = Path(__file__).resolve().parents[3]
SCRIPT = KIT / "platforms" / "kits" / "sdd" / "init-spec.sh"
TEMPLATES = KIT / "plugins" / "guardrails" / "templates"


class InitSpecTemplateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "AGENTS.md").write_text("# x\n")

    def tearDown(self):
        self.tmp.cleanup()

    def init(self, kind=None):
        if kind:
            (self.repo / ".ai-kit.yaml").write_text(f"project:\n  kind: {kind}\n")
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        result = subprocess.run(["bash", str(SCRIPT), str(self.repo)], capture_output=True, text=True,
                                errors="replace", check=False, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def spec(self):
        return (self.repo / "docs" / "spec" / "spec.md").read_text(encoding="utf-8")

    def test_game_kind_copies_the_game_template(self):
        result = self.init("game")
        self.assertEqual(self.spec(), (TEMPLATES / "spec-index-game.md").read_text(encoding="utf-8"))
        self.assertIn("from spec-index-game.md (project.kind: game)", result.stdout)

    def test_other_kinds_copy_the_business_template(self):
        for kind in (None, "business", "tooling"):
            with self.subTest(kind=kind):
                (self.repo / "docs" / "spec" / "spec.md").unlink(missing_ok=True)
                self.init(kind)
                self.assertEqual(self.spec(), (TEMPLATES / "spec-index-business.md").read_text(encoding="utf-8"))

    def test_an_invalid_kind_stops_before_any_copy(self):
        (self.repo / ".ai-kit.yaml").write_text("project:\n  kind: arcade\n")
        result = subprocess.run(["bash", str(SCRIPT), str(self.repo)], capture_output=True, text=True,
                                errors="replace", check=False)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.repo / "docs" / "spec" / "spec.md").exists())

    def test_an_existing_spec_is_never_overwritten(self):
        (self.repo / "docs" / "spec").mkdir(parents=True)
        (self.repo / "docs" / "spec" / "spec.md").write_text("---\nproject: x\n---\n# x\n")
        self.init("game")
        self.assertEqual(self.spec(), "---\nproject: x\n---\n# x\n")


if __name__ == "__main__":
    unittest.main()
