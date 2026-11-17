"""The spec-tools composite action (KIT-081 stage 1): a project's CI runs the kit's spec validators and schemas from
the kit commit it pins, with no copy in the project. The file parses as a composite action, pins its actions by
commit SHA, keeps `${{ }}` out of `run:`, and runs every tool from its own checkout ($GITHUB_ACTION_PATH). Its steps'
own shell runs here against a throwaway project, with GITHUB_ACTION_PATH at the kit's action folder."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
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
ACTION_DIR = KIT / "platforms" / "ci" / "actions" / "spec-tools"
ACTION = ACTION_DIR / "action.yml"
PINNED = re.compile(r"^\s*-?\s*uses:\s*[\w.-]+/[\w./-]+@[0-9a-f]{40}\s+#\s*v\d+(\.\d+)*\s*$")
TOOL = re.compile(r'"\$GITHUB_ACTION_PATH/([^"]+)"')

SPEC_MD = '---\nproject: "x"\nversion: "0.1.0"\nupdated: "2026-11-15"\n---\n\n# x\n'
FEAT = """\
---
id: FEAT-001
title: "Fixture"
status: planned
requirements: []
created: "2026-11-15"
---

# FEAT-001

## Tasks

| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Model | Wave | Item |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | Add the tool | `README.md` | `docker exec x ls` | CA-1 | — | todo | Low | small | 0 | — |
"""


def action():
    return yaml.safe_load(ACTION.read_text(encoding="utf-8"))


def step(name):
    found = [s for s in action()["runs"]["steps"] if s.get("name") == name]
    assert len(found) == 1, f"action.yml has {len(found)} steps named {name!r}"
    return found[0]


@unittest.skipIf(yaml is None, "pyyaml is not installed (CI=1 makes it required)")
class SpecToolsActionFile(unittest.TestCase):
    def test_a_composite_action_whose_actions_are_pinned_by_sha(self):
        data = action()
        self.assertEqual(data["runs"]["using"], "composite")
        lines = [line for line in ACTION.read_text(encoding="utf-8").splitlines() if re.match(r"^\s*-?\s*uses:", line)]
        self.assertTrue(lines)
        for line in lines:
            self.assertRegex(line, PINNED)
        for item in data["runs"]["steps"]:
            with self.subTest(step=item.get("name", item.get("uses"))):
                self.assertNotIn("${{", item.get("run", ""))  # pass it through env: instead
                if "run" in item:
                    self.assertEqual(item.get("shell"), "bash")  # a composite run step must name its shell

    def test_every_tool_runs_from_the_actions_own_checkout(self):
        runs = "\n".join(item.get("run", "") for item in action()["runs"]["steps"])
        tools = TOOL.findall(runs)
        self.assertEqual(sorted(set(t for t in tools if t.endswith(".py"))),
                         ["../../../tools/profile.py", "../../validations/check_docs_structure.py",
                          "../../validations/check_spec.py", "../../validations/row_checks.py",
                          "../../validations/spec_trace.py"])
        for rel in tools:
            with self.subTest(path=rel):
                self.assertTrue((ACTION_DIR / rel).exists(), rel)
        self.assertIn("../../schemas", tools)
        for word in (".github/spec-lint", "git clone", "git fetch", "actions/checkout", "curl", "wget"):
            self.assertNotIn(word, ACTION.read_text(encoding="utf-8"))  # nothing fetches another ref

    def test_its_readme_documents_every_input(self):
        readme = (ACTION_DIR / "README.md").read_text(encoding="utf-8")
        for name in action()["inputs"]:
            self.assertIn(f"| `{name}` |", readme)


@unittest.skipIf(yaml is None, "pyyaml is not installed (CI=1 makes it required)")
class SpecToolsActionRuns(unittest.TestCase):
    LAYER = "integration"  # the steps' shell, the kit's validators and git in a throwaway project
    COVERS = ("platforms/ci/actions/spec-tools/**", "platforms/ci/validations/check_spec.py",
              "platforms/ci/validations/check_docs_structure.py", "platforms/ci/validations/spec_trace.py",
              "platforms/ci/validations/row_checks.py", "platforms/ci/validations/pr_gates.py",
              "platforms/ci/schemas/**", "platforms/tools/profile.py")

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.repo = self.tmp / "repo"
        spec = self.repo / "docs" / "spec"
        (spec / "features").mkdir(parents=True)
        (spec / "spec.md").write_text(SPEC_MD, encoding="utf-8")
        (spec / "features" / "FEAT-001.md").write_text(textwrap.dedent(FEAT), encoding="utf-8")
        (self.repo / "README.md").write_text("# x\n", encoding="utf-8")  # the row's Files entry exists (rule b)
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                               "-c", "commit.gpgsign=false", *args], check=True, capture_output=True,
                              text=True).stdout.strip()

    def run_step(self, name, **env):
        files = {key: self.tmp / key.lower() for key in ("GITHUB_ENV", "GITHUB_OUTPUT")}
        for path in files.values():
            path.write_text("", encoding="utf-8")
        full = {k: v for k, v in os.environ.items() if k != "CI"}
        full.update({k: str(v) for k, v in files.items()}, GITHUB_ACTION_PATH=str(ACTION_DIR),
                    RUNNER_TEMP=str(self.tmp), PATH=f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}",
                    AI_KIT_PYTHON=sys.executable)  # the install step exports it for the later steps (#372)
        full.update({k: str(v) for k, v in env.items()})  # a test may also set GITHUB_ACTION_PATH
        result = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", step(name)["run"]],
                                cwd=self.repo, env=full, capture_output=True, text=True, check=False)
        result.files = {key: path.read_text(encoding="utf-8") for key, path in files.items()}
        return result

    INSTALL = "Install the validators' modules (pyyaml and jsonschema, for the full check)"
    SSL_ERROR = ("ImportError: /lib/x86_64-linux-gnu/libcrypto.so.3: version `OPENSSL_3.3.0' not found (required by"
                 " /__t/Python/3.12.16/x64/lib/python3.12/lib-dynload/_ssl.cpython-312-x86_64-linux-gnu.so)")

    def fake_tools(self, apt_get=True, apt_fails=False):
        """A bin folder with a python3 whose ssl import fails when NO_SSL is set (the setup-python build in
        barichello/godot-ci:4.7.2, #372), a system python3 with yaml and jsonschema, an id whose -u prints FAKE_UID and,
        unless apt_get is false, an apt-get; each logs its arguments to calls.log."""
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        log = self.tmp / "calls.log"
        error = self.tmp / "ssl-error.txt"
        error.write_text(f"Traceback (most recent call last):\n{self.SSL_ERROR}\n", encoding="utf-8")
        tools = {
            "python3": f"""case "$*" in
  "-c import ssl") if [ -n "${{NO_SSL:-}}" ]; then cat "{error}" >&2; exit 1; fi ;;
  "-c import yaml, jsonschema") ;;
  *) echo "python3 $*" >> "{log}" ;;
esac""",
            "system-python3": f'echo "system-python3 $*" >> "{log}"',
            "id": 'if [ "$1" = -u ]; then echo "$FAKE_UID"; else exec /usr/bin/id "$@"; fi',
        }
        if apt_get:
            tools["apt-get"] = f'echo "apt-get $*" >> "{log}"' + ("\nexit 100" if apt_fails else "")
        for name, body in tools.items():
            (bin_dir / name).write_text(f"#!/bin/bash\n{body}\n", encoding="utf-8")
            (bin_dir / name).chmod(0o755)
        log.write_text("", encoding="utf-8")
        return bin_dir, log

    def install(self, bin_dir, **env):
        path = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"
        if not (bin_dir / "apt-get").exists():  # a Debian runner's /usr/bin holds apt-get: PATH is the fakes alone
            for tool in ("bash", "cat", "tail"):
                (bin_dir / tool).symlink_to(shutil.which(tool))
            path = str(bin_dir)
        return self.run_step(self.INSTALL, **{"PATH": path, "SYSTEM_PYTHON": bin_dir / "system-python3", "FAKE_UID": "0",
                                              **env})

    def test_with_ssl_the_install_step_uses_pip_and_exports_that_python(self):
        bin_dir, log = self.fake_tools()
        result = self.install(bin_dir)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(log.read_text(encoding="utf-8"),
                         "python3 -m pip install --disable-pip-version-check --quiet pyyaml jsonschema\n")
        self.assertEqual(result.files["GITHUB_ENV"], f"AI_KIT_PYTHON={bin_dir / 'python3'}\n")
        self.assertNotIn("::", result.stdout)

    def test_without_ssl_the_install_step_takes_the_distributions_modules(self):
        """#372: in barichello/godot-ci:4.7.2 the setup-python build cannot import ssl, so pip cannot reach PyPI; as
        root with apt-get the step installs python3-yaml and python3-jsonschema and the later steps run the system
        python3, with a warning that names the cause."""
        bin_dir, log = self.fake_tools()
        result = self.install(bin_dir, NO_SSL="1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(log.read_text(encoding="utf-8"),
                         "apt-get update -qq\napt-get install -y -qq --no-install-recommends python3 python3-yaml"
                         " python3-jsonschema\nsystem-python3 -c import yaml, jsonschema\n")
        self.assertEqual(result.files["GITHUB_ENV"], f"AI_KIT_PYTHON={bin_dir / 'system-python3'}\n")
        self.assertEqual(result.stdout, f"::warning::spec-tools: {bin_dir / 'python3'} cannot import ssl"
                                        f" ({self.SSL_ERROR}); installing python3, python3-yaml and python3-jsonschema"
                                        f" with apt-get, and the spec tools run on {bin_dir / 'system-python3'}\n")
        later = self.run_step("Export AI_KIT_DIR, the kit at this action's commit")  # the next steps still run
        self.assertEqual(later.returncode, 0, later.stderr)

    def test_without_ssl_or_a_root_apt_get_the_install_step_fails_naming_the_cause(self):
        """#372: the spec checks are never skipped silently: with no way to install the modules the step fails."""
        for case, kwargs, env in (("no apt-get", {"apt_get": False}, {}),
                                  ("not root", {}, {"FAKE_UID": "1001"})):
            with self.subTest(case=case):
                if (self.tmp / "bin").exists():
                    shutil.rmtree(self.tmp / "bin")
                bin_dir, log = self.fake_tools(**kwargs)
                result = self.install(bin_dir, NO_SSL="1", **env)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(result.stdout, f"::error::spec-tools: {bin_dir / 'python3'} cannot import ssl"
                                                f" ({self.SSL_ERROR}), so pip cannot install pyyaml and jsonschema from"
                                                " PyPI, and no apt-get runs as root to install python3-yaml and"
                                                " python3-jsonschema instead; run the action in a job without a"
                                                " container, or in an image with apt-get as root or a Python whose ssl"
                                                " module loads\n")
                self.assertEqual(log.read_text(encoding="utf-8"), "")
                self.assertEqual(result.files["GITHUB_ENV"], "")
        shutil.rmtree(self.tmp / "bin")
        bin_dir, log = self.fake_tools(apt_fails=True)
        failed = self.install(bin_dir, NO_SSL="1")
        self.assertEqual(failed.returncode, 1, failed.stdout + failed.stderr)
        self.assertIn(f"::error::spec-tools: {bin_dir / 'python3'} cannot import ssl ({self.SSL_ERROR}), and apt-get"
                      " could not install python3, python3-yaml and python3-jsonschema\n", failed.stdout)
        self.assertEqual(failed.files["GITHUB_ENV"], "")

    def test_every_later_step_runs_the_exported_python(self):
        """#372: after the install step no step calls a bare python3, which in a container job may be the build that
        cannot import ssl."""
        names = [s.get("name") for s in action()["runs"]["steps"]]
        for item in action()["runs"]["steps"][names.index(self.INSTALL) + 1:]:
            with self.subTest(step=item.get("name")):
                self.assertIsNone(re.search(r"(?<![\w/-])python3\b", item.get("run", "")))

    def test_the_checks_input_selects_the_steps_and_refuses_an_unknown_name(self):
        name = "Resolve the requested checks"
        self.assertEqual(self.run_step(name, CHECKS="spec, rows").files["GITHUB_OUTPUT"], "spec=true\nrows=true\n")
        self.assertEqual(self.run_step(name, CHECKS="spec,trace").files["GITHUB_OUTPUT"], "spec=true\ntrace=true\n")
        self.assertEqual(self.run_step(name, CHECKS="none").files["GITHUB_OUTPUT"], "")
        refused = self.run_step(name, CHECKS="spec,*")
        self.assertEqual(refused.returncode, 2, refused.stdout + refused.stderr)
        self.assertIn("unknown check '*'", refused.stdout)
        # KIT-087 P2a: the input is empty by default, and the profile's ci.spec_tools_checks, default spec, decides
        self.assertEqual(action()["inputs"]["checks"]["default"], "")
        self.assertEqual(self.run_step(name, CHECKS="", AI_KIT_PROFILE_JSON='{"ci": {"spec_tools_checks": ["spec"]}}')
                         .files["GITHUB_OUTPUT"], "spec=true\n")
        for check in ("spec", "trace", "rows"):
            self.assertTrue(any(f"steps.checks.outputs.{check} == 'true'" in str(s.get("if", ""))
                                for s in action()["runs"]["steps"]), check)

    def test_without_the_checks_input_the_profile_selects_them(self):
        """KIT-087 P2a: an empty checks input reads ci.spec_tools_checks from the resolved profile, which the step
        before it exported; the profile default ["spec"] is the old input default."""
        self.assertEqual(action()["inputs"]["checks"]["default"], "")
        names = [s.get("name") for s in action()["runs"]["steps"]]
        self.assertLess(names.index("Resolve the project profile and export AI_KIT_PROFILE_JSON"),
                        names.index("Resolve the requested checks"))
        name = "Resolve the requested checks"
        view = '{"ci": {"spec_tools_checks": ["spec", "trace", "rows"], "trigger": "auto"}}'
        self.assertEqual(self.run_step(name, CHECKS="", AI_KIT_PROFILE_JSON=view).files["GITHUB_OUTPUT"],
                         "spec=true\ntrace=true\nrows=true\n")
        self.assertEqual(self.run_step(name, CHECKS="trace", AI_KIT_PROFILE_JSON=view).files["GITHUB_OUTPUT"],
                         "trace=true\n", "the input wins when given")
        self.assertEqual(self.run_step(name, CHECKS="", AI_KIT_PROFILE_JSON='{"ci": {"spec_tools_checks": []}}')
                         .files["GITHUB_OUTPUT"], "")
        broken = self.run_step(name, CHECKS="", AI_KIT_PROFILE_JSON="")
        self.assertNotEqual(broken.returncode, 0)
        self.assertIn("spec-tools: no checks input and no resolved profile", broken.stdout + broken.stderr)
        (self.repo / ".ai-kit.yaml").write_text("ci:\n  spec_tools_checks: [spec, rows]\n", encoding="utf-8")
        exported = self.run_step("Resolve the project profile and export AI_KIT_PROFILE_JSON", PROFILE=".ai-kit.yaml")
        self.assertEqual(exported.returncode, 0, exported.stderr)
        lines = exported.files["GITHUB_ENV"].splitlines()
        result = self.run_step(name, CHECKS="", AI_KIT_PROFILE_JSON="\n".join(lines[1:-1]))
        self.assertEqual(result.files["GITHUB_OUTPUT"], "spec=true\nrows=true\n")

    def test_it_exports_the_kit_at_its_own_commit_as_ai_kit_dir(self):
        result = self.run_step("Export AI_KIT_DIR, the kit at this action's commit")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.files["GITHUB_ENV"], f"AI_KIT_DIR={KIT}\n")

    def test_it_links_home_ai_kit_to_its_own_commit_unless_a_kit_is_there(self):
        """KIT-081 stage 1b: a project's justfile imports ~/.ai-kit/platforms/kits/just/<profile>.just, and just reads no
        variable in an import path, so the action links ~/.ai-kit to its own checkout; a kit already there stays, and
        (KIT-083) the step fails unless that kit is at the action's commit."""
        name = "Link ~/.ai-kit to the kit at this action's commit (the justfile imports)"
        home = self.tmp / "home"
        home.mkdir()
        linked = self.run_step(name, HOME=home)
        self.assertEqual(linked.returncode, 0, linked.stderr)
        self.assertTrue((home / ".ai-kit").is_symlink())
        self.assertEqual((home / ".ai-kit").resolve(), KIT.resolve())
        self.assertTrue((home / ".ai-kit" / "platforms" / "kits" / "just" / "godot.just").is_file())
        again = self.run_step(name, HOME=home)
        self.assertEqual((again.returncode, again.stdout), (0, ""))
        other = self.tmp / "other-home"
        (other / ".ai-kit").mkdir(parents=True)  # a folder that is no git checkout: its commit is unknown
        kept = self.run_step(name, HOME=other)
        self.assertEqual(kept.returncode, 1, kept.stdout + kept.stderr)
        self.assertFalse((other / ".ai-kit").is_symlink())
        self.assertEqual(kept.stdout, f"::error::spec-tools: {other}/.ai-kit is at no git commit, this action at"
                                      f" {self.head(KIT)}, so a justfile importing ~/.ai-kit would run another kit;"
                                      f" check out {self.head(KIT)} there, or remove {other}/.ai-kit so the action"
                                      " links its own commit\n")

    def head(self, path):
        return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=True, capture_output=True,
                              text=True).stdout.strip()

    def test_a_kit_already_at_home_passes_only_at_the_actions_commit(self):
        """KIT-083: a runner that already holds ~/.ai-kit serves the justfile imports from it, so the step compares its
        HEAD with the action's commit: the action checkout's HEAD, or on a runner, which downloads an action as an
        archive without .git, the SHA the caller pins (github.action_ref)."""
        name = "Link ~/.ai-kit to the kit at this action's commit (the justfile imports)"
        kit = self.tmp / "kit"  # a kit checkout of its own, so the test controls both commits
        action = kit / "platforms" / "ci" / "actions" / "spec-tools"
        action.mkdir(parents=True)
        (action / "action.yml").write_text("name: x\n", encoding="utf-8")
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]
        subprocess.run([*git, "init", "-q", str(kit)], check=True)
        subprocess.run([*git, "-C", str(kit), "add", "-A"], check=True)
        subprocess.run([*git, "-C", str(kit), "commit", "-q", "-m", "kit"], check=True)
        home = self.tmp / "runner-home"
        home.mkdir()
        subprocess.run(["git", "clone", "-q", str(kit), str(home / ".ai-kit")], check=True)
        sha = self.head(kit)
        same = self.run_step(name, HOME=home, GITHUB_ACTION_PATH=action)
        self.assertEqual(same.returncode, 0, same.stdout + same.stderr)
        self.assertEqual(same.stdout, f"::notice::spec-tools: {home}/.ai-kit is another checkout at this action's"
                                      f" commit {sha}; a justfile importing ~/.ai-kit runs the same kit\n")
        subprocess.run([*git, "-C", str(home / ".ai-kit"), "commit", "-q", "--allow-empty", "-m", "newer"], check=True)
        newer = self.head(home / ".ai-kit")
        moved = self.run_step(name, HOME=home, GITHUB_ACTION_PATH=action)
        self.assertEqual(moved.returncode, 1, moved.stdout + moved.stderr)
        self.assertIn(f"::error::spec-tools: {home}/.ai-kit is at {newer}, this action at {sha}, so a justfile",
                      moved.stdout)
        archive = self.tmp / "_actions" / "owner" / "kit" / "ref"  # the runner's layout: a copy with no .git
        shutil.copytree(kit, archive, ignore=shutil.ignore_patterns(".git"))
        action = archive / "platforms" / "ci" / "actions" / "spec-tools"
        for ref, code in ((newer, 0), (sha, 1)):
            with self.subTest(action_ref=ref):
                result = self.run_step(name, HOME=home, GITHUB_ACTION_PATH=action, ACTION_REF=ref)
                self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        unknown = self.run_step(name, HOME=home, GITHUB_ACTION_PATH=action, ACTION_REF="v14.0.0")
        self.assertEqual(unknown.returncode, 1, unknown.stdout + unknown.stderr)
        self.assertEqual(unknown.stdout, f"::error::spec-tools: {home}/.ai-kit already exists and this action's commit"
                                         " is unknown (pin the action by its 40-character commit SHA), so a justfile"
                                         " importing ~/.ai-kit may run another kit\n")
        self.assertTrue((home / ".ai-kit").is_dir() and not (home / ".ai-kit").is_symlink())

    def test_the_baseline_step_says_why_it_compares_nothing(self):
        """KIT-083: the baseline step printed nothing when it had no base to compare with; it now says why."""
        name = "Baseline only shrinks"
        cases = (("", "::notice::spec-tools: no base commit (the base input is empty); the baseline is not compared"),
                 ("0" * 40, f"::warning::spec-tools: the base commit {'0' * 40} is not in the checkout (fetch-depth: 0"
                            " fetches it); the baseline is not compared"),
                 (self.git("rev-parse", "HEAD"), "::notice::spec-tools: the base commit has no docs/spec/baseline.json;"
                                                 " the baseline is not compared"))
        for base, line in cases:
            with self.subTest(base=base):
                result = self.run_step(name, BASE_SHA=base)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(result.stdout, line + "\n")

    def test_the_spec_steps_run_the_kit_validators_on_the_project(self):
        try:
            import jsonschema  # noqa: F401  (the step runs with CI=1, which needs both libraries)
        except ImportError:
            if os.environ.get("CI"):
                raise
            self.skipTest("jsonschema missing")
        validate = "Validate frontmatter and FEAT/REQ references"
        result = self.run_step(validate)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("spec: OK", result.stdout)
        structure = self.run_step("Every authored folder says what belongs in it (sdd.doc_structure)")
        self.assertEqual(structure.returncode, 0, structure.stdout + structure.stderr)
        self.assertIn("doc-structure: off", structure.stdout)
        (self.repo / "docs/spec/features/FEAT-001.md").write_text("---\nid: FEAT-001\n---\n", encoding="utf-8")
        broken = self.run_step(validate)
        self.assertEqual(broken.returncode, 1, broken.stdout + broken.stderr)
        self.assertIn("FAIL", broken.stderr)

    def test_trace_and_rows_run_from_the_kit(self):
        trace = self.run_step("Journeys, FEAT and REQ symmetry and the traceability matrix (spec_trace.py check)")
        self.assertEqual(trace.returncode, 0, trace.stdout + trace.stderr)
        rows = "Open task rows (row_checks.py)"
        finding = "FEAT-001 T1: Proof of completion clause 1 'docker exec x ls' (forbidden construct) [e]"
        everything = self.run_step(rows, EVENT="push")
        self.assertEqual(everything.returncode, 1, everything.stdout + everything.stderr)
        self.assertIn(finding, everything.stdout)
        base = self.git("rev-parse", "HEAD")
        self.repo.joinpath("notes.txt").write_text("x\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "head")
        unchanged = self.run_step(rows, EVENT="pull_request", BASE_SHA=base, HEAD_SHA=self.git("rev-parse", "HEAD"))
        self.assertEqual(unchanged.returncode, 0, unchanged.stdout + unchanged.stderr)  # --changed: no FEAT changed
        self.assertNotIn(finding, unchanged.stdout)

    def test_it_exports_the_resolved_profile_as_json(self):
        """KIT-087: the profile input names the file; the step exports the resolved view, and a refused profile fails
        it."""
        import json
        name = "Resolve the project profile and export AI_KIT_PROFILE_JSON"
        self.assertEqual(action()["inputs"]["profile"]["default"], ".ai-kit.yaml")
        missing = self.run_step(name, PROFILE=".ai-kit.yaml")
        self.assertEqual(missing.returncode, 0, missing.stderr)
        self.assertIn("profile: warning: no .ai-kit.yaml", missing.stderr)
        (self.repo / "ci.yaml").write_text("ci:\n  trigger: auto\nx-team: {any: thing}\n", encoding="utf-8")
        result = self.run_step(name, PROFILE="ci.yaml")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.files["GITHUB_ENV"].splitlines()
        self.assertRegex(lines[0], r"^AI_KIT_PROFILE_JSON<<ai_kit_profile_[0-9a-f]{32}$")
        self.assertEqual(lines[-1], lines[0].split("<<", 1)[1])
        resolved = json.loads("\n".join(lines[1:-1]))
        self.assertEqual(resolved["ci"]["trigger"], "auto")
        self.assertNotIn("x-team", resolved)
        # KIT-087 P4: an sdd: block left in spec.md is no home, so no conflict; a refused profile still fails the step
        (self.repo / "ci.yaml").write_text("sdd:\n  tracker: none\n", encoding="utf-8")
        (self.repo / "docs/spec/spec.md").write_text(SPEC_MD.replace("---\n\n", "sdd:\n  tracker: github\n---\n\n"),
                                                     encoding="utf-8")
        legacy = self.run_step(name, PROFILE="ci.yaml")
        self.assertEqual(legacy.returncode, 0, legacy.stderr)
        self.assertEqual(json.loads("\n".join(legacy.files["GITHUB_ENV"].splitlines()[1:-1]))["sdd"]["tracker"], "none")
        (self.repo / "ci.yaml").write_text("sdd:\n  tracker: jira\n", encoding="utf-8")
        refused = self.run_step(name, PROFILE="ci.yaml")
        self.assertEqual(refused.returncode, 1, refused.stderr)
        self.assertIn("sdd.tracker 'jira' is not one of", refused.stderr)
        self.assertEqual(refused.files["GITHUB_ENV"], "")


if __name__ == "__main__":
    unittest.main()
