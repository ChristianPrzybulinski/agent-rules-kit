"""guardrails context hooks (KIT-071): the SessionStart checklist, the SubagentStart attribution and the PreToolUse git
context.

All three only add context: they exit 0, never deny and stay within the per-hook latency budget. The attribution line
(trailer and PR footer) speaks only where the effective settings (user, then project, then local) set
includeGitInstructions to false, or CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS is set; it then carries the user's own
attribution.commit and attribution.pr text where set, drops an empty one, and stays silent for attribution: false or
includeCoAuthoredBy: false, so the user's choice wins. SessionStart context never reaches a subagent (review probe, 2026-11-14), hence the
SubagentStart copy. check_kit.py runs the git context cases (hook_git_context_cases.json) and the four attribution
cases; these tests cover the settings layers, malformed input, the budget and that check_kit.py fails when a hook
breaks."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("plugins/guardrails/hooks/**", "platforms/ci/validations/check_kit.py",
          "platforms/ci/validations/hook_*_cases.json")

KIT = Path(__file__).resolve().parents[3]
HOOKS_REL = "plugins/guardrails/hooks/hooks.json"
GIT_CASES_REL = "platforms/ci/validations/hook_git_context_cases.json"
CHECK_KIT = "platforms/ci/validations/check_kit.py"
GIT_MARKER = "ai-kit git, after this "
CHECKLIST_MARKER = "ai-kit session start:"
ATTRIBUTION_MARKER = "ai-kit attribution:"
TRAILER = "Co-Authored-By: <your model's display name, as in Claude Sonnet 5.5> <noreply@anthropic.com>"
BUDGET_S = 0.5  # best of three runs, as in test_hooks_guard_compact.py


def commands(hooks, event, marker):
    return [hook["command"] for group in hooks["hooks"].get(event, []) for hook in group["hooks"]
            if marker in hook["command"]]


HOOKS = json.loads((KIT / HOOKS_REL).read_text(encoding="utf-8"))
GIT_CONTEXT = commands(HOOKS, "PreToolUse", GIT_MARKER)
CHECKLIST = commands(HOOKS, "SessionStart", CHECKLIST_MARKER)
SUBAGENT = commands(HOOKS, "SubagentStart", ATTRIBUTION_MARKER)


class ContextHooksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir()
        (bin_dir / "python3").symlink_to(sys.executable)  # the real interpreter, not the macOS shim
        self.env = {"PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""), "HOME": self.tmp.name}
        self.project = Path(self.tmp.name) / "project"
        (self.project / ".claude").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, command, stdin):
        return subprocess.run(["bash", "-c", command], input=stdin, text=True, capture_output=True,
                              timeout=10, cwd=self.tmp.name, env=self.env, check=False)

    def settings(self, rel, data):
        path = Path(self.tmp.name) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")

    def start(self, command, event, **env):
        """The additionalContext a start hook adds in self.project, or None when it prints nothing."""
        result = subprocess.run(["bash", "-c", command], text=True, capture_output=True, timeout=10, cwd=self.tmp.name,
                                env={**self.env, **env}, check=False,
                                input=json.dumps({"hook_event_name": event, "source": "startup", "cwd": str(self.project)}))
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        if not result.stdout:
            return None
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], event)
        return output["additionalContext"]

    def test_each_hook_ships_once(self):
        self.assertEqual((len(GIT_CONTEXT), len(CHECKLIST), len(SUBAGENT)), (1, 1, 1))

    def test_checklist_names_the_start_steps(self):
        """Markers, not prose: one line under its marker, the files to read, the commands that verify the working
        directory, Git root, branch and head as code, and a kit skill for the rest. Its wording is check_kit.py's to
        gate (CHECKLIST_WORDS)."""
        context = self.start(CHECKLIST[0], "SessionStart")
        self.assertTrue(context.startswith(CHECKLIST_MARKER), context)
        self.assertNotIn("\n", context)
        for name in ("AGENTS.md", "README"):
            self.assertIn(name, context)
        self.assertEqual(re.findall(r"`(git [^`]+)`", context),
                         ["git rev-parse --show-toplevel", "git branch --show-current", "git rev-parse HEAD"])
        skills = re.findall(r"skill `([a-z0-9-]+)`", context)
        self.assertIn("session", skills)
        for name in skills:
            self.assertTrue((KIT / "plugins/guardrails/skills" / name / "SKILL.md").is_file(), name)
        self.assertNotIn("Co-Authored-By", context)  # default settings: Claude Code's own attribution stays

    def test_checklist_runs_only_on_startup_and_clear(self):
        group = next(g for g in HOOKS["hooks"]["SessionStart"] if CHECKLIST_MARKER in g["hooks"][0]["command"])
        self.assertEqual(group["matcher"], "^(startup|clear)$")

    def test_subagent_attribution_runs_for_every_agent_type(self):
        self.assertEqual([group.get("matcher", "") for group in HOOKS["hooks"]["SubagentStart"]], [""])

    def test_attribution_only_where_git_instructions_are_off(self):
        self.settings("project/.claude/settings.json", {"includeGitInstructions": False})
        checklist, subagent = self.start(CHECKLIST[0], "SessionStart"), self.start(SUBAGENT[0], "SubagentStart")
        self.assertIn(CHECKLIST_MARKER, checklist)
        for word in (TRAILER, "Generated with [Claude Code](https://claude.com/claude-code)"):
            self.assertIn(word, checklist)
            self.assertIn(word, subagent)
        self.assertTrue(subagent.startswith(ATTRIBUTION_MARKER), subagent)
        self.assertTrue(checklist.endswith(" " + subagent))  # one line, the same in both events
        self.assertNotIn(CHECKLIST_MARKER, subagent)

    def test_attribution_silent_by_default(self):
        self.assertIsNone(self.start(SUBAGENT[0], "SubagentStart"))
        self.settings("project/.claude/settings.json", {"includeGitInstructions": True})
        self.assertIsNone(self.start(SUBAGENT[0], "SubagentStart"))
        self.assertNotIn("Co-Authored-By", self.start(CHECKLIST[0], "SessionStart"))

    def test_own_attribution_setting_wins(self):
        self.settings("project/.claude/settings.json", {"includeGitInstructions": False})
        user, local = ".claude/settings.json", "project/.claude/settings.local.json"
        footer = "end each PR body with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`"
        for rel, data, want, absent in (
                (user, {"attribution": {"commit": "", "pr": ""}}, None, ()),
                (user, {"attribution": False}, None, ()),
                (local, {"includeCoAuthoredBy": False}, None, ()),
                (local, {"attribution": {"commit": "Co-Authored-By: Bot <b@x>"}},
                 ("end each commit message with `Co-Authored-By: Bot <b@x>`", footer), (TRAILER,)),
                (user, {"attribution": {"pr": "Made with a bot"}},
                 (TRAILER, "end each PR body with `Made with a bot`"), ("Generated with",)),
                (local, {"attribution": {"commit": "", "pr": "Made with a bot"}},
                 ("end each PR body with `Made with a bot`",), ("Co-Authored-By", "commit message"))):
            with self.subTest(rel=rel, data=data):
                self.settings(rel, data)
                subagent, checklist = self.start(SUBAGENT[0], "SubagentStart"), self.start(CHECKLIST[0], "SessionStart")
                if want is None:
                    self.assertIsNone(subagent)
                    self.assertNotIn(ATTRIBUTION_MARKER, checklist)
                else:
                    for word in want:
                        self.assertIn(word, subagent)
                    for word in absent:
                        self.assertNotIn(word, subagent)
                    self.assertTrue(checklist.endswith(" " + subagent))
                (Path(self.tmp.name) / rel).unlink()

    def test_settings_layers(self):
        self.settings("project/.claude/settings.json", {"includeGitInstructions": False})
        self.settings("project/.claude/settings.local.json", {"includeGitInstructions": True})  # the opt-out
        self.assertIsNone(self.start(SUBAGENT[0], "SubagentStart"))
        (self.project / ".claude/settings.local.json").unlink()
        (self.project / ".claude/settings.json").unlink()
        self.settings(".claude/settings.json", {"includeGitInstructions": False})  # the user file, as the README says
        self.assertIn(TRAILER, self.start(SUBAGENT[0], "SubagentStart"))
        self.assertIn(TRAILER, self.start(SUBAGENT[0], "SubagentStart", CLAUDE_PROJECT_DIR=str(self.project)))
        (Path(self.tmp.name) / ".claude/settings.json").unlink()
        self.assertIn(TRAILER, self.start(SUBAGENT[0], "SubagentStart", CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS="1"))
        config = Path(self.tmp.name) / "config"
        self.settings("config/settings.json", {"includeGitInstructions": False})
        self.assertIn(TRAILER, self.start(SUBAGENT[0], "SubagentStart", CLAUDE_CONFIG_DIR=str(config)))

    def test_start_hooks_fail_open(self):
        self.settings("project/.claude/settings.json", {"includeGitInstructions": False})
        (self.project / ".claude/settings.local.json").write_text("{not json", encoding="utf-8")
        self.assertIn(TRAILER, self.start(SUBAGENT[0], "SubagentStart"))
        for stdin in ("", "not json", "[1, 2]", json.dumps({"cwd": 3})):
            for command in (CHECKLIST[0], SUBAGENT[0]):
                result = self.run_hook(command, stdin)  # cwd has no .claude: default settings
                self.assertEqual((result.returncode, result.stderr), (0, ""), stdin)
            self.assertEqual(self.run_hook(SUBAGENT[0], stdin).stdout, "", stdin)

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
        for name, command in (("git context", GIT_CONTEXT[0]), ("checklist", CHECKLIST[0]),
                              ("subagent attribution", SUBAGENT[0])):
            runs = []
            for _ in range(3):
                start = time.monotonic()
                self.run_hook(command, payload)
                runs.append(time.monotonic() - start)
            self.assertLess(min(runs), BUDGET_S, f"{name} took {min(runs):.3f} s at best of 3")

    test_latency_budget.LAYER = "performance"  # KIT-077: a latency budget runs alone (performance.yml)


class CheckKitCatchesBrokenHooksTest(unittest.TestCase):
    """check_kit.py fails when the git context hook speaks on a silent case, a start hook is gone or the attribution
    line ignores the settings."""

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

    def assert_fails(self, result, patterns):
        """Each pattern matches a FAIL line of its own and no other FAIL line appears: the mutations merged into one
        check_kit.py run neither mask nor add a failure."""
        lines = [line for line in result.stderr.splitlines() if line.startswith("FAIL: ")]
        self.assertNotEqual(result.returncode, 0)
        for pattern in patterns:
            with self.subTest(pattern=pattern):
                self.assertEqual(sum(bool(re.search(pattern, line)) for line in lines), 1, result.stderr)
        self.assertEqual([line for line in lines if not any(re.search(p, line) for p in patterns)], [], result.stderr)
        self.assertEqual(len(lines), len(patterns), result.stderr)

    def test_a_speaking_git_context_and_missing_start_hooks_fail(self):
        """Three hooks, three events: the git context hook (PreToolUse) speaks on every silent case, and the checklist
        (SessionStart) and the attribution (SubagentStart) are gone, so no hook case of one event hides another's."""
        hooks = json.loads(json.dumps(HOOKS))
        for group in hooks["hooks"]["PreToolUse"]:
            for hook in group["hooks"]:
                if GIT_MARKER in hook["command"]:
                    hook["command"] = hook["command"].replace('else ""\nT=', 'else "commit"\nT=', 1)
                    self.assertNotEqual(hook["command"], GIT_CONTEXT[0])
        hooks["hooks"]["SessionStart"] = [g for g in hooks["hooks"]["SessionStart"]
                                          if CHECKLIST_MARKER not in g["hooks"][0]["command"]]
        del hooks["hooks"]["SubagentStart"]
        silent = json.loads((self.kit / GIT_CASES_REL).read_text(encoding="utf-8"))["silent"]
        self.assert_fails(self.check(hooks), [
            "SessionStart needs the checklist hook", "SubagentStart needs the attribution hook",
            *(rf"{re.escape(GIT_CASES_REL)}: silent case printed .*: {re.escape(case)}$" for case in silent)])

    def test_attribution_that_ignores_the_settings_fails(self):
        """The commit text of the settings ignored in both start hooks, and SubagentStart speaking with default
        settings: each settings case is checked on its own, so the two mutations add their lines side by side."""
        hooks = json.loads(json.dumps(HOOKS))
        for group in hooks["hooks"]["SessionStart"] + hooks["hooks"]["SubagentStart"]:
            for hook in group["hooks"]:
                if ATTRIBUTION_MARKER in hook["command"]:
                    hook["command"] = hook["command"].replace('if isinstance(a.get("commit"),str)', "if False", 1)
        self.assertNotEqual(hooks, HOOKS)
        hook = hooks["hooks"]["SubagentStart"][0]["hooks"][0]
        unconditional = hook["command"].replace("\nif off and ", "\nif True or off and ", 1)
        self.assertNotEqual(unconditional, hook["command"])
        hook["command"] = unconditional
        custom = re.escape("must state Co-Authored-By: Bot <bot@example.invalid>")
        self.assert_fails(self.check(hooks), [
            # the ignored custom attribution
            rf"SessionStart checklist \(custom attribution settings\) {custom}",
            r"SubagentStart attribution \(custom attribution settings\) must add "
            r"Co-Authored-By: Bot <bot@example\.invalid>",
            r"SessionStart checklist \(hidden attribution settings\) must leave attribution to Claude Code",
            r"SubagentStart attribution \(hidden attribution settings\) must stay silent",
            # the unconditional attribution
            r"SubagentStart attribution \(default settings\) must stay silent"])


if __name__ == "__main__":
    unittest.main()
