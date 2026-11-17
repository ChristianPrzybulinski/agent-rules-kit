"""spec_trace.py and the versioned FEAT (KIT-096): status per version block (the last block is the FEAT's status, its
rows alone move it), validate and deliver on the block, the anti-bucket rule in `check` (by process steps, by the REQs
of the block's Scope and by ENBs), the FEAT's `processes` step ranges, block names by the profile's
`release.versioning`, one process holding N FEATs, and `versions`, which lists the blocks and reports sdd-check C17
(a REQ or a row added to a block after it reached `planned`, read from git). A spec without `## Versions` checks and
renders as before (the other spec_trace tests)."""
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
COVERS = ("platforms/ci/validations/spec_trace.py", "platforms/ci/validations/check_spec.py")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec_trace as trace  # noqa: E402

FEAT_1 = """\
---
id: FEAT-001
title: "Fixture use case: pick a move"
status: {status}
requirements: [REQ-F-001, REQ-F-002]
processes: [PROC-001 S1–S2]
{extra}created: "2026-11-17"
---

# FEAT-001

## Versions

### {first}

Status: delivered
Scope: REQ-F-001

#### Tasks

| ID | Task | Files | Status |
|---|---|---|---|
| T1 | first | `a/**` | done |
| T2 | second | `b/**` | done |

#### Closure

- closed at abc1234.

### {second}

Status: {status}
Scope: REQ-F-002

#### Tasks

| ID | Task | Files | Status |
|---|---|---|---|
| T3 | third | `c/**` | {t3} |

#### Closure
{closure}
## History

- 2026-11-16 sdd-review: delivered at abc1234 (release: merge)
"""

FEAT_2 = """\
---
id: FEAT-002
title: "Fixture use case: end the turn"
status: in-progress
requirements: [REQ-F-003]
processes: [PROC-001 S3–S4]
created: "2026-11-17"
---

# FEAT-002

## Tasks

| ID | Task | Files | Status |
|---|---|---|---|
| T1 | first | `d/**` | done |
| T2 | second | `e/**` | doing |
"""

REQ = """\
---
id: {rid}
title: "Fixture rule {rid}"
type: functional
priority: must
features: [{feats}]
created: "2026-11-17"
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
---

# PROC-001

## Steps

| Step | Action → result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | picks a move → move is locked | REQ-F-001 | FEAT-001 T1 | FEAT-001 T2 |
| S2 | turn resolves → damage shows | REQ-F-002 | FEAT-001 T3 | FEAT-001 T3 |
| S3 | turn ends → next turn starts | REQ-F-003 | FEAT-002 T1 | FEAT-002 T2 |
| S4 | next turn starts → move list shows | — | FEAT-002 T2 | FEAT-002 T1 |

## Alternative paths

| Step | At | Action → result | Rules | Implemented by | Proven by |
|---|---|---|---|---|---|
| A1 | S2 | the move misses → "missed" shows | REQ-F-002 | FEAT-001 T3 | FEAT-001 T3 |
"""

GIT = ("-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false")


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


class VersionCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "game-docs"
        self.spec = self.root / "docs/spec"
        self.feat()
        write(self.root, "docs/spec/features/FEAT-002.md", FEAT_2)
        self.req("REQ-F-001", "FEAT-001")
        self.req("REQ-F-002", "FEAT-001")
        self.req("REQ-F-003", "FEAT-002")
        self.process()

    def tearDown(self):
        self.tmp.cleanup()

    def feat(self, status="in-progress", t3="todo", closure="", extra="", first="0.1.0", second="0.2.0",
             old=None, new=None):
        text = FEAT_1.format(status=status, t3=t3, closure=closure, extra=extra, first=first, second=second)
        write(self.root, "docs/spec/features/FEAT-001.md", text if old is None else text.replace(old, new))

    def req(self, rid, feats):
        write(self.root, f"docs/spec/requirements/functional/{rid}.md", REQ.format(rid=rid, feats=feats))

    def process(self, old=None, new=None):
        write(self.root, "docs/spec/processes/PROC-001-battle-turn.md",
              PROCESS if old is None else PROCESS.replace(old, new))

    def text(self, fid="FEAT-001"):
        return (self.spec / "features" / f"{fid}.md").read_text(encoding="utf-8")

    def check(self):
        run(["generate", str(self.spec)])
        return trace.check(trace.load(self.spec))

    def assert_error(self, errs, *fragments):
        for fragment in fragments:
            self.assertTrue(any(fragment in e for e in errs), f"no error containing {fragment!r} in {errs}")


class BlockStatusTest(VersionCase):
    def test_done_rows_of_a_delivered_block_do_not_move_the_open_block(self):
        self.feat(status="planned")
        code, out, err = run(["status", str(self.spec)])
        self.assertNotIn("FEAT-001", err)

    def test_a_started_row_of_the_open_block_moves_it(self):
        self.feat(status="planned", t3="doing")
        code, _, err = run(["status", str(self.spec)])
        self.assertEqual(code, 1)
        self.assertIn("FEAT-001: status='planned' but its task rows imply 'in-progress'", err)

    def test_status_write_moves_the_frontmatter_and_the_block_line(self):
        self.feat(status="planned", t3="doing")
        run(["--date", "2026-11-18", "status", str(self.spec), "--write"])
        text = self.text()
        self.assertIn("status: in-progress", text.split("---")[1])
        self.assertIn("### 0.2.0\n\nStatus: in-progress\n", text)
        self.assertIn("### 0.1.0\n\nStatus: delivered\n", text)
        self.assertIn("- 2026-11-18 status: planned -> in-progress (T3 doing)", text)

    def test_validate_needs_the_block_closure(self):
        self.feat(t3="done")
        code, _, err = run(["validate", str(self.spec), "FEAT-001", "--at", "def5678", "--check"])
        self.assertEqual(code, 1)
        self.assertIn("FEAT-001 0.2.0 has no `#### Closure` record in its version block", err)

    def test_validate_moves_the_block(self):
        self.feat(t3="done", closure="\n- closed at def5678.\n")
        code, out, err = run(["--date", "2026-11-18", "validate", str(self.spec), "FEAT-001", "--at", "def5678"])
        self.assertEqual(code, 0, out + err)
        text = self.text()
        self.assertIn("status: delivered", text.split("---")[1])
        self.assertIn("### 0.2.0\n\nStatus: delivered\n", text)

    def test_deliver_moves_the_block(self):
        write(self.root, "docs/spec/spec.md", '---\nproject: "fixture"\nversion: "0.2.0"\nupdated: "2026-11-17"\n'
                                              "sdd:\n  release: release\n---\n\n# Fixture\n")
        self.feat(t3="done", closure="\n- closed at def5678.\n")
        run(["validate", str(self.spec), "FEAT-001", "--at", "def5678"])
        self.assertIn("### 0.2.0\n\nStatus: validated\n", self.text())
        code, out, err = run(["deliver", str(self.spec), "FEAT-001", "--in", "0.2.0"])
        self.assertEqual(code, 0, out + err)
        self.assertIn("### 0.2.0\n\nStatus: delivered\n", self.text())


class NeedAndLintTest(VersionCase):
    NEED = ('---\nid: NEED-001\ntitle: "Fixture need"\ntype: improvement\nstatus: refined\norigin: "owner"\n'
            'requirements: [REQ-F-002]\nfeatures: [FEAT-001]\ncreated: "2026-11-17"\n---\n\n# NEED-001\n')

    def need_status(self):
        text = (self.spec / "needs" / "NEED-001-fixture.md").read_text(encoding="utf-8")
        return text.split("status: ")[1].split("\n")[0]

    def test_delivering_the_block_that_holds_the_need_reqs_delivers_the_need(self):
        write(self.root, "docs/spec/needs/NEED-001-fixture.md", self.NEED)
        self.feat(t3="done", closure="\n- closed at def5678.\n")
        run(["validate", str(self.spec), "FEAT-001", "--at", "def5678"])
        self.assertEqual(self.need_status(), "delivered")

    def test_a_need_whose_reqs_no_delivered_block_holds_stays_open(self):
        write(self.root, "docs/spec/needs/NEED-001-fixture.md", self.NEED)
        self.feat(t3="done", closure="\n- closed at def5678.\n", old="Scope: REQ-F-002", new="Scope: —")
        run(["validate", str(self.spec), "FEAT-001", "--at", "def5678"])
        self.assertEqual(self.need_status(), "refined")

    def test_spec_trace_and_check_spec_agree_on_a_need_over_two_feats(self):
        """NEED-001 lists FEAT-002 (old shape, covers REQ-F-003) and FEAT-001 (versioned: block 0.1.0 delivered, but it
        holds none of the NEED's REQs). Delivering FEAT-002 must not deliver the NEED, which check_spec.py would then
        fail [need-status]: both tools apply check_spec.feat_delivered_for."""
        write(self.root, "docs/spec/needs/NEED-001-fixture.md",
              self.NEED.replace("requirements: [REQ-F-002]", "requirements: [REQ-F-003]")
              .replace("features: [FEAT-001]", "features: [FEAT-001, FEAT-002]"))
        write(self.root, "docs/spec/features/FEAT-002.md",
              FEAT_2.replace("| doing |", "| done |") + "\n## Closure\n\n- closed at def5678.\n")
        code, out, err = run(["validate", str(self.spec), "FEAT-002", "--at", "def5678"])
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.need_status(), "refined")
        checked = subprocess.run([sys.executable, str(HERE / "check_spec.py"), str(self.spec),
                                  str(HERE.parent / "schemas")], capture_output=True, text=True, check=False,
                                 env={k: v for k, v in os.environ.items() if k != "CI"})
        self.assertNotIn("[need-status]", checked.stderr)

    def test_lint_counts_the_open_block_rows(self):
        self.feat(status="delivered", t3="done", old="## Versions", new="## Plan\n\n### Tests\n\n- 1 task rows planned.\n\n"
                                                                          "## Versions")
        code, out, err = run(["lint", str(self.spec), "FEAT-001"])
        self.assertNotIn("Plan says", err)
        self.feat(status="delivered", t3="done", old="## Versions", new="## Plan\n\n### Tests\n\n- 3 task rows.\n\n"
                                                                          "## Versions")
        code, out, err = run(["lint", str(self.spec), "FEAT-001"])
        self.assertIn("FEAT-001: Plan says 3 rows, the open version block 0.2.0 has 1", err)


class AntiBucketTest(VersionCase):
    def test_a_versioned_feat_inside_its_steps_passes(self):
        self.assertEqual(self.check(), [])

    def test_a_block_row_serving_an_undeclared_step_fails(self):
        self.process("| REQ-F-003 | FEAT-002 T1 |", "| REQ-F-003 | FEAT-002 T1 · FEAT-001 T3 |")
        self.assert_error(self.check(), "FEAT-001 0.2.0: FEAT-001 T3 serves PROC-001 S3, outside the FEAT's "
                                        "processes (PROC-001 S1–S2)")

    def test_closed_blocks_are_not_checked(self):
        self.process("| REQ-F-003 | FEAT-002 T1 |", "| REQ-F-003 | FEAT-002 T1 · FEAT-001 T1 |")
        self.assertEqual(self.check(), [])

    def test_a_scope_req_cited_only_outside_the_declared_steps_fails(self):
        self.feat(old="Scope: REQ-F-002", new="Scope: REQ-F-002 · REQ-F-003")
        text = self.text().replace("requirements: [REQ-F-001, REQ-F-002]", "requirements: [REQ-F-001, REQ-F-002, "
                                                                            "REQ-F-003]")
        write(self.root, "docs/spec/features/FEAT-001.md", text)
        self.req("REQ-F-003", "FEAT-002, FEAT-001")
        self.assert_error(self.check(), "FEAT-001 0.2.0: Scope names REQ-F-003, which only PROC-001 S3 cites, outside "
                                        "the FEAT's processes")

    def test_a_block_naming_an_undeclared_enabler_fails(self):
        self.feat(old="#### Tasks\n\n| ID | Task | Files | Status |\n|---|---|---|---|\n| T3",
                  new="#### Plan delta\n\n- Contract: `ENB-004:turn-result` gains `missed`.\n\n#### Tasks\n\n"
                      "| ID | Task | Files | Status |\n|---|---|---|---|\n| T3")
        self.assert_error(self.check(), "FEAT-001 0.2.0 names ENB-004, which the FEAT's enablers do not list")
        self.feat(extra="enablers: [ENB-004]\n",
                  old="#### Tasks\n\n| ID | Task | Files | Status |\n|---|---|---|---|\n| T3",
                  new="#### Plan delta\n\n- Contract: `ENB-004:turn-result` gains `missed`.\n\n#### Tasks\n\n"
                      "| ID | Task | Files | Status |\n|---|---|---|---|\n| T3")
        self.assertFalse(any("ENB-004" in e for e in self.check()))

    def test_step_ranges_are_checked(self):
        cases = (("PROC-001 S1–S9", "FEAT-001: processes PROC-001 S1–S9: S9 is not a step of PROC-001"),
                 ("PROC-001 S2–S1", "FEAT-001: processes PROC-001 S2–S1: the range runs backwards"),
                 ("PROC-001 S1–A1", "FEAT-001: processes PROC-001 S1–A1: both ends are main steps or both are "
                                    "alternatives"))
        for item, fragment in cases:
            with self.subTest(item=item):
                self.feat(old="processes: [PROC-001 S1–S2]", new=f"processes: [{item}]")
                self.assert_error(self.check(), fragment)

    def test_single_steps_and_alternatives_can_be_declared(self):
        self.feat(old="processes: [PROC-001 S1–S2]", new="processes: [PROC-001 S1, PROC-001 S2]")
        self.assertEqual(self.check(), [])
        self.feat(old="processes: [PROC-001 S1–S2]", new="processes: [PROC-001 S1, PROC-001 A1]")
        self.assert_error(self.check(), "FEAT-001 T3 serves PROC-001 S2, outside")
        self.assertFalse(any("serves PROC-001 A1" in e for e in self.check()))


class VersionNameTest(VersionCase):
    def test_semver_is_the_default(self):
        self.feat(first="0.1 greybox", second="0.1 polish")
        self.assertEqual(self.check(), [])
        self.feat(first="M1", second="M2")
        self.assert_error(self.check(), "FEAT-001: version block 'M1' does not start with a semver version")

    def test_milestone_from_the_profile(self):
        write(self.root, ".ai-kit.yaml", "release:\n  versioning: milestone\n")
        self.feat(first="M1", second="M2 polish")
        self.assertEqual(self.check(), [])
        self.feat()
        self.assert_error(self.check(), "FEAT-001: version block '0.1.0' does not start with a milestone version")


class VersionsCommandTest(VersionCase):
    def git(self, *args):
        result = subprocess.run(["git", *GIT, "-C", str(self.root), *args], capture_output=True, text=True,
                                check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def planned_then(self, rows="", scope="Scope: REQ-F-002", history=""):
        """Commit block 0.2.0 at planned with T3, then add rows and scope in a second commit."""
        self.git("init", "-q")
        self.feat(status="planned")
        self.commit("plan 0.2.0")
        text = self.text().replace("| T3 | third | `c/**` | todo |\n", "| T3 | third | `c/**` | todo |\n" + rows)
        text = text.replace("Scope: REQ-F-002", scope).replace("## History\n\n", f"## History\n\n{history}")
        write(self.root, "docs/spec/features/FEAT-001.md", text)
        self.commit("amend 0.2.0")

    def test_lists_the_blocks_and_the_feats_of_each_process(self):
        code, out, err = run(["versions", str(self.spec)])
        self.assertEqual(code, 0, out + err)
        self.assertIn("FEAT-001 0.1.0: delivered, 2 rows (T1–T2)", out)
        self.assertIn("FEAT-001 0.2.0: in-progress, 1 row (T3)", out)
        self.assertIn("PROC-001: FEAT-001 (S1–S2), FEAT-002 (S3–S4)", out)
        self.assertIn("C17 not run on FEAT-001: no git history", out)

    def test_off_without_versioned_feats(self):
        write(self.root, "docs/spec/features/FEAT-001.md", FEAT_2.replace("FEAT-002", "FEAT-001"))
        code, out, _ = run(["versions", str(self.spec)])
        self.assertEqual(code, 0)
        self.assertIn("versions: off", out)

    def test_a_req_and_a_row_added_after_planned_are_c17(self):
        self.req("REQ-F-003", "FEAT-002, FEAT-001")
        self.planned_then(rows="| T4 | fourth | `d/**` | todo |\n", scope="Scope: REQ-F-002 · REQ-F-003")
        code, out, err = run(["versions", str(self.spec), "--feat", "FEAT-001"])
        self.assertEqual(code, 1, out + err)
        self.assertIn("C17 high: FEAT-001 0.2.0: REQ-F-003 joined the block's Scope after it reached planned", out)
        self.assertIn("C17 high: FEAT-001 0.2.0: T4 was added after the block's rows were planned", out)

    def test_a_row_for_a_defect_or_an_in_scope_req_is_allowed(self):
        for line in ("- 2026-11-17 resync: T4 added for a defect found in T3.\n",
                     "- 2026-11-17 resync: T4 added, a missing step of REQ-F-002.\n"):
            with self.subTest(line=line):
                self.tmp.cleanup()
                self.setUp()
                self.planned_then(rows="| T4 | fourth | `d/**` | todo |\n", history=line)
                code, out, err = run(["versions", str(self.spec), "--feat", "FEAT-001"])
                self.assertEqual(code, 0, out + err)
                self.assertNotIn("C17 high", out)

    def test_rows_written_after_planned_in_a_later_commit_are_the_cut(self):
        self.git("init", "-q")
        self.feat(status="planned", old="| T3 | third | `c/**` | todo |\n", new="")
        self.commit("plan 0.2.0, no rows yet")
        self.feat(status="planned")
        self.commit("sdd-tasks writes T3")
        code, out, err = run(["versions", str(self.spec), "--feat", "FEAT-001"])
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("C17 high", out)

    def test_a_feat_not_yet_committed_has_nothing_to_compare(self):
        self.git("init", "-q")
        write(self.root, "README.md", "fixture\n")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "start")
        code, out, err = run(["versions", str(self.spec), "--feat", "FEAT-001"])
        self.assertEqual(code, 0, out + err)
        self.assertIn("C17: FEAT-001 has no commit yet", out)
        self.assertNotIn("C17 not run", out)

    def test_an_unknown_feat_fails(self):
        code, _, err = run(["versions", str(self.spec), "--feat", "FEAT-009"])
        self.assertEqual(code, 1)
        self.assertIn("FEAT-009 does not exist in features/", err)


if __name__ == "__main__":
    unittest.main()
