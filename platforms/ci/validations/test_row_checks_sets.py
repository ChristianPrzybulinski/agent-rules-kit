"""row_checks.py rules l and m (KIT-115): N open rows of one title shape are a set cut per item, and a row of a set that
depends on another row of it is an order. Calibrated on the Stratics tables: only the two `Handler <move>` FEATs fire."""
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/row_checks.py",)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import row_checks as rc  # noqa: E402
from test_row_checks import feat_text, make_repo, run  # noqa: E402
from test_row_checks_versions import versioned  # noqa: E402

FILES = "`tools/demo/demo.py`, `tools/demo/tests/test_demo.py`"
PROOF = "`python3 -m unittest discover -s tools/demo/tests`; `grep -q demo tools/demo/demo.py`"


def handler(n, depends="T1", status="todo"):
    return (f"T{n}", f"Handler `move_{n}` (base category `unique`): the effect of move {n}", FILES, PROOF, depends,
            status)


def contract(status="todo"):
    return ("T1", "Define the UniqueEffect contract: Plan § Contract", FILES, PROOF, "—", status)


class SiblingRows(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.spec = make_repo(self.root)
        self.cfg = rc.load_config(self.spec)

    def lint(self, rows, strict=False, all_rows=False):
        (self.spec / "features" / "FEAT-900.md").write_text(feat_text("FEAT-900", rows), encoding="utf-8")
        parsed = rc.parse_feat(self.spec / "features" / "FEAT-900.md", self.cfg)
        return rc.lint(parsed, self.cfg, strict, all_rows)[0]

    def rules(self, findings, rule):
        return [f for f in findings if f.rule == rule]

    def test_a_set_of_four_open_rows_is_reported_once_on_its_first_row(self):
        found = self.rules(self.lint([contract()] + [handler(n) for n in range(2, 6)]), "l")
        self.assertEqual(len(found), 1, [f.render() for f in found])
        self.assertEqual(found[0].task, "T2")
        self.assertEqual(found[0].level, rc.WARN)
        self.assertIn("4 open rows share the shape 'handler <x>' (T2 to T5)", found[0].message)
        self.assertIn("sdd-tasks § 2", found[0].message)

    def test_three_rows_of_one_shape_are_not_a_set(self):
        self.assertEqual(self.rules(self.lint([contract()] + [handler(n) for n in range(2, 5)]), "l"), [])

    def test_a_settled_row_is_not_counted_so_a_recut_set_keeps_its_history(self):
        rows = [contract(), handler(2, status="done"), handler(3, status="cancelled"), handler(4, status="doing")]
        rows += [handler(n) for n in range(5, 8)]
        self.assertEqual(self.rules(self.lint(rows, all_rows=True), "l"), [])

    def test_distinct_titles_are_never_a_set(self):
        titles = ["Quest log and accept", "Wild-defeat progress", "Quest abandon and deliver", "Reward grant",
                  "Content image build", "Signing and publish", "Boot manifest format"]
        rows = [(f"T{n}", f"{title}: Plan § Design", FILES, PROOF, "—", "todo") for n, title in enumerate(titles, 1)]
        self.assertEqual(self.rules(self.lint(rows), "l"), [])

    def test_a_title_with_no_item_token_is_never_a_set(self):
        rows = [(f"T{n}", "Server E2E of the rules: Plan § Tests", FILES, PROOF, "—", "todo") for n in range(1, 7)]
        self.assertEqual(self.rules(self.lint(rows), "l"), [])

    def test_sequence_steps_row_ids_and_bare_items_are_never_a_set(self):
        for titles in (["Phase 1: build", "Phase 2: build", "Phase 3: build", "Phase 4: build"],
                       ["Step 1 of the import", "Step 2 of the import", "Step 3 of the import", "Step 4 of the import"],
                       ["Wire T1 into the server", "Wire T2 into the server", "Wire T3 into the server",
                        "Wire T4 into the server"],
                       ["`a0`: x", "`a1`: x", "`a2`: x", "`a3`: x"],
                       ["0", "1", "2", "3"]):
            rows = [(f"T{n}", title, FILES, PROOF, "—", "todo") for n, title in enumerate(titles, 1)]
            self.assertEqual(self.rules(self.lint(rows), "l"), [], titles)

    def test_a_set_that_starts_in_a_closed_block_is_reported_on_its_first_open_block_row(self):
        text = versioned("FEAT-900", [handler(1), handler(2)], [handler(3), handler(4), handler(5)])
        (self.spec / "features" / "FEAT-900.md").write_text(text, encoding="utf-8")
        parsed = rc.parse_feat(self.spec / "features" / "FEAT-900.md", self.cfg)
        found = self.rules(rc.lint(parsed, self.cfg)[0], "l")
        self.assertEqual([f.task for f in found], ["T3"])
        self.assertIn("5 open rows share the shape 'handler <x>' (T1 to T5)", found[0].message)

    def test_a_set_whose_first_row_fails_rule_a_is_reported_on_the_next(self):
        """#431: rule a stops the other rules on its row, so rule l moves to the first row they run on."""
        text = feat_text("FEAT-900", [contract()] + [handler(n) for n in range(2, 7)])
        line = next(x for x in text.splitlines() if x.startswith("| T2 |"))
        path = self.spec / "features" / "FEAT-900.md"
        path.write_text(text.replace(line, line.replace("| Low |", "| Huge |", 1)), encoding="utf-8")
        found = rc.lint(rc.parse_feat(path, self.cfg), self.cfg)[0]
        self.assertTrue(any(f.rule == "a" and f.task == "T2" for f in found), [f.render() for f in found])
        self.assertEqual([f.task for f in found if f.rule == "l"], ["T3"])

    def test_a_numbered_title_is_a_set_too(self):
        rows = [(f"T{n}", f"Describe ENB-00{n} (module {n}) on the skeleton: Plan § Design", FILES, PROOF, "—",
                 "todo") for n in range(1, 6)]
        found = self.rules(self.lint(rows), "l")
        self.assertEqual(len(found), 1)
        self.assertIn("'describe <n>'", found[0].message)

    def test_an_edge_between_two_rows_of_a_set_is_reported_on_the_dependent(self):
        rows = [contract()] + [handler(n) for n in range(2, 6)]
        rows[3] = handler(4, depends="T3")
        found = self.rules(self.lint(rows), "m")
        self.assertEqual([(f.task, f.cell) for f in found], [("T4", "Depends on")])
        self.assertIn("T3 is a row of the same set", found[0].message)

    def test_every_row_depending_on_the_contract_row_is_clean(self):
        self.assertEqual(self.rules(self.lint([contract()] + [handler(n) for n in range(2, 8)]), "m"), [])

    def test_strict_promotes_both_rules_to_fail_and_the_exit_code_follows(self):
        rows = [contract()] + [handler(n) for n in range(2, 6)]
        rows[3] = handler(4, depends="T3")
        (self.spec / "features" / "FEAT-900.md").write_text(feat_text("FEAT-900", rows), encoding="utf-8")
        code, out, _ = run("check", "--spec", str(self.spec), "FEAT-900")
        self.assertEqual(code, 0, out)
        self.assertIn("WARN: FEAT-900 T2: Task 4 open rows share the shape", out)
        code, out, _ = run("check", "--spec", str(self.spec), "--strict", "FEAT-900")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL: FEAT-900 T2: Task 4 open rows share the shape", out)
        self.assertIn("FAIL: FEAT-900 T4: Depends on T3 is a row of the same set", out)


if __name__ == "__main__":
    unittest.main()
