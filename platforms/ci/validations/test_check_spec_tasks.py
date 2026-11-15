"""check_spec.py on task rows (KIT-068): TASK-nnn files (tracker: none), the FEAT task table's Item links, its longest
Depends on chain, its size and cell warnings, and the per-rule baseline that may only shrink. Every test runs the full
check and the structural one (python -S hides pyyaml and jsonschema)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

VALIDATIONS = Path(__file__).resolve().parent
CHECK_SPEC = VALIDATIONS / "check_spec.py"
SCHEMAS = VALIDATIONS.parent / "schemas"
TEMPLATES = VALIDATIONS.parents[2] / "plugins" / "guardrails" / "templates"

SPEC_INDEX = """---
project: "fixture"
version: "0.1.0"
updated: "2026-11-14"
{extra}---

# Fixture
"""

HEADER = ("| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Model | Wave | Item |\n"
          "|---|---|---|---|---|---|---|---|---|---|---|\n")

FEAT = """---
id: {fid}
title: "Fixture feature {fid}"
status: {status}
requirements: []
created: "2026-11-14"
---

# {fid}

## Plan

### Design

Fixture.

## Tasks

{table}
## History

- 2026-11-14 plan: created.
"""

TASK = """---
id: {tid}
feat: {fid}
rows: [{rows}]
title: "Fixture task {tid}"
status: {status}
created: "2026-11-14"
---

# {tid} — Fixture task

## Task

Plan § Design.
"""


def row(tid, depends="—", item="—", task="Build the slice: Plan § Design"):
    return f"| {tid} | {task} | `src/a.py` | `pytest tests/test_a.py` | CA-1 | {depends} | todo | Low | small | 0 | {item} |\n"


class SpecFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spec = Path(self.tmp.name)
        (self.spec / "features").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def index(self, extra=""):
        (self.spec / "spec.md").write_text(SPEC_INDEX.format(extra=extra))

    def feat(self, fid, *rows, status="planned"):
        table = HEADER + "".join(rows) if rows else ""
        (self.spec / "features" / f"{fid}-fixture.md").write_text(FEAT.format(fid=fid, status=status, table=table))

    def task(self, tid, fid="FEAT-001", rows="T1", status="todo", name=None, text=None):
        (self.spec / "tasks").mkdir(exist_ok=True)
        body = text if text is not None else TASK.format(tid=tid, fid=fid, rows=rows, status=status)
        (self.spec / "tasks" / f"{name or tid + '-fixture'}.md").write_text(body)

    def run_mode(self, flags, *args):
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        result = subprocess.run([sys.executable, *flags, str(CHECK_SPEC), *args, str(self.spec), str(SCHEMAS)],
                                capture_output=True, text=True, check=False, env=env)
        if flags:
            self.assertIn("spec validation will be structural", result.stderr)
        return result

    def run_both(self, *args):
        return [self.run_mode(flags, *args) for flags in ([], ["-S"])]

    def assert_passes(self, *warnings):
        for result in self.run_both():
            self.assertEqual(result.returncode, 0, result.stderr)
            for warning in warnings:
                self.assertIn(warning, result.stderr)
        return result

    def assert_fails(self, *messages):
        for result in self.run_both():
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            for message in messages:
                self.assertIn(message, result.stderr)
        return result


class TaskFileTest(SpecFixture):
    """tracker: none keeps one docs/spec/tasks/TASK-nnn-slug.md per cut item, its status in frontmatter."""

    def test_valid_task_file_passes(self):
        self.feat("FEAT-001", row("T1", item="TASK-001"))
        self.task("TASK-001")
        self.assert_passes()

    def test_bundled_rows_share_one_task(self):
        self.feat("FEAT-001", row("T1", item="TASK-001"), row("T2", item="TASK-001"))
        self.task("TASK-001", rows="T1, T2")
        self.assert_passes()

    def test_unknown_status_fails(self):
        self.feat("FEAT-001", row("T1", item="TASK-001"))
        self.task("TASK-001", status="review")
        self.assert_fails("TASK-001-fixture.md", "'review'")

    def test_file_name_must_carry_the_id(self):
        self.feat("FEAT-001", row("T1", item="TASK-001"))
        self.task("TASK-001", name="TASK-002-fixture")
        self.assert_fails("id=TASK-001 != file name prefix")

    def test_feat_must_exist(self):
        self.feat("FEAT-001", row("T1", item="TASK-001"))
        self.task("TASK-001")
        self.task("TASK-002", fid="FEAT-009")
        self.assert_fails("feat FEAT-009 does not exist in features/")

    def test_row_must_be_in_the_feat_table(self):
        self.feat("FEAT-001", row("T1", item="TASK-001"))
        self.task("TASK-001", rows="T1, T7")
        self.assert_fails("row T7 is not a row of the FEAT-001 task table")

    def test_item_cell_must_name_the_task(self):
        self.feat("FEAT-001", row("T1", item="#12"))
        self.task("TASK-001")
        self.assert_fails("FEAT-001 T1 Item is '#12', not TASK-001")

    def test_item_naming_a_missing_task_fails(self):
        self.feat("FEAT-001", row("T1", item="TASK-009"))
        self.assert_fails("T1 Item TASK-009 has no file under tasks/")

    def test_item_naming_a_task_that_does_not_list_the_row_fails(self):
        self.feat("FEAT-001", row("T1", item="TASK-001"), row("T2", item="TASK-001"))
        self.task("TASK-001", rows="T1")
        self.assert_fails("T2 Item TASK-001, but TASK-001 rows does not list T2")

    def test_task_prefix_is_reserved_for_decisions(self):
        self.index("decision_kinds: {tech: TASK}\n")
        self.assert_fails("decision prefix 'TASK' must match")

    def test_kit_task_template_validates(self):
        """The spec-task.md template sdd-tasks copies validates once its placeholders hold real values."""
        template = (TEMPLATES / "spec-task.md").read_text()
        self.feat("FEAT-000", row("T1", item="TASK-000"))
        self.task("TASK-000", text=template.replace("YYYY-MM-DD", "2026-11-14"))
        self.assert_passes()


class TaskTableTest(SpecFixture):
    """The FEAT task table of an open FEAT: longest Depends on chain, row count and Task cell size."""

    def chain(self, length, fid="FEAT-001", status="planned"):
        rows = [row("T1")] + [row(f"T{n}", depends=f"T{n - 1}") for n in range(2, length + 1)]
        self.feat(fid, *rows, status=status)

    def test_chain_at_the_kit_maximum_passes(self):
        self.chain(4)
        self.assert_passes()

    def test_chain_above_the_kit_maximum_fails(self):
        self.chain(5)
        self.assert_fails("longest Depends on chain is 5 rows (T1 → T2 → T3 → T4 → T5), above sdd.max_chain 4")

    def test_chain_reads_the_project_maximum(self):
        self.index("sdd:\n  max_chain: 2\n")
        self.chain(3)
        self.assert_fails("longest Depends on chain is 3 rows (T1 → T2 → T3), above sdd.max_chain 2")

    def test_rows_of_another_feat_do_not_extend_the_chain(self):
        """`FEAT-002 T1, T2` continues FEAT-002 up to the next `;`; only bare own-FEAT ids join the chain."""
        self.feat("FEAT-002", row("T1"), row("T2", depends="T1"), row("T3", depends="T2"))
        self.feat("FEAT-001", row("T1", depends="FEAT-002 T1, T2, T3"), row("T2", depends="T1; FEAT-002 T3"),
                  row("T3", depends="T2"), row("T4", depends="T3, FEAT-002 T2"))
        self.assert_passes()

    def test_cycle_fails(self):
        self.feat("FEAT-001", row("T1", depends="T2"), row("T2", depends="T1"))
        self.assert_fails("Depends on cycle T1 → T2 → T1 [task-cycle]")

    def test_dependency_on_a_missing_row_fails(self):
        self.feat("FEAT-001", row("T1"), row("T2", depends="T1, T9"))
        self.assert_fails("T2 Depends on T9, which is not a row of the FEAT-001 task table [task-depends]")

    def test_delivered_feat_is_history(self):
        self.chain(6, status="delivered")
        self.assert_passes()

    def test_rows_above_max_feat_tasks_warn_only(self):
        self.index("sdd:\n  max_feat_tasks: 3\n")
        self.feat("FEAT-001", *(row(f"T{n}") for n in range(1, 5)))
        self.assert_passes("4 task rows, above sdd.max_feat_tasks 3")

    def test_rows_at_the_default_max_feat_tasks_do_not_warn(self):
        self.feat("FEAT-001", *(row(f"T{n}") for n in range(1, 31)))
        result = self.assert_passes()
        self.assertNotIn("max_feat_tasks", result.stderr)

    def test_long_task_cell_warns_only(self):
        self.feat("FEAT-001", row("T1", task="x" * 1001), row("T2", task="y" * 1000))
        result = self.assert_passes("T1 Task cell has 1001 characters, above 1000")
        self.assertNotIn("T2 Task cell", result.stderr)


class BaselineTest(SpecFixture):
    """docs/spec/baseline.json holds old findings per rule and artifact; it may only shrink. A count per artifact,
    except task-chain, which holds the chain length in rows."""

    def setUp(self):
        super().setUp()
        self.chain_feat("FEAT-001")

    def chain_feat(self, fid, length=5):
        rows = [row("T1")] + [row(f"T{n}", depends=f"T{n - 1}") for n in range(2, length + 1)]
        self.feat(fid, *rows)

    def baseline(self, rules):
        (self.spec / "baseline.json").write_text(json.dumps({"rules": rules}))

    def stored(self):
        return json.loads((self.spec / "baseline.json").read_text())["rules"]

    def test_finding_in_the_baseline_does_not_block(self):
        self.baseline({"task-chain": {"FEAT-001": 5}})
        result = self.assert_passes()
        self.assertIn("1 finding held by baseline.json", result.stdout)
        self.assertIn("BASELINE:", result.stdout)

    def test_new_finding_beside_the_baseline_fails(self):
        self.baseline({"task-chain": {"FEAT-001": 5}})
        self.chain_feat("FEAT-002")
        self.assert_fails("FEAT-002-fixture.md: longest Depends on chain is 5 rows")

    def test_held_chain_that_grows_fails(self):
        self.baseline({"task-chain": {"FEAT-001": 5}})
        self.chain_feat("FEAT-001", length=6)
        self.assert_fails("baseline.json holds a 5-row task-chain for FEAT-001, found 6 rows")

    def test_shorter_held_chain_must_be_lowered(self):
        self.baseline({"task-chain": {"FEAT-001": 6}})
        self.assert_fails("baseline.json holds a 6-row task-chain for FEAT-001, found 5 rows: lower it with "
                          "check_spec.py --baseline-update")

    def test_extra_finding_on_a_held_artifact_fails(self):
        self.feat("FEAT-002", row("T1", depends="T9"))
        self.baseline({"task-chain": {"FEAT-001": 5}, "task-depends": {"FEAT-002": 1}})
        self.assert_passes()
        self.feat("FEAT-002", row("T1", depends="T8, T9"))
        self.assert_fails("baseline.json holds 1 task-depends finding for FEAT-002, found 2")

    def test_fixed_finding_must_leave_the_baseline(self):
        self.baseline({"task-chain": {"FEAT-001": 5}})
        self.chain_feat("FEAT-001", length=4)
        self.assert_fails("baseline.json holds a 5-row task-chain for FEAT-001, found none: lower it "
                          "with check_spec.py --baseline-update")

    def test_update_only_lowers(self):
        self.chain_feat("FEAT-001", length=4)
        self.chain_feat("FEAT-002")
        self.chain_feat("FEAT-003", length=6)
        for flags in ([], ["-S"]):
            self.baseline({"task-chain": {"FEAT-001": 5, "FEAT-003": 7}, "C11": {"REQ-F-001": 2}})
            result = self.run_mode(flags, "--baseline-update")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("FEAT-002-fixture.md: longest Depends on chain is 5 rows", result.stderr)
            self.assertEqual(self.stored(), {"task-chain": {"FEAT-003": 6}, "C11": {"REQ-F-001": 2}},
                             "the fixed key leaves, a shorter chain is lowered, the new finding is not added, "
                             "sdd-check rows stay")

    def test_init_writes_the_current_findings_once(self):
        self.chain_feat("FEAT-002", length=6)
        for flags in ([], ["-S"]):
            result = self.run_mode(flags, "--baseline-init")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self.stored(), {"task-chain": {"FEAT-001": 5, "FEAT-002": 6}})
            again = self.run_mode(flags, "--baseline-init")
            self.assertEqual(again.returncode, 1)
            self.assertIn("baseline.json exists and may only shrink", again.stderr)
            (self.spec / "baseline.json").unlink()

    def test_against_refuses_a_grown_baseline(self):
        older = self.spec.parent / f"{self.spec.name}-older.json"
        older.write_text(json.dumps({"rules": {"task-chain": {"FEAT-001": 5, "FEAT-003": 7}}}))
        self.addCleanup(older.unlink)
        self.baseline({"task-chain": {"FEAT-001": 5}})
        self.assert_passes()
        for result in self.run_both("--baseline-against", str(older)):
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.chain_feat("FEAT-001", length=6)
        self.chain_feat("FEAT-002")
        self.baseline({"task-chain": {"FEAT-001": 6, "FEAT-002": 5}})
        for result in self.run_both("--baseline-against", str(older)):
            self.assertEqual(result.returncode, 1)
            self.assertIn("baseline.json raises task-chain FEAT-001 from 5 to 6", result.stderr)
            self.assertIn("baseline.json adds task-chain FEAT-002", result.stderr)

    def test_against_a_missing_older_file_passes(self):
        """A pull request's base without baseline.json has nothing to compare: the check skips."""
        self.baseline({"task-chain": {"FEAT-001": 5}})
        missing = self.spec.parent / f"{self.spec.name}-absent.json"
        for result in self.run_both("--baseline-against", str(missing)):
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("no older baseline", result.stdout)

    def test_unknown_rule_fails_and_sdd_check_rows_pass(self):
        self.baseline({"task-chain": {"FEAT-001": 5}, "Q5": {"FEAT-001": 1}, "made-up": {"FEAT-001": 1}})
        self.assert_fails("baseline.json: unknown rule 'made-up'")

    def test_value_must_be_a_positive_integer(self):
        self.baseline({"task-chain": {"FEAT-001": 0}})
        self.assert_fails("baseline.json: task-chain FEAT-001 must be an integer of at least 1")


WORKFLOW = VALIDATIONS.parents[1] / "kits" / "github" / "workflows" / "spec-lint.yml"


class SpecLintWorkflowTest(unittest.TestCase):
    """The spec-lint.yml template projects copy runs --baseline-against on a pull request, so a hand-grown baseline
    fails CI. The step's own shell runs here against a throwaway git repository."""

    def steps(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("pyyaml missing")
        return yaml.safe_load(WORKFLOW.read_text())["jobs"]["validate"]["steps"]

    def baseline_step(self):
        found = [step for step in self.steps() if step.get("name") == "Baseline only shrinks"]
        self.assertEqual(len(found), 1, "spec-lint.yml has no 'Baseline only shrinks' step")
        return found[0]

    def test_template_carries_the_baseline_step(self):
        steps = self.steps()
        checkout = next(step for step in steps if str(step.get("uses", "")).startswith("actions/checkout@"))
        self.assertEqual((checkout.get("with") or {}).get("fetch-depth"), 0, "the base ref must be fetched")
        step = self.baseline_step()
        self.assertEqual(step.get("if"), "github.event_name == 'pull_request'")
        self.assertIn("--baseline-against", step["run"])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        lint = self.repo / ".github" / "spec-lint"
        (lint / "schemas").mkdir(parents=True)
        (lint / "check_spec.py").write_bytes(CHECK_SPEC.read_bytes())
        for schema in SCHEMAS.glob("*.json"):
            (lint / "schemas" / schema.name).write_bytes(schema.read_bytes())
        (self.repo / "docs" / "spec" / "features").mkdir(parents=True)
        self.feat("FEAT-001")
        self.git("init", "-q", "-b", "main")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                       check=True, capture_output=True, text=True)

    def feat(self, fid):
        rows = [row("T1")] + [row(f"T{n}", depends=f"T{n - 1}") for n in range(2, 6)]
        (self.repo / "docs" / "spec" / "features" / f"{fid}-fixture.md").write_text(
            FEAT.format(fid=fid, status="planned", table=HEADER + "".join(rows)))

    def baseline(self, rules):
        (self.repo / "docs" / "spec" / "baseline.json").write_text(json.dumps({"rules": rules}))

    def base_commit(self):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")

    def run_step(self):
        try:
            import jsonschema  # noqa: F401  (the step runs with CI=1, which needs both libraries)
        except ImportError:
            self.skipTest("jsonschema missing")
        runner = Path(self.tmp.name) / "runner"
        runner.mkdir()
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        env.update(BASE_REF="main", RUNNER_TEMP=str(runner),
                   PATH=f"{Path(sys.executable).parent}{os.pathsep}{os.environ.get('PATH', '')}")
        return subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", self.baseline_step()["run"]],
                              cwd=self.repo, env=env, capture_output=True, text=True, check=False)

    def test_baseline_step_refuses_a_grown_baseline(self):
        self.baseline({"task-chain": {"FEAT-001": 5}})
        self.base_commit()
        self.feat("FEAT-002")
        self.baseline({"task-chain": {"FEAT-001": 5, "FEAT-002": 5}})
        result = self.run_step()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("baseline.json adds task-chain FEAT-002", result.stderr)

    def test_baseline_step_passes_a_shrunk_baseline(self):
        self.feat("FEAT-002")
        self.baseline({"task-chain": {"FEAT-001": 5, "FEAT-002": 5}})
        self.base_commit()
        (self.repo / "docs" / "spec" / "features" / "FEAT-002-fixture.md").unlink()
        self.baseline({"task-chain": {"FEAT-001": 5}})
        result = self.run_step()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_baseline_step_skips_when_the_base_has_no_baseline(self):
        self.base_commit()
        self.baseline({"task-chain": {"FEAT-001": 5}})
        result = self.run_step()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
