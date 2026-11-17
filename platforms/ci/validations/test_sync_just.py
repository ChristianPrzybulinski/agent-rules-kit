"""platforms/tools/sync_just.py in-process (KIT-077 item 4): a project keeps no justfile for the kit's recipes (KIT-085):
the sync writes none and requires no import, removes the starter justfiles older syncs wrote (recognized by their
whole text, never through a symbolic link), keeps a justfile with the project's own content whole, and keeps the
migration from the generated kit.just copies (marked removed, unmarked kept, a kit.just import line rewritten in
place); --check names what is left. sync-project.sh's wiring stays an integration test in
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


V2 = ("# This folder's recipes for just (https://just.systems). The import runs the {p} recipes of the\n"
      "# installed agent-rules-kit (~/.ai-kit; in CI the kit's spec-tools action links it), with no copy in the\n"
      "# project. Add this folder's own recipes below it.\n"
      "import '~/.ai-kit/platforms/kits/just/{p}.just'\n")  # the starter KIT-081 stage 1b wrote, kept verbatim
V1 = ("# This folder's recipes for just (https://just.systems). The kit's recipes come from kit.just, which\n"
      "# agent-rules-kit's platforms/tools/sync-project.sh writes; add this folder's own recipes below the import.\n"
      "{line}\n")  # the starter KIT-074 to KIT-080 wrote; stage 1b rewrote its import line in place


class NoProjectJustfile(Base):
    """KIT-085: the sync writes no justfile and requires no import; skill sdd-implement runs the kit's module."""

    def test_a_folder_without_a_justfile_gets_none_and_check_passes(self):
        (self.repo / "client").mkdir()
        out, _ = self.ok("write", "docs,godot:client")
        self.assertEqual(sorted(p.name for p in self.repo.rglob("*")), ["client"])
        self.assertIn("sync: just: no project justfile; skill sdd-implement runs the kit's modules"
                      " (just -f ~/.ai-kit/platforms/kits/just/docs.just -d . <recipe>,"
                      " just -f ~/.ai-kit/platforms/kits/just/godot.just -d client <recipe>);"
                      " 0 starters and 0 copies removed", out)
        self.assertNotIn("import", out)
        self.ok("check", "docs,godot:client")

    def test_the_starters_older_syncs_wrote_go(self):
        self.write("justfile", V2.format(p="docs"))
        self.write("client/justfile", V1.format(line="import '~/.ai-kit/platforms/kits/just/godot.just'"))
        self.write("server/justfile", V1.format(line="import 'kit.just'").replace("\n", "\r\n") + "\n")
        self.write("server/kit.just", MARKED)
        self.write("tools/justfile", V2.format(p="python"))  # a folder no profile names any more
        out = self.failing("check", "docs,godot:client,java:server")
        for name in ("justfile", "client/justfile", "server/justfile", "tools/justfile"):
            with self.subTest(name=name):
                self.assertIn(f"sync: {name} is the starter justfile an older sync wrote, only the kit import;", out)
        self.assertIn("sync: server/kit.just is a copy the kit no longer generates", out)
        out, _ = self.ok("write", "docs,godot:client,java:server")
        self.assertEqual([p for p in self.repo.rglob("*") if p.is_file()], [])
        self.assertIn("sync: removed client/justfile (the starter an older sync wrote; skill sdd-implement runs", out)
        self.assertIn("4 starters and 1 copies removed", out)
        self.ok("check", "docs,godot:client,java:server")

    def test_a_justfile_with_the_projects_own_content_stays_whole(self):
        own = {"justfile": V2.format(p="docs") + "\nown:\n    echo own\n",
               "client/justfile": "# my notes\n" + V2.format(p="godot"),
               "server/justfile": V2.format(p="java").replace("/java.just'", "/java.just'  # kit"),
               "tools/.justfile": V2.format(p="python"),  # only `justfile` is a name the sync wrote
               "web/justfile": "own:\n    echo own\n"}
        for name, text in own.items():
            self.write(name, text)
        profiles = "docs,godot:client,java:server,python:tools,python:web"
        self.ok("check", profiles)
        out, err = self.ok("write", profiles)
        for name, text in own.items():
            with self.subTest(name=name):
                self.assertEqual(self.text(name), text)
        for name in ("justfile", "client/justfile", "server/justfile", "tools/.justfile"):
            self.assertIn(f"sync: kept {name} (the project's own; it imports a kit module", out)
        self.assertNotIn("web/justfile", out + err)  # nothing of the kit's in it, nothing to say

    def test_a_starter_reached_through_a_symbolic_link_stays(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        target = Path(outside.name) / "justfile"
        target.write_text(V2.format(p="godot"), encoding="utf-8")
        (self.repo / "client").symlink_to(outside.name)  # a profile folder through a link
        (self.repo / "justfile").symlink_to(target)  # a justfile that is a link
        self.ok("check", "docs,godot:client")
        self.ok("write", "docs,godot:client")
        self.assertTrue((self.repo / "justfile").is_symlink())
        self.assertEqual(target.read_text(encoding="utf-8"), V2.format(p="godot"))

    def test_a_dangling_justfile_link_and_a_justfile_folder_are_left_alone(self):
        (self.repo / "client").mkdir()
        (self.repo / "client" / "justfile").symlink_to(self.repo / "nowhere")
        (self.repo / "justfile").mkdir()
        self.ok("check", "docs,godot:client")
        self.ok("write", "docs,godot:client")
        self.assertTrue((self.repo / "client" / "justfile").is_symlink())
        self.assertTrue((self.repo / "justfile").is_dir())


class Migration(Base):
    """KIT-081 stage 1b: the kit.just and kit-<profile>.just copies an older sync generated go; the project's own
    files and imports stay. KIT-085 keeps that migration and rewrites only kit.just import lines."""

    def test_the_marked_copies_go_and_the_kit_just_import_is_rewritten_in_place(self):
        self.write("kit.just", MARKED)
        self.write("kit-docs.just", MARKED)
        self.write("client/kit.just", MARKED)
        self.write("justfile", "set allow-duplicate-recipes := true\nimport 'kit.just'  # kit recipes\n\nown:\n"
                               "    echo own\n")
        self.write("client/justfile", f"import '~/.ai-kit/platforms/kits/just/godot.just'\n{DOCS}\nimport 'kit.just'\n")
        out, _ = self.ok("write", "docs,godot:client")
        self.assertEqual(self.text("justfile"), "set allow-duplicate-recipes := true\n"
                                                f"{DOCS}  # kit recipes\n\nown:\n    echo own\n")
        # the project's other kit imports stay as they are; a kit.just import line goes when the module is imported
        self.assertEqual(self.text("client/justfile"), "import '~/.ai-kit/platforms/kits/just/godot.just'\n"
                                                       f"{DOCS}\n")
        self.assertEqual(sorted(p.name for p in self.repo.rglob("*.just")), [])
        for line in ("sync: justfile:2 imports the kit's docs module (was kit.just)",
                     "sync: client/justfile:3 dropped import 'kit.just'; the kit's module is imported",
                     "sync: removed kit.just (a kit module copy;", "sync: removed kit-docs.just (",
                     "sync: removed client/kit.just ("):
            with self.subTest(line=line):
                self.assertIn(line, out)
        self.ok("check", "docs,godot:client")

    def test_a_kit_just_import_in_a_folder_without_one_profile_is_a_warning(self):
        self.write("justfile", "import 'kit.just'\nown:\n    echo own\n")
        _, err = self.ok("write", "docs,python")
        self.assertIn("sync: warning: justfile:1 imports kit.just, which the kit no longer generates (KIT-081 stage"
                      " 1b); remove the line, or import a kit module", err)
        self.assertEqual(self.text("justfile"), "import 'kit.just'\nown:\n    echo own\n")

    def test_an_unmarked_kit_just_and_its_import_stay_the_projects(self):
        self.write("kit.just", "own:\n    echo own\n")
        self.write("justfile", "import 'kit.just'\n")
        self.write("client/kit.just", "own:\n    echo own\n")
        self.write("client/justfile", V1.format(line="import 'kit.just'"))  # its kit.just is the project's
        out, err = self.ok("write", "docs,godot:client")
        self.assertEqual(self.text("kit.just"), "own:\n    echo own\n")
        self.assertEqual(self.text("justfile"), "import 'kit.just'\n")
        self.assertEqual(self.text("client/justfile"), V1.format(line="import 'kit.just'"))
        self.assertIn("sync: kept kit.just (not generated by the kit; the project's own)", out)
        self.assertEqual(err, "")
        self.ok("check", "docs,godot:client")

    def test_a_marked_module_reached_through_a_symbolic_link_stays(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        target = Path(outside.name) / "kit.just"
        target.write_text(MARKED, encoding="utf-8")
        (self.repo / "kit.just").symlink_to(target)
        self.write("justfile", f"{DOCS}\nown:\n    echo own\n")
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
        self.assertNotIn("missing", out)  # KIT-085: no justfile is required


class SkillNamesTheCommand(unittest.TestCase):
    """KIT-085: skill sdd-implement runs the recipes, so its text names the command shape the sync prints and the
    profile lookup that picks the stack. KIT-087 P2b: the skill names the kit as `"$KIT"`, the folder the session
    reference project-profile.md finds (~/.ai-kit by default, the folder the sync prints)."""

    SKILL = KIT / "plugins" / "guardrails" / "skills" / "sdd-implement"

    @staticmethod
    def shape(stack, folder):
        return sj.run_line(stack, folder).replace(f"{sj.KIT_HOME}/platforms/kits/just/{stack}.just",
                                                  f'"$KIT/platforms/kits/just/{stack}.just"')

    def test_the_recipes_reference_names_the_command_and_the_profile_lookup(self):
        text = (self.SKILL / "references" / "recipes.md").read_text(encoding="utf-8")
        self.assertIn(self.shape("<stack>", "<repo>/<folder>").replace(" <recipe>", " <recipe> [args]"), text)
        self.assertIn("`PROFILE resolve --section stacks --json <repo>` (`KIT` and `PROFILE`: "
                      "`../../session/references/project-profile.md`)", text)
        self.assertIn("profile.py resolve --section tests --json <repo>", text)

    def test_the_skill_and_its_test_gates_point_at_the_reference(self):
        skill = (self.SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(self.shape("<stack>", "<folder>"), skill)
        self.assertIn("`references/recipes.md`", skill)
        self.assertIn("(`recipes.md`)", (self.SKILL / "references" / "test-gates.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
