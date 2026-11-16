"""The per-profile just modules (KIT-074): recipe names, the commands each recipe runs (stub tools on PATH), and the
check_kit.py gate that keeps the AGENTS and CI templates on the modules' recipe names. A project imports a module from
the installed kit, `import '~/.ai-kit/platforms/kits/just/<profile>.just'` (KIT-081 stage 1b: no copy), so each test
project does so, with a throwaway HOME whose ~/.ai-kit holds the kit's modules."""
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/kits/just/**", "plugins/guardrails/templates/**", "platforms/kits/github/workflows/**",
          "platforms/ci/validations/check_kit.py")

KIT = Path(__file__).resolve().parents[3]
MODULES = KIT / "platforms" / "kits" / "just"
CHECK_KIT = "platforms/ci/validations/check_kit.py"
JUST = shutil.which("just")
RECIPES = {
    "godot": {"editor", "run", "import", "boot", "test", "lint", "fmt", "verify", "export"},
    "java": {"run", "test", "verify", "fmt", "lint", "dependency-check"},
    "python": {"test", "lint", "fmt", "verify"},
    "docs": {"lint", "verify", "changelog"},
}


def executable(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


@unittest.skipIf(JUST is None and not os.environ.get("CI"), "just is not on PATH (CI=1 makes it required)")
class ModuleTest(unittest.TestCase):
    """Each module imported by a throwaway project's justfile from ~/.ai-kit, the line sync-project.sh writes; HOME is
    a throwaway folder whose .ai-kit/platforms/kits/just is the kit's module folder."""

    def setUp(self):
        if JUST is None:  # KIT-077: the CI jobs that run this layer install the pinned just
            self.fail("just is not on PATH")

    def project(self, profile, justfile=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "project"
        root.mkdir()
        self.home = Path(tmp.name) / "home"
        (self.home / ".ai-kit" / "platforms" / "kits").mkdir(parents=True)
        (self.home / ".ai-kit" / "platforms" / "kits" / "just").symlink_to(MODULES)
        line = f"import '~/.ai-kit/platforms/kits/just/{profile}.just'\n"
        (root / "justfile").write_text(line + (justfile or ""), encoding="utf-8")
        self.bin = root / ".stub-bin"
        self.bin.mkdir()
        self.log = root / ".stub-log"
        return root

    def just(self, root, *args, env=None):
        full = dict(os.environ, PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}", STUB_LOG=str(self.log),
                    HOME=str(self.home))
        full.update(env or {})
        return subprocess.run([JUST, *args], cwd=root, capture_output=True, text=True, env=full, check=False)

    def calls(self):
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []


class RecipeNames(ModuleTest):
    def test_each_module_has_its_recipes(self):
        for profile, want in RECIPES.items():
            with self.subTest(profile=profile):
                root = self.project(profile)
                result = self.just(root, "--summary")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(set(result.stdout.split()), want)

    def test_a_project_recipe_sits_beside_the_imported_ones(self):
        root = self.project("java", "\n# project recipe\ndb-shell:\n    echo db\n")
        result = self.just(root, "--summary")
        self.assertEqual(set(result.stdout.split()), RECIPES["java"] | {"db-shell"})


class ImportedFromTheKit(ModuleTest):
    def test_an_imported_recipe_runs_in_the_projects_folder(self):
        """just runs an imported recipe in the importing justfile's folder, so `--path .` is the project, never the
        kit's module folder, and the kit's file stays where it is."""
        root = self.project("godot")
        executable(self.bin / "godot", '#!/usr/bin/env bash\nprintf "%s %s\\n" "$PWD" "$*" >> "$STUB_LOG"\n')
        self.assertEqual(self.just(root, "editor").returncode, 0)
        self.assertEqual(self.calls(), [f"{root.resolve()} --path . --editor"])
        self.assertEqual([p.name for p in root.iterdir() if p.suffix == ".just"], [])

    def test_without_the_installed_kit_just_names_the_missing_import(self):
        root = self.project("docs")
        (self.home / ".ai-kit" / "platforms" / "kits" / "just").unlink()
        result = self.just(root, "--summary")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("could not find source file for import", result.stderr)


class Godot(ModuleTest):
    STUB = """#!/usr/bin/env bash
printf 'godot %s\\n' "$*" >> "$STUB_LOG"
case "$*" in
  *--quit*) printf '%s\\n' "${STUB_BOOT:-booted}" ;;
  *GdUnitCmdTool*) printf 'Overall Summary: %s test cases | 0 errors\\n' "${STUB_CASES:-3}" ;;
esac
exit "${STUB_EXIT:-0}"
"""

    def setUp(self):
        self.root = self.project("godot")
        executable(self.bin / "godot", self.STUB)
        (self.root / "addons" / "gdUnit4").mkdir(parents=True)
        (self.root / "tests").mkdir()
        (self.root / "tests" / "a_test.gd").write_text("extends GdUnitTestSuite\n", encoding="utf-8")

    def test_test_imports_then_runs_gdunit4(self):
        result = self.just(self.root, "test")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.calls(), [
            "godot --headless --path . --import",
            "godot --headless --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode"])

    def test_zero_executed_test_cases_fail(self):
        result = self.just(self.root, "test", env={"STUB_CASES": "0"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("executed no test case", result.stderr)

    def test_a_missing_runner_or_no_suite_fails(self):
        shutil.rmtree(self.root / "tests")
        result = self.just(self.root, "test")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no gdUnit4 suite", result.stderr)
        shutil.rmtree(self.root / "addons")
        result = self.just(self.root, "test")
        self.assertIn("addons/gdUnit4 missing", result.stderr)

    def test_gut_runs_when_chosen(self):
        (self.root / "addons" / "gut").mkdir()
        (self.root / "tests" / "test_b.gd").write_text("extends GutTest\n", encoding="utf-8")
        result = self.just(self.root, "test", env={"GODOT_TEST_RUNNER": "gut"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("-s addons/gut/gut_cmdln.gd -gdir=res://test,res://tests -ginclude_subdirs -gexit", self.calls()[-1])

    def test_an_unknown_runner_fails(self):
        result = self.just(self.root, "test", env={"GODOT_TEST_RUNNER": "nope"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown GODOT_TEST_RUNNER 'nope'", result.stderr)

    def test_boot_fails_on_a_script_error_at_exit_0(self):
        for line in ("SCRIPT ERROR: Parse Error: x", "ERROR: Can't load script: res://a.gd"):
            with self.subTest(line=line):
                result = self.just(self.root, "boot", env={"STUB_BOOT": line})
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("script error", result.stderr)
        self.assertEqual(self.just(self.root, "boot").returncode, 0)

    def test_run_passes_its_arguments_to_the_game(self):
        result = self.just(self.root, "run", "--server-url=ws://127.0.0.1:8080/ws")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), ["godot --path . -- --server-url=ws://127.0.0.1:8080/ws"])

    def test_export_names_preset_and_output(self):
        result = self.just(self.root, "export", "Windows Desktop", "build/game.exe")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), ['godot --headless --path . --export-release Windows Desktop build/game.exe'])

    def test_lint_and_fmt_skip_addons_and_dot_godot(self):
        executable(self.bin / "gdformat", '#!/usr/bin/env bash\nprintf "gdformat %s\\n" "$*" >> "$STUB_LOG"\n')
        executable(self.bin / "gdlint", '#!/usr/bin/env bash\nprintf "gdlint %s\\n" "$*" >> "$STUB_LOG"\n')
        (self.root / "main.gd").write_text("extends Node\n", encoding="utf-8")
        (self.root / "addons" / "gdUnit4" / "x.gd").write_text("extends Node\n", encoding="utf-8")
        (self.root / ".godot").mkdir()
        (self.root / ".godot" / "y.gd").write_text("extends Node\n", encoding="utf-8")
        self.assertEqual(self.just(self.root, "lint").returncode, 0)
        self.assertEqual(self.just(self.root, "fmt").returncode, 0)
        calls = self.calls()
        self.assertEqual(sorted(c.split()[0] for c in calls), ["gdformat", "gdformat", "gdlint"])
        self.assertIn("gdformat --check", " | ".join(calls))
        self.assertTrue(all("addons" not in c and ".godot" not in c for c in calls), calls)
        self.assertTrue(all("main.gd" in c and "tests/a_test.gd" in c for c in calls), calls)


class Java(ModuleTest):
    def setUp(self):
        self.root = self.project("java")
        executable(self.root / "mvnw", '#!/usr/bin/env bash\nprintf "mvnw %s\\n" "$*" >> "$STUB_LOG"\n')

    def test_the_gate_and_the_ci_flags(self):
        self.assertEqual(self.just(self.root, "verify").returncode, 0)
        self.assertEqual(self.just(self.root, "verify", env={"MVN_FLAGS": "-B -ntp"}).returncode, 0)
        self.assertEqual(self.calls(), ["mvnw spotless:check verify", "mvnw -B -ntp spotless:check verify"])

    def test_one_test_and_the_other_recipes(self):
        for args in (("test", "-Dtest=SomeTest"), ("fmt",), ("lint",), ("run",)):
            self.assertEqual(self.just(self.root, *args).returncode, 0, args)
        self.assertEqual(self.calls(), ["mvnw test -Dtest=SomeTest", "mvnw spotless:apply", "mvnw spotless:check",
                                        "mvnw spring-boot:run"])

    def test_dependency_check_pins_its_plugin(self):
        self.assertEqual(self.just(self.root, "dependency-check").returncode, 0)
        self.assertRegex(self.calls()[0], r"^mvnw org\.owasp:dependency-check-maven:\d+\.\d+\.\d+:check "
                                          r"-DfailBuildOnCVSS=7 -DnvdApiKeyEnvironmentVariable=NVD_API_KEY$")


class Python(ModuleTest):
    def setUp(self):
        self.root = self.project("python")

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_unittest_runs_every_test_folder(self):
        ok = "import unittest\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n"
        self.write("tools/a/tests/test_a.py", ok)
        self.write("tools/b/tests/test_b.py", ok)
        result = self.just(self.root, "test", env={"PYTHON": sys.executable})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(re.findall(r"Ran 1 test", result.stderr)), 2, result.stderr)

    def test_a_failing_test_fails(self):
        self.write("tests/test_a.py", "import unittest\n\nclass T(unittest.TestCase):\n"
                   "    def test_no(self):\n        self.fail('no')\n")
        self.assertNotEqual(self.just(self.root, "test", env={"PYTHON": sys.executable}).returncode, 0)

    def test_no_test_file_fails(self):
        self.write("tools/a.py", "x = 1\n")
        result = self.just(self.root, "test", env={"PYTHON": sys.executable})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no test_*.py", result.stderr)

    def test_lint_finds_a_syntax_error_without_writing_bytecode(self):
        self.write("tools/a.py", "x = 1\n")
        self.assertEqual(self.just(self.root, "lint", env={"PYTHON": sys.executable}).returncode, 0)
        self.write("tools/b.py", "def f(:\n")
        result = self.just(self.root, "lint", env={"PYTHON": sys.executable})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tools/b.py:1", result.stdout + result.stderr)
        self.assertEqual(list(self.root.rglob("__pycache__")), [])

    def test_fmt_needs_a_configured_formatter(self):
        result = self.just(self.root, "fmt", env={"PYTHON": sys.executable})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no formatter configured", result.stderr)


class Docs(ModuleTest):
    """KIT-081 stage 1: the recipes run the installed kit's validators, ${AI_KIT_DIR:-$HOME/.ai-kit}, not a copy."""
    STUB = '#!/usr/bin/env python3\nimport os, sys\nopen(os.environ["STUB_LOG"], "a").write(" ".join(sys.argv) + "\\n")\n'

    def setUp(self):
        self.root = self.project("docs")  # self.home/.ai-kit holds the modules only, no validator
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        other = tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        self.kit = Path(other.name) / "kit"
        for name in ("check_spec.py", "spec_trace.py", "check_docs_structure.py", "changelog_fragments.py"):
            executable(self.kit / "platforms" / "ci" / "validations" / name, self.STUB)
        (self.root / "docs" / "spec").mkdir(parents=True)

    def names(self):
        return [" ".join([Path(c.split()[0]).name, *c.split()[1:]]) for c in self.calls()]

    def env(self, **extra):
        env = {"PYTHON": sys.executable, "AI_KIT_DIR": "", "HOME": str(self.home)}
        env.update(extra)
        return env

    def test_lint_runs_every_kit_check_from_the_repository_root(self):
        (self.root / "sub").mkdir()
        result = self.just(self.root / "sub", "lint", env=self.env(AI_KIT_DIR=str(self.kit)))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.names(), [f"check_spec.py docs/spec {self.kit}/platforms/ci/schemas",
                                        "spec_trace.py check docs/spec", "check_docs_structure.py"])

    def test_without_ai_kit_dir_the_installed_kit_in_home_runs(self):
        shutil.copytree(self.kit / "platforms" / "ci", self.home / ".ai-kit" / "platforms" / "ci")
        self.assertEqual(self.just(self.root, "verify", env=self.env()).returncode, 0)
        self.assertEqual(self.names()[0], f"check_spec.py docs/spec {self.home}/.ai-kit/platforms/ci/schemas")

    def test_without_the_kit_lint_fails_and_says_where_it_looked(self):
        result = self.just(self.root, "lint", env=self.env())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"lint: no agent-rules-kit spec tools in {self.home}/.ai-kit", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_changelog_runs_the_kit_consolidator_on_the_repository_root(self):
        """KIT-084: `just changelog` moves the changelog.d fragments into CHANGELOG.md; `--check` only validates."""
        (self.root / "sub").mkdir()
        for args, want in ((("changelog",), "changelog_fragments.py --repo-dir ."),
                           (("changelog", "--check"), "changelog_fragments.py --repo-dir . --check")):
            with self.subTest(args=args):
                self.log.unlink(missing_ok=True)
                result = self.just(self.root / "sub", *args, env=self.env(AI_KIT_DIR=str(self.kit)))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(self.names(), [want])

    def test_without_the_kit_changelog_fails_and_says_where_it_looked(self):
        result = self.just(self.root, "changelog", env=self.env())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"changelog: no agent-rules-kit changelog tool in {self.home}/.ai-kit", result.stderr)
        self.assertEqual(self.calls(), [])


# check_kit.py § 14 reads these paths; each fixture holds one mistake or one case that must pass.
FIXTURES = {
    "platforms/kits/just/godot.just": (
        "import:\n    godot --headless --import\n\n"
        'boot scene="res://main.tscn": import\n    godot --headless {{scene}}\n\n'
        "test: import\n    godot --headless -s runner.gd\n\n"
        "verify: test\n"),
    "platforms/kits/just/java.just": "test:\n    ./mvnw test\n\nverify:\n    ./mvnw verify\n",
    "plugins/guardrails/templates/project-agents-java-spring.md": (
        "# Fixture AGENTS template (java)\n\n- Tests `just test`, the gate `just verify`.\n"
        "- A recipe java.just lacks: `just verify-all`.\n"),
    "plugins/guardrails/templates/project-agents-godot-2d.md": (
        "# Fixture AGENTS template (godot)\n\n- The gate `just verify` and the boot proof `just boot`; no tests.\n"),
    "platforms/kits/github/workflows/ci-godot.yml": (
        "# Fixture CI template (godot)\njobs:\n  test:\n    steps:\n"
        "      - run: just boot\n"
        "      - run: just boot-proof\n"
        "      - run: just --no-deps test 2>&1 | tee test-run.log\n"
        "      - run: just --no-deps tests\n"),
    "platforms/kits/github/workflows/ci-java.yml": (
        "# Fixture CI template (java)\njobs:\n  verify:\n    steps:\n      - run: just verify\n"),
}


class TemplatesNameKitRecipes(unittest.TestCase):
    """check_kit.py fails when an AGENTS or CI template names a recipe its profile module lacks."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.kit = Path(cls.tmp.name) / "kit"
        listed = subprocess.run(["git", "-C", str(KIT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                                capture_output=True, text=True, check=True).stdout
        for rel in filter(None, listed.split("\0")):
            if (KIT / rel).is_file():
                (cls.kit / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(KIT / rel, cls.kit / rel)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def check(self):
        return subprocess.run([sys.executable, "-B", str(self.kit / CHECK_KIT)], capture_output=True, text=True)

    def test_each_template_mistake_fails_on_its_own_line(self):
        """Synthetic modules and templates at the four paths check_kit.py reads, so rewording a real template breaks
        no test; the real kit passing is the static job's check_kit.py run (.github/workflows/ci.yml). One run: each
        template is checked on its own, so the mistakes neither mask nor add a line."""
        for rel, body in FIXTURES.items():
            (self.kit / rel).write_text(body, encoding="utf-8")
        result = self.check()
        lines = [line for line in result.stderr.splitlines() if line.startswith("FAIL: ")]
        expected = [
            "project-agents-java-spring.md: names just recipe 'verify-all', which platforms/kits/just/java.just "
            "does not define",
            "ci-godot.yml: names just recipe 'boot-proof', which platforms/kits/just/godot.just does not define",
            # #283 item 7: ci-godot runs `just --no-deps test` after `just boot`; the recipe after the option counts
            "ci-godot.yml: names just recipe 'tests', which platforms/kits/just/godot.just does not define",
            "project-agents-godot-2d.md: names no `just test`",
        ]
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for text in expected:
            with self.subTest(text=text):
                self.assertEqual(sum(text in line for line in lines), 1, result.stderr)
        self.assertEqual([line for line in lines if not any(text in line for text in expected)], [], result.stderr)
        self.assertEqual(len(lines), len(expected), result.stderr)
        self.assertNotIn("names just recipe 'boot'", result.stderr)  # #283 item 8: a default parameter is defined
        self.assertNotIn("names just recipe 'test'", result.stderr)  # the recipe after --no-deps is read whole


if __name__ == "__main__":
    unittest.main()
