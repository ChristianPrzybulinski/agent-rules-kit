"""core hooks: the guard's --no-verify pattern, the SessionStart compact branch and a latency budget per hook."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[3] / "plugins" / "core" / "hooks" / "hooks.json"
EVENTS = json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]
GUARD, POST_EDIT, SESSION_START = (
    EVENTS[event][0]["hooks"][0]["command"] for event in ("PreToolUse", "PostToolUse", "SessionStart"))
BUDGET_S = 0.5  # best of three runs; the python3 start dominates
STATUS_LIMIT = 2000
TRUNCATED = "\n[truncated]"

SKIPPED_HOOKS = (
    "git commit --no-verify -m 'wip'",
    'git commit -m "wip" --no-verify',
    "git push --no-verify origin feat",
    "git merge --no-verify feat",
    "git commit -nm 'wip'",
    "git -C repo commit -a -n -m 'wip'",
    "cd repo && git commit --no-verify",
)
OTHER_FLAGS = (
    "git commit -m 'wip'",
    "git commit --amend --no-edit",
    "git commit -am 'add notes'",
    "git clean -n",
    "git log -n 5",
    "git push -n origin feat",
    "grep -rn -- --no-verify docs",
    "npm run lint -- --no-verify",
)


class HooksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name).resolve()
        bin_dir = self.dir / "bin"
        bin_dir.mkdir()
        # The real interpreter, as in check_kit.py: the macOS /usr/bin/python3 shim's cold start is not the hook's cost.
        (bin_dir / "python3").symlink_to(sys.executable)
        self.env = {"PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""), "HOME": str(self.dir),
                    "GIT_CEILING_DIRECTORIES": str(self.dir.parent)}

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, command, payload):
        return subprocess.run(["bash", "-c", command], input=json.dumps(payload), text=True, capture_output=True,
                              timeout=10, cwd=self.dir, env=self.env, check=False)

    def guard(self, command):
        return self.run_hook(GUARD, {"tool_name": "Bash", "tool_input": {"command": command}})

    def session_start(self, source, cwd):
        return self.run_hook(SESSION_START, {"hook_event_name": "SessionStart", "source": source, "cwd": str(cwd)})

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=kit", "-c", "user.email=kit@example.invalid", *args],
                              capture_output=True, text=True, env=self.env, check=True).stdout.strip()

    def test_guard_blocks_skipped_git_hooks(self):
        for command in SKIPPED_HOOKS:
            with self.subTest(command=command):
                result = self.guard(command)
                self.assertEqual(result.returncode, 2)
                reason = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
                self.assertIn("git --no-verify", reason)

    def test_guard_allows_other_n_flags(self):
        for command in OTHER_FLAGS:
            with self.subTest(command=command):
                result = self.guard(command)
                self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_compact_reinjects_git_state(self):
        repo = self.dir / "repo"
        self.git("init", "-q", "-b", "feat/kit-050", str(repo))
        (repo / "tracked.txt").write_text("a\n", encoding="utf-8")
        self.git("-C", str(repo), "add", "tracked.txt")
        self.git("-C", str(repo), "commit", "-qm", "init")
        (repo / "tracked.txt").write_text("b\n", encoding="utf-8")
        (repo / "new.txt").write_text("c\n", encoding="utf-8")
        head = self.git("-C", str(repo), "rev-parse", "--short", "HEAD")

        result = self.session_start("compact", repo)

        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertNotIn("systemMessage", output)
        context = output["hookSpecificOutput"]["additionalContext"]
        for expected in ("## feat/kit-050", " at " + head + ":", " M tracked.txt", "?? new.txt"):
            self.assertIn(expected, context)
        self.assertEqual(self.session_start("startup", repo).stdout, "")

    def test_compact_status_is_bounded(self):
        repo = self.dir / "repo"
        self.git("init", "-q", "-b", "main", str(repo))
        for index in range(300):
            (repo / f"untracked-file-{index:04d}.txt").touch()

        context = json.loads(self.session_start("compact", repo).stdout)["hookSpecificOutput"]["additionalContext"]

        status = context.split(":\n", 1)[1]
        self.assertTrue(status.endswith(TRUNCATED))
        self.assertEqual(len(status), STATUS_LIMIT + len(TRUNCATED))
        self.assertIn(" at no commit:", context)

    def test_compact_outside_git_is_silent(self):
        result = self.session_start("compact", self.dir)
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_each_hook_within_budget(self):
        (self.dir / "notes.txt").touch()
        cases = (
            ("guard", GUARD, {"tool_name": "Bash", "tool_input": {"command": "git status"}}),
            ("post-edit", POST_EDIT, {"tool_name": "Edit", "tool_input": {"file_path": "notes.txt"}, "cwd": str(self.dir)}),
            ("session-start", SESSION_START, {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(self.dir)}),
            ("compact", SESSION_START, {"hook_event_name": "SessionStart", "source": "compact", "cwd": str(self.dir)}),
        )
        for name, command, payload in cases:
            with self.subTest(hook=name):
                runs = []
                for _ in range(3):
                    start = time.perf_counter()
                    self.run_hook(command, payload)
                    runs.append(time.perf_counter() - start)
                self.assertLess(min(runs), BUDGET_S, f"{name} hook took {min(runs):.3f} s at best of 3")


if __name__ == "__main__":
    unittest.main()
