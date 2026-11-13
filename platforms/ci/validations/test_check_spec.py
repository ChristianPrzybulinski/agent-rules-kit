"""check_spec.py FEAT<->REQ cross-check (both frontmatters must agree on every link), progress files, conflict
markers and the project's decision kinds."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
