"""The functional layer (KIT-077): the kit synced into the consumer project kept in platforms/ci/fixtures/consumer/,
then that project's own checks, as its CI and its developers run them: the spec-tools action's spec steps, which the
written spec-lint.yml calls pinned to the kit commit, the `verify` recipe of each profile folder's kit module as skill
sdd-implement runs it (`just -f ~/.ai-kit/platforms/kits/just/<stack>.just -d <folder> verify`, with ~/.ai-kit linked
to the kit as the spec-tools action links it on a runner; AI_KIT_DIR unset), `sync-project.sh --check`, and a second
sync that changes nothing. The project carries no copy of the kit: it uses the installed guardrails@ai-kit plugin
(KIT-081 stage 2b), runs the spec tools from the kit (stage 1) and keeps no justfile for the kit's recipes (KIT-085).
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
ACTION_DIR = KIT / "platforms" / "ci" / "actions" / "spec-tools"
ACTION = "ChristianPrzybulinski/agent-rules-kit/platforms/ci/actions/spec-tools"
PROFILE = "docs,python:tools"
JUST = shutil.which("just")
GIT = ("git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false")


def spec_steps():
    """The run lines of the spec-tools action's `spec` steps that a push runs, the commands a consumer's CI runs on
    docs/spec (the baseline step runs on a pull request only)."""
    import yaml  # the functional job installs it; the action's steps themselves need it under CI=1
    steps = yaml.safe_load((ACTION_DIR / "action.yml").read_text(encoding="utf-8"))["runs"]["steps"]
    runs = [step["run"] for step in steps if step.get("if") == "steps.checks.outputs.spec == 'true'"]
    assert len(runs) == 2, runs
    return runs


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
        # The kit runs from ~/.ai-kit, linked as the spec-tools action links it on a runner (KIT-085: the just modules
        # run from there), and from GITHUB_ACTION_PATH for the action's own steps.
        self.home = Path(tmp.name) / "home"
        self.home.mkdir()
        (self.home / ".ai-kit").symlink_to(KIT)
        # A throwaway HOME also moves Python's user site, where a developer's python3 may hold pyyaml and jsonschema;
        # PYTHONUSERBASE keeps the one python3 on PATH had (a CI runner installs them for the system Python).
        userbase = subprocess.run(["python3", "-c", "import site; print(site.getuserbase())"], capture_output=True,
                                  text=True, check=True).stdout.strip()
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, HOME=str(self.home), GITHUB_ACTION_PATH=str(ACTION_DIR),
                        PYTHONUSERBASE=os.environ.get("PYTHONUSERBASE", userbase),
                        AI_KIT_PYTHON=shutil.which("python3"))  # the action's install step exports it (#372)
        self.env.pop("AI_KIT_DIR", None)
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
        for run in spec_steps():
            self.ok(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", run])
        for folder, stack in ((".", "docs"), ("tools", "python")):  # KIT-085: the module, no project justfile
            module = ["-f", str(self.home / ".ai-kit" / "platforms" / "kits" / "just" / f"{stack}.just"),
                      "-d", str(self.repo / folder)]
            self.assertIn("verify", self.ok([JUST, *module, "--summary"]).stdout.split())
            self.ok([JUST, *module, "verify"], cwd=self.repo / folder)
        self.assertIn("consistent with kit", self.sync("--check", *args).stdout)

    def assert_resync_changes_nothing(self, *args):
        self.commit("synced")
        self.sync(*args)
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_sync_then_the_projects_checks_pass(self):
        self.sync("--profile", PROFILE)
        self.assertFalse((self.repo / ".github" / "spec-lint").exists())  # KIT-081 stage 1: no copy of the spec tools
        head = subprocess.run(["git", "-C", str(KIT), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
        workflow = (self.repo / ".github" / "workflows" / "spec-lint.yml").read_text(encoding="utf-8")
        self.assertIn(f"uses: {ACTION}@{head}  # v{(KIT / 'VERSION').read_text(encoding='utf-8').strip()}", workflow)
        self.assertEqual(sorted(p.name for p in self.repo.rglob("*just*")), [])  # KIT-085: no justfile, no copy
        self.assertFalse((self.repo / ".claude" / "skills").exists())  # KIT-081 stage 2b: no copy in the project
        self.assert_own_checks_pass()  # the .ai-kit.yaml stacks hold the profile list: bare runs keep it
        self.assert_resync_changes_nothing()


if __name__ == "__main__":
    unittest.main()
