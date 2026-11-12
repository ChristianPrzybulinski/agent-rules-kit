"""complexity.py: CRAP from a fixture JaCoCo XML and CC from a stub gdradon on a fixture .gd pair, or CRAP when a
fixture gd_coverage.py --json report holds the GDScript function."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent.parent / "tools" / "complexity.py"
JAVA = "src/main/java/com/example/Bank.java"
GD = "scripts/player.gd"

# withdraw: CC 12, fully covered, so CRAP = CC = 12. audit: CC 4, uncovered, CRAP 4^2 + 4 = 20.
# legacy: CC 6, uncovered, CRAP 42, but unchanged. small: CC 2, uncovered, CRAP 6, below target.
# lambda$withdraw$0 sits inside withdraw: CC 3, half covered, CRAP 9 * 0.125 + 3 = 4.1, below target.
# transfer: CC 6, half covered, CRAP 36 * 0.125 + 6 = 10.5 (the cube matters only between 0 and 100 %).
REPORT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!DOCTYPE report PUBLIC "-//JACOCO//DTD Report 1.1//EN" "report.dtd">
<report name="fixture">
  <package name="com/example">
    <class name="com/example/Bank" sourcefilename="Bank.java">
      <method name="withdraw" desc="(I)I" line="5">
        <counter type="INSTRUCTION" missed="0" covered="40"/><counter type="COMPLEXITY" missed="0" covered="12"/>
      </method>
      <method name="lambda$withdraw$0" desc="()V" line="8">
        <counter type="INSTRUCTION" missed="5" covered="5"/><counter type="COMPLEXITY" missed="1" covered="2"/>
      </method>
      <method name="audit" desc="()V" line="20">
        <counter type="INSTRUCTION" missed="30" covered="0"/><counter type="COMPLEXITY" missed="4" covered="0"/>
      </method>
      <method name="transfer" desc="()V" line="25">
        <counter type="INSTRUCTION" missed="10" covered="10"/><counter type="COMPLEXITY" missed="3" covered="3"/>
      </method>
      <method name="legacy" desc="()V" line="30">
        <counter type="INSTRUCTION" missed="50" covered="0"/><counter type="COMPLEXITY" missed="6" covered="0"/>
      </method>
      <method name="small" desc="()V" line="40">
        <counter type="INSTRUCTION" missed="8" covered="0"/><counter type="COMPLEXITY" missed="2" covered="0"/>
      </method>
    </class>
    <class name="com/example/Ledger" sourcefilename="Ledger.java"/>
  </package>
</report>
"""

GD_BASE = "extends Node\n\n\nfunc move(delta: float) -> void:\n\tposition.x += delta\n\n\n" \
          "func legacy_branchy(value: int) -> int:\n\treturn value\n\n\nfunc tiny() -> void:\n\tpass\n"
# gdradon reports wrong line numbers; the tool must join on the names.
GDRADON_OUT = "    F 1:0 move - C (12)\n    F 2:0 legacy_branchy - C (15)\n    F 3:0 tiny - B (10)\n"

CHANGED = [
    f"{JAVA} Bank.audit CRAP 20.0",
    f"{GD} move CC 12",
    f"{JAVA} Bank.withdraw CRAP 12.0",
    f"{JAVA} Bank.transfer CRAP 10.5",
]


class ComplexityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.stub = Path(self.tmp.name) / "stub"
        self.stub.mkdir()
        gdradon = self.stub / "gdradon"
        gdradon.write_text('#!/bin/sh\nshift\nfor f in "$@"; do echo "$f"; printf \'%s\' "$STUB_OUT"; done\n')
        gdradon.chmod(0o755)
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
                    "STUB_OUT": GDRADON_OUT, "PATH": f"{self.stub}{os.pathsep}/usr/bin{os.pathsep}/bin"}
        self.git("init", "-q", "-b", "main", str(self.repo), cwd=self.tmp.name)
        java = [f"// line {n}" for n in range(1, 46)]
        self.write(JAVA, "\n".join(java) + "\n")
        self.write(GD, GD_BASE)
        self.commit("base")
        self.base = self.git("rev-parse", "HEAD").strip()
        for n in (6, 21, 26, 41):  # inside withdraw, audit, transfer and small
            java[n - 1] = f"// changed {n}"
        self.write(JAVA, "\n".join(java) + "\n")
        self.write(GD, GD_BASE.replace("position.x += delta", "position.x += delta * 2").replace("\tpass", "\treturn"))
        self.commit("change")
        self.report = Path(self.tmp.name) / "jacoco.xml"
        self.report.write_text(REPORT)

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

    def run_tool(self, *args, env=None, cwd=None):
        return subprocess.run([sys.executable, "-B", str(TOOL), *args], cwd=cwd or self.repo, env=env or self.env,
                              capture_output=True, text=True, check=False)

    def test_reports_changed_functions_above_target_only(self):
        result = self.run_tool("--base", self.base, "--jacoco", str(self.report))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), CHANGED)
        self.assertIn("4 of 7 measured function(s) above target", result.stderr)

    def test_full_coverage_scores_cc_and_no_coverage_scores_crap(self):
        lines = self.run_tool("--base", self.base, "--jacoco", str(self.report)).stdout.splitlines()
        self.assertIn(f"{JAVA} Bank.withdraw CRAP 12.0", lines)  # 100 % covered: CRAP = CC
        self.assertIn(f"{JAVA} Bank.audit CRAP 20.0", lines)  # 0 % covered: CC^2 + CC
        self.assertIn(f"{JAVA} Bank.transfer CRAP 10.5", lines)  # 50 % covered: CC^2 * 0.5^3 + CC

    def test_file_arguments_measure_every_function(self):
        result = self.run_tool("--jacoco", str(self.report), JAVA, GD)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[:2], [f"{JAVA} Bank.legacy CRAP 42.0", f"{JAVA} Bank.audit CRAP 20.0"])
        self.assertIn(f"{GD} legacy_branchy CC 15", result.stdout)
        self.assertNotIn("tiny", result.stdout)  # CC 10 meets the GDScript target
        self.assertNotIn("small", result.stdout)  # CRAP 6 meets the Java target

    def test_threshold_exits_1_when_a_value_reaches_it(self):
        self.assertEqual(self.run_tool("--base", self.base, "--jacoco", str(self.report), "--threshold", "20").returncode, 1)
        self.assertEqual(self.run_tool("--base", self.base, "--jacoco", str(self.report), "--threshold", "21").returncode, 0)

    def test_missing_report_is_named_and_never_scored_as_zero_coverage(self):
        result = self.run_tool("--base", self.base)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no JaCoCo report at target/site/*/jacoco.xml", result.stderr)
        self.assertEqual(result.stdout.splitlines(), [f"{GD} move CC 12"])
        absent = self.run_tool("--base", self.base, "--jacoco", str(self.report) + ".absent", "--threshold", "99")
        self.assertEqual(absent.returncode, 2)
        self.assertIn("jacoco.xml.absent", absent.stderr)

    def test_function_gdradon_does_not_report_is_not_measured(self):
        result = self.run_tool("--base", self.base, "--jacoco", str(self.report), env={**self.env, "STUB_OUT": ""})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(GD, result.stdout)
        self.assertIn("3 of 5 measured function(s)", result.stderr)  # the three Java findings

    def test_missing_gdradon_fails_open_with_a_notice(self):
        env = {**self.env, "PATH": f"/usr/bin{os.pathsep}/bin"}
        result = self.run_tool("--base", self.base, "--jacoco", str(self.report), env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("gdradon not available (pip install gdtoolkit); skipped for 1 .gd file(s)", result.stderr)
        self.assertNotIn(GD, result.stdout)
        self.assertEqual(self.run_tool("--base", self.base, "--jacoco", str(self.report), "--threshold", "99",
                                       env=env).returncode, 2)

    def test_file_outside_the_report_is_named_and_a_class_without_methods_is_not(self):
        self.write("src/main/java/com/example/Ledger.java", "interface Ledger {}\n")
        self.write("src/main/java/com/example/Audit.java", "class Audit {}\n")
        self.commit("ledger and audit")
        result = self.run_tool("--base", "HEAD~1", "--jacoco", str(self.report))
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)
        self.assertIn("src/main/java/com/example/Audit.java is not in the JaCoCo report", result.stderr)
        self.assertNotIn("Ledger.java is not in", result.stderr)

    def test_test_sources_need_no_report_and_bad_ref_exits_2(self):
        self.write("src/test/java/com/example/BankTest.java", "class BankTest {}\n")
        self.commit("test only")
        head = self.git("rev-parse", "HEAD").strip()
        result = self.run_tool("--base", head + "~1", "--threshold", "1")
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)
        self.assertNotIn("JaCoCo", result.stderr)
        self.assertEqual(self.run_tool("--base", "no-such-ref").returncode, 2)

    def gd_report(self, project, functions, ref=None):
        """A gd_coverage.py --json file holding (repository-relative path, start, covered, total) per function."""
        path = Path(self.tmp.name) / f"gd-coverage-{len(functions)}.json"
        items = [{"path": p, "name": "ignored by the join", "start": s, "end": s + 1,
                  "lines": {"covered": c, "total": n}} for p, s, c, n in functions]
        path.write_text(json.dumps({"tool": "gd_coverage", "version": 1, "ref": ref, "project": project,
                                    "functions": items}))
        return str(path)

    def test_gd_coverage_report_turns_a_gdscript_cc_into_crap(self):
        report = self.gd_report(".", [(GD, 4, 1, 2), (GD, 12, 1, 1)])  # move half covered, tiny fully
        result = self.run_tool("--base", self.base, "--jacoco", str(self.report), "--gd-coverage", report)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"{GD} move CRAP 30.0", result.stdout.splitlines())  # 12^2 * 0.5^3 + 12
        self.assertIn(f"{GD} tiny CRAP 10.0", result.stdout.splitlines())  # covered: CRAP = CC, which CRAP < 10 fails
        self.assertIn("GDScript coverage for 2 of 2 measured function(s); the rest score CC", result.stderr)

    def test_gd_coverage_joins_by_repository_relative_path_and_func_line(self):
        project, inside = GD.split("/", 1)  # gd_coverage.py run in scripts/ still writes paths from the root
        report = self.gd_report(project, [(GD, 4, 0, 1), (GD, 9, 1, 1), (GD, 12, 0, 0)], "0" * 40)
        result = self.run_tool("--gd-coverage", report, inside, cwd=self.repo / project)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [f"{inside} move CRAP 156.0", f"{inside} legacy_branchy CC 15"])
        self.assertIn("GDScript coverage for 1 of 3 measured function(s); the rest score CC", result.stderr)
        self.assertIn(f"measured 000000000000, not HEAD {self.git('rev-parse', 'HEAD')[:12]}", result.stderr)

    def test_unreadable_gd_coverage_report_is_named_and_never_scored_as_zero_coverage(self):
        other = Path(self.tmp.name) / "other.json"
        other.write_text('{"tool": "jacoco"}')
        for report, why in ((str(other) + ".absent", "other.json.absent not read"),
                            (str(other), "not a gd_coverage.py --json version 1 report")):
            result = self.run_tool("--base", self.base, "--jacoco", str(self.report), "--gd-coverage", report)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(why, result.stderr)
            self.assertEqual(result.stdout.splitlines(), CHANGED)
            self.assertEqual(self.run_tool("--base", self.base, "--jacoco", str(self.report), "--gd-coverage",
                                           report, "--threshold", "99").returncode, 2)


if __name__ == "__main__":
    unittest.main()
