"""guardrails hooks: the guard's --no-verify pattern and time on contrived input, the SessionStart compact branch and a latency budget per hook.

KIT-058: after compaction the hook also reports up to two repositories of the files the session edited most recently,
read from the last 4 MB of the payload's transcript_path; without a readable transcript it reports the cwd alone."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[3] / "plugins" / "guardrails" / "hooks" / "hooks.json"
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
# Allowed commands built to make a backtracking regex blow up; before KIT-054 the first ran past the 10 s hook timeout.
CONTRIVED = (
    "git" + " -C -a" * 40 + " status",
    "sudo" + " -u x" * 40 + " echo",
    "echo a" + "\n" * 20000 + "echo b",
    "cat > settings.txt <<EOF\n" + "".join(f"KEY_{index}=value-{index}\n" for index in range(1000)) + "EOF",
)
CONTRIVED_BUDGET_S = 1.0


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

    def test_guard_time_is_bounded_on_contrived_input(self):
        for command in CONTRIVED:
            with self.subTest(command=command[:40]):
                runs = []
                for _ in range(3):
                    start = time.perf_counter()
                    result = self.guard(command)
                    runs.append(time.perf_counter() - start)
                self.assertEqual((result.returncode, result.stdout), (0, ""))
                self.assertLess(min(runs), CONTRIVED_BUDGET_S, f"guard took {min(runs):.3f} s at best of 3")

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

    def make_repo(self, name, branch):
        repo = self.dir / name
        self.git("init", "-q", "-b", branch, str(repo))
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        self.git("-C", str(repo), "add", "a.txt")
        self.git("-C", str(repo), "commit", "-qm", "init")
        return repo

    def write_transcript(self, *edited):
        """A Claude Code transcript whose assistant records edit the given files, oldest first."""
        lines = ['{"type":"user","message":{"role":"user","content":"start"}}', "not json"]
        for index, path in enumerate(edited):
            name = ("Edit", "Write", "NotebookEdit")[index % 3]
            key = "notebook_path" if name == "NotebookEdit" else "file_path"
            lines.append(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "text", "text": "editing"},
                {"type": "tool_use", "id": f"t{index}", "name": name, "input": {key: str(path)}}]}}))
            lines.append(json.dumps({"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": f"t{index}", "content": "ok"}]}}))
        transcript = self.dir / "transcript.jsonl"
        transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return transcript

    def compact_with_transcript(self, cwd, transcript):
        return self.run_hook(SESSION_START, {"hook_event_name": "SessionStart", "source": "compact", "cwd": str(cwd),
                                             "transcript_path": str(transcript)})

    def test_compact_adds_repositories_of_edited_files(self):  # KIT-058
        work = self.make_repo("work", "feat/edited")
        (work / "a.txt").write_text("changed\n", encoding="utf-8")
        older = self.make_repo("older", "feat/older")
        oldest = self.make_repo("oldest", "feat/oldest")
        shell = self.make_repo("shell", "main")
        (self.dir / "scratch").mkdir()
        transcript = self.write_transcript(
            oldest / "a.txt", older / "a.txt", shell / "a.txt", self.dir / "scratch" / "n.txt",
            work / "a.txt", self.dir / "gone" / "x.txt", "relative/path.txt")

        result = self.compact_with_transcript(shell, transcript)

        self.assertEqual(result.returncode, 0)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        head = self.git("-C", str(work), "rev-parse", "--short", "HEAD")
        self.assertTrue(context.startswith(
            "ai-kit: git state after compaction; check the summary against it. " + str(shell) + " at "), context)
        self.assertIn(str(work) + " at " + head + " (edited in this session):\n## feat/edited\n M a.txt", context)
        self.assertIn(str(older) + " at ", context)
        self.assertNotIn(str(oldest), context)  # two repositories at most, most recent edit first
        self.assertEqual(context.count(str(shell) + " at "), 1)

    def test_compact_outside_git_reports_edited_repositories(self):  # KIT-058
        work = self.make_repo("work", "feat/edited")
        result = self.compact_with_transcript(self.dir, self.write_transcript(work / "a.txt"))
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn(str(work) + " at ", context)
        self.assertIn("(edited in this session):\n## feat/edited", context)

    def test_compact_without_a_readable_transcript_reports_cwd_only(self):  # KIT-058
        work = self.make_repo("work", "feat/edited")
        (self.dir / "bad.jsonl").write_bytes(b"\xff\xfe" + b"{" * 1000)
        for transcript in (self.dir / "missing.jsonl", self.dir / "bad.jsonl", self.dir):
            with self.subTest(transcript=transcript.name):
                result = self.compact_with_transcript(work, transcript)
                context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertNotIn("edited in this session", context)
                self.assertIn(str(work) + " at ", context)
        result = self.compact_with_transcript(self.dir, self.dir / "missing.jsonl")
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_each_hook_within_budget(self):
        (self.dir / "notes.txt").touch()
        # Worst case for the KIT-058 read: more than the 4 MB tail, every line an edit outside any repository.
        record = json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Edit", "input": {
            "file_path": str(self.dir / "notes.txt"), "old_string": "a" * 300, "new_string": "b" * 300}}]}})
        transcript = self.dir / "transcript.jsonl"
        transcript.write_text((record + "\n") * (6_000_000 // len(record)), encoding="utf-8")
        cases = (
            ("guard", GUARD, {"tool_name": "Bash", "tool_input": {"command": "git status"}}),
            ("post-edit", POST_EDIT, {"tool_name": "Edit", "tool_input": {"file_path": "notes.txt"}, "cwd": str(self.dir)}),
            ("session-start", SESSION_START, {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(self.dir)}),
            ("compact", SESSION_START, {"hook_event_name": "SessionStart", "source": "compact", "cwd": str(self.dir)}),
            ("compact-transcript", SESSION_START, {"hook_event_name": "SessionStart", "source": "compact",
                                                   "cwd": str(self.dir), "transcript_path": str(transcript)}),
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
