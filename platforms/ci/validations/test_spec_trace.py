"""spec_trace tests: journey link checks, FEAT<->REQ symmetry, matrix staleness and PR impact."""
import contextlib
import io
import os
import subprocess
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

FEAT = """\
---
id: {fid}
title: "Fixture feature {fid}"
status: clarified
requirements: [{reqs}]
created: "2026-10-05"
---

# {fid}

## Tasks

| ID | Task | Files |
|---|---|---|
| T1 | first task | `a/**` |
| T2 | second task | `b/**` |
"""

REQ = """\
---
id: {rid}
title: "Fixture rule {rid}"
type: functional
priority: must
features: [{feats}]
created: "2026-10-05"
---

# {rid}
"""

JOURNEY = """\
---
id: J-01
title: "Fixture journey"
status: proposed
owner: product
created: "2026-10-05"
updated: "2026-10-05"
---

# J-01

| Step | Player action → visible result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | opens | REQ-F-001 | FEAT-001 T1 | `game-client/tests/a/**` |
| S2 | confirms | — | FEAT-001 T2 | FEAT-001 T1 · manual: look at it |

| Step | At | Player action → visible result | Rules | Implemented by | Proven by |
|---|---|---|---|---|---|
| A1 | S1 | fails | REQ-F-001 | FEAT-001 T1 | `game-server/src/test/**` |

| Step | What the steps need | Implemented by |
|---|---|---|
| P1 | contract | FEAT-001 T2 |
"""


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def fixture(root, journey=JOURNEY):
    """root is the spec's clone; clones the journeys point at sit beside it."""
    for sibling in ("game-client", "game-server"):
        (root.parent / sibling).mkdir(exist_ok=True)
    spec = "docs/spec"
    write(root, f"{spec}/features/FEAT-001.md", FEAT.format(fid="FEAT-001", reqs="REQ-F-001"))
    write(root, f"{spec}/features/FEAT-002.md", FEAT.format(fid="FEAT-002", reqs=""))
    write(root, f"{spec}/requirements/functional/REQ-F-001.md",
          REQ.format(rid="REQ-F-001", feats="FEAT-001"))
    write(root, f"{spec}/journeys/J-01.md", journey)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        trace.main(["generate", str(root / spec)])


def errors(root, repos=()):
    return trace.check(trace.load(root / "docs/spec", repos))


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "game-docs"

    def tearDown(self):
        self.tmp.cleanup()

    def with_journey(self, old, new):
        fixture(self.root, JOURNEY.replace(old, new))
        return errors(self.root)

    def assert_error(self, errs, fragment):
        self.assertTrue(any(fragment in e for e in errs), f"no error containing {fragment!r} in {errs}")

    def test_valid_fixture_passes(self):
        fixture(self.root)
        self.assertEqual(errors(self.root), [])
        steps = trace.load(self.root / "docs/spec").journeys["J-01"]["steps"]
        self.assertEqual([s.id for s in steps], ["S1", "S2", "A1", "P1"])
        self.assertEqual(steps[1].tests, ["FEAT-001 T1"])
        self.assertEqual(steps[1].manual, "look at it")

    def test_unknown_rule_fails(self):
        self.assert_error(self.with_journey("| S1 | opens | REQ-F-001 |", "| S1 | opens | REQ-F-099 |"),
                          "Rules cites REQ-F-099, which does not exist")

    def test_task_outside_the_table_fails(self):
        errs = self.with_journey("| FEAT-001 T2 | FEAT-001 T1 ·", "| FEAT-001 T9 | FEAT-001 T1 ·")
        self.assert_error(errs, "FEAT-001 T9 is not a row of the FEAT-001 task table")

    def test_unknown_feat_fails(self):
        errs = self.with_journey("| P1 | contract | FEAT-001 T2 |", "| P1 | contract | FEAT-077 T1 |")
        self.assert_error(errs, "FEAT-077 T1 names FEAT-077, which does not exist")

    def test_rule_value_in_a_rules_cell_fails(self):
        errs = self.with_journey("| S1 | opens | REQ-F-001 |", "| S1 | opens | REQ-F-001 (3–16 chars) |")
        self.assert_error(errs, "Rules holds more than ids")

    def test_free_text_in_implemented_by_fails(self):
        errs = self.with_journey("| P1 | contract | FEAT-001 T2 |", "| P1 | contract | FEAT-001 T2 and docs |")
        self.assert_error(errs, "Implemented by holds more than ids")

    def test_alternative_step_must_point_at_a_main_step(self):
        self.assert_error(self.with_journey("| A1 | S1 |", "| A1 | S7 |"), "At='S7' is not a main step")

    def test_unrooted_test_path_fails(self):
        errs = self.with_journey("`game-server/src/test/**`", "`src/test/**`")
        self.assert_error(errs, "is not rooted at a clone name")

    def test_repo_flag_allows_a_clone_that_is_not_checked_out(self):
        fixture(self.root, JOURNEY.replace("`game-server/src/test/**`", "`game-tools/src/test/**`"))
        errs = errors(self.root)
        self.assert_error(errs, "is not rooted at a clone name")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = trace.main(["--repo", "game-tools", "check", str(self.root / "docs/spec")])
        self.assertEqual(code, 0, err.getvalue())

    def test_own_repo_test_path_must_exist(self):
        errs = self.with_journey("`game-server/src/test/**`", "`game-docs/tools/none/**`")
        self.assert_error(errs, "matches no file in this repository")

    def test_text_outside_test_refs_fails(self):
        errs = self.with_journey("`game-server/src/test/**` |", "`game-server/src/test/**` see T7 |")
        self.assert_error(errs, "Proven by holds text outside test refs")

    def test_main_step_without_tests_fails(self):
        self.assert_error(self.with_journey("| `game-client/tests/a/**` |", "| — |"),
                          "Proven by cites no test")

    def test_duplicate_step_id_fails(self):
        self.assert_error(self.with_journey("| S2 | confirms |", "| S1 | confirms |"),
                          "S1: duplicate step id")

    def test_journey_id_must_match_the_file_name(self):
        self.assert_error(self.with_journey("id: J-01", "id: J-02"), "id=J-02 != file name prefix")

    def test_journey_status_is_an_enum(self):
        self.assert_error(self.with_journey("status: proposed", "status: done"), "status='done' not in")

    def test_journey_requires_an_owner(self):
        self.assert_error(self.with_journey("owner: product\n", ""), "required field missing: owner")

    def test_req_missing_a_feat_that_lists_it_fails(self):
        fixture(self.root)
        req = REQ.format(rid="REQ-F-001", feats="FEAT-002")
        write(self.root, "docs/spec/requirements/functional/REQ-F-001.md", req)
        errs = errors(self.root)
        self.assert_error(errs, "FEAT-001 lists REQ-F-001 in requirements, but REQ-F-001 does not list FEAT-001")
        self.assert_error(errs, "REQ-F-001 lists FEAT-002 in features, but FEAT-002 does not list REQ-F-001")

    def test_stale_matrix_fails(self):
        fixture(self.root)
        journey = JOURNEY.replace("| S2 | confirms | — |", "| S2 | confirms | REQ-F-001 |")
        write(self.root, "docs/spec/journeys/J-01.md", journey)
        self.assert_error(errors(self.root), "traceability.md is stale or missing")


PENDING_REQ = """\
---
id: REQ-F-001
title: "Fixture rule REQ-F-001"
type: functional
status: proposed
priority: must
features: [{feats}]
created: "2026-11-14"
---

# REQ-F-001
"""

PENDING_NEED = """\
---
id: {nid}
title: "Fixture need {nid}"
type: improvement
status: {status}
origin: "owner"
journeys: [{journeys}]
{extra}created: "2026-11-14"
---

# {nid}
"""

PENDING_JOURNEY = JOURNEY.split("| Step |")[0] + """\
| Step | Player action → visible result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | opens the trade → sees both offers | REQ-F-001 | — | — |
"""

AMEND_JOURNEY = JOURNEY.split("| Step |")[0] + """\
| Step | Player action → visible result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | opens the trade → sees both offers | REQ-F-001 | FEAT-001 T1 | FEAT-001 T2 |
| S2 | counters the offer → sees the new total | REQ-F-001 | — | — |
"""

OPEN_NEED = ("proposed", "triaged", "specified", "refined")
SETTLED_NEED = ("delivered", "rejected", "merged", "routed", "parked")


class PendingStepTest(unittest.TestCase):
    """sdd-clarify writes a step before its FEAT and tasks exist: `—` in Implemented by and Proven by passes while an
    open NEED (not delivered, rejected, merged, routed or parked) lists the journey, else main's rule (KIT-066)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "game-docs"
        self.spec = self.root / "docs/spec"
        write(self.root, "docs/spec/journeys/J-01.md", PENDING_JOURNEY)

    def tearDown(self):
        self.tmp.cleanup()

    def req(self, feats=""):
        write(self.root, "docs/spec/requirements/functional/REQ-F-001.md", PENDING_REQ.format(feats=feats))

    def feat(self, status):
        feat = FEAT.format(fid="FEAT-001", reqs="REQ-F-001").replace("status: clarified", f"status: {status}")
        write(self.root, "docs/spec/features/FEAT-001.md", feat)

    def need(self, status, nid="NEED-001", journeys="J-01", extra=""):
        write(self.root, f"docs/spec/needs/{nid}-fixture.md",
              PENDING_NEED.format(nid=nid, status=status, journeys=journeys, extra=extra))

    def journey(self, old, new):
        write(self.root, "docs/spec/journeys/J-01.md", PENDING_JOURNEY.replace(old, new))

    def check(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            trace.main(["generate", str(self.spec)])
        return errors(self.root)

    def assert_errors(self, errs, *fragments):
        for fragment in fragments:
            self.assertTrue(any(fragment in e for e in errs), f"no error containing {fragment!r} in {errs}")

    def test_step_passes_while_an_open_need_lists_the_journey(self):
        self.req()
        for status in OPEN_NEED:
            with self.subTest(status=status):
                self.need(status)
                self.assertEqual(self.check(), [])

    def test_step_fails_once_no_open_need_lists_the_journey(self):
        self.req()
        for status in SETTLED_NEED:
            with self.subTest(status=status):
                self.need(status)
                self.assert_errors(self.check(), "J-01 S1: Implemented by cites no task",
                                   "J-01 S1: Proven by cites no test", "no open NEED lists J-01")
        with self.subTest("an open NEED that lists another journey"):
            self.need("refined", journeys="J-02")
            self.assert_errors(self.check(), "J-01 S1: Implemented by cites no task", "no open NEED lists J-01")

    def test_amended_step_waits_for_its_need_although_an_older_feat_delivered_the_req(self):
        self.req(feats="FEAT-001")
        self.feat("delivered")
        write(self.root, "docs/spec/journeys/J-01.md", AMEND_JOURNEY)
        self.need("refined", nid="NEED-002")
        self.assertEqual(self.check(), [])
        self.need("delivered", nid="NEED-002")
        self.assert_errors(self.check(), "J-01 S2: Implemented by cites no task", "J-01 S2: Proven by cites no test")

    def test_need_whose_feats_delivered_every_req_no_longer_holds_the_wait(self):
        self.req(feats="FEAT-001")
        self.feat("delivered")
        self.need("refined", extra="features: [FEAT-001]\nrequirements: [REQ-F-001]\n")
        self.assert_errors(self.check(), "J-01 S1: Implemented by cites no task", "J-01 S1: Proven by cites no test")

    def test_need_with_a_req_no_delivered_feat_covers_still_holds_the_wait(self):
        self.req(feats="FEAT-001")
        self.feat("delivered")
        self.need("refined", extra="features: [FEAT-001]\nrequirements: [REQ-F-001, REQ-F-002]\n")
        self.assertEqual(self.check(), [])
        self.feat("in-progress")
        self.need("refined", extra="features: [FEAT-001]\nrequirements: [REQ-F-001]\n")
        self.assertEqual(self.check(), [])

    def test_step_without_rules_waits_only_while_a_need_is_open(self):
        self.req()
        self.journey("| REQ-F-001 | — | — |", "| — | — | — |")
        self.need("specified")
        self.assertEqual(self.check(), [])
        self.need("delivered")
        self.assert_errors(self.check(), "J-01 S1: Implemented by cites no task", "J-01 S1: Proven by cites no test")

    def test_project_without_needs_keeps_the_rule_of_main(self):
        self.req()
        errs = self.check()
        self.assertFalse((self.spec / "needs").exists())
        self.assert_errors(errs, "J-01 S1: Implemented by cites no task", "J-01 S1: Proven by cites no test")

    def test_empty_cell_is_not_the_placeholder(self):
        self.req()
        self.need("refined")
        self.journey("| REQ-F-001 | — | — |", "| REQ-F-001 |  |  |")
        self.assert_errors(self.check(), "J-01 S1: Implemented by cites no task", "J-01 S1: Proven by cites no test")

    def test_prerequisite_row_always_cites_a_task(self):
        self.req()
        self.need("refined")
        write(self.root, "docs/spec/journeys/J-01.md", PENDING_JOURNEY + textwrap.dedent("""
            | Step | What the steps need | Implemented by |
            |---|---|---|
            | P1 | contract | — |
            """))
        self.assert_errors(self.check(), "J-01 P1: Implemented by cites no task")

    def test_journey_without_steps_still_fails(self):
        self.req()
        self.need("refined")
        write(self.root, "docs/spec/journeys/J-01.md", PENDING_JOURNEY.split("| Step |")[0])
        self.assert_errors(self.check(), "J-01: no main step (S<n>) found")


class ImpactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "game-docs"
        fixture(self.root)
        self.git("init", "-q", "-b", "main")
        self.commit("base")
        self.base = self.git("rev-parse", "HEAD").strip()

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True, text=True).stdout

    def commit(self, message):
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.test", "commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD").strip()

    def impact(self, head):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            trace.main(["impact", str(self.root / "docs/spec"), self.base, head])
        return out.getvalue()

    def edit(self, rel, old, new):
        path = self.root / rel
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    def test_changed_rule_lists_the_steps_that_cite_it(self):
        self.edit("docs/spec/requirements/functional/REQ-F-001.md", "# REQ-F-001", "# REQ-F-001\n\nNew limit.")
        report = self.impact(self.commit("rule"))
        tests = "`game-client/tests/a/**`, `game-server/src/test/**`"
        self.assertIn(f"| REQ-F-001 edited | J-01 S1, J-01 A1 | {tests} |", report)

    def test_changed_task_row_lists_only_its_steps(self):
        self.edit("docs/spec/features/FEAT-001.md", "| T2 | second task |", "| T2 | second task, narrowed |")
        report = self.impact(self.commit("row"))
        self.assertIn("| FEAT-001 T2 row edited | J-01 S2, J-01 P1 | FEAT-001 T1, manual |", report)
        self.assertNotIn("FEAT-001 T1 row edited", report)
        self.assertNotIn("text outside the task table", report)

    def test_feat_text_outside_the_table_lists_every_step_citing_the_feat(self):
        self.edit("docs/spec/features/FEAT-001.md", "## Tasks", "A new decision line.\n\n## Tasks")
        report = self.impact(self.commit("text"))
        steps = "J-01 S1, J-01 S2, J-01 A1, J-01 P1"
        self.assertIn(f"| FEAT-001 text outside the task table | {steps} |", report)

    def test_change_no_journey_cites_is_reported(self):
        self.edit("docs/spec/features/FEAT-002.md", "| T1 | first task |", "| T1 | first task, changed |")
        report = self.impact(self.commit("uncited"))
        self.assertIn("No journey cites: FEAT-002 T1 row edited", report)

    def test_diff_without_spec_changes(self):
        write(self.root, "README.md", "readme\n")
        self.assertIn("No REQ, FEAT or journey file changed", self.impact(self.commit("readme")))


STATUS_FEAT = """\
---
id: FEAT-001
title: "Fixture feature"
status: {status}
requirements: []
created: "2026-10-05"
updated: "2026-10-05"
---

# FEAT-001

## Acceptance criteria

| ID | Given | When | Then | Test type |
|---|---|---|---|---|
| CA-1 | — | — | works | e2e |

## Tasks

| ID | Task | Files | Status |
|---|---|---|---|
| T1 | first, a \\| pipe | `a/**` | {t1} |
| T2 | second | `b/**` | {t2} |

## History

- 2026-10-05 specify: created.

Not verified: implementation.
"""


class StatusTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "game-docs"
        self.spec = self.root / "docs/spec"
        self.path = self.spec / "features/FEAT-001.md"

    def tearDown(self):
        self.tmp.cleanup()

    def feat(self, status="clarified", t1="todo", t2="todo"):
        write(self.root, "docs/spec/features/FEAT-001.md", STATUS_FEAT.format(status=status, t1=t1, t2=t2))

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = trace.main(["--date", "2026-10-06", *argv])
        return code, out.getvalue(), err.getvalue()

    def text(self):
        return self.path.read_text(encoding="utf-8")

    def test_mark_done_sets_only_the_status_cell_and_appends_history(self):
        self.feat()
        code, out, _ = self.run_main("mark-done", str(self.spec), "FEAT-001", "T1", "--pr", "game-docs#241")
        self.assertEqual((code, out), (0, "FEAT-001 T1 -> done\n"))
        self.assertIn("| T1 | first, a \\| pipe | `a/**` | done |", self.text())
        self.assertIn("| T2 | second | `b/**` | todo |", self.text())
        self.assertIn("- 2026-10-05 specify: created.\n- 2026-10-06 done: T1 (game-docs#241)\n\nNot verified", self.text())

    def test_mark_done_twice_changes_nothing(self):
        self.feat()
        self.run_main("mark-done", str(self.spec), "FEAT-001", "T1")
        once = self.text()
        code, out, _ = self.run_main("mark-done", str(self.spec), "FEAT-001", "T1")
        self.assertEqual((code, out, self.text()), (0, "FEAT-001 T1 is already done\n", once))

    def test_mark_done_unknown_row_exits(self):
        self.feat()
        with self.assertRaises(SystemExit):
            self.run_main("mark-done", str(self.spec), "FEAT-001", "T9")

    def test_mark_done_rejects_a_malformed_pr(self):
        self.feat()
        with self.assertRaises(SystemExit):
            self.run_main("mark-done", str(self.spec), "FEAT-001", "T1", "--pr", "241")

    def test_no_done_row_leaves_the_status_alone(self):
        self.feat(status="clarified")
        self.assertEqual(self.run_main("status", str(self.spec))[0], 0)

    def test_status_fails_when_a_done_row_disagrees_with_the_frontmatter(self):
        self.feat(status="clarified", t1="done")
        code, _, err = self.run_main("status", str(self.spec))
        self.assertEqual(code, 1)
        self.assertIn("FEAT-001: status='clarified' but its task rows imply 'in-progress'", err)

    def test_write_derives_in_progress_and_stops_there_when_every_row_is_done(self):
        """KIT-069: rows imply in-progress at most; validated is sdd-review's, delivered sdd-release's."""
        self.feat(status="clarified", t1="done")
        self.run_main("status", str(self.spec), "--write")
        self.assertIn("status: in-progress\n", self.text())
        self.assertIn('updated: "2026-10-06"', self.text())
        self.assertEqual(self.run_main("status", str(self.spec))[0], 0)
        self.feat(status="in-progress", t1="done", t2="done")
        self.assertEqual(self.run_main("status", str(self.spec))[0], 0)
        self.run_main("status", str(self.spec), "--write")
        self.assertIn("status: in-progress\n", self.text())

    def test_planned_feat_with_every_row_done_derives_in_progress(self):
        self.feat(status="planned", t1="done", t2="done")
        code, _, err = self.run_main("status", str(self.spec))
        self.assertEqual(code, 1)
        self.assertIn("FEAT-001: status='planned' but its task rows imply 'in-progress'", err)

    def test_a_doing_row_moves_a_planned_feat_to_in_progress_with_its_history_line(self):
        """#247: since KIT-068 a row takes `doing`, so work running on a row moves the FEAT, as a done row does."""
        self.feat(status="planned", t1="doing")
        code, _, err = self.run_main("status", str(self.spec))
        self.assertEqual(code, 1)
        self.assertIn("FEAT-001: status='planned' but its task rows imply 'in-progress'", err)
        self.run_main("status", str(self.spec), "--write")
        self.assertIn("status: in-progress\n", self.text())
        self.assertIn("- 2026-10-06 status: planned -> in-progress (T1 doing)", self.text())
        self.assertEqual(self.run_main("status", str(self.spec))[0], 0)

    def test_todo_and_blocked_rows_leave_a_planned_feat_planned(self):
        self.feat(status="planned", t1="todo", t2="blocked")
        self.assertEqual(self.run_main("status", str(self.spec))[0], 0)

    def test_cancelled_feat_is_never_rewritten(self):
        self.feat(status="cancelled", t1="done")
        self.assertEqual(self.run_main("status", str(self.spec))[0], 0)

    def test_validated_or_delivered_feat_is_never_rewritten_by_rows(self):
        for status in ("validated", "delivered"):
            with self.subTest(status=status):
                self.feat(status=status, t1="done", t2="done")
                self.assertEqual(self.run_main("status", str(self.spec))[0], 0)
                self.run_main("status", str(self.spec), "--write")
                self.assertIn(f"status: {status}\n", self.text())

    def test_superseded_row_counts_as_closed(self):
        """A consumer replaces a row by another and marks it superseded; its FEAT can still be closed."""
        for status in ("validated", "delivered"):
            with self.subTest(status=status):
                self.feat(status=status, t1="done", t2="superseded")
                self.assertEqual(self.run_main("status", str(self.spec))[0], 0)

    def test_cancelled_row_counts_as_closed(self):
        """A resync cancels a row whose work left the FEAT (KIT-068 TASK status); its FEAT can still be closed."""
        for status in ("validated", "delivered"):
            with self.subTest(status=status):
                self.feat(status=status, t1="done", t2="cancelled")
                self.assertEqual(self.run_main("status", str(self.spec))[0], 0)

    def test_a_validated_feat_with_a_reopened_row_returns_to_in_progress(self):
        """sdd-release refuses a FEAT and files a new row: status --write moves it back, so sdd-review can run again."""
        self.feat(status="validated", t1="done", t2="todo")
        code, _, err = self.run_main("status", str(self.spec))
        self.assertEqual(code, 1)
        self.assertIn("imply 'in-progress'", err)
        code, out, err = self.run_main("status", str(self.spec), "--write")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("nothing to rewrite", out + err)
        self.assertIn("status: in-progress\n", self.text())
        self.assertIn("- 2026-10-06 status: validated -> in-progress (reopened: T2 todo)", self.text())
        self.assertEqual(self.run_main("status", str(self.spec))[0], 0)

    def test_a_history_line_goes_after_the_last_bullet_s_continuation(self):
        """append_history never splits a multi-line bullet (the calibration's History-split defect)."""
        self.feat(status="validated", t1="done", t2="todo")
        self.path.write_text(self.text().replace("- 2026-10-05 specify: created.",
                                                 "- 2026-10-05 specify: created with the\n  two rows below."))
        self.assertEqual(self.run_main("status", str(self.spec), "--write")[0], 0)
        self.assertIn("created with the\n  two rows below.\n- 2026-10-06 status: validated -> in-progress", self.text())

    def test_validated_or_delivered_feat_with_an_open_row_fails(self):
        for status in ("validated", "delivered"):
            with self.subTest(status=status):
                self.feat(status=status, t1="done", t2="todo")
                code, _, err = self.run_main("status", str(self.spec))
                self.assertEqual(code, 1)
                self.assertIn(f"FEAT-001: status={status!r} but T2 is 'todo'", err)


CORPUS = os.environ.get("SPEC_TRACE_CORPUS")


class CorpusTest(unittest.TestCase):
    """Run against a real spec directory: SPEC_TRACE_CORPUS=<repo>/docs/spec python3 test_spec_trace.py"""

    LAYER = "functional"  # real behaviour on a real project

    @unittest.skipUnless(CORPUS, "SPEC_TRACE_CORPUS is not set")
    def test_corpus_check_and_status_pass(self):
        for command in ("check", "status"):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = trace.main([command, CORPUS])
            self.assertEqual(code, 0, err.getvalue())


if __name__ == "__main__":
    unittest.main()
