"""check_spec.py FEAT closure records (KIT-069): `validated` is set only by sdd-review and `delivered` only by
sdd-release, or by sdd-review under `release: merge`. Each step writes its History line through spec_trace.py
validate or deliver, so a FEAT at either status without the line was moved by hand or by old tooling."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

VALIDATIONS = Path(__file__).resolve().parent
CHECK_SPEC = VALIDATIONS / "check_spec.py"
SCHEMAS = VALIDATIONS.parent / "schemas"

FEAT = """---
id: FEAT-001
title: "Fixture feature FEAT-001"
status: {status}
requirements: [REQ-F-001]
created: "2026-10-05"
---

# FEAT-001

## Closure

{body_line}

## History

- 2026-10-05 plan: created from NEED-001.
{history}
"""

REQ = """---
id: REQ-F-001
title: "Fixture requirement REQ-F-001"
type: functional
priority: must
features: [FEAT-001]
created: "2026-10-05"
---

# REQ-F-001
"""

REVIEWED = "- 2026-11-14 sdd-review: validated at 1a2b3c4"
REVIEW_DELIVERED = "- 2026-11-14 sdd-review: delivered at 1a2b3c4 (release: merge)"
RELEASED = "- 2026-11-20 sdd-release: delivered in v1.4.0"
LEGACY = "- 2026-11-14 delivered before sdd-review"


class ClosureRecordTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spec = Path(self.tmp.name)
        (self.spec / "features").mkdir()
        (self.spec / "requirements" / "functional").mkdir(parents=True)
        (self.spec / "requirements" / "functional" / "REQ-F-001.md").write_text(REQ)

    def tearDown(self):
        self.tmp.cleanup()

    def feat(self, status, *history, body_line="Main: 1a2b3c4 · outcome validated"):
        text = FEAT.format(status=status, history="\n".join(history), body_line=body_line)
        (self.spec / "features" / "FEAT-001.md").write_text(text)

    def run_both(self):
        """The full check, then the structural one: python -S hides pyyaml and jsonschema."""
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        return [subprocess.run([sys.executable, *flags, str(CHECK_SPEC), str(self.spec), str(SCHEMAS)],
                               capture_output=True, text=True, check=False, env=env) for flags in ([], ["-S"])]

    def assert_passes(self):
        for result in self.run_both():
            self.assertEqual(result.returncode, 0, result.stderr)

    def assert_fails(self, *messages):
        for result in self.run_both():
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("FAIL:", result.stderr)
            for message in messages:
                self.assertIn(message, result.stderr)

    def test_in_progress_needs_no_record(self):
        self.feat("in-progress")
        self.assert_passes()

    def test_validated_with_the_sdd_review_line_passes(self):
        self.feat("validated", REVIEWED)
        self.assert_passes()

    def test_validated_without_the_sdd_review_line_fails(self):
        self.feat("validated")
        self.assert_fails("status validated needs the History line sdd-review writes", "spec_trace.py validate")

    def test_delivered_by_sdd_release_passes(self):
        self.feat("delivered", REVIEWED, RELEASED)
        self.assert_passes()

    def test_delivered_by_sdd_review_under_release_merge_passes(self):
        self.feat("delivered", REVIEW_DELIVERED)
        self.assert_passes()

    def test_delivered_with_only_the_validation_line_fails(self):
        self.feat("delivered", REVIEWED)
        self.assert_fails("status delivered needs the History line sdd-release writes", "spec_trace.py deliver")

    def test_delivered_without_any_line_fails(self):
        self.feat("delivered")
        self.assert_fails("status delivered needs the History line")

    def test_delivered_before_the_closure_step_carries_the_legacy_line(self):
        self.feat("delivered", LEGACY)
        self.assert_passes()

    def test_a_closure_failure_names_its_rule(self):
        self.feat("validated")
        self.assert_fails("[feature-closure]")

    def test_the_baseline_can_hold_a_closure_finding(self):
        """feature-closure is a registered rule (KIT-068 RULES), so baseline.json may hold an old finding."""
        self.feat("delivered")
        (self.spec / "baseline.json").write_text('{"rules": {"feature-closure": {"FEAT-001": 1}}}\n')
        for result in self.run_both():
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("BASELINE:", result.stdout)
            self.assertIn("[feature-closure]", result.stdout)

    def test_baseline_init_holds_a_legacy_delivered_feat_but_not_a_new_one(self):
        """Adoption: a consumer's FEATs delivered under the old derivation go into baseline.json once."""
        self.feat("delivered")
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        init = subprocess.run([sys.executable, str(CHECK_SPEC), "--baseline-init", str(self.spec), str(SCHEMAS)],
                              capture_output=True, text=True, check=False, env=env)
        self.assertEqual(init.returncode, 0, init.stderr)
        for result in self.run_both():
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("BASELINE:", result.stdout)
            self.assertIn("[feature-closure]", result.stdout)
        (self.spec / "features" / "FEAT-002.md").write_text(
            FEAT.format(status="delivered", history="", body_line="").replace("FEAT-001", "FEAT-002")
            .replace("requirements: [REQ-F-001]", "requirements: []"))
        self.assert_fails("FEAT-002", "status delivered needs the History line")

    def test_a_record_outside_the_history_section_does_not_count(self):
        self.feat("validated", body_line=REVIEWED)
        self.assert_fails("status validated needs the History line sdd-review writes")



class ClosureParityTest(unittest.TestCase):
    """check_spec.py requires the closure line and spec_trace.py reads it to decide what to write: each keeps its own
    copy of the regexes and the History parsing, so both are pinned to the same verdicts on the same fixtures."""
    CASES = (  # (name, status, History lines, body line, the line counts)
        ("validated by sdd-review", "validated", [REVIEWED], "", True),
        ("validated with no line", "validated", [], "", False),
        ("validated with only a delivered line", "validated", [REVIEW_DELIVERED], "", False),
        ("delivered by sdd-release", "delivered", [RELEASED], "", True),
        ("delivered by sdd-review under release: merge", "delivered", [REVIEW_DELIVERED], "", True),
        ("delivered with the legacy line", "delivered", [LEGACY], "", True),
        ("delivered with only the validated line", "delivered", [REVIEWED], "", False),
        ("delivered with no line", "delivered", [], "", False),
        ("an indented line is a continuation, not a record", "validated", ["  " + REVIEWED], "", False),
        ("a longer word is not the status", "validated", [REVIEWED.replace("validated", "validatedly")], "", False),
        ("a record outside History does not count", "validated", [], REVIEWED, False),
        ("a record past a later section does not count", "validated", ["", "## Notes", "", REVIEWED], "", False),
    )

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(VALIDATIONS))
        import check_spec
        import spec_trace
        cls.check_spec, cls.spec_trace = check_spec, spec_trace

    def test_the_two_copies_share_their_patterns(self):
        for name in ("CLOSURE_LINE", "LEGACY_DELIVERED"):
            with self.subTest(pattern=name):
                self.assertEqual(getattr(self.check_spec, name).pattern, getattr(self.spec_trace, name).pattern)
                self.assertEqual(getattr(self.check_spec, name).flags, getattr(self.spec_trace, name).flags)

    def test_both_tools_give_the_same_verdict_on_each_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "FEAT-001.md"
            for name, status, history, body_line, counts in self.CASES:
                with self.subTest(case=name):
                    path.write_text(FEAT.format(status=status, history="\n".join(history), body_line=body_line))
                    self.check_spec.failures.clear()
                    self.check_spec.check_feature_closure(path, status)
                    self.assertEqual(not self.check_spec.failures, counts, "check_spec.py")
                    self.assertEqual(self.spec_trace.has_history_line(path, status), counts, "spec_trace.py")
            self.check_spec.failures.clear()

if __name__ == "__main__":
    unittest.main()
