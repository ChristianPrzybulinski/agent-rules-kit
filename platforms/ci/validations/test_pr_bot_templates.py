"""The two pull-request bot templates (KIT-084): `changelog-consolidate.yml` runs the kit's changelog_fragments.py and
`spec-status-sync.yml` the kit's `spec_trace.py sync-status --write`, each from the kit commit the spec-tools action pins
(KIT-081: no copy in the project), then opens or refreshes one pull request with a token from a secret. Both are
dispatch-only by default and open a pull request only when the tool changed something. The steps' own shell then runs
here against a throwaway repository, with a stub `gh` and a local bare repository as `origin`.

The rules every template follows (actions pinned by SHA, timeouts, persist-credentials, no `${{ }}` in `run:`, a
read-only workflow token) are test_kit_workflows.py's."""
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # as check.sh: without pyyaml a local run skips, a CI=1 run fails
    if os.environ.get("CI"):
        raise
    yaml = None

LAYER = "contract"  # KIT-077 layer (platforms/tools/run_tests.py): the kit's own files, read in-process

KIT = Path(__file__).resolve().parents[3]
TEMPLATES = KIT / "platforms" / "kits" / "github" / "workflows"
ACTION = "ChristianPrzybulinski/agent-rules-kit/platforms/ci/actions/spec-tools@"
# template: (the kit tool, its arguments, the paths it writes, the branch of the pull request)
BOTS = {"changelog-consolidate.yml": ("changelog_fragments.py", "--repo-dir .", "CHANGELOG.md changelog.d",
                                      "chore/changelog-consolidate"),
        "spec-status-sync.yml": ("spec_trace.py", "sync-status --write", "docs/spec", "chore/spec-sync-status")}
TOKEN = "${{ secrets.PR_BOT_TOKEN }}"


def load(name):
    return yaml.safe_load((TEMPLATES / name).read_text(encoding="utf-8"))


def job_steps(name):
    jobs = load(name)["jobs"]
    assert len(jobs) == 1, f"{name} has {len(jobs)} jobs"
    return next(iter(jobs.values()))["steps"]


def by_id(name, step_id):
    found = [s for s in job_steps(name) if s.get("id") == step_id]
    assert len(found) == 1, f"{name} has {len(found)} steps with id {step_id!r}"
    return found[0]


def pr_step(name):
    found = [s for s in job_steps(name) if "gh pr create" in s.get("run", "")]
    assert len(found) == 1, f"{name} has {len(found)} steps that open a pull request"
    return found[0]


@unittest.skipIf(yaml is None, "pyyaml is not installed (CI=1 makes it required)")
class BotTemplates(unittest.TestCase):
    def test_each_runs_only_on_dispatch_and_says_how_to_add_a_schedule(self):
        for name in BOTS:
            text = (TEMPLATES / name).read_text(encoding="utf-8")
            with self.subTest(template=name):
                on = load(name).get(True, load(name).get("on"))  # PyYAML reads the bare key `on` as True
                self.assertEqual(on, {"workflow_dispatch": None})
                self.assertRegex(text, r"(?m)^#\s+schedule:\s*$")
                self.assertRegex(text, r"(?m)^#\s+- cron: '[^']+'")

    def test_each_runs_the_kit_tool_after_the_spec_tools_action(self):
        for name, (tool, args, _, _) in BOTS.items():
            steps = job_steps(name)
            with self.subTest(template=name):
                links = [i for i, s in enumerate(steps) if s.get("uses", "").startswith(ACTION)]
                calls = [i for i, s in enumerate(steps)
                         if f'python3 "$AI_KIT_DIR/platforms/ci/validations/{tool}" {args}' in s.get("run", "")]
                self.assertEqual(len(links), 1, "one spec-tools step")
                self.assertEqual(len(calls), 1, f"one step that runs {tool} {args}")
                self.assertLess(links[0], calls[0])
                self.assertEqual(steps[links[0]].get("with"), {"checks": "none"})
                self.assertEqual(steps[calls[0]].get("id"), "tool")
                text = (TEMPLATES / name).read_text(encoding="utf-8")
                self.assertNotIn(".github/spec-lint", text)
                self.assertNotIn("--body-file .github", text)  # the body is the template's, never a project file

    def test_a_pull_request_opens_only_when_the_tool_changed_something(self):
        for name, (_, _, paths, branch) in BOTS.items():
            tool, pr = by_id(name, "tool"), pr_step(name)
            with self.subTest(template=name):
                self.assertIn(f'git status --porcelain -- {paths}', tool["run"])
                self.assertIn('echo "changed=true" >> "$GITHUB_OUTPUT"', tool["run"])
                self.assertEqual(pr.get("if"), "steps.tool.outputs.changed == 'true'")
                self.assertEqual(pr["env"]["BRANCH"], branch)
                self.assertIn("gh pr edit", pr["run"])  # a second run refreshes the open pull request
                self.assertNotIn("gh pr merge", (TEMPLATES / name).read_text(encoding="utf-8"))

    def test_only_the_steps_that_need_the_token_hold_it(self):
        """The checkout keeps no credential; the push and the pull request use the secret, and sync-status reads the
        task issues with it too."""
        for name, holders in (("changelog-consolidate.yml", ["pr"]), ("spec-status-sync.yml", ["tool", "pr"])):
            text = (TEMPLATES / name).read_text(encoding="utf-8")
            with self.subTest(template=name):
                self.assertEqual(set(re.findall(r"\$\{\{\s*secrets\.[^}]*\}\}", text)), {TOKEN})
                found = ["pr" if "gh pr create" in s.get("run", "") else s.get("id", s.get("name", "?"))
                         for s in job_steps(name) if TOKEN in json.dumps(s.get("env", {}))]
                self.assertEqual(found, holders)
                self.assertEqual(pr_step(name)["env"]["GH_TOKEN"], TOKEN)
                self.assertNotIn("token:", text)  # never a checkout credential
                self.assertNotIn("GH_TOKEN@", pr_step(name)["run"])  # never in a URL


def executable(path, text):
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


# Records each call; `gh pr list` prints $STUB_OPEN_PR (the open pull request's number, or nothing).
GH_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$STUB_LOG"
if [ "$1 $2" = "pr list" ]; then printf '%s\\n' "${STUB_OPEN_PR:-}"; fi
"""


@unittest.skipIf(yaml is None, "pyyaml is not installed (CI=1 makes it required)")
class BotRuns(unittest.TestCase):
    """The tool step and the pull request step of each template, run as a runner runs them: AI_KIT_DIR is this kit, a
    bare repository is `origin`, and `gh` is a stub that records its calls."""

    LAYER = "integration"  # git, the kit tool and the steps' shell in a throwaway repository
    COVERS = ("platforms/kits/github/workflows/changelog-consolidate.yml",
              "platforms/kits/github/workflows/spec-status-sync.yml",
              "platforms/ci/validations/changelog_fragments.py")

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.origin = self.tmp / "origin.git"
        self.repo = self.tmp / "repo"
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        executable(self.bin / "gh", GH_STUB)
        self.log = self.tmp / "gh.log"
        (self.tmp / "gitconfig").write_text("", encoding="utf-8")
        self.git(self.tmp, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.git(self.tmp, "init", "-q", "-b", "main", str(self.repo))
        (self.repo / "CHANGELOG.md").write_text("# Changelog\n\n## [Unreleased]\n\n## [0.1.0]\n- x\n", encoding="utf-8")
        (self.repo / "changelog.d").mkdir()
        (self.repo / "changelog.d" / "README.md").write_text("fragments\n", encoding="utf-8")
        (self.repo / "docs" / "spec").mkdir(parents=True)
        (self.repo / "docs" / "spec" / "spec.md").write_text("# spec\n", encoding="utf-8")
        self.commit("base")
        self.git(self.repo, "remote", "add", "origin", str(self.origin))
        self.git(self.repo, "push", "-q", "origin", "main")

    def env(self, **extra):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "GH_", "CI"))}
        env.update(PATH=f"{self.bin}{os.pathsep}{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}",
                   HOME=str(self.tmp), GIT_CONFIG_GLOBAL=str(self.tmp / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
                   STUB_LOG=str(self.log), RUNNER_TEMP=str(self.tmp), AI_KIT_DIR=str(KIT))
        env.update(extra)
        return env

    def git(self, cwd, *args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c",
                               "commit.gpgsign=false", *args], cwd=cwd, env=self.env(), check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, message):
        self.git(self.repo, "add", "-A")
        self.git(self.repo, "commit", "-q", "-m", message)

    def run_step(self, step, **env):
        output = self.tmp / "github_output"
        output.write_text("", encoding="utf-8")
        full = self.env(GITHUB_OUTPUT=str(output), **{k: str(v) for k, v in step.get("env", {}).items()
                                                     if "${{" not in str(v)})
        full.update({k: str(v) for k, v in env.items()})
        result = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", step["run"]], cwd=self.repo,
                                env=full, capture_output=True, text=True, check=False, timeout=120)
        result.outputs = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines() if line)
        return result

    def calls(self):
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []

    def test_no_fragment_changes_nothing_and_opens_no_pull_request(self):
        result = self.run_step(by_id("changelog-consolidate.yml", "tool"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.outputs, {"fragments": "0", "changed": "false"})
        self.assertEqual(self.git(self.repo, "status", "--porcelain"), "")

    def test_a_malformed_fragment_fails_the_tool_step_and_writes_nothing(self):
        (self.repo / "changelog.d" / "1.added.md").write_text("bare\n", encoding="utf-8")
        self.commit("bad fragment")
        result = self.run_step(by_id("changelog-consolidate.yml", "tool"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("changelog.d/1.added.md:1:", result.stderr)
        self.assertNotIn("changed", result.outputs)
        self.assertEqual(self.git(self.repo, "status", "--porcelain"), "")

    def test_fragments_become_one_pull_request_and_a_second_run_refreshes_it(self):
        (self.repo / "changelog.d" / "1.added.md").write_text("- a thing\n", encoding="utf-8")
        (self.repo / "changelog.d" / "2.fixed.md").write_text("- a fix\n", encoding="utf-8")
        self.commit("fragments")
        pr = pr_step("changelog-consolidate.yml")
        for open_pr, want in (("", "pr create --head chore/changelog-consolidate --base main"), ("7", "pr edit 7")):
            with self.subTest(open_pr=open_pr):
                self.git(self.repo, "checkout", "-q", "main")  # each run starts from a fresh checkout of the ref
                tool = self.run_step(by_id("changelog-consolidate.yml", "tool"))
                self.assertEqual(tool.returncode, 0, tool.stdout + tool.stderr)
                self.assertEqual(tool.outputs, {"fragments": "2", "changed": "true"})
                self.log.unlink(missing_ok=True)
                done = self.run_step(pr, GH_TOKEN="test-token", BASE="main", N=tool.outputs["fragments"],
                                     STUB_OPEN_PR=open_pr)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                self.assertEqual(self.calls()[0], "pr list --head chore/changelog-consolidate --base main --state "
                                                  "open --json number --jq .[0].number // empty")
                self.assertTrue(self.calls()[1].startswith(want), self.calls())
                self.assertIn("--title chore(changelog): consolidate 2 fragment(s)", self.calls()[1])
        pushed = self.git(self.origin, "show", "--stat", "--format=%s", "chore/changelog-consolidate")
        self.assertIn("chore(changelog): consolidate 2 fragment(s)", pushed)
        self.assertIn("changelog.d/1.added.md", pushed)
        log = self.git(self.origin, "show", "chore/changelog-consolidate:CHANGELOG.md")
        self.assertIn("## [Unreleased]\n\n### Added\n- a thing\n\n### Fixed\n- a fix\n", log)
        body = (self.tmp / "body.md").read_text(encoding="utf-8")
        self.assertIn('"entries": 2', body)
        self.assertNotIn("test-token", body + done.stdout + done.stderr)

    def test_the_status_pull_request_commits_only_docs_spec(self):
        pr = pr_step("spec-status-sync.yml")
        (self.repo / "docs" / "spec" / "spec.md").write_text("# spec\n\nsynced\n", encoding="utf-8")
        (self.tmp / "sync.txt").write_text("sync-status: wrote 1 file(s)\n", encoding="utf-8")
        done = self.run_step(pr, GH_TOKEN="test-token", BASE="main")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertTrue(self.calls()[1].startswith("pr create --head chore/spec-sync-status --base main"), self.calls())
        files = [line for line in self.git(self.origin, "show", "--name-only", "--format=%s",
                                           "chore/spec-sync-status").splitlines() if line]
        self.assertEqual(files, ["chore(spec): sync status from GitHub", "docs/spec/spec.md"])
        self.assertIn("sync-status: wrote 1 file(s)", (self.tmp / "body.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
