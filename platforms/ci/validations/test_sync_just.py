"""platforms/tools/sync_just.py in-process (KIT-077 item 4): the just-module logic that test_sync_dev_standards.py
checked through a whole sync-project.sh run: a project's own justfile and its import line, an edited module, a
dropped profile and a profile folder that does not exist. sync-project.sh's wiring, the refusals before its first
write and the generated modules under just itself stay integration tests there."""
import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git

KIT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location("sync_just_under_test", KIT / "platforms" / "tools" / "sync_just.py")
sj = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sj)
VERSION = "0.0.0"


class Recipes(unittest.TestCase):
    def test_every_recipe_header_form_is_read(self):  # #283 item 8: a default parameter was missed
        text = "\n".join([
            "build:", "@quiet:", "test *ARGS:", "check +FILES:", "lint $FLAG:", 'run target="debug":',
            "pick x='a' y=b:", "verify: lint boot test", "export PRESET OUT:",
            'x := "a"', 'set shell := ["bash", "-c"]', "alias b := build", 'export X := "1"', "  indented:",
            "[group('ci')]", "# comment:",
        ])
        self.assertEqual(sj.recipes(text), ["build", "quiet", "test", "check", "lint", "run", "pick", "verify",
                                            "export"])


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)

    def run_mode(self, mode, profiles="docs"):
        """(exit code, stdout, stderr) of `sync_just.py <mode> <repo> <version> <profiles>`, in-process."""
        out, err = io.StringIO(), io.StringIO()
        saved, code = sys.argv, 0
        sys.argv = ["sync_just.py", mode, str(self.repo), VERSION, profiles]
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                sj.main()
        except SystemExit as stop:
            code = stop.code
        finally:
            sys.argv = saved
        return code, out.getvalue(), err.getvalue()

    def ok(self, mode, profiles="docs"):
        code, out, err = self.run_mode(mode, profiles)
        self.assertEqual(code, 0, out + err)
        return out, err

    def failing(self, mode, profiles="docs"):
        code, out, err = self.run_mode(mode, profiles)
        self.assertEqual(code, 1, out + err)
        return out

    def text(self, rel):
        return (self.repo / rel).read_text(encoding="utf-8")


class ProjectJustfile(Base):
    def test_a_project_justfile_is_kept_and_must_import_kit_just(self):
        """was test_sync_dev_standards JustModules.test_a_project_justfile_is_kept_and_must_import_kit_just"""
        (self.repo / "Justfile").write_text("own:\n    echo own\n", encoding="utf-8")
        _, err = self.ok("preflight")
        self.assertIn("sync: warning: Justfile does not import kit.just", err)
        self.ok("write")
        self.assertEqual(self.text("Justfile"), "own:\n    echo own\n")
        # no starter beside it (compare names: macOS folders are case-insensitive)
        self.assertEqual([p.name for p in self.repo.iterdir() if p.name.lower() == "justfile"], ["Justfile"])
        self.assertIn("sync: Justfile does not import kit.just", self.failing("check"))
        (self.repo / "Justfile").write_text("import \"kit.just\"\n\nown:\n    echo own\n", encoding="utf-8")
        self.ok("check")


class Modules(Base):
    def test_check_flags_an_edited_module(self):  # was JustModules.test_check_flags_an_edited_module
        self.ok("write")
        (self.repo / "kit.just").write_text(self.text("kit.just") + "extra:\n    echo x\n", encoding="utf-8")
        self.assertIn("sync: kit.just diverges from the kit", self.failing("check"))

    def test_a_dropped_profile_takes_its_module_and_keeps_the_justfile(self):
        """was JustModules.test_a_dropped_profile_takes_its_module_and_keeps_the_justfile"""
        (self.repo / "client").mkdir()
        self.ok("write", "docs,godot:client")
        self.assertIn("sync: client/kit.just is generated but not in profile", self.failing("check", "docs"))
        self.ok("write", "docs")
        self.assertFalse((self.repo / "client" / "kit.just").exists())
        self.assertTrue((self.repo / "client" / "justfile").exists())

    def test_a_missing_folder_is_named(self):  # was JustModules.test_a_missing_folder_is_named
        _, err = self.ok("preflight", "docs,python:platform")
        self.assertIn("sync: warning: platform/ does not exist; no kit.just written there", err)


if __name__ == "__main__":
    unittest.main()
