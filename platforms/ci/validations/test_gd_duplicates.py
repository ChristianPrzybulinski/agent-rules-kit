"""gd_duplicates.py: structural duplicates of changed GDScript functions in a throwaway repo."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent.parent / "tools" / "gd_duplicates.py"
HAS_GDTOOLKIT = importlib.util.find_spec("gdtoolkit") is not None
NEEDS_PARSER = unittest.skipUnless(HAS_GDTOOLKIT, "gdtoolkit is not installed (pip install gdtoolkit==4.5.0)")

# Copied from stratics-client app/network/group_validator.gd and stats_validator.gd at f98e0091.
INTEGER = """static func _integer(value: Variant, minimum: int, maximum: int) -> bool:
\tif typeof(value) != TYPE_INT and typeof(value) != TYPE_FLOAT:
\t\treturn false
\treturn (
\t\tis_finite(float(value))
\t\tand value == floorf(float(value))
\t\tand value >= minimum
\t\tand value <= maximum
\t)
"""
NAME_OK = """static func _name_ok(name: String) -> bool:
\treturn name.length() > 2 and name.length() < 17 and not name.begins_with(" ")
"""
LABEL = """func _label(stat: String, value: int) -> String:
\tvar text := stat.capitalize() + ": " + str(value)
\tif value > 99:
\t\ttext += " (max)"
\treturn text
"""
CLAMP_ALL = """func clamp_all(values: Array, low: float, high: float) -> Array:
\tvar result := []
\tfor value in values:
\t\tif value < low:
\t\t\tresult.append(low)
\t\telif value > high:
\t\t\tresult.append(high)
\t\telse:
\t\t\tresult.append(value)
\treturn result
"""
# DENSE: 2 lines, 56 nodes (only MIN_LINES drops it). SPARSE: 4 lines, 23 nodes (only MIN_NODES drops it).
DENSE = """func _valid_tag(tag: String) -> bool:
\treturn tag.length() > 2 and tag.length() < 17 and not tag.begins_with(" ") and tag.to_lower() == tag
"""
SPARSE = """func _reset() -> void:
\thealth = 10
\tmana = 5
\tlevel = 1
"""
# A session wrapper that differs from its siblings only in its string literals (the client's `_request` shape).
REQUEST = """func _request(kind: String, payload: Dictionary) -> void:
\tif not _connected():
\t\tpush_warning("{a}: not connected")
\t\treturn
\tvar message := {{"type": "{a}_" + kind, "payload": payload}}
\t_pending[kind] = Time.get_ticks_msec()
{extra}\tnetwork.send(message)
\temit_signal("{a}_requested", kind)
"""


def request(area, extra=""):
    return REQUEST.format(a=area, extra=extra)


def gd(*functions):
    return "extends RefCounted\n\n\n" + "\n\n".join(functions)


def line_of(text, needle):
    return next(n for n, line in enumerate(text.splitlines(), 1) if needle in line)


GROUP = gd(NAME_OK, INTEGER)
STATS = gd(LABEL, INTEGER)


class GdDuplicatesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.cache = Path(self.tmp.name) / "cache"
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
                    "XDG_CACHE_HOME": str(self.cache)}
        self.git("init", "-q", "-b", "main", str(self.repo), cwd=self.tmp.name)
        self.write("app/group_validator.gd", GROUP)
        self.write("app/legacy_a.gd", gd(CLAMP_ALL, SPARSE))
        self.write("app/legacy_b.gd", gd(CLAMP_ALL, SPARSE))
        self.write("app/small_a.gd", gd(DENSE, SPARSE))
        self.write("app/small_b.gd", gd(DENSE, SPARSE))
        self.write("app/daycare_session.gd", gd(request("daycare")))
        self.write("app/arena_session.gd", gd(request("arena")))
        self.write("addons/vendor/copy.gd", gd(INTEGER))
        self.commit("base")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.write("app/stats_validator.gd", STATS)
        self.commit("stats")
        self.stats_integer = f"app/stats_validator.gd:{line_of(STATS, '_integer')} _integer"
        self.group_integer = f"app/group_validator.gd:{line_of(GROUP, '_integer')} _integer"

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.repo, env=self.env, capture_output=True,
                              text=True, check=True).stdout

    def write(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self, message):
        self.git("add", "-A")
        self.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", message)

    def run_tool(self, *args, env=None):
        return subprocess.run([sys.executable, "-B", str(TOOL), *args], cwd=self.repo, env=env or self.env,
                              capture_output=True, text=True, check=False)

    @NEEDS_PARSER
    def test_changed_copy_of_an_existing_function_is_reported_and_unchanged_pairs_are_not(self):
        result = self.run_tool("--base", self.base)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [f"1.000 {self.stats_integer} {self.group_integer}"])
        self.assertIn("1 pair(s) at >= 0.82 for 2 function(s)", result.stderr)  # _label and _integer
        self.assertEqual(self.git("status", "--porcelain"), "")  # the cache lives outside the tree

    @NEEDS_PARSER
    def test_all_reports_unchanged_pairs_but_not_small_functions_or_addons(self):
        result = self.run_tool("--all")
        self.assertEqual(result.returncode, 0, result.stderr)
        # Not DENSE or SPARSE (below one minimum each), not the addons/ copy, not the sessions (their strings differ).
        self.assertEqual(result.stdout.splitlines(), [f"1.000 {self.group_integer} {self.stats_integer}",
                                                      "1.000 app/legacy_a.gd:4 clamp_all app/legacy_b.gd:4 clamp_all"])

    @NEEDS_PARSER
    def test_change_in_the_next_function_does_not_mark_the_one_above_it(self):
        self.write("app/legacy_a.gd", gd(CLAMP_ALL, SPARSE.replace("_reset()", "_reset_all()")))
        self.commit("rename")
        result = self.run_tool("--base", "HEAD~1")
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)  # clamp_all is unchanged

    @NEEDS_PARSER
    def test_pair_that_differs_only_in_strings_is_not_reported(self):
        self.assertEqual(self.run_tool("app/daycare_session.gd").stdout, "")
        self.write("app/profile_session.gd", gd(request("daycare")))  # the control: identical strings
        self.commit("profile")
        self.assertEqual(self.run_tool("app/daycare_session.gd").stdout.splitlines(),
                         ["1.000 app/daycare_session.gd:4 _request app/profile_session.gd:4 _request"])

    @NEEDS_PARSER
    def test_threshold_exits_1_when_a_pair_reaches_it(self):
        self.write("app/retry_session.gd", gd(request("daycare", extra="\t_retries[kind] = 0\n")))
        self.commit("retry")
        result = self.run_tool("app/retry_session.gd")
        self.assertEqual(result.stdout.splitlines(),
                         ["0.898 app/retry_session.gd:4 _request app/daycare_session.gd:4 _request"])
        self.assertEqual(self.run_tool("app/retry_session.gd", "--threshold", "0.85").returncode, 1)
        self.assertEqual(self.run_tool("app/retry_session.gd", "--threshold", "0.95").returncode, 0)

    @NEEDS_PARSER
    def test_file_that_does_not_parse_is_named_and_the_run_goes_on(self):
        self.write("app/broken.gd", "extends RefCounted\n\nfunc broken(:\n\tpass\n")
        self.commit("broken")
        result = self.run_tool("--all")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("gd_duplicates: not parsed: app/broken.gd: ", result.stderr)
        self.assertIn("1 file(s) not parsed", result.stderr)
        self.assertIn("app/legacy_a.gd:4 clamp_all", result.stdout)

    @NEEDS_PARSER
    def test_cache_is_reused_and_a_corrupt_entry_is_parsed_again(self):
        first = self.run_tool("--all").stdout
        entries = sorted((self.cache / "ai-kit" / "gd-duplicates").glob("*.json"))
        self.assertEqual(len(entries), 6, entries)  # one per distinct source: the legacy and small pairs share one
        for entry in entries:  # rename every cached function: the next run must print the cached names
            rows = json.loads(entry.read_text())
            entry.write_text(json.dumps([["cached" + row[0], *row[1:]] for row in rows]))
        self.assertIn("cachedclamp_all", self.run_tool("--all").stdout)
        for entry in entries:
            entry.write_text("not json")
        self.assertEqual(self.run_tool("--all").stdout, first)
        for entry in entries:
            json.loads(entry.read_text())  # rewritten whole

    def test_missing_gdtoolkit_fails_open_with_a_notice(self):
        stub = Path(self.tmp.name) / "stub" / "gdtoolkit"
        stub.mkdir(parents=True)
        (stub / "__init__.py").write_text("")
        (stub / "parser.py").write_text('raise ImportError("stub: gdtoolkit is not installed")\n')
        env = {**self.env, "PYTHONPATH": str(stub.parent)}
        result = self.run_tool("--base", self.base, env=env)
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)
        self.assertIn("gdtoolkit not available (pip install gdtoolkit); duplicates not measured for 1 .gd file(s)",
                      result.stderr)
        self.assertEqual(self.run_tool("--base", self.base, "--threshold", "0.9", env=env).returncode, 2)

    def test_no_changed_function_exits_0_and_bad_ref_exits_2(self):
        result = self.run_tool("--base", "HEAD", "--threshold", "0.9")
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)
        self.assertIn("no changed .gd function to compare", result.stderr)
        self.assertEqual(self.run_tool("--base", "no-such-ref").returncode, 2)


if __name__ == "__main__":
    unittest.main()
