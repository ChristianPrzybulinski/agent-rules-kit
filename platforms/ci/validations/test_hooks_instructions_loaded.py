"""guardrails InstructionsLoaded hook (KIT-070, issue #238): records each CLAUDE.md and .claude/rules/*.md load.

Claude Code fires InstructionsLoaded when an instruction file enters the context, path rules included (load_reason
path_glob_match, with globs and trigger_file_path), runs it asynchronously and ignores its output and exit code (hooks
reference, 2026-11-15). The hook appends one JSON line per load to $CLAUDE_PLUGIN_DATA/instructions-loaded.jsonl,
which platforms/tools/skill_usage.py --rules counts; it spends no model tokens, prints nothing, always exits 0, keeps
only the documented fields (never the transcript path or any file content) and rotates the log past 5 MiB. These tests
cover the record, malformed input, a missing data directory, the rotation, the budget and that check_kit.py fails when
the hook breaks."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("plugins/guardrails/hooks/**", "platforms/ci/validations/check_kit.py")

KIT = Path(__file__).resolve().parents[3]
HOOKS_REL = "plugins/guardrails/hooks/hooks.json"
CHECK_KIT = "platforms/ci/validations/check_kit.py"
MARKER = "ai-kit rule-load log"
LOG = "instructions-loaded.jsonl"
FIELDS = {"ts", "session_id", "cwd", "file_path", "memory_type", "load_reason", "globs", "trigger_file_path",
          "parent_file_path"}
BUDGET_S = 0.5
RULE_LOAD = {"session_id": "s1", "transcript_path": "/x/t.jsonl", "cwd": "/repo", "hook_event_name": "InstructionsLoaded",
             "file_path": "/repo/.claude/rules/guardrails-godot.md", "memory_type": "Project",
             "load_reason": "path_glob_match", "globs": ["client/**/*.gd"], "trigger_file_path": "/repo/client/a.gd"}


def hook_commands(hooks):
    return [(group, hook) for group in hooks["hooks"].get("InstructionsLoaded", []) for hook in group["hooks"]]


HOOKS = json.loads((KIT / HOOKS_REL).read_text(encoding="utf-8"))


class InstructionsLoadedHookTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "data"

    def tearDown(self):
        self.tmp.cleanup()

    def command(self):
        found = hook_commands(HOOKS)
        self.assertEqual(len(found), 1, "one InstructionsLoaded hook")
        return found[0][1]["command"]

    def run_hook(self, payload, data=True):
        env = {key: value for key, value in os.environ.items() if key != "CLAUDE_PLUGIN_DATA"}
        if data:
            env["CLAUDE_PLUGIN_DATA"] = str(self.data)
        text = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run(["bash", "-c", self.command()], input=text, text=True, capture_output=True,
                              timeout=5, env=env, check=False)

    def lines(self, name=LOG):
        path = self.data / name
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def test_hook_is_declared_for_every_load_reason(self):
        found = hook_commands(HOOKS)
        self.assertEqual(len(found), 1)
        group, hook = found[0]
        self.assertNotIn("matcher", group)  # every load reason, so session_start loads count too
        self.assertEqual(hook["type"], "command")
        self.assertLessEqual(hook["timeout"], 5)
        self.assertIn(MARKER, hook["command"])

    def test_records_a_path_rule_load(self):
        result = self.run_hook(RULE_LOAD)
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)
        [record] = self.lines()
        self.assertEqual(set(record), FIELDS)
        self.assertEqual(record["file_path"], RULE_LOAD["file_path"])
        self.assertEqual(record["load_reason"], "path_glob_match")
        self.assertEqual(record["globs"], ["client/**/*.gd"])
        self.assertEqual(record["trigger_file_path"], "/repo/client/a.gd")
        self.assertIsNone(record["parent_file_path"])
        self.assertIsInstance(record["ts"], int)
        self.run_hook(dict(RULE_LOAD, load_reason="session_start", file_path="/repo/CLAUDE.md"))
        self.assertEqual([r["load_reason"] for r in self.lines()], ["path_glob_match", "session_start"])

    def test_malformed_input_writes_nothing(self):
        for payload in ("not json", "[1, 2]", "", '"text"'):
            with self.subTest(payload=payload):
                result = self.run_hook(payload)
                self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)
                self.assertEqual(self.lines(), [])

    def test_without_a_data_directory_it_does_nothing(self):
        result = self.run_hook(RULE_LOAD, data=False)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertFalse(self.data.exists())

    def test_rotates_past_five_mebibytes(self):
        self.data.mkdir()
        (self.data / LOG).write_text("x" * (5 * 2**20 + 1), encoding="utf-8")
        result = self.run_hook(RULE_LOAD)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.data / f"{LOG}.1").stat().st_size, 5 * 2**20 + 1)
        self.assertEqual(len(self.lines()), 1)

    def test_an_unwritable_data_directory_fails_open(self):
        self.data.write_text("a file, not a folder\n", encoding="utf-8")
        result = self.run_hook(RULE_LOAD)
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def test_stays_within_budget(self):
        best = min(self.timed() for _ in range(3))
        self.assertLess(best, BUDGET_S)

    test_stays_within_budget.LAYER = "performance"  # KIT-077: a latency budget runs alone (performance.yml)

    def timed(self):
        start = time.monotonic()
        self.run_hook(RULE_LOAD)
        return time.monotonic() - start


class CheckKitInstructionsLoadedTest(unittest.TestCase):
    """check_kit.py must fail on a copy whose rule-load hook prints, fails or drops a field."""

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

    def check_with(self, command):
        kit = Path(tempfile.mkdtemp(dir=self.tmp.name)) / "kit"
        shutil.copytree(self.template, kit)
        hooks = json.loads((kit / HOOKS_REL).read_text(encoding="utf-8"))
        hook_commands(hooks)[0][1]["command"] = command
        (kit / HOOKS_REL).write_text(json.dumps(hooks, indent=2) + "\n", encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(kit / CHECK_KIT)], capture_output=True, text=True,
                                check=False)
        return result.stdout + result.stderr

    def test_check_kit_fails_a_broken_hook(self):
        broken = {
            "prints": f"python3 -c 'print(\"x\")' # {MARKER}",
            "fails": f"python3 -c 'import sys; sys.exit(1)' # {MARKER}",
            "writes nothing": f"true # {MARKER}",
        }
        for name, command in broken.items():
            with self.subTest(name=name):
                self.assertIn("InstructionsLoaded rule-load log", self.check_with(command))


if __name__ == "__main__":
    unittest.main()
