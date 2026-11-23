"""row_checks tests (KIT-073): one finding per broken rule of a synthetic FEAT, clean rows, components, exit codes.

Ported from a consumer project's row linter suite with neutral names: the component map sends the old repository
names `backend` and `frontend` to the `server/` and `client/` folders of one repository.
"""
import contextlib
import dataclasses
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/row_checks.py", "platforms/ci/validations/pr_gates.py",
          "platforms/ci/validations/check_spec.py")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import row_checks as rc  # noqa: E402
import pr_gates  # noqa: E402

HEADER = ("| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Model | Wave | Item |\n"
          "|---|---|---|---|---|---|---|---|---|---|---|")

SPEC_MD = """\
---
project: "fixture"
version: "0.1.0"
updated: "2026-11-15"
---

# Fixture spec
"""

# The fixture's profile (KIT-087 P4: .ai-kit.yaml is the only home of the sdd and evidence keys).
PROFILE = """\
evidence:
  visual_approval: owner
sdd:
  tracker: github
  components: {project: ".", backend: server, frontend: client}
  row_checks:
    gates: tools/gates.json
    tests:
      - {code: ["server/src/main/**"], tests: "server/src/test/**", sample: "server/src/test/java/Sample.java"}
      - {code: ["client/**/*.gd", "client/**/*.tscn"], exclude: ["**/tests/**", "client/.*", "client/.*/**"], tests: "client/tests/**", sample: "client/tests/sample.gd"}
      - {code: ["tools/*/**/*.py"], exclude: ["**/tests/**"], tests: "tools/$1/tests/**", sample: "tools/$1/tests/test_sample.py", level: warn}
    assets: {paths: ["client/**"], suffixes: [".tscn", ".tres", ".png", ".csv", ".wav"]}
    protocol: {folder: protocol, schemas: protocol/schemas, consumers: {backend: ["server/src/main/java/ws/MessageTypes.java", "server/src/main/java/ws/ErrorCode.java"], frontend: ["client/app/network/protocol.gd"]}}
    artifacts: tools/artifact-policies.json
    visual: {paths: ["client/**/*.tscn", "client/features/ui/**"], ignore: ["client/tests/**"], catalog: {screen: "client/tests/evidence/screens/$id.json", motion: "client/tests/evidence/motion/$id.gd"}}
"""

GATES = {"owner": "org", "backlog_repo": "docs",
         "proof_allowlist": ["./mvnw", "godot", "python3", "grep", "git", "test", "!", "jq", "docker"],
         "proof_script_runners": {"godot": ["-s", "--script"]},
         "generated_neighbours": [".uid", ".import", ".translation"]}

ARTIFACTS = [{"pattern": "*.translation", "dec": "DEC-010", "policy": "committed with its source"},
             {"pattern": "docs/spec/traceability.md", "dec": "DEC-013", "policy": "generated, never edited by hand"}]

# (id, task, files, proof, depends, status) — Covers CA-1, Complexity Low, Model small, Wave 1, Item —
ROWS = [
    ("T1", "Good row: every rule passes", "`tools/demo/demo.py`, `tools/demo/tests/test_demo.py`",
     "`python3 -m unittest discover -s tools/demo/tests`; `grep -q demo tools/demo/demo.py`", "—", "todo"),
    ("T2", "Rule a: status outside the enum", "`tools/demo/demo.py`, `tools/demo/tests/test_demo.py`",
     "`grep -q demo tools/demo/demo.py`", "—", "ready"),
    ("T3", "Rule b: unrooted Files entry", "`nowhere/demo/**`", "`test -f README.md`", "—", "todo"),
    ("T4", "Rule c: code without a test path", "`tools/demo/demo.py`",
     "`python3 -m unittest discover -s tools/demo/tests`", "—", "todo"),
    ("T5", "Rule d: scene without a covering glob", "`frontend/scenes/a.tscn`, `frontend/tests/a_test.gd`",
     "`godot --path . --headless --quit`", "—", "todo"),
    ("T6", "Rule e: refused construct", "`tools/demo/demo.py`, `tools/demo/tests/test_demo.py`",
     "`docker exec demo ls`", "—", "todo"),
    ("T7", "Rule e: nothing command-shaped", "`tools/demo/demo.py`, `tools/demo/tests/test_demo.py`",
     "reviewed by a human", "—", "todo"),
    ("T8", "Manual check backed by an automated one", "`tools/demo/demo.py`, `tools/demo/tests/test_demo.py`",
     "`grep -q demo tools/demo/demo.py`; manual: the mail capture shows the mail", "—", "todo"),
    ("T9", "Rule f: dependency is not in the table", "`tools/demo/demo.py`, `tools/demo/tests/test_demo.py`",
     "`grep -q demo tools/demo/demo.py`", "T99", "todo"),
    ("T10", "Rule g: proof names a path outside Files", "`tools/demo/demo.py`, `tools/demo/tests/test_demo.py`",
     "`grep -q demo tools/demo/other.py`", "—", "todo"),
    ("T11", "Rule h: sends `ghost_msg` to the client", "`tools/demo/demo.py`, `tools/demo/tests/test_demo.py`",
     "`grep -q demo tools/demo/demo.py`", "—", "todo"),
    ("T12", "Done row with a defect is skipped", "`tools/demo/demo.py`, `tools/demo/tests/test_demo.py`",
     "`docker exec demo ls`", "—", "done"),
    ("T13", "Rule c on a server row is a FAIL", "`backend/src/main/java/demo/**`", "`./mvnw -q verify`", "—",
     "todo"),
    ("T14", "Commit or git-ignore the generated `i18n/en.en.translation`", "`frontend/.gitignore`, "
     "`frontend/i18n/**`, `frontend/tests/i18n/**`", "`grep -q en client/.gitignore`", "—", "todo"),
    ("T15", "Keep `i18n/en.en.translation` committed with its source (DEC-010)", "`frontend/.gitignore`, "
     "`frontend/i18n/**`, `frontend/tests/i18n/**`", "`git grep -q en .gitignore`", "—", "todo"),
    ("T16", "Add strings to `i18n/en.csv` and extend the key test", "`frontend/i18n/**`, `frontend/tests/i18n/**`",
     "`godot --path . --headless -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests/i18n -c`", "—", "todo"),
    ("T17", "Regenerate `docs/spec/traceability.md` by hand", "`docs/spec/traceability.md`",
     "`python3 tools/trace/trace.py check`", "—", "todo"),
    ("T18", "Rule h: the roster maps `user` → `self`, a value map", "`tools/demo/demo.py`, "
     "`tools/demo/tests/test_demo.py`", "`grep -q demo tools/demo/demo.py`", "—", "todo"),
    ("T19", "Rule h: replies -> and later the `cfg_log_format` flag applies", "`tools/demo/demo.py`, "
     "`tools/demo/tests/test_demo.py`", "`grep -q demo tools/demo/demo.py`", "—", "todo"),
    ("T20", "Rule h: on `hello` → `ghost_reply` when the client connects", "`tools/demo/demo.py`, "
     "`tools/demo/tests/test_demo.py`", "`grep -q demo tools/demo/demo.py`", "—", "todo"),
    ("T21", "Rule h: sends `a_msg`, `b_msg` and `c_msg` to the client", "`tools/demo/demo.py`, "
     "`tools/demo/tests/test_demo.py`", "`grep -q demo tools/demo/demo.py`", "—", "todo"),
    ("T22", "Rule d: a listed generated neighbour", "`frontend/scenes/**`, `frontend/scenes/a.tscn.uid`, "
     "`frontend/tests/a_test.gd`", "`godot --path . --headless --quit`", "—", "todo"),
]


def row_line(tid, task, files, proof, depends, status, complexity="Low", model="small", wave="1", item="—"):
    proof = proof.replace("|", "\\|")
    return f"| {tid} | {task} | {files} | {proof} | CA-1 | {depends} | {status} | {complexity} | {model} | {wave} | {item} |"


def feat_text(fid, rows, header=HEADER):
    body = "\n".join(row_line(*r) for r in rows)
    return (f"---\nid: {fid}\ntitle: \"Synthetic fixture\"\nstatus: planned\nrequirements: []\n"
            f"created: \"2026-11-15\"\n---\n\n# {fid}\n\n## Tasks\n\n{header}\n{body}\n\n## History\n\n"
            f"- 2026-11-15 plan: rows.\n")


def make_repo(root, spec_md=SPEC_MD, rows=ROWS, fid="FEAT-900", profile=PROFILE):
    """A repository with the fixture spec, its profile, gates, registry, protocol schemas and component folders."""
    files = {
        "docs/spec/spec.md": textwrap.dedent(spec_md),
        ".ai-kit.yaml": profile,
        f"docs/spec/features/{fid}.md": feat_text(fid, rows),
        "tools/gates.json": json.dumps(GATES),
        "tools/artifact-policies.json": json.dumps(ARTIFACTS),
        "protocol/schemas/hello.json": "{}",
        "server/pom.xml": "<project/>",
        "client/project.godot": "[application]",
        "README.md": "# fixture\n",
        ".gitattributes": "* text=auto\n",
    }
    for rel, text in files.items():
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return Path(root) / "docs/spec"


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = rc.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.spec = make_repo(self.root)
        self.cfg = rc.load_config(self.spec)

    def findings(self, strict=False, all_rows=False, fid="FEAT-900"):
        rows = rc.parse_feat(self.spec / "features" / f"{fid}.md", self.cfg)
        return rc.lint(rows, self.cfg, strict, all_rows)[0]

    def row(self, *paths, proof="`test -f server/src/main/java/A.java`", depends="—", task="T1", status="todo",
            text="Change code"):
        line = row_line(task, text, ", ".join(f"`{p}`" for p in paths), proof, depends, status)
        return rc.parse_rows("FEAT-901", f"## Tasks\n\n{HEADER}\n{line}\n", self.cfg)[0]


class FixtureRules(Base):
    def by_task(self, **kw):
        out = {}
        for f in self.findings(**kw):
            out.setdefault(f.task, []).append(f)
        return out

    def test_good_rows_have_no_finding(self):
        got = self.by_task()
        for task in ("T1", "T8", "T16", "T18", "T19"):
            self.assertNotIn(task, got, [f.render() for f in got.get(task, [])])

    def test_each_task_reports_its_expected_findings(self):
        expected = {"T2": [("a", "FAIL")], "T3": [("b", "FAIL")], "T4": [("c", "WARN")],
                    "T5": [("d", "WARN"), ("j", "WARN")], "T6": [("e", "FAIL")], "T7": [("e", "WARN")],
                    "T9": [("f", "WARN")], "T10": [("g", "FAIL")], "T11": [("h", "WARN")],
                    "T13": [("c", "FAIL")], "T14": [("i", "WARN")], "T15": [], "T17": [("i", "WARN")],
                    "T20": [("h", "WARN")], "T21": [("h", "WARN")] * 3, "T22": [("d", "WARN")]}
        got = self.by_task()
        expected = {k: v for k, v in expected.items() if v}
        self.assertEqual(set(got), set(expected), {k: [f.render() for f in v] for k, v in got.items()})
        for task, want in expected.items():
            self.assertEqual([(f.rule, f.level) for f in got[task]], want, task)

    def test_rule_h_reads_the_send_run(self):
        got = self.by_task()
        self.assertIn("'ghost_msg'", got["T11"][0].message)
        self.assertIn("'ghost_reply'", got["T20"][0].message)
        self.assertEqual([f.message.split("'")[1] for f in got["T21"]], ["a_msg", "b_msg", "c_msg"])
        self.assertIn("protocol/schemas/ghost_msg.json", got["T11"][0].message)

    def test_rule_d_names_the_glob_or_the_neighbour(self):
        got = self.by_task()
        self.assertIn("exact asset path", got["T5"][0].message)
        self.assertIn("a.tscn.uid", got["T22"][0].message)
        self.assertIn("implicit", got["T22"][0].message)

    def test_done_rows_are_skipped_unless_all_rows(self):
        self.assertNotIn("T12", self.by_task())
        self.assertIn("T12", {f.task for f in self.findings(all_rows=True)})

    def test_strict_promotes_c_and_f(self):
        levels = {f.task: f.level for f in self.findings(strict=True)}
        self.assertEqual((levels["T4"], levels["T9"]), ("FAIL", "FAIL"))
        self.assertEqual(levels["T7"], "WARN")

    def test_malformed_row_is_one_fail_and_skips_other_rules(self):
        rows = rc.parse_rows("FEAT-901", f"## Tasks\n\n{HEADER}\n| T1 | only | three |\n", self.cfg)
        got = rc.lint(rows, self.cfg)[0]
        self.assertEqual([(f.rule, f.level) for f in got], [("a", "FAIL")])
        self.assertIn("3 cells, expected 11", got[0].message)

    def test_rule_a_checks_the_kit_vocabulary(self):
        line = row_line("T1", "x", "`README.md`", "`test -f README.md`", "—", "todo", complexity="Medium",
                        model="opus", wave="one", item="42")
        rows = rc.parse_rows("FEAT-901", f"## Tasks\n\n{HEADER}\n{line}\n", self.cfg)
        got = [f for f in rc.lint(rows, self.cfg)[0] if f.rule == "a"]
        self.assertEqual([f.cell for f in got], ["Complexity", "Model", "Wave", "Item"], [f.render() for f in got])

    def test_a_table_without_the_kit_columns_fails_once_and_the_rows_still_run(self):
        legacy = ("| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Devin model "
                  "| Wave |\n|---|---|---|---|---|---|---|---|---|---|")
        lines = [f"| T{n} | x | `nowhere/x` | `test -f README.md` | CA-1 | — | todo | Low | swe | 1 |" for n in (1, 2)]
        rows = rc.parse_rows("FEAT-901", "## Tasks\n\n" + legacy + "\n" + "\n".join(lines) + "\n", self.cfg)
        got = rc.lint(rows, self.cfg)[0]
        self.assertEqual([(f.rule, f.task) for f in got if f.rule == "a"], [("a", "")])
        self.assertIn("Model, Item", got[0].message)
        self.assertEqual([f.task for f in got if f.rule == "b"], ["T1", "T2"])

    def test_rule_i_names_the_artifact_and_the_decision(self):
        got = {f.task: f for f in self.findings() if f.rule == "i"}
        self.assertEqual(set(got), {"T14", "T17"})
        self.assertIn("DEC-010", got["T14"].message)
        self.assertIn("en.en.translation", got["T14"].message)
        self.assertIn("DEC-013", got["T17"].message)
        self.assertIn("traceability.md", got["T17"].message)


class Predicates(Base):
    def test_escaped_pipe_in_a_cell_is_a_literal_pipe(self):
        cells = rc.split_cells(r"| T1 | x | `a.md` | `! godot --headless --path . --quit 2>&1 \| grep -q 'SCRIPT ERROR'` |")
        self.assertEqual(len(cells), 4)
        self.assertEqual(cells[3], "`! godot --headless --path . --quit 2>&1 | grep -q 'SCRIPT ERROR'`")
        self.assertTrue(pr_gates.command_allowed(cells[3].strip("`"), GATES["proof_allowlist"])[0])

    def test_godot_script_argument_is_not_a_deliverable(self):
        clause = "`godot --path . --headless -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c` green"
        self.assertEqual(rc.proof_paths(clause, self.cfg), [])
        self.assertEqual(rc.proof_paths("`test -f tests/support/frames.gd`", self.cfg), ["tests/support/frames.gd"])

    def test_dot_directories_and_dashed_names_stay_whole(self):
        self.assertEqual(rc.proof_paths("`grep -q x .github/workflows/docs-checks.yml`", self.cfg),
                         [".github/workflows/docs-checks.yml"])
        self.assertEqual(rc.proof_paths('`python3 "$PROTOCOL_DIR/../tools/protocol-gen/gen.py" --check`', self.cfg), [])
        self.assertEqual(rc.proof_paths("`test -f tools/protocol-gen/gen.py`", self.cfg), ["tools/protocol-gen/gen.py"])

    def test_clause_split_keeps_semicolons_inside_backticks(self):
        self.assertEqual(rc.split_clauses("`a; b`; c"), ["`a; b`", "c"])

    def test_depends_on_with_feat_prefix_carries_over(self):
        refs, ok = rc.parse_depends("FEAT-006 T0, T2; FEAT-008 T1")
        self.assertTrue(ok)
        self.assertEqual(refs, [("FEAT-006", "T0"), ("FEAT-006", "T2"), ("FEAT-008", "T1")])

    def test_cross_feat_dependency_must_exist_on_disk(self):
        (self.spec / "features" / "FEAT-008.md").write_text(feat_text("FEAT-008", ROWS[:1]), encoding="utf-8")
        ok = self.row("README.md", proof="`test -f README.md`", depends="FEAT-008 T1")
        self.assertEqual(rc.rule_f(ok, self.cfg), [])
        for depends, text in (("FEAT-008 T7", "FEAT-008 T7 is not in that FEAT's table"),
                              ("FEAT-777 T1", "FEAT-777 not found"), ("soon", "is not —, Tn")):
            got = rc.rule_f(self.row("README.md", proof="`test -f README.md`", depends=depends), self.cfg)
            self.assertEqual(len(got), 1, depends)
            self.assertIn(text, got[0].message)


class Components(Base):
    def test_both_forms_of_single_component_rows_pass_scope(self):
        for paths in (("backend/src/**", "backend/pom.xml"), ("server/src/**", "server/pom.xml"),
                      ("frontend/tests/**", "client/project.godot"), ("tools/new/**", "README.md")):
            with self.subTest(paths=paths):
                self.assertEqual(rc.rule_b(self.row(*paths), self.cfg), [])

    def test_invalid_paths_still_fail_scope(self):
        for path in ("unknown/foo.py", "../server/foo.py", "/server/foo.py", ".git/config", "README.md/foo"):
            self.assertEqual(len(rc.rule_b(self.row(path), self.cfg)), 1, path)
        got = rc.rule_b(self.row("protocol/**", "unknown/foo.py"), self.cfg)
        self.assertEqual([(f.rule, f.level) for f in got], [("b", "FAIL")])

    def test_cross_component_rows_fail_with_split_the_row(self):
        for paths in (("tools/new/**", "server/pom.xml"), ("server/src/**", "client/tests/**"),
                      ("README.md", "client/project.godot"), ("backend/src/**", "frontend/tests/**"),
                      ("project/server/src/**", "project/README.md"),
                      ("server/src/**", "client/tests/**", "README.md")):
            with self.subTest(paths=paths):
                got = rc.rule_b(self.row(*paths), self.cfg)
                self.assertEqual([(f.rule, f.level) for f in got], [("b", "FAIL")])
                self.assertIn("split the row", got[0].message)

    def test_companion_files_do_not_make_a_row_span_components(self):
        subject = self.row("server/src/main/**", "docs/spec/enablers/ENB-020.md")
        got = rc.rule_b(subject, self.cfg)
        self.assertEqual([(f.rule, f.level) for f in got], [("b", "FAIL")])
        self.assertIn("split the row", got[0].message)
        cfg = dataclasses.replace(self.cfg, companions=("docs/spec/enablers/*.md",))
        self.assertEqual(rc.rule_b(subject, cfg), [])
        got = rc.rule_b(self.row("server/src/main/**", "docs/spec/features/FEAT-001.md"), cfg)
        self.assertEqual([(f.rule, f.level) for f in got], [("b", "FAIL")])
        self.assertIn("split the row", got[0].message)

    def test_companion_globs_match_normalized_component_paths(self):
        self.cfg = dataclasses.replace(self.cfg, companions=("client/docs/*.md",))
        for companion in ("frontend/docs/contract.md", "client/docs/contract.md"):
            with self.subTest(companion=companion):
                subject = self.row("server/src/main/**", companion)
                self.assertEqual(rc.rule_b(subject, self.cfg), [])
                self.assertEqual(rc.row_component(subject), "backend")

    def test_companion_files_still_require_a_top_level_path(self):
        cfg = dataclasses.replace(self.cfg, companions=("nowhere/*.md",))
        got = rc.rule_b(self.row("server/src/main/**", "nowhere/x.md"), cfg)
        self.assertEqual([(f.rule, f.level) for f in got], [("b", "FAIL")])
        self.assertIn("does not start at a top-level path", got[0].message)

    def test_companion_files_keep_the_owned_component_for_proofs(self):
        self.cfg = dataclasses.replace(self.cfg, companions=("docs/spec/enablers/*.md",))
        proof = "`./mvnw -q verify`; `test -f src/main/java/A.java`"
        plain = self.row("server/src/main/**", proof=proof)
        subject = self.row("server/src/main/**", "docs/spec/enablers/ENB-020.md", proof=proof)
        self.assertEqual(rc.row_component(subject), "backend")
        for rule in (rc.rule_e, rc.rule_g):
            with self.subTest(rule=rule.__name__):
                self.assertEqual(rule(plain, self.cfg), [])
                self.assertEqual(rule(subject, self.cfg), [])

    def test_companion_files_still_cover_proof_paths(self):
        self.cfg = dataclasses.replace(self.cfg, companions=("docs/spec/enablers/*.md",))
        subject = self.row("server/src/main/**", "docs/spec/enablers/ENB-020.md",
                           proof="`test -f docs/spec/enablers/ENB-020.md`")
        self.assertEqual(rc.rule_g(subject, self.cfg), [])

    def test_all_companion_files_keep_their_component(self):
        self.cfg = dataclasses.replace(self.cfg, companions=("client/docs/*.md",))
        subject = self.row("frontend/docs/one.md", "client/docs/two.md")
        self.assertEqual(rc.rule_b(subject, self.cfg), [])
        self.assertEqual(rc.row_component(subject), "frontend")

    def test_component_proof_escapes_fail_with_the_sandbox_reason(self):
        cases = (("server/pom.xml", "python3 ../tools/check/check.py"),
                 ("backend/pom.xml", "python3 ../tools/check/check.py"),
                 ("project/server/pom.xml", "python3 ../tools/check/check.py"),
                 ("client/project.godot", "git grep -q 'text' '../.gitattributes'"),
                 ("frontend/project.godot", "git grep -q 'text' '../.gitattributes'"))
        for path, command in cases:
            for suffix in ("", " green"):
                with self.subTest(path=path, suffix=suffix):
                    got = rc.rule_e(self.row(path, proof=f"`{command}`{suffix}"), self.cfg)
                    self.assertEqual([(f.rule, f.level) for f in got], [("e", "FAIL")])
                    self.assertIn("a `..` path step", got[0].message)

    def test_component_local_proofs_pass(self):
        for path, proof in (("server/pom.xml", "`test -f pom.xml`"),
                            ("client/project.godot", "`git grep -q 'setting' 'project.godot'`"),
                            ("server/pom.xml", '`python3 "$PROTOCOL_DIR/gen.py" --check`')):
            with self.subTest(path=path, proof=proof):
                self.assertEqual(rc.rule_e(self.row(path, proof=proof), self.cfg), [])

    def test_a_dotdot_step_fails_even_inside_the_component_or_after_a_variable(self):
        """KIT-080 (#280): no `..` at all, so `src/../pom.xml` and the old proof_var_depths grants fail too."""
        for proof in ("`test -f src/../pom.xml`", '`python3 "$PROTOCOL_DIR/../tools/gen.py" --check`'):
            with self.subTest(proof=proof):
                got = rc.rule_e(self.row("server/pom.xml", proof=proof), self.cfg)
                self.assertEqual([(f.rule, f.level) for f in got], [("e", "FAIL")])
                self.assertIn("a `..` path step", got[0].message)

    def test_an_interpreter_with_inline_code_fails_under_a_component(self):
        got = rc.rule_e(self.row("server/pom.xml", proof="`python3 -c \"print(open('x').read())\"`"), self.cfg)
        self.assertEqual([(f.rule, f.level) for f in got], [("e", "FAIL")])
        self.assertIn("inline code", got[0].message)

    def test_root_row_with_root_proof_paths_passes(self):
        subject = self.row("tools/check/check.py", ".gitattributes",
                           proof="`python3 tools/check/check.py`; `git grep -q 'text' '.gitattributes'`")
        self.assertEqual(rc.rule_b(subject, self.cfg), [])
        self.assertEqual(rc.rule_e(subject, self.cfg), [])

    def test_root_proof_cannot_escape_the_checkout(self):
        got = rc.rule_e(self.row("README.md", proof="`test -f ../outside.md`"), self.cfg)
        self.assertEqual([(f.rule, f.level) for f in got], [("e", "FAIL")])
        self.assertIn("../outside.md: a `..` path step", got[0].message)

    def test_spanning_row_keeps_the_other_proof_checks(self):
        paths = ("server/pom.xml", "README.md")
        self.assertEqual(rc.rule_e(self.row(*paths, proof="`python3 ../tools/check/check.py`"), self.cfg), [])
        got = rc.rule_e(self.row(*paths, proof="`docker exec demo ls`"), self.cfg)
        self.assertEqual([(f.rule, f.level) for f in got], [("e", "FAIL")])
        self.assertIn("forbidden construct", got[0].message)

    def test_each_component_still_requires_tests(self):
        paths = ("server/src/main/java/A.java", "client/features/world/player.gd", "tools/new/new.py")
        for path in paths:
            self.assertEqual(len(rc.rule_c(self.row(path), self.cfg)), 1, path)
        self.assertEqual(rc.rule_c(self.row(*paths, "backend/src/test/**", "client/tests/**",
                                            "project/tools/new/tests/**"), self.cfg), [])
        self.assertEqual(rc.rule_c(self.row("tools/new/new.py", paths[0]), self.cfg)[0].level, "FAIL")
        self.assertIn("tools/new/tests/**", rc.rule_c(self.row("tools/new/new.py"), self.cfg)[0].message)

    def test_rule_c_names_every_stack_whose_tests_are_missing(self):
        """#269: the message named only the last stack, while any fail-level stack sets the level."""
        got = rc.rule_c(self.row("server/src/main/java/A.java", "client/features/world/player.gd", "tools/new/new.py"),
                        self.cfg)
        self.assertEqual([(f.rule, f.level) for f in got], [("c", "FAIL")])
        for tests in ("server/src/test/**", "client/tests/**", "tools/new/tests/**"):
            self.assertIn(tests, got[0].message)

    def test_a_covering_glob_counts_as_a_test_path(self):
        self.assertEqual(rc.rule_c(self.row("server/src/**/*.java"), self.cfg), [])
        self.assertEqual(rc.rule_c(self.row("client/**"), self.cfg), [])

    def test_protocol_tables_and_client_dot_folders_need_no_test_path(self):
        tables = ("project/server/src/main/java/ws/ErrorCode.java", "server/src/main/java/ws/MessageTypes.java",
                  "client/app/network/protocol.gd")
        self.assertEqual(rc.rule_c(self.row(*tables, "client/.github/workflows/**", "client/.claude/**"), self.cfg), [])
        self.assertEqual(len(rc.rule_c(self.row(*tables, "server/src/main/java/A.java"), self.cfg)), 1)
        self.assertEqual(len(rc.rule_c(self.row("client/.claude/**", "client/app/network/network.gd"), self.cfg)), 1)

    def test_generated_assets_accept_mixed_form_covering_globs(self):
        self.assertEqual(len(rc.rule_d(self.row("client/features/world/a.tscn"), self.cfg)), 1)
        self.assertEqual(rc.rule_d(self.row("client/features/world/a.tscn", "frontend/features/world/**"),
                                   self.cfg), [])

    def test_proof_paths_and_dependency_globs_normalize(self):
        self.assertEqual(rc.rule_g(self.row("backend/src/main/**"), self.cfg), [])
        subject = self.row("client/tests/**", depends="T2", proof="`test -f backend/src/main/java/A.java`")
        subject.siblings = {"T2": self.row("server/src/main/**", task="T2")}
        self.assertEqual(rc.rule_g(subject, self.cfg), [])
        subject.siblings = {}
        self.assertEqual(len(rc.rule_g(subject, self.cfg)), 1)


class WithoutParameters(unittest.TestCase):
    def test_a_spec_without_row_check_keys_runs_the_kit_rules_that_need_none(self):
        bare = "---\nproject: \"fixture\"\nversion: \"0.1.0\"\nupdated: \"2026-11-15\"\n---\n"
        with tempfile.TemporaryDirectory() as tmp:
            spec = make_repo(tmp, spec_md=bare, profile="")
            code, out, err = run("check", "--spec", str(spec), "FEAT-900")
        self.assertEqual(code, 1, err)
        self.assertIn("FEAT-900 T6: Proof of completion clause 1 'docker exec demo ls' (forbidden construct) [e]", out)
        self.assertNotIn("[c]", out)
        self.assertNotIn("[h]", out)
        self.assertNotIn("[j]", out)

    def test_an_invalid_profile_is_a_usage_error(self):
        bad = PROFILE.replace("visual_approval: owner", "visual_approval: anyone")
        with tempfile.TemporaryDirectory() as tmp:
            spec = make_repo(tmp, profile=bad)
            code, _, err = run("check", "--spec", str(spec), "FEAT-900")
        self.assertEqual(code, 2)
        self.assertIn("visual_approval", err)

    def test_a_missing_gates_file_is_a_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = make_repo(tmp)
            (Path(tmp) / "tools/gates.json").unlink()
            code, _, err = run("check", "--spec", str(spec), "FEAT-900")
        self.assertEqual(code, 2)
        self.assertIn("tools/gates.json", err)


class Cli(Base):
    def test_exit_codes_and_output_format(self):
        code, out, _ = run("check", "--spec", str(self.spec), "FEAT-900")
        self.assertEqual(code, 1)
        self.assertIn("FAIL: FEAT-900 T6: Proof of completion clause 1 'docker exec demo ls' (forbidden construct) [e]",
                      out)
        self.assertRegex(out, r"row-checks: \d+ rows, \d+ fail, \d+ warn\n$")

    def test_no_target_is_a_usage_error(self):
        self.assertEqual(run("check", "--spec", str(self.spec))[0], 2)

    def test_clean_feat_exits_zero(self):
        (self.spec / "features" / "FEAT-901.md").write_text(feat_text("FEAT-901", ROWS[:1]), encoding="utf-8")
        code, out, _ = run("check", "--spec", str(self.spec), "FEAT-901")
        self.assertEqual(code, 0, out)
        self.assertIn("row-checks: 1 rows, 0 fail, 0 warn", out)

    def test_a_feat_path_works_too(self):
        code, out, _ = run("check", "--spec", str(self.spec), str(self.spec / "features" / "FEAT-900.md"))
        self.assertEqual(code, 1)
        self.assertIn("FEAT-900 T6", out)

    def test_spec_defaults_to_docs_spec_in_the_working_directory(self):
        old = os.getcwd()
        os.chdir(self.root)
        try:
            code, out, _ = run("check", "FEAT-900")
        finally:
            os.chdir(old)
        self.assertEqual(code, 1)
        self.assertIn("FEAT-900 T6", out)

    def test_feat_without_tasks_table_warns_once(self):
        path = self.spec / "features" / "FEAT-902.md"
        path.write_text("# FEAT-902\n\n## Tasks\n\nnone yet\n", encoding="utf-8")
        code, out, _ = run("check", "--spec", str(self.spec), "FEAT-902")
        self.assertEqual(code, 0)
        self.assertIn("WARN: FEAT-902: no Tasks table", out)

    def test_all_reads_every_feat(self):
        (self.spec / "features" / "FEAT-901.md").write_text(feat_text("FEAT-901", ROWS[:1]), encoding="utf-8")
        code, out, _ = run("check", "--spec", str(self.spec), "--all")
        self.assertEqual(code, 1)
        self.assertIn("row-checks: 22 rows", out)


class ConfigShapes(Base):
    """A row-checks config the tool cannot use exits 2, a usage error, never 1 or 0: a consumer's cut reads only the
    FAIL lines, so a crash or an empty config would read as clean rows (review finding 2)."""

    def write_json(self, rel, data):
        (self.root / rel).write_text(json.dumps(data), encoding="utf-8")

    def assert_usage_error(self, fragment):
        code, out, err = run("check", "--spec", str(self.spec), "FEAT-900")
        self.assertEqual(code, 2, out + err)
        self.assertIn(fragment, err)
        self.assertNotIn("Traceback", err)

    def test_an_artifact_entry_without_dec_is_a_usage_error(self):
        self.write_json("tools/artifact-policies.json", [{"pattern": "*.translation"}])
        self.assert_usage_error("dec")

    def test_an_artifacts_object_instead_of_a_list_is_a_usage_error(self):
        self.write_json("tools/artifact-policies.json", ARTIFACTS[0])
        self.assert_usage_error("a list")

    def test_a_gates_file_that_still_holds_proof_var_depths_loads(self):
        """KIT-080: the key is no longer read; a config written for 13.0 keeps working, and its `..` grants fail."""
        self.write_json("tools/gates.json", dict(GATES, proof_var_depths={"HOME": "1"}))
        code, out, err = run("check", "--spec", str(self.spec), "FEAT-900")
        self.assertEqual(code, 1, out + err)
        self.assertNotIn("proof_var_depths", err)

    def test_a_gates_file_that_is_not_an_object_is_a_usage_error(self):
        self.write_json("tools/gates.json", [])
        self.assert_usage_error("an object")

    def test_other_gate_keys_of_the_wrong_shape_are_usage_errors(self):
        for key, value in (("proof_allowlist", "python3"), ("proof_allowlist", [3]), ("generated_neighbours", ".uid"),
                           ("companion_files", "docs/x.md"), ("companion_files", [3]),
                           ("proof_script_runners", ["godot"]), ("proof_script_runners", {"godot": "-s"})):
            with self.subTest(key=key, value=value):
                self.write_json("tools/gates.json", dict(GATES, **{key: value}))
                self.assert_usage_error(key)

    def test_companion_files_load_from_the_gates_json(self):
        self.write_json("tools/gates.json", dict(GATES, companion_files=["docs/spec/enablers/*.md"]))
        cfg = rc.load_config(self.spec)
        self.assertEqual(cfg.companions, ("docs/spec/enablers/*.md",))
        self.assertEqual(rc.rule_b(self.row("server/src/main/**", "docs/spec/enablers/ENB-020.md"), cfg), [])

    def test_an_unexpected_error_exits_2_not_1(self):
        original = rc.lint

        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        rc.lint = boom
        try:
            code, out, err = run("check", "--spec", str(self.spec), "FEAT-900")
        finally:
            rc.lint = original
        self.assertEqual(code, 2, out + err)
        self.assertIn("row-checks: internal error: RuntimeError: boom", err)
        self.assertIn("Traceback", err)  # the cause, for whoever fixes it


class Changed(unittest.TestCase):
    def test_changed_picks_only_changed_feat_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = make_repo(root)
            for name in ("FEAT-901", "FEAT-902"):
                (spec / "features" / f"{name}.md").write_text(feat_text(name, ROWS), encoding="utf-8")
            (spec / "features" / "FEAT-900.md").unlink()

            def git(*a):
                subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=root, check=True,
                               capture_output=True)

            git("init", "-q")
            git("add", ".")
            git("commit", "-qm", "base")
            path = spec / "features" / "FEAT-902.md"
            path.write_text(path.read_text() + "\n", encoding="utf-8")
            git("commit", "-qam", "touch 902")
            code, out, _ = run("check", "--spec", str(spec), "--changed", "HEAD~1", "HEAD")
        self.assertEqual(code, 1)
        self.assertIn("FEAT-902 T6", out)
        self.assertNotIn("FEAT-901", out)


if __name__ == "__main__":
    unittest.main()
