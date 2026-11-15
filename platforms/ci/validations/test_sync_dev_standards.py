"""sync-project.sh and the KIT-074 dev standards: the opt-in doc-structure check in .github/spec-lint/, a generated
kit.just per profile folder, and the keyed-CSV merge driver for the godot profile."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_sync_project import KIT, SCRIPT, SPEC_MD, VERSION  # noqa: E402

JUST = shutil.which("just")
MODULES = KIT / "platforms" / "kits" / "just"
DRIVER = KIT / "platforms" / "kits" / "godot" / "scripts" / "keyed_csv_merge.py"
DOCS_CHECK = KIT / "platforms" / "ci" / "validations" / "check_docs_structure.py"


def header(profile):
    return (f"# agent-rules-kit: generated from platforms/kits/just/{profile}.just by platforms/tools/sync-project.sh;"
            f" kit {VERSION}; do not edit\n")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
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


class DocStructure(Base):
    COPY = ".github/spec-lint/check_docs_structure.py"

    def test_off_by_default(self):
        self.spec_md("sdd:\n  tracker: none\n")
        self.ok()
        self.assertFalse((self.repo / self.COPY).exists())
        self.ok("--check")

    def test_enabled_vendors_the_check_and_check_compares_it(self):
        self.spec_md("sdd:\n  doc_structure:\n    enabled: true\n")
        self.ok()
        self.assertEqual((self.repo / self.COPY).read_bytes(), DOCS_CHECK.read_bytes())
        self.ok("--check")
        (self.repo / self.COPY).write_text("# edited\n")
        self.assertIn("sync: check_docs_structure.py diverges from the kit", self.failing("--check").stdout)

    def test_turned_off_again_the_copy_goes(self):
        self.spec_md("sdd:\n  doc_structure:\n    enabled: true\n")
        self.ok()
        self.spec_md("sdd:\n  doc_structure:\n    enabled: false\n")
        result = self.failing("--check")
        self.assertIn("sync: .github/spec-lint/check_docs_structure.py is generated but sdd.doc_structure is off",
                      result.stdout)
        self.ok()
        self.assertFalse((self.repo / self.COPY).exists())
        self.ok("--check")

    def test_the_vendored_copy_reads_its_block_and_runs(self):
        self.spec_md("sdd:\n  doc_structure:\n    enabled: true\n")
        self.ok()
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True)
        result = subprocess.run([sys.executable, "-B", str(self.repo / self.COPY), "--root", str(self.repo)],
                                capture_output=True, text=True, env=dict(os.environ, CI=""))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL: docs/ has no README.md", result.stdout)
        self.assertNotIn(".github/spec-lint", result.stdout)
        self.assertNotIn("FAIL: .claude", result.stdout)


class JustModules(Base):
    def test_a_root_profile_gets_kit_just_and_a_starter_justfile(self):
        self.ok()
        self.assertEqual(self.text("kit.just"), header("docs") + (MODULES / "docs.just").read_text())
        self.assertIn("import 'kit.just'", self.text("justfile").splitlines())
        self.ok("--check")
        before = self.text("kit.just")
        self.ok()
        self.assertEqual(before, self.text("kit.just"))

    def test_a_project_justfile_is_kept_and_must_import_kit_just(self):
        (self.repo / "Justfile").write_text("own:\n    echo own\n")
        result = self.ok()
        self.assertEqual(self.text("Justfile"), "own:\n    echo own\n")
        # no starter beside it (compare names: macOS folders are case-insensitive)
        self.assertEqual([p.name for p in self.repo.iterdir() if p.name.lower() == "justfile"], ["Justfile"])
        self.assertIn("sync: warning: Justfile does not import kit.just", result.stderr)
        self.assertIn("sync: Justfile does not import kit.just", self.failing("--check").stdout)
        (self.repo / "Justfile").write_text("import \"kit.just\"\n\nown:\n    echo own\n")
        self.ok("--check")

    def test_monorepo_folders_get_their_own_module(self):
        for folder in ("client", "server"):
            (self.repo / folder).mkdir()
        self.ok("--profile", "docs,godot:client,java:server,python:platform")
        self.assertEqual(self.text("client/kit.just"), header("godot") + (MODULES / "godot.just").read_text())
        self.assertEqual(self.text("server/kit.just"), header("java") + (MODULES / "java.just").read_text())
        self.assertEqual(self.text("kit.just"), header("docs") + (MODULES / "docs.just").read_text())
        for folder in ("client", "server", "."):
            self.assertIn("import 'kit.just'", self.text(f"{folder}/justfile").splitlines())
        self.assertFalse((self.repo / "platform").exists())  # no folder, no module: the sync creates none
        self.ok("--check", "--profile", "docs,godot:client,java:server,python:platform")

    def test_a_missing_folder_is_named(self):
        result = self.ok("--profile", "docs,python:platform")
        self.assertIn("sync: warning: platform/ does not exist; no kit.just written there", result.stderr)

    def test_two_profiles_in_one_folder_get_a_module_each_and_shared_recipes(self):
        self.ok("--profile", "docs,python")
        self.assertEqual(self.text("kit-docs.just"), header("docs") + (MODULES / "docs.just").read_text())
        self.assertEqual(self.text("kit-python.just"), header("python") + (MODULES / "python.just").read_text())
        kit = self.text("kit.just").splitlines()
        self.assertIn("mod kit-docs 'kit-docs.just'", kit)
        self.assertIn("mod kit-python 'kit-python.just'", kit)
        self.assertIn("lint: kit-docs::lint kit-python::lint", kit)
        self.assertIn("test: kit-python::test", kit)
        self.assertIn("verify: kit-docs::verify kit-python::verify", kit)
        self.ok("--check", "--profile", "docs,python")
        if JUST:
            summary = subprocess.run([JUST, "--summary"], cwd=self.repo, capture_output=True, text=True)
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertTrue({"fmt", "lint", "test", "verify"} <= set(summary.stdout.split()), summary.stdout)

    def test_check_flags_an_edited_module(self):
        self.ok()
        (self.repo / "kit.just").write_text(self.text("kit.just") + "extra:\n    echo x\n")
        self.assertIn("sync: kit.just diverges from the kit", self.failing("--check").stdout)

    def test_an_unmarked_kit_just_refuses_the_sync_before_any_write(self):
        (self.repo / "kit.just").write_text("own:\n    echo own\n")
        result = self.failing()
        self.assertIn("kit.just exists and is not generated", result.stdout + result.stderr)
        self.assertFalse((self.repo / ".claude").exists())
        self.assertFalse((self.repo / "CLAUDE.md").exists())

    def test_a_symlinked_profile_folder_refuses_the_sync(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        (self.repo / "client").symlink_to(outside.name)
        result = self.failing("--profile", "docs,godot:client")
        self.assertIn("client goes through a symbolic link", result.stdout + result.stderr)
        self.assertEqual(os.listdir(outside.name), [])

    def test_a_dropped_profile_takes_its_module_and_keeps_the_justfile(self):
        (self.repo / "client").mkdir()
        self.ok("--profile", "docs,godot:client")
        self.assertIn("sync: client/kit.just is generated but not in profile",
                      self.failing("--check", "--profile", "docs").stdout)
        self.ok("--profile", "docs")
        self.assertFalse((self.repo / "client" / "kit.just").exists())
        self.assertTrue((self.repo / "client" / "justfile").exists())


class MergeDriver(Base):
    COPY = ".github/merge-drivers/keyed_csv_merge.py"

    def config(self):
        return subprocess.run(["git", "-C", str(self.repo), "config", "--get", "merge.keyed-csv.driver"],
                              capture_output=True, text=True, env=dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull))

    def test_the_godot_profile_vendors_the_driver_and_names_the_setup_step(self):
        (self.repo / "client").mkdir()
        result = self.ok("--profile", "docs,godot:client")
        self.assertEqual((self.repo / self.COPY).read_bytes(), DRIVER.read_bytes())
        self.assertIn("git config merge.keyed-csv.driver", result.stdout)
        self.assertNotEqual(self.config().returncode, 0)  # the sync never writes git config
        self.ok("--check", "--profile", "docs,godot:client")
        (self.repo / self.COPY).write_text("# edited by agent-rules-kit\n")
        self.assertIn(f"sync: {self.COPY} diverges from the kit",
                      self.failing("--check", "--profile", "docs,godot:client").stdout)

    def test_the_step_is_not_repeated_once_configured(self):
        (self.repo / "client").mkdir()
        subprocess.run(["git", "-C", str(self.repo), "config", "merge.keyed-csv.driver", "x %O %A %B"], check=True)
        self.assertNotIn("git config merge.keyed-csv.driver", self.ok("--profile", "docs,godot:client").stdout)

    def test_no_godot_profile_no_driver_and_a_leftover_goes(self):
        self.ok()
        self.assertFalse((self.repo / ".github" / "merge-drivers").exists())
        (self.repo / "client").mkdir()
        self.ok("--profile", "docs,godot:client")
        self.assertIn(f"sync: {self.COPY} is generated but not in profile",
                      self.failing("--check", "--profile", "docs").stdout)
        self.ok("--profile", "docs")
        self.assertFalse((self.repo / self.COPY).exists())

    def test_a_hand_written_file_at_the_driver_path_refuses_the_sync(self):
        (self.repo / ".github" / "merge-drivers").mkdir(parents=True)
        (self.repo / self.COPY).write_text("print('mine')\n")
        (self.repo / "client").mkdir()
        result = self.failing("--profile", "docs,godot:client")
        self.assertIn(f"{self.COPY} exists and is not generated", result.stdout + result.stderr)
        self.assertEqual(self.text(self.COPY), "print('mine')\n")
        self.assertFalse((self.repo / "CLAUDE.md").exists())


if __name__ == "__main__":
    unittest.main()
