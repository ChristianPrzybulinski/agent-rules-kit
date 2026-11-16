"""needs_parser.py (KIT-083): the one CI=1 gdtoolkit switch of the GDScript tool tests, which KIT-082 wrote into
test_gd_coverage.py, test_gd_duplicates.py and test_gd_mutation.py each. A test or class that parses GDScript runs
with gdtoolkit, skips without it, and fails without it under CI=1, where the jobs install the pinned gdtoolkit."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import needs_parser  # noqa: E402

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git


def sample(ran):
    """A test case class built per call, so discovery never collects it."""
    class Sample(unittest.TestCase):
        def test_parses(self):
            ran.append("ran")
    return Sample


class NeedsParserTest(unittest.TestCase):
    def run_sample(self, has_gdtoolkit, ci, on_class):
        """Decorates a sample test (or its class) as an import would under that state, runs it, and returns what ran
        and the result."""
        ran = []
        cls = sample(ran)
        with mock.patch.object(needs_parser, "HAS_GDTOOLKIT", has_gdtoolkit), mock.patch.dict(os.environ):
            os.environ.pop("CI", None)
            if ci:
                os.environ["CI"] = "1"
            if on_class:
                cls = needs_parser.NEEDS_PARSER(cls)
            else:
                cls.test_parses = needs_parser.NEEDS_PARSER(cls.test_parses)
        result = unittest.TestResult()
        cls("test_parses").run(result)
        return ran, result

    def test_with_gdtoolkit_the_test_runs(self):
        for ci in (False, True):
            for on_class in (False, True):
                with self.subTest(ci=ci, on_class=on_class):
                    ran, result = self.run_sample(True, ci, on_class)
                    self.assertEqual(ran, ["ran"])
                    self.assertEqual((result.testsRun, result.failures, result.errors, result.skipped), (1, [], [], []))

    def test_without_gdtoolkit_a_local_run_skips(self):
        for on_class in (False, True):
            with self.subTest(on_class=on_class):
                ran, result = self.run_sample(False, False, on_class)
                self.assertEqual(ran, [])
                self.assertEqual((result.failures, result.errors), ([], []))
                self.assertEqual([reason for _, reason in result.skipped],
                                 ["gdtoolkit is not installed (pip install gdtoolkit==4.5.0; CI=1 makes it required)"])

    def test_without_gdtoolkit_a_ci_run_fails(self):
        for on_class in (False, True):
            with self.subTest(on_class=on_class):
                ran, result = self.run_sample(False, True, on_class)
                self.assertEqual(ran, [])
                self.assertEqual((len(result.failures), result.errors, result.skipped), (1, [], []))
                self.assertIn("AssertionError: gdtoolkit is not installed (CI=1 makes it required: pip install"
                              " gdtoolkit==4.5.0)", result.failures[0][1])


if __name__ == "__main__":
    unittest.main()
