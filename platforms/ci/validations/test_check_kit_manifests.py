"""The Codex manifest of each kit plugin (`plugins/<name>/plugin.json`) carries no `$schema` (KIT-081 stage 3, Codex).

codex-cli 0.164.0 reads a root manifest whose `$schema` names https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
as an Agent Plugins manifest and lists no hook of the plugin, with no warning and no error (probe 2026-11-19, six
arms: the schema URL first or last in the file gave 0 hooks; no key, another schema URL, an unknown key or `author`
gave 8; removing `.claude-plugin/` changed nothing, so the lookup order is not the cause)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/check_kit.py", "plugins/*/plugin.json")

KIT = Path(__file__).resolve().parents[3]
CHECK_KIT = "platforms/ci/validations/check_kit.py"
MANIFEST = "plugins/guardrails/plugin.json"
AGENT_PLUGINS = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"


class CodexManifestContractTest(unittest.TestCase):
    LAYER = "contract"  # the kit's own files, read in-process

    def test_no_kit_codex_manifest_has_a_schema_key(self):
        manifests = sorted((KIT / "plugins").glob("*/plugin.json"))
        self.assertTrue(manifests)
        for path in manifests:
            with self.subTest(path=str(path.relative_to(KIT))):
                self.assertNotIn("$schema", json.loads(path.read_text(encoding="utf-8")))


class CheckKitManifestsTest(unittest.TestCase):
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
        return subprocess.run([sys.executable, "-B", str(self.kit / CHECK_KIT)], capture_output=True, text=True,
                              check=False)

    def set_codex_manifest(self, **extra):
        path = self.kit / MANIFEST
        data = json.loads(path.read_text(encoding="utf-8"))
        data.update(extra)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def fail_lines(self, result):
        return [line for line in result.stderr.splitlines() if line.startswith("FAIL: ")]

    def test_the_real_kit_passes(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_schema_key_in_the_codex_manifest_fails(self):
        for value in (AGENT_PLUGINS, "https://example.com/plugin.schema.json"):
            with self.subTest(value=value):
                self.set_codex_manifest(**{"$schema": value})
                result = self.check()
                lines = self.fail_lines(result)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(len(lines), 1, result.stderr)
                self.assertIn(MANIFEST, lines[0])
                self.assertIn("$schema", lines[0])
                self.assertIn("lists no hooks", lines[0])

    def test_a_schema_key_in_the_other_manifests_is_not_this_check(self):
        for rel in ("plugins/guardrails/.claude-plugin/plugin.json", "plugins/guardrails/.devin-plugin/plugin.json"):
            with self.subTest(rel=rel):
                path = self.kit / rel
                data = json.loads(path.read_text(encoding="utf-8"))
                data["$schema"] = AGENT_PLUGINS
                path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                result = self.check()
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
