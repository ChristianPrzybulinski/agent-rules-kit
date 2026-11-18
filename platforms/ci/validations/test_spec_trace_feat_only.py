"""spec_trace.py under the FEAT-only flow (KIT-100): a FEAT with no REQ and no task rows, named with the profile's
`sdd.id_prefix.feature`, takes its status from its PR: `sync-status` reads the PR the FEAT's `pr` field names, else
the PR whose body closes its `issue`; an open PR makes it in-progress, a merged one delivered, each with a History
line that check_spec.py accepts. `gh` is mocked; the full flow ignores the fields."""
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
COVERS = ("platforms/ci/validations/spec_trace.py", "platforms/ci/validations/check_spec.py")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec_trace as trace  # noqa: E402

REPO = "org/tool"
TODAY = "2026-11-18"

SPEC_MD = """\
---
project: "tool"
version: "0.1.0"
updated: "2026-11-17"
---

# Tool
"""

FEAT = """\
---
id: {fid}
title: "Fixture feature {fid}"
status: {status}
{extra}created: "2026-11-17"
---

# {fid}

## History

- 2026-11-17 plan: created from the request.
"""

LEGACY = """\
---
id: KIT-001
title: "An old record kept as it is"
status: done
confirmed: "2026-10-01 (owner)"
issue: "#3"
pr: "#4"
---

# KIT-001
"""


VERSIONED = """\
---
id: KIT-104
title: "Fixture use case KIT-104"
status: planned
pr: "#12"
created: "2026-11-17"
---

# KIT-104

## Versions

### 1.0.0

Status: delivered
Scope: the first delivery.

#### Closure

- closed by its PR.

### 1.1.0

Status: planned
Scope: the second delivery.

#### Closure

## History

- 2026-11-17 pr: delivered (tool#11 merged)
"""


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def canned(routes):
    """Fake `gh api`: routes maps a URL substring to its payload (a list is one page of a paged listing)."""
    def gh(query):
        for sub, payload in routes.items():
            if sub in query:
                page = re.search(r"[?&]page=(\d+)", query)
                body = payload if not isinstance(payload, list) else (payload if not page or page.group(1) == "1"
                                                                      else [])
                return subprocess.CompletedProcess(["gh"], 0, json.dumps(body), "")
        return subprocess.CompletedProcess(["gh"], 1, "", f"no canned route for {query}")
    return gh


def pull(number, state="closed", merged=True, body=""):
    return {"number": number, "state": state, "merged_at": "2026-11-18T10:00:00Z" if merged else None, "body": body}


class FeatOnlySyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.spec = self.root / "docs" / "spec"
        write(self.root, "docs/spec/spec.md", SPEC_MD)
        self.profile("project:\n  kind: tooling\nsdd:\n  id_prefix: {feature: KIT}\n  github: {repo: org/tool}\n")

    def tearDown(self):
        self.tmp.cleanup()

    def profile(self, text):
        write(self.root, ".ai-kit.yaml", text)

    def feat(self, fid="KIT-101", status="planned", extra='pr: "#12"\n'):
        return write(self.root, f"docs/spec/features/{fid}.md", FEAT.format(fid=fid, status=status, extra=extra))

    def routes(self, pulls=(), single=None):
        routes = {f"repos/{REPO}/issues?state=all": [], f"repos/{REPO}/pulls?state=all": list(pulls)}
        for number, payload in (single or {}).items():
            routes[f"repos/{REPO}/pulls/{number}"] = payload
        return canned(routes)

    def sync(self, gh, write_files=True):
        spec = trace.load(self.spec)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = trace.sync_status(spec, trace.github_settings(self.spec), write_files, TODAY, gh)
        return code, out.getvalue()

    def frontmatter(self, path):
        return trace.split_frontmatter(path.read_text(encoding="utf-8"))[0]

    def check_spec(self):
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        return subprocess.run([sys.executable, "-B", str(HERE / "check_spec.py"), str(self.spec),
                               str(HERE.parent / "schemas")], capture_output=True, text=True, check=False, env=env)

    def test_the_id_prefix_loads_the_feats(self):
        self.feat()
        spec = trace.load(self.spec)
        self.assertEqual(list(spec.feats), ["KIT-101"])
        self.assertEqual(spec.feats["KIT-101"]["requirements"], [])

    def test_check_accepts_a_feat_with_no_req(self):
        self.feat()
        self.assertEqual(trace.check(trace.load(self.spec)), [])

    def test_a_merged_pr_delivers_the_feat(self):
        path = self.feat()
        code, output = self.sync(self.routes(single={12: pull(12)}))
        self.assertEqual(code, 0, output)
        self.assertIn("KIT-101: planned -> delivered (tool#12 merged)", output)
        self.assertEqual(self.frontmatter(path)["status"], "delivered")
        self.assertIn("- 2026-11-18 pr: delivered (tool#12 merged)", path.read_text(encoding="utf-8"))
        result = self.check_spec()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_an_open_pr_makes_it_in_progress(self):
        path = self.feat()
        self.sync(self.routes(single={12: pull(12, "open", False)}))
        self.assertEqual(self.frontmatter(path)["status"], "in-progress")
        self.assertIn("- 2026-11-18 pr: in-progress (tool#12 open)", path.read_text(encoding="utf-8"))

    def test_the_pr_that_closes_its_issue_counts_without_a_pr_field(self):
        path = self.feat(extra='issue: "#7"\n')
        self.sync(self.routes(pulls=[pull(30, body="Closes #7")]))
        self.assertEqual(self.frontmatter(path)["status"], "delivered")
        self.assertIn("pr: delivered (tool#30 merged)", path.read_text(encoding="utf-8"))

    def test_a_closed_unmerged_pr_only_warns(self):
        path = self.feat()
        _, output = self.sync(self.routes(single={12: pull(12, "closed", False)}))
        self.assertIn("WARN KIT-101: tool#12 closed without a merge", output)
        self.assertEqual(self.frontmatter(path)["status"], "planned")

    def test_a_dry_run_writes_nothing(self):
        path = self.feat()
        before = path.read_text(encoding="utf-8")
        _, output = self.sync(self.routes(single={12: pull(12)}), write_files=False)
        self.assertIn("KIT-101: planned -> delivered", output)
        self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_delivered_cancelled_and_legacy_records_are_never_rewritten(self):
        delivered = self.feat("KIT-102", "delivered", 'pr: "#12"\n')
        cancelled = self.feat("KIT-103", "cancelled", 'pr: "#12"\n')
        legacy = write(self.root, "docs/spec/features/KIT-001-old.md", LEGACY)
        before = [p.read_text(encoding="utf-8") for p in (delivered, cancelled, legacy)]
        self.sync(self.routes(single={12: pull(12, "open", False), 4: pull(4, "open", False)}))
        self.assertEqual([p.read_text(encoding="utf-8") for p in (delivered, cancelled, legacy)], before)

    def test_a_feat_without_pr_or_issue_stays(self):
        path = self.feat(extra="")
        _, output = self.sync(self.routes())
        self.assertIn("KIT-101: planned (no PR)", output)
        self.assertEqual(self.frontmatter(path)["status"], "planned")

    def test_a_pr_outside_the_backlog_repositories_warns(self):
        path = self.feat(extra='pr: "elsewhere/other#12"\n')
        _, output = self.sync(self.routes())
        self.assertIn("WARN KIT-101: other#12 is outside the backlog repositories; status not synced", output)
        self.assertEqual(self.frontmatter(path)["status"], "planned")

    def test_a_pr_with_non_ascii_digits_never_reaches_gh(self):
        """`\\d` matches Arabic-Indic digits; the field takes ASCII digits only, as check_spec.py's ITEM_REF does."""
        path = self.feat(extra='pr: "#\u0663"\n')
        other = self.feat("KIT-105", extra='pr: "#12"\n')
        code, output = self.sync(self.routes(single={12: pull(12)}))
        self.assertEqual(code, 0, output)
        self.assertIn("WARN KIT-101: pr '#\u0663' is not #N or OWNER/NAME#N; status not synced", output)
        self.assertEqual(self.frontmatter(path)["status"], "planned")
        self.assertEqual(self.frontmatter(other)["status"], "delivered")

    def test_a_versioned_lite_feat_delivers_its_open_block(self):
        """KIT-096 coexistence: a lite FEAT with `## Versions` follows its PR in its last block, which check_spec.py
        then accepts with no REQ."""
        path = write(self.root, "docs/spec/features/KIT-104.md", VERSIONED)
        _, output = self.sync(self.routes(single={12: pull(12)}))
        self.assertIn("KIT-104: planned -> delivered (tool#12 merged)", output)
        text = path.read_text(encoding="utf-8")
        self.assertEqual(self.frontmatter(path)["status"], "delivered")
        self.assertEqual(text.count("Status: delivered"), 2, text)
        result = self.check_spec()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_full_flow_ignores_the_pr_field(self):
        self.profile("sdd:\n  github: {repo: org/tool}\n")
        path = write(self.root, "docs/spec/features/FEAT-001.md",
                     FEAT.format(fid="FEAT-001", status="planned", extra='requirements: []\npr: "#12"\n'))
        before = path.read_text(encoding="utf-8")
        _, output = self.sync(self.routes(single={12: pull(12)}))
        self.assertNotIn("delivered", output)
        self.assertEqual(path.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
