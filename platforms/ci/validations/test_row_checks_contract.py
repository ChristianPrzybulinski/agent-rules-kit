"""row_checks rules j and k (KIT-073): evidence clauses of visual rows and one regeneration row per contract consumer.

Ported from a consumer project's row linter suite with neutral names (components `backend` -> server/, `frontend` ->
client/, contract folder `protocol/`).
"""
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/row_checks.py", "platforms/ci/validations/pr_gates.py",
          "platforms/ci/validations/check_spec.py")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import row_checks as rc  # noqa: E402
from test_row_checks import HEADER, SPEC_MD, make_repo, row_line  # noqa: E402

EVIDENCE_LOGIN = "evidence: screen `login` states `form`, `code`"
LOGIN_FILES = ["frontend/ui/account/login_screen.gd", "frontend/ui/account/login_screen.tscn",
               "frontend/features/ui/account/**", "frontend/tests/account/**", "frontend/i18n/en.csv"]
PROOF = "`python3 -m unittest discover -s tools/demo/tests`"


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = rc.main(list(argv))
    return code, out.getvalue()


class Base(unittest.TestCase):
    spec_md = SPEC_MD

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.spec = make_repo(self.root, spec_md=self.spec_md, rows=[])
        self.cfg = rc.load_config(self.spec)

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *args], check=True,
                       capture_output=True)

    def main_has(self, paths):
        """origin/main of the fixture repository holds these catalog files."""
        for rel in paths:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text("{}\n", encoding="utf-8")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("commit", "-qm", "main")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.cfg = rc.load_config(self.spec)

    def row(self, proof, files=(), task="T1", depends="—", status="todo"):
        line = row_line(task, "Task", " ".join(f"`{f}`" for f in files), proof, depends, status)
        return rc.parse_rows("FEAT-901", f"## Tasks\n\n{HEADER}\n{line}\n", self.cfg)[0]


class RuleJ(Base):
    def test_a_visual_row_without_a_clause_is_one_warn(self):
        got = rc.rule_j(self.row(PROOF, LOGIN_FILES), self.cfg)
        self.assertEqual([(f.cell, f.level) for f in got], [("Files", "WARN")])
        self.assertIn("client/ui/account/login_screen.tscn", got[0].message)
        self.assertEqual(len(rc.rule_j(self.row("`godot --headless --quit`", ["frontend/features/ui/hud/**"]),
                                       self.cfg)), 1)

    def test_the_clause_is_clean_when_main_has_the_catalog_entry(self):
        self.main_has(["client/tests/evidence/screens/login.json"])
        self.assertEqual(rc.rule_j(self.row(f"{PROOF}; {EVIDENCE_LOGIN}", LOGIN_FILES), self.cfg), [])

    def test_a_catalog_id_missing_on_main_is_one_warn_unless_files_cover_it(self):
        self.main_has(["client/tests/evidence/screens/other.json", "client/tests/evidence/motion/walk.gd"])
        got = rc.rule_j(self.row(EVIDENCE_LOGIN, ["frontend/ui/account/login_screen.tscn"]), self.cfg)
        self.assertEqual([f.level for f in got], [("WARN")])
        self.assertIn("client/tests/evidence/screens/login.json", got[0].message)
        self.assertEqual(rc.rule_j(self.row(EVIDENCE_LOGIN, ["frontend/tests/evidence/screens/**"]), self.cfg), [])
        self.assertEqual(rc.rule_j(self.row("evidence: motion `walk`"), self.cfg), [])
        self.assertEqual(len(rc.rule_j(self.row("evidence: motion `run`"), self.cfg)), 1)

    def test_server_rows_and_ignored_paths_have_no_finding(self):
        self.assertEqual(rc.rule_j(self.row("`./mvnw -q verify`", ["backend/src/main/java/A.java"]), self.cfg), [])
        self.assertEqual(rc.rule_j(self.row("`godot --headless --quit`", ["frontend/tests/hud/a.tscn"]), self.cfg), [])

    def test_each_clause_error_is_one_warn(self):
        got = rc.rule_j(self.row("evidence: screen `Login`; evidence: screen login; evidence: motion `a` states `b`"),
                        self.cfg)
        self.assertEqual([f.level for f in got], ["WARN"] * 3)
        self.assertTrue(all("evidence: bad clause" in f.message for f in got))

    def test_without_a_visual_approver_rule_j_is_off(self):
        cfg = rc.load_config(make_repo(self.root, spec_md=SPEC_MD.replace("visual_approval: owner",
                                                                           "visual_approval: none"), rows=[]))
        self.assertEqual(rc.rule_j(self.row(PROOF, LOGIN_FILES), cfg), [])


class RuleE(Base):
    def test_an_evidence_clause_beside_a_command_is_neither_prose_nor_a_command(self):
        self.assertEqual(rc.rule_e(self.row("`godot --path . --headless --quit`; " + EVIDENCE_LOGIN), self.cfg), [])

    def test_a_proof_of_evidence_clauses_only_fails_with_rule_j_on_or_off(self):
        """#270: such a row has no runnable proof, and with visual_approval none rule j never looks at it."""
        off = rc.load_config(make_repo(self.root, spec_md=SPEC_MD.replace("visual_approval: owner",
                                                                           "visual_approval: none"), rows=[]))
        for cfg in (self.cfg, off):
            got = rc.rule_e(self.row(f"{EVIDENCE_LOGIN}; evidence: motion `walk`"), cfg)
            self.assertEqual([(f.rule, f.level) for f in got], [("e", "FAIL")])
            self.assertIn("only evidence: clauses", got[0].message)
            self.assertIn("row_checks.evidence_only", got[0].message)


class EvidenceOnlyAllowed(Base):
    spec_md = SPEC_MD.replace("  row_checks:\n", "  row_checks:\n    evidence_only: true\n")

    def test_the_parameter_lets_an_evidence_only_proof_pass(self):
        self.assertTrue(self.cfg.evidence_only)
        self.assertEqual(rc.rule_e(self.row(EVIDENCE_LOGIN), self.cfg), [])
        got = rc.rule_e(self.row("reviewed by a human"), self.cfg)
        self.assertEqual([(f.rule, f.level) for f in got], [("e", "WARN")])


class CatalogCli(Base):
    def write_feat(self):
        line = row_line("T1", "Client HUD", "`frontend/features/ui/hud/**`, `frontend/tests/hud/**`",
                        f"`godot --path . --headless --quit`; {EVIDENCE_LOGIN}", "—", "todo")
        (self.spec / "features" / "FEAT-901.md").write_text(f"# FEAT-901\n\n## Tasks\n\n{HEADER}\n{line}\n",
                                                            encoding="utf-8")

    def test_without_origin_main_the_catalog_check_is_skipped_and_the_summary_says_so(self):
        self.write_feat()
        code, out = run("check", "--spec", str(self.spec), "FEAT-901")
        self.assertEqual(code, 0)
        self.assertEqual(out, "row-checks: rule j catalog check skipped: no origin/main in this repository\n"
                              "row-checks: 1 rows, 0 fail, 0 warn\n")

    def test_origin_main_runs_the_catalog_check(self):
        self.write_feat()
        self.main_has(["client/tests/evidence/screens/other.json"])
        code, out = run("check", "--spec", str(self.spec), "FEAT-901")
        self.assertEqual(code, 0)
        self.assertIn("has no catalog file client/tests/evidence/screens/login.json on origin/main", out)
        self.assertNotIn("skipped", out)
        self.assertTrue(out.endswith("row-checks: 1 rows, 0 fail, 1 warn\n"), out)


KPROOF = "`python3 -m unittest discover -s tools/demo/tests`"
CONTRACT = ("T1", "Contract", "`protocol/schemas/x.json`", KPROOF, "—", "todo")
SERVER = ("T2", "Server", "`server/src/main/java/ws/ErrorCode.java` `server/src/main/java/ws/MessageTypes.java`",
          KPROOF, "T1", "todo")
CLIENT = ("T3", "Client", "`client/app/network/protocol.gd` `client/tests/i18n/**`", KPROOF, "T1", "todo")
DOCS = ("T4", "Docs", "`tools/demo/README.md`", KPROOF, "T1", "todo")


def with_status(row, status):
    return row[:5] + (status,)


def with_depends(row, depends):
    return row[:4] + (depends, row[5])


def with_files(row, files):
    return row[:2] + (files,) + row[3:]


class RuleK(Base):
    def k(self, rows, all_rows=False):
        text = f"## Tasks\n\n{HEADER}\n" + "\n".join(row_line(*r) for r in rows) + "\n"
        parsed = rc.parse_rows("FEAT-901", text, self.cfg)
        return [f.render() for f in rc.lint(parsed, self.cfg, all_rows=all_rows)[0] if f.rule == "k"]

    def missing(self, consumer, task="T1"):
        return f"WARN: FEAT-901 {task}: contract row {task} has no {consumer} regeneration row [k]"

    def test_a_contract_row_without_consumer_rows_gets_two_warns(self):
        self.assertEqual(self.k([CONTRACT, DOCS]), [self.missing("backend"), self.missing("frontend")])

    def test_both_consumer_rows_clear_the_finding(self):
        self.assertEqual(self.k([CONTRACT, SERVER, CLIENT]), [])

    def test_one_missing_consumer_gets_one_warn(self):
        self.assertEqual(self.k([CONTRACT, SERVER]), [self.missing("frontend")])

    def test_no_contract_row_gets_no_finding(self):
        self.assertEqual(self.k([DOCS, SERVER]), [])

    def test_a_done_contract_row_gets_no_finding(self):
        self.assertEqual(self.k([with_status(CONTRACT, "done"), DOCS], all_rows=True), [])

    def test_a_doing_contract_row_is_checked(self):
        self.assertEqual(self.k([with_status(CONTRACT, "doing"), DOCS], all_rows=True),
                         [self.missing("backend"), self.missing("frontend")])

    def test_done_or_inactive_consumer_rows_do_not_count(self):
        for status in ("done", "blocked", "cancelled"):
            with self.subTest(status=status):
                self.assertEqual(self.k([CONTRACT, with_status(SERVER, status), with_status(CLIENT, status)]),
                                 [self.missing("backend"), self.missing("frontend")])

    def test_a_new_contract_cannot_reuse_done_consumers_of_an_older_contract(self):
        rows = [with_status(CONTRACT, "done"), with_status(SERVER, "done"), with_status(CLIENT, "done"),
                ("T9",) + CONTRACT[1:]]
        self.assertEqual(self.k(rows), [self.missing("backend", "T9"), self.missing("frontend", "T9")])

    def test_open_consumers_without_a_dependency_on_the_contract_do_not_count(self):
        for depends in ("—", "T4", "T10", "FEAT-999 T1", "FEAT-999 T4, T1"):
            with self.subTest(depends=depends):
                self.assertEqual(self.k([CONTRACT, with_depends(SERVER, depends), with_depends(CLIENT, depends),
                                         DOCS]), [self.missing("backend"), self.missing("frontend")])

    def test_doing_consumers_count(self):
        self.assertEqual(self.k([CONTRACT, with_status(SERVER, "doing"), with_status(CLIENT, "doing")]), [])

    def test_contract_dependency_can_be_qualified_or_part_of_a_list(self):
        for depends in ("FEAT-901 T1", "T4, T1", "FEAT-999 T4; T1"):
            with self.subTest(depends=depends):
                self.assertEqual(self.k([CONTRACT, with_depends(SERVER, depends), with_depends(CLIENT, depends),
                                         DOCS]), [])

    def test_only_the_consumer_without_an_open_dependent_row_gets_a_warn(self):
        self.assertEqual(self.k([CONTRACT, with_status(SERVER, "done"), CLIENT]), [self.missing("backend")])
        self.assertEqual(self.k([CONTRACT, SERVER, with_depends(CLIENT, "—")]), [self.missing("frontend")])

    def test_each_contract_needs_its_own_consumer_dependencies(self):
        other = ("T5",) + CONTRACT[1:]
        self.assertEqual(self.k([CONTRACT, other, SERVER, CLIENT]),
                         [self.missing("backend", "T5"), self.missing("frontend", "T5")])
        self.assertEqual(self.k([CONTRACT, other, with_depends(SERVER, "T1, T5"), with_depends(CLIENT, "T1, T5")]),
                         [])

    def test_a_contract_row_covering_both_tables_is_its_own_regeneration(self):
        schema, server, client = ("`protocol/schemas/x.json`", "`backend/src/main/java/ws/ErrorCode.java`",
                                  "`frontend/app/network/protocol.gd`")
        self.assertEqual(self.k([with_files(CONTRACT, f"{schema} {server} {client}"), DOCS]), [])
        self.assertEqual(self.k([with_files(CONTRACT, f"{schema} {server}"), DOCS]), [self.missing("frontend")])

    def test_a_row_owning_a_file_beside_the_table_is_not_a_regeneration_row(self):
        network = with_files(CLIENT, "`client/app/network/network.gd`")
        self.assertEqual(self.k([CONTRACT, SERVER, network]), [self.missing("frontend")])

    def test_a_contract_row_spanning_components_warns_instead_of_failing_scope(self):
        files = "`protocol/**` `server/src/main/java/ws/ErrorCode.java` `server/src/main/java/ws/MessageTypes.java` " \
                "`client/app/network/protocol.gd`"
        text = f"## Tasks\n\n{HEADER}\n" + row_line("T1", "Contract", files, "`python3 ../tools/gen.py --check`",
                                                     "—", "todo") + "\n"
        got = rc.lint(rc.parse_rows("FEAT-901", text, self.cfg), self.cfg, strict=True)[0]
        self.assertEqual([(f.rule, f.level) for f in got], [("b", "WARN")])
        self.assertIn("split the row", got[0].message)
        self.assertIn("contract row", got[0].message)


class Off(Base):
    spec_md = "---\nproject: \"fixture\"\nversion: \"0.1.0\"\nupdated: \"2026-11-15\"\n---\n"

    def test_without_the_protocol_key_rules_h_and_k_are_off(self):
        rows = rc.parse_rows("FEAT-901", f"## Tasks\n\n{HEADER}\n" + row_line(
            "T1", "sends `ghost_msg`", "`protocol/schemas/x.json`", KPROOF, "—", "todo") + "\n", self.cfg)
        got = rc.lint(rows, self.cfg)[0]
        self.assertEqual([f.rule for f in got if f.rule in "hk"], [])


if __name__ == "__main__":
    unittest.main()
