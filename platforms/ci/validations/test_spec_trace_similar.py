"""spec_trace.py `similar` (KIT-097): the duplicate checks of sdd-check C20-C24. Mechanical findings, which exit 1:
C21 one contract provided by two ENBs, C24 one REQ in two open FEAT blocks (a versioned FEAT's open block, or an open
FEAT without `## Versions`). Candidates for judgment, which keep exit 0: C20 two REQs with the same actor, trigger and
result, the same statement words or the same title words, C22 two processes with the same trigger and a shared actor, C23 two FEATs with the same
use case (actor and goal) or a shared process step. Retired REQs and processes and cancelled FEATs take no part. The
words are compared after a deterministic normalization: casefold, punctuation and claim tags removed, stop words
dropped, order ignored."""
import contextlib
import io
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): load() asks git for the clone root
COVERS = ("platforms/ci/validations/spec_trace.py",)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec_trace as trace  # noqa: E402

REQ = """\
---
id: {rid}
title: "{title}"
type: functional
status: {status}
priority: must
features: []
created: "2026-11-17"
---

# {rid}

## Statement

{statement}

| Value | Meaning | Tunable |
|---|---|---|
| 1 | one | fixed |
"""

PROC = """\
---
id: {pid}
title: "Fixture process {pid}"
status: {status}
owner: product
kind: product
---

# {pid}

## Trigger

- [FACT] {trigger}

## Actors

{actors}

## Steps

| Step | Action → result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | picks → locked | — | — | — |
| S2 | resolves → shown | — | — | — |
| S3 | ends → next | — | — | — |
"""

FEAT = """\
---
id: {fid}
title: "Fixture {fid}"
status: {status}
requirements: [{reqs}]
processes: [{processes}]
created: "2026-11-17"
---

# {fid}

## Scope

- Use case: {use_case}
- REQ-F-001

{versions}"""

VERSIONS = """\
## Versions

### 0.1.0

Status: delivered
Scope: REQ-F-002

#### Tasks

| ID | Task | Files | Status |
|---|---|---|---|
| T1 | first | `a/**` | done |

#### Closure

- closed at abc1234.

### 0.2.0

Status: {status}
Scope: {scope}

#### Tasks

| ID | Task | Files | Status |
|---|---|---|---|
| T2 | second | `b/**` | todo |
"""

ENB = """\
---
id: {eid}
title: "Fixture {eid}"
status: approved
owner: team
providesApis: [{apis}]
consumesApis: []
dependsOn: []
---

# {eid}

## Provided contracts

| Contract | Kind | Accessed at | Schema or file | Version | Consumers |
|---|---|---|---|---|---|
{rows}
"""


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = trace.main(argv)
    return code, out.getvalue(), err.getvalue()


class WordsTest(unittest.TestCase):
    LAYER = "unit"  # in-process: the normalization alone

    def test_case_punctuation_tags_order_and_stop_words_do_not_count(self):
        self.assertEqual(trace.similar_words("[FACT] The Player picks a move!"),
                         trace.similar_words("move, picks: player"))

    def test_a_meaningful_word_counts(self):
        self.assertNotEqual(trace.similar_words("the player picks a move"),
                            trace.similar_words("the player does not pick a move"))

    def test_the_template_statement_splits_into_actor_trigger_and_result(self):
        actor, trigger, result = trace.statement_parts(
            "The system must lock the chosen move, when the player picks a move, for the player.")
        self.assertEqual(actor, trace.similar_words("player"))
        self.assertEqual(trigger, trace.similar_words("player picks move"))
        self.assertEqual(result, trace.similar_words("lock chosen move"))

    def test_a_statement_outside_the_template_has_no_parts(self):
        self.assertIsNone(trace.statement_parts("Moves lock quickly."))


class SimilarCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "game-docs"
        self.spec = self.root / "docs/spec"
        write(self.root, "docs/spec/spec.md", '---\nproject: "fixture"\nversion: "0.1.0"\nupdated: "2026-11-17"\n'
                                              "---\n\n# Fixture\n")

    def tearDown(self):
        self.tmp.cleanup()

    def req(self, rid, title, statement, status="approved"):
        write(self.root, f"docs/spec/requirements/functional/{rid}.md",
              REQ.format(rid=rid, title=title, statement=statement, status=status))

    def proc(self, pid, trigger, actors, status="approved"):
        write(self.root, f"docs/spec/processes/{pid}-fixture.md",
              PROC.format(pid=pid, trigger=trigger, status=status,
                          actors="\n".join(f"- [FACT] {a}" for a in actors)))

    def feat(self, fid, use_case, status="in-progress", reqs="", processes="", block=None):
        versions = VERSIONS.format(status=block[0], scope=block[1]) if block else ""
        write(self.root, f"docs/spec/features/{fid}.md",
              FEAT.format(fid=fid, status=status, reqs=reqs, processes=processes, use_case=use_case,
                          versions=versions))

    def enb(self, eid, *apis):
        rows = "\n".join(f"| {api} | message | websocket | — | 1 | public |" for api in apis)
        write(self.root, f"docs/spec/enablers/{eid}-fixture.md", ENB.format(eid=eid, apis=", ".join(apis), rows=rows))

    def similar(self):
        code, out, err = run(["similar", str(self.spec)])
        return code, out.splitlines(), err


class RequirementTest(SimilarCase):
    def test_same_actor_trigger_and_result_in_other_case_and_punctuation(self):
        self.req("REQ-F-001", "Lock the move", "The system must lock the chosen move, when the player picks a move, "
                                              "for the player.")
        self.req("REQ-F-002", "Picked moves are final", "The System must lock the chosen move when the Player picks "
                                                       "a move, for the Player")
        code, lines, _ = self.similar()
        self.assertEqual(code, 0)
        self.assertIn("C20 candidate: REQ-F-001 ~ REQ-F-002: same actor, trigger and result", lines)

    def test_same_statement_words_outside_the_template(self):
        self.req("REQ-F-001", "Lock the move", "A picked move locks; the turn waits.")
        self.req("REQ-F-002", "Moves are final", "The turn waits, and the picked move locks.")
        _, lines, _ = self.similar()
        self.assertIn("C20 candidate: REQ-F-001 ~ REQ-F-002: same statement words", lines)

    def test_one_line_per_pair_with_the_first_reason(self):
        statement = "The system must lock the move, when picked, for the player."
        self.req("REQ-F-001", "Lock the move", statement)
        self.req("REQ-F-002", "Lock the move", statement)
        _, lines, _ = self.similar()
        self.assertEqual([line for line in lines if line.startswith("C20")],
                         ["C20 candidate: REQ-F-001 ~ REQ-F-002: same actor, trigger and result"])

    def test_same_title_words(self):
        self.req("REQ-F-001", "Fixture rule: move lock", "The system must lock the move, when picked, for the player.")
        self.req("REQ-F-002", "Move lock (fixture rule)", "The system must show the move, when hovered, for the "
                                                          "player.")
        _, lines, _ = self.similar()
        self.assertIn("C20 candidate: REQ-F-001 ~ REQ-F-002: same title words", lines)

    def test_a_retired_req_and_a_different_rule_are_no_candidates(self):
        statement = "The system must lock the move, when picked, for the player."
        self.req("REQ-F-001", "Lock the move", statement)
        self.req("REQ-F-002", "Lock the move", statement, status="retired")
        self.req("REQ-F-003", "Show the damage", "The system must show the damage, when a hit lands, for the player.")
        code, lines, _ = self.similar()
        self.assertEqual(code, 0)
        self.assertFalse([line for line in lines if line.startswith("C20")], lines)


class ProcessTest(SimilarCase):
    def test_same_trigger_and_a_shared_actor(self):
        self.proc("PROC-001", "The player picks a move.", ["the player", "the server"])
        self.proc("PROC-002", "the Player picks a move", ["The player"])
        self.proc("PROC-003", "the player picks a move", ["the player"], status="retired")
        self.proc("PROC-004", "the turn timer ends", ["the server"])
        code, lines, _ = self.similar()
        self.assertEqual(code, 0)
        self.assertIn("C22 candidate: PROC-001 ~ PROC-002: same trigger and actor (player)", lines)
        self.assertFalse([line for line in lines if "PROC-003" in line or "PROC-004" in line], lines)

    def test_same_trigger_with_no_shared_actor_is_no_candidate(self):
        self.proc("PROC-001", "a release is tagged", ["the operator"])
        self.proc("PROC-002", "a release is tagged", ["the release job"])
        _, lines, _ = self.similar()
        self.assertFalse([line for line in lines if line.startswith("C22")], lines)


class FeatureTest(SimilarCase):
    def setUp(self):
        super().setUp()
        self.proc("PROC-001", "the player picks a move", ["the player"])

    def test_same_actor_and_goal(self):
        self.feat("FEAT-001", "the player picks a move.")
        self.feat("FEAT-002", "The Player picks a move")
        self.feat("FEAT-003", "the player picks a move", status="cancelled")
        code, lines, _ = self.similar()
        self.assertEqual(code, 0)
        self.assertIn("C23 candidate: FEAT-001 ~ FEAT-002: same actor and goal", lines)
        self.assertFalse([line for line in lines if "FEAT-003" in line], lines)

    def test_shared_process_steps(self):
        self.feat("FEAT-001", "the player picks a move", processes="PROC-001 S1–S2")
        self.feat("FEAT-002", "the player ends the turn", processes="PROC-001 S2–S3")
        self.feat("FEAT-003", "the server logs the turn", processes="PROC-001 S3")
        _, lines, _ = self.similar()
        self.assertIn("C23 candidate: FEAT-001 ~ FEAT-002: same steps PROC-001 S2", lines)
        self.assertIn("C23 candidate: FEAT-002 ~ FEAT-003: same steps PROC-001 S3", lines)
        self.assertFalse([line for line in lines if "FEAT-001 ~ FEAT-003" in line], lines)


class MechanicalTest(SimilarCase):
    def test_a_contract_provided_by_two_enablers_fails(self):
        self.enb("ENB-001", "battle-wire", "battle-table")
        self.enb("ENB-002", "battle-wire")
        code, lines, _ = self.similar()
        self.assertEqual(code, 1)
        self.assertIn("C21 high: contract battle-wire is provided by ENB-001 and ENB-002", lines)
        self.assertFalse([line for line in lines if "battle-table" in line], lines)

    def test_a_req_in_two_open_blocks_fails(self):
        self.req("REQ-F-001", "Lock the move", "The system must lock the move, when picked, for the player.")
        self.feat("FEAT-001", "the player picks a move", status="planned", reqs="REQ-F-001, REQ-F-002",
                  block=("planned", "REQ-F-001"))
        self.feat("FEAT-002", "the player ends the turn", reqs="REQ-F-001")
        self.feat("FEAT-003", "the server logs the turn", status="delivered", reqs="REQ-F-001")
        code, lines, _ = self.similar()
        self.assertEqual(code, 1)
        self.assertIn("C24 high: REQ-F-001 is in the open blocks FEAT-001 0.2.0 and FEAT-002", lines)
        self.assertFalse([line for line in lines if "FEAT-003" in line], lines)

    def test_a_req_of_a_delivered_block_is_not_open(self):
        self.feat("FEAT-001", "the player picks a move", status="planned", reqs="REQ-F-001, REQ-F-002",
                  block=("planned", "REQ-F-001"))
        self.feat("FEAT-002", "the player ends the turn", reqs="REQ-F-002")
        code, lines, _ = self.similar()
        self.assertEqual(code, 0, lines)
        self.assertFalse([line for line in lines if line.startswith("C24")], lines)

    def test_summary_counts_findings_and_candidates(self):
        self.enb("ENB-001", "battle-wire")
        self.enb("ENB-002", "battle-wire")
        self.feat("FEAT-001", "the player picks a move")
        self.feat("FEAT-002", "the player picks a move")
        _, lines, _ = self.similar()
        self.assertEqual(lines[-1], "similar: 1 finding (C21, C24), 1 candidate (C20, C22, C23); 0 REQs, 0 processes, "
                                    "2 FEATs, 2 ENBs")


class UnchangedTest(SimilarCase):
    def test_a_spec_with_none_of_them_prints_the_summary_only(self):
        code, lines, err = self.similar()
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(lines, ["similar: 0 findings (C21, C24), 0 candidates (C20, C22, C23); 0 REQs, 0 processes, "
                                 "0 FEATs, 0 ENBs"])

    def test_the_kit_fixture_consumer_spec(self):
        code, lines, _ = run(["similar", str(HERE.parent / "fixtures/consumer/docs/spec")])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
