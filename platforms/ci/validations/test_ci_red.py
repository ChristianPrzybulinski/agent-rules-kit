"""platforms/tools/ci_red.py (KIT-077), the red job of ci.yml: the PR body's `## Red` exception line, the job result for
each red verdict, and a push or dispatch that has no pull request to compare."""
import contextlib
import importlib.util
import io
import os
import unittest
from pathlib import Path
from unittest import mock

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git

KIT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location("ci_red_under_test", KIT / "platforms" / "tools" / "ci_red.py")
ci_red = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ci_red)

BODY = "## What\n\nA workflow fix.\n\n## Red\n\n{red}\n\n## Proof\n\nExecutor: x\n"


class RedException(unittest.TestCase):
    def test_the_first_line_of_the_red_section_names_the_exception(self):
        body = BODY.format(red="Exception: workflow text only; no executable behavior changes.")
        self.assertEqual(ci_red.red_exception(body), "Exception: workflow text only; no executable behavior changes.")
        self.assertEqual(ci_red.red_exception(body.replace("\n", "\r\n")),
                         "Exception: workflow text only; no executable behavior changes.")

    def test_no_exception_without_the_section_or_its_opening_word(self):
        for body in (None, "", "## What\n\nx\n", BODY.format(red="test_x fails on base"), "## Red\n\n## Proof\n",
                     BODY.format(red="The Exception: is mid-line"), "### Red\n\nException: a deeper heading\n",
                     "## Redo\n\nException: another section\n"):
            with self.subTest(body=body):
                self.assertIsNone(ci_red.red_exception(body))


class Verdict(unittest.TestCase):
    def test_ok_exempt_and_flag_pass(self):
        self.assertEqual(ci_red.verdict(0, "red: OK — 1 of 1 failing tests are Red on base", None), (0, ""))
        code, note = ci_red.verdict(3, "red: FLAG — the Red is made only of data entries", None)
        self.assertEqual(code, 0)
        self.assertTrue(note.startswith("::warning title=red::"))

    def test_none_passes_only_with_an_exception(self):
        output = "red: NONE — no test file added or changed; the PR's ## Red section must name its exception"
        code, note = ci_red.verdict(1, output, BODY.format(red="Exception: text only"))
        self.assertEqual(code, 0)
        self.assertTrue(note.startswith("::notice title=red::"), note)
        self.assertIn("Exception: text only", note)
        code, note = ci_red.verdict(1, output, BODY.format(red="no test"))
        self.assertEqual(code, 1)
        self.assertTrue(note.startswith("::error title=red::"), note)

    def test_a_finding_or_an_error_fails_even_with_an_exception(self):
        body = BODY.format(red="Exception: text only")
        for code, output in ((1, "red: FAIL\nhead failed (exit 1)"), (2, "red: ERROR — no test ran on base")):
            with self.subTest(code=code):
                self.assertEqual(ci_red.verdict(code, output, body)[0], 1)


class CurrentBody(unittest.TestCase):
    """#294: the body is read when the job runs, so a `## Red` exception added after the push counts on a re-run;
    the event payload, which `gh run rerun` replays unchanged, is only the fallback."""
    PAYLOAD = {"pull_request": {"number": 7, "body": "## Red\n\nnothing yet\n"}}
    ENV = {"GITHUB_REPOSITORY": "o/kit", "GITHUB_API_URL": "https://api.example", "GITHUB_TOKEN": "t0ken"}

    def test_the_body_comes_from_the_api_at_run_time(self):
        seen = []

        def fetch(request, timeout):
            seen.append((request.full_url, request.get_header("Authorization"), timeout))
            return io.BytesIO(b'{"body": "## Red\\n\\nException: manual: a version bump only"}')

        body, note = ci_red.pr_body(self.PAYLOAD, self.ENV, fetch)
        self.assertEqual(ci_red.red_exception(body), "Exception: manual: a version bump only")
        self.assertEqual(note, "")
        self.assertEqual(seen, [("https://api.example/repos/o/kit/pulls/7", "Bearer t0ken", 30)])

    def test_an_api_failure_falls_back_to_the_event_body_with_a_notice(self):
        def fetch(request, timeout):
            raise OSError("network down")

        body, note = ci_red.pr_body(self.PAYLOAD, self.ENV, fetch)
        self.assertEqual(body, "## Red\n\nnothing yet\n")
        self.assertTrue(note.startswith("::notice title=red::"), note)
        self.assertIn("network down", note)
        self.assertNotIn("t0ken", note)

    def test_without_a_repository_or_number_the_event_body_is_used(self):
        body, note = ci_red.pr_body({"pull_request": {"body": "x"}}, {}, None)
        self.assertEqual((body, note), ("x", ""))


class NoPullRequest(unittest.TestCase):
    def test_a_push_or_a_dispatch_has_nothing_to_compare(self):
        for event in ("push", "workflow_dispatch", ""):
            out = io.StringIO()
            with self.subTest(event=event), mock.patch.dict(os.environ, {"GITHUB_EVENT_NAME": event}), \
                    contextlib.redirect_stdout(out):
                self.assertEqual(ci_red.main(), 0)
                self.assertIn("nothing to compare", out.getvalue())


if __name__ == "__main__":
    unittest.main()
