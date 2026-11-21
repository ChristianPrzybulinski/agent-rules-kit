"""row_checks.py rule n (KIT-116): a row whose code starts using another ENB's contract lists both ENB files in Files,
since its PR updates the consumer's Required contracts and the provider's Consumers. Calibrated on the Stratics case
FEAT-091 T21 (profile code querying hall_of_fame_get, which the trainer ENB provides)."""
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/row_checks.py",)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import row_checks as rc  # noqa: E402
from test_row_checks import feat_text, make_repo, run  # noqa: E402

PROOF = "`test -f client/features/profile/profile.gd`"
PROFILE_ENB = "docs/spec/enablers/ENB-021.md"
TRAINER_ENB = "docs/spec/enablers/ENB-029.md"


def enabler(eid, title, code, provided=(), required=(), status="approved"):
    """An ENB file: provided is [(contract, consumers)], required is [(contract, from)]."""
    prov = "\n".join(f"| {c} | message | ws | `protocol/schemas/{c}.json` | 1 | {who} |" for c, who in provided)
    req = "\n".join(f"| {c} | message | {src} | reads it |" for c, src in required)
    globs = "\n".join(f"- `{g}`" for g in code)
    return textwrap.dedent(f"""\
        ---
        id: {eid}
        title: "{title}"
        status: {status}
        owner: team
        providesApis: [{", ".join(c for c, _ in provided)}]
        consumesApis: [{", ".join(c for c, _ in required)}]
        ---

        # {eid} — {title}

        ## Provided contracts

        | Contract | Kind | Accessed at | Schema or file | Version | Consumers |
        |---|---|---|---|---|---|
        """) + prov + textwrap.dedent("""

        ## Required contracts

        | Contract | Kind | From | Used for |
        |---|---|---|---|
        """) + req + "\n\n## Code\n\n" + globs + "\n"


def row(files, task="Profile champion mark: Plan § Screens; query hall_of_fame_get and list the entries", tid="T1",
        status="todo", depends="—"):
    return (tid, task, files, PROOF, depends, status)


class EnablerCatalogRows(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.spec = make_repo(self.root)
        self.write_enablers()

    def write_enablers(self, profile_required=(), trainer_consumers="client", retired=False):
        folder = self.spec / "enablers"
        folder.mkdir(exist_ok=True)
        (folder / "ENB-021.md").write_text(enabler(
            "ENB-021", "Profile", ["server/src/main/java/profile/**", "client/features/profile/**"],
            provided=[("profile_get", "client")], required=profile_required), encoding="utf-8")
        (folder / "ENB-029.md").write_text(enabler(
            "ENB-029", "Trainer", ["server/src/main/java/trainer/**", "client/features/trainer/**"],
            provided=[("hall_of_fame_get", trainer_consumers), ("party", "client")],
            status="retired" if retired else "approved"), encoding="utf-8")
        (folder / "ENB-018.md").write_text(enabler(
            "ENB-018", "Inventory", ["client/features/inventory/**"], provided=[("inventory_use", "client")]),
            encoding="utf-8")

    def lint(self, rows, strict=False):
        cfg = rc.load_config(self.spec)
        (self.spec / "features" / "FEAT-900.md").write_text(feat_text("FEAT-900", rows), encoding="utf-8")
        parsed = rc.parse_feat(self.spec / "features" / "FEAT-900.md", cfg)
        return [f for f in rc.lint(parsed, cfg, strict)[0] if f.rule == "n"]

    def test_a_new_consumer_without_its_enabler_files_warns_once_per_file(self):
        found = self.lint([row("`client/features/profile/**`, `client/tests/profile/**`")])
        self.assertEqual(sorted(f.message.split(":")[0] for f in found),
                         [f"lacks {PROFILE_ENB}", f"lacks {TRAINER_ENB}"], [f.render() for f in found])
        self.assertTrue(all(f.level == rc.WARN and f.cell == "Files" for f in found))
        by_file = {f.message.split(":")[0]: f.message for f in found}
        self.assertIn("hall_of_fame_get (its Required contracts)", by_file[f"lacks {PROFILE_ENB}"])
        self.assertIn("hall_of_fame_get (Consumers: ENB-021)", by_file[f"lacks {TRAINER_ENB}"])
        self.assertIn("sdd-tasks § 3", found[0].message)

    def test_both_enabler_files_in_files_or_a_spec_glob_pass(self):
        for extra in (f"`{PROFILE_ENB}`, `{TRAINER_ENB}`", "`docs/spec/enablers/**`"):
            self.assertEqual(self.lint([row(f"`client/features/profile/**`, `client/tests/profile/**`, {extra}")]),
                             [], extra)

    def test_a_pair_already_in_both_catalogs_needs_nothing(self):
        self.write_enablers(profile_required=[("hall_of_fame_get", "ENB-029")], trainer_consumers="ENB-021, client")
        self.assertEqual(self.lint([row("`client/features/profile/**`, `client/tests/profile/**`")]), [])

    def test_only_the_missing_side_is_named(self):
        self.write_enablers(trainer_consumers="ENB-021, client")
        found = self.lint([row("`client/features/profile/**`, `client/tests/profile/**`")])
        self.assertEqual([f.message.split(":")[0] for f in found], [f"lacks {PROFILE_ENB}"])

    def test_a_row_that_builds_the_provider_is_not_a_new_consumer(self):
        files = "`client/features/profile/**`, `client/features/trainer/**`, `client/tests/profile/**`"
        self.assertEqual(self.lint([row(files)]), [])

    def test_sad_paths_have_no_finding(self):
        cases = {
            "no ENB code in Files": row("`client/app/network/**`, `client/tests/network/**`"),
            "a one-word id in prose": row("`client/features/profile/**`", task="Show the party on the profile: Plan § S"),
            "a longer id is not the shorter one": row("`client/features/profile/**`",
                                                      task="Send hall_of_fame_get_all: Plan § S"),
            "a dotted suffix is not the id": row("`client/features/profile/**`",
                                                 task="Read rewards.hall_of_fame_get: Plan § S"),
            "its own contract": row("`client/features/profile/**`", task="Answer profile_get: Plan § S"),
            "a settled row": row("`client/features/profile/**`", status="done"),
        }
        for name, case in cases.items():
            self.assertEqual(self.lint([case]), [], name)

    def test_a_backticked_one_word_id_counts(self):
        found = self.lint([row("`client/features/profile/**`", task="Show the `party` on the profile: Plan § S")])
        self.assertEqual(len(found), 2, [f.render() for f in found])

    def test_a_retired_provider_and_a_spec_without_enablers_are_skipped(self):
        self.write_enablers(retired=True)
        self.assertEqual(self.lint([row("`client/features/profile/**`")]), [])
        for path in (self.spec / "enablers").iterdir():
            path.unlink()
        (self.spec / "enablers").rmdir()
        self.assertEqual(self.lint([row("`client/features/profile/**`")]), [])

    def test_strict_fails_and_the_command_exits_1(self):
        rows = [row("`client/features/profile/**`, `client/tests/profile/**`")]
        self.assertTrue(all(f.level == rc.FAIL for f in self.lint(rows, strict=True)))
        code, out, _ = run("check", "--spec", str(self.spec), "FEAT-900")
        self.assertEqual(code, 0, out)
        self.assertIn("[n]", out)
        code, out, _ = run("check", "--spec", str(self.spec), "--strict", "FEAT-900")
        self.assertEqual(code, 1, out)


if __name__ == "__main__":
    unittest.main()
