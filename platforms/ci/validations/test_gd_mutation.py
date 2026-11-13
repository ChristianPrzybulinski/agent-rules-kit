"""gd_mutation.py: PIT's default operators on the GDScript tree, the runner with a stub Godot, the coverage join and
the differential cache."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

TOOL = Path(__file__).resolve().parent.parent.parent / "tools" / "gd_mutation.py"
HAS_GDTOOLKIT = importlib.util.find_spec("gdtoolkit") is not None
NEEDS_PARSER = unittest.skipUnless(HAS_GDTOOLKIT, "gdtoolkit is not installed (pip install gdtoolkit==4.5.0)")
sys.path.insert(0, str(TOOL.parent))
spec = importlib.util.spec_from_file_location("gd_mutation", TOOL)
gd_mutation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd_mutation)

NO_TYPES = gd_mutation.Types(set(), set())


def mutants(source, types=NO_TYPES):
    """(line, operator, from, to) of every mutant of the source, in tree order: a node before its children."""
    _, found, dropped = gd_mutation.generate(source, "a.gd", "a.gd", types)
    assert dropped == 0, dropped
    return [(m.line, m.operator, m.before, m.after) for m in found]


def body(*lines, returns="void", args="a: int, b: int, xs: Array"):
    return f"func f({args}) -> {returns}:\n" + "".join(f"\t{line}\n" for line in lines)


@NEEDS_PARSER
class OperatorTest(unittest.TestCase):
    """Each of PIT 1.30.0's default operators where GDScript has it; line 2 is the first statement of `f`."""

    def test_comparisons_negate_and_move_the_boundary(self):
        expected = {"<": (">=", "<="), "<=": (">", "<"), ">": ("<=", ">="), ">=": ("<", ">"), "==": ("!=", None),
                    "!=": ("==", None)}
        for op, (negated, boundary) in expected.items():
            with self.subTest(op=op):
                found = mutants(body(f"var c = a {op} b"))
                want = [(2, "NEGATE_CONDITIONALS", f"a {op} b", f"a {negated} b")]
                if boundary:
                    want.append((2, "CONDITIONALS_BOUNDARY", f"a {op} b", f"a {boundary} b"))
                self.assertEqual(found, want)

    def test_membership_and_type_tests_are_negated(self):
        for test, negated in (("a in xs", "a not in xs"), ("a not in xs", "a in xs"), ("a is int", "a is not int"),
                              ("a is not int", "a is int")):
            with self.subTest(test=test):
                self.assertEqual(mutants(body(f"var c = {test}")), [(2, "NEGATE_CONDITIONALS", test, negated)])

    def test_math_operators_swap(self):
        for op, new in (("+", "-"), ("-", "+"), ("*", "/"), ("/", "*"), ("%", "*"), ("&", "|"), ("|", "&"),
                        ("^", "&"), ("<<", ">>"), (">>", "<<")):
            with self.subTest(op=op):
                self.assertEqual(mutants(body(f"var c = a {op} b")), [(2, "MATH", f"a {op} b", f"a {new} b")])

    def test_each_operator_of_a_chain_is_one_mutant(self):
        self.assertEqual(mutants(body("var c = a + b * 2 - 1")),
                         [(2, "MATH", "a + b * 2", "a - b * 2"), (2, "MATH", "b * 2 - 1", "b * 2 + 1"),
                          (2, "MATH", "b * 2", "b / 2")])

    def test_increments_and_negations(self):
        self.assertEqual(mutants(body("a += 1", "a -= b", "a *= 2", "a = -a", "a = -1", "a = -(a + 0)")),
                         [(2, "INCREMENTS", "a += 1", "a -= 1"), (3, "INCREMENTS", "a -= b", "a += b"),
                          (5, "INVERT_NEGS", "-a", "a"), (7, "INVERT_NEGS", "-(a + 0)", "(a + 0)"),
                          (7, "MATH", "a + 0", "a - 0")])

    def test_not_is_removed_and_bare_conditions_are_negated(self):
        source = body("if not a:", "\tpass", "elif !b:", "\tpass", "while xs.is_empty() and a > 0:", "\tbreak",
                      "if true:", "\tpass", "var c = 1 if (a) else 2", "match a:", "\tvar z when z:", "\t\tpass")
        self.assertEqual(mutants(source), [
            (2, "NEGATE_CONDITIONALS", "not a", "a"),
            (4, "NEGATE_CONDITIONALS", "!b", "b"),
            (6, "NEGATE_CONDITIONALS", "xs.is_empty()", "not (xs.is_empty())"),
            (6, "NEGATE_CONDITIONALS", "a > 0", "a <= 0"),
            (6, "CONDITIONALS_BOUNDARY", "a > 0", "a >= 0"),
            (10, "NEGATE_CONDITIONALS", "a", "not (a)"),
            (12, "NEGATE_CONDITIONALS", "z", "not (z)")])

    def test_call_statements_become_pass_except_logging(self):
        source = body("xs.append(1)", "queue_free()", "print(a)", "push_error('x')", "assert(a > 0)",
                      "var c = xs.pop_back()", "await get_tree().process_frame")
        self.assertEqual(mutants(source)[:2], [(2, "VOID_METHOD_CALLS", "xs.append(1)", "pass"),
                                               (3, "VOID_METHOD_CALLS", "queue_free()", "pass")])
        self.assertNotIn("VOID_METHOD_CALLS", [m[1] for m in mutants(source)[2:]])

    def test_returns_fit_the_return_type(self):
        cases = (("bool", "a > 0", [("TRUE_RETURNS", "true"), ("FALSE_RETURNS", "false")]),
                 ("bool", "true", [("FALSE_RETURNS", "false")]),
                 ("int", "a", [("PRIMITIVE_RETURNS", "0")]), ("int", "0", []),
                 ("float", "1.5", [("PRIMITIVE_RETURNS", "0.0")]), ("float", "0.0", []),
                 ("String", "str(a)", [("EMPTY_RETURNS", '""')]), ("String", "''", []),
                 ("StringName", "&\"x\"", [("EMPTY_RETURNS", '&""')]),
                 ("Array[int]", "xs", [("EMPTY_RETURNS", "[]")]),
                 ("Dictionary", "{1: 2}", [("EMPTY_RETURNS", "{}")]),
                 ("PackedByteArray", "PackedByteArray([1])", [("EMPTY_RETURNS", "PackedByteArray()")]),
                 ("Node", "get_parent()", [("NULL_RETURNS", "null")]), ("Variant", "a", [("NULL_RETURNS", "null")]),
                 ("Node", "null", []), ("Vector2", "Vector2.ONE", []), ("Error", "OK", []),
                 ("Node.ProcessMode", "PROCESS_MODE_ALWAYS", []), ("Mode", "Mode.A", []),
                 ("Sample.Inner", "Sample.Inner.new()", [("NULL_RETURNS", "null")]))
        types = gd_mutation.Types({"Sample", "Inner"}, {"Mode"})
        for returns, value, want in cases:
            with self.subTest(returns=returns, value=value):
                found = [m for m in mutants(body(f"return {value}", returns=returns, args=""), types)
                         if m[1].endswith("_RETURNS")]
                self.assertEqual(found, [(2, operator, value, new) for operator, new in want])
        untyped = "func f(a):\n\treturn a\n\n\nfunc g() -> void:\n\treturn\n"
        self.assertEqual(mutants(untyped), [(2, "NULL_RETURNS", "a", "null")])

    def test_accessors_return_their_variable_type_and_functions_are_named_as_coverage_names_them(self):
        source = ("class_name Sample\nextends Node\n\nvar hp: int = 3:\n\tget:\n\t\treturn hp\n\tset(value):\n"
                  "\t\thp = value\nvar guess := 2:\n\tget:\n\t\treturn guess\nvar loose = 1:\n\tget:\n"
                  "\t\treturn loose\n\n\nstatic func s() -> int:\n\treturn 1\n\n\nclass Inner:\n"
                  "\tfunc g() -> bool:\n\t\treturn false\n")
        functions, found, _ = gd_mutation.generate(source, "a.gd", "a.gd", NO_TYPES)
        self.assertEqual(functions, [("hp.get", 5, 6), ("hp.set", 7, 8), ("guess.get", 10, 11),
                                     ("loose.get", 13, 14), ("s", 17, 18), ("Inner.g", 22, 23)])
        self.assertEqual([(m.function, m.operator, m.after) for m in found],
                         [("hp.get", "PRIMITIVE_RETURNS", "0"), ("loose.get", "NULL_RETURNS", "null"),
                          ("s", "PRIMITIVE_RETURNS", "0"), ("Inner.g", "TRUE_RETURNS", "true")])

    def test_lambdas_patterns_annotations_and_constants_are_left_alone(self):
        source = body("var g := func(x): return x + 1", "const K := 1 + 2", "match a:", "\t1 + 1:", "\t\tpass",
                      "@warning_ignore(\"integer_division\")", "var c = a")
        self.assertEqual(mutants(source), [])

    def test_mutants_keep_every_line_and_parse_again(self):
        source = body("xs.append(", "\t\ta +", "\t\tb)", "if (a > 0", "\t\tand b):", "\treturn [", "\t\t1,", "\t]",
                      "return xs", returns="Array")
        found = gd_mutation.generate(source, "a.gd", "a.gd", NO_TYPES)[1]
        self.assertEqual([(m.line, m.operator) for m in found],
                         [(2, "VOID_METHOD_CALLS"), (3, "MATH"), (6, "NEGATE_CONDITIONALS"),
                          (5, "NEGATE_CONDITIONALS"), (5, "CONDITIONALS_BOUNDARY"), (7, "EMPTY_RETURNS"),
                          (10, "EMPTY_RETURNS")])
        for mutant in found:
            mutated = mutant.apply(source)
            self.assertEqual(mutated.count("\n"), source.count("\n"), mutant)
            gd_mutation.GD_PARSER.parse(mutated)
        self.assertEqual(found[0].apply(source).splitlines()[1:5], ["\tpass", "", "", "\tif (a > 0"])

    def test_a_mutant_that_does_not_parse_is_dropped(self):
        def broken(self, node):
            first, stop = self.span(node)
            self.add("VOID_METHOD_CALLS", node, first, stop, "pass(", "x", "pass(")

        with mock.patch.object(gd_mutation.Generator, "on_expr_stmt", broken):
            _, found, dropped = gd_mutation.generate(body("xs.clear()"), "a.gd", "a.gd", NO_TYPES)
        self.assertEqual((found, dropped), ([], 1))


CALC = """class_name Calc
extends Node


func add(a: int, b: int) -> int:
\treturn a + b


func sign_of(n: int) -> int:
\tif n < 0:
\t\treturn -1
\treturn 1
"""
UTIL = "extends Node\n\n\nfunc twice(x: int) -> int:\n\treturn x * 2\n"
PROJECT = 'config_version=5\n\n[application]\n\nconfig/name="t"\n'
SUITE = "extends GdUnitTestSuite\n\n\nfunc test_add() -> void:\n\tassert_int(Calc.new().add(1, 2)).is_equal(3)\n"
# What the stub does when the mutated calc.gd holds the key; one key per mutant of CALC.
RULES = {"a - b": "100",  # add MATH: killed
         "\treturn 0\n\n\nfunc": "105",  # add PRIMITIVE_RETURNS: invalid by exit code
         "n >= 0": "sleep",  # sign_of NEGATE_CONDITIONALS: timed out
         "\t\treturn 0\n": "parse",  # sign_of PRIMITIVE_RETURNS of -1: invalid by a parse error naming the file
         "-1\n\treturn 0": "2"}  # sign_of PRIMITIVE_RETURNS of 1: error; CONDITIONALS_BOUNDARY n <= 0 survives
STUB = """#!{python}
import json, os, subprocess, sys, time
from pathlib import Path
args = sys.argv[1:]
text = None
if "--path" in args:
    folder = Path(args[args.index("--path") + 1])
    target, log = folder / "app" / "calc.gd", folder.parent / "godot.log"
    text = target.read_text() if target.is_file() else None
    if log.exists():
        log.chmod(0o644)
if os.environ.get("STUB_LOG"):
    with open(os.environ["STUB_LOG"], "a") as out:
        call = {{"args": args, "home": os.environ["HOME"], "nice": os.getpriority(os.PRIO_PROCESS, 0), "text": text,
                "at": time.time()}}
        out.write(json.dumps(call) + "\\n")
if args == ["--version"]:
    print("4.7.2.stub")
    sys.exit(0)
if "--import" in args:
    sys.exit(int(os.environ.get("STUB_IMPORT", "0")))
rules = json.loads(os.environ.get("STUB_RULES", "{{}}"))
action = next((v for k, v in rules.items() if text and k in text), None)
if action == "sleep":  # a test waiting on a process it started
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    Path(os.environ["STUB_CHILD"]).write_text(str(child.pid))
    time.sleep(60)
if action == "parse":
    print("SCRIPT ERROR: Parse Error: Expected expression after return.")
    print("          at: GDScript::reload (res://app/calc.gd:11)")
    sys.exit(1)
if action == "slow":  # longer than 10 x the unmutated run, shorter than the default timeout constant
    time.sleep(4)
if action == "lock":  # the tool cannot append this run's output to the worker's log: its run raises
    log.chmod(0o444)
if action == "dir":  # the tool cannot restore the mutated file
    target.unlink()
    target.mkdir()
if action is None:
    time.sleep(float(os.environ.get("STUB_PAUSE", "0")))
print("Overall Summary:")
print("\\x1b[1m %s test cases | 0 errors | 0 failures | 0 flaky | 0 skipped | 0 orphans |\\x1b[0m"
      % os.environ.get("STUB_CASES", "2"))
sys.exit(int(action) if action and action.isdigit() else int(os.environ.get("STUB_EXIT", "0")))
"""
# The tool's load average and core count, from STUB_LOAD and STUB_CORES: no test reads the real host.
SITE = """import os
if os.environ.get("STUB_LOAD"):
    os.getloadavg = lambda: (float(os.environ["STUB_LOAD"]),) * 3
if os.environ.get("STUB_CORES"):
    os.cpu_count = lambda: int(os.environ["STUB_CORES"])
"""
STATUSES = [("add", 6, "PRIMITIVE_RETURNS", "invalid"), ("add", 6, "MATH", "killed"),
            ("sign_of", 10, "NEGATE_CONDITIONALS", "timed out"), ("sign_of", 10, "CONDITIONALS_BOUNDARY", "survived"),
            ("sign_of", 11, "PRIMITIVE_RETURNS", "invalid"), ("sign_of", 12, "PRIMITIVE_RETURNS", "error")]
SURVIVOR = "client/app/calc.gd:10 sign_of CONDITIONALS_BOUNDARY n < 0 → n <= 0"
# The error and timed-out mutants survive instead, so the cache keeps every result.
KEPT = json.dumps({k: v for k, v in RULES.items() if v not in ("2", "sleep")})
KEPT_STATUSES = [*STATUSES[:2], ("sign_of", 10, "NEGATE_CONDITIONALS", "survived"), *STATUSES[3:5],
                 ("sign_of", 12, "PRIMITIVE_RETURNS", "survived")]


class RunnerTest(unittest.TestCase):
    """The runner against a stub `godot` whose exit depends on the mutant written into its copy."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.repo, self.scratch, self.log = root / "repo", root / "scratch", root / "godot.jsonl"
        self.child, self.out = root / "child.pid", root / "out.json"
        self.scratch.mkdir()
        stub = root / "bin" / "godot"
        stub.parent.mkdir()
        stub.write_text(STUB.format(python=sys.executable))
        stub.chmod(0o755)
        site = root / "site" / "sitecustomize.py"
        site.parent.mkdir()
        site.write_text(SITE)
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
                    "GODOT": str(stub), "TMPDIR": str(self.scratch), "STUB_LOG": str(self.log),
                    "STUB_RULES": json.dumps(RULES), "STUB_CHILD": str(self.child), "STUB_PAUSE": "0.2",
                    "XDG_CACHE_HOME": str(root / "cache"),
                    # one gate run holds the host (the cap is 2), 4 cores at load 0.5: no run waits
                    "PATH": f"{stub.parent}{os.pathsep}{os.environ.get('PATH', '')}", "PYTHONPATH": str(site.parent),
                    "XDG_STATE_HOME": str(root / "state"), "STUB_LOAD": "0.5", "STUB_CORES": "4"}
        self.loop_state(gates=[os.getpid()])
        self.git("init", "-q", "-b", "main", str(self.repo), cwd=self.tmp.name)
        self.project = self.repo / "client"
        self.write("project.godot", PROJECT)
        self.write("addons/gdUnit4/bin/GdUnitCmdTool.gd", "extends SceneTree\n")
        self.write("app/calc.gd", CALC)
        self.write("app/util.gd", UTIL)
        self.write("tests/calc_test.gd", SUITE)
        self.write("tests/helper.gd", "extends RefCounted\n\n# builds a Calc\n")
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

    def loop_state(self, gates=(), proofs=()):
        """The review loop's children.json, with a gate-slot record per process of `gates` and of `proofs`."""
        state = Path(self.env["XDG_STATE_HOME"]) / "stratics-review-loop" / "children.json"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps({"gates": {"running": {f"r#{pid}": {"pid": pid} for pid in gates}},
                                     "proofs": {f"r:proof:{pid}": {"pid": pid} for pid in proofs}}))

    def run_tool(self, *args, cwd=None, constant="0", **env):
        """The tool with --timeout-constant 0, so a timed-out stub mutant waits 10 x the unmutated run only;
        constant=None keeps the default."""
        args += ("--timeout-constant", constant) if constant is not None else ()
        return subprocess.run([sys.executable, "-B", str(TOOL), *args], cwd=cwd or self.project,
                              env={**self.env, **env}, capture_output=True, text=True, check=False)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def statuses(self, path=None):
        data = json.loads((self.project / path if path else self.out).read_text())
        return data, [(m["function"], m["line"], m["operator"], m["status"]) for m in data["mutants"]]

    def assert_no_leftovers(self):
        self.assertEqual(list(self.scratch.iterdir()), [])
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual((self.project / "app" / "calc.gd").read_text(), CALC)

    @NEEDS_PARSER
    def test_each_status_restores_the_file_runs_niced_and_removes_its_copy(self):
        result = self.run_tool("app/calc.gd", "--json", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [SURVIVOR])
        self.assertIn("6 mutant(s): 1 killed, 1 survived, 1 timed out, 2 invalid, 1 error; score 66.7 % (2/3)",
                      result.stderr)
        data, statuses = self.statuses()
        self.assertEqual(statuses, STATUSES)
        self.assertEqual((data["tool"], data["ref"], data["project"], data["godot"], data["score"]),
                         ("gd_mutation", self.git("rev-parse", "HEAD").strip(), "client", "4.7.2.stub", 0.6667))
        self.assertEqual([m["exit"] for m in data["mutants"]], [105, 100, None, 0, 1, 2])
        baseline, = data["baselines"]
        self.assertEqual((baseline["tests"], baseline["exit"], baseline["cases"], baseline["ok"]),
                         (["res://tests/calc_test.gd"], 0, 2, True))
        self.assertAlmostEqual(baseline["timeout"], 10 * baseline["seconds"], delta=0.06)  # both rounded to 0.01
        version, imported, unmutated, *runs = self.calls()
        self.assertEqual(version["args"], ["--version"])
        self.assertEqual(imported["args"][2:], ["--headless", "--import"])
        self.assertEqual(unmutated["args"][2:], ["--headless", "-s", "addons/gdUnit4/bin/GdUnitCmdTool.gd", "-a",
                                                 "res://tests/calc_test.gd", "-c", "--ignoreHeadlessMode"])
        self.assertEqual(unmutated["text"], CALC)
        self.assertEqual([sum(key in run["text"] for key in RULES) for run in runs],
                         [int(status != "survived") for *_, status in STATUSES])
        self.assertTrue(all(r["args"][1] == unmutated["args"][1] != imported["args"][1] for r in runs))
        self.assertTrue(all(r["nice"] == min(os.getpriority(os.PRIO_PROCESS, 0) + 10, 20) for r in runs))
        self.assertTrue(all("/gd-mutation-" in r["home"] and r["home"].endswith("/w0/home") for r in runs))
        self.assert_no_leftovers()

    @NEEDS_PARSER
    def test_timeout_stops_the_run_and_the_processes_it_started(self):
        self.run_tool("app/calc.gd")
        pid = int(self.child.read_text())
        for _ in range(50):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            self.fail(f"process {pid} the run started is still alive")

    @NEEDS_PARSER
    def test_workers_each_get_a_clone_and_keep_leaves_the_files_restored(self):
        result = self.run_tool("app/calc.gd", "--workers", "2", "--keep", "--json", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        data, statuses = self.statuses()
        self.assertEqual(statuses, STATUSES)
        kept = Path(result.stderr.split("gd_mutation: kept ", 1)[1].split()[0])
        for worker in ("w0", "w1"):
            self.assertEqual((kept / worker / "project" / "app" / "calc.gd").read_text(), CALC)
        self.assertEqual({c["args"][1] for c in self.calls()[3:]},
                         {str(kept / "w0" / "project"), str(kept / "w1" / "project")})
        self.assertEqual(data["host"], {"cores": 4, "gate_cap": 2, "peak": 2, "waits": {"gates": 0, "load": 0},
                                        "waited": 0.0, "load": [0.5, 0.5], "gates": [1, 1]})
        self.assertNotIn("waited", result.stderr)

    @NEEDS_PARSER
    def test_a_loaded_host_runs_one_mutant_at_a_time_and_every_mutant_still_runs(self):
        result = self.run_tool("app/calc.gd", "--workers", "2", "--json", str(self.out), STUB_LOAD="4.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        data, statuses = self.statuses()
        self.assertEqual(statuses, STATUSES)
        self.assertEqual((data["host"]["peak"], data["host"]["waits"]["gates"]), (1, 0))
        self.assertGreaterEqual(data["host"]["waits"]["load"], 1)
        self.assertIn("for the load", result.stderr)
        self.assertIn("at most 1 of 2 worker(s) ran at once", result.stderr)
        self.assert_no_leftovers()

    @NEEDS_PARSER
    def test_gate_runs_at_the_cap_hold_the_import_until_one_ends(self):
        proof = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
        self.addCleanup(proof.wait)
        self.addCleanup(proof.kill)
        self.loop_state(gates=[os.getpid()], proofs=[proof.pid])
        ended = []

        def end():  # the proof ends half a second after `godot --version`, the call just before the first look
            while not (self.log.exists() and '["--version"]' in self.log.read_text()):
                time.sleep(0.05)
            time.sleep(0.5)
            proof.kill()
            proof.wait()
            ended.append(time.time())

        ender = threading.Thread(target=end, daemon=True)
        ender.start()
        result = self.run_tool("app/calc.gd", "--json", str(self.out))
        ender.join(10)
        self.assertEqual(result.returncode, 0, result.stderr)
        data, statuses = self.statuses()
        self.assertEqual(statuses, STATUSES)
        self.assertEqual((data["host"]["waits"], data["host"]["gates"]), ({"gates": 1, "load": 0}, [1, 2]))
        self.assertGreaterEqual(data["host"]["waited"], gd_mutation.HOST_POLL - 0.1)
        self.assertIn("1 start(s) waited for the gate cap and 0 for the load", result.stderr)
        imported, = [call for call in self.calls() if "--import" in call["args"]]
        self.assertGreater(imported["at"], ended[0])
        self.assert_no_leftovers()

    @NEEDS_PARSER
    def test_mutant_whose_run_raises_is_not_run_the_next_ones_run_and_the_tool_exits_2(self):
        rules = {**RULES, "a - b": "lock"}
        result = self.run_tool("app/calc.gd", "--json", str(self.out), STUB_RULES=json.dumps(rules))
        self.assertEqual((result.returncode, result.stdout.splitlines()), (2, [SURVIVOR]), result.stderr)
        self.assertIn("gd_mutation: client/app/calc.gd:6 MATH not run: PermissionError", result.stderr)
        self.assertIn("6 mutant(s): 1 survived, 1 timed out, 2 invalid, 1 error, 1 not run; score 50.0 % (1/2)",
                      result.stderr)
        expected = [(f, n, o, "not run" if o == "MATH" else s) for f, n, o, s in STATUSES]
        self.assertEqual(self.statuses()[1], expected)
        self.assertEqual(len(self.calls()), 3 + 6)
        self.assert_no_leftovers()

    @NEEDS_PARSER
    def test_worker_that_cannot_restore_the_file_stops_and_the_rest_are_not_run(self):
        result = self.run_tool("app/calc.gd", "--json", str(self.out), STUB_RULES=json.dumps({"a - b": "dir"}))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("calc.gd not restored (IsADirectoryError", result.stderr)
        self.assertIn("4 mutant(s) not run: every worker stopped", result.stderr)
        self.assertEqual([s for *_, s in self.statuses()[1]], ["survived", "survived"] + ["not run"] * 4)
        self.assertEqual(len(self.calls()), 3 + 2)
        self.assert_no_leftovers()

    @NEEDS_PARSER
    def test_timeout_adds_the_constant_so_a_run_slower_than_10_x_the_unmutated_one_is_not_timed_out(self):
        result = self.run_tool("app/calc.gd", "--json", str(self.out), constant=None,
                               STUB_RULES=json.dumps({"a - b": "slow"}), STUB_PAUSE="0")
        self.assertEqual(result.returncode, 0, result.stderr)
        data, statuses = self.statuses()
        baseline, = data["baselines"]
        self.assertAlmostEqual(baseline["timeout"], 10 * baseline["seconds"] + 30, delta=0.06)
        slow, = [m for m in data["mutants"] if m["operator"] == "MATH"]
        self.assertGreater(slow["seconds"], 10 * baseline["seconds"])
        self.assertEqual({s for *_, s in statuses}, {"survived"})

    @NEEDS_PARSER
    def test_unmutated_run_that_does_not_count_exits_2_and_runs_no_mutant(self):
        for env, why in (({"STUB_EXIT": "100"}, "exited 100 with 2 test case(s)"),
                         ({"STUB_CASES": "0"}, "exited 0 with 0 test case(s)")):
            with self.subTest(why=why):
                self.log.unlink(missing_ok=True)
                result = self.run_tool("app/calc.gd", "--json", str(self.out), **env)
                self.assertEqual((result.returncode, result.stdout), (2, ""), result.stderr)
                self.assertIn(f"unmutated run of res://tests/calc_test.gd {why}", result.stderr)
                self.assertEqual({s for *_, s in self.statuses()[1]}, {"not run"})
                self.assertEqual(len(self.calls()), 3)
                self.out.unlink()
                self.assert_no_leftovers()

    @NEEDS_PARSER
    def test_file_without_tests_runs_nothing_and_tests_or_addons_are_not_mutated(self):
        result = self.run_tool("app/util.gd", "tests/calc_test.gd", "addons/gdUnit4/bin/GdUnitCmdTool.gd",
                               "--json", str(self.out))
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)
        self.assertEqual([s for *_, s in self.statuses()[1]], ["no tests", "no tests"])
        self.assertIn("client/tests/calc_test.gd is not mutated", result.stderr)
        self.assertIn("client/addons/gdUnit4/bin/GdUnitCmdTool.gd is not mutated", result.stderr)
        self.assertEqual(self.calls(), [])

    @NEEDS_PARSER
    def test_base_mutates_the_changed_functions_only(self):
        self.write("app/calc.gd", CALC.replace("return 1\n", "return 2\n"))
        self.commit("sign")
        result = self.run_tool("--base", "HEAD~1", "--json", "out.json", cwd=self.project / "app")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({f for f, *_ in self.statuses(path="app/out.json")[1]}, {"sign_of"})
        self.log.unlink()
        result = self.run_tool("--base", "HEAD")
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)
        self.assertIn("no changed .gd function to mutate", result.stderr)
        result = self.run_tool("--ref", "HEAD~1")
        self.assertEqual((result.returncode, result.stdout), (2, ""), result.stderr)
        self.assertIn("--base reads the change of HEAD, not of HEAD~1", result.stderr)
        self.assertEqual(self.calls(), [])

    def coverage(self, **changes):
        """A gd_coverage.py --json report of HEAD that ran sign_of's `if` and last return but not `return -1`."""
        statements = [{"line": 10, "end": 10, "hits": 3}, {"line": 11, "end": 11, "hits": 0},
                      {"line": 12, "end": 12, "hits": 3}]
        report = {"tool": "gd_coverage", "version": 1, "ref": self.git("rev-parse", "HEAD").strip(),
                  "project": "client", "godot": "4.7.2.stub", "files": {"instrumented": 1, "failed": [], "excluded": []},
                  "functions": [{"path": "client/app/calc.gd", "name": "sign_of", "start": 9, "end": 12,
                                 "lines": {"covered": 2, "total": 3}, "branches": {"covered": 1, "total": 2},
                                 "uncovered_lines": [11], "unmeasured_lines": [], "statements": statements,
                                 "outcomes": []}]}
        report.update(changes)
        path = Path(self.tmp.name) / "coverage.json"
        path.write_text(json.dumps(report))
        return str(path)

    @NEEDS_PARSER
    def test_mutant_on_an_uncovered_line_is_listed_without_a_run(self):
        result = self.run_tool("app/calc.gd", "--coverage", self.coverage(), "--json", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.statuses()[1][4], ("sign_of", 11, "PRIMITIVE_RETURNS", "no coverage"))
        self.assertEqual([s for *_, s in self.statuses()[1]][:4] + [self.statuses()[1][5][3]],
                         ["invalid", "killed", "timed out", "survived", "error"])
        self.assertIn("gd_mutation: no coverage: client/app/calc.gd:11 sign_of (1 mutant(s) not run)", result.stderr)
        self.assertIn("2 mutant(s) on lines the coverage report does not measure are run", result.stderr)
        self.assertFalse(any(run["text"] and "\t\treturn 0\n" in run["text"] for run in self.calls()))
        self.assertEqual(len(self.calls()), 3 + 5)

    @NEEDS_PARSER
    def test_coverage_report_of_another_ref_project_or_tool_exits_2(self):
        for changes, why in (({"ref": "0" * 40}, "measured 000000000000 of client"),
                             ({"project": "."}, "measured"),
                             ({"tool": "complexity"}, "is not a gd_coverage.py --json report"),
                             ({"functions": [{"path": "x"}]}, "not read: KeyError")):
            with self.subTest(why=why):
                result = self.run_tool("app/calc.gd", "--coverage", self.coverage(**changes))
                self.assertEqual((result.returncode, result.stdout), (2, ""), result.stderr)
                self.assertIn(why, result.stderr)
                self.assertEqual(self.calls(), [])
                self.assert_no_leftovers()

    def test_missing_tools_or_refs_exit_2(self):
        stub = Path(self.tmp.name) / "stub" / "gdtoolkit"
        stub.mkdir(parents=True)
        (stub / "__init__.py").write_text("")
        (stub / "parser.py").write_text('raise ImportError("stub: gdtoolkit is not installed")\n')
        cases = (({"PYTHONPATH": str(stub.parent)}, ("app/calc.gd",), "gdtoolkit not available"),
                 ({"GODOT": "", "PATH": "/usr/bin:/bin"}, ("app/calc.gd",), "godot not found"),
                 ({}, ("--ref", "no-such-ref", "app/calc.gd"), "git rev-parse failed"),
                 ({}, ("--workers", "0", "app/calc.gd"), "--workers must be 1 or more"))
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
    def test_project_without_gdunit4_or_an_import_that_does_not_finish_exits_2(self):
        result = self.run_tool("app/calc.gd", "--timeout", "1", STUB_RULES="{}", STUB_IMPORT="0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.git("rm", "-q", "-r", "client/addons")
        self.commit("no gdunit4")
        self.log.unlink()
        result = self.run_tool("app/calc.gd")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("addons/gdUnit4/bin/GdUnitCmdTool.gd is not in the project", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assert_no_leftovers()

    def cached_run(self, *args, **env):
        """A run of calc.gd that must exit 0, and the Godot calls it made."""
        before = len(self.calls())
        result = self.run_tool("app/calc.gd", "--json", str(self.out), *args, **env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result, self.calls()[before:]

    @NEEDS_PARSER
    def test_second_run_with_nothing_changed_starts_no_godot(self):
        first, _ = self.cached_run(STUB_RULES=KEPT)
        second, calls = self.cached_run(STUB_RULES=KEPT)
        self.assertEqual(calls, [])
        self.assertEqual(second.stdout, first.stdout)
        self.assertIn("6 mutant(s) not run: their result is in the cache", second.stderr)
        data, statuses = self.statuses()
        self.assertEqual(statuses, KEPT_STATUSES)
        self.assertEqual([m["exit"] for m in data["mutants"]], [105, 100, 0, 0, 1, 0])
        self.assertTrue(all(m["cached"] for m in data["mutants"]))
        self.assertEqual((data["godot"], data["cached"], data["baselines"], data["score"]), (None, 6, [], 0.25))
        self.assertEqual(data["cache"], os.path.join(self.tmp.name, "cache", "ai-kit", "gd-mutation", "cache.json"))
        self.assert_no_leftovers()

    @NEEDS_PARSER
    def test_an_error_or_a_timed_out_mutant_runs_again(self):
        self.cached_run()
        _, (version, imported, unmutated, timed_out, error) = self.cached_run()
        self.assertIn("n >= 0", timed_out["text"])
        self.assertIn("-1\n\treturn 0", error["text"])
        self.assertEqual(self.statuses()[1], STATUSES)
        self.assertEqual([m["cached"] for m in self.statuses()[0]["mutants"]], [True, True, False, True, True, False])

    @NEEDS_PARSER
    def test_a_run_a_slow_host_stopped_is_not_kept_as_detected(self):
        self.cached_run(STUB_RULES=json.dumps({"n >= 0": "sleep"}))  # the host was too slow for this mutant's run
        self.assertEqual(self.statuses()[1][2], STATUSES[2])
        _, calls = self.cached_run(STUB_RULES="{}")  # a quiet host: its tests pass
        self.assertEqual(len(calls), 3 + 1)
        self.assertIn("n >= 0", calls[3]["text"])
        data, statuses = self.statuses()
        self.assertEqual(statuses[2], ("sign_of", 10, "NEGATE_CONDITIONALS", "survived"))
        self.assertEqual([m["cached"] for m in data["mutants"]], [True, True, False, True, True, True])
        cache = Path(self.tmp.name) / "cache" / "ai-kit" / "gd-mutation" / "cache.json"
        kept = json.loads(cache.read_text())
        for entry in kept["functions"].values():  # a cache saved while "timed out" was kept
            for result in entry["mutants"].values():
                result["status"] = "timed out"
        cache.write_text(json.dumps(kept))
        _, calls = self.cached_run(STUB_RULES="{}")
        self.assertEqual(len(calls), 3 + 6)

    @NEEDS_PARSER
    def test_a_moved_function_keeps_its_results_and_a_changed_function_or_test_runs_again(self):
        self.cached_run(STUB_RULES=KEPT)
        self.write("app/calc.gd", CALC.replace("-> int:\n\treturn a + b", "-> int:\n\tvar unused := 0\n\treturn a + b"))
        self.commit("add changes, sign_of moves one line down")
        _, calls = self.cached_run(STUB_RULES=KEPT)
        self.assertEqual(len(calls), 3 + 2)
        self.assertTrue(all("var unused" in call["text"] and "a + b" not in call["text"] for call in calls[3:]))
        moved = [("add", 7, "PRIMITIVE_RETURNS", "invalid"), ("add", 7, "MATH", "killed"),
                 ("sign_of", 11, "NEGATE_CONDITIONALS", "survived"),
                 ("sign_of", 11, "CONDITIONALS_BOUNDARY", "survived"), ("sign_of", 12, "PRIMITIVE_RETURNS", "invalid"),
                 ("sign_of", 13, "PRIMITIVE_RETURNS", "survived")]
        data, statuses = self.statuses()
        self.assertEqual(statuses, moved)
        self.assertEqual([m["cached"] for m in data["mutants"]], [False, False, True, True, True, True])
        self.write("tests/calc_test.gd", SUITE + "\n\nfunc test_sign() -> void:\n\tpass\n")
        self.commit("a new test")
        _, calls = self.cached_run(STUB_RULES=KEPT)
        self.assertEqual(len(calls), 3 + 6)
        data, statuses = self.statuses()
        self.assertEqual((statuses, data["cached"]), (moved, 0))

    @NEEDS_PARSER
    def test_no_cache_runs_every_mutant_and_leaves_the_cache_alone(self):
        cache = Path(self.tmp.name) / "own" / "cache.json"
        self.cached_run("--cache", str(cache), STUB_RULES="{}")
        kept = cache.read_bytes()
        _, calls = self.cached_run("--cache", str(cache), "--no-cache", STUB_RULES="{}")
        self.assertEqual(len(calls), 3 + 6)
        self.assertEqual(cache.read_bytes(), kept)
        self.assertEqual((self.statuses()[0]["cache"], self.statuses()[0]["cached"]), (None, 0))
        self.assertFalse((Path(self.tmp.name) / "cache").exists())

    @NEEDS_PARSER
    def test_a_cache_that_cannot_be_read_or_written_runs_every_mutant(self):
        cache = Path(self.tmp.name) / "cache.json"
        cache.write_text("{")
        result, calls = self.cached_run("--cache", str(cache), STUB_RULES="{}")
        self.assertIn("cache.json not read (JSONDecodeError); every mutant runs", result.stderr)
        self.assertEqual(len(calls), 3 + 6)
        self.assertEqual(len(gd_mutation.load_cache(cache)), 2)
        blocked = Path(self.tmp.name) / "a-file" / "cache.json"
        blocked.parent.write_text("")
        result, calls = self.cached_run("--cache", str(blocked), STUB_RULES="{}")
        self.assertIn("not read (NotADirectoryError); every mutant runs", result.stderr)
        self.assertIn("a-file/cache.json not written: FileExistsError", result.stderr)
        self.assertEqual(len(calls), 3 + 6)


def mutant(key, status="killed", cached=False, span=(1, 2)):
    found = gd_mutation.Mutant("client/p.gd", "p.gd", "f", 2, 9, "MATH", "a + b", "a - b", 10, 11, "-", span=span,
                               status=status, exit=100, seconds=1.0, tests=["res://tests/p_test.gd"])
    found.key, found.cached = key, cached
    return found


class CacheFileTest(unittest.TestCase):
    """The cache file and the function key, without Godot or gdtoolkit."""

    def test_key_ignores_where_the_function_is_and_trailing_blanks_but_not_its_text_or_tests(self):
        hashes = {"res://tests/p_test.gd": "1"}
        key = gd_mutation.function_key(mutant("", span=(2, 3)), ["", "func f():  ", "\treturn a + b\r"], hashes)
        self.assertEqual(key, gd_mutation.function_key(mutant(""), ["func f():", "\treturn a + b"], hashes))
        self.assertNotEqual(key, gd_mutation.function_key(mutant(""), ["func f():", "\treturn a+b"], hashes))
        self.assertNotEqual(key, gd_mutation.function_key(mutant(""), ["func f():", "\treturn a + b"],
                                                          {"res://tests/p_test.gd": "2"}))
        self.assertEqual(mutant("", span=(2, 3)).place(), "0:9:1:MATH:-")

    def test_a_save_merges_with_other_runs_and_keeps_the_functions_used_last(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c" / "cache.json"
            with mock.patch.object(gd_mutation, "CACHE_FUNCTIONS", 2), \
                    mock.patch.object(gd_mutation.time, "time", side_effect=[1.0, 2.0, 3.0, 4.0]):
                gd_mutation.save_cache(path, [mutant("a")], "s1")
                gd_mutation.save_cache(path, [mutant("b"), mutant("x", status="error")], "s2")
                gd_mutation.save_cache(path, [mutant("a", status="survived", cached=True)], "s3")
                gd_mutation.save_cache(path, [mutant("c", status="invalid")], "s4")
            entries = gd_mutation.load_cache(path)
            self.assertEqual(sorted(entries), ["a", "c"])
            self.assertEqual({k: (e["ref"], e["used"]) for k, e in entries.items()}, {"a": ("s1", 3.0),
                                                                                       "c": ("s4", 4.0)})
            self.assertEqual(entries["a"]["mutants"], {"1:9:1:MATH:-": {"status": "killed", "exit": 100,
                                                                         "seconds": 1.0}})
            self.assertEqual(sorted(p.name for p in path.parent.iterdir()), ["cache.json", "cache.json.lock"])

    def test_only_the_mutants_own_verdict_is_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cache.json"
            gd_mutation.save_cache(path, [mutant(status, status=status) for status in gd_mutation.STATUSES], "s1")
            self.assertEqual(sorted(gd_mutation.load_cache(path)), ["invalid", "killed", "survived"])


class HostTest(unittest.TestCase):
    """The admission of Godot runs by gate runs and load, with stub looks at the host instead of the real one."""

    @staticmethod
    def host(*looks, cores=4, wait=60):
        """A host whose Nth look is the Nth (gate runs, load) of looks, the last one after."""
        found = gd_mutation.Host(poll=0.01, wait=wait)
        found.cores, left = cores, list(looks)
        found.probe = lambda: left.pop(0) if len(left) > 1 else left[0]
        return found

    def test_only_the_live_gate_slot_records_of_each_loop_count(self):
        gone = subprocess.Popen([sys.executable, "-c", "pass"])
        gone.wait()
        live = os.getpid()
        with tempfile.TemporaryDirectory() as folder:
            docs, other = Path(folder) / "docs.json", Path(folder) / "other.json"
            docs.write_text(json.dumps({
                "gates": {"running": {"stratics-docs#1": {"pid": live}, "stratics-docs#2": {"pid": gone.pid}}},
                "rechecks": {"running": {"stratics-docs#3": {"pid": live}},
                             "failed": {"stratics-docs#4": {"pid": live}}},
                "proofs": {"stratics-docs:proof-check:5": {"pid": live}, "stratics-docs:merge:6": {"pid": None}},
                "running": {"implement-7": {"pid": live}}, "reviews": {"running": {"review-8": {"pid": live}}}}))
            other.write_text(json.dumps({"proofs": {"stratics-client:run_proof:9": {"pid": live}}}))
            self.assertEqual((gd_mutation.gate_runs([docs]), gd_mutation.gate_runs([docs, other])), (3, 4))

    def test_a_look_reads_the_loop_state_and_the_load_and_serves_every_worker_a_second(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "stratics-review-loop" / "children.json"
            state.parent.mkdir()
            state.write_text(json.dumps({"gates": {"running": {"r#1": {"pid": os.getpid()}}}}))
            found = gd_mutation.Host()
            with mock.patch.dict(os.environ, {"XDG_STATE_HOME": folder}), \
                    mock.patch.object(gd_mutation.os, "getloadavg", return_value=(3.5, 2.0, 1.0)):
                self.assertEqual(found.probe(), (1, 3.5))
                state.write_text("{}")
                self.assertEqual(found.probe(), (1, 3.5))
                with mock.patch.object(gd_mutation, "HOST_FRESH", 0):
                    self.assertEqual(found.probe(), (0, 3.5))

    def test_gate_runs_at_the_cap_hold_even_the_first_run(self):
        found = self.host((2, 0.0), (3, 0.0), (1, 0.0))
        self.assertIs(found.acquire(), True)
        self.assertEqual((found.running, found.peak, found.waits), (1, 1, {"gates": 1, "load": 0}))
        self.assertGreater(found.waited, 0)

    def test_load_at_the_cores_holds_only_a_run_beside_another_of_ours(self):
        found = self.host((0, 4.0))
        self.assertIs(found.acquire(), True)
        left = iter([False, False, True])
        self.assertIsNone(found.acquire(lambda: next(left)))  # it waits until no mutant is left
        self.assertEqual((found.running, found.peak, found.waits), (1, 1, {"gates": 0, "load": 1}))
        found.release()
        self.assertIs(found.acquire(), True)
        below = self.host((1, 3.99))
        self.assertEqual((below.acquire(), below.acquire(), below.peak, below.waits), (True, True, 2,
                                                                                         {"gates": 0, "load": 0}))

    def test_a_run_of_ours_that_ends_wakes_a_waiting_one(self):
        found = self.host((0, 4.0))
        found.poll = 60
        self.assertIs(found.acquire(), True)
        threading.Timer(0.2, found.release).start()
        began = time.monotonic()
        self.assertIs(found.acquire(), True)
        self.assertLess(time.monotonic() - began, 30)

    def test_gate_runs_at_the_cap_for_the_whole_wait_close_the_host(self):
        found = self.host((2, 0.0), wait=0.05)
        with mock.patch.object(gd_mutation, "notice") as told:
            self.assertIs(found.acquire(), False)
            self.assertIs(found.acquire(), False)
        told.assert_called_once_with("2 gate run(s) held the host for 0.05 s: no further Godot run starts")
        self.assertEqual((found.running, found.closed), (0, True))

    def test_a_host_that_does_not_tell_bounds_no_run_and_says_so_once(self):
        found, unreadable = gd_mutation.Host(), gd_mutation.Host()
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(os.environ, {"XDG_STATE_HOME": folder}), \
                mock.patch.object(gd_mutation.os, "getloadavg", side_effect=OSError("no load")), \
                mock.patch.object(gd_mutation, "HOST_FRESH", 0), mock.patch.object(gd_mutation, "notice") as told:
            self.assertEqual((found.acquire(), found.acquire()), (True, True))
            state = Path(folder) / "stratics-review-loop" / "children.json"
            state.parent.mkdir()
            state.write_text('{"gates": ')  # a state the tool cannot read
            self.assertIs(unreadable.acquire(), True)
        self.assertEqual([call.args[0] for call in told.call_args_list],
                         [f"gate runs not counted: no *-review-loop/children.json under {folder}",
                          "load not read: os.getloadavg failed (OSError)",
                          "gate runs not counted: *-review-loop/children.json unreadable (JSONDecodeError) under "
                          f"{folder}", "load not read: os.getloadavg failed (OSError)"])
        self.assertEqual({k: v for k, v in found.report().items() if k != "cores"},
                         {"gate_cap": 2, "peak": 2, "waits": {"gates": 0, "load": 0}, "waited": 0.0, "load": None,
                          "gates": None})

    def test_a_closed_host_runs_no_unmutated_selection(self):
        found = self.host((2, 0.0))
        found.closed = True
        worker = gd_mutation.Worker(Path("/nonexistent"), {}, Path("/nonexistent/godot.log"))
        with mock.patch.object(gd_mutation, "run_godot", return_value=(0, "", 1.0, None)) as run, \
                mock.patch.object(gd_mutation, "notice"):
            runs = gd_mutation.baselines("godot", worker, [("res://tests/a_test.gd",)], 60, 30, found)
        run.assert_not_called()
        self.assertEqual(runs, {("res://tests/a_test.gd",): {"tests": ["res://tests/a_test.gd"], "exit": None,
                                                             "cases": None, "seconds": None, "timeout": None,
                                                             "ok": False}})

    def test_a_closed_host_runs_no_mutant_and_each_is_not_run(self):
        found = self.host((2, 0.0))
        found.closed = True
        mutants = [mutant("a", status=""), mutant("b", status="")]
        worker = gd_mutation.Worker(Path("/nonexistent"), {}, Path("/nonexistent/godot.log"))
        with mock.patch.object(gd_mutation, "run_godot") as run, mock.patch.object(gd_mutation, "notice") as told:
            self.assertEqual(gd_mutation.run_mutants("godot", [worker, worker], mutants, {}, {}, found), 2)
        run.assert_not_called()
        self.assertEqual([m.status for m in mutants], ["not run", "not run"])
        told.assert_called_once_with("2 mutant(s) not run: every worker stopped")


if __name__ == "__main__":
    unittest.main()
