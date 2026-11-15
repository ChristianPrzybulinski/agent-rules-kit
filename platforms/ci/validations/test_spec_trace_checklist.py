"""spec_trace tests for KIT-073: the journey checklist, the spec.md index check (sdd.spec_index), component test
paths (sdd.components) and calls without a spec argument. Ported from a consumer project's suite, neutral names."""
import contextlib
import io
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec_trace as trace  # noqa: E402

FEAT = """\
---
id: {fid}
title: "Fixture feature {fid}"
status: planned
requirements: [{reqs}]
created: "2026-10-05"
---

# {fid}

## Tasks

| ID | Task | Files | Status |
|---|---|---|---|
| T1 | first task | `a/**` | todo |
| T2 | second task | `b/**` | done |
"""

REQ = """\
---
id: {rid}
title: "Fixture rule {rid}"
type: functional
priority: must
features: [{feats}]
created: "2026-10-05"
---

# {rid}
"""

JOURNEY = """\
---
id: J-01
title: "Fixture journey"
status: approved
owner: product
created: "2026-10-05"
updated: "2026-10-05"
---

# J-01

## Goal

This is stage E3 of the roadmap; stage E4 follows.

## Preconditions

- The server runs.

## Steps

| Step | Player action → visible result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | opens | REQ-F-001 | FEAT-001 T1 | `{root}/tests/a/**` |
| S2 | confirms | — | FEAT-001 T2 | FEAT-001 T1 · manual: look at it |

| Step | At | Player action → visible result | Rules | Implemented by | Proven by |
|---|---|---|---|---|---|
| A1 | S1 | fails | REQ-F-001 | FEAT-001 T1 | `{root}/tests/b/**` |

| Step | What the steps need | Implemented by |
|---|---|---|
| P1 | contract | FEAT-001 T2 |
"""

SPEC_MD = """\
---
project: "fixture"
version: "0.1.0"
updated: "2026-10-05"
sdd:
  spec_index: {index}
---

# Spec

| ID | Title | Features |
|---|---|---|
| [REQ-F-001](requirements/functional/REQ-F-001.md) | Fixture rule | FEAT-001 |

| ID | Title | Status |
|---|---|---|
| [J-01](journeys/J-01.md) | Fixture journey | approved |
"""


def write(root, rel, text):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def fixture(root, journey=None, index="true"):
    """A clone named `repo` with one approved journey whose test paths live in that clone."""
    root = Path(root)
    write(root, "tests/a/test_a.py", "")
    write(root, "tests/b/test_b.py", "")
    spec = root / "docs/spec"
    write(root, "docs/spec/features/FEAT-001.md", FEAT.format(fid="FEAT-001", reqs="REQ-F-001"))
    write(root, "docs/spec/requirements/functional/REQ-F-001.md", REQ.format(rid="REQ-F-001", feats="FEAT-001"))
    write(root, "docs/spec/journeys/J-01.md", journey or JOURNEY.format(root=root.name))
    write(root, "docs/spec/spec.md", SPEC_MD.format(index=index))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        trace.main(["generate", str(spec)])
    return spec


def run_main(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = trace.main(list(argv))
        except SystemExit as stop:  # argparse usage errors exit 2
            code = stop.code
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / "repo"
        self.root.mkdir()
        self.spec = fixture(self.root)

    def errors(self):
        return trace.check(trace.load(self.spec))

    def assert_error(self, errs, fragment):
        self.assertTrue(any(fragment in e for e in errs), f"no error containing {fragment!r} in {errs}")


class IndexTest(Base):
    def test_valid_fixture_passes(self):
        self.assertEqual(self.errors(), [])

    def test_unindexed_requirement_fails(self):
        write(self.root, "docs/spec/requirements/functional/REQ-F-002.md", REQ.format(rid="REQ-F-002", feats=""))
        self.assert_error(self.errors(), "requirements/functional/REQ-F-002.md has no row in spec.md")

    def test_unindexed_nonfunctional_requirement_and_journey_fail(self):
        write(self.root, "docs/spec/requirements/non-functional/REQ-NF-001.md", REQ.format(rid="REQ-NF-001", feats=""))
        write(self.root, "docs/spec/journeys/J-02.md", JOURNEY.format(root="repo").replace("J-01", "J-02"))
        errs = self.errors()
        self.assert_error(errs, "requirements/non-functional/REQ-NF-001.md has no row in spec.md")
        self.assert_error(errs, "journeys/J-02.md has no row in spec.md")

    def test_missing_index_target_fails(self):
        path = self.spec / "spec.md"
        path.write_text(path.read_text() + "| [REQ-F-002](requirements/functional/REQ-F-002.md) | Missing | — |\n")
        self.assert_error(self.errors(), "spec.md: link points to missing file requirements/functional/REQ-F-002.md")

    def test_the_check_is_off_unless_spec_index_is_true(self):
        for index in ("false", None):
            with self.subTest(index=index):
                text = SPEC_MD.format(index="false")
                if index is None:
                    text = text.replace("sdd:\n  spec_index: false\n", "")
                write(self.root, "docs/spec/spec.md", text)
                write(self.root, "docs/spec/requirements/functional/REQ-F-002.md",
                      REQ.format(rid="REQ-F-002", feats=""))
                self.assertFalse([e for e in self.errors() if "spec.md" in e], self.errors())


class ChecklistTest(Base):
    def test_rows_carry_action_rules_proof_and_manual(self):
        code, out, _ = run_main("checklist", str(self.spec), "J-01")
        self.assertEqual(code, 0)
        self.assertIn("Stage: E3", out)
        self.assertIn("- The server runs.", out)
        self.assertIn("| S1 | — | opens | REQ-F-001 — Fixture rule REQ-F-001 | `repo/tests/a/**` | — |  |", out)
        self.assertIn("| S2 | — | confirms | — | FEAT-001 T1 | look at it |  |", out)
        self.assertIn("| A1 | S1 | fails |", out)

    def test_prerequisite_shows_task_status(self):
        _, out, _ = run_main("checklist", str(self.spec), "J-01")
        self.assertIn("| P1 | contract | FEAT-001 T2 | done |", out)

    def test_stage_is_the_first_in_goal_and_optional(self):
        spec = trace.load(self.spec)
        self.assertEqual(spec.journeys["J-01"]["stage"], "E3")
        self.assertEqual(spec.journeys["J-01"]["steps"][0].action, "opens")
        self.assertEqual(trace.section("# x\n", "Goal"), "")

    def test_unknown_or_unapproved_id_fails_without_traceback(self):
        code, out, err = run_main("checklist", str(self.spec), "J-99")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("FAIL: J-99", err)
        path = self.spec / "journeys/J-01.md"
        path.write_text(path.read_text().replace("approved", "proposed"))
        self.assertEqual(run_main("checklist", str(self.spec), "J-01")[0], 1)

    def test_journey_with_parse_errors_fails(self):
        path = self.spec / "journeys/J-01.md"
        path.write_text(path.read_text().replace("| REQ-F-001 | FEAT-001 T1 | `repo/tests/a/**`",
                                                 "| REQ-F-099 | FEAT-001 T1 | `repo/tests/a/**`"))
        code, out, err = run_main("checklist", str(self.spec), "J-01")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("REQ-F-099", err)

    def test_two_runs_are_identical(self):
        self.assertEqual(run_main("checklist", str(self.spec), "J-01"), run_main("checklist", str(self.spec), "J-01"))

    def test_out_refuses_to_overwrite_without_force(self):
        target = self.root.parent / "out.md"
        self.assertEqual(run_main("checklist", str(self.spec), "J-01", "--out", str(target))[0], 0)
        first = target.read_text()
        target.write_text("kept")
        code, _, err = run_main("checklist", str(self.spec), "J-01", "--out", str(target))
        self.assertEqual((code, target.read_text()), (1, "kept"))
        self.assertIn("FAIL:", err)
        self.assertEqual(run_main("checklist", str(self.spec), "J-01", "--out", str(target), "--force")[0], 0)
        self.assertEqual(target.read_text(), first)

    def test_the_journey_id_needs_no_spec_argument(self):
        old = os.getcwd()
        os.chdir(self.root)
        try:
            code, out, err = run_main("checklist", "J-01")
        finally:
            os.chdir(old)
        self.assertEqual(code, 0, err)
        self.assertIn("# J-01 — Fixture journey", out)


class DefaultSpecTest(Base):
    """A loop calls `impact BASE HEAD` and `sync-status` from the repository root with no spec argument."""

    def in_root(self, *argv):
        old = os.getcwd()
        os.chdir(self.root)
        try:
            return run_main(*argv)
        finally:
            os.chdir(old)

    def test_check_status_and_lint_default_to_docs_spec(self):
        self.assertEqual(self.in_root("check")[0], 0)
        self.assertEqual(self.in_root("status")[0], 1)  # FEAT-001 has a done row: in-progress is due
        code, _, err = self.in_root("lint", "FEAT-001")
        self.assertIn(code, (0, 1), err)
        self.assertNotIn("is not a FEAT", err)

    def test_impact_takes_two_or_three_positionals(self):
        import subprocess
        git = lambda *a: subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t",  # noqa: E731
                                         *a], check=True, capture_output=True)
        git("init", "-q")
        git("add", ".")
        git("commit", "-qm", "base")
        req = self.spec / "requirements/functional/REQ-F-001.md"
        req.write_text(req.read_text() + "\nmore\n")
        git("commit", "-qam", "edit")
        code, out, err = self.in_root("impact", "HEAD~1", "HEAD")
        self.assertEqual(code, 0, err)
        self.assertIn("| REQ-F-001 edited | J-01 S1, J-01 A1 |", out)
        self.assertEqual(run_main("impact", str(self.spec), "HEAD~1", "HEAD")[0:2], (0, out))

    def test_mark_done_without_a_spec_argument(self):
        code, out, _ = self.in_root("mark-done", "FEAT-001", "T1")
        self.assertEqual(code, 0)
        self.assertIn("FEAT-001 T1 -> done", out)


class MatrixWithoutJourneysTest(unittest.TestCase):
    """`traceability.md` is required when journeys are on (`sdd.journeys`, absent = on when docs/spec/journeys/
    exists) and kept fresh once it exists; a project with neither passes `check`, since sync-project.sh vendors
    spec_trace.py to every project with docs/spec (sync-status needs no journeys)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / "repo"
        self.spec = self.root / "docs/spec"
        write(self.root, "docs/spec/features/FEAT-001.md", FEAT.format(fid="FEAT-001", reqs="REQ-F-001"))
        write(self.root, "docs/spec/requirements/functional/REQ-F-001.md",
              REQ.format(rid="REQ-F-001", feats="FEAT-001"))
        self.spec_md()

    def spec_md(self, sdd=""):
        write(self.root, "docs/spec/spec.md",
              f'---\nproject: "fixture"\nversion: "0.1.0"\nupdated: "2026-10-05"\n{sdd}---\n\n# Spec\n')

    def stale(self):
        return [e for e in trace.check(trace.load(self.spec)) if "is stale or missing" in e]

    def test_no_journeys_and_no_matrix_pass(self):
        self.assertEqual(trace.check(trace.load(self.spec)), [])
        code, out, _ = run_main("check", str(self.spec))
        self.assertEqual(code, 0, out)

    def test_journeys_on_without_a_folder_still_need_the_matrix(self):
        self.spec_md("sdd:\n  journeys: true\n")
        self.assertTrue(self.stale())

    def test_a_journeys_folder_still_needs_the_matrix(self):
        (self.spec / "journeys").mkdir()
        self.assertTrue(self.stale())

    def test_an_existing_matrix_stays_fresh_without_journeys(self):
        self.assertEqual(run_main("generate", str(self.spec))[0], 0)
        self.assertEqual(self.stale(), [])
        write(self.root, "docs/spec/requirements/functional/REQ-F-002.md", REQ.format(rid="REQ-F-002", feats=""))
        self.assertTrue(self.stale())  # the matrix has a row per REQ


class ComponentPathsTest(unittest.TestCase):
    """sdd.components: a test path may be rooted at a component name or folder of this repository."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / "product"
        for rel in ("server/pom.xml", "client/project.godot", "server/src/test/Example.java",
                    "client/tests/a/example.gd", "tools/example/tests/test_example.py"):
            write(self.root, rel, "fixture")

    def errors_for(self, path):
        journey = JOURNEY.format(root="x").replace("`x/tests/a/**`", f"`{path}`").replace("`x/tests/b/**`",
                                                                                        "`client/tests/a/**`")
        spec = fixture(self.root, journey, index="false")
        index = spec / "spec.md"
        index.write_text(index.read_text().replace(
            "  spec_index: false\n", "  spec_index: false\n  components: {project: \".\", backend: server, "
                                     "frontend: client}\n"))
        return [e for e in trace.check(trace.load(spec)) if "test path" in e]

    def test_both_forms_and_root_tools_pass(self):
        for path in ("server/src/test/**", "client/tests/a/**", "tools/example/tests/**", "backend/src/test/**",
                     "frontend/tests/a/**", "project/tools/example/tests/**", "client/tests/missing/**",
                     "backend/src/test/java/Missing.java"):
            with self.subTest(path=path):
                self.assertEqual(self.errors_for(path), [])

    def test_unrooted_or_missing_root_paths_fail(self):
        for path in ("unknown/tests/**", "tools/missing/tests/**", "../client/tests/**", "project/../client/tests/**"):
            with self.subTest(path=path):
                self.assertTrue(self.errors_for(path), path)


if __name__ == "__main__":
    unittest.main()
