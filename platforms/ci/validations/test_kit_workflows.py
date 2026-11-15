"""The kit's own required workflows (KIT-076): ci.yml, gitleaks.yml and codeql.yml run on every pull request to main, on
pushes to main and on demand (CodeQL also weekly), never on pull_request_target, with a read-only default token, per-ref
concurrency and the check names the ruleset requires. Every kit workflow and every template projects copy pins its
actions by commit SHA, sets a timeout and its checkout's persist-credentials, keeps `${{ }}` out of `run:` and is
linted by the pinned actionlint and zizmor; Dependabot watches both folders. The gitleaks scan step runs against a
throwaway repository: a pull request scans its own commits, a push to main the whole history."""
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

KIT = Path(__file__).resolve().parents[3]
WORKFLOWS = KIT / ".github" / "workflows"
TEMPLATES = KIT / "platforms" / "kits" / "github" / "workflows"
# The ruleset requires these contexts: a renamed job would leave it waiting for the old name on every pull request.
CHECKS = {"ci.yml": ["ci", "workflow-lint"], "gitleaks.yml": ["gitleaks"],
          "codeql.yml": ["codeql (python)", "codeql (actions)"]}
TRIGGERS = {"pull_request": {"branches": ["main"]}, "push": {"branches": ["main"]}, "workflow_dispatch": None}
WEEKLY = re.compile(r"^\d{1,2} \d{1,2} \* \* [0-6]$")
# The one checkout that keeps its credential: `git lfs pull` in the same job authenticates with it.
KEEPS_CREDENTIAL = {("ci-godot.yml", "import-and-test")}
JOB_GRANTS = {"contents": "read", "security-events": "write"}  # security-events: CodeQL's SARIF upload only
PINNED = re.compile(r"^\s*-?\s*uses:\s*[\w.-]+/[\w./-]+@[0-9a-f]{40}\s+#\s*v\d+(\.\d+)*\s*$")
GITLEAKS = shutil.which("gitleaks")


def load(name, folder=WORKFLOWS):
    return yaml.safe_load((folder / name).read_text(encoding="utf-8"))


def every_workflow():
    """(path, parsed) for the kit's own workflows and the templates projects copy."""
    paths = sorted(WORKFLOWS.glob("*.yml")) + sorted(TEMPLATES.glob("*.yml"))
    return [(path, yaml.safe_load(path.read_text(encoding="utf-8"))) for path in paths]


def triggers(workflow):
    return workflow.get(True, workflow.get("on"))  # PyYAML reads the bare key `on` as True


def contexts(job):
    """The check-run names a job reports: its `name` with each matrix value filled in."""
    names = [job.get("name", "")]
    for key, values in job.get("strategy", {}).get("matrix", {}).items():
        token = "${{ matrix.%s }}" % key
        names = [name.replace(token, str(value)) for name in names for value in values]
    return names


def steps(workflow):
    return [step for job in workflow["jobs"].values() for step in job["steps"]]


@unittest.skipIf(yaml is None, "pyyaml is not installed (CI=1 makes it required)")
class RequiredWorkflows(unittest.TestCase):
    def test_each_runs_on_pull_requests_and_pushes_to_main_and_on_demand(self):
        for name in CHECKS:
            on = dict(triggers(load(name)))
            schedule = on.pop("schedule", None)
            with self.subTest(workflow=name):
                self.assertEqual(on, TRIGGERS)
                if name == "codeql.yml":  # weekly too; GitHub disables a public repository's schedule after 60 idle days
                    self.assertEqual(len(schedule), 1)
                    self.assertRegex(schedule[0]["cron"], WEEKLY)
                else:
                    self.assertIsNone(schedule)

    def test_no_kit_workflow_runs_fork_code_with_the_base_token(self):
        for path in sorted(WORKFLOWS.glob("*.yml")):
            with self.subTest(workflow=path.name):
                on = triggers(load(path.name))
                keys = {on} if isinstance(on, str) else set(on)
                self.assertFalse(keys & {"pull_request_target", "workflow_run"})

    def test_the_token_is_read_only_unless_a_job_needs_more(self):
        for name in CHECKS:
            workflow = load(name)
            with self.subTest(workflow=name):
                self.assertEqual(workflow.get("permissions"), {"contents": "read"})
                for job in workflow["jobs"].values():
                    for scope, level in job.get("permissions", {}).items():
                        self.assertEqual(JOB_GRANTS.get(scope), level, f"{scope}: {level}")
                checkouts = [s for s in steps(workflow) if s.get("uses", "").startswith("actions/checkout@")]
                self.assertTrue(checkouts)
                for step in checkouts:
                    self.assertIs(step.get("with", {}).get("persist-credentials"), False)

    def test_a_newer_commit_cancels_the_older_run_on_the_same_ref(self):
        for name in CHECKS:
            with self.subTest(workflow=name):
                self.assertEqual(load(name).get("concurrency"),
                                 {"group": "${{ github.workflow }}-${{ github.ref }}", "cancel-in-progress": True})

    def test_workflow_lint_runs_pinned_actionlint_and_zizmor_on_both_folders(self):
        job = load("ci.yml")["jobs"]["workflow-lint"]
        install = next((s for s in job["steps"] if s.get("name", "").startswith("install actionlint")), None)
        self.assertIsNotNone(install, "no `install actionlint and zizmor` step")
        for tool in ("ACTIONLINT", "ZIZMOR"):
            self.assertRegex(install["env"][f"{tool}_VERSION"], r"^\d+\.\d+\.\d+$")
            self.assertRegex(install["env"][f"{tool}_SHA256"], r"^[0-9a-f]{64}$")
        self.assertIn("sha256sum -c -", install["run"])
        runs = {s["run"].split()[0]: s["run"] for s in job["steps"] if "run" in s and s is not install}
        for tool in ("actionlint", "zizmor"):
            self.assertIn(".github/workflows/*.yml platforms/kits/github/workflows/*.yml", runs.get(tool, ""), tool)
        self.assertNotIn("--persona", runs["zizmor"])  # the default persona is the gate the docs state


@unittest.skipIf(yaml is None, "pyyaml is not installed (CI=1 makes it required)")
class EveryWorkflow(unittest.TestCase):
    """The kit's own workflows and the templates projects copy (KIT-076)."""

    def test_every_action_is_pinned_by_commit_sha_with_its_version(self):
        for path, _ in every_workflow():
            lines = [line for line in path.read_text(encoding="utf-8").splitlines()
                     if re.match(r"^\s*-?\s*uses:", line)]
            with self.subTest(workflow=path.name):
                self.assertTrue(lines)
                for line in lines:
                    self.assertRegex(line, PINNED)

    def test_every_job_has_a_timeout_within_the_hosted_limit(self):
        for path, workflow in every_workflow():
            for name, job in workflow["jobs"].items():
                with self.subTest(workflow=path.name, job=name):
                    self.assertIsInstance(job.get("timeout-minutes"), int)
                    self.assertTrue(1 <= job["timeout-minutes"] <= 360)

    def test_every_checkout_states_persist_credentials(self):
        for path, workflow in every_workflow():
            for name, job in workflow["jobs"].items():
                for step in job["steps"]:
                    if not step.get("uses", "").startswith("actions/checkout@"):
                        continue
                    with self.subTest(workflow=path.name, job=name):
                        keep = (path.name, name) in KEEPS_CREDENTIAL
                        self.assertIs(step.get("with", {}).get("persist-credentials"), keep)

    def test_no_expression_is_spliced_into_a_run_script(self):
        for path, workflow in every_workflow():
            for name, job in workflow["jobs"].items():
                for step in job["steps"]:
                    with self.subTest(workflow=path.name, job=name, step=step.get("name", step.get("run", ""))[:40]):
                        self.assertNotIn("${{", step.get("run", ""))  # pass it through env: instead

    def test_the_workflow_token_never_writes_by_default(self):
        for path, workflow in every_workflow():
            with self.subTest(workflow=path.name):
                self.assertIn("permissions", workflow)
                grants = workflow["permissions"] or {}
                self.assertNotIn("write", grants.values() if isinstance(grants, dict) else [grants])

    def test_dependabot_updates_the_actions_of_both_folders(self):
        config = yaml.safe_load((KIT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
        directories = {u.get("directory") for u in config["updates"] if u["package-ecosystem"] == "github-actions"}
        self.assertEqual(directories, {"/", "/platforms/kits/github/workflows"})

    def test_the_check_names_are_stable_and_never_skipped(self):
        for name, expected in CHECKS.items():
            jobs = load(name)["jobs"].values()
            with self.subTest(workflow=name):
                self.assertEqual([c for job in jobs for c in contexts(job)], expected)
                for job in jobs:
                    self.assertNotIn("if", job)  # a skipped required job reports success
                    self.assertIsInstance(job.get("timeout-minutes"), int)

    def test_codeql_keeps_python_and_actions_without_a_build(self):
        workflow = load("codeql.yml")
        job = workflow["jobs"]["analyze"]
        self.assertEqual(job["strategy"]["matrix"]["language"], ["python", "actions"])
        init = [s for s in job["steps"] if s.get("uses", "").startswith("github/codeql-action/init@")]
        self.assertEqual([s["with"]["build-mode"] for s in init], ["none"])

    def test_gitleaks_is_the_pinned_cli_over_the_full_history_with_values_redacted(self):
        workflow = load("gitleaks.yml")
        text = (WORKFLOWS / "gitleaks.yml").read_text(encoding="utf-8")
        self.assertEqual([s["uses"] for s in steps(workflow) if "gitleaks" in s.get("uses", "")], [])
        self.assertNotIn("secrets.", text)  # the CLI needs no token
        checkout = [s for s in steps(workflow) if s.get("uses", "").startswith("actions/checkout@")]
        self.assertEqual([s["with"]["fetch-depth"] for s in checkout], [0])
        install = next((s for s in steps(workflow) if s.get("name", "").startswith("install gitleaks")), None)
        self.assertIsNotNone(install, "no `install gitleaks` step")
        self.assertRegex(install["env"]["GITLEAKS_VERSION"], r"^\d+\.\d+\.\d+$")
        self.assertRegex(install["env"]["GITLEAKS_SHA256"], r"^[0-9a-f]{64}$")
        self.assertIn("sha256sum -c -", install["run"])
        self.assertIsNotNone(scan_step(), "no `scan` step")
        self.assertIn("--redact", scan_step()["run"])


def scan_step():
    return next((s for s in steps(load("gitleaks.yml")) if s.get("name", "").startswith("scan")), None)


@unittest.skipIf(yaml is None or GITLEAKS is None, "pyyaml or gitleaks is not available")
class GitleaksRange(unittest.TestCase):
    """The scan step's script, run as the workflow runs it, on main with a fabricated token in an old commit (built at
    run time, never in this file) and a pull request branch on top."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
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

    def scan(self, event):
        self.assertIsNotNone(scan_step(), "gitleaks.yml has no `scan` step")
        env = dict(os.environ, GITHUB_EVENT_NAME=event, BASE_SHA=self.base, HEAD_SHA=self.head(),
                   PATH=f"{Path(GITLEAKS).parent}{os.pathsep}{os.environ['PATH']}")
        return subprocess.run(["bash", "-c", scan_step()["run"]], cwd=self.repo, env=env, capture_output=True,
                              text=True, timeout=60)

    def test_a_pull_request_scans_only_its_own_commits(self):
        result = self.scan("pull_request")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"gitleaks range: {self.base}..{self.head()}", result.stdout)

    def test_a_secret_the_pull_request_adds_fails_and_stays_redacted(self):
        self.commit("feature.env", f"GITHUB_TOKEN={self.token}\n")
        result = self.scan("pull_request")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn(self.token, result.stdout + result.stderr)

    def test_main_and_a_dispatch_scan_the_whole_history(self):
        for event in ("push", "workflow_dispatch"):
            with self.subTest(event=event):
                result = self.scan(event)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("gitleaks range: HEAD", result.stdout)
                self.assertNotIn(self.token, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
