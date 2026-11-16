"""pr_gates.py inputs (KIT-075): a PR body splits only on CommonMark line endings (#251), and the gates config is
refused with exit 2 naming the key when a value has the wrong type (#252)."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pr_gates  # noqa: E402

EXTRA_SEPARATORS = ("\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", " ", " ")


class BodyLines(unittest.TestCase):
    def test_only_commonmark_line_endings_start_a_heading(self):
        for sep in EXTRA_SEPARATORS:
            with self.subTest(sep=repr(sep)):
                secs = pr_gates.sections(f"## What\n\nAdds sub.{sep}## Red\nnot a section\n")
                self.assertNotIn("Red", secs)
                self.assertIn(sep, secs["What"])
        for end in ("\n", "\r\n", "\r"):
            with self.subTest(end=repr(end)):
                self.assertEqual(pr_gates.sections(f"## What{end}x{end}## Red{end}y{end}")["Red"], "y")

    def test_a_proof_line_holding_an_extra_separator_stays_one_line(self):
        for sep in EXTRA_SEPARATORS:
            with self.subTest(sep=repr(sep)):
                lines = pr_gates.parse_proof(f"```proof\npython3 a.py{sep}python3 b.py\n```\n")
                self.assertEqual(lines, [f"python3 a.py{sep}python3 b.py"])
        self.assertEqual(pr_gates.parse_proof("```proof\r\npython3 a.py\rpython3 b.py\r\n```"),
                         ["python3 a.py", "python3 b.py"])


GOOD = {"owner": "org", "backlog_repo": "docs", "repos": {"docs": {"require_fragment": True}}}


class ConfigTypes(unittest.TestCase):
    CASES = {  # key: a value of the wrong type that is still iterable or truthy
        "owner": 5,
        "backlog_repo": ["docs"],
        "review_context": 1,
        "repos": ["docs"],
        "protected_paths": {"core": "protected/**"},
        "generated_neighbours": ".uid",
        "proof_allowlist": "python3",
        "proof_script_runners": {"python3": "-m"},
        "proof_var_depths": {"HOME": "1"},
        "expected_red_checks": {"docs": ["ci"]},
        "red": [{"glob": "tests/**", "command": ["true"]}],
    }

    def test_a_valid_config_has_no_error(self):
        full = {**GOOD, "review_context": "org/review", "protected_paths": {"core": ["protected/**"]},
                "generated_neighbours": [".uid"], "proof_allowlist": ["python3"],
                "proof_script_runners": {"python3": ["-m"]}, "proof_var_depths": {"HOME": 1},
                "expected_red_checks": {"docs": {"ci": {"until_issue_closed": 7, "why": "known"}}},
                "red": [{"glob": "tests/**", "command": "python3 -m unittest {tests}", "cwd": "."}]}
        self.assertEqual(pr_gates.config_errors(full, required=pr_gates.REQUIRED_KEYS), [])

    def test_each_key_of_the_wrong_type_is_named(self):
        for key, value in self.CASES.items():
            with self.subTest(key=key):
                errors = pr_gates.config_errors({**GOOD, key: value})
                self.assertEqual(len(errors), 1, errors)
                self.assertTrue(errors[0].startswith(key), errors)

    def test_main_exits_2_naming_the_key(self):
        for config, key in (({**GOOD, "protected_paths": {"core": "protected/**"}}, "protected_paths"),
                            ({"backlog_repo": "docs", "repos": {"docs": {}}}, "owner")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "gates.json"
                path.write_text(json.dumps(config), encoding="utf-8")
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    code = pr_gates.main(["--config", str(path), "--repo", "docs", "--pr", "1"])
                self.assertEqual(code, 2)
                self.assertIn(key, err.getvalue())

    def test_a_config_without_proof_allowlist_exits_2_naming_it(self):
        """#288 item 7 (KIT-079): every task PR's report and `proof-commands` read the key, so its absence is a config
        error up front, not a KeyError mid-report. No GH_TOKEN: the refusal comes before any API call."""
        for mode in ("report", "proof-commands"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp, \
                    mock.patch.dict(os.environ, {"GH_TOKEN": ""}):
                path = Path(tmp) / "gates.json"
                path.write_text(json.dumps(GOOD), encoding="utf-8")
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    code = pr_gates.main([mode, "--config", str(path), "--repo", "docs", "--pr", "1"])
                self.assertEqual(code, 2)
                self.assertIn("proof_allowlist is required", err.getvalue())


if __name__ == "__main__":
    unittest.main()
