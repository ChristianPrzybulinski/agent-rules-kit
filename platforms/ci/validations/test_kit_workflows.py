"""The kit's own required workflows (KIT-076): ci.yml, gitleaks.yml and codeql.yml run on every pull request to main, on
pushes to main and on demand (CodeQL also weekly), never on pull_request_target, with a read-only default token, per-ref
concurrency and the check names the ruleset requires. Every kit workflow and every template projects copy pins its
actions by commit SHA, sets a timeout and its checkout's persist-credentials, keeps `${{ }}` out of `run:` and is
linted by the pinned actionlint and zizmor; Dependabot watches both folders and the spec-tools action. The gitleaks
scan step runs against a throwaway repository: a pull request scans its own commits, a push to main the whole history.

KIT-077: ci.yml runs the pull request layers as parallel jobs, and the required `ci` job gathers them: it always runs
and passes only when each passed. ci-full.yml runs the whole integration layer and the functional layer on main,
nightly and on demand; performance.yml the latency budgets; release.yml refuses a commit without a green ci-full."""
import contextlib
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

LAYER = "contract"  # KIT-077 layer (platforms/tools/run_tests.py): the kit's own files, read in-process

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
# It also requires `CodeQL`, which GitHub's code scanning posts for codeql.yml's upload and no job names.
CHECKS = {"ci.yml": ["ci", "workflow-lint"], "gitleaks.yml": ["gitleaks"],
          "codeql.yml": ["codeql (python)", "codeql (actions)"]}
# Every context a workflow reports (KIT-077): the required ones above and the layers' own jobs, so a new, renamed or
# removed job is a deliberate change here.
CONTEXTS = {"ci.yml": ["static", "unit", "integration (1)", "integration (2)", "integration (3)", "red", "ci",
                       "workflow-lint"],
            "gitleaks.yml": ["gitleaks"], "codeql.yml": ["codeql (python)", "codeql (actions)"]}
# The one job that carries an `if`: `ci` gathers the pull request layers and the red check (#281: required on every
# pull request), so it must run, and fail, when one did not pass (a skipped required job reports success).
AGGREGATORS = {("ci.yml", "ci"): ["static", "unit", "integration", "red"]}
# Where each test layer runs (platforms/tools/run_tests.py --layer), as (workflow, job).
LAYER_JOBS = {"unit": [("ci.yml", "unit")], "contract": [("ci.yml", "unit")],
              "integration": [("ci-full.yml", "integration"), ("ci.yml", "integration")],
              "functional": [("ci-full.yml", "functional")], "performance": [("performance.yml", "performance")]}
TRIGGERS = {"pull_request": {"branches": ["main"]}, "push": {"branches": ["main"]}, "workflow_dispatch": None}
WEEKLY = re.compile(r"^\d{1,2} \d{1,2} \* \* [0-6]$")
DAILY = re.compile(r"^\d{1,2} \d{1,2} \* \* \*$")
# The one checkout that keeps its credential: `git lfs pull` in the same job authenticates with it.
KEEPS_CREDENTIAL = {("ci-godot.yml", "import-and-test")}
JOB_GRANTS = {"contents": "read", "security-events": "write",  # security-events: CodeQL's SARIF upload only
              "pull-requests": "read"}  # red reads the PR body when it runs (#294)
# The only jobs whose token may write, and the scopes (#279): any other `write`, or a `write-all`, fails.
WRITE_GRANTS = {("codeql.yml", "analyze", "security-events"), ("release.yml", "release", "contents")}
# A tool fetched by a run step is pinned by version and sha-256 (#294): never a script piped into a shell.
PIPED_INSTALL = re.compile(r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:sudo\s+)?(?:ba|z|da)?sh\b")
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


def grants(permissions) -> dict:
    """A `permissions` value as {scope: level}: the scalar `write-all` or `read-all` grants every scope ("*")."""
    if isinstance(permissions, str):
        return {"*": permissions.split("-", 1)[0]}
    return dict(permissions or {})


def token_writes(name, workflow) -> list:
    """(job, scope) for each grant that writes, at the workflow level (job "*") or in a job, outside WRITE_GRANTS."""
    out = [("*", scope) for scope, level in grants(workflow.get("permissions")).items() if "write" in str(level)]
    for job_name, job in (workflow.get("jobs") or {}).items():
        out += [(job_name, scope) for scope, level in grants(job.get("permissions")).items()
                if "write" in str(level) and (name, job_name, scope) not in WRITE_GRANTS]
    return out


@unittest.skipIf(yaml is None, "pyyaml is not installed (CI=1 makes it required)")
class RequiredWorkflows(unittest.TestCase):
    def test_each_runs_on_pull_requests_and_pushes_to_main_and_on_demand(self):
        for name in CHECKS:
            on = triggers(load(name))
            on = dict(on) if isinstance(on, dict) else {on: None}  # a bare `on: workflow_dispatch` is a string
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
        job = load("ci.yml")["jobs"].get("workflow-lint")
        self.assertIsNotNone(job, "ci.yml has no workflow-lint job")
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
                self.assertEqual(token_writes(path.name, workflow), [])

    def test_a_write_all_token_or_an_unlisted_job_write_is_caught(self):
        """#279: `write-all` passed the old check, which looked for the word `write` among the values."""
        self.assertEqual(token_writes("evals.yml", {"permissions": "write-all", "jobs": {}}), [("*", "*")])
        self.assertEqual(token_writes("evals.yml", {"permissions": "read-all",
                                                    "jobs": {"eval": {"permissions": "write-all"}}}), [("eval", "*")])
        self.assertEqual(token_writes("release.yml", {"permissions": {}, "jobs": {"release": {"permissions": {
            "contents": "write", "issues": "write"}}}}), [("release", "issues")])
        self.assertEqual(token_writes("release.yml", {"permissions": {}, "jobs": {"release": {"permissions": {
            "contents": "write"}}}}), [])

    def test_every_workflow_file_is_a_yml_file(self):
        """#279 nit: actionlint, zizmor and these tests read `*.yml`; a `.yaml` workflow would escape all three."""
        for folder in (WORKFLOWS, TEMPLATES):
            with self.subTest(folder=folder.name):
                self.assertEqual(sorted(p.name for p in folder.iterdir() if p.suffix != ".yml"), [])

    def test_no_run_step_pipes_a_download_into_a_shell(self):
        """#294 item 2: Claude Code is fetched by version and sha-256, as just, gitleaks, actionlint and zizmor are."""
        self.assertTrue(PIPED_INSTALL.search("curl -fsSL https://claude.ai/install.sh | bash"))
        for path, workflow in every_workflow():
            for name, job in workflow["jobs"].items():
                for step in job["steps"]:
                    with self.subTest(workflow=path.name, job=name, step=step.get("name", "")[:40]):
                        self.assertIsNone(PIPED_INSTALL.search(step.get("run", "")))
                        if "claude-code-releases" in step.get("run", ""):
                            self.assertRegex(step["env"]["CLAUDE_CODE_VERSION"], r"^\d+\.\d+\.\d+$")
                            self.assertRegex(step["env"]["CLAUDE_CODE_SHA256"], r"^[0-9a-f]{64}$")
                            self.assertIn("sha256sum -c -", step["run"])

    def test_dependabot_updates_the_actions_of_both_folders_and_the_kit_actions(self):
        config = yaml.safe_load((KIT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
        directories = {u.get("directory") for u in config["updates"] if u["package-ecosystem"] == "github-actions"}
        self.assertEqual(directories, {"/", "/platforms/kits/github/workflows",
                                       "/platforms/ci/actions/spec-tools",  # KIT-081: projects pin the action
                                       "/platforms/ci/actions/gitleaks"})  # KIT-084: and this one

    def test_the_check_names_are_stable_and_never_skipped(self):
        for name, expected in CONTEXTS.items():
            jobs = load(name)["jobs"]
            with self.subTest(workflow=name):
                found = [c for job in jobs.values() for c in contexts(job)]
                self.assertEqual(found, expected)
                for required in CHECKS[name]:
                    self.assertEqual(found.count(required), 1, required)
                for key, job in jobs.items():
                    self.assertIsInstance(job.get("timeout-minutes"), int)
                    if (name, key) in AGGREGATORS:  # a skipped required job reports success, so it always runs
                        self.assertEqual(job.get("if"), "always()")
                        self.assertEqual(job.get("needs"), AGGREGATORS[(name, key)])
                    else:
                        self.assertNotIn("if", job)

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


def runs(workflow, job):
    return [step["run"] for step in load(workflow)["jobs"][job]["steps"] if "run" in step]


def install_env(workflow, job):
    """The env of the job's pinned-tool install steps, merged."""
    env = {}
    for step in load(workflow)["jobs"][job]["steps"]:
        if step.get("name", "").startswith("install just"):
            env.update(step.get("env", {}))
    return env


@unittest.skipIf(yaml is None, "pyyaml is not installed (CI=1 makes it required)")
class LayeredGate(unittest.TestCase):
    """KIT-077: the layers, where each runs, the `ci` gathering job, the red job, ci-full and the release guard."""

    def gather(self, results):
        """The exit code of the `ci` job's script for the given needs results."""
        script = load("ci.yml")["jobs"]["ci"]["steps"][0]["run"]
        code = script.split("<<'PY'\n", 1)[1].rsplit("PY", 1)[0]
        needs = json.dumps({job: {"result": result, "outputs": {}} for job, result in results.items()})
        saved = os.environ.get("NEEDS")
        os.environ["NEEDS"] = needs
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(code, "ci.yml:ci", "exec"), {})  # noqa: S102 - the kit's own workflow text
        except SystemExit as stop:
            return stop.code
        finally:
            if saved is None:
                os.environ.pop("NEEDS")
            else:
                os.environ["NEEDS"] = saved
        return None

    def test_ci_passes_only_when_every_layer_passed(self):
        jobs = AGGREGATORS[("ci.yml", "ci")]
        self.assertEqual(self.gather({job: "success" for job in jobs}), 0)
        for job in jobs:
            for result in ("failure", "cancelled", "skipped"):
                with self.subTest(job=job, result=result):
                    self.assertEqual(self.gather({**{j: "success" for j in jobs}, job: result}), 1)
        self.assertEqual(self.gather({}), 1)

    def test_every_layer_runs_where_the_standard_puts_it(self):
        found = {}
        for path in sorted(WORKFLOWS.glob("*.yml")):
            for key in load(path.name)["jobs"]:
                for run in runs(path.name, key):
                    match = re.search(r"run_tests\.py --layer (\S+)", run)
                    for layer in match.group(1).split(",") if match else ():
                        found.setdefault(layer, []).append((path.name, key))
        self.assertEqual(found, LAYER_JOBS)

    def test_a_pull_request_runs_the_integration_tests_its_change_reaches_in_shards(self):
        for name, changed in (("ci.yml", True), ("ci-full.yml", False)):
            job = load(name)["jobs"]["integration"]
            shards = job["strategy"]["matrix"]["shard"]
            step = next(s for s in job["steps"] if "run_tests.py" in s.get("run", ""))
            with self.subTest(workflow=name):
                self.assertEqual(shards, list(range(1, len(shards) + 1)))
                self.assertEqual(step["env"]["SHARD"], "${{ matrix.shard }}/%d" % len(shards))
                self.assertIs(job["strategy"]["fail-fast"], False)
                self.assertEqual("--changed-from HEAD^1" in step["run"], changed)
        checkout = load("ci.yml")["jobs"]["integration"]["steps"][0]
        self.assertEqual(checkout["with"]["fetch-depth"], 2)  # HEAD^1: the merge commit's base, or the last push

    def test_jobs_that_run_the_just_and_gitleaks_tests_install_the_pinned_tools(self):
        gitleaks = next(s for s in steps(load("gitleaks.yml")) if s.get("name", "").startswith("install gitleaks"))
        java = yaml.safe_load((TEMPLATES / "ci-java.yml").read_text(encoding="utf-8"))
        just = next(s for s in steps(java) if s.get("name", "").startswith("Install just"))
        pins = {**{k: v for k, v in gitleaks["env"].items()}, **{k: v for k, v in just["env"].items()}}
        both = ("JUST", "GITLEAKS")
        for workflow, job, tools in (("ci.yml", "integration", both), ("ci.yml", "red", both),
                                     ("ci-full.yml", "integration", both), ("ci-full.yml", "functional", ("JUST",))):
            env = install_env(workflow, job)
            for tool in tools:
                with self.subTest(workflow=workflow, job=job, tool=tool):
                    for key in (f"{tool}_VERSION", f"{tool}_SHA256"):
                        self.assertEqual(env.get(key), pins[key])

    def test_jobs_that_run_the_gdscript_tool_tests_install_the_pinned_gdtoolkit(self):
        """KIT-082: under CI=1 the test_gd_* tests fail instead of skipping without gdtoolkit, so every job that runs
        the unit or integration layer, and red on a pull request's changed tests, installs the one pin the Godot kit
        gives projects."""
        requirements = "platforms/kits/godot/requirements-gdtoolkit.txt"
        self.assertRegex((KIT / requirements).read_text(encoding="utf-8"), r"(?m)^gdtoolkit==\d+\.\d+\.\d+$")
        jobs = sorted({*LAYER_JOBS["unit"], *LAYER_JOBS["integration"], ("ci.yml", "red")})
        self.assertEqual(len(jobs), 4)
        for workflow, job in jobs:
            with self.subTest(workflow=workflow, job=job):
                runs = [step.get("run", "") for step in load(workflow)["jobs"][job]["steps"]]
                self.assertIn(f"pip install -r {requirements}", runs)

    def test_the_godot_template_imports_once(self):
        """#283 item 7: `just boot` and `just test` both depend on `import`; two invocations imported twice, so the
        test step skips the dependency the boot step just ran."""
        job = load("ci-godot.yml", TEMPLATES)["jobs"]["import-and-test"]
        calls = [line.strip() for step in job["steps"] for line in step.get("run", "").splitlines()
                 if re.match(r"\s*just ", line)]
        self.assertEqual(len(calls), 2, calls)
        self.assertEqual(calls[0], "just boot")
        self.assertRegex(calls[1], r"^just --no-deps test(?=\s|$)")  # the import `just boot` ran is not run again
        self.assertRegex(calls[1], r"\|\s*tee\s+test-run\.log(?=\s|$)")  # the log the upload step keeps

    def test_a_template_job_that_runs_just_links_the_kit_first(self):
        """KIT-081 stage 1b: a project's justfile imports the kit's module from ~/.ai-kit, so each template job that
        runs a just recipe calls the spec-tools action (checks: none), which links the pinned kit there, before its
        first just step."""
        action = "ChristianPrzybulinski/agent-rules-kit/platforms/ci/actions/spec-tools@"
        found = 0
        for path in sorted(TEMPLATES.glob("*.yml")):
            for job_name, job in (load(path.name, TEMPLATES).get("jobs") or {}).items():
                runs = [i for i, s in enumerate(job.get("steps", [])) if re.search(r"(?m)^\s*just ", s.get("run", ""))]
                if not runs:
                    continue
                found += 1
                with self.subTest(workflow=path.name, job=job_name):
                    links = [i for i, s in enumerate(job["steps"]) if s.get("uses", "").startswith(action)]
                    self.assertTrue(links and links[0] < runs[0], "no spec-tools step before the first just step")
                    self.assertEqual(job["steps"][links[0]].get("with", {}).get("checks"), "none")
        self.assertEqual(found, 4)  # ci-godot import-and-test and lint, ci-java build and dependency-check

    def test_the_templates_pin_one_kit_release_that_has_the_spec_tools_action(self):
        """Every kit action pin in the templates (spec-tools, and gitleaks since KIT-084) names the same commit, as
        `<40-hex SHA>  # vX.Y.Z`, of a release no older than 14.0.0, the first that ships the spec-tools action: a
        project whose workflow pins 13.1.0 (5a4924e) fails at that `uses:` line, since the commit has no
        platforms/ci/actions/spec-tools/action.yml."""
        kit_action = re.compile(r"/platforms/ci/actions/[\w-]+@")
        pins = {kit_action.split(line, 1)[1].strip()
                for path in sorted(TEMPLATES.glob("*.yml"))
                for line in path.read_text(encoding="utf-8").splitlines() if kit_action.search(line)}
        self.assertEqual(len(pins), 1, pins)
        match = re.fullmatch(r"[0-9a-f]{40}  # v(\d+)\.(\d+)\.(\d+)", pins.pop())
        self.assertIsNotNone(match)
        self.assertGreaterEqual(tuple(int(part) for part in match.groups()), (14, 0, 0))

    def test_spec_lint_runs_the_kit_spec_tools_through_the_pinned_action(self):
        """KIT-081 stage 1: no template runs a copy of the spec tools in the project. spec-lint.yml and pr-contract.yml
        call the spec-tools action pinned by SHA; the action runs check_docs_structure.py whenever `spec` is asked
        (#283 item 6: it passes as "off" unless enabled, so no step needs a hand edit), and spec-lint.yml's paths
        include the workflow itself, so the bot's pin bump runs the check it updates."""
        action = "ChristianPrzybulinski/agent-rules-kit/platforms/ci/actions/spec-tools@"
        for name in ("spec-lint.yml", "pr-contract.yml"):
            text = (TEMPLATES / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertNotIn(".github/spec-lint", text)
                self.assertEqual([s["uses"].split("@")[0] + "@" for s in steps(load(name, TEMPLATES))
                                  if action in s.get("uses", "")], [action])
        validate = load("spec-lint.yml", TEMPLATES)
        self.assertEqual([s.get("with", {}).get("checks") for s in steps(validate) if action in s.get("uses", "")],
                         ["spec"])
        for event in ("push", "pull_request"):
            self.assertIn(".github/workflows/spec-lint.yml", triggers(validate)[event]["paths"])
        contract = load("pr-contract.yml", TEMPLATES)
        self.assertNotIn("script", triggers(contract)["workflow_call"]["inputs"])
        self.assertTrue(all("$AI_KIT_DIR/platforms/ci/validations/pr_gates.py" in s["run"]
                            for s in steps(contract) if "pr_gates.py" in s.get("run", "")))
        spec_steps = yaml.safe_load((KIT / "platforms/ci/actions/spec-tools/action.yml").read_text(encoding="utf-8"))
        structure = [s for s in spec_steps["runs"]["steps"] if "check_docs_structure.py" in s.get("run", "")]
        self.assertEqual([s.get("if") for s in structure], ["steps.checks.outputs.spec == 'true'"])

    def test_red_runs_on_the_merge_commit_and_ci_needs_it(self):
        job = load("ci.yml")["jobs"]["red"]
        self.assertEqual(job["steps"][0]["with"]["fetch-depth"], 0)
        self.assertIn("python3 -B platforms/tools/ci_red.py", runs("ci.yml", "red"))
        self.assertIn("red", load("ci.yml")["jobs"]["ci"]["needs"])

    def test_ci_fails_when_red_fails(self):
        jobs = AGGREGATORS[("ci.yml", "ci")]
        self.assertEqual(self.gather({**{job: "success" for job in jobs}, "red": "failure"}), 1)

    def test_ci_full_runs_on_main_nightly_and_on_demand(self):
        on = triggers(load("ci-full.yml"))
        self.assertEqual(sorted(on), ["push", "schedule", "workflow_dispatch"])
        self.assertEqual(on["push"], {"branches": ["main"]})
        self.assertEqual(len(on["schedule"]), 1)
        self.assertRegex(on["schedule"][0]["cron"], DAILY)

    def test_performance_runs_nightly_and_on_demand_one_test_at_a_time(self):
        on = triggers(load("performance.yml"))
        self.assertEqual(sorted(on), ["schedule", "workflow_dispatch"])
        self.assertRegex(on["schedule"][0]["cron"], DAILY)
        self.assertTrue(any("--jobs 1" in run for run in runs("performance.yml", "performance")))

    def test_release_refuses_a_commit_without_a_green_ci_full(self):
        job = load("release.yml")["jobs"]["release"]
        names = [step.get("name", "") for step in job["steps"]]
        guard = next(i for i, step in enumerate(job["steps"]) if "release_guard.py" in step.get("run", ""))
        self.assertLess(guard, names.index("gh release create"))
        self.assertEqual(job["permissions"], {"contents": "write", "actions": "read"})
        self.assertIn('--sha "$SHA" --tag "$TAG"', job["steps"][guard]["run"])
        self.assertEqual(job["steps"][guard]["env"]["SHA"], "${{ github.sha }}")


@unittest.skipIf(yaml is None, "pyyaml is not installed (CI=1 makes it required)")
class StableBranch(unittest.TestCase):
    """KIT-081: every install follows the `stable` branch, which release.yml moves to the released commit as its last
    step, after the release exists, through the API and fast-forward only: a non-fast-forward fails the step."""

    def test_the_release_moves_stable_last_and_never_forces_it(self):
        job = load("release.yml")["jobs"]["release"]
        names = [step.get("name", "") for step in job["steps"]]
        move = [i for i, step in enumerate(job["steps"]) if "refs/heads/stable" in step.get("run", "")]
        self.assertEqual(move, [len(job["steps"]) - 1], "release.yml does not move stable in its last step")
        self.assertGreater(move[0], names.index("gh release create"))
        step = job["steps"][move[0]]
        self.assertEqual(step["run"].strip(),
                         'gh api -X PATCH "repos/$REPO/git/refs/heads/stable" -f sha="$SHA" -F force=false')
        self.assertEqual(step["env"], {"GH_TOKEN": "${{ github.token }}", "REPO": "${{ github.repository }}",
                                       "SHA": "${{ github.sha }}"})
        self.assertIs(job["steps"][0]["with"]["persist-credentials"], False)  # the API call needs no git credential
        self.assertEqual(job["permissions"], {"contents": "write", "actions": "read"})


def scan_step():
    return next((s for s in steps(load("gitleaks.yml")) if s.get("name", "").startswith("scan")), None)


@unittest.skipIf(yaml is None or (GITLEAKS is None and not os.environ.get("CI")),
                 "pyyaml or gitleaks is not available (CI=1 makes both required)")
class GitleaksRange(unittest.TestCase):
    """The scan step's script, run as the workflow runs it, on main with a fabricated token in an old commit (built at
    run time, never in this file) and a pull request branch on top."""

    LAYER = "integration"  # starts processes (scripts, git, temp repos)
    COVERS = (".github/workflows/gitleaks.yml",)

    def setUp(self):
        if GITLEAKS is None:  # KIT-077: the CI jobs that run this layer install the pinned gitleaks
            self.fail("gitleaks is not on PATH")
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
