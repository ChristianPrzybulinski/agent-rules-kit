"""spec_trace sync-status tests (KIT-073): task and FEAT status derived from canned GitHub data, `gh` mocked.

Ported from a consumer project's suite with neutral repositories: the backlog `org/product` (once named
`org/product-docs`) and two code repositories whose PRs close backlog issues. Row words follow
sdd-tasks/references/task-issue.md § States; the FEAT status stops at in-progress (KIT-069).
"""
import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec_trace as trace  # noqa: E402

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
        with self.assertRaises(SystemExit) as stop:
            self.run_sync(gh)
        self.assertIn("HTTP 401", str(stop.exception))


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
