"""gd_coverage.py: probes, report and runner of GDScript coverage, with a stub Godot and, when present, the real one."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent.parent / "tools" / "gd_coverage.py"
HAS_GDTOOLKIT = importlib.util.find_spec("gdtoolkit") is not None
NEEDS_PARSER = unittest.skipUnless(HAS_GDTOOLKIT, "gdtoolkit is not installed (pip install gdtoolkit==4.5.0)")
GODOT = os.environ.get("GODOT") or shutil.which("godot")
GDUNIT4 = os.environ.get("KIT_GDUNIT4", "")  # an addons/gdUnit4 folder, e.g. from a Godot project's git archive
NEEDS_GODOT = unittest.skipUnless(HAS_GDTOOLKIT and GODOT and Path(GDUNIT4, "bin", "GdUnitCmdTool.gd").is_file(),
                                  "needs gdtoolkit, godot and KIT_GDUNIT4 set to an addons/gdUnit4 folder")
sys.path.insert(0, str(TOOL.parent))
spec = importlib.util.spec_from_file_location("gd_coverage", TOOL)
gd_coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd_coverage)

SOURCE = """@tool
extends Node

var hp: int = 3:
\tget:
\t\treturn hp
\tset(value):
\t\thp = value


func total(xs: Array[int], n: int) -> int:
\tvar s := 0
\tfor x in xs:
\t\ts += x
\tfor i in range(n, 10, 2):
\t\tif i > 4: break
\twhile s > 100 and \\
\t\t\tn > 0:
\t\ts -= 1
\tif (s > 3
\t\t\tand n > 0):
\t\ts += 1
\telif s < 0:
\t\treturn -1
\telse:
\t\ts = 0
\t@warning_ignore("integer_division")
\ts = s / 2
\tvar sort := func(a, b):
\t\treturn a < b
\treturn s


func pick(n: int) -> String:
\tmatch n:
\t\t1, 2:
\t\t\treturn "low"
\t\tvar z when z > 3:
\t\t\treturn str(z)
\t\t_:
\t\t\tpass
\tawait get_tree().process_frame
\tvar text := "x"
\treturn text


func one(a: int) -> int: return a


static func multi(xs: Array) -> int:
\tfor x in [
\t\t1,
\t\t2,
\t]:
\t\tprint(x)
\treturn xs.size()


class Inner:
\tfunc g() -> void:
\t\tpass
"""
# Reviewed line by line: a run starts after a compound statement, return, break, continue or await; an annotated
# run start and a multi-line iterable stay unmeasured; the lambda body is never entered.
EXPECTED = """@tool
extends Node

var hp: int = 3:
\tget:
\t\tKitCov.hit(0); return hp
\tset(value):
\t\tKitCov.hit(1); hp = value


func total(xs: Array[int], n: int) -> int:
\tKitCov.hit(2); var s := 0
\tfor x in xs:
\t\tKitCov.hit(3); s += x
\tfor i in range((n if KitCov.t(4) else n), 10, 2):
\t\tif KitCov.b(5, i > 4): break
\twhile KitCov.b(7, s > 100 and \\
\t\t\tn > 0):
\t\ts -= 1
\tif KitCov.b(9, (s > 3
\t\t\tand n > 0)):
\t\ts += 1
\telif KitCov.b(11, s < 0):
\t\treturn -1
\telse:
\t\ts = 0
\t@warning_ignore("integer_division")
\ts = s / 2
\tKitCov.hit(13); var sort := func(a, b):
\t\treturn a < b
\treturn s


func pick(n: int) -> String:
\tmatch (n if KitCov.t(14) else n):
\t\t1, 2:
\t\t\tKitCov.hit(15); return "low"
\t\tvar z when z > 3:
\t\t\tKitCov.hit(16); return str(z)
\t\t_:
\t\t\tKitCov.hit(17); pass
\tKitCov.hit(18); await get_tree().process_frame
\tKitCov.hit(19); var text := "x"
\treturn text


func one(a: int) -> int: KitCov.hit(20); return a


static func multi(xs: Array) -> int:
\tfor x in [
\t\t1,
\t\t2,
\t]:
\t\tKitCov.hit(21); print(x)
\tKitCov.hit(22); return xs.size()


class Inner:
\tfunc g() -> void:
\t\tKitCov.hit(23); pass
"""
CALC = """class_name Calc
extends RefCounted


func add(a: int, b: int) -> int:
\treturn a + b


func sign_of(n: int) -> int:
\tif n < 0:
\t\treturn -1
\treturn 1
"""
NETWORK = "extends Node\n\n\nfunc _ready() -> void:\n\tpass\n"
PROJECT = 'config_version=5\n\n[application]\n\nconfig/name="t"\n\n[autoload]\n\nNetwork="*res://app/network.gd"\n'
STUB = """#!{python}
import json, os, re, shutil, sys
from pathlib import Path
args = sys.argv[1:]
if os.environ.get("STUB_LOG"):
    with open(os.environ["STUB_LOG"], "a") as out:
        call = {{"args": args, "home": os.environ["HOME"], "nice": os.getpriority(os.PRIO_PROCESS, 0)}}
        out.write(json.dumps(call) + "\\n")
if args == ["--version"]:
    print("4.7.2.stub")
    sys.exit(0)
copy = Path(args[args.index("--path") + 1])
if "--import" in args:
    sys.exit(0)
if os.environ.get("STUB_DUMP"):
    shutil.copytree(copy, os.environ["STUB_DUMP"])
size = int(re.search(r"const SIZE := (\\d+)", (copy / "kit_cov" / "kit_cov.gd").read_text()).group(1))
if os.environ.get("STUB_WRITE", "1") == "1":
    hits = [int(os.environ.get("STUB_HIT", "1"))] * size
    own = Path(os.environ["KIT_COV_OUT"], f"hits-{{os.getpid()}}.json")
    own.write_text(json.dumps({{"reason": "exit_tree", "hits": hits}}))
if os.environ.get("STUB_OTHER"):  # a Godot process a test started (pid 1 is never the run's)
    hits = [int(os.environ["STUB_OTHER"])] * size
    Path(os.environ["KIT_COV_OUT"], "hits-1.json").write_text(json.dumps({{"reason": "exit_tree", "hits": hits}}))
if os.environ.get("STUB_SLEEP"):  # a test waiting on a process it started
    import subprocess, time
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    Path(os.environ["STUB_SLEEP"]).write_text(str(child.pid))
    time.sleep(60)
print("Overall Summary:")
print("\\x1b[1m %s test cases | 0 errors | 0 failures | 0 flaky | 0 skipped | 0 orphans |\\x1b[0m"
      % os.environ.get("STUB_CASES", "2"))
sys.exit(int(os.environ.get("STUB_EXIT", "0")))
"""
ALL_COVERED = ["client/app/calc.gd:5 add lines 1/1 branches 0/0",
               "client/app/calc.gd:9 sign_of lines 3/3 branches 2/2",
               "client/app/network.gd:4 _ready lines 1/1 branches 0/0"]


class InstrumentTest(unittest.TestCase):
    @NEEDS_PARSER
    def test_probes_keep_every_line_and_the_output_parses(self):
        probes = gd_coverage.instrument(SOURCE, "app/s.gd")
        self.assertEqual(probes.output, EXPECTED)
        self.assertEqual(probes.probes, {"hit": 14, "b": 4, "t": 2, "unmeasured": 2})
        self.assertEqual(probes.next_slot, 24)
        names = [(f.name, f.start, f.end) for f in probes.functions]
        self.assertEqual(names, [("hp.get", 5, 6), ("hp.set", 7, 8), ("total", 11, 31), ("pick", 34, 44),
                                 ("one", 47, 47), ("multi", 50, 56), ("Inner.g", 60, 61)])

    @NEEDS_PARSER
    def test_counters_follow_runs_and_branches(self):
        functions = {f.name: f for f in gd_coverage.instrument(SOURCE, "app/s.gd").functions}
        total = {(s.line, s.counter) for s in functions["total"].statements}
        self.assertTrue({(13, (2,)), (19, (7,)), (26, (12,)), (28, None), (31, (13,))} <= total)
        self.assertEqual([(b.line, b.kind, b.outcome, b.counter) for b in functions["pick"].branches],
                         [(36, "match", "arm", (15,)), (38, "match", "arm", (16,)), (40, "match", "arm", (17,))])
        self.assertEqual([(s.line, s.end, s.counter) for s in functions["multi"].statements],
                         [(51, 54, None), (55, 55, (21,)), (56, 56, (22,))])

    @NEEDS_PARSER
    def test_slots_continue_from_the_previous_file(self):
        probes = gd_coverage.instrument(CALC, "app/calc.gd", first_slot=40)
        self.assertIn("\tKitCov.hit(40); return a + b", probes.output)
        self.assertIn("\tif KitCov.b(41, n < 0):", probes.output)
        self.assertEqual(probes.next_slot, 44)

    @NEEDS_PARSER
    def test_source_that_does_not_parse_raises(self):
        with self.assertRaises(Exception):
            gd_coverage.instrument("extends Node\n\nfunc broken(:\n\tpass\n", "app/broken.gd")

    def test_report_counts_lines_and_branch_outcomes(self):
        function = gd_coverage.Function("app/calc.gd", "sign_of", 9, 12, [
            gd_coverage.Statement(10, 10, (0, 1)), gd_coverage.Statement(11, 11, (0,)),
            gd_coverage.Statement(12, 12, (2,)), gd_coverage.Statement(12, 12, None),
            gd_coverage.Statement(13, 14, None)],
            [gd_coverage.Branch(10, "if", "true", (0,)), gd_coverage.Branch(10, "if", "false", (1,)),
             gd_coverage.Branch(15, "match", "arm", None)])
        result = gd_coverage.report(function, [0, 4, 0])
        self.assertEqual((result["lines"], result["branches"]),
                         ({"covered": 1, "total": 3}, {"covered": 1, "total": 2}))
        self.assertEqual((result["uncovered_lines"], result["unmeasured_lines"]), ([11, 12], [13]))
        self.assertEqual(result["outcomes"][:2], [{"line": 10, "kind": "if", "outcome": "true", "hits": 0},
                                                  {"line": 10, "kind": "if", "outcome": "false", "hits": 4}])

    def test_writer_becomes_the_first_autoload(self):
        line = 'KitCovWriter="*res://kit_cov/kit_cov_writer.gd"'
        self.assertEqual(gd_coverage.add_autoload(PROJECT).splitlines()[6:10],
                         ["[autoload]", line, "", 'Network="*res://app/network.gd"'])
        self.assertEqual(gd_coverage.add_autoload("config_version=5\n").splitlines(),
                         ["config_version=5", "", "[autoload]", "", line])

    def test_summary_is_read_from_the_last_overall_summary(self):
        output = ("Overall Summary:\n 9 test cases | 0 errors | 0 failures | 0 flaky | 0 skipped | 0 orphans |\n"
                  "Overall Summary:\n\x1b[1m 3 test cases | 1 errors | 2 failures | 0 flaky | 1 skipped | "
                  "4 orphans |\x1b[0m\n")
        self.assertEqual(gd_coverage.test_summary(output), {"cases": 3, "errors": 1, "failures": 2, "flaky": 0,
                                                            "skipped": 1, "orphans": 4})
        self.assertIsNone(gd_coverage.test_summary("Godot crashed\n"))


class RunnerTest(unittest.TestCase):
    """The runner against a stub `godot` that records how it was called and writes the counters."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.repo, self.scratch, self.log = root / "repo", root / "scratch", root / "godot.jsonl"
        self.scratch.mkdir()
        stub = root / "bin" / "godot"
        stub.parent.mkdir()
        stub.write_text(STUB.format(python=sys.executable))
        stub.chmod(0o755)
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
                    "GODOT": str(stub), "TMPDIR": str(self.scratch), "STUB_LOG": str(self.log)}
        self.git("init", "-q", "-b", "main", str(self.repo), cwd=self.tmp.name)
        self.project = self.repo / "client"
        self.write("project.godot", PROJECT)
        self.write("addons/gdUnit4/bin/GdUnitCmdTool.gd", "extends SceneTree\n")
        self.write("addons/other/plugin.gd", NETWORK)
        self.write("app/calc.gd", CALC)
        self.write("app/network.gd", NETWORK)
        self.write("tests/calc_test.gd", "extends GdUnitTestSuite\n\n\nfunc test_add() -> void:\n\tpass\n")
        oid = "ab" * 32
        store = self.repo / ".git" / "lfs" / "objects" / oid[:2] / oid[2:4]
        store.mkdir(parents=True)
        (store / oid).write_bytes(b"\x89PNG stored")
        self.write("assets/icon.png", f"version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize 11\n")
        self.write("assets/gone.png", f"version https://git-lfs.github.com/spec/v1\noid sha256:{'cd' * 32}\nsize 3\n")
        self.commit("base")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.repo, env=self.env, capture_output=True,
                              text=True, check=True).stdout

    def write(self, path, text):
        target = self.project / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self, message):
        self.git("add", "-A")
        self.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", message)

    def run_tool(self, *args, cwd=None, **env):
        return subprocess.run([sys.executable, "-B", str(TOOL), *args], cwd=cwd or self.project,
                              env={**self.env, **env}, capture_output=True, text=True, check=False)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    @NEEDS_PARSER
    def test_counted_run_reports_every_function_runs_niced_and_removes_its_copy(self):
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ALL_COVERED)
        self.assertIn("3 function(s): lines 5/5, branches 2/2; 2 test case(s)", result.stderr)
        self.assertIn("1 LFS object(s) are not in the local store", result.stderr)
        version, imported, tests = self.calls()
        self.assertEqual(version["args"], ["--version"])
        self.assertEqual(imported["args"][2:], ["--headless", "--import"])
        self.assertEqual(tests["args"][2:], ["--headless", "-s", "addons/gdUnit4/bin/GdUnitCmdTool.gd",
                                             "-a", "res://tests", "-c", "--ignoreHeadlessMode"])
        self.assertEqual(tests["nice"], min(os.getpriority(os.PRIO_PROCESS, 0) + 10, 20))
        self.assertTrue(tests["home"].startswith(str(self.scratch.resolve()) + "/gd-coverage-")
                        or tests["home"].startswith(str(self.scratch) + "/gd-coverage-"), tests["home"])
        self.assertEqual(list(self.scratch.iterdir()), [])
        self.assertEqual(self.git("status", "--porcelain"), "")

    @NEEDS_PARSER
    def test_copy_is_the_committed_tree_with_probes_outside_tests_and_addons(self):
        self.write("app/calc.gd", CALC.replace("return 1\n", "return 2\n"))  # not committed: not measured
        dump = Path(self.tmp.name) / "dump"
        self.assertEqual(self.run_tool(STUB_DUMP=str(dump)).returncode, 0)
        calc = (dump / "app" / "calc.gd").read_text()
        self.assertIn("\tKitCov.hit(0); return a + b", calc)
        self.assertIn("\tKitCov.hit(3); return 1\n", calc)
        self.assertEqual(calc.count("\n"), CALC.count("\n"))
        self.assertNotIn("KitCov", (dump / "tests" / "calc_test.gd").read_text())
        self.assertNotIn("KitCov", (dump / "addons" / "other" / "plugin.gd").read_text())
        self.assertIn("const SIZE := 5\n", (dump / "kit_cov" / "kit_cov.gd").read_text())
        self.assertIn('[autoload]\nKitCovWriter="*res://kit_cov/kit_cov_writer.gd"\n',
                      (dump / "project.godot").read_text())
        self.assertEqual((dump / "assets" / "icon.png").read_bytes(), b"\x89PNG stored")
        self.assertTrue((dump / "assets" / "gone.png").read_text().startswith("version https://git-lfs"))

    @NEEDS_PARSER
    def test_orphans_count_and_uncovered_lines_are_reported(self):
        result = self.run_tool("--json", "out.json", STUB_EXIT="101", STUB_HIT="0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[1], "client/app/calc.gd:9 sign_of lines 0/3 branches 0/2")
        data = json.loads((self.project / "out.json").read_text())
        self.assertEqual((data["ref"], data["project"], data["godot"]),
                         (self.git("rev-parse", "HEAD").strip(), "client", "4.7.2.stub"))
        self.assertEqual((data["tests"]["cases"], data["tests"]["exit"]), (2, 101))
        self.assertEqual((data["files"], data["lfs"], data["slots"]),
                         ({"instrumented": 2, "failed": [], "excluded": []}, {"filled": 1, "missing": 1}, 5))
        self.assertEqual(data["tests"]["other_processes"], 0)
        self.assertEqual(data["probes"], {"hit": 3, "b": 1, "t": 0, "unmeasured": 0})
        sign_of = data["functions"][1]
        self.assertEqual((sign_of["uncovered_lines"], sign_of["outcomes"][0]),
                         ([10, 11, 12], {"line": 10, "kind": "if", "outcome": "true", "hits": 0}))

    @NEEDS_PARSER
    def test_run_that_does_not_count_exits_2_and_says_why(self):
        for env, why in (({"STUB_EXIT": "100"}, "the suite exited 100"),
                         ({"STUB_EXIT": "105"}, "the suite exited 105"),
                         ({"STUB_CASES": "0"}, "no test case ran"),
                         ({"STUB_WRITE": "0"}, "the counters were not written"),
                         ({"STUB_WRITE": "0", "STUB_OTHER": "1"}, "the counters were not written")):
            with self.subTest(why=why):
                result = self.run_tool(**env)
                self.assertEqual((result.returncode, result.stdout), (2, ""), result.stderr)
                self.assertIn(f"gd_coverage: coverage not counted: {why}", result.stderr)
                self.assertEqual(list(self.scratch.iterdir()), [])

    @NEEDS_PARSER
    def test_base_reports_the_changed_functions_and_runs_nothing_without_one(self):
        self.write("app/calc.gd", CALC.replace("return -1", "return -2"))
        self.commit("sign")
        result = self.run_tool("--base", "HEAD~1", cwd=self.project / "app")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [ALL_COVERED[1]])
        self.log.unlink()
        result = self.run_tool("--base", "HEAD")
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)
        self.assertIn("no changed .gd function to measure", result.stderr)
        self.assertEqual(self.calls(), [])

    @NEEDS_PARSER
    def test_files_and_keep(self):
        result = self.run_tool("app/network.gd", "tests/calc_test.gd", "--keep")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [ALL_COVERED[2]])
        self.assertIn("client/tests/calc_test.gd is not instrumented", result.stderr)
        kept = Path(result.stderr.split("gd_coverage: kept ", 1)[1].split()[0])
        written = list((kept / "hits").glob("hits-*.json"))
        self.assertEqual(len(written), 1)
        self.assertEqual(json.loads(written[0].read_text())["reason"], "exit_tree")
        self.assertIn("--import", (kept / "godot.log").read_text())

    @NEEDS_PARSER
    def test_counters_of_other_godot_processes_are_added(self):
        result = self.run_tool("--json", "out.json", STUB_OTHER="2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("counters of 1 other Godot process(es) added", result.stderr)
        data = json.loads((self.project / "out.json").read_text())
        self.assertEqual(data["tests"]["other_processes"], 1)
        self.assertEqual(data["functions"][1]["outcomes"][0]["hits"], 3)

    @NEEDS_PARSER
    def test_excluded_files_get_no_probes(self):
        dump = Path(self.tmp.name) / "dump"
        result = self.run_tool("--exclude", "res://app/network.gd", "--json", "out.json", STUB_DUMP=str(dump))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ALL_COVERED[:2])
        self.assertIn("1 excluded", result.stderr)
        self.assertEqual((dump / "app" / "network.gd").read_text(), NETWORK)
        self.assertEqual(json.loads((self.project / "out.json").read_text())["files"],
                         {"instrumented": 1, "failed": [], "excluded": ["client/app/network.gd"]})

    @NEEDS_PARSER
    def test_ignored_suites_go_to_gdunit4_and_the_report(self):
        wiring = "res://tests/architecture/dependency_rules_test.gd"
        result = self.run_tool("--ignore", "AutoloadOrderTest", "--ignore", f"{wiring}:test_modules",
                               "--json", "out.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls()[2]["args"][2:], [
            "--headless", "-s", "addons/gdUnit4/bin/GdUnitCmdTool.gd", "-a", "res://tests",
            "-i", "AutoloadOrderTest", "-i", f"{wiring}:test_modules", "-c", "--ignoreHeadlessMode"])
        self.assertIn(f"gdUnit4 leaves out AutoloadOrderTest, {wiring}:test_modules (--ignore)", result.stderr)
        self.assertEqual(json.loads((self.project / "out.json").read_text())["tests"]["ignored"],
                         ["AutoloadOrderTest", f"{wiring}:test_modules"])

    @NEEDS_PARSER
    def test_timeout_stops_the_run_and_the_processes_it_started(self):
        child = Path(self.tmp.name) / "child.pid"
        result = self.run_tool("--timeout", "2", STUB_SLEEP=str(child))
        self.assertEqual((result.returncode, result.stdout), (2, ""), result.stderr)
        self.assertIn("coverage not counted: the suite did not finish in 2 s", result.stderr)
        pid = int(child.read_text())
        for _ in range(50):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            self.fail(f"process {pid} the run started is still alive")
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_missing_tools_or_refs_exit_2(self):
        stub = Path(self.tmp.name) / "stub" / "gdtoolkit"
        stub.mkdir(parents=True)
        (stub / "__init__.py").write_text("")
        (stub / "parser.py").write_text('raise ImportError("stub: gdtoolkit is not installed")\n')
        cases = (({"PYTHONPATH": str(stub.parent)}, (), "gdtoolkit not available"),
                 ({"GODOT": "", "PATH": "/usr/bin:/bin"}, (), "godot not found"),
                 ({}, ("--ref", "no-such-ref"), "git rev-parse failed"))
        for env, args, why in cases:
            with self.subTest(why=why):
                if why == "godot not found" and not HAS_GDTOOLKIT:
                    continue
                result = self.run_tool(*args, **env)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(why, result.stderr)
        result = self.run_tool(cwd=self.repo)
        self.assertEqual(result.returncode, 2)
        self.assertIn("no project.godot in the current directory or above", result.stderr)

    @NEEDS_PARSER
    def test_project_without_gdunit4_exits_2(self):
        shutil.rmtree(self.project / "addons" / "gdUnit4")
        self.commit("drop gdUnit4")
        result = self.run_tool()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("addons/gdUnit4/bin/GdUnitCmdTool.gd is not in the project", result.stderr)


CALC_TEST = """extends GdUnitTestSuite


func test_add() -> void:
\tassert_int(Calc.new().add(1, 2)).is_equal({sum})


func test_sign() -> void:
\tassert_int(Calc.new().sign_of(5)).is_equal(1)
{extra}"""
WIRING_TEST = ("extends GdUnitTestSuite\n\n\nfunc test_wiring() -> void:\n\tassert_int(1).is_equal(2)\n\n\n"
               "func test_other() -> void:\n\tassert_int(1).is_equal(1)\n")
ORPHAN = "\n\nfunc test_orphan() -> void:\n\tvar node := Node.new()\n\tassert_object(node).is_not_null()\n"


@NEEDS_GODOT
class GodotTest(unittest.TestCase):
    """The writer autoload under the real Godot and gdUnit4: the counters reach disk on exit 0, 100 and 101."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com", "GODOT": GODOT}
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], env=self.env, check=True)
        shutil.copytree(GDUNIT4, self.repo / "addons" / "gdUnit4")
        (self.repo / "project.godot").write_text(
            PROJECT.replace("[autoload]\n\nNetwork=\"*res://app/network.gd\"\n", "")
            + '\n[editor_plugins]\n\nenabled=PackedStringArray("res://addons/gdUnit4/plugin.cfg")\n')
        (self.repo / "app").mkdir()
        (self.repo / "app" / "calc.gd").write_text(CALC)
        (self.repo / "tests").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def measure(self, test, *args):
        (self.repo / "tests" / "calc_test.gd").write_text(test)
        subprocess.run(["git", "add", "-A"], cwd=self.repo, env=self.env, check=True)
        subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "t"], cwd=self.repo,
                       env=self.env, check=True)
        result = subprocess.run([sys.executable, "-B", str(TOOL), "--keep", *args], cwd=self.repo, env=self.env,
                                capture_output=True, text=True, check=False)
        kept = Path(result.stderr.split("gd_coverage: kept ", 1)[1].split()[0])
        self.addCleanup(shutil.rmtree, kept, True)
        files = list((kept / "hits").glob("hits-*.json"))
        self.assertEqual(len(files), 1, files)
        return result, json.loads(files[0].read_text())

    def test_passing_suite_is_counted(self):
        result, written = self.measure(CALC_TEST.format(sum=3, extra=""))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["app/calc.gd:5 add lines 1/1 branches 0/0",
                                                      "app/calc.gd:9 sign_of lines 2/3 branches 1/2"])
        self.assertEqual((written["reason"], written["hits"]), ("exit_tree", [1, 0, 1, 1]))

    def test_failing_suite_writes_the_counters_but_is_not_counted(self):
        result, written = self.measure(CALC_TEST.format(sum=4, extra=""))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("coverage not counted: the suite exited 100", result.stderr)
        self.assertEqual((written["reason"], written["hits"][0]), ("exit_tree", 1))

    def test_suite_with_orphans_is_counted(self):
        result, written = self.measure(CALC_TEST.format(sum=3, extra=ORPHAN))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("(exit 101)", result.stderr)
        self.assertEqual((written["reason"], written["hits"][1:]), ("exit_tree", [0, 1, 1]))

    def test_ignored_failing_test_lets_the_run_count(self):
        (self.repo / "tests" / "wiring_test.gd").write_text(WIRING_TEST)
        result, _ = self.measure(CALC_TEST.format(sum=3, extra=""), "--ignore",
                                 "res://tests/wiring_test.gd:test_wiring")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("; 3 test case(s) in", result.stderr)


if __name__ == "__main__":
    unittest.main()
