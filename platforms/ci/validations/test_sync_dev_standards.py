"""sync-project.sh and the KIT-074 dev standards, which run from the installed kit since KIT-081 stage 1b: each profile
folder's justfile imports the kit's just module, and the godot profile's keyed-CSV merge driver runs from the kit
(the sync prints the one-time git config step). The copies older syncs wrote go: a marked kit.just or vendored driver
is removed, an unmarked one stays, and --check names what is left. The opt-in doc-structure check runs from the kit
since KIT-081 stage 1 (no copy to write)."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/tools/sync-project.sh", "platforms/tools/sync_agents_md.py", "platforms/tools/sync_just.py",
          "platforms/tools/sync_unvendor.py", "platforms/tools/sync-profiles.txt", "plugins/guardrails/**",
          "platforms/kits/just/**", "platforms/kits/github/workflows/spec-lint.yml",
          "platforms/kits/godot/scripts/**", "platforms/ci/validations/check_spec.py",
          "platforms/ci/validations/row_checks.py", "platforms/ci/validations/pr_gates.py",
          "platforms/ci/validations/spec_trace.py", "platforms/ci/validations/check_docs_structure.py",
          "platforms/ci/schemas/**")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_sync_project import KIT, SCRIPT, SPEC_MD  # noqa: E402

JUST = shutil.which("just")
DRIVER = KIT / "platforms" / "kits" / "godot" / "scripts" / "keyed_csv_merge.py"
SYNC_JUST = KIT / "platforms" / "tools" / "sync_just.py"
MARKED = ("# agent-rules-kit: generated from platforms/kits/just/docs.just by platforms/tools/sync-project.sh; kit 13.1.0;"
          " do not edit\nlint:\n    echo copy\n")
KIT_DRIVER = "python3 ~/.ai-kit/platforms/kits/godot/scripts/keyed_csv_merge.py --marker-size %L --path %P %O %A %B"


def imports(profile):
    return f"import '~/.ai-kit/platforms/kits/just/{profile}.just'"


class Base(unittest.TestCase):
    FOLDER = ""  # the repository's folder name inside the temporary folder; "" is the temporary folder itself

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / self.FOLDER
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        (self.repo / "AGENTS.md").write_text("# x\n")
        (self.repo / "docs" / "spec").mkdir(parents=True)

    def run_sync(self, *args):
        env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull)
        return subprocess.run(["bash", str(SCRIPT), *args, str(self.repo)], capture_output=True, text=True,
                              check=False, env=env)

    def ok(self, *args):
        result = self.run_sync(*args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def failing(self, *args):
        result = self.run_sync(*args)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        return result

    def spec_md(self, extra):
        (self.repo / "docs" / "spec" / "spec.md").write_text(SPEC_MD.format(extra=extra))

    def text(self, rel):
        return (self.repo / rel).read_text(encoding="utf-8")


class JustModules(Base):
    # The import logic alone (the starter justfile, a project's justfile and its import line, the migration, a folder
    # with several profiles, a missing folder) is tested in-process in test_sync_just.py (KIT-077).

    def summary(self, folder):
        """`just --summary` in a folder, with a throwaway HOME whose ~/.ai-kit is this kit, as the action links it."""
        home = Path(self.tmp.name) / "home"
        if not home.exists():
            home.mkdir()
            (home / ".ai-kit").symlink_to(KIT)
        return subprocess.run([JUST, "--summary"], cwd=self.repo / folder, capture_output=True, text=True,
                              env=dict(os.environ, HOME=str(home)))

    def test_each_profile_folder_imports_the_installed_kit_module_and_holds_no_copy(self):
        for folder in ("client", "server"):
            (self.repo / folder).mkdir()
        self.ok("--profile", "docs,godot:client,java:server,python:platform")
        for folder, profile in ((".", "docs"), ("client", "godot"), ("server", "java")):
            with self.subTest(folder=folder):
                self.assertEqual(self.text(f"{folder}/justfile").splitlines()[-1], imports(profile))
                self.assertFalse((self.repo / folder / "kit.just").exists())
        self.assertFalse((self.repo / "platform").exists())  # no folder, no justfile: the sync creates none
        self.ok("--check", "--profile", "docs,godot:client,java:server,python:platform")
        if JUST:
            for folder, recipe in ((".", "lint"), ("client", "boot"), ("server", "dependency-check")):
                with self.subTest(folder=folder):
                    result = self.summary(folder)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(recipe, result.stdout.split())

    def test_the_sync_migrates_the_generated_copies(self):
        """KIT-081 stage 1b: a marked kit.just goes and the line importing it names the kit's module; an unmarked
        kit.just is the project's and stays."""
        (self.repo / "client").mkdir()
        (self.repo / "kit.just").write_text(MARKED)
        (self.repo / "client" / "kit.just").write_text(MARKED)
        (self.repo / "justfile").write_text("set allow-duplicate-recipes := true\nimport 'kit.just'\n\nown:\n"
                                            "    echo own\n")
        (self.repo / "client" / "kit-own.just").write_text("own:\n    echo own\n")
        check = self.failing("--check", "--profile", "docs,godot:client").stdout
        self.assertIn("sync: kit.just is a copy the kit no longer generates", check)
        self.assertIn("sync: justfile:2 imports kit.just, which the kit no longer generates", check)
        result = self.ok("--profile", "docs,godot:client")
        self.assertIn("sync: removed client/kit.just (", result.stdout)
        self.assertIn("sync: kept client/kit-own.just (not generated by the kit; the project's own)", result.stdout)
        self.assertFalse((self.repo / "kit.just").exists())
        self.assertEqual(self.text("client/kit-own.just"), "own:\n    echo own\n")
        self.assertEqual(self.text("justfile").splitlines()[1], imports("docs"))
        self.ok("--check", "--profile", "docs,godot:client")
        if JUST:
            result = self.summary(".")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(set(result.stdout.split()), {"changelog", "lint", "own", "verify"})  # KIT-084: changelog

    def test_a_symlinked_profile_folder_refuses_the_sync(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        (self.repo / "client").symlink_to(outside.name)
        result = self.failing("--profile", "docs,godot:client")
        self.assertIn("client goes through a symbolic link", result.stdout + result.stderr)
        self.assertEqual(os.listdir(outside.name), [])

    def sync_just(self, mode, profiles):
        """sync_just.py alone, as a write after a skipped preflight would run it."""
        return subprocess.run([sys.executable, str(SYNC_JUST), mode, str(self.repo), profiles],
                              capture_output=True, text=True, check=False)

    def test_a_dangling_justfile_link_refuses_the_sync_and_writes_nothing_outside(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        (self.repo / "client").mkdir()
        (self.repo / "client" / "justfile").symlink_to(Path(outside.name) / "justfile")  # dangling
        message = "sync: client/justfile is a symbolic link; the sync writes no justfile through it"
        self.assertIn(message, self.failing("--profile", "docs,godot:client").stdout)
        for mode in ("preflight", "write"):
            with self.subTest(mode=mode):
                result = self.sync_just(mode, "docs,godot:client")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(message, result.stdout)
        self.assertEqual(os.listdir(outside.name), [])

    def test_a_justfile_that_is_a_directory_refuses_the_sync(self):
        (self.repo / "justfile").mkdir()
        message = "sync: justfile is not a regular file; the sync writes no starter justfile there"
        self.assertIn(message, self.failing().stdout)
        for mode in ("preflight", "write"):
            with self.subTest(mode=mode):
                result = self.sync_just(mode, "docs")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(message, result.stdout)
                self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((self.repo / "CLAUDE.md").exists())


class MergeDriver(Base):
    """KIT-081 stage 1b: the driver runs from the installed kit; the copy older syncs vendored is a leftover."""
    COPY = ".github/merge-drivers/keyed_csv_merge.py"

    def config(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), "config", *args, "merge.keyed-csv.driver"],
                              capture_output=True, text=True, env=dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull))

    def vendored(self):
        (self.repo / ".github" / "merge-drivers").mkdir(parents=True)
        (self.repo / self.COPY).write_bytes(DRIVER.read_bytes())

    def test_the_godot_profile_names_the_installed_kits_driver_and_writes_no_copy(self):
        (self.repo / "client").mkdir()
        result = self.ok("--profile", "docs,godot:client")
        self.assertIn(f"sync:   git config merge.keyed-csv.driver '{KIT_DRIVER}'", result.stdout)
        self.assertFalse((self.repo / ".github" / "merge-drivers").exists())
        self.assertNotEqual(self.config("--get").returncode, 0)  # the sync never writes git config
        self.ok("--check", "--profile", "docs,godot:client")
        self.assertNotIn("git config merge.keyed-csv", self.ok("--profile", "docs").stdout)

    def test_the_step_is_not_repeated_once_configured(self):
        (self.repo / "client").mkdir()
        subprocess.run(["git", "-C", str(self.repo), "config", "merge.keyed-csv.driver", "x %O %A %B"], check=True)
        self.assertNotIn("git config merge.keyed-csv.driver", self.ok("--profile", "docs,godot:client").stdout)

    def test_a_vendored_copy_is_reported_then_removed(self):
        self.vendored()
        (self.repo / "client").mkdir()
        self.assertIn(f"sync: {self.COPY} is a copy the kit no longer generates (KIT-081 stage 1b); sync-project.sh"
                      " removes it", self.failing("--check", "--profile", "docs,godot:client").stdout)
        result = self.ok("--profile", "docs,godot:client")
        self.assertIn(f"sync: removed {self.COPY} (the driver runs from the installed kit, KIT-081 stage 1b)",
                      result.stdout)
        self.assertFalse((self.repo / ".github" / "merge-drivers").exists())
        self.ok("--check", "--profile", "docs,godot:client")

    def test_check_names_a_git_config_that_runs_the_removed_copy(self):
        (self.repo / "client").mkdir()
        old = f"python3 {self.COPY} --marker-size %L --path %P %O %A %B"
        subprocess.run(["git", "-C", str(self.repo), "config", "merge.keyed-csv.driver", old], check=True)
        self.assertIn(f"sync:   git config merge.keyed-csv.driver '{KIT_DRIVER}'",
                      self.ok("--profile", "docs,godot:client").stdout)
        out = self.failing("--check", "--profile", "docs,godot:client").stdout
        self.assertIn(f"sync: git config merge.keyed-csv.driver runs {self.COPY}, which the kit no longer generates;"
                      f" run:\nsync:   git config merge.keyed-csv.driver '{KIT_DRIVER}'", out)
        self.assertEqual(self.config("--get").stdout.strip(), old)  # --check reads the config and never changes it
        subprocess.run(["git", "-C", str(self.repo), "config", "merge.keyed-csv.driver", KIT_DRIVER], check=True)
        self.ok("--check", "--profile", "docs,godot:client")

    def test_a_hand_written_file_at_the_driver_path_stays_the_projects(self):
        (self.repo / ".github" / "merge-drivers").mkdir(parents=True)
        (self.repo / self.COPY).write_text("print('mine')\n")
        (self.repo / "client").mkdir()
        result = self.ok("--profile", "docs,godot:client")
        self.assertIn(f"sync: kept {self.COPY} (not generated by the kit", result.stdout)
        self.assertEqual(self.text(self.COPY), "print('mine')\n")
        self.ok("--check", "--profile", "docs,godot:client")

    def test_a_project_driver_that_names_the_kit_stays_the_projects(self):
        """#283 item 2 (KIT-079): only the generated header line marks the copy as the kit's, so a project's own
        driver that mentions the kit is neither removed nor replaced."""
        (self.repo / ".github" / "merge-drivers").mkdir(parents=True)
        own = '"""Our CSV driver, adapted from agent-rules-kit KIT-074."""\nprint("mine")\n'
        (self.repo / self.COPY).write_text(own)
        self.ok("--profile", "docs")
        self.assertEqual(self.text(self.COPY), own)
        self.ok("--check", "--profile", "docs")
        (self.repo / "client").mkdir()
        self.ok("--profile", "docs,godot:client")
        self.assertEqual(self.text(self.COPY), own)

    def test_a_copy_reached_through_a_symbolic_link_is_never_removed(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        (Path(outside.name) / "keyed_csv_merge.py").write_bytes(DRIVER.read_bytes())
        (self.repo / ".github").mkdir()
        (self.repo / ".github" / "merge-drivers").symlink_to(outside.name)
        self.ok("--profile", "docs")
        self.assertEqual((Path(outside.name) / "keyed_csv_merge.py").read_bytes(), DRIVER.read_bytes())


if __name__ == "__main__":
    unittest.main()
