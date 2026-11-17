"""row_checks.py on a versioned FEAT (KIT-096): the rows live under `## Versions` → `### <version>` → `#### Tasks`, read
through check_spec.task_sections. The open (last) block's rows are linted; every block's rows answer a `Depends on`. A
FEAT with `## Tasks` is read as before (test_row_checks.py)."""
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/row_checks.py", "platforms/ci/validations/check_spec.py")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_spec  # noqa: E402
import row_checks as rc  # noqa: E402
from test_row_checks import HEADER, ROWS, make_repo, row_line, run  # noqa: E402


def versioned(fid, closed, open_rows, comment=""):
    first = "\n".join(row_line(*r) for r in closed)
    second = "\n".join(row_line(*r) for r in open_rows)
    return (f"---\nid: {fid}\ntitle: \"Synthetic versioned fixture\"\nstatus: planned\nrequirements: []\n"
            f"created: \"2026-11-17\"\n---\n\n# {fid}\n\n## Versions\n\n### 0.1.0\n\nStatus: delivered\nScope: —\n\n"
            f"#### Tasks\n\n{HEADER}\n{first}\n\n#### Closure\n\n- closed.\n\n### 0.2.0\n\nStatus: planned\nScope: —\n\n"
            f"#### Tasks\n{comment}\n{HEADER}\n{second}\n\n#### Closure\n\n## History\n\n- 2026-11-17 plan: rows.\n")


def done(row):
    return row[:5] + ("done",)


class VersionedRows(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.spec = make_repo(self.root)
        self.cfg = rc.load_config(self.spec)

    def write(self, text, fid="FEAT-903"):
        (self.spec / "features" / f"{fid}.md").write_text(text, encoding="utf-8")

    def test_the_open_block_rows_are_linted(self):
        bad = ("T6",) + ROWS[5][1:]
        self.write(versioned("FEAT-903", [done(ROWS[0])], [bad]))
        code, out, _ = run("check", "--spec", str(self.spec), "FEAT-903")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL: FEAT-903 T6: Proof of completion clause 1 'docker exec demo ls'", out)
        self.assertNotIn("no Tasks table", out)

    def test_a_clean_open_block_passes_and_closed_rows_answer_depends_on(self):
        good = ("T2",) + ROWS[0][1:4] + ("T1", "todo")
        self.write(versioned("FEAT-903", [done(ROWS[0])], [good]))
        rows = rc.parse_feat(self.spec / "features" / "FEAT-903.md", self.cfg)
        self.assertEqual([r.task_id for r in rows], ["T2"])
        self.assertEqual(sorted(rows[0].siblings), ["T1", "T2"])
        code, out, _ = run("check", "--spec", str(self.spec), "FEAT-903")
        self.assertEqual(code, 0, out)
        self.assertIn("row-checks: 1 rows, 0 fail, 0 warn", out)

    def test_an_open_block_without_tasks_lints_no_closed_rows(self):
        bad = ("T6",) + ROWS[5][1:5] + ("done",)
        text = versioned("FEAT-903", [bad], [ROWS[0]])
        text = text.split("### 0.2.0")[0] + "### 0.2.0\n\nStatus: proposed\nScope: —\n\n## History\n"
        self.write(text)
        self.assertIsNone(rc.parse_feat(self.spec / "features" / "FEAT-903.md", self.cfg))
        code, out, _ = run("check", "--spec", str(self.spec), "--all-rows", "FEAT-903")
        self.assertEqual(code, 0, out)
        self.assertIn("WARN: FEAT-903: no Tasks table", out)
        self.assertNotIn("T6", out)

    def test_a_row_inside_a_comment_is_not_a_row(self):
        hidden = "<!-- " + row_line(*(("T7",) + ROWS[5][1:])) + " -->"
        good = ("T2",) + ROWS[0][1:]
        self.write(versioned("FEAT-903", [done(ROWS[0])], [good], comment=hidden))
        rows = rc.parse_feat(self.spec / "features" / "FEAT-903.md", self.cfg)
        self.assertEqual([r.task_id for r in rows], ["T2"])


class TaskSections(unittest.TestCase):
    def test_old_shape_is_the_tasks_section(self):
        text = f"# F\n\n## Tasks\n\n{HEADER}\n{row_line(*ROWS[0])}\n\n## History\n"
        sections = check_spec.task_sections(text)
        self.assertEqual([(s[0], s[1]) for s in sections], [(None, 4)])
        self.assertTrue(sections[0][2].startswith("| ID | Task |"))

    def test_versioned_shape_is_one_section_per_block(self):
        sections = check_spec.task_sections(versioned("FEAT-903", [done(ROWS[0])], [ROWS[0]]))
        self.assertEqual([s[0] for s in sections], ["0.1.0", "0.2.0"])
        for name, first, body in sections:
            self.assertTrue(body.startswith("| ID | Task |"), name)

    def test_no_tasks_is_empty(self):
        self.assertEqual(check_spec.task_sections("# F\n\n## History\n"), [])


if __name__ == "__main__":
    unittest.main()
