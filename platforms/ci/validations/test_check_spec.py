"""check_spec.py FEAT<->REQ cross-check (both frontmatters must agree on every link), progress files, conflict
markers, the project's decision kinds and NEED intake records."""
import importlib.util
import json
import os
import shutil
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

FEAT = """---
id: {fid}
title: "Fixture feature {fid}"
status: proposed
requirements: [{reqs}]
created: "2026-10-05"
---

# {fid}
"""

REQ = """---
id: {rid}
title: "Fixture requirement {rid}"
type: functional
priority: must
features: [{feats}]
created: "2026-10-05"
---

# {rid}
"""


class FeatReqCrossCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spec = Path(self.tmp.name)
        (self.spec / "features").mkdir()
        (self.spec / "requirements" / "functional").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def feat(self, fid, *reqs):
        (self.spec / "features" / f"{fid}.md").write_text(FEAT.format(fid=fid, reqs=", ".join(reqs)))

    def req(self, rid, *feats):
        path = self.spec / "requirements" / "functional" / f"{rid}.md"
        path.write_text(REQ.format(rid=rid, feats=", ".join(feats)))

    def run_check(self):
        return subprocess.run([sys.executable, str(CHECK_SPEC), str(self.spec), str(SCHEMAS)],
                              capture_output=True, text=True, check=False)

    def test_links_on_both_sides_pass(self):
        self.feat("FEAT-001", "REQ-F-001")
        self.feat("FEAT-002", "REQ-F-001")
        self.req("REQ-F-001", "FEAT-001", "FEAT-002")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_feat_listing_a_req_that_does_not_list_it_fails(self):
        self.feat("FEAT-001", "REQ-F-001")
        self.feat("FEAT-002", "REQ-F-001")
        self.req("REQ-F-001", "FEAT-001")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("requirements lists REQ-F-001, but REQ-F-001 features does not list FEAT-002", result.stderr)

    def test_req_listing_a_feat_that_does_not_list_it_fails(self):
        self.feat("FEAT-001", "REQ-F-001")
        self.feat("FEAT-002")
        self.req("REQ-F-001", "FEAT-001", "FEAT-002")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("features lists FEAT-002, but FEAT-002 requirements does not list REQ-F-001", result.stderr)

    def test_req_no_feat_lists_still_fails(self):
        self.feat("FEAT-001")
        self.req("REQ-F-001", "FEAT-001")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FEAT-001 requirements does not list REQ-F-001", result.stderr)


PROGRESS_TASK = {"id": "T1", "title": "Define the contract", "files": ["protocol/a.json"],
                 "proof": "example validates", "passes": False, "notes": ""}


class ProgressTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spec = Path(self.tmp.name)
        (self.spec / "features").mkdir()
        (self.spec / "progress").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def feat(self, fid):
        (self.spec / "features" / f"{fid}.md").write_text(FEAT.format(fid=fid, reqs=""))

    def progress(self, name, data):
        text = data if isinstance(data, str) else json.dumps(data)
        (self.spec / "progress" / f"{name}.json").write_text(text)

    def doc(self, feat, *tasks):
        return {"feat": feat, "generated": "2026-10-06", "tasks": list(tasks) or [dict(PROGRESS_TASK)]}

    def run_check(self):
        return subprocess.run([sys.executable, str(CHECK_SPEC), str(self.spec), str(SCHEMAS)],
                              capture_output=True, text=True, check=False)

    def test_valid_progress_file_passes(self):
        self.feat("FEAT-001")
        self.progress("FEAT-001", self.doc("FEAT-001"))
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("progress: OK (1 files)", result.stdout)

    def test_feat_without_a_feat_file_fails(self):
        self.feat("FEAT-001")
        self.progress("FEAT-002", self.doc("FEAT-002"))
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not exist in features/", result.stderr)

    def test_file_name_must_equal_feat(self):
        self.feat("FEAT-001")
        self.feat("FEAT-002")
        self.progress("FEAT-002", self.doc("FEAT-001"))
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("!= file name", result.stderr)

    def test_passes_must_be_a_boolean(self):
        self.feat("FEAT-001")
        self.progress("FEAT-001", self.doc("FEAT-001", dict(PROGRESS_TASK, passes="yes")))
        result = self.run_check()
        self.assertEqual(result.returncode, 1)

    def test_duplicate_task_id_fails(self):
        self.feat("FEAT-001")
        self.progress("FEAT-001", self.doc("FEAT-001", dict(PROGRESS_TASK), dict(PROGRESS_TASK)))
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate task id", result.stderr)

    def test_invalid_json_fails(self):
        self.feat("FEAT-001")
        self.progress("FEAT-001", "{not json")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid JSON", result.stderr)

    def test_kit_example_validates(self):
        self.feat("FEAT-009")
        example = VALIDATIONS.parent.parent / "kits" / "sdd" / "progress.example.json"
        shutil.copy(example, self.spec / "progress" / "FEAT-009.json")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)


class ConflictMarkerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spec = Path(self.tmp.name)
        (self.spec / "features").mkdir()
        (self.spec / "journeys").mkdir()
        (self.spec / "features" / "FEAT-001.md").write_text(FEAT.format(fid="FEAT-001", reqs=""))

    def tearDown(self):
        self.tmp.cleanup()

    def run_check(self):
        return subprocess.run([sys.executable, str(CHECK_SPEC), str(self.spec), str(SCHEMAS)],
                              capture_output=True, text=True, check=False)

    def test_conflict_left_in_a_feature_fails(self):
        path = self.spec / "features" / "FEAT-001.md"
        path.write_text(path.read_text() + "## History\n\n<<<<<<< HEAD\n- ours\n=======\n- theirs\n>>>>>>> origin/main\n")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FEAT-001.md:12: merge-conflict marker '<<<<<<<'", result.stderr)
        self.assertIn("merge-conflict marker '>>>>>>>'", result.stderr)

    def test_conflict_left_in_a_file_without_frontmatter_fails(self):
        (self.spec / "journeys" / "J-01.md").write_text("# J-01\n\n||||||| base\n- old\n")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("J-01.md:3: merge-conflict marker '|||||||'", result.stderr)

    def test_setext_underline_and_quotes_pass(self):
        (self.spec / "journeys" / "J-01.md").write_text("Title\n=======\n\n> > quoted\n`<<<<<<< HEAD` in code\n")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)


SPEC_INDEX = """---
project: "fixture"
version: "0.1.0"
updated: "2026-11-13"
{extra}---

# Fixture
"""

DECISION = """---
id: {did}
title: "Fixture decision {did}"
status: proposed
date: "2026-11-13"
{extra}---

# {did}
"""


class DecisionKindsTest(unittest.TestCase):
    """Decision ids are DEC-nnn unless spec.md declares decision_kinds (KIT-064)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spec = Path(self.tmp.name)
        (self.spec / "decisions").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def index(self, kinds=None):
        extra = f"decision_kinds: {kinds}\n" if kinds else ""
        (self.spec / "spec.md").write_text(SPEC_INDEX.format(extra=extra))

    def decision(self, did, kind=None):
        extra = f"kind: {kind}\n" if kind else ""
        (self.spec / "decisions" / f"{did}-fixture.md").write_text(DECISION.format(did=did, extra=extra))

    def run_both(self):
        """The full check, then the structural one: python -S hides pyyaml and jsonschema."""
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        runs = []
        for flags in ([], ["-S"]):
            runs.append(subprocess.run([sys.executable, *flags, str(CHECK_SPEC), str(self.spec), str(SCHEMAS)],
                                       capture_output=True, text=True, check=False, env=env))
        self.assertIn("spec validation will be structural", runs[1].stderr)
        return runs

    def assert_passes(self):
        for result in self.run_both():
            self.assertEqual(result.returncode, 0, result.stderr)

    def assert_fails(self, *messages):
        for result in self.run_both():
            self.assertEqual(result.returncode, 1, result.stderr)
            for message in messages:
                self.assertIn(message, result.stderr)

    def test_dec_without_declaration_passes(self):
        self.index()
        self.decision("DEC-001")
        self.assert_passes()

    def test_dec_without_spec_index_passes(self):
        self.decision("DEC-001")
        self.assert_passes()

    def test_other_prefix_without_declaration_fails(self):
        self.index()
        self.decision("TEC-001", "tech")
        self.assert_fails("id TEC-001: a decision id is DEC-nnn unless spec.md declares decision_kinds")

    def test_declared_kinds_pass(self):
        self.index("{tech: TEC, product: PRD}")
        self.decision("TEC-001", "tech")
        self.decision("PRD-001", "product")
        self.assert_passes()

    def test_prefix_must_match_kind(self):
        self.index("{tech: TEC, product: PRD}")
        self.decision("PRD-001", "tech")
        self.assert_fails("id PRD-001 prefix does not match kind 'tech' (TEC-nnn)")

    def test_kind_is_required_when_declared(self):
        self.index("{tech: TEC, product: PRD}")
        self.decision("TEC-001")
        self.assert_fails("kind missing; spec.md decision_kinds declares ['product', 'tech']")

    def test_undeclared_kind_fails(self):
        self.index("{tech: TEC, product: PRD}")
        self.decision("OPS-001", "ops")
        self.assert_fails("kind 'ops' is not in spec.md decision_kinds ['product', 'tech']")

    def test_invalid_prefixes_fail(self):
        self.index("{tech: tec, product: FEAT}")
        self.assert_fails("decision prefix 'tec' must match", "decision prefix 'FEAT' must match")

    def test_duplicate_prefix_fails(self):
        self.index("{tech: TEC, ops: TEC}")
        self.assert_fails("decision prefix TEC is declared for both 'tech' and 'ops'")

    def test_need_prefix_is_reserved(self):
        self.index("{tech: NEED}")
        self.assert_fails("decision prefix 'NEED' must match")

    def test_process_prefix_is_reserved(self):
        self.index("{process: PROC}")
        self.assert_fails("decision prefix 'PROC' must match")


NEED = """---
id: {nid}
title: "Fixture need {nid}"
type: {type}
status: {status}
origin: "owner"
{extra}created: "2026-11-14"
---

# {nid}
"""

JOURNEY = """---
id: J-01
title: "Fixture journey"
status: proposed
owner: "product"
created: "2026-11-14"
updated: "2026-11-14"
---

# J-01
"""

DEBT = """---
id: DEBT-001
title: "Fixture debt DEBT-001"
status: open
severity: low
trigger: "fixture trigger"
created: "2026-11-14"
---

# DEBT-001
"""


PROCESS = """---
id: PROC-001
title: "Fixture process"
status: proposed
owner: "product"
kind: product
{extra}created: "2026-11-16"
updated: "2026-11-16"
---

# PROC-001
"""


class ProcessTest(unittest.TestCase):
    """docs/spec/processes/PROC-nnn-slug.md frontmatter (KIT-090), with and without jsonschema."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spec = Path(self.tmp.name)
        (self.spec / "processes").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def process(self, name="PROC-001-fixture", old=None, new=None):
        text = PROCESS.format(extra="")
        (self.spec / "processes" / f"{name}.md").write_text(text if old is None else text.replace(old, new))

    def run_both(self):
        """The full check, then the structural one: python -S hides pyyaml and jsonschema."""
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        return [subprocess.run([sys.executable, *flags, str(CHECK_SPEC), str(self.spec), str(SCHEMAS)],
                               capture_output=True, text=True, check=False, env=env)
                for flags in ([], ["-S"])]

    def assert_fails(self, *messages):
        for result in self.run_both():
            self.assertEqual(result.returncode, 1, result.stderr)
            for message in messages:
                self.assertIn(message, result.stderr)

    def test_product_and_tech_processes_pass(self):
        self.process()
        (self.spec / "processes" / "PROC-002-runbook.md").write_text(
            PROCESS.format(extra="").replace("PROC-001", "PROC-002").replace("kind: product", "kind: tech"))
        for result in self.run_both():
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("spec: OK (2 artifacts)", result.stdout)

    def test_kind_is_required_and_an_enum(self):
        self.process(old="kind: product\n", new="")
        self.assert_fails("PROC-001-fixture.md")
        self.process(old="kind: product", new="kind: ops")
        self.assert_fails("PROC-001-fixture.md", "ops")

    def test_status_is_an_enum(self):
        self.process(old="status: proposed", new="status: done")
        self.assert_fails("PROC-001-fixture.md", "done")

    def test_id_pattern_and_file_name(self):
        self.process(old="id: PROC-001", new="id: PROC-1")
        self.assert_fails("PROC-001-fixture.md")
        self.process(name="PROC-003-other")
        self.assert_fails("id=PROC-001 != file name prefix")

    def test_unknown_field_fails_with_the_schema(self):
        self.process(old="kind: product", new="kind: product\nlevel: end-to-end")
        self.assertEqual(self.run_both()[0].returncode, 1)


class NeedTest(unittest.TestCase):
    """NEED-nnn intake records link forward only and back their status with links (KIT-066)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.spec = self.root / "docs" / "spec"  # the profile beside it sets sdd.needs (KIT-087 P4)
        for sub in ("needs", "features", "requirements/functional", "decisions", "journeys"):
            (self.spec / sub).mkdir(parents=True)
        (self.spec / "features" / "FEAT-001.md").write_text(FEAT.format(fid="FEAT-001", reqs="REQ-F-001"))
        (self.spec / "requirements" / "functional" / "REQ-F-001.md").write_text(
            REQ.format(rid="REQ-F-001", feats="FEAT-001"))
        (self.spec / "decisions" / "DEC-001-fixture.md").write_text(DECISION.format(did="DEC-001", extra=""))
        (self.spec / "journeys" / "J-01-fixture.md").write_text(JOURNEY)

    def tearDown(self):
        self.tmp.cleanup()

    def need(self, nid, status="proposed", type_="new", **links):
        extra = "".join(f"{field}: {value}\n" for field, value in links.items())
        (self.spec / "needs" / f"{nid}-fixture.md").write_text(
            NEED.format(nid=nid, type=type_, status=status, extra=extra))

    def run_both(self):
        """The full check, then the structural one: python -S hides pyyaml and jsonschema."""
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        return [subprocess.run([sys.executable, *flags, str(CHECK_SPEC), str(self.spec), str(SCHEMAS)],
                               capture_output=True, text=True, check=False, env=env)
                for flags in ([], ["-S"])]

    def assert_passes(self):
        for result in self.run_both():
            self.assertEqual(result.returncode, 0, result.stderr)

    def assert_fails(self, *messages):
        for result in self.run_both():
            self.assertEqual(result.returncode, 1, result.stderr)
            for message in messages:
                self.assertIn(message, result.stderr)

    def test_captured_need_passes(self):
        self.need("NEED-001")
        self.assert_passes()

    def test_refined_need_with_links_passes(self):
        self.need("NEED-001", status="refined", requirements="[REQ-F-001]", journeys="[J-01]",
                  decisions="[DEC-001]", features="[FEAT-001]")
        self.need("NEED-002", status="triaged", parent="NEED-001")
        self.assert_passes()

    def test_unknown_type_and_status_fail(self):
        self.need("NEED-001", status="done", type_="idea")
        self.assert_fails("NEED-001-fixture.md")

    def test_file_name_must_carry_the_id(self):
        (self.spec / "needs" / "NEED-009-other.md").write_text(
            NEED.format(nid="NEED-001", type="new", status="proposed", extra=""))
        self.assert_fails("id=NEED-001 != file name prefix")

    def test_link_to_missing_or_wrong_kind_fails(self):
        self.need("NEED-001", requirements="[REQ-F-002]", features="[REQ-F-001]")
        self.assert_fails("requirements lists REQ-F-002, which is not an existing requirement",
                          "features lists REQ-F-001, which is not an existing feature")

    def test_missing_journey_fails(self):
        self.need("NEED-001", journeys="[J-02]")
        self.assert_fails("journeys lists J-02, which has no file under journeys/")

    def test_parent_must_be_another_need(self):
        self.need("NEED-001", parent="NEED-001")
        self.need("NEED-002", parent="NEED-003")
        self.assert_fails("parent is the NEED itself", "parent NEED-003 is not an existing NEED")

    def test_refined_without_product_links_fails(self):
        self.need("NEED-001", status="refined", features="[FEAT-001]")
        self.assert_fails("status refined needs at least one link in requirements, journeys, decisions")

    def req_without_feat(self, rid, status="proposed"):
        text = REQ.format(rid=rid, feats="").replace("priority: must\n", f"status: {status}\npriority: must\n")
        (self.spec / "requirements" / "functional" / f"{rid}.md").write_text(text)

    def test_specified_need_passes(self):
        self.need("NEED-001", status="specified")
        self.assert_passes()

    def test_req_listed_only_by_a_need_passes(self):
        self.req_without_feat("REQ-F-002")
        self.need("NEED-001", status="refined", requirements="[REQ-F-002]")
        self.assert_passes()

    def test_req_listed_by_neither_feat_nor_need_fails(self):
        self.req_without_feat("REQ-F-002", status="approved")
        self.assert_fails("REQ-F-002 has no FEAT implementing it and no NEED listing it")

    def needs_mode(self, value):
        write_spec(self.root, SPEC_INDEX.format(extra=f"sdd:\n  needs: {value}\n"))

    def test_needs_on_keeps_need_files(self):
        """#237, both modes: `sdd.needs: true` (the default) keeps NEED files and lets one hold a REQ before its FEAT."""
        self.needs_mode("true")
        self.req_without_feat("REQ-F-002")
        self.need("NEED-001", status="refined", requirements="[REQ-F-002]")
        self.assert_passes()

    def test_needs_off_without_need_files_passes(self):
        self.needs_mode("false")
        self.assert_passes()

    def test_needs_off_reads_need_files_not_the_folder(self):
        """#288 item 5 (intended): needs-off reads the Markdown files at the top of needs/, not the folder, so a
        folder that keeps only NEED-nnn-data/ evidence passes, and any Markdown file there is a NEED record."""
        self.needs_mode("false")
        (self.spec / "needs" / "NEED-001-data").mkdir(parents=True)
        (self.spec / "needs" / "NEED-001-data" / "capture.md").write_text("evidence\n")
        self.assert_passes()
        (self.spec / "needs" / "README.md").write_text("# NEEDs\n")
        self.assert_fails("README.md: sdd.needs is false, so the project keeps no NEED files under needs/")

    def test_needs_off_refuses_a_need_file(self):
        self.needs_mode("false")
        self.need("NEED-001")
        self.assert_fails("NEED-001-fixture.md: sdd.needs is false, so the project keeps no NEED files under needs/")

    def test_needs_off_a_req_lands_with_its_feat(self):
        """#237: with no NEED to hold it, a REQ needs a FEAT (the rule before KIT-066); a NEED listing it does not
        count."""
        self.needs_mode("false")
        self.req_without_feat("REQ-F-002")
        self.need("NEED-001", status="refined", requirements="[REQ-F-002]")
        self.assert_fails("REQ-F-002 has no FEAT implementing it (sdd.needs: false: a REQ lands in the change that "
                          "creates its FEAT)")

    def test_unknown_req_status_fails(self):
        self.req_without_feat("REQ-F-002", status="done")
        self.need("NEED-001", requirements="[REQ-F-002]")
        self.assert_fails("REQ-F-002.md")

    def test_delivered_needs_delivered_features(self):
        self.need("NEED-001", status="delivered", requirements="[REQ-F-001]")
        self.need("NEED-002", status="delivered", requirements="[REQ-F-001]", features="[FEAT-001]")
        self.assert_fails("NEED-001-fixture.md: status delivered needs the features that delivered it",
                          "NEED-002-fixture.md: status delivered, but FEAT-001 is proposed")

    def approved_decision(self, did):
        text = DECISION.format(did=did, extra="").replace("status: proposed", "status: approved")
        (self.spec / "decisions" / f"{did}-fixture.md").write_text(text)

    def test_markdown_in_a_need_data_folder_is_not_a_need(self):
        self.need("NEED-001")
        (self.spec / "needs" / "NEED-001-data").mkdir()
        (self.spec / "needs" / "NEED-001-data" / "notes.md").write_text("# Interview notes\n\n- bulky evidence\n")
        self.assert_passes()

    def test_decision_need_delivered_by_its_approved_decision_passes(self):
        self.approved_decision("DEC-002")
        self.need("NEED-001", status="delivered", type_="decision", decisions="[DEC-002]")
        self.assert_passes()

    def test_delivered_without_features_needs_a_decision_need_and_an_approved_decision(self):
        self.approved_decision("DEC-002")
        self.need("NEED-001", status="delivered", type_="decision", decisions="[DEC-001]")
        self.need("NEED-002", status="delivered", type_="new", decisions="[DEC-002]")
        self.assert_fails("NEED-001-fixture.md: status delivered needs the features that delivered it",
                          "NEED-002-fixture.md: status delivered needs the features that delivered it")

    def test_req_listed_only_by_a_closed_need_fails(self):
        self.req_without_feat("REQ-F-002")
        for status in ("rejected", "merged", "routed", "parked"):
            with self.subTest(status=status):
                self.need("NEED-001", status=status, requirements="[REQ-F-002]")
                self.assert_fails("REQ-F-002 has no FEAT implementing it and no NEED listing it")

    def test_req_listed_only_by_a_delivered_need_fails(self):
        self.req_without_feat("REQ-F-002", status="approved")
        self.approved_decision("DEC-002")
        self.need("NEED-001", status="delivered", type_="decision", decisions="[DEC-002]", requirements="[REQ-F-002]")
        self.assert_fails("REQ-F-002 has no FEAT implementing it and no NEED listing it "
                          "(NEED-001 lists it but is closed or delivered)")

    def test_decisions_link_must_be_a_decision(self):
        self.need("NEED-001", decisions="[REQ-F-001]")
        self.assert_fails("decisions lists REQ-F-001, which is not an existing decision")

    def test_debts_link_must_be_a_debt(self):
        (self.spec / "debts").mkdir()
        (self.spec / "debts" / "DEBT-001-fixture.md").write_text(DEBT)
        self.need("NEED-001", debts="[DEBT-001]")
        self.assert_passes()
        self.need("NEED-002", debts="[DEC-001]")
        self.assert_fails("debts lists DEC-001, which is not an existing debt")

    def test_processes_link_must_be_a_process(self):
        """KIT-090: a NEED lists the processes it changes, as it lists journeys."""
        (self.spec / "processes").mkdir()
        (self.spec / "processes" / "PROC-001-fixture.md").write_text(PROCESS.format(extra=""))
        self.need("NEED-001", status="refined", processes="[PROC-001]")
        self.assert_passes()
        self.need("NEED-002", processes="[PROC-009]")
        self.assert_fails("processes lists PROC-009, which is not an existing process")


class MiniYamlTest(unittest.TestCase):
    """The structural parser against pyyaml on the same text (KIT-067 review): comments, quotes holding ' #'."""

    LAYER = "unit"  # in-process: no subprocess, no git

    TEXT = ('k: ["a #b", c]  # note\nt: it\'s here  # c\nq: "x # y"  # z\nm: {path: "p #1"}\n'
            'c: \'gh issue create --title "x"\'\nd: "it\'s"\ne: \'it\'\'s\'\n')
    WANT = {"k": ["a #b", "c"], "t": "it's here", "q": "x # y", "m": {"path": "p #1"},
            "c": 'gh issue create --title "x"', "d": "it's", "e": "it's"}

    def test_quoted_text_keeps_its_hash(self):
        loader = importlib.util.spec_from_file_location("check_spec_under_test", CHECK_SPEC)
        module = importlib.util.module_from_spec(loader)
        loader.loader.exec_module(module)
        self.assertEqual(module.mini_yaml(self.TEXT), self.WANT)
        try:
            import yaml
        except ImportError:
            self.skipTest("pyyaml missing: only the structural side ran")
        self.assertEqual(yaml.safe_load(self.TEXT), self.WANT)


SDD_FULL = """sdd:
  needs: false
  journeys: true
  tracker: none
  # Risks and Tests stay on in every project
  plan_sections: [Design, Contract, Tests, Risks]
  pr_unit: feat
  task_minutes: 90
  row_check: "python3 tools/row_lint.py check"
  cut_command: python3 tools/cut.py
  max_chain: 3
  max_feat_tasks: 20
  release: manual
  review_rounds: 2
  commits_by: orchestrator
  protected_paths:
    "game/protocol/": contract
    platform/loop/**: loop
  bundle: {rows: 3, points: 6, high_rows: 1}
  rule_paths:
    json: [game/protocol, game/content]
    godot: [client]
  visual_approval: owner
  owner_approvals: [decision, approved-dec-change, protocol-version, in-game-evidence]
  doc_structure:
    enabled: true
    exempt: docs/doc-structure-exempt.txt
    headings: ["## Scope", "## Out of scope"]
    done_index: false
"""

SDD_DEFAULTS = {"needs": True, "journeys": False, "tracker": "github",
                "plan_sections": ["Design", "Contract", "Data", "UI", "Flag", "Tests", "Observability", "Risks",
                                  "Dependencies"],
                "pr_unit": "task", "task_minutes": 30, "row_check": None, "cut_command": None, "max_chain": 4,
                "max_feat_tasks": 30, "release": "merge", "commits_by": "executor", "protected_paths": {},
                "bundle": {"rows": 1, "points": 3, "high_rows": 1}, "rule_paths": {},
                "components": {}, "spec_index": False,
                "github": {"repo": None, "pr_repos": [], "aliases": [], "blocked_labels": ["blocked"],
                           "progress_labels": ["status:in-progress"]},
                "row_checks": {"gates": None, "tests": [], "assets": None, "protocol": None, "artifacts": None,
                               "visual": None, "evidence_only": False},
                "owner_approvals": ["decision"],
                "doc_structure": {"enabled": False, "exempt": ".github/doc-structure-exempt.txt",
                                  "headings": ["## What goes here", "## What does not go here"],
                                  "done_index": True}}


class SddParamsTest(unittest.TestCase):
    """The project's sdd parameters (KIT-067), the sdd section of .ai-kit.yaml since KIT-087 P4: schema-checked keys
    that fail the spec check, kit defaults, a resolved view. Each fixture writes them as an `sdd:` block that
    write_spec moves into the profile (review_rounds and visual_approval to their homes)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.spec = self.root / "docs" / "spec"
        self.spec.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def index(self, extra=""):
        write_spec(self.root, SPEC_INDEX.format(extra=extra))

    def run_both(self, *args):
        """The full check, then the structural one: python -S hides pyyaml and jsonschema."""
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        runs = []
        for flags in ([], ["-S"]):
            runs.append(subprocess.run([sys.executable, *flags, str(CHECK_SPEC), *args, str(self.spec), str(SCHEMAS)],
                                       capture_output=True, text=True, check=False, env=env))
        self.assertIn("spec validation will be structural", runs[1].stderr)
        return runs

    def assert_passes(self):
        for result in self.run_both():
            self.assertEqual(result.returncode, 0, result.stderr)

    def assert_fails(self, *messages):
        """A refused key fails --params in both modes (KIT-087 P4: the profile is its home; the spec run itself keeps
        the key's default, KIT-100)."""
        for result in self.run_both("--params"):
            self.assertEqual(result.returncode, 1, result.stderr)
            for message in messages:
                self.assertIn(message, result.stderr)

    def params(self):
        """check_spec.py --params in both modes; both print the same resolved section, here cut to the keys the sdd:
        block had (the profile-only keys are test_profile.py's)."""
        runs = self.run_both("--params")
        for result in runs:
            self.assertEqual(result.returncode, 0, result.stderr)
        resolved = [json.loads(result.stdout) for result in runs]
        self.assertEqual(resolved[0], resolved[1])
        return {key: value for key, value in resolved[0].items() if key in SDD_DEFAULTS}

    def test_spec_without_block_passes(self):
        self.index()
        self.assert_passes()

    def test_every_key_set_passes(self):
        self.index(SDD_FULL)
        self.assert_passes()

    def test_flow_block_passes(self):
        self.index("sdd: {tracker: none, pr_unit: feat, plan_sections: [Tests, Risks]}\n")
        self.assert_passes()

    def test_the_templates_carry_no_block_and_pass(self):
        """KIT-087 P4: no spec.md template init-spec.sh copies carries an sdd: block, which would now fail; each
        passes and resolves the kit defaults (a game project's preset comes from project.kind in .ai-kit.yaml)."""
        templates = VALIDATIONS.parents[2] / "plugins" / "guardrails" / "templates"
        for name in ("spec-index-business.md", "spec-index-game.md", "spec-index-tooling.md"):
            with self.subTest(template=name):
                text = (templates / name).read_text()
                (self.spec / "spec.md").write_text(text.replace("YYYY-MM-DD", "2026-11-14"))
                self.assertNotIn("\nsdd:", text)
                self.assert_passes()
                self.assertEqual(self.params(), SDD_DEFAULTS)

    def test_unknown_tracker_fails(self):
        self.index("sdd:\n  tracker: jira\n")
        self.assert_fails("sdd.tracker 'jira' is not one of ['github', 'none']")

    def test_unknown_key_fails(self):
        self.index("sdd:\n  trackr: none\n")
        self.assert_fails("sdd.trackr is not a known key")

    def test_block_must_be_a_map(self):
        self.index("sdd: [needs]\n")
        self.assert_fails("sdd must be a map")

    def test_plan_sections_keep_risks_and_tests(self):
        self.index("sdd:\n  plan_sections: [Design, Tests]\n")
        self.assert_fails("sdd.plan_sections must include 'Risks'")

    def test_unknown_plan_section_fails(self):
        self.index("sdd:\n  plan_sections: [Design, Risks, Tests, Budget]\n")
        self.assert_fails("sdd.plan_sections item 'Budget' is not one of")

    def test_integer_below_minimum_fails(self):
        self.index("sdd:\n  max_chain: 0\n  review_rounds: -1\n")
        self.assert_fails("sdd.max_chain 0 is below the minimum 1", "review.rounds -1 is below the minimum 1")

    def test_max_feat_tasks_below_minimum_fails(self):
        self.index("sdd:\n  max_feat_tasks: 0\n")
        self.assert_fails("sdd.max_feat_tasks 0 is below the minimum 1")

    def test_boolean_key_refuses_a_word(self):
        self.index("sdd:\n  needs: maybe\n")
        self.assert_fails("sdd.needs must be a boolean")

    def test_bundle_unknown_key_fails(self):
        self.index("sdd:\n  bundle: {rows: 3, pts: 6}\n")
        self.assert_fails("sdd.bundle.pts is not a known key")

    def test_rule_paths_must_stay_inside_the_repo(self):
        self.index("sdd:\n  rule_paths: {json: [../shared]}\n")
        self.assert_fails("sdd.rule_paths.json item '../shared' does not match")

    def test_unknown_visual_approval_fails(self):
        self.index("sdd:\n  visual_approval: product\n")
        self.assert_fails("evidence.visual_approval 'product' is not one of ['owner', 'reviewer', 'none']")

    def test_owner_approvals_list_change_kinds(self):
        self.index("sdd:\n  owner_approvals: [decision, Protocol Version]\n")
        self.assert_fails("sdd.owner_approvals item 'Protocol Version' does not match")

    def test_owner_approvals_must_be_a_list(self):
        self.index("sdd:\n  owner_approvals: decision\n")
        self.assert_fails("sdd.owner_approvals must be a list")

    def test_structural_parser_reads_comments_nulls_and_empty_values_like_pyyaml(self):
        """Both modes resolve the same block from trailing comments, NULL/Null/~ and an empty value."""
        self.index("protocol_version: 1  # bumped on a wire change\n"
                   "sdd:\n"
                   "  tracker: none  # no issue tracker\n"
                   "  pr_unit: \"feat\"  # quoted, then a comment\n"
                   "  row_check: NULL\n"
                   "  cut_command: Null\n"
                   "  plan_sections:\n"
                   "    - Tests  # always on\n"
                   "    - Risks\n"
                   "  owner_approvals: [decision, protocol-version]  # flow list, then a comment\n")
        self.assert_passes()
        resolved = self.params()
        self.assertEqual((resolved["tracker"], resolved["pr_unit"], resolved["row_check"], resolved["cut_command"]),
                         ("none", "feat", None, None))
        self.assertEqual(resolved["plan_sections"], ["Tests", "Risks"])
        self.assertEqual(resolved["owner_approvals"], ["decision", "protocol-version"])

    def test_empty_value_is_null_in_both_modes(self):
        self.index("sdd:\n  row_check:\n")
        self.assertIsNone(self.params()["row_check"])

    def test_params_prints_the_kit_defaults(self):
        self.index()
        self.assertEqual(self.params(), SDD_DEFAULTS)

    def test_params_without_spec_index_prints_the_kit_defaults(self):
        self.assertEqual(self.params(), SDD_DEFAULTS)

    def test_params_merge_values_over_defaults(self):
        self.index("sdd:\n  tracker: none\n  bundle: {rows: 3}\n  rule_paths: {json: [game/protocol]}\n")
        (self.spec / "journeys").mkdir()
        resolved = self.params()
        self.assertEqual(resolved["tracker"], "none")
        self.assertEqual(resolved["bundle"], {"rows": 3, "points": 3, "high_rows": 1})
        self.assertEqual(resolved["rule_paths"], {"json": ["game/protocol"]})
        self.assertTrue(resolved["journeys"], "without the key, a journeys/ folder turns journeys on")
        self.assertEqual(resolved["max_chain"], 4)

    def test_params_refuse_an_invalid_block(self):
        self.index("sdd:\n  pr_unit: wave\n")
        for result in self.run_both("--params"):
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("sdd.pr_unit 'wave' is not one of ['task', 'feat']", result.stderr)


if __name__ == "__main__":
    unittest.main()
