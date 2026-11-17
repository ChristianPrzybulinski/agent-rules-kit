"""spec_trace.py and processes (KIT-090): PROC-nnn step checks, the `—` waiting rule through a NEED's `processes`, a
journey step that cites `PROC-nnn` or `PROC-nnn S<a>–S<b>` and its expansion, the Processes and Tasks → processes
views of the matrix, and closure; a spec without processes/ renders the matrix exactly as before."""
import contextlib
import io
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/spec_trace.py",)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec_trace as trace  # noqa: E402
import test_spec_trace as base  # noqa: E402  (the journey fixture of main)

FEAT = """\
---
id: {fid}
title: "Fixture feature {fid}"
status: {status}
requirements: [{reqs}]
created: "2026-11-16"
---

# {fid}

## Tasks

| ID | Task | Files | Status |
|---|---|---|---|
| T1 | first task | `a/**` | done |
| T2 | second task | `b/**` | done |

## Closure

- closed.
"""

REQ = """\
---
id: {rid}
title: "Fixture rule {rid}"
type: functional
priority: must
features: [{feats}]
created: "2026-11-16"
---

# {rid}
"""

PROCESS = """\
---
id: PROC-001
title: "Fixture battle turn"
status: proposed
owner: product
kind: product
created: "2026-11-16"
updated: "2026-11-16"
---

# PROC-001 — Fixture battle turn

## Trigger

- [FACT] the player picks a move.

## States

| State | Entry | Duration | Unit | Experience | Exit |
|---|---|---|---|---|---|
| choose | turn starts | until input | turns | sees the move list | a move is picked |

## Steps

| Step | Action → result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | picks a move → move is locked | REQ-F-001 | FEAT-001 T1 | `game-client/tests/a/**` |
| S2 | turn resolves → damage shows | REQ-F-002 | FEAT-002 T1 | FEAT-002 T2 |
| S3 | turn ends → next turn starts | — | FEAT-001 T2 | FEAT-001 T1 · manual: watch it |

## Alternative paths

| Step | At | Action → result | Rules | Implemented by | Proven by |
|---|---|---|---|---|---|
| A1 | S2 | the move misses → "missed" shows | REQ-F-001 | FEAT-002 T1 | `game-server/src/test/**` |
"""

JOURNEY = """\
---
id: J-01
title: "Fixture journey"
status: proposed
owner: product
created: "2026-11-16"
updated: "2026-11-16"
---

# J-01

| Step | Player action → visible result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | opens the battle → sees the field | REQ-F-001 | FEAT-001 T1 | `game-client/tests/a/**` |
| S2 | fights one turn: {cite} | — | — | — |
"""

NEED = """\
---
id: NEED-001
title: "Fixture need NEED-001"
type: improvement
status: {status}
origin: "owner"
{links}created: "2026-11-16"
---

# NEED-001
"""


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def quiet(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = trace.main(argv)
    return code, out.getvalue(), err.getvalue()


class ProcessCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "game-docs"
        self.spec = self.root / "docs/spec"
        for sibling in ("game-client", "game-server"):
            (self.root.parent / sibling).mkdir(parents=True, exist_ok=True)
        write(self.root, "docs/spec/features/FEAT-001.md",
              FEAT.format(fid="FEAT-001", status="planned", reqs="REQ-F-001"))
        write(self.root, "docs/spec/features/FEAT-002.md",
              FEAT.format(fid="FEAT-002", status="planned", reqs="REQ-F-002"))
        write(self.root, "docs/spec/requirements/functional/REQ-F-001.md", REQ.format(rid="REQ-F-001", feats="FEAT-001"))
        write(self.root, "docs/spec/requirements/functional/REQ-F-002.md", REQ.format(rid="REQ-F-002", feats="FEAT-002"))
        self.process()

    def tearDown(self):
        self.tmp.cleanup()

    def process(self, old=None, new=None, text=PROCESS):
        write(self.root, "docs/spec/processes/PROC-001-battle-turn.md", text if old is None else text.replace(old, new))

    def journey(self, cite="PROC-001"):
        write(self.root, "docs/spec/journeys/J-01.md", JOURNEY.format(cite=cite))

    def need(self, status, links):
        write(self.root, "docs/spec/needs/NEED-001-fixture.md", NEED.format(status=status, links=links))

    def check(self):
        quiet(["generate", str(self.spec)])
        return trace.check(trace.load(self.spec))

    def assert_error(self, errs, *fragments):
        for fragment in fragments:
            self.assertTrue(any(fragment in e for e in errs), f"no error containing {fragment!r} in {errs}")


class ProcessStepTest(ProcessCase):
    def test_valid_process_passes_and_holds_n_feats(self):
        self.assertEqual(self.check(), [])
        process = trace.load(self.spec).processes["PROC-001"]
        self.assertEqual([s.id for s in process["steps"]], ["S1", "S2", "S3", "A1"])
        self.assertEqual(process["kind"], "product")
        feats = {t.split()[0] for s in process["steps"] for t in s.tasks}
        self.assertEqual(feats, {"FEAT-001", "FEAT-002"})

    def test_rules_hold_req_ids_only(self):
        self.process("| S1 | picks a move → move is locked | REQ-F-001 |",
                     "| S1 | picks a move → move is locked | REQ-F-001 (at most 4 moves) |")
        self.assert_error(self.check(), "PROC-001 S1: Rules holds more than ids")

    def test_unknown_rule_fails(self):
        self.process("| REQ-F-002 | FEAT-002 T1 |", "| REQ-F-099 | FEAT-002 T1 |")
        self.assert_error(self.check(), "PROC-001 S2: Rules cites REQ-F-099, which does not exist")

    def test_unknown_task_fails(self):
        self.process("| FEAT-001 T2 | FEAT-001 T1 ·", "| FEAT-001 T9 | FEAT-001 T1 ·")
        self.assert_error(self.check(), "PROC-001 S3: FEAT-001 T9 is not a row of the FEAT-001 task table")

    def test_alternative_must_point_at_a_main_step(self):
        self.process("| A1 | S2 |", "| A1 | S7 |")
        self.assert_error(self.check(), "PROC-001 A1: At='S7' is not a main step (S<n>) of PROC-001")

    def test_frontmatter_kind_status_id_and_file_name(self):
        cases = (("kind: product", "kind: ops", "kind='ops' not in ['product', 'tech']"),
                 ("kind: product\n", "", "required field missing: kind"),
                 ("status: proposed", "status: done", "status='done' not in"),
                 ("id: PROC-001", "id: PROC-002", "id=PROC-002 != file name prefix"),
                 ("id: PROC-001", "id: PROC-1", "id 'PROC-1' does not match PROC-nnn"))
        for old, new, fragment in cases:
            with self.subTest(fragment=fragment):
                self.process(old, new)
                self.assert_error(self.check(), fragment)

    def test_tech_process_passes(self):
        self.process("kind: product", "kind: tech")
        self.assertEqual(self.check(), [])

    def test_process_without_a_main_step_fails(self):
        self.process(text=PROCESS.split("## Steps")[0])
        self.assert_error(self.check(), "PROC-001: no main step (S<n>) found in a Step table")

    def test_a_process_step_cannot_cite_a_process(self):
        self.process("| S3 | turn ends → next turn starts |", "| S3 | PROC-002 |")
        self.assert_error(self.check(), "PROC-001 S3: a process step cannot cite a process (PROC-002)")

    def test_a_process_alone_requires_the_matrix(self):
        self.assertTrue(any("traceability.md is stale or missing" in e
                            for e in trace.check(trace.load(self.spec))))


class WaitingRuleTest(ProcessCase):
    """A process step written in sdd-clarify holds `—` while an open NEED lists the process in `processes`."""

    def setUp(self):
        super().setUp()
        self.process("| REQ-F-002 | FEAT-002 T1 | FEAT-002 T2 |", "| REQ-F-002 | — | — |")

    def test_dash_waits_while_an_open_need_lists_the_process(self):
        for status in ("proposed", "triaged", "specified", "refined"):
            with self.subTest(status=status):
                self.need(status, "processes: [PROC-001]\n")
                self.assertEqual(self.check(), [])

    def test_dash_fails_once_no_open_need_lists_the_process(self):
        self.need("rejected", "processes: [PROC-001]\n")
        self.assert_error(self.check(), "PROC-001 S2: Implemented by cites no task",
                          "PROC-001 S2: Proven by cites no test",
                          "a NEED listing the process is open: no open NEED lists PROC-001")

    def test_a_need_listing_only_journeys_does_not_hold_a_process_step(self):
        self.journey()
        self.need("refined", "journeys: [J-01]\n")
        self.assert_error(self.check(), "PROC-001 S2: Implemented by cites no task")

    def test_without_needs_nothing_waits(self):
        self.assert_error(self.check(), "PROC-001 S2: Implemented by cites no task")


class ManualRunbookTest(ProcessCase):
    """#360 item 2: a `kind: tech` step a person runs, with no FEAT behind it, holds `—` in Implemented by when its
    Proven by is a `manual:` check alone; no open NEED needs to list the process."""

    FILLED = "| REQ-F-002 | FEAT-002 T1 | FEAT-002 T2 |"

    def runbook(self, kind="tech", proven="manual: report pasted in History"):
        self.process(text=PROCESS.replace("kind: product", f"kind: {kind}").replace(
            self.FILLED, f"| REQ-F-002 | — | {proven} |"))

    def test_a_manual_tech_step_holds_a_dash(self):
        self.runbook()
        self.assertEqual(self.check(), [])
        step = next(s for s in trace.load(self.spec).processes["PROC-001"]["steps"] if s.id == "S2")
        self.assertEqual((step.tasks, step.manual), ([], "report pasted in History"))

    def test_a_product_step_still_cites_a_task(self):
        self.runbook(kind="product")
        self.assert_error(self.check(), "PROC-001 S2: Implemented by cites no task")

    def test_a_tech_step_proven_by_a_test_still_cites_a_task(self):
        for proven in ("FEAT-002 T2", "FEAT-002 T2 · manual: watch it", "—"):
            with self.subTest(proven=proven):
                self.runbook(proven=proven)
                self.assert_error(self.check(), "PROC-001 S2: Implemented by cites no task",
                                  "in a `kind: tech` process, `—` with a Proven by of `manual:` alone")

    def test_validate_takes_the_manual_step_as_filled(self):
        self.runbook()
        self.need("refined", "requirements: [REQ-F-002]\nprocesses: [PROC-001]\nfeatures: [FEAT-002]\n")
        code, out, err = quiet(["validate", str(self.spec), "FEAT-002", "--at", "abc1234", "--check"])
        self.assertEqual(code, 0, err)
        self.assertIn("FEAT-002: ready to validate", out)


class ExpansionTest(ProcessCase):
    """A journey step that cites a process holds `—` in its own cells; the process's steps carry them."""

    def expanded(self, cite):
        self.journey(cite)
        self.assertEqual(self.check(), [])
        return trace.load(self.spec).journeys["J-01"]["steps"][1]

    def test_whole_process(self):
        step = self.expanded("PROC-001")
        self.assertEqual([s.ref for s in step.expands], ["PROC-001 S1", "PROC-001 S2", "PROC-001 S3", "PROC-001 A1"])
        self.assertEqual(step.rules, ["REQ-F-001", "REQ-F-002"])
        self.assertEqual(step.tasks, ["FEAT-001 T1", "FEAT-002 T1", "FEAT-001 T2"])
        self.assertEqual(step.manual, "watch it")

    def test_range_takes_its_main_steps_and_their_alternatives(self):
        for cite in ("PROC-001 S2–S3", "PROC-001 S2-S3"):
            with self.subTest(cite=cite):
                step = self.expanded(cite)
                self.assertEqual([s.ref for s in step.expands], ["PROC-001 S2", "PROC-001 S3", "PROC-001 A1"])

    def test_range_of_one_main_step_leaves_out_other_alternatives(self):
        step = self.expanded("PROC-001 S1–S1")
        self.assertEqual([s.ref for s in step.expands], ["PROC-001 S1"])
        self.assertEqual(step.tests, ["`game-client/tests/a/**`"])

    def test_bad_citations_fail(self):
        cases = (("PROC-009", "J-01 S2: cites PROC-009, which does not exist"),
                 ("PROC-001 S2–S7", "J-01 S2: PROC-001 S2–S7: S7 is not a main step of PROC-001"),
                 ("PROC-001 S3–S1", "J-01 S2: PROC-001 S3–S1: the range runs backwards"),
                 ("PROC-001 S2", "J-01 S2: cites 'PROC-001 S2': write PROC-nnn or PROC-nnn S<a>–S<b>"),
                 ("PROC-001 A1–S2", "J-01 S2: cites 'PROC-001 A1–S2': write PROC-nnn or PROC-nnn S<a>–S<b>"),
                 ("PROC-001 and PROC-001", "J-01 S2: cites more than one process"))
        for cite, fragment in cases:
            with self.subTest(cite=cite):
                self.journey(cite)
                self.assert_error(self.check(), fragment)

    def test_a_citing_step_carries_no_links_of_its_own(self):
        write(self.root, "docs/spec/journeys/J-01.md",
              JOURNEY.format(cite="PROC-001").replace("PROC-001 | — | — | — |",
                                                       "PROC-001 | REQ-F-001 | FEAT-001 T1 | — |"))
        self.assert_error(self.check(), "J-01 S2: a step that cites PROC-001 holds `—` in Rules, Implemented by "
                                        "and Proven by")

    def test_a_prerequisite_cannot_cite_a_process(self):
        write(self.root, "docs/spec/journeys/J-01.md", JOURNEY.format(cite="x") + textwrap.dedent("""
            | Step | What the steps need | Implemented by |
            |---|---|---|
            | P1 | PROC-001 | FEAT-001 T1 |
            """))
        self.assert_error(self.check(), "J-01 P1: a prerequisite cannot cite a process")

    def test_matrix_lists_the_journey_step_under_the_process_tasks_and_rules(self):
        self.journey("PROC-001 S2–S3")
        quiet(["generate", str(self.spec)])
        matrix = (self.spec / "traceability.md").read_text(encoding="utf-8")
        self.assertIn("| FEAT-002 T1 | J-01 S2 |", matrix)
        self.assertIn("| [REQ-F-002](requirements/functional/REQ-F-002.md) | Fixture rule REQ-F-002 | FEAT-002 | "
                      "J-01 S2 | FEAT-001 T1, FEAT-002 T2, `game-server/src/test/**`, manual |", matrix)


class MatrixTest(ProcessCase):
    def test_processes_and_tasks_to_processes_views(self):
        self.journey("PROC-001 S2–S3")
        quiet(["generate", str(self.spec)])
        matrix = (self.spec / "traceability.md").read_text(encoding="utf-8")
        self.assertIn("## Processes\n", matrix)
        self.assertIn("| Process | Title | Kind | Status | Main steps | Alternative steps | Rules cited | "
                      "Cited by |", matrix)
        self.assertIn("| [PROC-001](processes/PROC-001-battle-turn.md) | Fixture battle turn | product | proposed | "
                      "3 | 1 | 2 | J-01 S2 |", matrix)
        tasks = matrix.split("## Tasks → processes")[1]
        self.assertIn("| FEAT-001 T1 | PROC-001 S1, PROC-001 S3 |", tasks)
        self.assertIn("| FEAT-001 T2 | PROC-001 S3 |", tasks)
        self.assertIn("| FEAT-002 T1 | PROC-001 S2, PROC-001 A1 |", tasks)
        self.assertIn("| FEAT-002 T2 | PROC-001 S2 |", tasks)
        rules = matrix.split("## Rules → processes → tests")[1].split("## ")[0]
        self.assertIn("| [REQ-F-001](requirements/functional/REQ-F-001.md) | Fixture rule REQ-F-001 | FEAT-001 | "
                      "PROC-001 S1, PROC-001 A1 | `game-client/tests/a/**`, `game-server/src/test/**` |", rules)
        self.assertEqual(quiet(["check", str(self.spec)])[0], 0)

    def test_a_process_edit_makes_the_matrix_stale(self):
        quiet(["generate", str(self.spec)])
        self.process("| S3 | turn ends → next turn starts | — |", "| S3 | turn ends → next turn starts | REQ-F-002 |")
        self.assertTrue(any("traceability.md is stale" in e for e in trace.check(trace.load(self.spec))))

    def test_a_spec_without_processes_renders_the_matrix_of_main(self):
        shutil_root = Path(self.tmp.name) / "plain" / "game-docs"
        for sibling in ("game-client", "game-server"):
            (shutil_root.parent / sibling).mkdir(parents=True, exist_ok=True)
        base.fixture(shutil_root)
        self.assertEqual(trace.render_matrix(trace.load(shutil_root / "docs/spec")), MAIN_MATRIX)


class ClosureTest(ProcessCase):
    def setUp(self):
        super().setUp()
        self.process("| REQ-F-002 | FEAT-002 T1 | FEAT-002 T2 |", "| REQ-F-002 | — | — |")

    def test_validate_names_the_unfilled_process_step_of_a_listed_process(self):
        self.need("refined", "requirements: [REQ-F-002]\nprocesses: [PROC-001]\nfeatures: [FEAT-002]\n")
        code, _, err = quiet(["validate", str(self.spec), "FEAT-002", "--at", "abc1234", "--check"])
        self.assertEqual(code, 1)
        self.assertIn("PROC-001 S2: Implemented by and Proven by still `—`; NEED-001, which lists FEAT-002, lists "
                      "PROC-001", err)

    def test_validate_reaches_a_process_step_through_a_citing_journey(self):
        self.journey("PROC-001 S2–S3")
        self.need("refined", "requirements: [REQ-F-002]\njourneys: [J-01]\nprocesses: [PROC-001]\n"
                             "features: [FEAT-002]\n")
        code, _, err = quiet(["validate", str(self.spec), "FEAT-002", "--at", "abc1234", "--check"])
        self.assertEqual(code, 1)
        self.assertIn("PROC-001 S2: Implemented by and Proven by still `—`; NEED-001, which lists FEAT-002, lists "
                      "J-01 (J-01 S2 cites it)", err)

    def test_a_listed_process_without_a_file_is_a_gap(self):
        self.need("refined", "requirements: [REQ-F-002]\nprocesses: [PROC-007]\nfeatures: [FEAT-002]\n")
        code, _, err = quiet(["validate", str(self.spec), "FEAT-002", "--at", "abc1234", "--check"])
        self.assertEqual(code, 1)
        self.assertIn("NEED-001 lists PROC-007, which has no process file", err)

    def test_filled_steps_validate(self):
        self.process(text=PROCESS)
        self.need("refined", "requirements: [REQ-F-002]\nprocesses: [PROC-001]\nfeatures: [FEAT-002]\n")
        code, out, err = quiet(["validate", str(self.spec), "FEAT-002", "--at", "abc1234", "--check"])
        self.assertEqual(code, 0, err)
        self.assertIn("FEAT-002: ready to validate", out)



class ChecklistTest(ProcessCase):
    """KIT-092: the owner checklist walks a citing step's process steps, so sdd-release smokes each one."""

    def checklist(self, cite):
        write(self.root, "docs/spec/journeys/J-01.md",
              JOURNEY.format(cite=cite).replace("status: proposed", "status: approved"))
        self.assertEqual(self.check(), [])
        code, out, err = quiet(["checklist", str(self.spec), "J-01"])
        self.assertEqual(code, 0, err)
        return out

    def test_a_citing_step_lists_each_cited_step_with_its_own_proof(self):
        out = self.checklist("PROC-001 S2–S3")
        self.assertIn("| S2 | — | fights one turn: PROC-001 S2–S3 | — | — | — | — |", out)
        self.assertIn("| S2 › PROC-001 S2 | — | turn resolves → damage shows | REQ-F-002 — Fixture rule REQ-F-002 | "
                      "FEAT-002 T2 | — |  |", out)
        self.assertIn("| S2 › PROC-001 S3 | — | turn ends → next turn starts | — | FEAT-001 T1 | watch it |  |", out)
        self.assertIn('| S2 › PROC-001 A1 | PROC-001 S2 | the move misses → "missed" shows | '
                      "REQ-F-001 — Fixture rule REQ-F-001 | `game-server/src/test/**` | — |  |", out)
        self.assertNotIn("PROC-001 S1 |", out)

    def test_a_whole_process_lists_every_step_and_a_plain_step_renders_as_before(self):
        out = self.checklist("PROC-001")
        self.assertIn("| S1 | — | opens the battle → sees the field | REQ-F-001 — Fixture rule REQ-F-001 | "
                      "`game-client/tests/a/**` | — |  |", out)
        self.assertEqual(out.count("| S2 › PROC-001 "), 4)

    def test_an_error_of_the_cited_process_fails_before_writing(self):
        write(self.root, "docs/spec/journeys/J-01.md",
              JOURNEY.format(cite="PROC-001").replace("status: proposed", "status: approved"))
        self.process("| REQ-F-002 | FEAT-002 T1 |", "| REQ-F-009 | FEAT-002 T1 |")
        quiet(["generate", str(self.spec)])
        code, out, err = quiet(["checklist", str(self.spec), "J-01"])
        self.assertEqual((code, out), (1, ""))
        self.assertIn("PROC-001 S2: Rules cites REQ-F-009, which does not exist", err)

    def test_an_unknown_cited_process_fails_before_writing(self):
        write(self.root, "docs/spec/journeys/J-01.md",
              JOURNEY.format(cite="PROC-009").replace("status: proposed", "status: approved"))
        code, out, err = quiet(["checklist", str(self.spec), "J-01"])
        self.assertEqual((code, out), (1, ""))
        self.assertIn("J-01 S2: cites PROC-009, which does not exist", err)


MAIN_MATRIX = """\
# Traceability matrix

Generated by `spec_trace.py generate` from the FEAT, REQ and journey files.
Never edit it by hand: `spec_trace.py check` fails when it is stale. These are reverse views
only — the links are written once, in the journeys (journey → rule, task, test) and in FEAT/REQ
frontmatter.

## Journeys

| Journey | Title | Status | Main steps | Alternative steps | Prerequisites | Rules cited |
|---|---|---|---|---|---|---|
| [J-01](journeys/J-01.md) | Fixture journey | proposed | 2 | 1 | 1 | 1 |

## Rules → journeys → tests

One row per REQ. `—` in Journey steps: no journey proves the rule yet.

| Rule | Title | FEATs | Journey steps | Tests at those steps |
|---|---|---|---|---|
| [REQ-F-001](requirements/functional/REQ-F-001.md) | Fixture rule REQ-F-001 | FEAT-001 | J-01 S1, J-01 A1 | \
`game-client/tests/a/**`, `game-server/src/test/**` |

## Tasks → journeys

Every task a journey cites, in `Implemented by` or as a test task in `Proven by`.

| Task | Journey steps |
|---|---|
| FEAT-001 T1 | J-01 S1, J-01 S2, J-01 A1 |
| FEAT-001 T2 | J-01 S2, J-01 P1 |
"""  # rendered by origin/main 6c43439 on base.fixture()


if __name__ == "__main__":
    unittest.main()
