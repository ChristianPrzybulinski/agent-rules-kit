"""guardrails context hooks (KIT-071): the SessionStart checklist and the PreToolUse git context.

Both only add context: they exit 0, never deny and stay within the per-hook latency budget. check_kit.py runs the
git context cases (hook_git_context_cases.json) and the checklist; these tests cover malformed input, the budget and
that check_kit.py fails when either hook breaks."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
HOOKS_REL = "plugins/guardrails/hooks/hooks.json"
CHECK_KIT = "platforms/ci/validations/check_kit.py"
GIT_MARKER = "ai-kit git, after this "
CHECKLIST_MARKER = "ai-kit session start:"
BUDGET_S = 0.5  # best of three runs, as in test_hooks_guard_compact.py


def commands(hooks, event, marker):
    return [hook["command"] for group in hooks["hooks"][event] for hook in group["hooks"] if marker in hook["command"]]


HOOKS = json.loads((KIT / HOOKS_REL).read_text(encoding="utf-8"))
GIT_CONTEXT = commands(HOOKS, "PreToolUse", GIT_MARKER)
CHECKLIST = commands(HOOKS, "SessionStart", CHECKLIST_MARKER)


class ContextHooksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir()
        (bin_dir / "python3").symlink_to(sys.executable)  # the real interpreter, not the macOS shim
        self.env = {"PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""), "HOME": self.tmp.name}

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, command, stdin):
        return subprocess.run(["bash", "-c", command], input=stdin, text=True, capture_output=True,
                              timeout=10, cwd=self.tmp.name, env=self.env, check=False)

    def test_each_hook_ships_once(self):
        self.assertEqual((len(GIT_CONTEXT), len(CHECKLIST)), (1, 1))

    def test_checklist_names_the_start_steps(self):
        result = self.run_hook(CHECKLIST[0], json.dumps({"hook_event_name": "SessionStart", "source": "startup"}))
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SessionStart")
        for word in ("one outcome", "AGENTS.md", "README", "git rev-parse --show-toplevel", "git branch --show-current",
                     "git rev-parse HEAD", "skill `session`"):
            self.assertIn(word, output["additionalContext"])

    def test_checklist_runs_only_on_startup_and_clear(self):
        group = next(g for g in HOOKS["hooks"]["SessionStart"] if CHECKLIST_MARKER in g["hooks"][0]["command"])
        self.assertEqual(group["matcher"], "^(startup|clear)$")

    def test_git_context_by_kind(self):
        for command, kind in (("git commit -m x", "commit"), ("gh pr create --fill", "PR")):
            result = self.run_hook(GIT_CONTEXT[0], json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}))
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertNotIn("permissionDecision", output)
            self.assertTrue(output["additionalContext"].startswith(GIT_MARKER + kind), output)

    def test_git_context_is_silent_on_malformed_input(self):
        for stdin in ("", "not json", "[1, 2]", json.dumps({"tool_input": "git commit"}),
                      json.dumps({"tool_input": {"command": ["git", "commit"]}}), json.dumps({"tool_input": {}})):
            result = self.run_hook(GIT_CONTEXT[0], stdin)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""), stdin)

    def test_latency_budget(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}})
        for name, command in (("git context", GIT_CONTEXT[0]), ("checklist", CHECKLIST[0])):
            runs = []
            for _ in range(3):
                start = time.monotonic()
                self.run_hook(command, payload)
                runs.append(time.monotonic() - start)
            self.assertLess(min(runs), BUDGET_S, f"{name} took {min(runs):.3f} s at best of 3")


class CheckKitCatchesBrokenHooksTest(unittest.TestCase):
    """check_kit.py fails when the git context hook speaks on a silent case or the checklist hook is gone."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.kit = Path(self.tmp.name) / "kit"
        listed = subprocess.run(["git", "-C", str(KIT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                                capture_output=True, text=True, check=True).stdout
        for rel in filter(None, listed.split("\0")):  # the working tree, so uncommitted edits count
            if (KIT / rel).is_file():
                (self.kit / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(KIT / rel, self.kit / rel)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, hooks):
        (self.kit / HOOKS_REL).write_text(json.dumps(hooks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return subprocess.run([sys.executable, "-B", str(self.kit / CHECK_KIT)], capture_output=True, text=True,
                              check=False)

    def test_git_context_that_always_speaks_fails(self):
        hooks = json.loads(json.dumps(HOOKS))
        for group in hooks["hooks"]["PreToolUse"]:
            for hook in group["hooks"]:
                if GIT_MARKER in hook["command"]:
                    hook["command"] = hook["command"].replace('else ""\nT=', 'else "commit"\nT=', 1)
                    self.assertNotEqual(hook["command"], GIT_CONTEXT[0])
        result = self.check(hooks)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("silent case printed", result.stderr)

    def test_missing_checklist_fails(self):
        hooks = json.loads(json.dumps(HOOKS))
        hooks["hooks"]["SessionStart"] = [g for g in hooks["hooks"]["SessionStart"]
                                          if CHECKLIST_MARKER not in g["hooks"][0]["command"]]
        result = self.check(hooks)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SessionStart needs the checklist hook", result.stderr)


if __name__ == "__main__":
    unittest.main()
