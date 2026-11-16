"""platforms/tools/run_tests.py (KIT-077): the layer tags, the selection by layer and by the changed files, the chunks
and shards, unittest's summary lines, and the kit's own suite: every class tagged, every COVERS glob live, only the
latency budgets in the performance layer. The runner's parallel run on a throwaway suite is the integration class."""
import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git

KIT = Path(__file__).resolve().parents[3]
RUNNER = KIT / "platforms" / "tools" / "run_tests.py"
_SPEC = importlib.util.spec_from_file_location("run_tests_under_test", RUNNER)
rt = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(rt)
PERFORMANCE = {"test_hooks_context.ContextHooksTest.test_latency_budget",
               "test_hooks_guard_compact.HooksTest.test_each_hook_within_budget",
               "test_hooks_instructions_loaded.InstructionsLoadedHookTest.test_stays_within_budget",
               "test_hooks_path_rules.HookCommandTest.test_stays_within_budget"}  # KIT-081 stage 3


class Fake:
    """A test as discover() sees it: an id and a type."""

    def __init__(self, tid):
        self.tid = tid

    def id(self):
        return self.tid


def entry(tid, layer, covers=(), module=None):
    return rt.Entry(Fake(tid), layer, covers, module or f"platforms/ci/validations/{tid.split('.')[0]}.py")


SUITE = [entry("test_a.Unit.test_one", "unit"), entry("test_a.Unit.test_two", "unit"),
         entry("test_b.Shape.test_one", "contract"),
         entry("test_c.Sync.test_one", "integration", ("platforms/tools/sync-project.sh", "plugins/guardrails/**")),
         entry("test_c.Sync.test_two", "integration", ("platforms/tools/sync-project.sh", "plugins/guardrails/**")),
         entry("test_d.Review.test_one", "integration", ("platforms/tools/review_checks.py",)),
         entry("test_e.Fixture.test_one", "functional"), entry("test_f.Hook.test_budget", "performance")]


def ids(entries):
    return [e.id for e in entries]


class Selection(unittest.TestCase):
    def test_layers_pick_their_tests(self):
        self.assertEqual(ids(rt.select(SUITE, {"unit", "contract"})),
                         ["test_a.Unit.test_one", "test_a.Unit.test_two", "test_b.Shape.test_one"])
        self.assertEqual(ids(rt.select(SUITE, {"performance"})), ["test_f.Hook.test_budget"])

    def test_a_change_reaches_the_integration_classes_whose_covers_match(self):
        picked = rt.select(SUITE, {"unit", "integration"}, ["plugins/guardrails/skills/git/SKILL.md"])
        self.assertEqual(ids(picked), ["test_a.Unit.test_one", "test_a.Unit.test_two", "test_c.Sync.test_one",
                                       "test_c.Sync.test_two"])

    def test_a_changed_test_module_runs_its_own_classes(self):
        picked = rt.select(SUITE, {"integration"}, ["platforms/ci/validations/test_d.py"])
        self.assertEqual(ids(picked), ["test_d.Review.test_one"])

    def test_a_change_no_test_covers_runs_no_integration_test(self):
        for changed in (["docs/features/KIT-077.md"], ["CHANGELOG.md", ".github/CONTRIBUTING.md"], []):
            with self.subTest(changed=changed):
                self.assertEqual(ids(rt.select(SUITE, {"integration"}, changed)), [])

    def test_code_no_covers_names_runs_the_whole_layer(self):
        for path in ("platforms/tools/new_tool.py", "platforms/ci/validations/helper.py",
                     "platforms/kits/docker/compose.yml"):
            with self.subTest(path=path):
                picked = rt.select([e for e in SUITE if e.layer == "integration"] + [entry(
                    "test_g.Other.test_one", "integration", ("platforms/tools/other.py",))], {"integration"}, [path])
                self.assertEqual(len(picked), 4)

    def test_a_root_manifest_or_version_change_no_covers_names_runs_the_whole_layer(self):
        """#294 item 3: the root plugin manifests and VERSION are code too, so a release PR runs every integration
        class before its merge instead of only the ones whose COVERS names a root file."""
        for path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json", ".devin-plugin/plugin.json",
                     "VERSION"):
            with self.subTest(path=path):
                self.assertEqual(rt.unknown_code([path], ["platforms/tools/sync-project.sh"]), [path])
                picked = rt.select(SUITE, {"integration"}, [path])
                self.assertEqual(ids(picked), ids(rt.select(SUITE, {"integration"})))

    def test_unknown_code_ignores_markdown_test_modules_and_paths_outside_the_code_folders(self):
        covers = ["platforms/tools/sync-project.sh"]
        self.assertEqual(rt.unknown_code(["platforms/tools/README.md", "platforms/ci/validations/test_x.py",
                                          ".github/workflows/ci.yml", "docs/x.py", "platforms/tools/sync-project.sh"],
                                         covers), [])
        self.assertEqual(rt.unknown_code(["platforms/ci/validations/helper.py"], covers),
                         ["platforms/ci/validations/helper.py"])

    def test_the_other_layers_ignore_the_changes(self):
        picked = rt.select(SUITE, {"unit", "contract", "functional", "performance"}, [])
        self.assertEqual(ids(picked), ids(rt.select(SUITE, {"unit", "contract", "functional", "performance"})))
        self.assertEqual(len(picked), 5)


class Chunks(unittest.TestCase):
    def test_a_fast_class_is_one_chunk_and_a_slow_test_its_own(self):
        self.assertEqual(rt.chunks(SUITE), [
            ["test_a.Unit.test_one", "test_a.Unit.test_two"], ["test_b.Shape.test_one"], ["test_c.Sync.test_one"],
            ["test_c.Sync.test_two"], ["test_d.Review.test_one"], ["test_e.Fixture.test_one"],
            ["test_f.Hook.test_budget"]])

    def test_shards_interleave_and_cover_every_chunk_once(self):
        items = list(range(10))
        parts = [rt.shard(items, f"{i}/3") for i in (1, 2, 3)]
        self.assertEqual(parts, [[0, 3, 6, 9], [1, 4, 7], [2, 5, 8]])
        for bad in ("0/3", "4/3", "1/0"):
            with self.subTest(spec=bad), self.assertRaises(ValueError):
                rt.shard(items, bad)


class Summary(unittest.TestCase):
    def total(self, **kw):
        base = {"run": 3, "failures": [], "errors": [], "unexpected": [], "skipped": [], "seconds": {}, "outcomes": {}}
        base.update(kw)
        return base

    def test_ok_keeps_unittests_lines_and_lists_skips_by_reason(self):
        text, ok = rt.summary(self.total(skipped=[("a", "no just"), ("b", "no just"), ("c", "no godot")]), 1.5)
        self.assertTrue(ok)
        self.assertIn("\nRan 3 tests in 1.500s\n\nOK (skipped=3)\n", text)
        self.assertIn("run_tests: skipped 2: no just\nrun_tests: skipped 1: no godot\n", text)

    def test_a_failure_prints_its_block_and_fails(self):
        text, ok = rt.summary(self.total(failures=[("test_x (m.C.test_x)", "Traceback\nAssertionError: 1 != 2")],
                                         seconds={"m.C.test_x": 0.2}), 0.2, durations=1)
        self.assertFalse(ok)
        self.assertIn("=" * 70 + "\nFAIL: test_x (m.C.test_x)\n" + "-" * 70 + "\nTraceback\nAssertionError", text)
        self.assertIn("FAILED (failures=1)\n", text)
        self.assertIn("run_tests: slowest 1\n     0.200s  m.C.test_x\n", text)

    def test_an_unexpected_success_fails(self):
        _, ok = rt.summary(self.total(unexpected=["test_y (m.C.test_y)"]), 0.1)
        self.assertFalse(ok)

    def test_one_test_is_singular(self):
        self.assertIn("Ran 1 test in", rt.summary(self.total(run=1), 0.0)[0])


class Discovery(unittest.TestCase):
    def write(self, folder, name, text):
        (folder / name).write_text(textwrap.dedent(text), encoding="utf-8")

    def test_an_untagged_class_or_an_integration_class_without_covers_is_named(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.write(folder, "test_rt_tagged.py", """
                import unittest
                LAYER = "unit"
                class Tagged(unittest.TestCase):
                    def test_x(self):
                        pass
                class Slow(unittest.TestCase):
                    LAYER = "integration"
                    COVERS = ("platforms/tools/x.sh",)
                    def test_y(self):
                        pass
                    def test_z(self):
                        pass
                    test_z.LAYER = "performance"
                """)
            self.write(folder, "test_rt_untagged.py", """
                import unittest
                class Bare(unittest.TestCase):
                    def test_x(self):
                        pass
                class Wide(unittest.TestCase):
                    LAYER = "integration"
                    def test_y(self):
                        pass
                """)
            try:
                entries, failed, problems = rt.discover(folder)
                self.assertEqual(failed, [])
                self.assertEqual(problems, [
                    "test_rt_untagged.Bare: LAYER None is none of unit, contract, integration, functional, performance",
                    "test_rt_untagged.Wide: an integration class lists the files it exercises in COVERS"])
                layers = {e.id.split(".", 1)[1]: e.layer for e in entries}
                self.assertEqual(layers["Tagged.test_x"], "unit")
                self.assertEqual(layers["Slow.test_y"], "integration")
                self.assertEqual(layers["Slow.test_z"], "performance")
                files, _, problems = rt.discover(folder, ["test_rt_untagged.py"])
                self.assertEqual((problems, sorted(e.id for e in files)),
                                 ([], ["test_rt_untagged.Bare.test_x", "test_rt_untagged.Wide.test_y"]))
            finally:
                for name in ("test_rt_tagged", "test_rt_untagged"):
                    sys.modules.pop(name, None)
                while str(folder) in sys.path:
                    sys.path.remove(str(folder))

    def test_an_unknown_layer_is_a_usage_error(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(rt.main(["--layer", "unit,smoke"]), 2)
        self.assertIn("run_tests: unknown layer smoke", err.getvalue())


class KitSuite(unittest.TestCase):
    LAYER = "contract"  # the kit's own files, read in-process

    @classmethod
    def setUpClass(cls):
        cls.entries, cls.failed, cls.problems = rt.discover()
        tracked = []
        for base, dirs, files in os.walk(KIT):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
            tracked += [Path(base, name).relative_to(KIT).as_posix() for name in files]
        cls.files = tracked

    def test_every_test_class_has_a_layer(self):
        self.assertEqual((self.failed, self.problems), ([], []))

    def test_every_covers_glob_names_a_kit_file(self):
        globs = sorted({glob for e in self.entries for glob in e.covers})
        dead = [glob for glob in globs if not any(rt.pr_gates.path_matches(path, glob) for path in self.files)]
        self.assertEqual(dead, [])

    def test_only_the_latency_budgets_are_the_performance_layer(self):
        self.assertEqual({e.id for e in self.entries if e.layer == "performance"}, PERFORMANCE)


class ParallelRun(unittest.TestCase):
    """The runner as CI starts it, on a throwaway suite: worker processes, unittest's report, the exit codes."""

    LAYER = "integration"  # starts processes (scripts, git, temp repos)
    COVERS = ("platforms/tools/run_tests.py",)

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name)
        (self.folder / "test_rt_pass.py").write_text(textwrap.dedent("""
            import unittest
            LAYER = "unit"
            class Pass(unittest.TestCase):
                def test_one(self):
                    self.assertTrue(True)
                @unittest.skip("not here")
                def test_skipped(self):
                    pass
            """), encoding="utf-8")
        (self.folder / "test_rt_fail.py").write_text(textwrap.dedent("""
            import unittest
            LAYER = "integration"
            COVERS = ("platforms/tools/x.sh",)
            class Fail(unittest.TestCase):
                def test_two(self):
                    print("noise only a failure shows")
                    self.assertEqual(1, 2)
            """), encoding="utf-8")

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-B", str(RUNNER), "--start", str(self.folder), "--jobs", "2", *args],
                              capture_output=True, text=True, check=False, timeout=120)

    def test_a_failing_test_fails_the_run_with_unittests_report(self):
        result = self.run_cli("--json", str(self.folder / "out.json"))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL: test_two (test_rt_fail.Fail.test_two)", result.stdout)
        self.assertIn("noise only a failure shows", result.stdout)
        self.assertIn("Ran 3 tests in ", result.stdout)
        self.assertIn("FAILED (failures=1, skipped=1)", result.stdout)
        self.assertIn('"outcome": "fail"', (self.folder / "out.json").read_text(encoding="utf-8"))

    def test_a_layer_passes_alone_and_a_file_runs_whole(self):
        result = self.run_cli("--layer", "unit")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK (skipped=1)", result.stdout)
        self.assertNotIn("test_two", result.stdout)
        whole = self.run_cli(str(self.folder / "test_rt_fail.py"))
        self.assertEqual(whole.returncode, 1, whole.stdout + whole.stderr)
        self.assertIn("Ran 1 test in ", whole.stdout)

    def test_nothing_to_run_is_no_failure_only_with_changes_or_a_shard(self):
        self.assertEqual(self.run_cli("--layer", "functional").returncode, 2)
        empty = self.run_cli("--layer", "functional", "--shard", "1/2")
        self.assertEqual(empty.returncode, 0, empty.stdout + empty.stderr)
        self.assertIn("run_tests: nothing to run", empty.stdout)

    def test_a_module_that_cannot_import_is_an_error(self):
        (self.folder / "test_rt_broken.py").write_text("import not_a_module_anywhere\n", encoding="utf-8")
        result = self.run_cli("--layer", "unit")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: test_rt_broken", result.stdout)
        self.assertIn("ModuleNotFoundError", result.stdout)

    def test_in_files_mode_a_module_that_cannot_import_stops_only_itself(self):
        """#294 item 1 (KIT-079): red runs the PR's modules on base, where loading a file the PR adds raises
        FileNotFoundError, not ImportError; that module is one error and the next module still runs."""
        (self.folder / "test_rt_new.py").write_text("open('/a file the PR adds/ci_red.py')\n", encoding="utf-8")
        result = self.run_cli(str(self.folder / "test_rt_new.py"), str(self.folder / "test_rt_fail.py"))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ERROR: test_rt_new", result.stdout)
        self.assertIn("FileNotFoundError", result.stdout)
        self.assertIn("FAIL: test_two (test_rt_fail.Fail.test_two)", result.stdout)
        self.assertIn("Ran 2 tests in ", result.stdout)
        self.assertNotIn("Traceback (most recent call last)", result.stderr)


if __name__ == "__main__":
    unittest.main()
