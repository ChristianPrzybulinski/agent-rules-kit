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

    def test_a_record_outside_the_history_section_does_not_count(self):
        self.feat("validated", body_line=REVIEWED)
        self.assert_fails("status validated needs the History line sdd-review writes")


if __name__ == "__main__":
    unittest.main()
