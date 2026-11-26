"""spec_trace.py and enablers (KIT-095): ENB-nnn tables (frontmatter ids equal the contract tables, kinds, REQ cells),
the Enablers and Contracts views of the matrix, and the `enablers` command's C18 (a REQ or process step no ENB
satisfies) and C19 (a contract the catalog lacks, a contract with no consumer, a schema or migration file no row
covers). A spec without enablers/ is unaffected: the command is off and the matrix renders as before."""
import contextlib
import io
import shutil
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
from test_profile import write_spec  # noqa: E402  (a fixture's sdd: block goes to .ai-kit.yaml, KIT-087 P4)
import test_spec_trace as base  # noqa: E402  (the journey fixture of main)
import test_spec_trace_process as process_tests  # noqa: E402  (main's matrix for that fixture)

SPEC_INDEX = """\
---
project: fixture
version: "0.1"
updated: "2026-11-17"
sdd:
  row_checks:
    protocol:
      schemas: game/protocol/schemas
---

# Spec
"""

FEAT = """\
---
id: {fid}
title: "Fixture feature {fid}"
status: planned
requirements: [{reqs}]
enablers: [{enablers}]
created: "2026-11-17"
---

# {fid}

## Plan

### Contract

{contract}

### Tests

- none.

## Tasks

| ID | Task | Files | Status |
|---|---|---|---|
| T1 | first task | `a/**` | todo |
"""

REQ = """\
---
id: {rid}
title: "Fixture rule {rid}"
type: {type}
priority: must
features: [{feats}]
created: "2026-11-17"
---

# {rid}
"""

ENB_1 = """\
---
id: ENB-001
title: "Battle"
status: approved
owner: battle-team
domain: combat
providesApis: [battle-wire, battle-table]
consumesApis: []
dependsOn: []
---

# ENB-001 — Battle

## Context

- Bounded context: turns, damage and the end of a battle.

## Aggregates

| Aggregate | Invariant | Rules |
|---|---|---|
| Battle | one move per side per turn | REQ-F-001 |

## Events

| Event | Direction | Contract |
|---|---|---|
| battle ended | publishes | battle-wire |

## Provided contracts

| Contract | Kind | Accessed at | Schema or file | Version | Consumers |
|---|---|---|---|---|---|
| battle-wire | message | websocket /game | `game/protocol/schemas/battle_*.json` | 3 | ENB-002 |
| battle-table | table | battle schema | `server/db/migration/V1__battle.sql` | V1 | public |

## Required contracts

| Contract | Kind | From | Used for |
|---|---|---|---|

## Qualities

| Quality | Target | Rules |
|---|---|---|
| turn latency | p95 under 100 ms | REQ-NF-001 |

## Code

- `server/src/battle/**`
"""

ENB_2 = """\
---
id: ENB-002
title: "Shop"
status: proposed
owner: shop-team
providesApis: [shop-wire]
consumesApis: [battle-wire]
dependsOn: [ENB-001]
---

# ENB-002 — Shop

## Aggregates

| Aggregate | Invariant | Rules |
|---|---|---|
| Cart | never below zero coins | REQ-F-002 |

## Provided contracts

| Contract | Kind | Accessed at | Schema or file | Version | Consumers |
|---|---|---|---|---|---|
| shop-wire | message | websocket /game | `game/protocol/schemas/shop_*.json` | 1 | client |

## Required contracts

| Contract | Kind | From | Used for |
|---|---|---|---|
| battle-wire | message | ENB-001 | rewards after a battle |
"""

DECISION = """\
---
id: DEC-001
title: "Battle runs on the server"
status: approved
date: "2026-11-17"
enablers: [ENB-001]
---

# DEC-001
"""

PROCESS = """\
---
id: PROC-001
title: "Fixture battle turn"
status: proposed
owner: product
kind: product
---

# PROC-001

## Steps

| Step | Action → result | Rules | Implemented by | Proven by |
|---|---|---|---|---|
| S1 | picks a move → move is locked | REQ-F-001 | FEAT-001 T1 | FEAT-001 T1 |
| S2 | pays the fee → coins drop | REQ-F-003 | FEAT-001 T1 | FEAT-001 T1 |
"""


def write(root, rel, text):
    if str(rel).endswith("spec/spec.md"):  # its sdd: block goes to .ai-kit.yaml (KIT-087 P4)
        return write_spec(root, textwrap.dedent(text), rel)
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = trace.main(argv)
    return code, out.getvalue(), err.getvalue()


class EnablerCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "game-docs"
        self.spec = self.root / "docs/spec"
        write(self.root, "docs/spec/spec.md", SPEC_INDEX)
        self.feat("FEAT-001", "REQ-F-001, REQ-NF-001", "ENB-001", "- `ENB-001:battle-wire` gains `battle_ended`.")
        self.feat("FEAT-002", "REQ-F-002", "ENB-002", "- `ENB-002:shop-wire`: new.")
        self.req("REQ-F-001", "FEAT-001")
        self.req("REQ-NF-001", "FEAT-001", "non-functional")
        self.req("REQ-F-002", "FEAT-002")
        self.enabler(ENB_1)
        write(self.root, "docs/spec/enablers/ENB-002-shop.md", ENB_2)
        write(self.root, "docs/spec/decisions/DEC-001-server-battle.md", DECISION)
        for name in ("battle_start.json", "battle_ended.json", "shop_open.json"):
            write(self.root, f"game/protocol/schemas/{name}", "{}\n")
        write(self.root, "server/db/migration/V1__battle.sql", "-- fixture\n")

    def tearDown(self):
        self.tmp.cleanup()

    def feat(self, fid, reqs, enablers, contract):
        write(self.root, f"docs/spec/features/{fid}.md",
              FEAT.format(fid=fid, reqs=reqs, enablers=enablers, contract=contract))

    def req(self, rid, feats, type_="functional"):
        folder = "functional" if type_ == "functional" else "non-functional"
        write(self.root, f"docs/spec/requirements/{folder}/{rid}.md", REQ.format(rid=rid, feats=feats, type=type_))

    def enabler(self, text=ENB_1, old=None, new=None):
        write(self.root, "docs/spec/enablers/ENB-001-battle.md", text if old is None else text.replace(old, new))

    def check(self):
        run(["generate", str(self.spec)])
        return trace.check(trace.load(self.spec))

    def enablers(self, *args):
        return run(["enablers", str(self.spec), "--catalog", "server/db/migration/*.sql", *args])

    def assert_error(self, errs, *fragments):
        for fragment in fragments:
            self.assertTrue(any(fragment in e for e in errs), f"no error containing {fragment!r} in {errs}")


class EnablerTableTest(EnablerCase):
    def test_valid_enablers_pass(self):
        self.assertEqual(self.check(), [])
        spec = trace.load(self.spec)
        self.assertEqual(sorted(spec.enablers), ["ENB-001", "ENB-002"])
        self.assertEqual(sorted(spec.enablers["ENB-001"]["provides"]), ["battle-table", "battle-wire"])

    def test_provides_apis_equals_the_provided_table(self):
        self.enabler(old="providesApis: [battle-wire, battle-table]", new="providesApis: [battle-wire, battle-log]")
        self.assert_error(self.check(),
                          "ENB-001: providesApis lists battle-log, which no Provided contracts row holds",
                          "ENB-001: Provided contracts row battle-table is missing from providesApis")

    def test_consumes_apis_equals_the_required_table(self):
        write(self.root, "docs/spec/enablers/ENB-002-shop.md",
              ENB_2.replace("consumesApis: [battle-wire]", "consumesApis: []"))
        self.assert_error(self.check(), "ENB-002: Required contracts row battle-wire is missing from consumesApis")

    def test_kind_is_an_enum(self):
        self.enabler(old="| battle-table | table |", new="| battle-table | database |")
        self.assert_error(self.check(), "ENB-001: battle-table kind 'database' is not one of api, message, event")

    def test_required_contract_comes_from_its_provider(self):
        write(self.root, "docs/spec/enablers/ENB-002-shop.md", ENB_2.replace("| ENB-001 | rewards", "| ENB-003 | rewards"))
        self.assert_error(self.check(), "ENB-002: Required contract battle-wire is From ENB-003, but ENB-001 provides it")

    def test_rules_cells_cite_existing_reqs_of_the_right_type(self):
        self.enabler(old="| one move per side per turn | REQ-F-001 |", new="| one move per side per turn | REQ-F-009 |")
        self.assert_error(self.check(), "ENB-001: Aggregates cites REQ-F-009, which does not exist")
        self.enabler(old="| p95 under 100 ms | REQ-NF-001 |", new="| p95 under 100 ms | REQ-F-001 |")
        self.assert_error(self.check(), "ENB-001: Qualities cites REQ-F-001; it holds REQ-NF ids only")
        self.enabler(old="| one move per side per turn | REQ-F-001 |", new="| one move per side per turn | at most 1 |")
        self.assert_error(self.check(), "ENB-001: Aggregates Rules holds more than REQ ids")

    def test_event_contract_is_its_own(self):
        self.enabler(old="| publishes | battle-wire |", new="| publishes | shop-wire |")
        self.assert_error(self.check(), "ENB-001: event battle ended publishes shop-wire, which is not a Provided contract")

    def test_duplicate_contract_row(self):
        row = "| battle-table | table | battle schema | `server/db/migration/V1__battle.sql` | V1 | public |"
        self.enabler(old=row, new=row + "\n" + row)
        self.assert_error(self.check(), "ENB-001: Provided contracts lists battle-table twice")


class EnablerMatrixTest(EnablerCase):
    def test_matrix_lists_enablers_and_contracts(self):
        self.check()
        matrix = (self.spec / "traceability.md").read_text(encoding="utf-8")
        self.assertIn("## Enablers", matrix)
        self.assertIn("| [ENB-001](enablers/ENB-001-battle.md) | Battle | battle-team | combat | battle-table, "
                      "battle-wire | — | REQ-F-001, REQ-NF-001 | FEAT-001 (planned) | DEC-001 | — |", matrix)
        self.assertIn("## Contracts", matrix)
        self.assertIn("| battle-wire | message | ENB-001 | ENB-002 | websocket /game | "
                      "`game/protocol/schemas/battle_*.json` | 3 |", matrix)

    def test_enablers_alone_require_the_matrix(self):
        self.assertEqual(self.check(), [])
        (self.spec / "traceability.md").unlink()
        self.assert_error(trace.check(trace.load(self.spec)), "traceability.md is stale or missing")

    def test_a_spec_without_enablers_renders_the_matrix_of_main(self):
        root = Path(self.tmp.name) / "plain"
        base.fixture(root)
        self.assertEqual(trace.render_matrix(trace.load(root / "docs/spec")), process_tests.MAIN_MATRIX)


class EnablerCommandTest(EnablerCase):
    def test_clean_spec_passes(self):
        code, out, err = self.enablers()
        self.assertEqual((code, err), (0, ""), out)
        self.assertIn("enablers: OK (2 enablers, 3 contracts)", out)

    def test_off_without_enablers_folder(self):
        shutil.rmtree(self.spec / "enablers")
        code, out, _ = self.enablers()
        self.assertEqual(code, 0)
        self.assertIn("enablers: off", out)

    def test_c18_req_no_enabler_satisfies(self):
        write(self.root, "docs/spec/enablers/ENB-002-shop.md", ENB_2.replace("| REQ-F-002 |", "| REQ-F-001 |"))
        code, out, _ = self.enablers()
        self.assertEqual(code, 1)
        self.assertIn("C18 high: REQ-F-002 (FEAT-002) has no ENB that satisfies it in Aggregates or Qualities", out)
        code, out, _ = self.enablers("--feat", "FEAT-001")
        self.assertEqual(code, 0, out)

    def test_c18_skips_a_retired_req_and_reports_its_unsatisfied_keeper(self):
        """#450: a retired REQ stays listed beside its keeper; only the keeper still needs an ENB."""
        self.req("REQ-F-003", "FEAT-001")
        retired = self.spec / "requirements/functional/REQ-F-003.md"
        retired.write_text(retired.read_text(encoding="utf-8").replace("---\n", "---\nstatus: retired\n", 1),
                           encoding="utf-8")
        self.feat("FEAT-001", "REQ-F-001, REQ-NF-001, REQ-F-003", "ENB-001", "- `ENB-001:battle-wire`.")
        code, out, _ = self.enablers()
        self.assertEqual(code, 0, out)
        self.assertNotIn("C18", out)
        self.enabler(old="| one move per side per turn | REQ-F-001 |", new="| one move per side per turn | REQ-F-003 |")
        code, out, _ = self.enablers()
        self.assertEqual(code, 1, out)
        self.assertIn("C18 high: REQ-F-001 (FEAT-001) has no ENB that satisfies it in Aggregates or Qualities", out)
        self.assertNotIn("C18 high: REQ-F-003", out)

    def test_c18_process_step_no_enabler_satisfies(self):
        write(self.root, "docs/spec/processes/PROC-001-turn.md", PROCESS)
        self.req("REQ-F-003", "FEAT-001")
        self.feat("FEAT-001", "REQ-F-001, REQ-NF-001, REQ-F-003", "ENB-001", "- `ENB-001:battle-wire`.")
        code, out, _ = self.enablers()
        self.assertEqual(code, 1)
        self.assertIn("C18 high: PROC-001 S2 cites REQ-F-003, which no ENB satisfies", out)
        self.assertNotIn("PROC-001 S1", out)

    def test_c19_plan_contract_missing_from_the_catalog(self):
        self.feat("FEAT-001", "REQ-F-001, REQ-NF-001", "ENB-001", "- `ENB-001:battle-log` is new.")
        code, out, _ = self.enablers()
        self.assertEqual(code, 1)
        self.assertIn("C19 high: FEAT-001 Plan § Contract cites ENB-001:battle-log, which ENB-001 Provided contracts "
                      "lacks", out)

    def test_c19_plan_contract_of_an_enabler_the_feat_does_not_list(self):
        self.feat("FEAT-001", "REQ-F-001, REQ-NF-001", "ENB-001", "- `ENB-002:shop-wire` gains a field.")
        code, out, _ = self.enablers()
        self.assertEqual(code, 1)
        self.assertIn("C19 high: FEAT-001 Plan § Contract cites ENB-002:shop-wire, but FEAT-001 enablers does not "
                      "list ENB-002", out)

    def test_c19_contract_with_no_consumer(self):
        write(self.root, "docs/spec/enablers/ENB-002-shop.md", ENB_2.replace("| 1 | client |", "| 1 | — |"))
        code, out, _ = self.enablers()
        self.assertEqual(code, 1)
        self.assertIn("C19 medium: ENB-002 shop-wire has no consumer and no public mark", out)

    def test_c19_schema_and_migration_files_no_row_covers(self):
        write(self.root, "game/protocol/schemas/trade_offer.json", "{}\n")
        write(self.root, "server/db/migration/V2__trade.sql", "-- fixture\n")
        code, out, _ = self.enablers()
        self.assertEqual(code, 1)
        self.assertIn("C19 high: game/protocol/schemas/trade_offer.json is in no ENB catalog (Schema or file)", out)
        self.assertIn("C19 high: server/db/migration/V2__trade.sql is in no ENB catalog (Schema or file)", out)
        self.assertNotIn("battle_start.json", out)


class CatalogGlobTest(EnablerCase):
    """--catalog and sdd.row_checks.protocol.schemas are globs rooted at the repository: a bad one is a FAIL line
    with exit 1, never a traceback; `dir/**` covers the files under dir; a walk never enters a dot folder."""

    def assert_refused(self, argv, fragment):
        code, out, err = run(argv)
        self.assertEqual(code, 1, out + err)
        self.assertIn("FAIL: ", err)
        self.assertIn(fragment, err)
        self.assertNotIn("Traceback", err)

    def test_bad_catalog_globs_fail_cleanly(self):
        for pattern in ("", "/etc/*", "../outside/*", "server/../../x"):
            with self.subTest(pattern=pattern):
                self.assert_refused(["enablers", str(self.spec), "--catalog", pattern],
                                    f"--catalog {pattern!r} must be a glob rooted at the repository")

    def test_bad_protocol_schemas_fail_cleanly(self):
        for folder in ("/etc", "../outside"):
            with self.subTest(folder=folder):
                write(self.root, "docs/spec/spec.md", SPEC_INDEX.replace("game/protocol/schemas", folder))
                self.assert_refused(["enablers", str(self.spec)],
                                    "sdd.row_checks.protocol.schemas")

    def test_double_star_suffix_covers_files(self):
        write(self.root, "server/db/migration/V2__trade.sql", "-- fixture\n")
        code, out, _ = run(["enablers", str(self.spec), "--catalog", "server/**"])
        self.assertEqual(code, 1, out)
        self.assertIn("C19 high: server/db/migration/V2__trade.sql is in no ENB catalog", out)

    def test_walk_skips_dot_folders(self):
        write(self.root, ".git/objects/ab/cdef", "blob\n")
        write(self.root, "server/.cache/x.sql", "-- cache\n")
        write(self.root, "server/db/migration/V2__trade.sql", "-- fixture\n")
        code, out, _ = run(["enablers", str(self.spec), "--catalog", "**/*.sql", "--catalog", "**/*"])
        self.assertEqual(code, 1, out)
        self.assertNotIn(".git", out)
        self.assertNotIn(".cache", out)
        self.assertIn("server/db/migration/V2__trade.sql", out)



class MigrationsFromProfileTest(EnablerCase):
    """KIT-087 P2b: the profile's sdd.migrations folders join the catalog check in place of --catalog."""

    def test_profile_migration_folders_need_a_catalog_row(self):
        write(self.root, "server/db/migration/V2__trade.sql", "-- fixture\n")
        code, out, _ = run(["enablers", str(self.spec)])
        self.assertEqual(code, 0, out)  # no profile, no --catalog: migrations are not walked
        write(self.root, ".ai-kit.yaml", "sdd:\n  migrations: [server/db/migration]\n"
                                         "  row_checks: {protocol: {schemas: game/protocol/schemas}}\n")
        code, out, _ = run(["enablers", str(self.spec)])
        self.assertEqual(code, 1, out)
        self.assertIn("C19 high: server/db/migration/V2__trade.sql is in no ENB catalog (Schema or file)", out)
        self.assertNotIn("V1__battle.sql", out)

    def test_a_bad_profile_folder_fails_cleanly(self):
        write(self.root, ".ai-kit.yaml", "sdd:\n  migrations: ['../outside']\n")
        code, out, err = run(["enablers", str(self.spec)])
        self.assertEqual(code, 1, out + err)
        self.assertIn("migrations", err)
        self.assertNotIn("Traceback", err)


class SpecFileErrorTest(EnablerCase):
    """#356 item 1: a spec file that cannot be read (bad YAML, not UTF-8) is one `FAIL:` line that names it and exit 1,
    never a traceback; a frontmatter that is no mapping stays what it was: a finding, or a record skipped."""

    def assert_unreadable(self, rel, data, *argv):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        for args in (argv or (["check", str(self.spec)], ["enablers", str(self.spec)])):
            code, out, err = run(list(args))
            self.assertEqual(code, 1, out + err)
            self.assertIn(f"FAIL: {rel}: ", err)
            self.assertNotIn("Traceback", err)

    def test_bad_yaml_enabler(self):
        self.assert_unreadable("docs/spec/enablers/ENB-001-battle.md", b"---\nid: [ENB-001\n---\n\n# ENB-001\n")

    def test_non_utf8_enabler(self):
        self.assert_unreadable("docs/spec/enablers/ENB-001-battle.md", ENB_1.encode("utf-8") + b"\xff\xfe\n")

    def test_bad_yaml_feat(self):
        self.assert_unreadable("docs/spec/features/FEAT-001.md", b"---\nid: FEAT-001\ntitle: [x\n---\n")

    def test_non_utf8_feat(self):
        self.assert_unreadable("docs/spec/features/FEAT-001.md", b"---\nid: FEAT-001\n---\n\xff\n")

    def test_feat_frontmatter_that_is_no_mapping_is_skipped(self):
        (self.spec / "features/FEAT-001.md").write_text("---\n- FEAT-001\n---\n", encoding="utf-8")
        code, out, err = run(["check", str(self.spec)])
        self.assertEqual(code, 1, out + err)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("FEAT-001", trace.load(self.spec).feats)

    def test_enabler_frontmatter_that_is_no_mapping_stays_a_finding(self):
        self.enabler("---\n- ENB-001\n---\n")
        code, out, err = run(["check", str(self.spec)])
        self.assertEqual(code, 1, out + err)
        self.assertIn("ENB-001-battle.md: frontmatter missing, not closed by --- or not a mapping", err)
        self.assertNotIn("Traceback", err)

    def test_non_utf8_decision(self):
        self.assert_unreadable("docs/spec/decisions/DEC-001-server-battle.md", b"---\nid: DEC-001\n---\n\xff\n")


class OneVerdictTest(EnablerCase):
    """#356 item 2: `enablers` fails an ENB table error that `check` fails, so the two commands never disagree."""

    def test_table_error_fails_the_enablers_command(self):
        self.enabler(old="providesApis: [battle-wire, battle-table]", new="providesApis: [battle-wire]")
        code, out, err = self.enablers()
        self.assertEqual(code, 1, out + err)
        self.assertIn("FAIL: ENB-001: Provided contracts row battle-table is missing from providesApis", err)
        self.assertNotIn("enablers: OK", out)


class NamedFilesTest(EnablerCase):
    """#356 item 3: spec_trace.py and check_spec.py read the same files of processes/ and enablers/."""

    def test_both_tools_read_the_shared_patterns(self):
        import check_spec
        self.assertEqual(check_spec.NAMED_FILES, {"processes": "PROC-*.md", "enablers": "ENB-*.md"})
        write(self.root, "docs/spec/enablers/README.md", "# Enablers\n")
        self.assertEqual([p.name for p in check_spec.named_files(self.spec, "enablers")],
                         ["ENB-001-battle.md", "ENB-002-shop.md"])
        self.assertEqual(sorted(trace.load(self.spec).enablers), ["ENB-001", "ENB-002"])


if __name__ == "__main__":
    unittest.main()
