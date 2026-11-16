"""platforms/tools/sync_just.py in-process (KIT-077 item 4): each profile folder's justfile imports the installed kit's
module (KIT-081 stage 1b: no copy in the project): the import line, the starter justfile, a project's own justfile,
the migration from the generated kit.just copies (marked removed, unmarked kept, the import line rewritten in place),
--check on what is left, a folder with several profiles and a profile folder that does not exist. sync-project.sh's
wiring, the refusals before its first write and the imports under just itself stay integration tests in
test_sync_dev_standards.py."""
import ast
import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git

KIT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location("sync_just_under_test", KIT / "platforms" / "tools" / "sync_just.py")
sj = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sj)
MARKED = "# agent-rules-kit: generated from platforms/kits/just/docs.just by platforms/tools/sync-project.sh;" \
    " kit 13.1.0; do not edit\nlint:\n    echo copy\n"
DOCS = "import '~/.ai-kit/platforms/kits/just/docs.just'"


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


    def test_check_kit_reads_recipes_with_the_same_pattern(self):
        tree = ast.parse((KIT / "platforms" / "ci" / "validations" / "check_kit.py").read_text(encoding="utf-8"))
        patterns = [node.value.args[0].value for node in ast.walk(tree) if isinstance(node, ast.Assign)
                    and [getattr(t, "id", "") for t in node.targets] == ["JUST_RECIPE"]]
        self.assertEqual(patterns, [sj.RECIPE.pattern])


class Backtracking(unittest.TestCase):
    LAYER = "integration"  # starts a process, so a runaway match ends at the timeout instead of hanging the run
    COVERS = ("platforms/tools/sync_just.py",)

    def test_a_line_of_quoted_defaults_matches_in_linear_time(self):  # CodeQL py/redos on the #283 pattern
        script = ("import importlib.util, sys\n"
                  "spec = importlib.util.spec_from_file_location('sj', sys.argv[1])\n"
                  "sj = importlib.util.module_from_spec(spec); spec.loader.exec_module(sj)\n"
                  "line = 'a' + ' A=\"\"' * 40 + ' !'\n"
                  "print(sj.recipes(line), sj.recipes('a' + ' A=\"\"' * 40 + ':'))\n")
        try:
            module = str(KIT / "platforms" / "tools" / "sync_just.py")
            result = subprocess.run([sys.executable, "-I", "-B", "-c", script, module], capture_output=True, text=True,
                                    timeout=60)
        except subprocess.TimeoutExpired:
            self.fail("a 40-parameter line that is no recipe did not finish in 60 s: the pattern backtracks")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[] ['a']")


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)

    def run_mode(self, mode, profiles="docs"):
        """(exit code, stdout, stderr) of `sync_just.py <mode> <repo> <profiles>`, in-process."""
        out, err = io.StringIO(), io.StringIO()
        saved, code = sys.argv, 0
        sys.argv = ["sync_just.py", mode, str(self.repo), profiles]
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


    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


class ImportLine(Base):
    def test_a_folder_without_a_justfile_gets_a_starter_that_imports_the_installed_kit_module(self):
        (self.repo / "client").mkdir()
        out, _ = self.ok("write", "docs,godot:client")
        self.assertEqual(sj.import_line("godot"), "import '~/.ai-kit/platforms/kits/just/godot.just'")
        for folder, profile in ((".", "docs"), ("client", "godot")):
            with self.subTest(folder=folder):
                lines = self.text(f"{folder}/justfile").splitlines()
                self.assertEqual(lines[-1], f"import '~/.ai-kit/platforms/kits/just/{profile}.just'")
                self.assertTrue(all(line.startswith("#") for line in lines[:-1]), lines)
        self.assertIn("sync: created client/justfile (import '~/.ai-kit/platforms/kits/just/godot.just';", out)
        self.assertEqual(sorted(p.name for p in self.repo.rglob("*.just")), [])  # no module copy in the project
        self.ok("check", "docs,godot:client")
        before = self.text("justfile")
        self.ok("write", "docs,godot:client")
        self.assertEqual(self.text("justfile"), before)

    def test_a_project_justfile_is_kept_and_must_import_the_kit_module(self):
        """was test_sync_dev_standards JustModules.test_a_project_justfile_is_kept_and_must_import_kit_just"""
        self.write("Justfile", "own:\n    echo own\n")
        _, err = self.ok("write")
        self.assertIn(f"sync: warning: Justfile does not import the kit's docs module; add the line {DOCS}", err)
        self.assertEqual(self.text("Justfile"), "own:\n    echo own\n")
        # no starter beside it (compare names: macOS folders are case-insensitive)
        self.assertEqual([p.name for p in self.repo.iterdir() if p.name.lower() == "justfile"], ["Justfile"])
        self.assertIn(f"sync: Justfile does not import the kit's docs module; add the line {DOCS}",
                      self.failing("check"))
        self.write("Justfile", 'import? "~/.ai-kit/platforms/kits/just/docs.just"  # kit\n\nown:\n    echo own\n')
        self.ok("check")

    def test_a_folder_with_several_profiles_gets_no_import_and_a_warning(self):
        _, err = self.ok("write", "docs,python")
        self.assertFalse((self.repo / "justfile").exists())
        self.assertIn("sync: warning: ./ has profiles docs, python: the sync imports no kit module there", err)
        _, err = self.ok("check", "docs,python")
        self.assertIn("has profiles docs, python", err)

    def test_a_missing_folder_is_named(self):  # was JustModules.test_a_missing_folder_is_named
        _, err = self.ok("preflight", "docs,python:platform")
        self.assertIn("sync: warning: platform/ does not exist; no justfile written there", err)


class Migration(Base):
    """KIT-081 stage 1b: the kit.just and kit-<profile>.just copies an older sync generated go; the project's own
    files and imports stay."""

    def test_the_marked_copies_go_and_the_kit_just_import_is_rewritten_in_place(self):
        self.write("kit.just", MARKED)
        self.write("kit-docs.just", MARKED)
        self.write("client/kit.just", MARKED)
        self.write("justfile", "set allow-duplicate-recipes := true\nimport 'kit.just'  # kit recipes\n\nown:\n"
                               "    echo own\n")
        self.write("client/justfile", f"import '~/.ai-kit/platforms/kits/just/java.just'\n{DOCS}\nimport 'kit.just'\n")
        out, _ = self.ok("write", "docs,godot:client")
        self.assertEqual(self.text("justfile"), "set allow-duplicate-recipes := true\n"
                                                f"{DOCS}  # kit recipes\n\nown:\n    echo own\n")
        # after a profile switch the first kit module import is this profile's; a kit.just import line goes
        self.assertEqual(self.text("client/justfile"), "import '~/.ai-kit/platforms/kits/just/godot.just'\n"
                                                       f"{DOCS}\n")
        self.assertEqual(sorted(p.name for p in self.repo.rglob("*.just")), [])
        for line in ("sync: justfile:2 imports the kit's docs module (was kit.just)",
                     "sync: client/justfile:1 imports the kit's godot module (was the kit's java module)",
                     "sync: client/justfile:3 dropped import 'kit.just'; the kit's module is imported",
                     "sync: removed kit.just (the justfile imports the installed kit's module, KIT-081 stage 1b)",
                     "sync: removed kit-docs.just (", "sync: removed client/kit.just ("):
            with self.subTest(line=line):
                self.assertIn(line, out)
        self.ok("check", "docs,godot:client")

    def test_an_unmarked_kit_just_and_its_import_stay_the_projects(self):
        self.write("kit.just", "own:\n    echo own\n")
        self.write("justfile", "import 'kit.just'\n")
        out, err = self.ok("write")
        self.assertEqual(self.text("kit.just"), "own:\n    echo own\n")
        self.assertEqual(self.text("justfile"), "import 'kit.just'\n")
        self.assertIn("sync: kept kit.just (not generated by the kit; the project's own)", out)
        self.assertIn("sync: warning: justfile does not import the kit's docs module", err)
        check = self.failing("check")
        self.assertNotIn("imports kit.just", check)
        self.assertIn("sync: justfile does not import the kit's docs module", check)

    def test_a_marked_module_reached_through_a_symbolic_link_stays(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        target = Path(outside.name) / "kit.just"
        target.write_text(MARKED, encoding="utf-8")
        (self.repo / "kit.just").symlink_to(target)
        self.write("justfile", f"{DOCS}\n")
        self.ok("write")
        self.assertTrue((self.repo / "kit.just").is_symlink())
        self.assertEqual(target.read_text(encoding="utf-8"), MARKED)

    def test_check_names_each_copy_left_and_each_line_importing_it(self):
        self.write("kit.just", MARKED)
        self.write("client/kit-godot.just", MARKED)
        self.write("justfile", "# recipes\nown:\n    echo own\nimport 'kit.just'\n")
        out = self.failing("check", "docs,godot:client")
        self.assertIn("sync: kit.just is a copy the kit no longer generates (KIT-081 stage 1b); sync-project.sh"
                      " removes it", out)
        self.assertIn("sync: client/kit-godot.just is a copy the kit no longer generates", out)
        self.assertIn("sync: justfile:4 imports kit.just, which the kit no longer generates (KIT-081 stage 1b);"
                      f" replace the line with {DOCS} (sync-project.sh does)", out)
        self.assertIn("sync: client/justfile missing; it imports the kit's godot module", out)
        self.assertNotIn("sync: justfile does not import", out)  # the kit.just line already names the fix


if __name__ == "__main__":
    unittest.main()
