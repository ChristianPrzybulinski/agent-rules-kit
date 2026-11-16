"""The functional layer (KIT-077): the kit synced into the consumer project kept in platforms/ci/fixtures/consumer/,
then that project's own checks, as its CI and its developers run them: the spec-lint workflow's validation step,
`just verify` in each profile folder, `sync-project.sh --check`, and a second sync that changes nothing. The project
uses the installed guardrails@ai-kit plugin; the vendored mode that pinned the kit (KIT-072) went with KIT-081 stage 2b.
ci-full runs this layer on push to main, nightly and before a release, with the pinned just installed; a CI run without
just fails instead of skipping."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

LAYER = "functional"
KIT = Path(__file__).resolve().parents[3]
FIXTURE = KIT / "platforms" / "ci" / "fixtures" / "consumer"
SYNC = KIT / "platforms" / "tools" / "sync-project.sh"
SPEC_LINT = KIT / "platforms" / "kits" / "github" / "workflows" / "spec-lint.yml"
PROFILE = "docs,python:tools"
JUST = shutil.which("just")
GIT = ("git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false")


def validation_step():
    """The run line of spec-lint.yml's validation step, the command a consumer's CI runs on docs/spec."""
    lines = SPEC_LINT.read_text(encoding="utf-8").splitlines()
    name = "- name: Validate frontmatter and FEAT/REQ references"
    start = next(i for i, line in enumerate(lines) if line.strip() == name)
    run = lines[start + 1].strip()
    assert run.startswith("run: "), run
    return run[len("run: "):]


class ConsumerFixture(unittest.TestCase):
    def setUp(self):
        if JUST is None:
            if os.environ.get("CI"):
                self.fail("just is not on PATH: the functional layer's CI job installs the pinned just")
            self.skipTest("just is not installed (CI=1 makes it required)")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "consumer"
        shutil.copytree(FIXTURE, self.repo)
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull)
        self.git("init", "-q", "-b", "main")
        self.commit("the fixture as the kit keeps it")

    def run_in(self, argv, cwd=None):
        return subprocess.run(argv, cwd=cwd or self.repo, env=self.env, capture_output=True, text=True,
                              errors="replace", check=False, timeout=600)

    def ok(self, argv, cwd=None):
        result = self.run_in(argv, cwd)
        self.assertEqual(result.returncode, 0, f"{' '.join(map(str, argv))}\n{result.stdout}{result.stderr}")
        return result

    def git(self, *args):
        return self.ok([*GIT, *args])

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)

    def sync(self, *args):
        return self.ok(["bash", str(SYNC), *args, str(self.repo)])

    def assert_own_checks_pass(self, *args):
        self.ok(["bash", "-c", validation_step()])
        self.assertIn("lint", self.ok([JUST, "--summary"]).stdout.split())
        self.ok([JUST, "verify"])
        self.ok([JUST, "verify"], cwd=self.repo / "tools")
        self.assertIn("consistent with kit", self.sync("--check", *args).stdout)

    def assert_resync_changes_nothing(self, *args):
        self.commit("synced")
        self.sync(*args)
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_sync_then_the_projects_checks_pass(self):
        self.sync("--profile", PROFILE)
        self.assertTrue((self.repo / ".github" / "spec-lint" / "check_spec.py").is_file())
        self.assertTrue((self.repo / "tools" / "kit.just").is_file())
        self.assertFalse((self.repo / ".claude" / "skills").exists())  # KIT-081 stage 2b: no copy in the project
        self.assert_own_checks_pass()  # the CLAUDE.md marker records the profile list: bare runs keep it
        self.assert_resync_changes_nothing()


if __name__ == "__main__":
    unittest.main()
