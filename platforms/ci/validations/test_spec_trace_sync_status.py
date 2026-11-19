"""spec_trace sync-status tests (KIT-073): task and FEAT status derived from canned GitHub data, `gh` mocked.

Ported from a consumer project's suite with neutral repositories: the backlog `org/product` (once named
`org/product-docs`) and two code repositories whose PRs close backlog issues. Row words follow
sdd-tasks/references/task-issue.md § States; the FEAT status stops at in-progress (KIT-069).
"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/spec_trace.py",)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec_trace as trace  # noqa: E402
from test_profile import write_spec  # noqa: E402

FEAT11 = """\
---
id: {fid}
title: "{title}"
status: {status}
requirements: []
created: "2026-10-05"
updated: "2026-10-05"
---

# {fid}

## Tasks

| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Model | Wave | Item |
|---|---|---|---|---|---|---|---|---|---|---|
{rows}

## History

- 2026-10-05 specify: created.

Not verified: implementation.
"""

FEAT7 = """\
---
id: {fid}
title: "{title}"
status: {status}
requirements: []
created: "2026-10-05"
updated: "2026-10-05"
---

# {fid}

## Tasks

| ID | Task | Files | Proof of completion | Covers | Depends on | Status |
|---|---|---|---|---|---|---|
{rows}

## History

- 2026-10-05 specify: created.
"""

ROW11 = "| {tid} | {task} | `a/**` | ci green | CA-1 | — | {status} | Low | small | 0 | — |"
ROW7 = "| {tid} | {task} | `a/**` | ci green | CA-1 | — | {status} |"

REPO, OLD = "org/product", "org/product-docs"
LIB = "org/lib"  # a second repository whose issues rows cite in full (KIT-112)
CLIENT, SERVER = "org/product-client", "org/product-server"

SPEC_MD = f"""\
---
project: "fixture"
version: "0.1.0"
updated: "2026-10-05"
sdd:
  tracker: github
  github: {{repo: {REPO}, pr_repos: [{CLIENT}, {SERVER}], aliases: [{OLD}], blocked_labels: ["blocked", "needs-human"], progress_labels: ["status:in-progress", "review:pending"]}}
---

# Spec

The in-progress FEATs, derived by sync-status:
<!-- sync-status:begin -->
- none
<!-- sync-status:end -->

The FEAT counts, derived by sync-status:
<!-- sync-counts:begin -->
0 FEATs.
<!-- sync-counts:end -->

### Features

| ID | Title | Status | Card | Flag |
|---|---|---|---|---|
| [FEAT-001](features/FEAT-001.md) | First fixture | planned | — | — |
| [FEAT-002](features/FEAT-002.md) | Second fixture | planned | — | — |
"""

ISSUES = f"repos/{REPO}/issues?state=all"
PULLS = "repos/{repo}/pulls?state=all"
TODAY = "2026-10-06"


def write(root, rel, text):
    if rel.endswith("spec/spec.md"):  # its sdd: block goes to .ai-kit.yaml (KIT-087 P4)
        return write_spec(root, textwrap.dedent(text), rel)
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def issue(number, title, state="open", labels=(), reason=None):
    out = {"number": number, "title": title, "state": state, "labels": [{"name": lb} for lb in labels]}
    if reason:
        out["state_reason"] = reason
    return out


def pull(state="closed", merged=True, body=""):
    return {"state": state, "merged_at": "2026-10-05T12:00:00Z" if merged else None, "body": body}


def canned(routes):
    """Fake `gh api`: routes maps a URL substring to {page: payload} for paged lists."""
    def gh(query):
        for sub, payload in routes.items():
            if sub not in query:
                continue
            page = re.search(r"[?&]page=(\d+)", query)
            return subprocess.CompletedProcess(["gh"], 0, json.dumps(payload.get(int(page.group(1)) if page else 1, [])),
                                               "")
        return subprocess.CompletedProcess(["gh"], 1, "", f"no canned route for {query}")
    return gh


def feat_rows(*specs):
    return "\n".join(ROW11.format(tid=tid, task=task, status=status) for tid, task, status in specs)


class SyncStatusTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.spec = self.root / "docs/spec"
        self.spec_md = write(self.root, "docs/spec/spec.md", SPEC_MD)
        self.path1 = write(self.root, "docs/spec/features/FEAT-001.md", FEAT11.format(
            fid="FEAT-001", title="First fixture", status="planned",
            rows=feat_rows(("T1", "first, a \\| pipe", "todo"), ("T2", "second", "todo"), ("T3", "third", "todo"))))
        self.path2 = write(self.root, "docs/spec/features/FEAT-002.md", FEAT7.format(
            fid="FEAT-002", title="Second fixture", status="planned",
            rows=ROW7.format(tid="T1", task="only task", status="todo")))

    def tearDown(self):
        self.tmp.cleanup()

    def run_sync(self, gh, write=True):
        spec = trace.load(self.spec)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = trace.sync_status(spec, trace.github_settings(self.spec), write, TODAY, gh)
        return code, out.getvalue()

    def text(self, path):
        return path.read_text(encoding="utf-8")

    def status(self, fid, tid):
        return trace.load(self.spec).feats[fid]["task_status"][tid]

    def routes(self, issues, pulls=None):
        """Canned listings: the backlog issues and one `pulls?state=all` page per PR repository."""
        routes = {ISSUES: {1: issues}}
        for repo in (REPO, CLIENT, SERVER):
            listed = [dict(pr, number=n) for (r, n), pr in (pulls or {}).items() if r == repo]
            routes[PULLS.format(repo=repo)] = {1: listed}
        return canned(routes)

    def test_closed_bundle_member_tracks_primary_without_a_warning(self):
        primary = issue(10, "[FEAT-001 T1] First — bundled with FEAT-001 T2 #11")
        member = issue(11, "[FEAT-001 T2] Second", "closed", reason="not_planned")
        for state, prs, expected in (("open", {}, "todo"),
                                    ("open", {(REPO, 20): pull("open", False, f"Closes {REPO}#10")}, "doing"),
                                    ("closed", {(REPO, 20): pull(body=f"Closes {REPO}#10")}, "done")):
            with self.subTest(state=state, expected=expected):
                code, output = self.run_sync(self.routes([{**primary, "state": state}, member], prs))
                self.assertEqual(code, 0)
                self.assertNotIn("closed without a merged PR", output)
                self.assertEqual(self.status("FEAT-001", "T2"), expected)

    def test_not_planned_close_cancels_the_row(self):
        _, output = self.run_sync(self.routes([issue(11, "[FEAT-001 T2] Second", "closed", reason="not_planned")]))
        self.assertIn("FEAT-001 T2: todo -> cancelled (closed as not planned)", output)
        self.assertEqual(self.status("FEAT-001", "T2"), "cancelled")

    def test_not_planned_close_keeps_a_done_row_and_warns(self):
        """A row already done (its PR recorded by mark-done) is never cancelled by a stray not-planned issue."""
        self.path1.write_text(self.text(self.path1).replace("| T3 | third | `a/**` | ci green | CA-1 | — | todo |",
                                                            "| T3 | third | `a/**` | ci green | CA-1 | — | done |"),
                              encoding="utf-8")
        _, out = self.run_sync(self.routes([issue(13, "[FEAT-001 T3] third", "closed", reason="not_planned")]))
        self.assertIn("WARN FEAT-001 T3: product#13 closed as not planned, but the row is done", out)
        self.assertNotIn("T3: done -> cancelled", out)
        self.assertEqual(self.status("FEAT-001", "T3"), "done")

    def set_row(self, tid, status, path=None):
        path = path or self.path1
        text = self.text(path)
        old = next(line for line in text.splitlines() if line.startswith(f"| {tid} |"))
        cells = old.split(" | ")
        cells[6] = status
        path.write_text(text.replace(old, " | ".join(cells)), encoding="utf-8")

    def test_a_cancelled_row_never_reopens(self):
        """Review finding 1: a cancelled row whose issue, closed as not planned, keeps a stale blocked label (or any
        later activity) stays cancelled."""
        self.set_row("T3", "cancelled")
        for state, labels, reason, prs in (("closed", ["blocked"], "not_planned", {}),
                                          ("open", ["status:in-progress"], None, {}),
                                          ("closed", [], None, {(CLIENT, 90): pull(body=f"Closes {REPO}#13")})):
            with self.subTest(state=state, labels=labels):
                _, out = self.run_sync(self.routes([issue(13, "[FEAT-001 T3] third", state, labels, reason)], prs))
                self.assertNotIn("T3: cancelled ->", out)
                self.assertEqual(self.status("FEAT-001", "T3"), "cancelled")

    def test_a_not_planned_close_beats_a_blocked_label(self):
        gh = self.routes([issue(12, "[FEAT-001 T2] second", "closed", ["blocked"], reason="not_planned")])
        _, out = self.run_sync(gh)
        self.assertIn("FEAT-001 T2: todo -> cancelled (closed as not planned)", out)
        self.assertEqual(self.status("FEAT-001", "T2"), "cancelled")

    def test_a_closed_issue_with_a_stale_blocked_label_keeps_the_row_and_warns(self):
        gh = self.routes([issue(12, "[FEAT-001 T2] second", "closed", ["blocked"], reason="completed")])
        _, out = self.run_sync(gh)
        self.assertIn("WARN FEAT-001 T2: product#12 closed without a merged PR", out)
        self.assertEqual(self.status("FEAT-001", "T2"), "todo")

    def test_a_delivered_feat_with_cancelled_rows_passes_the_status_gate(self):
        """The repro of finding 1: after the migration's superseded -> cancelled, a delivered FEAT stays clean."""
        path = write(self.root, "docs/spec/features/FEAT-003.md", FEAT11.format(
            fid="FEAT-003", title="Delivered fixture", status="delivered",
            rows=feat_rows(("T1", "a", "done"), ("T2", "b", "cancelled"))))
        gh = self.routes([issue(31, "[FEAT-003 T1] a", "closed"),
                          issue(32, "[FEAT-003 T2] b", "closed", ["blocked"], reason="not_planned")],
                         {(CLIENT, 90): pull(body=f"Closes {REPO}#31")})
        code, out = self.run_sync(gh)
        self.assertEqual(code, 0)
        self.assertIn("| b | `a/**` | ci green | CA-1 | — | cancelled |", self.text(path))
        self.assertEqual([e for e in trace.status_errors(trace.load(self.spec)) if "FEAT-003" in e], [])

    def test_a_kit_bundle_title_names_every_row(self):
        gh = self.routes([issue(10, "[FEAT-001 T1+T2] First and second", "closed")],
                         {(REPO, 20): pull(body=f"Closes {REPO}#10")})
        _, output = self.run_sync(gh)
        self.assertIn("FEAT-001 T1: todo -> done (product#20)", output)
        self.assertIn("FEAT-001 T2: todo -> done (product#20)", output)

    def test_bundle_member_inherits_primary_block(self):
        primary = issue(10, "[FEAT-001 T1] First — bundled with FEAT-001 T2 #11", labels=["needs-human"])
        member = issue(11, "[FEAT-001 T2] Second", "closed", reason="not_planned")
        _, output = self.run_sync(self.routes([primary, member]))
        self.assertNotIn("closed without a merged PR", output)
        self.assertEqual(self.status("FEAT-001", "T2"), "blocked")

    def test_pr_closing_every_member_is_recorded_once_per_row(self):
        primary = issue(10, "[FEAT-001 T1] First — bundled with FEAT-001 T2 #11", "closed")
        member = issue(11, "[FEAT-001 T2] Second", "closed", reason="not_planned")
        pr = pull(body=f"Closes {REPO}#10\nCloses {REPO}#11")
        _, output = self.run_sync(self.routes([primary, member], {(REPO, 20): pr}))
        self.assertIn("FEAT-001 T2: todo -> done (product#20)", output)
        self.assertNotIn("product#20, product#20", output)

    def test_merged_pr_marks_done_and_derives_in_progress(self):
        gh = self.routes([issue(11, "[FEAT-001 T1] first, a | pipe", "closed")],
                         {(CLIENT, 90): pull(body=f"Closes {REPO}#11")})
        code, out = self.run_sync(gh)
        self.assertEqual(code, 0)
        self.assertIn("FEAT-001 T1: todo -> done (product-client#90)", out)
        self.assertIn("FEAT-001: planned -> in-progress", out)
        text = self.text(self.path1)
        self.assertIn("| T1 | first, a \\| pipe | `a/**` | ci green | CA-1 | — | done | Low | small | 0 | — |", text)
        self.assertIn("| T2 | second | `a/**` | ci green | CA-1 | — | todo | Low | small | 0 | — |", text)
        self.assertIn("status: in-progress\n", text)
        self.assertIn('updated: "2026-10-06"', text)
        self.assertIn("- 2026-10-06 sync: status derived from GitHub (T1 todo -> done via product-client#90).\n\n"
                      "Not verified: implementation.", text)

    def test_an_earlier_backlog_name_and_the_code_repositories_still_close(self):
        routes = {PULLS.format(repo=REPO): {1: [dict(pull(body=f"Closes {OLD}#11"), number=90)]},
                  PULLS.format(repo=CLIENT): {1: [dict(pull(body=f"Closes {REPO}#12"), number=90)]},
                  PULLS.format(repo=SERVER): {1: []}}
        result = trace.closing_prs(trace.github_settings(self.spec), canned(routes))
        self.assertEqual(result[11][0]["ref"], "product#90")
        self.assertEqual(result[12][0]["ref"], "product-client#90")

    def test_open_pr_marks_doing_in_a_7_column_table(self):
        gh = self.routes([issue(21, "[FEAT-002 T1] only task")],
                         {(REPO, 91): pull(state="open", merged=False, body="Closes #21")})
        code, out = self.run_sync(gh)
        self.assertEqual(code, 0)
        self.assertIn("FEAT-002 T1: todo -> doing (product#91)", out)
        self.assertIn("| T1 | only task | `a/**` | ci green | CA-1 | — | doing |", self.text(self.path2))

    def test_a_progress_label_marks_doing(self):
        _, out = self.run_sync(self.routes([issue(21, "[FEAT-002 T1] only task", labels=["review:pending"])]))
        self.assertIn("FEAT-002 T1: todo -> doing (label:review:pending)", out)

    def test_blocked_label_beats_an_open_pr(self):
        gh = self.routes([issue(11, "[FEAT-001 T1] first", labels=["blocked"])],
                         {(CLIENT, 90): pull(state="open", merged=False, body=f"Closes {REPO}#11")})
        code, out = self.run_sync(gh)
        self.assertEqual(code, 0)
        self.assertIn("FEAT-001 T1: todo -> blocked (label:blocked)", out)
        self.assertIn("| — | blocked | Low | small | 0 | — |", self.text(self.path1))

    def test_closed_without_merged_pr_keeps_todo_and_warns(self):
        gh = self.routes([issue(12, "[FEAT-001 T2] second", "closed", reason="completed")],
                         {(SERVER, 92): pull(merged=False, body=f"Refs {REPO}#12 only")})
        code, out = self.run_sync(gh)
        self.assertEqual(code, 0)
        self.assertIn("WARN FEAT-001 T2: product#12 closed without a merged PR", out)
        self.assertIn("| T2 | second | `a/**` | ci green | CA-1 | — | todo | Low | small | 0 | — |",
                      self.text(self.path1))

    def test_done_row_without_an_issue_is_kept_and_reported(self):
        self.path1.write_text(self.text(self.path1).replace("| T3 | third | `a/**` | ci green | CA-1 | — | todo |",
                                                            "| T3 | third | `a/**` | ci green | CA-1 | — | done |"),
                              encoding="utf-8")
        code, out = self.run_sync(self.routes([]))
        self.assertEqual(code, 0)
        self.assertIn("FEAT-001 T1: todo (no issue)", out)
        self.assertIn("FEAT-001 T3: done (no issue)", out)
        self.assertIn("| — | done |", self.text(self.path1))

    def test_two_issues_for_one_task_warn_and_merge_the_evidence(self):
        gh = self.routes([issue(11, "[FEAT-001 T1] first"), issue(12, "[FEAT-001 T1] Fix round", "closed")],
                         {(CLIENT, 90): pull(body=f"Closes {REPO}#12")})
        code, out = self.run_sync(gh)
        self.assertEqual(code, 0)
        self.assertIn("WARN FEAT-001 T1: task issues #11, #12 — evidence merged", out)
        self.assertIn("FEAT-001 T1: todo -> done (product-client#90)", out)

    def test_only_open_issues_lend_their_labels(self):
        """Review B1 follow-up: a closed issue still labelled blocked must not block the row its open issue tracks."""
        gh = self.routes([issue(12, "[FEAT-001 T2] second", "closed", ["blocked"], reason="completed"),
                          issue(22, "[FEAT-001 T2] Fix round")])
        _, out = self.run_sync(gh)
        self.assertIn("WARN FEAT-001 T2: task issues #12, #22 — evidence merged", out)
        self.assertNotIn("T2: todo -> blocked", out)
        self.assertEqual(self.status("FEAT-001", "T2"), "todo")

    def test_all_rows_done_stops_at_in_progress(self):
        gh = self.routes([issue(11, "[FEAT-001 T1] a", "closed"), issue(12, "[FEAT-001 T2] b", "closed"),
                          issue(13, "[FEAT-001 T3] c", "closed")],
                         {(CLIENT, 90): pull(body=f"Closes {REPO}#11"),
                          (SERVER, 91): pull(body=f"Closes {REPO}#12 — FEAT-001 T2 context"),
                          (REPO, 92): pull(body="Closes #13")})
        code, out = self.run_sync(gh)
        self.assertEqual(code, 0)
        self.assertIn("FEAT-001: planned -> in-progress", out)
        self.assertNotIn("delivered", out)
        self.assertNotIn("validated", out)
        self.assertIn("status: in-progress\n", self.text(self.path1))

    def test_frozen_statuses_are_never_rewritten(self):
        for fid, status in (("FEAT-003", "delivered"), ("FEAT-004", "cancelled")):
            write(self.root, f"docs/spec/features/{fid}.md", FEAT11.format(
                fid=fid, title="Frozen fixture", status=status, rows=feat_rows(("T1", "a", "done"))))
        gh = self.routes([issue(31, "[FEAT-003 T1] a", "closed"), issue(32, "[FEAT-004 T1] b", "closed")],
                         {(CLIENT, 90): pull(body=f"Closes {REPO}#31"), (SERVER, 91): pull(body=f"Closes {REPO}#32")})
        code, out = self.run_sync(gh)
        self.assertEqual(code, 0)
        for fid, want in (("FEAT-003", "delivered"), ("FEAT-004", "cancelled")):
            self.assertIn(f"status: {want}\n", self.text(self.root / f"docs/spec/features/{fid}.md"))
            self.assertNotIn(f"{fid}: {want} ->", out)

    def test_superseded_row_is_never_rewritten(self):
        self.path1.write_text(self.text(self.path1).replace("| T3 | third | `a/**` | ci green | CA-1 | — | todo |",
                                                            "| T3 | third | `a/**` | ci green | CA-1 | — | superseded |"),
                              encoding="utf-8")
        gh = self.routes([issue(13, "[FEAT-001 T3] third", "closed")], {(CLIENT, 90): pull(body=f"Closes {REPO}#13")})
        code, out = self.run_sync(gh)
        self.assertEqual(code, 0)
        self.assertIn("| — | superseded |", self.text(self.path1))
        self.assertNotIn("T3 superseded ->", out)

    def test_second_run_is_a_noop(self):
        gh = self.routes([issue(11, "[FEAT-001 T1] a", "closed")], {(CLIENT, 90): pull(body=f"Closes {REPO}#11")})
        self.run_sync(gh)
        once = {p: self.text(p) for p in (self.path1, self.path2, self.spec_md)}
        code, out = self.run_sync(gh)
        self.assertEqual(code, 0)
        self.assertNotIn("todo -> done", out)
        self.assertEqual({p: self.text(p) for p in once}, once)
        self.assertEqual(self.text(self.path1).count("sync: status derived from GitHub"), 1)

    def test_spec_index_status_cell_and_marker_block(self):
        gh = self.routes([issue(11, "[FEAT-001 T1] a", "closed")], {(CLIENT, 90): pull(body=f"Closes {REPO}#11")})
        self.run_sync(gh)
        text = self.text(self.spec_md)
        self.assertIn("| [FEAT-001](features/FEAT-001.md) | First fixture | in-progress | — | — |", text)
        self.assertIn("| [FEAT-002](features/FEAT-002.md) | Second fixture | planned | — | — |", text)
        self.assertIn("<!-- sync-status:begin -->\n- FEAT-001 First fixture (1/3 done)\n<!-- sync-status:end -->", text)
        self.assertIn('updated: "2026-10-06"', text)
        self.assertIn("<!-- sync-counts:begin -->\n2 FEATs: 1 `planned`, 1 `in-progress`.\n<!-- sync-counts:end -->",
                      text)

    def test_counts_line_matches_its_own_canonical_form(self):
        """Ported from the consumer (review finding 4a): the counts line follows the FEAT files, names proposed and
        cancelled FEATs, and a second run leaves it as it is."""
        self.run_sync(self.routes([issue(11, "[FEAT-001 T1] a", "closed")],
                                  {(CLIENT, 90): pull(body=f"Closes {REPO}#11")}))
        for fid, status in (("FEAT-005", "proposed"), ("FEAT-006", "proposed"), ("FEAT-007", "proposed"),
                            ("FEAT-009", "cancelled")):
            write(self.root, f"docs/spec/features/{fid}.md", FEAT11.format(
                fid=fid, title="Counted fixture", status=status, rows=feat_rows(("T1", "x", "todo"))))
        code, _ = self.run_sync(self.routes([]))
        self.assertEqual(code, 0)
        text = self.text(self.spec_md)
        self.assertIn("<!-- sync-counts:begin -->\n6 FEATs: 3 `proposed` (FEAT-005–FEAT-007), 1 `planned`, "
                      "1 `in-progress`, 1 `cancelled` (FEAT-009).\n<!-- sync-counts:end -->", text)
        self.run_sync(self.routes([]))
        self.assertEqual(self.text(self.spec_md), text)

    def test_counts_line_needs_its_markers(self):
        self.spec_md.write_text(self.text(self.spec_md).replace(
            "<!-- sync-counts:begin -->\n0 FEATs.\n<!-- sync-counts:end -->\n", ""), encoding="utf-8")
        self.run_sync(self.routes([issue(11, "[FEAT-001 T1] a", "closed")],
                                  {(CLIENT, 90): pull(body=f"Closes {REPO}#11")}))
        self.assertNotIn("FEATs:", self.text(self.spec_md))

    def test_cells_outside_status_stay_byte_identical(self):
        gh = self.routes([issue(11, "[FEAT-001 T1] a", "closed")], {(CLIENT, 90): pull(body=f"Closes {REPO}#11")})
        before = self.text(self.path1)
        self.run_sync(gh)
        after = self.text(self.path1)
        old_row = next(line for line in before.splitlines() if line.startswith("| T1 |"))
        new_row = next(line for line in after.splitlines() if line.startswith("| T1 |"))
        strip = lambda line: [c for i, c in enumerate(trace.UNESCAPED_PIPE.split(line)) if i != 7]  # noqa: E731
        self.assertEqual(strip(old_row), strip(new_row))
        for line in before.splitlines():
            if line.startswith("| T") and not line.startswith("| T1 |"):
                self.assertIn(line, after)

    def test_dry_run_reports_but_writes_nothing(self):
        gh = self.routes([issue(11, "[FEAT-001 T1] a", "closed")], {(CLIENT, 90): pull(body=f"Closes {REPO}#11")})
        before = {p: self.text(p) for p in (self.path1, self.path2, self.spec_md)}
        code, out = self.run_sync(gh, write=False)
        self.assertEqual(code, 0)
        self.assertIn("FEAT-001 T1: todo -> done (product-client#90)", out)
        self.assertEqual({p: self.text(p) for p in before}, before)

    def test_no_request_names_one_pr_or_one_issue(self):
        queries = []
        listed = self.routes([issue(11, "[FEAT-001 T1] a", "closed"), issue(12, "[FEAT-001 T2] b"),
                              issue(13, "[FEAT-001 T3] c"), issue(21, "[FEAT-002 T1] d")],
                             {(REPO, 92): pull(body="Closes #13")})
        self.run_sync(lambda q: queries.append(q) or listed(q), write=False)
        self.assertEqual(sorted({q.split("?")[0] for q in queries}),
                         sorted(f"repos/{r}/{kind}" for r, kind in ((REPO, "issues"), (REPO, "pulls"),
                                                                    (CLIENT, "pulls"), (SERVER, "pulls"))))
        self.assertEqual(len(queries), 6, queries)  # a non-empty listing reads one more, empty, page

    def test_short_closes_counts_only_inside_the_backlog_repo(self):
        gh = self.routes([issue(11, "[FEAT-001 T1] a"), issue(12, "[FEAT-001 T2] b")],
                         {(CLIENT, 90): pull(body="Closes #11"), (REPO, 91): pull(body="Closes #12")})
        code, out = self.run_sync(gh, write=False)
        self.assertEqual(code, 0)
        self.assertNotIn("FEAT-001 T1: todo ->", out)
        self.assertIn("FEAT-001 T2: todo -> done (product#91)", out)

    def test_status_gate_agrees_with_the_written_files(self):
        gh = self.routes([issue(11, "[FEAT-001 T1] a", "closed")], {(CLIENT, 90): pull(body=f"Closes {REPO}#11")})
        self.run_sync(gh)
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = trace.main(["status", str(self.spec)])
        self.assertEqual(code, 0, err.getvalue())

    def test_a_failing_gh_call_stops_with_its_error(self):
        def gh(query):
            return subprocess.CompletedProcess(["gh"], 1, "", "HTTP 401: Bad credentials")
        with self.assertRaises(trace.SyncError) as stop:
            self.run_sync(gh)
        self.assertIn("HTTP 401", str(stop.exception))

    def item_rows(self, *rows):
        """FEAT-001 with (Tn, Status, Item) rows."""
        lines = "\n".join(ROW11.format(tid=tid, task="task", status=status).replace("| 0 | — |", f"| 0 | {item} |")
                          for tid, status, item in rows)
        self.path1.write_text(textwrap.dedent(FEAT11.format(fid="FEAT-001", title="First fixture", status="planned",
                                                            rows=lines)), encoding="utf-8")

    def test_the_item_cell_names_the_issue_even_after_a_rename(self):
        """#268: the KIT-068 Item cell is the mapping; the title is only the fallback."""
        self.item_rows(("T1", "todo", "#11"), ("T2", "todo", f"{OLD}#12"), ("T3", "todo", "—"))
        issues = [issue(11, "Renamed: no row prefix any more", "closed"), issue(12, "Also renamed", "closed"),
                  issue(13, "[FEAT-001 T3] Third", "closed")]
        pulls = {(REPO, 20): pull(body=f"Closes {REPO}#11"), (REPO, 21): pull(body=f"Closes {REPO}#12"),
                 (REPO, 22): pull(body=f"Closes {REPO}#13")}
        code, output = self.run_sync(self.routes(issues, pulls))
        self.assertEqual(code, 0, output)
        self.assertEqual([self.status("FEAT-001", t) for t in ("T1", "T2", "T3")], ["done", "done", "done"])

    def test_the_item_cell_wins_over_an_issue_whose_title_names_the_row(self):
        self.item_rows(("T1", "todo", "#11"))
        issues = [issue(11, "[FEAT-001 T1] Current", "open", labels=["blocked"]), issue(14, "[FEAT-001 T1] Old")]
        _, output = self.run_sync(self.routes(issues, {(REPO, 20): pull("open", False, f"Closes {REPO}#14")}))
        self.assertEqual(self.status("FEAT-001", "T1"), "blocked")
        self.assertNotIn("evidence merged", output)

    def test_an_item_of_a_repository_that_cannot_be_read_keeps_its_row_and_a_task_file_falls_back_to_the_title(self):
        """KIT-112 follow-up: no canned route for other/repo, so its row keeps its status instead of taking the
        backlog issue that shares its title; a TASK file has no repository and still reads the title."""
        self.item_rows(("T1", "todo", "other/repo#11"), ("T2", "todo", "TASK-007"))
        issues = [issue(11, "Not this one", "closed"), issue(15, "[FEAT-001 T1] First", labels=["blocked"]),
                  issue(16, "[FEAT-001 T2] Second", labels=["blocked"])]
        _, out = self.run_sync(self.routes(issues, {(REPO, 20): pull(body=f"Closes {REPO}#11")}))
        self.assertEqual([self.status("FEAT-001", t) for t in ("T1", "T2")], ["todo", "blocked"])
        self.assertIn("WARN other/repo: issues not read (", out)


    def test_feat_issue_never_fans_its_state_out_to_task_rows(self) -> None:
        for state, labels, reason, merged in (
                ("open", (), None, False),
                ("open", ("blocked",), None, False),
                ("open", ("status:in-progress",), None, False),
                ("closed", (), "not_planned", False),
                ("closed", (), "completed", True)):
            with self.subTest(state=state, labels=labels, reason=reason, merged=merged):
                self.item_rows(("T1", "done", "#99"), ("T2", "doing", f"{REPO}#99"),
                               ("T3", "todo", "#99"), ("T4", "blocked", "#99"))
                text = self.path1.read_text(encoding="utf-8")
                self.path1.write_text(text.replace('requirements: []', f'issue: "{REPO}#99"\nrequirements: []'),
                                      encoding="utf-8")
                gh = self.routes([issue(99, "[FEAT-001] One feature", state, labels, reason)],
                                 {(REPO, 200): pull("closed" if merged else "open", merged, "Closes #99")})
                code, output = self.run_sync(gh)
                self.assertEqual(code, 0, output)
                actual = trace.load(self.spec).feats["FEAT-001"]
                self.assertEqual(actual["task_status"], {"T1": "done", "T2": "doing", "T3": "todo", "T4": "blocked"})
                self.assertEqual(actual["status"], "in-progress")
                first = self.path1.read_text(encoding="utf-8")
                self.run_sync(gh)
                self.assertEqual(self.path1.read_text(encoding="utf-8"), first)

    def test_feat_issue_prevents_legacy_title_fallback_for_new_rows(self) -> None:
        self.item_rows(("T1", "todo", "—"))
        text = self.path1.read_text(encoding="utf-8")
        self.path1.write_text(text.replace('requirements: []', 'issue: "#99"\nrequirements: []'), encoding="utf-8")
        self.run_sync(self.routes([issue(12, "[FEAT-001 T1] Old issue", "closed")],
                                 {(REPO, 20): pull(body="Closes #12")}))
        self.assertEqual(self.status("FEAT-001", "T1"), "todo")

    def test_legacy_card_does_not_disable_task_issue_sync(self) -> None:
        self.item_rows(("T1", "todo", "#11"))
        text = self.path1.read_text(encoding="utf-8")
        self.path1.write_text(text.replace('requirements: []', 'card: 99\nrequirements: []'), encoding="utf-8")
        self.run_sync(self.routes([issue(11, "[FEAT-001 T1] Legacy", "closed")],
                                 {(REPO, 20): pull(body="Closes #11")}))
        self.assertEqual(self.status("FEAT-001", "T1"), "done")


    # KIT-112: a row's Item cell is read in the repository it names; `#11` exists in both the backlog and LIB.

    def lib_gh(self, backlog, lib, pulls=None, lib_issues=True):
        """Canned listings for the backlog, LIB and the PR repositories (`pulls`: {(repo, number): pull}); the
        queries are kept in `self.queries`."""
        self.queries = []
        routes = {ISSUES: {1: backlog}}
        if lib_issues:
            routes[f"repos/{LIB}/issues?state=all"] = {1: lib}
        for repo in (REPO, CLIENT, SERVER, LIB):
            routes[PULLS.format(repo=repo)] = {1: [dict(pr, number=n) for (r, n), pr in (pulls or {}).items()
                                                   if r == repo]}
        listed = canned(routes)
        return lambda query: self.queries.append(query) or listed(query)

    def run_lib(self, gh):
        settings = trace.github_settings(self.spec)
        settings["pr_repos"].append(LIB)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = trace.sync_status(trace.load(self.spec), settings, True, TODAY, gh)
        return code, out.getvalue()

    def two_repository_rows(self):
        self.item_rows(("T1", "todo", "#11"), ("T2", "todo", f"{LIB}#11"), ("T3", "todo", f"{LIB}#12"),
                       ("T4", "todo", f"{OLD}#11"))

    def test_item_issue_names_the_repository_of_each_cell(self):
        settings = trace.github_settings(self.spec)
        for cell, expected in (("#11", (REPO, 11)), (f"{REPO}#11", (REPO, 11)), (f"{OLD}#11", (REPO, 11)),
                               (f"{LIB}#11", (LIB, 11)), ("—", None), ("TASK-007", None), ("", None)):
            with self.subTest(cell=cell):
                self.assertEqual(trace.item_issue(cell, settings), expected)

    def test_closing_prs_reads_a_full_reference_in_its_repository_and_a_bare_one_in_the_prs_own(self):
        routes = {PULLS.format(repo=REPO): {1: [dict(pull(body=f"Closes #11\nCloses {OLD}#12"), number=1)]},
                  PULLS.format(repo=LIB): {1: [dict(pull(body="Closes #11"), number=2)]},
                  PULLS.format(repo=CLIENT): {1: [dict(pull(body=f"Closes {LIB}#12"), number=3)]},
                  PULLS.format(repo=SERVER): {1: []}}
        settings = trace.github_settings(self.spec)
        settings["pr_repos"].append(LIB)
        by_issue = trace.closing_prs(settings, canned(routes), by_issue=True)
        self.assertEqual({key: [p["ref"] for p in prs] for key, prs in by_issue.items()},
                         {(REPO, 11): ["product#1"], (REPO, 12): ["product#1"], (LIB, 11): ["lib#2"],
                          (LIB, 12): ["product-client#3"]})
        self.assertEqual(sorted(trace.closing_prs(settings, canned(routes))), [11, 12])  # the backlog's, as before

    def test_a_number_that_exists_in_two_repositories_is_read_in_the_one_the_cell_names(self):
        self.two_repository_rows()
        gh = self.lib_gh(
            [issue(11, "Backlog eleven", labels=["blocked"])],
            [issue(11, "Lib eleven", "closed"), issue(12, "Lib twelve", labels=["status:in-progress"])],
            {(LIB, 40): pull(body="Closes #11"), (REPO, 41): pull("open", False, "Closes #11"),
             (CLIENT, 42): pull("open", False, f"Closes {LIB}#12")})
        code, out = self.run_lib(gh)
        self.assertEqual(code, 0, out)
        self.assertIn("FEAT-001 T2: todo -> done (lib#40)", out)  # lib#11 closed by the PR of lib, not the backlog's
        self.assertIn("FEAT-001 T3: todo -> doing (product-client#42)", out)
        self.assertEqual([self.status("FEAT-001", t) for t in ("T1", "T2", "T3", "T4")],
                         ["blocked", "done", "doing", "blocked"])  # T1 and T4: the backlog's #11 (labelled blocked)

    def test_a_bare_close_in_the_backlog_never_closes_the_other_repositorys_issue(self):
        self.two_repository_rows()
        gh = self.lib_gh([issue(11, "Backlog eleven")], [issue(11, "Lib eleven")],
                         {(REPO, 41): pull(body="Closes #11")})
        _, out = self.run_lib(gh)
        self.assertEqual([self.status("FEAT-001", t) for t in ("T1", "T2")], ["done", "todo"])

    def test_each_repository_is_listed_once_and_a_single_repository_spec_lists_only_the_backlog(self):
        self.two_repository_rows()
        self.run_lib(self.lib_gh([issue(11, "Backlog eleven")], [issue(11, "Lib eleven")]))
        listings = [q for q in self.queries if "/issues?" in q and q.endswith("&page=1")]
        self.assertEqual(sorted(q.split("?")[0] for q in listings), [f"repos/{LIB}/issues", f"repos/{REPO}/issues"])
        self.queries.clear()
        self.item_rows(("T1", "todo", "#11"), ("T2", "todo", f"{REPO}#12"), ("T3", "todo", f"{OLD}#13"))
        self.run_lib(self.lib_gh([issue(11, "Backlog eleven")], []))
        self.assertEqual({q.split("?")[0] for q in self.queries if "/issues?" in q}, {f"repos/{REPO}/issues"})

    def test_a_repository_that_cannot_be_read_is_reported_and_its_rows_keep_their_status(self):
        self.item_rows(("T1", "todo", f"{LIB}#11"), ("T2", "todo", "#12"))
        gh = self.lib_gh([issue(15, "[FEAT-001 T1] First", labels=["blocked"]), issue(12, "Twelve", "closed")], [],
                         {(REPO, 41): pull(body="Closes #12")}, lib_issues=False)
        code, out = self.run_lib(gh)
        self.assertEqual(code, 0, out)
        self.assertIn(f"WARN {LIB}: issues not read (", out)
        self.assertEqual([self.status("FEAT-001", t) for t in ("T1", "T2")], ["todo", "done"])  # not the title's blocked

    def test_the_backlog_that_cannot_be_read_still_stops(self):
        self.item_rows(("T1", "todo", f"{LIB}#11"))
        gh = self.lib_gh([], [], lib_issues=True)
        failing = lambda query: subprocess.CompletedProcess(["gh"], 1, "", "HTTP 404") if ISSUES in query else gh(query)
        with self.assertRaises(trace.SyncError):
            self.run_lib(failing)

    def test_a_feat_issue_composes_with_a_cross_repository_row(self):
        """KIT-106: FEAT-001 keeps its row states and reads no repository; FEAT-002 beside it still syncs from LIB."""
        self.item_rows(("T1", "doing", f"{LIB}#11"), ("T2", "todo", "#11"))
        text = self.path1.read_text(encoding="utf-8")
        self.path1.write_text(text.replace("requirements: []", f'issue: "{REPO}#99"\nrequirements: []'),
                              encoding="utf-8")
        row = ROW11.format(tid="T1", task="only task", status="todo").replace("| 0 | — |", f"| 0 | {LIB}#11 |")
        self.path2.write_text(FEAT11.format(fid="FEAT-002", title="Second fixture", status="planned", rows=row),
                              encoding="utf-8")
        gh = self.lib_gh([issue(99, "[FEAT-001] One feature", "closed"), issue(11, "Backlog eleven", "closed")],
                         [issue(11, "Lib eleven", labels=["blocked"])], {(REPO, 41): pull(body="Closes #99")})
        code, out = self.run_lib(gh)
        self.assertEqual(code, 0, out)
        self.assertEqual(trace.load(self.spec).feats["FEAT-001"]["task_status"], {"T1": "doing", "T2": "todo"})
        self.assertEqual(self.status("FEAT-002", "T1"), "blocked")  # lib#11, not the backlog's closed #11

    def test_an_earlier_backlog_name_still_maps_to_the_backlog(self):
        self.item_rows(("T1", "todo", f"{OLD}#11"))
        gh = self.lib_gh([issue(11, "Backlog eleven", "closed")], [issue(11, "Lib eleven")],
                         {(REPO, 41): pull(body=f"Closes {OLD}#11")})
        self.run_lib(gh)
        self.assertEqual(self.status("FEAT-001", "T1"), "done")
        self.assertFalse([q for q in self.queries if LIB in q and "/issues?" in q])  # no row names LIB

    # KIT-112 follow-ups (#413): an unreadable repository, the WARN wording, the case of a repository name, `updated`.

    def test_an_unreadable_repository_freezes_its_rows_instead_of_guessing_from_the_title(self):
        """Before: the row took the backlog issue titled like it, so a `doing` row fell back to `todo`."""
        self.item_rows(("T1", "doing", f"{LIB}#11"), ("T2", "todo", "#12"), ("T3", "done", f"{LIB}#13"))
        gh = self.lib_gh([issue(15, "[FEAT-001 T1] First"), issue(12, "Twelve", "closed")], [],
                         {(REPO, 41): pull(body="Closes #12")}, lib_issues=False)
        code, out = self.run_lib(gh)
        self.assertEqual(code, 0, out)
        self.assertEqual([self.status("FEAT-001", t) for t in ("T1", "T2", "T3")], ["doing", "done", "done"])

    def test_the_warning_names_the_repository_the_issues_the_reason_the_consequence_and_the_fix(self):
        self.item_rows(("T1", "doing", f"{LIB}#11"), ("T2", "todo", f"{LIB}#13"), ("T3", "todo", "#12"))
        gh = self.lib_gh([issue(12, "Twelve")], [], lib_issues=False)
        _, out = self.run_lib(gh)
        [line] = [ln for ln in out.splitlines() if ln.startswith(f"WARN {LIB}:")]
        self.assertIn("issues not read (", line)
        self.assertIn("no canned route", line)  # the reason `gh` gave
        self.assertIn(f"FEAT-001 T1 ({LIB}#11)", line)
        self.assertIn(f"FEAT-001 T2 ({LIB}#13)", line)
        self.assertNotIn("T3", line)
        self.assertIn("2 rows keep their current status and are not synced", line)
        self.assertIn(f"read access to {LIB}", line)
        self.assertIn("Item cells", line)

    def test_the_warning_for_one_row_is_singular_and_a_long_list_is_cut(self):
        self.item_rows(("T1", "todo", f"{LIB}#11"))
        _, out = self.run_lib(self.lib_gh([], [], lib_issues=False))
        self.assertIn("1 row keeps its current status and is not synced: FEAT-001 T1 (", out)
        self.item_rows(*[(f"T{n}", "todo", f"{LIB}#{n}") for n in range(1, 9)])
        _, out = self.run_lib(self.lib_gh([], [], lib_issues=False))
        self.assertIn("8 rows keep their current status and are not synced", out)
        self.assertIn("and 3 more", out)
        self.assertNotIn("FEAT-001 T8", out)

    def test_an_unreadable_pr_repository_stops_the_run_naming_it_and_what_to_change(self):
        """Any row may be closed by a PR there, so a row could not be told from one with no PR: never a WARN."""
        self.item_rows(("T1", "doing", "#11"))
        gh = self.lib_gh([issue(11, "Eleven")], [], lib_issues=False)
        settings = trace.github_settings(self.spec)
        settings["pr_repos"].append(LIB)
        failing = lambda query: (subprocess.CompletedProcess(["gh"], 1, "", "HTTP 404")
                                 if f"repos/{LIB}/pulls" in query else gh(query))
        with self.assertRaises(trace.SyncError) as caught:
            trace.closing_prs(settings, failing)
        message = str(caught.exception)
        self.assertIn(f"{LIB}: pull requests not read", message)
        self.assertIn("HTTP 404", message)
        self.assertIn("sdd.github.pr_repos", message)
        self.assertIn(f"read access to {LIB}", message)
        with self.assertRaises(trace.SyncError):
            self.run_lib(failing)

    def test_item_issue_compares_repository_names_without_case(self):
        settings = trace.github_settings(self.spec)
        settings["pr_repos"].append(LIB)
        for cell, expected in (("ORG/Product#11", (REPO, 11)), (f"{OLD.upper()}#11", (REPO, 11)),
                               ("Org/Lib#11", (LIB, 11)),  # the configured spelling, not the cell's
                               ("Other/Repo#11", ("Other/Repo", 11))):  # unknown: as written
            with self.subTest(cell=cell):
                self.assertEqual(trace.item_issue(cell, settings), expected)

    def test_a_repository_written_in_another_case_is_listed_once_and_its_pr_closes_read(self):
        self.item_rows(("T1", "todo", "Org/LIB#11"), ("T2", "todo", "ORG/lib#12"), ("T3", "todo", "ORG/PRODUCT#13"))
        gh = self.lib_gh([issue(13, "Thirteen")], [issue(11, "Lib eleven", "closed"), issue(12, "Lib twelve")],
                         {(LIB, 40): pull(body="Closes ORG/Lib#11"),
                          (CLIENT, 42): pull("open", False, "Closes Org/LIB#12"),
                          (REPO, 41): pull(body="Closes Org/Product#13")})
        code, out = self.run_lib(gh)
        self.assertEqual(code, 0, out)
        self.assertEqual([self.status("FEAT-001", t) for t in ("T1", "T2", "T3")], ["done", "doing", "done"])
        listings = [q.split("?")[0] for q in self.queries if "/issues?" in q and q.endswith("&page=1")]
        self.assertEqual(sorted(listings), [f"repos/{LIB}/issues", f"repos/{REPO}/issues"])
        self.assertEqual(self.text(self.path1).count("Org/LIB#11"), 1)  # what the spec says is never rewritten

    def test_a_pr_repository_that_is_the_backlog_in_another_case_is_listed_once(self):
        gh = self.lib_gh([], [])
        settings = trace.github_settings(self.spec)
        settings["pr_repos"] = [REPO.upper(), CLIENT, CLIENT.title()]
        trace.closing_prs(settings, gh)
        pulls = [q.split("?")[0] for q in self.queries if "/pulls?" in q and q.endswith("&page=1")]
        self.assertEqual(sorted(pulls), [f"repos/{CLIENT}/pulls", f"repos/{REPO}/pulls"])

    def test_a_feat_pr_or_issue_in_another_case_is_inside_the_backlog_repositories(self):
        settings = trace.github_settings(self.spec)
        closing = {(REPO, 99): [{"ref": "product#7", "state": "closed", "merged": True}]}
        prs, why = trace.feat_prs({"issue": "ORG/Product#99"}, settings, closing, canned({}))
        self.assertEqual((why, [p["ref"] for p in prs]), (None, ["product#7"]))
        gh = canned({f"repos/{CLIENT}/pulls/5": {1: {"state": "closed", "merged_at": "2026-10-05T12:00:00Z"}}})
        prs, why = trace.feat_prs({"pr": "Org/Product-Client#5"}, settings, closing, gh)
        self.assertEqual(why, None)
        self.assertEqual([p["merged"] for p in prs], [True])

    def test_updated_is_set_to_today_in_every_feat_a_sync_rewrites_whatever_it_held(self):
        """#413: KIT-107..113 showed no `updated` diff in #411 because they were created that day; the rule is the
        same for a FEAT dated earlier, dated today or with no `updated` line, in sync-status and in status --write."""
        for held in ('updated: "2026-10-05"', f'updated: "{TODAY}"', None):
            with self.subTest(held=held):
                text = FEAT7.format(fid="FEAT-009", title="T", status="planned", rows="")
                text = text.replace('updated: "2026-10-05"\n', f"{held}\n" if held else "")
                synced = trace.rewrite_frontmatter(text, "in-progress", TODAY)
                path = self.root / "docs/spec/features/FEAT-009.md"
                path.write_text(text, encoding="utf-8")
                trace.set_status(path, "in-progress", TODAY)
                self.assertEqual(path.read_text(encoding="utf-8"), synced)
                self.assertIn(f'updated: "{TODAY}"', synced)
                self.assertEqual(synced.count("updated:"), 1)
        untouched = FEAT7.format(fid="FEAT-009", title="T", status="planned", rows="")
        self.assertEqual(trace.rewrite_frontmatter(untouched, None, TODAY).count(f'updated: "{TODAY}"'), 1)


class SettingsTest(unittest.TestCase):
    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = trace.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_tracker_none_refuses_sync_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "docs/spec"
            write(Path(tmp), "docs/spec/spec.md", SPEC_MD.replace("tracker: github", "tracker: none"))
            code, _, err = self.run_main("sync-status", str(spec))
        self.assertEqual(code, 2)
        self.assertIn("sdd.tracker is none", err)

    def fake_gh(self, root, stderr="HTTP 401: Bad credentials"):
        """A `gh` on PATH that fails every call, as `run_gh` meets it (#267)."""
        stub = root / "bin" / "gh"
        stub.parent.mkdir()
        stub.write_text(f"#!/bin/sh\necho '{stderr}' >&2\nexit 1\n", encoding="utf-8")
        stub.chmod(0o755)
        old = os.environ["PATH"]
        os.environ["PATH"] = f"{stub.parent}{os.pathsep}{old}"
        self.addCleanup(os.environ.__setitem__, "PATH", old)

    def test_a_failing_gh_exits_2_with_its_message_on_stderr(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "docs/spec/spec.md", SPEC_MD)
            self.fake_gh(root)
            code, out, err = self.run_main("sync-status", str(root / "docs/spec"))
        self.assertEqual(code, 2, out + err)
        self.assertIn("FAIL: sync-status: gh api", err)
        self.assertIn("HTTP 401: Bad credentials", err)

    def test_no_backlog_repository_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "docs/spec/spec.md", SPEC_MD.replace(f"repo: {REPO}, ", ""))
            code, _, err = self.run_main("sync-status", str(root / "docs/spec"))
        self.assertEqual(code, 2)
        self.assertIn("no backlog repository", err)

    def test_the_repository_defaults_to_the_origin_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "docs/spec/spec.md", SPEC_MD.replace(f"repo: {REPO}, ", ""))
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "remote", "add", "origin", "git@github.com:acme/widgets.git"],
                           check=True)
            self.assertEqual(trace.github_settings(root / "docs/spec")["repo"], "acme/widgets")
            subprocess.run(["git", "-C", str(root), "remote", "set-url", "origin",
                            "https://github.com/acme/gadgets.git"], check=True)
            self.assertEqual(trace.github_settings(root / "docs/spec")["repo"], "acme/gadgets")
            self.assertEqual(trace.github_settings(root / "docs/spec", "x/y")["repo"], "x/y")


if __name__ == "__main__":
    unittest.main()
