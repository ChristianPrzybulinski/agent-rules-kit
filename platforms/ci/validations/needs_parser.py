"""The gdtoolkit switch of the GDScript tool tests (test_gd_coverage.py, test_gd_duplicates.py, test_gd_mutation.py),
kept in one place since KIT-083. A test that parses GDScript skips without gdtoolkit, except under CI=1: the CI jobs
that run it install the pinned gdtoolkit (KIT-082), so there a missing one fails the test, as a missing just or
gitleaks does."""
import functools
import importlib.util
import os
import unittest

HAS_GDTOOLKIT = importlib.util.find_spec("gdtoolkit") is not None


def NEEDS_PARSER(test):  # noqa: N802 (a decorator named like the skip decorators it replaces)
    """Decorates a test method, or a class whose every test then fails in setUp."""
    if HAS_GDTOOLKIT:
        return test
    if not os.environ.get("CI"):
        return unittest.skip("gdtoolkit is not installed (pip install gdtoolkit==4.5.0; CI=1 makes it required)")(test)

    def missing(self, *args, **kwargs):
        self.fail("gdtoolkit is not installed (CI=1 makes it required: pip install gdtoolkit==4.5.0)")
    if isinstance(test, type):  # a class: each of its tests fails in setUp
        test.setUp = missing
        return test
    return functools.wraps(test)(missing)
