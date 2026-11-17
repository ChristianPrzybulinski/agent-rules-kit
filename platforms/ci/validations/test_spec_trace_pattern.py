"""spec_trace.py and our pattern (KIT-098, sdd-constitution/references/pattern.md): the matrix's Links (SysML) view
names each link by its SysML relation (derive, refine, satisfy, verify, allocate) and appears only with processes or
enablers, so an older spec renders byte for byte as before; `catalog` exports the ENBs as Backstage
`catalog-info.yaml` to a path the caller names; `diagram` prints a Mermaid flowchart of one process's step tables."""
import shutil
import sys
import unittest
from pathlib import Path

import yaml

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): temp repositories, files written
COVERS = ("platforms/ci/validations/spec_trace.py",)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import spec_trace as trace  # noqa: E402
import test_spec_trace as base  # noqa: E402  (the journey fixture of main)
import test_spec_trace_enabler as enb  # noqa: E402  (the enabler fixture)
import test_spec_trace_process as process_tests  # noqa: E402  (main's matrix for the journey fixture)

run, write = enb.run, enb.write


class LinksViewTest(enb.EnablerCase):
    def matrix(self):
        self.assertEqual(self.check(), [])
        return (self.spec / "traceability.md").read_text(encoding="utf-8")

    def test_links_view_names_the_sysml_relations(self):
        matrix = self.matrix()
        self.assertIn("## Links (SysML)", matrix)
        self.assertIn("| Rule | derive (steps) | refine (FEATs) | satisfy (ENBs) | verify (tests) |", matrix)
        self.assertIn("| REQ-F-001 | — | FEAT-001 | ENB-001 | — |", matrix)
        self.assertIn("| REQ-F-002 | — | FEAT-002 | ENB-002 | — |", matrix)
        self.assertIn("| FEAT (use case) | refine (REQs) | allocate (ENBs) |", matrix)
        self.assertIn("| FEAT-001 | REQ-F-001, REQ-NF-001 | ENB-001 |", matrix)
        self.assertTrue(matrix.index("## Contracts") < matrix.index("## Links (SysML)"))

    def test_process_steps_derive_and_their_tests_verify(self):
        write(self.root, "docs/spec/processes/PROC-001-turn.md", enb.PROCESS)
        self.req("REQ-F-003", "FEAT-001")
        self.feat("FEAT-001", "REQ-F-001, REQ-NF-001, REQ-F-003", "ENB-001", "- `ENB-001:battle-wire`.")
        matrix = self.matrix()
        self.assertIn("| REQ-F-001 | PROC-001 S1 | FEAT-001 | ENB-001 | FEAT-001 T1 |", matrix)
        self.assertIn("| REQ-F-003 | PROC-001 S2 | FEAT-001 | — | FEAT-001 T1 |", matrix)

    def test_processes_alone_render_the_view_without_allocations(self):
        shutil.rmtree(self.spec / "enablers")
        write(self.root, "docs/spec/processes/PROC-001-turn.md", enb.PROCESS)
        self.req("REQ-F-003", "FEAT-001")
        self.feat("FEAT-001", "REQ-F-001, REQ-NF-001, REQ-F-003", "", "- none.")
        matrix = self.matrix()
        self.assertIn("## Links (SysML)", matrix)
        self.assertIn("| FEAT-001 | REQ-F-001, REQ-F-003, REQ-NF-001 | — |", matrix)

    def test_a_spec_without_processes_or_enablers_renders_the_matrix_of_main(self):
        root = Path(self.tmp.name) / "plain"
        base.fixture(root)
        matrix = trace.render_matrix(trace.load(root / "docs/spec"))
        self.assertEqual(matrix, process_tests.MAIN_MATRIX)
        self.assertNotIn("SysML", matrix)


class CatalogTest(enb.EnablerCase):
    def export(self, *extra):
        out = Path(self.tmp.name) / "portal/catalog-info.yaml"
        code, stdout, err = run(["catalog", str(self.spec), "--out", str(out), *extra])
        return code, stdout, err, out

    def entities(self):
        code, stdout, err, out = self.export()
        self.assertEqual((code, err), (0, ""), stdout)
        docs = list(yaml.safe_load_all(out.read_text(encoding="utf-8")))
        return {(d["kind"], d["metadata"]["name"]): d for d in docs}

    def test_every_entity_is_valid_backstage_yaml(self):
        entities = self.entities()
        self.assertEqual(sorted(entities), [
            ("API", "battle-wire"), ("API", "shop-wire"), ("Component", "ENB-001"), ("Component", "ENB-002"),
            ("Resource", "battle-table")])
        for (kind, name), doc in entities.items():
            self.assertEqual(doc["apiVersion"], "backstage.io/v1alpha1", name)
            self.assertRegex(name, r"^[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*$")
            self.assertLessEqual(len(name), 63)
            self.assertTrue(doc["spec"]["owner"], name)
            self.assertTrue(doc["spec"]["type"], name)

    def test_component_carries_the_enb_frontmatter(self):
        entities = self.entities()
        battle = entities[("Component", "ENB-001")]
        self.assertEqual(battle["metadata"]["title"], "Battle")
        self.assertEqual(battle["spec"]["lifecycle"], "production")
        self.assertEqual(battle["spec"]["owner"], "battle-team")
        self.assertNotIn("domain", battle["spec"])  # a Component has no domain field; its System has
        self.assertEqual(battle["metadata"]["annotations"]["agent-rules-kit/domain"], "combat")
        self.assertEqual(battle["spec"]["providesApis"], ["battle-wire"])
        self.assertNotIn("consumesApis", battle["spec"])
        shop = entities[("Component", "ENB-002")]
        self.assertEqual(shop["spec"]["lifecycle"], "experimental")
        self.assertNotIn("annotations", shop["metadata"])
        self.assertEqual(shop["spec"]["consumesApis"], ["battle-wire"])
        self.assertEqual(shop["spec"]["dependsOn"], ["component:ENB-001"])

    def test_contract_rows_become_apis_and_resources(self):
        entities = self.entities()
        wire = entities[("API", "battle-wire")]
        self.assertEqual(wire["spec"]["type"], "asyncapi")
        self.assertEqual(wire["spec"]["owner"], "battle-team")
        self.assertEqual(wire["spec"]["lifecycle"], "production")
        self.assertIn("game/protocol/schemas/battle_*.json", wire["spec"]["definition"])
        table = entities[("Resource", "battle-table")]
        self.assertEqual(table["spec"]["type"], "table")
        self.assertEqual(table["spec"]["dependencyOf"], ["component:ENB-001"])

    def test_a_single_file_definition_is_a_text_reference(self):
        write(self.root, "docs/spec/enablers/ENB-002-shop.md", enb.ENB_2.replace(
            "`game/protocol/schemas/shop_*.json`", "`game/protocol/schemas/shop_open.json`"))
        entities = self.entities()
        self.assertEqual(entities[("API", "shop-wire")]["spec"]["definition"],
                         {"$text": "../game-docs/game/protocol/schemas/shop_open.json"})
        stub = entities[("API", "battle-wire")]["spec"]["definition"]  # a glob names no single file: the stub stays
        self.assertIsInstance(stub, str)
        self.assertIn("Schema or file: `game/protocol/schemas/battle_*.json`", stub)

    def test_a_missing_file_keeps_the_stub(self):
        write(self.root, "docs/spec/enablers/ENB-002-shop.md", enb.ENB_2.replace(
            "`game/protocol/schemas/shop_*.json`", "`game/protocol/schemas/shop_gone.json`"))
        self.assertIsInstance(self.entities()[("API", "shop-wire")]["spec"]["definition"], str)

    def test_an_invalid_backstage_name_refuses_the_export(self):
        long_id = "a" * 64
        self.enabler(old="battle-table", new=long_id)
        code, _, err, out = self.export()
        self.assertEqual(code, 1)
        self.assertIn(f"{long_id} is not a valid Backstage name", err)
        self.assertFalse(out.exists())

    def test_a_symlinked_out_is_refused_even_with_force(self):
        target = Path(self.tmp.name) / "target.yaml"
        target.write_text("keep\n", encoding="utf-8")
        link = Path(self.tmp.name) / "portal/catalog-info.yaml"
        link.parent.mkdir(parents=True)
        link.symlink_to(target)
        code, _, err, _ = self.export("--force")
        self.assertEqual(code, 1)
        self.assertIn("is a symbolic link", err)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep\n")

    def test_required_resource_is_a_dependency(self):
        write(self.root, "docs/spec/enablers/ENB-002-shop.md", enb.ENB_2.replace(
            "consumesApis: [battle-wire]", "consumesApis: [battle-wire, battle-table]").replace(
            "| battle-wire | message | ENB-001 | rewards after a battle |",
            "| battle-wire | message | ENB-001 | rewards after a battle |\n"
            "| battle-table | table | ENB-001 | past results |"))
        shop = self.entities()[("Component", "ENB-002")]
        self.assertEqual(shop["spec"]["consumesApis"], ["battle-wire"])
        self.assertEqual(shop["spec"]["dependsOn"], ["component:ENB-001", "resource:battle-table"])

    def test_system_and_domain_pass_through(self):
        self.enabler(old="domain: combat", new="system: game-server\ndomain: combat")
        battle = self.entities()[("Component", "ENB-001")]
        self.assertEqual(battle["spec"]["system"], "game-server")

    def test_output_is_deterministic(self):
        self.entities()
        first = (Path(self.tmp.name) / "portal/catalog-info.yaml").read_text(encoding="utf-8")
        code, _, _, out = self.export("--force")
        self.assertEqual(code, 0)
        self.assertEqual(out.read_text(encoding="utf-8"), first)

    def test_existing_file_needs_force(self):
        self.entities()
        code, _, err, _ = self.export()
        self.assertEqual(code, 1)
        self.assertIn("exists; pass --force to overwrite it", err)

    def test_off_without_enablers_writes_nothing(self):
        shutil.rmtree(self.spec / "enablers")
        code, stdout, _, out = self.export()
        self.assertEqual(code, 0)
        self.assertIn("catalog: off", stdout)
        self.assertFalse(out.exists())

    def test_an_enabler_table_error_refuses_the_export(self):
        self.enabler(old="| battle-table | table |", new="| battle-table | database |")
        code, _, err, out = self.export()
        self.assertEqual(code, 1)
        self.assertIn("battle-table kind 'database'", err)
        self.assertFalse(out.exists())

    def test_out_is_required_and_never_inside_the_kit(self):
        with self.assertRaises(SystemExit):
            run(["catalog", str(self.spec)])
        kit_file = HERE.parents[2] / "catalog-info.yaml"
        code, _, err = run(["catalog", str(self.spec), "--out", str(kit_file)])
        self.assertEqual(code, 1)
        self.assertIn("inside the kit", err)
        self.assertFalse(kit_file.exists())


class DiagramTest(enb.EnablerCase):
    def setUp(self):
        super().setUp()
        write(self.root, "docs/spec/processes/PROC-001-turn.md", enb.PROCESS.replace(
            "| S2 | pays the fee → coins drop | REQ-F-003 | FEAT-001 T1 | FEAT-001 T1 |",
            "| S2 | pays the \"fee\" → coins drop | REQ-F-003 | FEAT-001 T1 | FEAT-001 T1 |\n\n"
            "## Alternative paths\n\n"
            "| Step | At | Action → result | Rules | Implemented by | Proven by |\n"
            "|---|---|---|---|---|---|\n"
            "| A1 | S1 | no move in time → turn passes | REQ-F-001 | FEAT-001 T1 | FEAT-001 T1 |"))

    def test_flowchart_of_main_and_alternative_steps(self):
        code, out, err = run(["diagram", str(self.spec), "PROC-001"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "\n".join([
            "```mermaid",
            "flowchart TD",
            '  S1["S1 picks a move → move is locked"]',
            '  S2["S2 pays the #quot;fee#quot; → coins drop"]',
            '  A1["A1 no move in time → turn passes"]',
            "  S1 --> S2",
            "  S1 -.-> A1",
            "```",
        ]) + "\n")

    def test_unknown_process_fails(self):
        code, _, err = run(["diagram", str(self.spec), "PROC-009"])
        self.assertEqual(code, 1)
        self.assertIn("PROC-009: unknown process", err)


if __name__ == "__main__":
    unittest.main()
