"""check_spec.py FEAT<->REQ cross-check: both frontmatters must agree on every link."""
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


if __name__ == "__main__":
    unittest.main()
