"""row_checks under sdd.passes (KIT-094): a greybox version block's rows are exempt from rule j, since a greybox of
placeholder art has no mock to match and the owner's playtest line is its acceptance; `passes: []` changes nothing."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): load_config starts git
COVERS = ("platforms/ci/validations/row_checks.py", "platforms/ci/validations/check_spec.py")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import row_checks as rc  # noqa: E402
from test_row_checks import HEADER, PROFILE, make_repo, row_line  # noqa: E402

VISUAL = "`frontend/ui/battle/dash.tscn`, `frontend/tests/battle/**`"
PROOF = "`godot --headless --quit`"


def versioned(rows_by_block):
    """A FEAT body with `## Versions` holding one `### <name>` block per (name, rows) pair, KIT-096's layout."""
    blocks = "".join(f"### {name}\n\nStatus: planned\nScope: REQ-F-001\n\n#### Tasks\n<!-- | T99 | in a comment | -->\n\n"
                     f"{HEADER}\n" + "\n".join(rows) + "\n\n#### Closure\n\n" for name, rows in rows_by_block)
    return f"# FEAT-901\n\n## Plan\n\n| T50 | not a row of a block |\n\n## Versions\n\n{blocks}## History\n\n- x\n"


def line(tid, files=VISUAL, proof=PROOF):
    return row_line(tid, "Dash", files, proof, "—", "todo")


class PassRows(unittest.TestCase):
    def test_each_block_row_takes_the_pass_its_heading_ends_with(self):
        text = versioned([("0.2.0", [line("T1")]), ("0.3 greybox", [line("T2"), line("T3")]),
                          ("0.3 polish", [line("T4")]), ("M5 polish", [line("T5")])])
        self.assertEqual(rc.pass_rows(text), {"T2": "greybox", "T3": "greybox", "T4": "polish", "T5": "polish"})

    def test_a_feat_without_versions_has_no_pass_rows(self):
        self.assertEqual(rc.pass_rows(f"## Tasks\n\n{HEADER}\n{line('T1')}\n"), {})

    def test_a_word_that_names_no_pass_is_no_pass(self):
        self.assertEqual(rc.pass_rows(versioned([("0.3 greyboxing", [line("T1")]), ("greybox 0.3", [line("T2")])])),
                         {})


class Base(unittest.TestCase):
    profile = PROFILE

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        spec = make_repo(self.root, rows=[], profile=self.profile)
        self.cfg = rc.load_config(spec)

    def row(self, pass_name):
        row = rc.parse_rows("FEAT-901", f"## Tasks\n\n{HEADER}\n{line('T1')}\n", self.cfg)[0]
        rc.mark_passes([row], versioned([(f"0.3 {pass_name}", [line("T1")])]))
        return row


class WithPasses(Base):
    profile = PROFILE.replace("sdd:\n", "sdd:\n  passes: [greybox, polish]\n")

    def test_the_profile_key_reaches_the_row_check(self):
        self.assertEqual(self.cfg.params.get("passes"), ["greybox", "polish"])

    def test_a_greybox_row_on_a_visual_path_needs_no_evidence_clause(self):
        row = self.row("greybox")
        self.assertEqual(row.pass_name, "greybox")
        self.assertEqual(rc.rule_j(row, self.cfg), [])

    def test_rule_j_reads_the_row_pass(self):
        row = rc.parse_rows("FEAT-901", f"## Tasks\n\n{HEADER}\n{line('T1')}\n", self.cfg)[0]
        row.pass_name = "greybox"
        self.assertEqual(rc.rule_j(row, self.cfg), [])

    def test_a_polish_row_still_needs_its_evidence_clause(self):
        got = rc.rule_j(self.row("polish"), self.cfg)
        self.assertEqual([f.rule for f in got], ["j"])
        self.assertIn("no `evidence:` clause", got[0].message)


class Cli(Base):
    """`row_checks.py check` on a versioned FEAT: parse_rows reads the open block's rows (KIT-096), and rule j skips
    them when that block is the greybox one."""
    profile = PROFILE.replace("sdd:\n", "sdd:\n  passes: [greybox, polish]\n")

    def check(self, blocks):
        text = ("---\nid: FEAT-902\ntitle: \"Dash\"\nstatus: planned\nrequirements: []\ncreated: \"2026-11-17\"\n"
                "---\n\n") + versioned(blocks)
        (self.root / "docs/spec/features/FEAT-902.md").write_text(text, encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = rc.main(["check", "--spec", str(self.root / "docs/spec"), "FEAT-902"])
        return code, out.getvalue()

    def test_a_greybox_open_block_row_gets_no_rule_j_warning(self):
        code, out = self.check([("0.3 greybox", [line("T1")])])
        self.assertEqual(code, 0, out)
        self.assertIn("row-checks: 1 rows", out)
        self.assertNotIn("[j]", out)

    def test_the_same_row_in_a_polish_open_block_is_warned(self):
        code, out = self.check([("0.3 greybox", [line("T1").replace("| todo |", "| done |")]),
                                ("0.3 polish", [line("T2")])])
        self.assertEqual(code, 0, out)
        self.assertIn("row-checks: 1 rows", out)
        self.assertIn("FEAT-902 T2: Files entry 'client/ui/battle/dash.tscn' is a visual or motion path", out)
        self.assertIn("[j]", out)


class WithoutPasses(Base):
    """`passes: []`, the default: a block named greybox is an ordinary block, and rule j holds it as before."""

    def test_the_default_is_one_pass(self):
        self.assertEqual(self.cfg.params.get("passes"), [])

    def test_a_greybox_block_row_still_needs_its_evidence_clause(self):
        got = rc.rule_j(self.row("greybox"), self.cfg)
        self.assertEqual([f.rule for f in got], ["j"])

    def test_a_row_outside_any_block_has_no_pass(self):
        row = rc.parse_rows("FEAT-901", f"## Tasks\n\n{HEADER}\n{line('T1')}\n", self.cfg)[0]
        self.assertEqual(getattr(row, "pass_name", ""), "")


if __name__ == "__main__":
    unittest.main()
