"""spec_trace.py lint (KIT-069 calibration): the mechanical part of sdd-review's closure.

Stale markers on a FEAT that is closing or closed: "Not verified" or an Audit still "Pending", `[PROPOSAL]` in Scope,
`[HYPOTHESIS]` in Open questions or in a done row, "until/once Tn" whose Tn is done, and a Plan row count that differs
from the task table. Traceability: each listed REQ's proving test appears in its row of the trace. The calibration found
16 stale items in 5 of 5 delivered FEATs and a REQ whose trace row listed no test."""
import contextlib
import io
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec_trace as trace  # noqa: E402

FEAT = """\
---
id: FEAT-001
title: "Fixture feature FEAT-001"
status: {status}
requirements: [REQ-F-001]
created: "2026-11-01"
---

# FEAT-001

## Scope

- {scope}

## Open questions

- {question}

## Plan

{plan}

## Tasks

| ID | Task | Files | Status |
|---|---|---|---|
| T1 | first {t1_note} | `a/**` | done |
| T2 | second | `b/**` | {t2} |

## Audit

{audit}

## History

- 2026-11-01 plan: created; held until T2 lands.
{history}
"""

REQ = """\
---
id: REQ-F-001
title: "Fixture rule REQ-F-001"
type: functional
status: approved
priority: must
features: [FEAT-001]
created: "2026-11-01"
---

# REQ-F-001

## Verification

- Proving test: FEAT-001 T1 ({proving}).
- Examples: input `1` → output `2`
"""

JOURNEY = """\
---
id: J-01
title: "Fixture journey"
status: approved
owner: product
created: "2026-11-01"
updated: "2026-11-01"
---

# J-01

| Step | Player action → visible result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | opens | {rules} | FEAT-001 T1 | `game-docs/tests/trade_flow_test.gd` |
"""

CLEAN = dict(status="validated", scope="REQ-F-001, the trade window", question="none open", plan="Two rows, one wave.",
             t1_note="", t2="done", audit="Clean full-scope check on 2026-11-02.", history="",
             proving="`trade_flow_test.gd`", rules="REQ-F-001")


class LintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "game-docs"
        self.spec = self.root / "docs/spec"
        (self.root / "tests").mkdir(parents=True)
        (self.root / "tests/trade_flow_test.gd").write_text("extends GdUnitTestSuite\n")

    def tearDown(self):
        self.tmp.cleanup()

    def fixture(self, **change):
        values = {**CLEAN, **change}
        self.write("features/FEAT-001.md", FEAT.format(**values))
        self.write("requirements/functional/REQ-F-001.md", REQ.format(proving=values["proving"]))
        self.write("journeys/J-01.md", JOURNEY.format(rules=values["rules"]))

    def write(self, rel, text):
        path = self.spec / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text), encoding="utf-8")

    def lint(self, *feat):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = trace.main(["lint", str(self.spec), *feat])
        return code, out.getvalue() + err.getvalue()

    def assert_finding(self, fragment, **change):
        self.fixture(**change)
        code, out = self.lint()
        self.assertEqual(code, 1, out)
        self.assertIn(fragment, out)

    def test_clean_closed_feat_passes(self):
        self.fixture()
        code, out = self.lint()
        self.assertEqual(code, 0, out)
        self.assertIn("spec-trace lint: OK", out)

    def test_not_verified_line_is_stale(self):
        self.assert_finding("'Not verified'", history="- 2026-11-03 sync: done. Not verified: implementation.")

    def test_pending_audit_is_stale(self):
        self.assert_finding("Audit", audit="Pending.")

    def test_proposal_left_in_scope_is_stale(self):
        self.assert_finding("[PROPOSAL] in Scope", scope="[PROPOSAL] a paid haircut at the barber")

    def test_hypothesis_in_open_questions_is_stale(self):
        self.assert_finding("[HYPOTHESIS] in Open questions", question="[HYPOTHESIS] the IT fits the row size")

    def test_history_bullet_split_by_an_inserted_line_is_flagged(self):
        """The calibration's FEAT-097: a sync line landed inside an earlier bullet, splitting it."""
        self.assert_finding("is split by", history=(
            "- 2026-11-04 refine: T1 no longer follows the event with an\n"
            "- 2026-11-08 sync: status derived (T1 todo -> done).\n"
            "  `inventory` push; the contract is unchanged."))

    def test_history_bullet_ending_in_a_colon_split_by_an_inserted_line_is_flagged(self):
        """The calibration's FEAT-084: the split bullet stops at a colon that introduces its continuation."""
        self.assert_finding("is split by", history=(
            "- 2026-10-21 specify + refine (architect; DTEC-065):\n"
            "- 2026-11-08 sync: status derived (T1 todo -> done).\n"
            "  created as `planned` with REQ-F-001 and T1-T2."))

    def test_multi_line_history_bullet_is_not_split(self):
        self.fixture(history=("- 2026-11-04 refine: T1 no longer follows the event with an\n"
                              "  `inventory` push; the contract is unchanged.\n"
                              "- 2026-11-08 sync: status derived (T1 todo -> done)."))
        code, out = self.lint()
        self.assertEqual(code, 0, out)
        self.assertNotIn("split", out)

    def test_hypothesis_in_a_done_row_is_stale(self):
        self.assert_finding("[HYPOTHESIS] in done row T1", t1_note="[HYPOTHESIS] one IT is enough")

    def test_hypothesis_in_an_open_row_is_not_stale(self):
        self.fixture(status="in-progress", t2="todo")
        self.write("features/FEAT-001.md", FEAT.format(**{**CLEAN, "status": "in-progress", "t2": "todo",
                                                            "t1_note": ""}).replace("| second |",
                                                                                    "| second [HYPOTHESIS] x |"))
        code, out = self.lint("FEAT-001")
        self.assertNotIn("[HYPOTHESIS]", out)

    def test_conditional_on_a_done_row_is_stale(self):
        self.assert_finding("'until T2' but T2 is done", plan="Two rows; the screen stays out until T2 lands.")

    def test_conditional_on_an_open_row_is_not_stale(self):
        self.fixture(status="in-progress", t2="todo", plan="Two rows; the screen stays out until T2 lands.")
        code, out = self.lint("FEAT-001")
        self.assertNotIn("until T2", out)

    def test_history_lines_are_not_linted_for_conditionals(self):
        self.fixture()  # History says "held until T2 lands" and T2 is done: history is a record
        code, out = self.lint()
        self.assertEqual(code, 0, out)

    def test_plan_row_count_that_differs_from_the_table_is_stale(self):
        self.assert_finding("Plan says 3 rows, the task table has 2", plan="Three rows in one wave.")

    def test_proving_test_missing_from_the_trace_is_reported(self):
        self.assert_finding("REQ-F-001: proving test HaircutBuyIT is not in its trace row",
                            proving="`HaircutBuyIT`, `trade_flow_test.gd`")

    def test_req_with_no_test_in_the_trace_is_reported(self):
        self.assert_finding("REQ-F-001: its trace row lists no test", rules="—")

    def test_without_a_feat_only_closed_feats_are_linted(self):
        self.fixture(status="in-progress", t2="todo", audit="Pending.")
        code, out = self.lint()
        self.assertEqual(code, 0, out)
        code, out = self.lint("FEAT-001")
        self.assertEqual(code, 1, out)
        self.assertIn("Audit", out)


if __name__ == "__main__":
    unittest.main()
