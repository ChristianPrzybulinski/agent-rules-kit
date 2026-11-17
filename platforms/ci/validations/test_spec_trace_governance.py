"""spec_trace.py governance (KIT-099): one generated, read-only view of who decides, approves, owns and runs what —
the profile's approval keys and protected paths, decisions by kind, enabler and process owners, each tech process with
its trigger and last run, each debt with its payment state — plus the C25 lines of sdd-check (an open FEAT that touches
an ENB with an open debt it neither pays nor accepts). It writes nothing, and a spec without debts, tech processes or
enablers still renders it."""
import shutil
import sys
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/spec_trace.py",)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_spec_trace_enabler as enb  # noqa: E402  (the ENB fixture: FEAT-001 on ENB-001, FEAT-002 on ENB-002)

DEBT = """\
---
id: {did}
title: "Fixture debt {did}"
status: {status}
severity: medium
trigger: "{trigger}"
features: []
enablers: [{enablers}]
created: "2026-11-17"
---

# {did}

{body}
"""

DECISION = """\
---
id: {did}
title: "Fixture decision {did}"
status: {status}
date: "2026-11-17"
kind: {kind}
deciders: "{deciders}"
---

# {did}

{body}
"""

TECH_PROCESS = """\
---
id: PROC-002
title: "Keep dependencies without known vulnerabilities"
status: approved
owner: tech-lead
kind: tech
---

# PROC-002

## Trigger

- [FACT] Weekly on Monday | the owner runs it; or an advisory names a dependency.

## Steps

| Step | Action → result | Rules | Implemented by | Proven by |
|---|---|---|---|---|

## History

- 2026-11-01: created.
- 2026-11-17: run: 1 CVE at 7 or above, NEED-004.
- 2026-11-10: run: no CVE at 7 or above.
"""


def governance(spec, *args):
    return enb.run(["governance", str(spec), *args])


class GovernanceCase(enb.EnablerCase):
    def setUp(self):
        super().setUp()
        self.debt("DEBT-001", "open", "when touching the battle module", "ENB-001")
        self.debt("DEBT-002", "accepted", "before the vertical slice", "ENB-001", "Accepted by DEC-002.")
        self.debt("DEBT-003", "paid", "flag on more than 30 days", "")
        self.debt("DEBT-004", "accepted", "never", "")
        self.decision("DEC-002", "approved", "tech", "tech-lead", "We live with DEBT-002.")
        self.decision("DEC-003", "proposed", "tech", "tech-lead (owner in chat, 2026-11-17); architect", "")
        self.decision("DEC-004", "approved", "game", "owner", "")
        enb.write(self.root, "docs/spec/processes/PROC-001-battle-turn.md", enb.PROCESS)
        enb.write(self.root, "docs/spec/processes/PROC-002-no-vulnerabilities.md", TECH_PROCESS)

    def debt(self, did, status, trigger, enablers, body=""):
        enb.write(self.root, f"docs/spec/debts/{did}.md",
                  DEBT.format(did=did, status=status, trigger=trigger, enablers=enablers, body=body))

    def decision(self, did, status, kind, deciders, body):
        enb.write(self.root, f"docs/spec/decisions/{did}.md",
                  DECISION.format(did=did, status=status, kind=kind, deciders=deciders, body=body))

    def view(self, *args):
        code, out, err = governance(self.spec, *args)
        self.assertEqual(code, 0, err)
        return out

    def row(self, out, first):
        rows = [line for line in out.splitlines() if line.startswith(f"| {first} |")]
        self.assertEqual(len(rows), 1, f"one row starting {first!r} in:\n{out}")
        return rows[0]


class GovernanceViewTest(GovernanceCase):
    def test_sections_in_order(self):
        out = self.view()
        heads = [line for line in out.splitlines() if line.startswith("## ")]
        self.assertEqual(heads, ["## Approvals", "## Protected paths", "## Decisions by kind", "## Owners",
                                 "## Tech processes", "## Debts", "## Debt payment (C25)"])
        self.assertTrue(out.startswith("# Governance\n"))

    def test_approvals_come_from_the_profile(self):
        out = self.view()
        self.assertIn("decision", self.row(out, "sdd.owner_approvals"))
        self.assertIn("none", self.row(out, "sdd.visual_approval"))
        self.assertIn("3", self.row(out, "review.rounds"))
        self.assertIn("true", self.row(out, "review.independent_reviewer"))

    def test_profile_review_and_gates_keys(self):
        enb.write(self.root, ".ai-kit.yaml",
                  "review:\n  rounds: 2\ngates:\n  protected_paths:\n    owner-ok: ['docs/spec/decisions/**']\n")
        out = self.view()
        self.assertIn("2", self.row(out, "review.rounds"))
        self.assertEqual(self.row(out, "`docs/spec/decisions/**`"),
                         "| `docs/spec/decisions/**` | owner-ok | gates.protected_paths |")

    def test_decisions_by_kind_count_each_status(self):
        out = self.view()
        self.assertEqual(self.row(out, "tech"), "| tech | architect, tech-lead | 1 | 1 | 0 | 0 |")
        self.assertEqual(self.row(out, "game"), "| game | owner | 0 | 1 | 0 | 0 |")
        self.assertEqual(self.row(out, "—"), "| — | — | 0 | 1 | 0 | 0 |")  # DEC-001 has no kind

    def test_owners_of_enablers_and_processes(self):
        out = self.view()
        self.assertEqual(self.row(out, "battle-team"), "| battle-team | ENB-001 | — |")
        self.assertEqual(self.row(out, "tech-lead"), "| tech-lead | — | PROC-002 (tech) |")
        self.assertEqual(self.row(out, "product"), "| product | — | PROC-001 (product) |")

    def test_tech_process_trigger_and_last_run(self):
        out = self.view()
        self.assertEqual(self.row(out, "[PROC-002](processes/PROC-002-no-vulnerabilities.md)"),
                         "| [PROC-002](processes/PROC-002-no-vulnerabilities.md) | Keep dependencies without known "
                         "vulnerabilities | approved | tech-lead | Weekly on Monday \\| the owner runs it; or an "
                         "advisory names a dependency. | 2026-11-17 |")
        self.assertNotIn("[PROC-001]", out)  # a product process is not a tech process

    def test_tech_process_never_run(self):
        enb.write(self.root, "docs/spec/processes/PROC-002-no-vulnerabilities.md",
                  TECH_PROCESS.replace("- 2026-11-17: run", "- 2026-11-17: note").replace("- 2026-11-10: run",
                                                                                        "- 2026-11-10: note"))
        self.assertTrue(self.row(self.view(), "[PROC-002](processes/PROC-002-no-vulnerabilities.md)")
                        .endswith("| never |"))

    def test_debts_with_their_payment_state(self):
        out = self.view()
        self.assertEqual(self.row(out, "[DEBT-001](debts/DEBT-001.md)"),
                         "| [DEBT-001](debts/DEBT-001.md) | Fixture debt DEBT-001 | medium | when touching the battle "
                         "module | ENB-001 | open |")
        self.assertTrue(self.row(out, "[DEBT-002](debts/DEBT-002.md)").endswith("| accepted by DEC-002 |"))
        self.assertTrue(self.row(out, "[DEBT-004](debts/DEBT-004.md)")
                        .endswith("| accepted; no approved decision names it |"))
        self.assertTrue(self.row(out, "[DEBT-003](debts/DEBT-003.md)").endswith("| — | paid |"))

    def test_a_feat_that_cites_a_debt_pays_it(self):
        self.feat("FEAT-001", "REQ-F-001, REQ-NF-001", "ENB-001", "- T1 pays DEBT-001 and DEBT-003.")
        out = self.view()
        self.assertTrue(self.row(out, "[DEBT-001](debts/DEBT-001.md)").endswith("| open; FEAT-001 plans it |"))
        self.assertTrue(self.row(out, "[DEBT-003](debts/DEBT-003.md)").endswith("| paid by FEAT-001 |"))

    def test_writes_nothing(self):
        before = sorted((p, p.read_bytes()) for p in self.root.rglob("*") if p.is_file())
        self.view()
        self.assertEqual(before, sorted((p, p.read_bytes()) for p in self.root.rglob("*") if p.is_file()))


class DebtPaymentTest(GovernanceCase):
    """C25: an open FEAT whose `enablers` names an ENB with an open debt must pay it (cite the DEBT) or cite an
    approved decision that accepts it (names the DEBT)."""
    C25 = ("- C25: FEAT-001 touches ENB-001, whose DEBT-001 is open (trigger: when touching the battle module): a "
           "task row pays it (cites DEBT-001), or the FEAT cites an approved decision that accepts it")

    def test_open_debt_on_a_touched_enabler(self):
        out = self.view()
        self.assertIn(self.C25, out)
        self.assertNotIn("DEBT-002 is", out)  # accepted
        self.assertNotIn("FEAT-002 touches", out)  # ENB-002 has no debt

    def test_feat_scope(self):
        self.assertIn(self.C25, self.view("--feat", "FEAT-001"))
        out = self.view("--feat", "FEAT-002")
        self.assertNotIn("C25: FEAT", out)
        self.assertIn("none", out.split("## Debt payment (C25)")[1])

    def test_paid_by_a_task_row(self):
        self.feat("FEAT-001", "REQ-F-001, REQ-NF-001", "ENB-001", "- T1 pays DEBT-001.")
        self.assertNotIn("C25: FEAT", self.view())

    def test_accepted_by_a_cited_approved_decision(self):
        self.decision("DEC-005", "approved", "tech", "tech-lead", "We accept DEBT-001 until the slice.")
        self.feat("FEAT-001", "REQ-F-001, REQ-NF-001", "ENB-001", "- Per DEC-005.")
        self.assertNotIn("C25: FEAT", self.view())

    def test_a_proposed_decision_does_not_accept(self):
        self.decision("DEC-005", "proposed", "tech", "tech-lead", "We accept DEBT-001 until the slice.")
        self.feat("FEAT-001", "REQ-F-001, REQ-NF-001", "ENB-001", "- Per DEC-005.")
        self.assertIn(self.C25, self.view())

    def test_a_closed_feat_is_not_checked(self):
        path = self.spec / "features/FEAT-001.md"
        path.write_text(path.read_text(encoding="utf-8").replace("status: planned", "status: delivered"),
                        encoding="utf-8")
        self.assertNotIn("C25: FEAT", self.view())

    def test_unknown_feat_fails(self):
        code, _, err = governance(self.spec, "--feat", "FEAT-099")
        self.assertEqual(code, 1)
        self.assertIn("FEAT-099 does not exist", err)


class WithoutGovernanceArtifactsTest(enb.EnablerCase):
    def test_bare_spec_renders_the_view(self):
        shutil.rmtree(self.spec / "enablers")
        shutil.rmtree(self.spec / "decisions")
        code, out, err = governance(self.spec)
        self.assertEqual(code, 0, err)
        tail = out.split("## Tech processes")[1]
        self.assertIn("none", tail.split("## Debts")[0])
        self.assertIn("none", tail.split("## Debts")[1].split("## Debt payment")[0])
        self.assertIn("C25: off (no enablers/ folder", out)


if __name__ == "__main__":
    unittest.main()
