"""check_kit.py on a throwaway copy (KIT-071): a subagent preloads only plugin-qualified, model-invocable kit skills,
and a `trigger` eval case repeats its AGENTS.md bullet in append_system_prompt.

A bare preload name resolved to Claude Code's bundled `review` instead of the kit skill (probe transcript, 2026-11-14),
and a skill with `disable-model-invocation: true` cannot be preloaded (Claude Code sub-agents doc)."""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
CHECK_KIT = "platforms/ci/validations/check_kit.py"
REVIEWER = "plugins/guardrails/agents/reviewer.md"
TRIGGER_CASE = "plugins/guardrails/evals/git-trigger-commit-this/prompt.md"

try:
    import jsonschema  # noqa: F401
    import yaml  # noqa: F401
    FULL = True
except ImportError:
    FULL = False


class CheckKitSkillUseTest(unittest.TestCase):
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

    def preload(self, *names):
        path = self.kit / REVIEWER
        text = path.read_text(encoding="utf-8")
        block = "skills:\n" + "".join(f"  - {name}\n" for name in names)
        new = re.sub(r"skills:\n(?:  - .*\n)+", lambda _: block, text, count=1)
        self.assertNotEqual(new, text)
        path.write_text(new, encoding="utf-8")

    def test_the_copy_passes(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_bare_preload_name_fails(self):
        self.preload("review", "guardrails:testing")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("skills: 'review' needs its plugin prefix", result.stderr)

    def test_unknown_plugin_or_skill_fails(self):
        self.preload("other:review", "guardrails:no-such-skill")
        result = self.check()
        self.assertIn("skills: 'other:review' is not a kit skill", result.stderr)
        self.assertIn("skills: 'guardrails:no-such-skill' is not a kit skill", result.stderr)

    def test_user_only_preload_fails(self):
        self.preload("guardrails:review", "guardrails:sdd-implement")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("skills: 'guardrails:sdd-implement' is user-only; cannot be preloaded", result.stderr)

    @unittest.skipUnless(FULL, "needs pyyaml to read the eval frontmatter")
    def test_trigger_case_without_append_fails(self):
        path = self.kit / TRIGGER_CASE
        text = path.read_text(encoding="utf-8")
        new = re.sub(r"^append_system_prompt: .*\n", "", text, count=1, flags=re.M)
        self.assertNotEqual(new, text)
        path.write_text(new, encoding="utf-8")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("a trigger case needs append_system_prompt", result.stderr)

    @unittest.skipUnless(FULL, "needs pyyaml to read the eval frontmatter")
    def test_drifted_append_fails(self):
        path = self.kit / TRIGGER_CASE
        text = path.read_text(encoding="utf-8")
        new = text.replace("load skill `git`.", "load skill `git` now.", 1)
        self.assertNotEqual(new, text)
        path.write_text(new, encoding="utf-8")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("append_system_prompt must repeat one bullet", result.stderr)


if __name__ == "__main__":
    unittest.main()
