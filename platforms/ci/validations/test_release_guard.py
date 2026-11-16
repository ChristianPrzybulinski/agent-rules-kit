"""platforms/tools/release_guard.py (KIT-077): release.yml publishes a release only from a commit where ci-full passed.
The verdict on a commit's ci-full runs, then the guard as release.yml runs it, with a stub gh that serves the runs and
refuses a tag deletion the way the ruleset protect-release-tags does: the guard never asks for one."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git

KIT = Path(__file__).resolve().parents[3]
GUARD = KIT / "platforms" / "tools" / "release_guard.py"
_SPEC = importlib.util.spec_from_file_location("release_guard_under_test", GUARD)
guard = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(guard)
SHA = "a" * 40
# Serves the responses in $STUB_RUNS (a JSON list of run lists), one per `gh api ...runs` call, the last one repeated;
# records every call in $STUB_LOG; refuses any `-X DELETE` as the tag ruleset does, and any call with $STUB_FAIL.
STUB = """#!/usr/bin/env python3
import json, os, sys
with open(os.environ["STUB_LOG"], "a") as log:
    log.write(" ".join(sys.argv[1:]) + "\\n")
if "DELETE" in sys.argv:
    print("HTTP 422: Repository rule violations found: Cannot delete this protected tag", file=sys.stderr)
    sys.exit(1)
if os.environ.get("STUB_FAIL"):
    print("HTTP 502: bad gateway", file=sys.stderr)
    sys.exit(1)
count = sum(1 for line in open(os.environ["STUB_LOG"]))
answers = json.loads(os.environ["STUB_RUNS"])
print(json.dumps(answers[min(count, len(answers)) - 1]))
"""
GREEN = [{"id": 1, "status": "completed", "conclusion": "success"}]
QUEUED = [{"id": 1, "status": "queued", "conclusion": None}]
RED = [{"id": 1, "status": "completed", "conclusion": "failure"}]


class Verdict(unittest.TestCase):
    def test_one_green_run_passes(self):
        self.assertEqual(guard.verdict([{"status": "completed", "conclusion": "failure"},
                                        {"status": "completed", "conclusion": "success"}]), "pass")

    def test_a_run_in_progress_is_waited_for(self):
        for status in ("queued", "in_progress", "waiting"):
            with self.subTest(status=status):
                self.assertEqual(guard.verdict([{"status": "completed", "conclusion": "failure"},
                                                {"status": status, "conclusion": None}]), "wait")

    def test_no_run_yet_is_waited_for(self):  # the tag push can come before the ci-full run is created
        self.assertEqual(guard.verdict([]), "wait")

    def test_completed_runs_none_green_fail(self):
        runs = [{"status": "completed", "conclusion": c} for c in ("failure", "cancelled", "skipped")]
        self.assertEqual(guard.verdict(runs), "fail")


class GuardRun(unittest.TestCase):
    LAYER = "integration"  # starts processes (scripts, git, temp repos)
    COVERS = ("platforms/tools/release_guard.py",)

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        folder = Path(tmp.name)
        (folder / "gh").write_text(STUB.replace("python3", sys.executable, 1), encoding="utf-8")
        (folder / "gh").chmod(0o755)
        self.log = folder / "calls.log"
        self.env = dict(os.environ, PATH=f"{folder}{os.pathsep}{os.environ['PATH']}", STUB_LOG=str(self.log))

    def run_guard(self, answers, **env):
        result = subprocess.run([sys.executable, "-B", str(GUARD), "--repo", "owner/kit", "--sha", SHA, "--tag",
                                 "v13.0.1", "--wait", "0.05", "--poll", "0.2"], capture_output=True, text=True,
                                env={**self.env, "STUB_RUNS": json.dumps(answers), **env}, timeout=60, check=False)
        calls = self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []
        return result, calls

    def assert_tag_kept(self, result, calls):
        self.assertFalse(any("DELETE" in call for call in calls), calls)
        self.assertIn("Tag v13.0.1 stays (the ruleset protect-release-tags forbids deleting it)", result.stdout)
        self.assertIn("no release is published", result.stdout)
        self.assertIn("gh run rerun 4242", result.stdout)

    def test_a_green_ci_full_passes(self):
        result, calls = self.run_guard([GREEN])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(calls, [f"api repos/owner/kit/actions/workflows/ci-full.yml/runs?head_sha={SHA}&per_page=100 "
                                 "--jq [.workflow_runs[] | {id, status, conclusion}]"])

    def test_a_ci_full_not_created_yet_then_queued_is_waited_for(self):
        running = [{"id": 1, "status": "in_progress", "conclusion": None}]
        result, calls = self.run_guard([[], QUEUED, running, GREEN])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(calls), 4)
        self.assertEqual(result.stdout.count(": wait"), 3)

    def test_a_queued_ci_full_that_fails_publishes_nothing_and_keeps_the_tag(self):
        result, calls = self.run_guard([QUEUED, RED], GITHUB_RUN_ID="4242")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(len(calls), 2)
        self.assertIn("::error title=release guard::no green ci-full.yml run on", result.stdout)
        self.assert_tag_kept(result, calls)

    def test_a_wait_that_runs_out_fails_and_keeps_the_tag(self):
        for answers in ([QUEUED], [[]]):
            with self.subTest(runs=answers[0]):
                self.log.unlink(missing_ok=True)
                result, calls = self.run_guard(answers, GITHUB_RUN_ID="4242")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("no completed green ci-full.yml run on", result.stdout)
                self.assert_tag_kept(result, calls)

    def test_a_gh_error_is_no_verdict(self):
        result, calls = self.run_guard([[]], STUB_FAIL="1")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(any("DELETE" in call for call in calls))
        self.assertIn("gh failed (1): HTTP 502", result.stdout)

if __name__ == "__main__":
    unittest.main()
