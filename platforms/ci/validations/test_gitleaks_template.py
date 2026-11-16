"""The gitleaks composite action (KIT-084) and the workflow template that calls it (KIT-074). A project pins the action
by SHA from any workflow and keeps one job per run, since GitHub calls a reusable workflow across repositories only
from a repository's .github/workflows/. The action installs the gitleaks CLI at the pin of the kit's own gitleaks.yml
(version and sha-256, so the two cannot drift), takes a `config` input and scans a pull request's commits, or the whole
history on a push or a dispatch. Its scan step runs here against a throwaway repository with the local gitleaks
(redacted finding, .gitleaksignore, the config path input, the range by event)."""
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # as check.sh: without pyyaml a local run skips, a CI=1 run fails
    if os.environ.get("CI"):
        raise
    yaml = None

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/kits/github/workflows/gitleaks.yml", "platforms/ci/actions/gitleaks/**")

KIT = Path(__file__).resolve().parents[3]
TEMPLATE = KIT / "platforms" / "kits" / "github" / "workflows" / "gitleaks.yml"
ACTION_DIR = KIT / "platforms" / "ci" / "actions" / "gitleaks"
ACTION = ACTION_DIR / "action.yml"
KIT_WORKFLOW = KIT / ".github" / "workflows" / "gitleaks.yml"
USES = "ChristianPrzybulinski/agent-rules-kit/platforms/ci/actions/gitleaks@"
GITLEAKS = shutil.which("gitleaks")


def action():
    return yaml.safe_load(ACTION.read_text(encoding="utf-8"))


def action_step(prefix):
    found = [s for s in action()["runs"]["steps"] if s.get("name", "").startswith(prefix)]
    assert len(found) == 1, f"action.yml has {len(found)} steps named {prefix!r}..."
    return found[0]


def install_pins(steps):
    """(GITLEAKS_VERSION, GITLEAKS_SHA256) of the one `install gitleaks` step among the steps."""
    found = [s for s in steps if s.get("name", "").startswith("install gitleaks")]
    assert len(found) == 1, f"{len(found)} `install gitleaks` steps"
    return found[0]["env"]["GITLEAKS_VERSION"], found[0]["env"]["GITLEAKS_SHA256"]


@unittest.skipIf(yaml is None, "pyyaml is not installed (CI=1 makes it required)")
class ActionFile(unittest.TestCase):
    LAYER = "contract"  # the kit's own files, read in-process

    def test_a_composite_action_with_the_pinned_cli(self):
        data = action()
        self.assertEqual(data["runs"]["using"], "composite")
        self.assertEqual(data["inputs"]["config"].get("default"), "")
        version, digest = install_pins(data["runs"]["steps"])
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertIn("sha256sum -c -", action_step("install gitleaks")["run"])
        # the CLI only, so no step uses another action, gitleaks/gitleaks-action least of all: it needs a
        # GITLEAKS_LICENSE secret in an organization's repository
        self.assertEqual([s["uses"] for s in data["runs"]["steps"] if "uses" in s], [])
        for item in data["runs"]["steps"]:
            with self.subTest(step=item.get("name")):
                self.assertNotIn("${{", item.get("run", ""))  # pass it through env: instead
                self.assertEqual(item.get("shell"), "bash")  # a composite run step must name its shell

    def test_the_action_and_the_kits_own_scan_pin_the_same_cli(self):
        """One version and sha-256: the kit's required gitleaks check runs the same CLI the action gives projects, and
        test_kit_workflows.py holds the CI jobs that run the gitleaks tests to that pin too."""
        kit = yaml.safe_load(KIT_WORKFLOW.read_text(encoding="utf-8"))
        kit_steps = [s for job in kit["jobs"].values() for s in job["steps"]]
        self.assertEqual(install_pins(action()["runs"]["steps"]), install_pins(kit_steps))

    def test_the_scan_redacts_and_takes_the_config_input(self):
        scan = action_step("scan")
        self.assertEqual(scan["env"]["CONFIG"], "${{ inputs.config }}")
        self.assertIn("--redact", scan["run"])
        self.assertIn('args+=(--config "$CONFIG")', scan["run"])

    def test_its_readme_documents_every_input(self):
        readme = (ACTION_DIR / "README.md").read_text(encoding="utf-8")
        for name in action()["inputs"]:
            self.assertIn(f"| `{name}` |", readme)

    def test_the_kit_lints_and_updates_it_as_it_does_the_spec_tools_action(self):
        ci = yaml.safe_load((KIT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
        zizmor = [s["run"] for s in ci["jobs"]["workflow-lint"]["steps"] if s.get("run", "").startswith("zizmor")]
        self.assertEqual(len(zizmor), 1)
        self.assertIn("platforms/ci/actions/*/action.yml", zizmor[0])  # the glob covers this action
        dependabot = yaml.safe_load((KIT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
        self.assertIn("/platforms/ci/actions/gitleaks",
                      {u.get("directory") for u in dependabot["updates"] if u["package-ecosystem"] == "github-actions"})


@unittest.skipIf(yaml is None, "pyyaml is not installed (CI=1 makes it required)")
class Template(unittest.TestCase):
    LAYER = "contract"  # the kit's own files, read in-process

    def test_the_template_calls_the_pinned_action_in_its_one_job(self):
        """The logic lives in the action: the template holds no CLI pin and no scan script of its own."""
        workflow = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
        self.assertEqual(len(workflow["jobs"]), 1)  # one billed job per run
        steps = next(iter(workflow["jobs"].values()))["steps"]
        self.assertTrue(steps[0]["uses"].startswith("actions/checkout@"))
        self.assertEqual(steps[0]["with"]["fetch-depth"], 0)  # the whole history, and a pull request's base commit
        calls = [s for s in steps if s.get("uses", "").startswith(USES)]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].get("with"), {"config": "${{ inputs.config }}"})
        self.assertEqual([s for s in steps if "run" in s], [])
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertNotIn("GITLEAKS_VERSION", text)

    def test_the_template_keeps_its_triggers_and_config_input(self):
        workflow = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
        on = workflow.get(True, workflow.get("on"))  # PyYAML reads the bare key `on` as True
        self.assertEqual(sorted(on), ["pull_request", "push", "workflow_call", "workflow_dispatch"])
        for event in ("workflow_call", "workflow_dispatch"):
            self.assertEqual(on[event]["inputs"]["config"]["default"], "")


@unittest.skipIf(yaml is None or (GITLEAKS is None and not os.environ.get("CI")),
                 "pyyaml or gitleaks is not available (CI=1 makes both required)")
class Scan(unittest.TestCase):
    """The action's scan step as a runner runs it, on a repository with a fabricated token (built at run time, never in
    this file) in an old commit of main and a pull request branch on top."""

    def setUp(self):
        if GITLEAKS is None:  # KIT-077: the CI jobs that run this layer install the pinned gitleaks
            self.fail("gitleaks is not on PATH")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runner_temp = Path(self.tmp.name) / "runner"
        (self.runner_temp / "gitleaks-bin").mkdir(parents=True)
        (self.runner_temp / "gitleaks-bin" / "gitleaks").symlink_to(GITLEAKS)  # where the install step puts it
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.token = "ghp_" + secrets.token_hex(18)
        self.git("init", "-q", "-b", "main")
        self.commit("app.env", f"GITHUB_TOKEN={self.token}\n")
        self.commit("app.env", "GITHUB_TOKEN=\n")
        self.base = self.head()
        self.git("checkout", "-q", "-b", "feature")
        self.commit("notes.md", "a clean change\n")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@t",
                               "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, text=True)

    def commit(self, name, text):
        (self.repo / name).write_text(text, encoding="utf-8")
        self.git("add", name)
        self.git("commit", "-q", "-m", f"edit {name}")

    def head(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    def scan(self, event, config="", base=None):
        report = Path(self.tmp.name) / "report.json"
        report.unlink(missing_ok=True)
        env = dict(os.environ, GITHUB_EVENT_NAME=event, BASE_SHA=base or self.base, HEAD_SHA=self.head(),
                   CONFIG=config, RUNNER_TEMP=str(self.runner_temp),
                   GITLEAKS_REPORT=str(report))  # the test's own report file, read below
        script = action_step("scan")["run"]
        self.assertIn('"${args[@]}" .', script)  # the line the report flags are added to
        script = script.replace('"${args[@]}" .', '"${args[@]}" --report-format json --report-path "$GITLEAKS_REPORT" .')
        result = subprocess.run(["bash", "--noprofile", "--norc", "-c", script], cwd=self.repo, env=env,
                                capture_output=True, text=True, timeout=60)
        result.findings = json.loads(report.read_text(encoding="utf-8")) if report.exists() else []
        return result

    def test_a_pull_request_scans_only_its_own_commits(self):
        result = self.scan("pull_request")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"gitleaks range: {self.base}..{self.head()}", result.stdout)

    def test_a_secret_the_pull_request_adds_fails_and_stays_redacted(self):
        self.commit("feature.env", f"GITHUB_TOKEN={self.token}\n")
        result = self.scan("pull_request")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(len(result.findings), 1)
        self.assertNotIn(self.token, result.stdout + result.stderr)

    def test_a_push_and_a_dispatch_scan_the_whole_history(self):
        for event in ("push", "workflow_dispatch"):
            with self.subTest(event=event):
                result = self.scan(event)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("gitleaks range: HEAD", result.stdout)
                self.assertNotIn(self.token, result.stdout + result.stderr)

    def test_a_pull_request_base_missing_from_the_checkout_is_named(self):
        result = self.scan("pull_request", base="0" * 40)
        self.assertEqual(result.returncode, 1)
        self.assertIn("::error::gitleaks: the base commit 0000000000000000000000000000000000000000 is not in the "
                      "checkout; check it out with fetch-depth: 0", result.stdout)

    def test_gitleaksignore_holds_a_reviewed_fingerprint(self):
        first = self.scan("push")
        self.assertEqual(len(first.findings), 1, first.stdout + first.stderr)
        (self.repo / ".gitleaksignore").write_text(first.findings[0]["Fingerprint"] + "\n", encoding="utf-8")
        result = self.scan("push")
        self.assertEqual((result.returncode, result.findings), (0, []), result.stdout + result.stderr)

    def test_the_config_input_names_an_allowlist(self):
        (self.repo / "ci").mkdir()
        (self.repo / "ci" / "gitleaks.toml").write_text(
            '[extend]\nuseDefault = true\n\n[[allowlists]]\ndescription = "fixture"\npaths = [\'\'\'^app\\.env$\'\'\']\n',
            encoding="utf-8")
        result = self.scan("push", config="ci/gitleaks.toml")
        self.assertEqual((result.returncode, result.findings), (0, []), result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
