"""A FEAT reference must retain the task gates and selected-row scope."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

LAYER = "unit"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr_gates as gates  # noqa: E402

ISSUE = {
    "body": "## Files (owned areas)\n`code/src/**`\n\n## Tasks\n"
            "| ID | Task | Files |\n|---|---|---|\n"
            "| T1 | First \\| task | `code/src/first.py` |\n"
            "| T2 | Second task | `code/src/second.py` |\n",
    "labels": [],
}
BODY = "## Task rows\nT1\n\n## Proof\n```proof\npython3 -m unittest\n```\n\nRefs org/docs#99\n"


class FeatureIssueGates(unittest.TestCase):
    def setUp(self) -> None:
        config = {"repos": {"code": {}}, "proof_allowlist": ["python3"],
                  "protected_paths": {"sensitive": ["src/first.py"]}}
        patcher = mock.patch.multiple(gates, OWNER="org", BACKLOG="docs", CONFIG=config)
        patcher.start()
        self.addCleanup(patcher.stop)

    def report(self, body: str = BODY, files: tuple = ("src/first.py",),
               issue: dict | None = None) -> tuple[str, bool]:
        record = issue if issue is not None else {**ISSUE, "labels": [{"name": "sensitive"}]}
        pr = {"body": body, "head": {"sha": "abc123"}, "labels": []}
        def api(token: str, path: str, params: dict | None = None) -> dict:
            return record if path.endswith("/issues/99") else pr
        with mock.patch.object(gates, "_api", side_effect=api), \
                mock.patch.object(gates, "_api_list", return_value=[{"filename": f} for f in files]), \
                mock.patch.object(gates, "_ci_state", return_value="green"), \
                mock.patch.object(gates, "_open_pr_files", return_value={}):
            return gates.gate_report("code", 5, "fixture-token")

    def test_reference_runs_all_task_gates_and_accepts_selected_scope(self) -> None:
        report, ok = self.report()
        self.assertTrue(ok, report)
        self.assertNotIn("no-task", report)
        self.assertIn("✅ scope: owned areas", report)
        self.assertIn("✅ proof: commands allowlisted", report)

    def test_other_tasks_files_cannot_widen_selected_scope(self) -> None:
        report, ok = self.report(files=("src/second.py",))
        self.assertFalse(ok, report)
        self.assertIn("❌ scope: owned areas", report)
        self.assertIn("src/second.py", report)

    def test_missing_proof_or_protected_label_still_fails(self) -> None:
        report, ok = self.report(body=BODY.replace("python3 -m unittest", ""))
        self.assertFalse(ok, report)
        self.assertIn("❌ contract: proof block", report)
        report, ok = self.report(issue=ISSUE)
        self.assertFalse(ok, report)
        self.assertIn("❌ scope: protected paths", report)

    def test_missing_unknown_duplicate_or_malformed_row_selection_fails(self) -> None:
        for row_text in ("", "T9", "T1 T1", "T1; T2", "T1\u2028T2"):
            with self.subTest(rows=row_text):
                report, ok = self.report(body=BODY.replace("\nT1\n", f"\n{row_text}\n"))
                self.assertFalse(ok, report)
                self.assertIn("❌ scope: owned areas", report)

    def test_missing_or_duplicate_task_rows_in_issue_fail_closed(self) -> None:
        bodies = ("## Files (owned areas)\n`code/src/**`",
                  ISSUE["body"] + "| T1 | Duplicate | `code/src/**` |\n")
        for text in bodies:
            with self.subTest(body=text):
                report, ok = self.report(issue={**ISSUE, "body": text})
                self.assertFalse(ok, report)
                self.assertIn("❌ scope: owned areas", report)

    def test_multiple_selected_rows_allow_only_their_union(self) -> None:
        report, ok = self.report(body=BODY.replace("\nT1\n", "\nT1, T2\n"),
                                 files=("src/first.py", "src/second.py"))
        self.assertTrue(ok, report)
        self.assertNotIn("no-task", report)

    def test_legacy_closing_issue_still_uses_its_own_files(self) -> None:
        record = {"body": "## Files (owned areas)\n`code/src/second.py`", "labels": []}
        report, ok = self.report(body=BODY.replace("Refs", "Closes"), files=("src/second.py",), issue=record)
        self.assertTrue(ok, report)
        self.assertNotIn("no-task", report)
        report, ok = self.report(body=BODY.replace("Refs", "Closes"), files=("other.py",), issue=record)
        self.assertFalse(ok, report)


if __name__ == "__main__":
    unittest.main()
