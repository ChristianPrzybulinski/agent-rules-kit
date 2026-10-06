"""kpi.py: per-batch review-loop numbers computed from a fixture ledger."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KPI = Path(__file__).resolve().parent.parent.parent / "tools" / "kpi.py"
HEADER = "at,batch,role,kind,pr,issue,sha,round,model,duration_s,usd,note\n"

TWO_PRS = HEADER + "".join(line + "\n" for line in [
    "2026-10-06T10:00:00+00:00,b1,devin,implement,r#1,1,,,m,900,,",
    "2026-10-06T10:00:00+00:00,b1,devin,implement,r#2,2,,,m,900,,",
    "2026-10-06T10:20:00+00:00,b1,claude,review,r#1,1,aaa,1,m,300,,verdict=flagged findings=3 spec=2",
    "2026-10-06T10:30:00+00:00,b1,claude,review,r#2,2,bbb,1,m,300,,verdict=approved findings=0 extra=ignored",
    "2026-10-06T11:30:00+00:00,b1,claude,review,r#1,1,ccc,2,m,300,,verdict=approved findings=0 spec=0",
])


class KpiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_kpi(self, text, *args):
        ledger = self.dir / "ledger.csv"
        ledger.write_text(text)
        return subprocess.run([sys.executable, "-B", str(KPI), str(ledger), *args],
                              capture_output=True, text=True, check=False)

    def test_two_prs_in_one_batch(self):
        result = self.run_kpi(TWO_PRS, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        batch = json.loads(result.stdout)[0]
        self.assertEqual(batch["batch"], "b1")
        self.assertEqual(batch["prs"], 2)
        self.assertEqual(batch["first_pass_approval"], 50.0)
        self.assertEqual((batch["approved"], batch["decided"]), (1, 2))
        self.assertEqual(batch["rounds_per_pr"], 1.5)
        self.assertEqual(batch["rounds_max"], 2)
        self.assertEqual(batch["spec_findings"], 66.7)
        self.assertEqual((batch["spec"], batch["findings"]), (2, 3))
        self.assertEqual(batch["median_time_to_green_min"], 60.0)

    def test_text_line_names_every_metric(self):
        result = self.run_kpi(TWO_PRS)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^batch b1: prs=2 first_pass_approval=50\.0% \(1/2\) .*median_time_to_green=60\.0 min")

    def test_batch_without_verdict_tokens_is_not_available(self):
        text = HEADER + "2026-10-06T10:00:00+00:00,b2,claude,review,r#9,9,aaa,1,m,300,,\n"
        result = self.run_kpi(text, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        batch = json.loads(result.stdout)[0]
        for key in ("first_pass_approval", "spec_findings", "median_time_to_green_min"):
            self.assertIsNone(batch[key], key)
        self.assertIn("first_pass_approval=n/a", self.run_kpi(text).stdout)

    def test_batch_filter(self):
        text = TWO_PRS + "2026-10-07T10:00:00+00:00,b3,claude,review,r#7,7,zzz,1,m,300,,verdict=approved findings=0\n"
        result = self.run_kpi(text, "--batch", "b3", "--json")
        self.assertEqual([b["batch"] for b in json.loads(result.stdout)], ["b3"])

    def test_missing_file_and_bad_header_exit_2(self):
        missing = subprocess.run([sys.executable, "-B", str(KPI), str(self.dir / "absent.csv")],
                                 capture_output=True, text=True, check=False)
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(self.run_kpi("a,b,c\n1,2,3\n").returncode, 2)


if __name__ == "__main__":
    unittest.main()
