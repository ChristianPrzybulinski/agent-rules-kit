"""check_spec.py under the FEAT-only flow (KIT-100): with the profile's `sdd.flow: feat-only` (the `tooling` preset) a
FEAT carries no REQ, may name its `issue` and `pr`, takes the id prefix `sdd.id_prefix.feature`, and is delivered by
its merged PR's History line; with the full flow every one of those stays refused."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/check_spec.py", "platforms/ci/schemas/**", "platforms/tools/profile.py",
          "plugins/guardrails/templates/spec-feature-lite.md")

VALIDATIONS = Path(__file__).resolve().parent
CHECK_SPEC = VALIDATIONS / "check_spec.py"
SCHEMAS = VALIDATIONS.parent / "schemas"
LITE = VALIDATIONS.parents[2] / "plugins" / "guardrails" / "templates" / "spec-feature-lite.md"

INDEX = """---
project: "fixture"
version: "0.1.0"
updated: "2026-11-17"
---

# Fixture
"""

LITE_FEAT = """---
id: {fid}
title: "Fixture feature {fid}"
status: {status}
{extra}created: "2026-11-17"
---

# {fid}

## Acceptance criteria

| ID | Given | When | Then | Proof |
|---|---|---|---|---|
| CA-1 | a FEAT with no REQ | check_spec runs | it passes | `check.sh --spec docs/spec` |

## History

- 2026-11-17 plan: created from the request.
{history}
"""

PR_DELIVERED = "- 2026-11-18 pr: delivered (fixture#12 merged)"
TOOLING = "project:\n  kind: tooling\n"


class FeatOnlyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.spec = self.root / "docs" / "spec"
        (self.spec / "features").mkdir(parents=True)
        (self.spec / "spec.md").write_text(INDEX)

    def tearDown(self):
        self.tmp.cleanup()

    def profile(self, text):
        (self.root / ".ai-kit.yaml").write_text(text)

    def feat(self, fid="FEAT-001", status="planned", extra="", history=""):
        (self.spec / "features" / f"{fid}.md").write_text(
            LITE_FEAT.format(fid=fid, status=status, extra=extra, history=history))

    def run_both(self, full_only=False):
        """The full check, then the structural one: python -S hides pyyaml and jsonschema."""
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        return [subprocess.run([sys.executable, "-B", *flags, str(CHECK_SPEC), str(self.spec), str(SCHEMAS)],
                               capture_output=True, text=True, check=False, env=env, cwd=self.root)
                for flags in ([[]] if full_only else [[], ["-S"]])]

    def assert_passes(self, full_only=False):
        for result in self.run_both(full_only):
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("FAIL", result.stderr)

    def assert_fails(self, *messages, full_only=False):
        for result in self.run_both(full_only):
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            for message in messages:
                self.assertIn(message, result.stderr)

    def test_a_feat_without_requirements_passes_under_feat_only(self):
        self.profile(TOOLING)
        self.feat()
        self.assert_passes()

    def test_the_flow_key_alone_turns_it_on(self):
        """Skills and tools read sdd.flow, never project.kind: a business project with feat-only gets it too."""
        self.profile("sdd:\n  flow: feat-only\n")
        self.feat()
        self.assert_passes()

    def test_a_feat_without_requirements_still_fails_under_the_full_flow(self):
        for profile in (None, "project:\n  kind: business\n", "project:\n  kind: tooling\nsdd:\n  flow: full\n"):
            with self.subTest(profile=profile):
                if profile is None:
                    (self.root / ".ai-kit.yaml").unlink(missing_ok=True)
                else:
                    self.profile(profile)
                self.feat()
                self.assert_fails("requirements", "[schema]")

    def test_issue_and_pr_are_fields_of_a_feat_only_feat(self):
        self.profile(TOOLING)
        self.feat(extra='issue: "#7"\npr: "org/fixture#12"\n')
        self.assert_passes()
        self.feat(extra='issue: ""\npr: null\n')
        self.assert_passes()

    def test_a_malformed_pr_fails_under_feat_only(self):
        self.profile(TOOLING)
        self.feat(extra='pr: "12"\n')
        self.assert_fails("'12' does not match", full_only=True)

    def test_pr_stays_unknown_to_the_full_flow(self):
        self.feat(extra='requirements: []\npr: "#12"\n')
        self.assert_fails("Additional properties are not allowed ('pr' was unexpected)", full_only=True)

    def test_the_id_prefix_names_the_feat_ids(self):
        self.profile(TOOLING + "sdd:\n  id_prefix: {feature: KIT}\n")
        self.feat("KIT-101")
        self.assert_passes()
        self.feat("FEAT-001")
        self.assert_fails("FEAT-001", "[schema]")

    def test_a_merged_pr_line_delivers_a_feat_only_feat(self):
        self.profile(TOOLING)
        self.feat(status="delivered", extra='pr: "#12"\n', history=PR_DELIVERED)
        self.assert_passes()

    def test_a_delivered_feat_only_feat_without_the_line_fails(self):
        self.profile(TOOLING)
        self.feat(status="delivered", extra='pr: "#12"\n')
        self.assert_fails("status delivered needs the History line", "[feature-closure]")

    def test_the_pr_line_does_not_deliver_under_the_full_flow(self):
        self.feat(status="delivered", extra="requirements: []\n", history=PR_DELIVERED)
        self.assert_fails("status delivered needs the History line", "[feature-closure]")

    def test_the_lite_template_validates_under_feat_only(self):
        self.profile(TOOLING)
        text = LITE.read_text(encoding="utf-8").replace("YYYY-MM-DD", "2026-11-17")
        self.assertNotIn("\nrequirements:", text.split("\n---\n", 1)[0])
        (self.spec / "features" / "FEAT-000.md").write_text(text)
        self.assert_passes()

    def test_an_invalid_profile_leaves_the_spec_check_as_it_was(self):
        """A refused profile key is profile.py's finding, never a spec failure: the flow falls back to full."""
        self.profile("sdd:\n  flow: lite\n")
        self.feat(extra="requirements: []\n")
        self.assert_passes()


if __name__ == "__main__":
    unittest.main()
