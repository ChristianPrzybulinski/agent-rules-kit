"""check_spec.py and enablers (KIT-095): ENB-nnn frontmatter, the `enablers` links of FEAT, decision and debt records,
FEAT `kind: feature | enabler`, `dependsOn` and the contract ids of `providesApis` and `consumesApis`, with and
without jsonschema. A spec without enablers/ is checked as before (the other check_spec tests)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/check_spec.py", "platforms/ci/schemas/**")

VALIDATIONS = Path(__file__).resolve().parent
CHECK_SPEC = VALIDATIONS / "check_spec.py"
SCHEMAS = VALIDATIONS.parent / "schemas"

ENABLER = """---
id: {eid}
title: "Fixture context {eid}"
status: approved
owner: battle-team
system: game
domain: combat
providesApis: [{provides}]
consumesApis: [{consumes}]
dependsOn: [{depends}]
created: "2026-11-17"
updated: "2026-11-17"
---

# {eid}
"""

FEAT = """---
id: FEAT-001
title: "Fixture feature FEAT-001"
status: proposed
requirements: [{reqs}]
{extra}created: "2026-11-17"
---

# FEAT-001
"""

REQ = """---
id: {rid}
title: "Fixture requirement {rid}"
type: {type}
priority: must
features: [FEAT-001]
created: "2026-11-17"
---

# {rid}
"""

DECISION = """---
id: DEC-001
title: "Fixture decision"
status: approved
date: "2026-11-17"
enablers: [{enablers}]
---

# DEC-001
"""

DEBT = """---
id: DEBT-001
title: "Fixture debt"
status: open
severity: low
trigger: "when the battle context grows"
enablers: [{enablers}]
created: "2026-11-17"
---

# DEBT-001
"""


class EnablerCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spec = Path(self.tmp.name)
        for sub in ("enablers", "features", "requirements/functional", "requirements/non-functional",
                    "decisions", "debts"):
            (self.spec / sub).mkdir(parents=True)
        self.enabler("ENB-001", provides="battle-wire, battle-table")
        self.enabler("ENB-002", consumes="battle-wire", depends="ENB-001")
        self.req("REQ-F-001")
        self.feat(reqs="REQ-F-001", extra="enablers: [ENB-001]\n")

    def tearDown(self):
        self.tmp.cleanup()

    def enabler(self, eid, provides="", consumes="", depends="", name=None, old=None, new=None):
        text = ENABLER.format(eid=eid, provides=provides, consumes=consumes, depends=depends)
        path = self.spec / "enablers" / f"{name or eid + '-fixture'}.md"
        path.write_text(text if old is None else text.replace(old, new))

    def feat(self, reqs="", extra=""):
        (self.spec / "features" / "FEAT-001.md").write_text(FEAT.format(reqs=reqs, extra=extra))

    def req(self, rid, type_="functional"):
        folder = "functional" if type_ == "functional" else "non-functional"
        text = REQ.format(rid=rid, type=type_)
        if type_ != "functional":
            text = text.replace("priority: must\n", 'priority: must\ncategory: performance\nmetric: "p95 ms"\n'
                                'target: "100"\nmeasurement: "load test"\n')
        (self.spec / "requirements" / folder / f"{rid}.md").write_text(text)

    def run_both(self):
        """The full check, then the structural one: python -S hides pyyaml and jsonschema."""
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        return [subprocess.run([sys.executable, *flags, str(CHECK_SPEC), str(self.spec), str(SCHEMAS)],
                               capture_output=True, text=True, check=False, env=env)
                for flags in ([], ["-S"])]

    def assert_passes(self):
        for result in self.run_both():
            self.assertEqual(result.returncode, 0, result.stderr)

    def assert_fails(self, *messages, full_only=False):
        for result in self.run_both()[:1] if full_only else self.run_both():
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            for message in messages:
                self.assertIn(message, result.stderr)


class EnablerFrontmatterTest(EnablerCase):
    def test_valid_enablers_pass(self):
        for result in self.run_both():
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("spec: OK (4 artifacts)", result.stdout)

    def test_owner_is_required(self):
        self.enabler("ENB-001", provides="battle-wire", old="owner: battle-team\n", new="")
        self.assert_fails("ENB-001-fixture.md", "owner")

    def test_status_is_an_enum(self):
        self.enabler("ENB-001", provides="battle-wire", old="status: approved", new="status: done")
        self.assert_fails("ENB-001-fixture.md", "done")

    def test_id_pattern_and_file_name(self):
        self.enabler("ENB-003", name="ENB-004-other")
        self.assert_fails("id=ENB-003 != file name prefix")

    def test_unknown_field_fails_with_the_schema(self):
        self.enabler("ENB-001", provides="battle-wire", old="domain: combat", new="domain: combat\nlifecycle: prod")
        self.assert_fails("ENB-001-fixture.md", full_only=True)

    def test_contract_id_pattern_fails_with_the_schema(self):
        self.enabler("ENB-001", provides="Battle Wire")
        self.assert_fails("ENB-001-fixture.md", full_only=True)

    def test_enb_is_a_reserved_decision_prefix(self):
        index = self.spec / "spec.md"
        index.write_text('---\nproject: fixture\nversion: "0.1"\nupdated: "2026-11-17"\n'
                         "decision_kinds: {tech: ENB}\n---\n\n# Spec\n")
        self.assert_fails("decision prefix 'ENB'")


class EnablerLinkTest(EnablerCase):
    def test_feat_lists_an_unknown_enabler(self):
        self.feat(reqs="REQ-F-001", extra="enablers: [ENB-009]\n")
        self.assert_fails("FEAT-001.md: enablers lists ENB-009, which is not an existing enabler [enabler-link]")

    def test_decision_and_debt_list_enablers(self):
        (self.spec / "decisions" / "DEC-001-fixture.md").write_text(DECISION.format(enablers="ENB-001"))
        (self.spec / "debts" / "DEBT-001-fixture.md").write_text(DEBT.format(enablers="ENB-002"))
        self.assert_passes()
        (self.spec / "decisions" / "DEC-001-fixture.md").write_text(DECISION.format(enablers="ENB-007"))
        (self.spec / "debts" / "DEBT-001-fixture.md").write_text(DEBT.format(enablers="ENB-008"))
        self.assert_fails("DEC-001-fixture.md: enablers lists ENB-007", "DEBT-001-fixture.md: enablers lists ENB-008")

    def test_depends_on_an_unknown_enabler_or_itself(self):
        self.enabler("ENB-002", consumes="battle-wire", depends="ENB-005")
        self.assert_fails("ENB-002-fixture.md: dependsOn lists ENB-005, which is not an existing enabler")
        self.enabler("ENB-002", consumes="battle-wire", depends="ENB-002")
        self.assert_fails("ENB-002-fixture.md: dependsOn lists the enabler itself")


class EnablerContractTest(EnablerCase):
    def test_consumed_contract_no_enabler_provides(self):
        self.enabler("ENB-002", consumes="shop-wire")
        self.assert_fails("ENB-002-fixture.md: consumesApis lists shop-wire, which no other enabler provides "
                          "[enabler-contract]")

    def test_contract_provided_by_two_enablers(self):
        self.enabler("ENB-002", provides="battle-wire")
        self.assert_fails("providesApis lists battle-wire, which ENB-001 provides too [enabler-contract]")

    def test_enabler_consumes_its_own_contract(self):
        self.enabler("ENB-001", provides="battle-wire", consumes="battle-wire")
        self.assert_fails("ENB-001-fixture.md: consumesApis lists battle-wire, which no other enabler provides")


class FeatureKindTest(EnablerCase):
    def test_kind_is_an_enum(self):
        self.feat(reqs="REQ-F-001", extra="kind: epic\nenablers: [ENB-001]\n")
        self.assert_fails("FEAT-001.md", "epic")

    def test_feature_kind_passes(self):
        self.feat(reqs="REQ-F-001", extra="kind: feature\nenablers: [ENB-001]\n")
        self.assert_passes()

    def test_enabler_feat_names_an_enabler(self):
        self.req("REQ-NF-001", "non-functional")
        (self.spec / "requirements" / "functional" / "REQ-F-001.md").unlink()
        self.feat(reqs="REQ-NF-001", extra="kind: enabler\n")
        self.assert_fails("FEAT-001.md: kind enabler needs at least one ENB in enablers [enabler-kind]")

    def test_enabler_feat_implements_no_functional_req(self):
        self.feat(reqs="REQ-F-001", extra="kind: enabler\nenablers: [ENB-001]\n")
        self.assert_fails("FEAT-001.md: kind enabler implements no REQ-F, but requirements lists REQ-F-001 "
                          "[enabler-kind]")

    def test_enabler_feat_with_a_quality_passes(self):
        self.req("REQ-NF-001", "non-functional")
        (self.spec / "requirements" / "functional" / "REQ-F-001.md").unlink()
        self.feat(reqs="REQ-NF-001", extra="kind: enabler\nenablers: [ENB-001]\n")
        self.assert_passes()



class SpecFileErrorTest(EnablerCase):
    """#356 item 1: a spec file that is not UTF-8 is one `FAIL:` line that names it, never a traceback."""

    def test_non_utf8_enabler_fails_cleanly(self):
        path = self.spec / "enablers" / "ENB-001-fixture.md"
        path.write_bytes(path.read_bytes() + b"\xff\xfe\n")
        for result in self.run_both():
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(f"FAIL: {path}: not UTF-8", result.stderr)
            self.assertNotIn("Traceback", result.stderr)


class NamedFilesTest(EnablerCase):
    """#356 item 3: check_spec.py reads processes/PROC-*.md and enablers/ENB-*.md, the files spec_trace.py reads, so a
    folder README is no record; another Markdown file there fails, since neither tool would read it."""

    def test_folder_readme_is_no_record(self):
        (self.spec / "processes").mkdir()
        for sub in ("enablers", "processes"):
            (self.spec / sub / "README.md").write_text("# Index\n")
        self.assert_passes()

    def test_misnamed_file_fails(self):
        self.enabler("ENB-003", name="enb-003-other")
        self.assert_fails("enb-003-other.md: not read: enablers/ holds ENB-*.md files only")


if __name__ == "__main__":
    unittest.main()
