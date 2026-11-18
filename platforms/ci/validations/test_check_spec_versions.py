"""check_spec.py and the versioned FEAT (KIT-096): a FEAT is one use case for the project's life, with one `### <version>`
block per project version under `## Versions`. The block structure (rule version-block), `max_feat_tasks` failing per
open block (rule block-tasks, held by baseline.json like task-chain), the chain checks per open block, the FEAT's
`processes` links (rule feature-process) and a NEED delivered by an earlier block, with and without jsonschema. A FEAT
without `## Versions` keeps the warning (test_check_spec_tasks.py)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_profile import write_spec  # noqa: E402  (a fixture's sdd: block goes to .ai-kit.yaml, KIT-087 P4)

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/check_spec.py", "platforms/ci/schemas/**")

VALIDATIONS = Path(__file__).resolve().parent
CHECK_SPEC = VALIDATIONS / "check_spec.py"
SCHEMAS = VALIDATIONS.parent / "schemas"

TABLE = """| ID | Task | Files | Depends on | Status |
|---|---|---|---|---|
"""

FEAT = """---
id: FEAT-001
title: "Fixture use case FEAT-001"
status: {status}
requirements: [REQ-F-001, REQ-F-002]
{extra}created: "2026-11-17"
---

# FEAT-001

## Versions
<!-- one block per project version -->

### 0.1.0

Status: delivered
Scope: REQ-F-001

#### Tasks

{table}| T1 | first | `a/**` | — | done |
| T2 | second | `b/**` | T1 | done |

#### Closure

- closed.

### 0.2.0

Status: {status}
Scope: REQ-F-002

#### Tasks

{table}{rows}
#### Closure

## History

- 2026-11-17 sdd-review: delivered at abc1234 (release: merge)
"""

REQ = """---
id: {rid}
title: "Fixture rule {rid}"
type: functional
priority: must
features: [FEAT-001]
created: "2026-11-17"
---

# {rid}
"""

PROCESS = """---
id: PROC-001
title: "Fixture battle turn"
status: proposed
owner: product
kind: product
created: "2026-11-17"
updated: "2026-11-17"
---

# PROC-001
"""

NEED = """---
id: NEED-001
title: "Fixture need NEED-001"
type: improvement
status: delivered
origin: "owner"
requirements: [REQ-F-001]
features: [FEAT-001]
created: "2026-11-17"
---

# NEED-001
"""


def rows(n, start=3, deps=None):
    """n open rows T<start>..; deps maps a row number to its Depends on cell."""
    deps = deps or {}
    return "".join(f"| T{i} | task {i} | `c{i}/**` | {deps.get(i, '—')} | todo |\n" for i in range(start, start + n))


class VersionCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.spec = self.root / "docs" / "spec"  # the profile beside it holds the sdd keys (KIT-087 P4)
        for sub in ("features", "requirements/functional", "processes", "needs"):
            (self.spec / sub).mkdir(parents=True)
        for rid in ("REQ-F-001", "REQ-F-002"):
            (self.spec / "requirements/functional" / f"{rid}.md").write_text(REQ.format(rid=rid))
        (self.spec / "processes" / "PROC-001.md").write_text(PROCESS)
        self.feat()

    def tearDown(self):
        self.tmp.cleanup()

    def feat(self, status="in-progress", block_rows=None, extra="", old=None, new=None):
        text = FEAT.format(status=status, extra=extra, table=TABLE,
                           rows=rows(1) if block_rows is None else block_rows)
        (self.spec / "features" / "FEAT-001.md").write_text(text if old is None else text.replace(old, new))

    def index(self, sdd):
        write_spec(self.root, f'---\nproject: "fixture"\nversion: "0.1.0"\nupdated: "2026-11-17"\n{sdd}---\n\n# Fixture\n')

    def run_both(self, *flags):
        """The full check, then the structural one: python -S hides pyyaml and jsonschema."""
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        return [subprocess.run([sys.executable, *mode, str(CHECK_SPEC), *flags, str(self.spec), str(SCHEMAS)],
                               capture_output=True, text=True, check=False, env=env)
                for mode in ([], ["-S"])]

    def assert_passes(self, *notes):
        for result in self.run_both():
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for note in notes:
                self.assertIn(note, result.stdout + result.stderr)

    def assert_fails(self, *messages, full_only=False):
        for result in self.run_both()[:1] if full_only else self.run_both():
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            for message in messages:
                self.assertIn(message, result.stderr)


class BlockStructureTest(VersionCase):
    def test_a_versioned_feat_passes(self):
        self.assert_passes("spec: OK")

    def test_feat_status_follows_its_last_block(self):
        self.feat(status="in-progress", old="Status: in-progress", new="Status: planned")
        self.assert_fails("status in-progress, but its last version block 0.2.0 is planned", "[version-block]")

    def test_only_the_last_block_is_open(self):
        self.feat(old="Status: delivered", new="Status: in-progress")
        self.assert_fails("FEAT-001 0.1.0 is in-progress, but only the last version block is open", "[version-block]")

    def test_a_block_without_a_valid_status_line_fails(self):
        for new in ("", "Status: done"):
            with self.subTest(new=new):
                self.feat(old="Status: delivered", new=new)
                self.assert_fails("FEAT-001 0.1.0 needs a `Status:` line", "[version-block]")

    def test_a_row_outside_every_block_fails(self):
        self.feat(old="## History", new=f"## Tasks\n\n{TABLE}| T9 | stray | `z/**` | — | todo |\n\n## History")
        self.assert_fails("T9 is outside every version block", "[version-block]")

    def test_two_blocks_with_one_name_fail(self):
        self.feat(old="### 0.2.0", new="### 0.1.0")
        self.assert_fails("two version blocks are named 0.1.0", "[version-block]")

    def test_a_block_scope_req_the_feat_does_not_list_fails(self):
        self.feat(old="Scope: REQ-F-002", new="Scope: REQ-F-002 · REQ-F-007")
        self.assert_fails("FEAT-001 0.2.0 Scope names REQ-F-007, which the FEAT's requirements do not list",
                          "[version-block]")

    def test_a_req_outside_every_block_scope_fails(self):
        self.feat(old="Scope: REQ-F-002", new="Scope: —")
        self.assert_fails("FEAT-001 requirements lists REQ-F-002, which no version block's Scope names",
                          "[version-block]")

    def test_versions_without_a_block_fails(self):
        (self.spec / "features" / "FEAT-001.md").write_text(
            FEAT.format(status="in-progress", extra="", table=TABLE, rows="").split("### 0.1.0")[0])
        self.assert_fails("## Versions holds no `### <version>` block", "[version-block]")


class CommentedRowTest(VersionCase):
    def test_a_row_inside_an_html_comment_is_not_a_row(self):
        self.feat(old="## History", new=f"<!--\n{TABLE}| T9 | stray | `z/**` | — | todo |\n-->\n\n## History")
        self.assert_passes("spec: OK")


class BlockTasksTest(VersionCase):
    def test_an_open_block_above_max_feat_tasks_fails(self):
        self.index("sdd:\n  max_feat_tasks: 3\n")
        self.feat(block_rows=rows(4))
        self.assert_fails("FEAT-001 0.2.0 has 4 task rows, above sdd.max_feat_tasks 3", "[block-tasks]")

    def test_rows_of_closed_blocks_do_not_count(self):
        self.index("sdd:\n  max_feat_tasks: 3\n")
        self.feat(block_rows=rows(3))  # 5 rows in the FEAT, 3 in the open block
        self.assert_passes()

    def test_a_closed_block_above_the_cap_does_not_fail(self):
        self.index("sdd:\n  max_feat_tasks: 1\n")
        self.feat(status="delivered", block_rows=rows(1).replace("todo", "done"))
        self.assert_passes()

    def test_the_versioned_feat_no_longer_warns(self):
        self.index("sdd:\n  max_feat_tasks: 3\n")
        self.feat(block_rows=rows(3))
        for result in self.run_both():
            self.assertNotIn("task-size", result.stderr)

    def test_baseline_holds_a_block_and_fails_when_it_grows(self):
        self.index("sdd:\n  max_feat_tasks: 3\n")
        self.feat(block_rows=rows(4))
        (self.spec / "baseline.json").write_text(json.dumps({"rules": {"block-tasks": {"FEAT-001": 4}}}))
        self.assert_passes("BASELINE: ")
        self.feat(block_rows=rows(5))
        self.assert_fails("holds a 4-row block-tasks for FEAT-001, found 5 rows")

    def test_baseline_init_records_the_block_size(self):
        self.index("sdd:\n  max_feat_tasks: 3\n")
        self.feat(block_rows=rows(4))
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        subprocess.run([sys.executable, str(CHECK_SPEC), "--baseline-init", str(self.spec), str(SCHEMAS)],
                       capture_output=True, text=True, check=False, env=env)
        held = json.loads((self.spec / "baseline.json").read_text())["rules"]
        self.assertEqual(held["block-tasks"], {"FEAT-001": 4})


class BlockChainTest(VersionCase):
    def test_a_dependency_on_an_earlier_block_row_is_not_missing(self):
        self.feat(block_rows=rows(1, deps={3: "T2"}))
        self.assert_passes()

    def test_a_dependency_on_no_row_fails(self):
        self.feat(block_rows=rows(1, deps={3: "T8"}))
        self.assert_fails("T3 Depends on T8, which is not a row of the FEAT-001 task table", "[task-depends]")

    def test_the_chain_is_measured_inside_the_open_block(self):
        self.index("sdd:\n  max_chain: 2\n")
        self.feat(block_rows=rows(3, deps={4: "T3", 5: "T4"}))
        self.assert_fails("FEAT-001 0.2.0: longest Depends on chain is 3 rows (T3 → T4 → T5), above sdd.max_chain 2",
                          "[task-chain]")

    def test_a_cycle_in_the_open_block_fails(self):
        self.feat(block_rows=rows(2, deps={3: "T4", 4: "T3"}))
        self.assert_fails("[task-cycle]")


class FeatureProcessTest(VersionCase):
    def test_declared_step_ranges_pass(self):
        self.feat(extra="processes: [PROC-001 S1–S3, PROC-001 A1, \"PROC-001 S5-S6\"]\n")
        self.assert_passes()

    def test_an_unknown_process_fails(self):
        self.feat(extra="processes: [PROC-009 S1–S2]\n")
        self.assert_fails("processes lists PROC-009 S1–S2, which names no existing process", "[feature-process]")

    def test_a_malformed_item_fails(self):
        self.feat(extra="processes: [PROC-001 steps 1 to 3]\n")
        self.assert_fails("processes lists 'PROC-001 steps 1 to 3': write PROC-nnn", "[feature-process]")

    def test_a_feat_without_versions_may_declare_processes(self):
        (self.spec / "features" / "FEAT-001.md").write_text(
            FEAT.format(status="planned", extra="processes: [PROC-001]\n", table=TABLE, rows="")
            .split("## Versions")[0])
        self.assert_passes()


class NeedDeliveredByAnEarlierBlockTest(VersionCase):
    def test_a_need_delivered_by_an_earlier_block_stays_valid(self):
        (self.spec / "needs" / "NEED-001.md").write_text(NEED)
        self.assert_passes()

    def test_a_need_whose_reqs_no_delivered_block_holds_fails(self):
        (self.spec / "needs" / "NEED-001.md").write_text(NEED.replace("requirements: [REQ-F-001]",
                                                                              "requirements: [REQ-F-002]"))
        self.assert_fails("status delivered, but FEAT-001 is in-progress", "[need-status]")

    def test_a_need_on_a_feat_with_no_delivered_block_fails(self):
        (self.spec / "needs" / "NEED-001.md").write_text(NEED)
        self.feat(old="Status: delivered", new="Status: cancelled")
        self.assert_fails("status delivered, but FEAT-001 is in-progress", "[need-status]")


if __name__ == "__main__":
    unittest.main()
