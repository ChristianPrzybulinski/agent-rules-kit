"""guardrails guard (KIT-020): git branch -D passes only for one branch whose tip is a merged PR's head; anything else fails closed."""
import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[3] / "plugins" / "guardrails" / "hooks" / "hooks.json"
GUARD_HOOK = json.loads(HOOKS.read_text(encoding="utf-8"))["hooks"]["PreToolUse"][0]["hooks"][0]
GUARD, GUARD_TIMEOUT = GUARD_HOOK["command"], GUARD_HOOK["timeout"]
BRANCH = "feat/kit-020"
OTHER_SHA = "0" * 40
GH_ARGS = ["pr", "list", "--head", BRANCH, "--state", "merged", "--json", "headRefOid"]
# Each command names the merged branch, yet is not exactly `git branch -D <one name>`: the guard denies it without asking gh.
OTHER_SHAPES = (
    f"git branch -D {BRANCH} other",
    f"git branch -D {BRANCH} && git status",
    f"git branch -D {BRANCH}; rm -rf build",
    f"git branch -D {BRANCH}\nreboot",
    f"cd . && git branch -D {BRANCH}",
    f"git branch -D -- {BRANCH}",
    f'git branch -D "{BRANCH}"',
    f"git branch -D $(echo {BRANCH})",
    f"git branch --delete --force {BRANCH}",
    f"git branch -Df {BRANCH}",
    # A git global option before the subcommand (KIT-053).
    f"git -C . branch -D {BRANCH}",
    f"git --no-pager branch -D {BRANCH}",
    f"git -c core.x=y branch -D {BRANCH}",
    # A command prefix or a line break before git (KIT-054).
    f"GIT_DIR=.git git branch -D {BRANCH}",
    f"/usr/bin/git branch -D {BRANCH}",
    f"command git branch -D {BRANCH}",
    f"nice git branch -D {BRANCH}",
    f"cd .\ngit branch -D {BRANCH}",
)


class MergedBranchGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name).resolve()
        self.bin = self.dir / "bin"
        self.bin.mkdir()
        # PATH holds only these links, so a gh installed on the machine is never reached.
        for name, target in (("python3", sys.executable), ("git", shutil.which("git")), ("bash", shutil.which("bash"))):
            (self.bin / name).symlink_to(target)
        self.env = {"PATH": str(self.bin), "HOME": str(self.dir), "GIT_CEILING_DIRECTORIES": str(self.dir.parent)}
        self.repo = self.dir / "repo"
        self.git("init", "-q", "-b", "main", str(self.repo))
        self.git("-C", str(self.repo), "commit", "-q", "--allow-empty", "-m", "init")
        self.git("-C", str(self.repo), "branch", BRANCH)
        self.tip = self.git("-C", str(self.repo), "rev-parse", f"refs/heads/{BRANCH}")
        self.calls = self.dir / "gh-calls.json"

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=kit", "-c", "user.email=kit@example.invalid", *args],
                              capture_output=True, text=True, env=self.env, check=True).stdout.strip()

    def stub_gh(self, body):
        """Install a gh that records its working directory and arguments, then runs body."""
        record = f"python3 -c 'import json,os,sys;print(json.dumps([os.getcwd()]+sys.argv[1:]))' \"$@\" > '{self.calls}'"
        script = self.bin / "gh"
        script.write_text(f"#!{shutil.which('bash')}\n{record}\n{body}\n", encoding="utf-8")
        script.chmod(0o755)

    def merged_pr(self, sha):
        self.stub_gh(f"printf '%s' '{json.dumps([{'headRefOid': sha}])}'")

    def guard(self, command):
        # The hook process starts outside the repository; only the payload's cwd points at it.
        payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(self.repo)}
        return subprocess.run(["bash", "-c", GUARD], input=json.dumps(payload), text=True, capture_output=True,
                              timeout=GUARD_TIMEOUT, cwd=self.dir, env=self.env, check=False)

    def assert_denied(self, result):
        self.assertEqual(result.returncode, 2, result.stderr)
        reason = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertTrue(reason.startswith("ai-kit guard: "), reason)

    def test_allows_branch_at_merged_pr_head(self):
        self.merged_pr(self.tip)

        result = self.guard(f"git branch -D {BRANCH}")

        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)
        self.assertEqual(json.loads(self.calls.read_text(encoding="utf-8")), [str(self.repo), *GH_ARGS])

    def test_denies_commits_after_the_merged_head(self):
        self.merged_pr(OTHER_SHA)
        self.assert_denied(self.guard(f"git branch -D {BRANCH}"))

    def test_denies_without_merged_pr(self):
        self.stub_gh("printf '[]'")
        self.assert_denied(self.guard(f"git branch -D {BRANCH}"))

    def test_denies_when_gh_fails(self):
        for body in ("echo 'To get started with GitHub CLI, please run:  gh auth login' >&2; exit 4", "printf 'not json'"):
            with self.subTest(body=body):
                self.stub_gh(body)
                self.assert_denied(self.guard(f"git branch -D {BRANCH}"))

    def test_denies_when_gh_is_missing(self):
        self.assert_denied(self.guard(f"git branch -D {BRANCH}"))

    def test_denies_when_gh_hangs_before_the_hook_timeout(self):
        self.stub_gh(f"exec {shutil.which('sleep')} 30")
        start = time.perf_counter()

        result = self.guard(f"git branch -D {BRANCH}")

        self.assert_denied(result)
        self.assertLess(time.perf_counter() - start, GUARD_TIMEOUT - 2)

    def test_denies_unknown_branch_without_asking_gh(self):
        self.merged_pr(self.tip)
        self.assert_denied(self.guard("git branch -D feat/never-created"))
        self.assertFalse(self.calls.exists())

    def test_denies_every_other_shape_without_asking_gh(self):
        self.merged_pr(self.tip)
        for command in OTHER_SHAPES:
            with self.subTest(command=command):
                self.assert_denied(self.guard(command))
                self.assertFalse(self.calls.exists())


if __name__ == "__main__":
    unittest.main()
