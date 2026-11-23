"""spec_trace.py validate and deliver (KIT-069): the only writers of FEAT `validated` and `delivered`.

`validate` is sdd-review's: every task row done, a `## Closure` record written, and every step of a journey that a NEED
listing the FEAT names cites its tasks and tests; it moves the FEAT to `validated`, or straight to `delivered` under
`release: merge` (the default). `deliver` is sdd-release's: `validated` to `delivered`. A FEAT reaching `delivered`
moves each NEED whose listed FEATs are now all delivered to `delivered` too."""
import contextlib
import io
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/spec_trace.py", "platforms/ci/validations/check_spec.py", "platforms/ci/schemas/**")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec_trace as trace  # noqa: E402
from test_profile import write_spec  # noqa: E402  (a fixture's sdd: block goes to .ai-kit.yaml, KIT-087 P4)

SPEC_INDEX = """\
---
project: "Fixture"
version: "0.1.0"
updated: "2026-11-14"
{sdd}---

# Spec
"""

FEAT = """\
---
id: {fid}
title: "Fixture feature {fid}"
status: {status}
requirements: [{reqs}]
created: "2026-11-01"
updated: "2026-11-01"
---

# {fid}

## Tasks

| ID | Task | Files | Status |
|---|---|---|---|
| T1 | first | `a/**` | {t1} |
| T2 | second | `b/**` | {t2} |

## Closure

{closure}

## History

- 2026-11-01 plan: created from NEED-001.
"""

REQ = """\
---
id: {rid}
title: "Fixture rule {rid}"
type: functional
status: approved
priority: must
features: [{feats}]
created: "2026-11-01"
---

# {rid}
"""

NEED = """\
---
id: {nid}
title: "Fixture need {nid}"
type: improvement
status: refined
origin: "owner"
requirements: [{reqs}]
journeys: [J-01]
features: [{feats}]
created: "2026-11-01"
updated: "2026-11-01"
---

# {nid}

## History

- 2026-11-01 intake: recorded.
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
| S1 | opens | REQ-F-001 | FEAT-001 T1 | FEAT-001 T2 |
| S2 | confirms | — | {s2_tasks} | {s2_tests} |
"""

CLOSURE = """\
Main: 1a2b3c4 · 2026-11-14 · outcome validated

| Check | Command or measurement | Result |
|---|---|---|
| Lint | `lint` | 0 findings |
"""


def write(root, rel, text):
    if str(rel).endswith("spec/spec.md"):  # its sdd: block goes to .ai-kit.yaml (KIT-087 P4)
        return write_spec(root, textwrap.dedent(text), rel)
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


class ClosureShapeTest(unittest.TestCase):
    LAYER = "unit"

    def test_placeholder_after_a_code_span_pipe_is_not_measured(self) -> None:
        for result in ("`a|b` TBD", "``a`|b`` TBD", r"`a\|b` TBD"):
            with self.subTest(result=result):
                gaps = trace.closure_shape_gaps("FEAT-001", CLOSURE.replace("0 findings", result))
                self.assertEqual(gaps, ["FEAT-001 closure has no check row with a measured Result: "
                                        "sdd-review writes it before validate"])

    def test_only_the_check_table_can_supply_a_measured_row(self) -> None:
        retro = "| Number | Counts | Command or source |\n|---|---|---|\n| Review rounds | 2 | PR history |\n"
        outcome = CLOSURE.split("\n\n", 1)[0] + "\n\n"
        empty_check = CLOSURE.replace("| Lint | `lint` | 0 findings |\n", "")
        for body in (outcome + retro, empty_check + "\n" + retro,
                     empty_check + "\n| Lint | `lint` | 0 findings |\n",
                     CLOSURE.replace("Command or measurement", "Command")):
            with self.subTest(body=body):
                self.assertEqual(trace.closure_shape_gaps("FEAT-001", body), [
                    "FEAT-001 closure has no check row with a measured Result: sdd-review writes it before validate"])

    def test_any_not_run_result_blocks_only_validated(self) -> None:
        not_run = "| Hml | smoke | not run: no hml |\n"
        for outcome in ("validated", "delivered (release: merge)", "returned: hml check pending"):
            for rows in (not_run, not_run + "| Lint | `lint` | 0 findings |\n",
                         "| Lint | `lint` | 0 findings |\n" + not_run):
                with self.subTest(outcome=outcome, rows=rows):
                    body = CLOSURE.replace("validated", outcome).replace("| Lint | `lint` | 0 findings |\n", rows)
                    expected = ["FEAT-001 closure: `not run` blocks validated (closure-record.md)"] if outcome == "validated" else []
                    self.assertEqual(trace.closure_shape_gaps("FEAT-001", body), expected)

    def test_check_header_is_case_insensitive_and_trimmed(self) -> None:
        body = CLOSURE.replace("| Check | Command or measurement | Result |", "|  CHECK  | command or Measurement | result |")
        self.assertEqual(trace.closure_shape_gaps("FEAT-001", body), [])

    def test_pipes_in_check_cells_do_not_shift_the_result(self) -> None:
        for command in ("`a|b`", "``a`|b``", r"a\|b"):
            with self.subTest(command=command):
                body = CLOSURE.replace("`lint`", command)
                self.assertEqual(trace.closure_shape_gaps("FEAT-001", body), [])
                self.assertEqual(trace.row_cells(f"| Lint | {command} | 0 findings |"),
                                 ["Lint", command, "0 findings"])


class ClosureCommandTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "game-docs"
        self.spec = self.root / "docs/spec"
        self.fixture()

    def tearDown(self):
        self.tmp.cleanup()

    def fixture(self, release=None, status="in-progress", t2="done", closure=CLOSURE, s2_tasks="FEAT-001 T2",
                s2_tests="manual: look at it", need_feats="FEAT-001"):
        sdd = f"sdd:\n  release: {release}\n" if release else ""
        write(self.root, "docs/spec/spec.md", SPEC_INDEX.format(sdd=sdd))
        write(self.root, "docs/spec/features/FEAT-001.md",
              FEAT.format(fid="FEAT-001", status=status, reqs="REQ-F-001", t1="done", t2=t2, closure=closure))
        write(self.root, "docs/spec/features/FEAT-002.md",
              FEAT.format(fid="FEAT-002", status="in-progress", reqs="REQ-F-002", t1="done", t2="todo", closure=""))
        write(self.root, "docs/spec/requirements/functional/REQ-F-001.md", REQ.format(rid="REQ-F-001", feats="FEAT-001"))
        write(self.root, "docs/spec/requirements/functional/REQ-F-002.md", REQ.format(rid="REQ-F-002", feats="FEAT-002"))
        reqs = "REQ-F-001, REQ-F-002" if "FEAT-002" in need_feats else "REQ-F-001"
        write(self.root, "docs/spec/needs/NEED-001.md", NEED.format(nid="NEED-001", reqs=reqs, feats=need_feats))
        write(self.root, "docs/spec/journeys/J-01.md", JOURNEY.format(s2_tasks=s2_tasks, s2_tests=s2_tests))

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = trace.main(["--date", "2026-11-14", *argv])
        return code, out.getvalue() + err.getvalue()

    def feat_text(self, fid="FEAT-001"):
        return (self.spec / f"features/{fid}.md").read_text(encoding="utf-8")

    def need_text(self):
        return (self.spec / "needs/NEED-001.md").read_text(encoding="utf-8")

    def validate(self, *extra):
        return self.run_main("validate", str(self.spec), "FEAT-001", "--at", "1a2b3c4", *extra)

    def test_validate_under_release_manual_sets_validated(self):
        self.fixture(release="manual")
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn("status: validated\n", self.feat_text())
        self.assertIn('updated: "2026-11-14"', self.feat_text())
        self.assertIn("- 2026-11-14 sdd-review: validated at 1a2b3c4\n", self.feat_text())
        self.assertIn("status: refined\n", self.need_text())

    def test_sync_index_preserves_code_span_and_escaped_pipes(self) -> None:
        for title in ("`a|b`", "``a`|b``", r"a\|b"):
            with self.subTest(title=title):
                index = (SPEC_INDEX.format(sdd="") + "\n| Feature | Title | Status |\n|---|---|---|\n"
                         f"| [FEAT-001](features/FEAT-001.md) | {title} | proposed |\n")
                write(self.root, "docs/spec/spec.md", index)
                self.assertTrue(trace.sync_index(trace.load(self.spec), "2026-11-14"))
                self.assertEqual((self.spec / "spec.md").read_text(encoding="utf-8"),
                                 index.replace("| proposed |", "| in-progress |"))

    def test_validate_under_release_merge_delivers_the_feat_and_its_need(self):
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn("status: delivered\n", self.feat_text())
        self.assertIn("- 2026-11-14 sdd-review: delivered at 1a2b3c4 (release: merge)\n", self.feat_text())
        self.assertIn("status: delivered\n", self.need_text())
        self.assertIn("- 2026-11-14 sdd-review: delivered (FEAT-001)\n", self.need_text())

    def test_validate_refuses_a_row_not_done(self):
        self.fixture(t2="todo")
        before = self.feat_text()
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("FEAT-001 T2 is todo", out)
        self.assertEqual(self.feat_text(), before)

    def test_validate_accepts_a_superseded_row(self):
        self.fixture(release="manual", t2="superseded")
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn("status: validated\n", self.feat_text())

    def test_validate_accepts_a_cancelled_row(self):
        self.fixture(release="manual", t2="cancelled")
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn("status: validated\n", self.feat_text())

    def test_validate_check_accepts_a_cancelled_row(self):
        self.fixture(release="manual", t2="cancelled")
        code, out = self.validate("--check")
        self.assertEqual(code, 0, out)
        self.assertNotIn("T2 is cancelled", out)

    def test_validate_adds_the_missing_history_line_to_a_feat_already_validated(self):
        self.fixture(release="manual", status="validated")
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn("- 2026-11-14 sdd-review: validated at 1a2b3c4", self.feat_text())

    def test_validate_refuses_a_feat_already_validated_with_an_open_row(self):
        self.fixture(release="manual", status="validated", t2="todo")
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("FEAT-001 T2 is todo", out)
        self.assertNotIn("sdd-review: validated", self.feat_text())

    def test_validate_on_a_validated_feat_with_its_line_changes_nothing(self):
        self.fixture(release="manual")
        self.validate()
        before = self.feat_text()
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn("already validated", out)
        self.assertEqual(self.feat_text(), before)

    def test_validate_refuses_without_a_closure_record(self):
        self.fixture(closure="<!-- sdd-review writes the closure record here -->")
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("## Closure", out)

    def test_validate_refuses_a_placeholder_closure(self):
        for closure in ("TBD", "[FACT] Pending completion and review of the moved rows."):
            with self.subTest(closure=closure):
                self.fixture(closure=closure)
                code, out = self.validate("--check")
                self.assertEqual(code, 1, out)
                self.assertIn("FEAT-001 closure has no outcome line (Main: <sha> · <date> · … · outcome …): "
                              "sdd-review writes it before validate", out)
                self.assertIn("FEAT-001 closure has no check row with a measured Result: "
                              "sdd-review writes it before validate", out)

    def test_validate_refuses_an_outcome_without_a_measured_check(self):
        outcome = "Main: 1a2b3c4 · 2026-11-14 · outcome validated"
        header = "\n\n| Check | Command or measurement | Result |\n|---|---|---|\n"
        for table in ("", header, *(header + f"| Lint | `lint` | {result} |\n"
                                    for result in ("", "—", "–", "-", " TBD ", "ToDo", "PENDING", "**TBD**", "_pending_",
                                                   "planned: 0 findings"))):
            with self.subTest(table=table):
                self.fixture(closure=outcome + table)
                code, out = self.validate("--check")
                self.assertEqual(code, 1, out)
                self.assertIn("FEAT-001 closure has no check row with a measured Result: "
                              "sdd-review writes it before validate", out)
                self.assertNotIn("closure has no outcome line", out)

    def test_validate_accepts_the_closure_record_shape_example(self):
        reference = HERE.parents[2] / "plugins/guardrails/skills/sdd-review/references/closure-record.md"
        example = reference.read_text(encoding="utf-8").split("```markdown\n## Closure\n", 1)[1].split("```", 1)[0]
        self.fixture(closure=example)
        code, out = self.validate("--check")
        self.assertEqual(code, 0, out)
        self.assertIn("ready to validate", out)

    def test_validate_does_not_count_a_table_header_as_a_measured_row(self):
        self.fixture(closure="Main: 1a2b3c4 · 2026-11-14 · outcome validated\n\n"
                             "| Check | Command | Result |\n|:---|:---:|---:|\n")
        code, out = self.validate("--check")
        self.assertEqual(code, 1, out)
        self.assertIn("FEAT-001 closure has no check row with a measured Result: "
                      "sdd-review writes it before validate", out)

    def test_validate_accepts_a_fact_tag_and_backticked_full_sha(self):
        self.fixture(closure="[FACT] Main: `3822b437e0123456789012345678901234567890` · 2026-11-21 · "
                             "reviewer provider=codex · outcome delivered (release: merge)\n\n"
                             "| Check | Command or measurement | Result |\n|---|---|---|\n"
                             "| Lint | `lint` | 0 findings |\n")
        code, out = self.validate("--check")
        self.assertEqual(code, 0, out)
        self.assertIn("ready to validate", out)

    def test_validate_accepts_an_outcome_line_wrapped_across_lines(self):
        """The literal FEAT-151 closure of stratics-docs-loop 20bf8cbc75 (lines 173-176): the outcome is on line two."""
        self.fixture(closure="[FACT] Main: `3822b437e0c04d30b4cbb046e016f6e283a063c2` · 2026-11-21 · reviewer provider=codex\n"
                             "session=5061 · outcome delivered (release: merge). T1 was delivered by\n"
                             "[stratics#5004](https://github.com/dev-game-studio/stratics/pull/5004), merge\n"
                             "`ecce9224112ff1288fcd00628890d950dd38986a`.\n\n"
                             "| Check | Command or measurement | Result |\n|---|---|---|\n"
                             "| Spec | `check.sh --spec docs/spec` | 0 findings |\n")
        code, out = self.validate("--check")
        self.assertEqual(code, 0, out)
        self.assertIn("ready to validate", out)

    def test_validate_refuses_an_outcome_word_in_a_later_paragraph(self):
        self.fixture(closure="Main: 1a2b3c4 · 2026-11-14 · reviewer\n\noutcome validated\n\n"
                             "| Check | Command or measurement | Result |\n|---|---|---|\n| Lint | `lint` | pass |\n")
        code, out = self.validate("--check")
        self.assertEqual(code, 1, out)
        self.assertIn("FEAT-001 closure has no outcome line", out)

    def test_not_run_is_a_check_row_for_closure_shape(self):
        for measured in ("", "| Lint | `lint` | 0 findings |\n"):
            with self.subTest(measured=measured):
                self.fixture(closure="Main: 1a2b3c4 · 2026-11-14 · outcome returned: hml check pending\n\n"
                                     "| Check | Command or measurement | Result |\n|---|---|---|\n"
                                     "| Hml | smoke | not run: no hml access |\n" + measured)
                gaps = trace.closure_record_gaps("FEAT-001", trace.load(self.spec).feats["FEAT-001"])
                self.assertEqual(gaps, [])

    def test_validate_ignores_commented_outcome_and_check_rows(self):
        outcome = "Main: 1a2b3c4 · 2026-11-14 · outcome validated"
        table = "| Check | Command or measurement | Result |\n|---|---|---|\n| Lint | `lint` | pass |"
        for closure, gap in ((f"<!-- {outcome} -->\n{table}", "outcome line"),
                             (f"{outcome}\n<!-- {table} -->", "check row with a measured Result")):
            with self.subTest(gap=gap):
                self.fixture(closure=closure)
                code, out = self.validate("--check")
                self.assertEqual(code, 1, out)
                self.assertIn(f"FEAT-001 closure has no {gap}", out)

    def test_validate_refuses_a_journey_step_still_pending(self):
        self.fixture(s2_tasks="—", s2_tests="—")
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("J-01 S2", out)
        self.assertIn("NEED-001", out)

    def test_validate_check_reports_and_writes_nothing(self):
        before = self.feat_text()
        code, out = self.validate("--check")
        self.assertEqual(code, 0, out)
        self.assertIn("ready to validate", out)
        self.assertEqual(self.feat_text(), before)

    def test_validate_refuses_a_feat_already_cancelled(self):
        self.fixture(status="cancelled")
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("cancelled", out)

    def test_deliver_moves_validated_to_delivered(self):
        self.fixture(release="manual", status="validated")
        code, out = self.run_main("deliver", str(self.spec), "FEAT-001", "--in", "v1.4.0")
        self.assertEqual(code, 0, out)
        self.assertIn("status: delivered\n", self.feat_text())
        self.assertIn("- 2026-11-14 sdd-release: delivered in v1.4.0\n", self.feat_text())
        self.assertIn("status: delivered\n", self.need_text())
        self.assertIn("- 2026-11-14 sdd-release: delivered (FEAT-001)\n", self.need_text())

    def test_deliver_leaves_a_need_whose_other_feat_is_open(self):
        self.fixture(release="manual", status="validated", need_feats="FEAT-001, FEAT-002")
        code, out = self.run_main("deliver", str(self.spec), "FEAT-001", "--in", "v1.4.0")
        self.assertEqual(code, 0, out)
        self.assertIn("status: delivered\n", self.feat_text())
        self.assertIn("status: refined\n", self.need_text())

    def test_deliver_refuses_a_feat_sdd_review_has_not_validated(self):
        code, out = self.run_main("deliver", str(self.spec), "FEAT-001", "--in", "v1.4.0")
        self.assertEqual(code, 1, out)
        self.assertIn("sdd-review", out)
        self.assertIn("status: in-progress\n", self.feat_text())

    def test_check_spec_accepts_what_validate_wrote(self):
        self.fixture(release="manual")
        self.assertEqual(self.validate()[0], 0)
        self.assertEqual(self.run_main("deliver", str(self.spec), "FEAT-001", "--in", "v1.4.0")[0], 0)
        result = subprocess.run([sys.executable, str(HERE / "check_spec.py"), str(self.spec),
                                 str(HERE.parent / "schemas")], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
