"""gen_index.py: generated plugin INDEX.md files on a throwaway kit (KIT-040)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
SCRIPT = KIT / "platforms" / "tools" / "gen_index.py"
REGENERATE = "python3 platforms/tools/gen_index.py"


def run(kit, *args):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), "--kit", str(kit), *args],
                          capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def manifest(plugin_dir, description, dependencies=None):
    data = {"name": plugin_dir.name, "version": "0.0.0", "description": description}
    if dependencies:
        data["dependencies"] = dependencies
    write(plugin_dir / ".claude-plugin" / "plugin.json", json.dumps(data))


def skill(plugin_dir, name, description, extra=""):
    write(plugin_dir / "skills" / name / "SKILL.md",
          f"---\nname: {name}\ndescription: {description}\n{extra}---\n\n# {name}\n")


class GenIndexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.kit = Path(self.tmp.name)
        self.demo = self.kit / "plugins" / "demo"
        manifest(self.demo, "demo plugin: a fixture")
        skill(self.demo, "alpha", "Alpha does a thing. Use when A.", "triggers:\n  - user\n  - model\n")
        skill(self.demo, "beta", '"Beta, with a | pipe and a \\"quote\\". Use when B."', "triggers: [user]\n")
        skill(self.demo, "gamma", "Gamma is user only by flag. Use when G.", "disable-model-invocation: true\n")
        skill(self.demo, "delta", "Delta has no triggers key. Use when D.")
        write(self.demo / "AGENTS.md", "# rules\n")
        write(self.demo / "rules" / "demo.md", "---\ndescription: x\n---\n")
        write(self.demo / "agents" / "helper.md", "---\nname: helper\n---\n")
        write(self.demo / "templates" / "doc-note.md", "# note\n")
        write(self.demo / "evals" / "case-one" / "prompt.md", "p\n")
        write(self.demo / "evals" / "results" / "old.json", "{}")
        write(self.demo / "evals" / ".hidden", "")
        write(self.demo / "hooks" / "hooks.json", "{}")
        bundle = self.kit / "plugins" / "bundle"
        manifest(bundle, "bundle: manifest only", ["demo"])

    def tearDown(self):
        self.tmp.cleanup()

    def generated(self, name="demo"):
        run(self.kit)
        return (self.kit / "plugins" / name / "INDEX.md").read_text(encoding="utf-8")

    def test_skill_rows_carry_description_and_invocation(self):
        text = self.generated()
        self.assertIn("# demo/ — demo plugin: a fixture", text)
        self.assertIn("| `alpha` | user, model | Alpha does a thing. Use when A. |", text)
        self.assertIn('| `beta` | user | Beta, with a \\| pipe and a "quote". Use when B. |', text)
        self.assertIn("| `gamma` | user | Gamma is user only by flag. Use when G. |", text)
        self.assertIn("| `delta` | user, model | Delta has no triggers key. Use when D. |", text)

    def test_every_content_directory_is_listed_and_noise_is_not(self):
        text = self.generated()
        for expected in ("## Always-on\n\n- `AGENTS.md`", "## `rules/`\n\n- `demo.md`",
                         "## `agents/`\n\n- `helper.md`", "## `templates/`\n\n- `doc-note.md`",
                         "## `evals/`\n\n- `case-one`\n", "## `hooks/`\n\n- `hooks.json`"):
            self.assertIn(expected, text)
        self.assertNotIn("results", text)
        self.assertNotIn(".hidden", text)

    def test_manifest_only_plugin_lists_dependencies_and_no_empty_section(self):
        text = self.generated("bundle")
        self.assertIn("Depends on: `demo`", text)
        self.assertNotIn("## `skills/`", text)
        self.assertNotIn("## `rules/`", text)

    def test_check_fails_on_missing_and_hand_edited_index_and_names_the_fix(self):
        missing = run(self.kit, "--check")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("plugins/demo/INDEX.md is stale", missing.stderr)
        self.assertIn(REGENERATE, missing.stderr)
        run(self.kit)
        self.assertEqual(run(self.kit, "--check").returncode, 0)
        index = self.demo / "INDEX.md"
        index.write_text(index.read_text(encoding="utf-8") + "\nhand-written line\n", encoding="utf-8")
        edited = run(self.kit, "--check")
        self.assertEqual(edited.returncode, 1)
        self.assertIn("plugins/demo/INDEX.md is stale", edited.stderr)
        self.assertNotIn("bundle", edited.stderr)

    def test_a_changed_description_or_new_skill_makes_the_index_stale(self):
        run(self.kit)
        skill(self.demo, "alpha", "Alpha changed. Use when A.", "triggers: [user, model]\n")
        self.assertEqual(run(self.kit, "--check").returncode, 1)
        run(self.kit)
        skill(self.demo, "epsilon", "Epsilon is new. Use when E.")
        self.assertEqual(run(self.kit, "--check").returncode, 1)
        self.assertIn("| `epsilon` |", self.generated())

    def test_a_new_plugin_is_picked_up_without_a_registered_list(self):
        run(self.kit)
        manifest(self.kit / "plugins" / "fresh", "fresh: brand new")
        result = run(self.kit, "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("plugins/fresh/INDEX.md is stale", result.stderr)

    def test_write_is_idempotent_and_reports_only_changes(self):
        first = run(self.kit)
        self.assertIn("wrote plugins/demo/INDEX.md", first.stdout)
        second = run(self.kit)
        self.assertEqual(second.returncode, 0)
        self.assertNotIn("wrote", second.stdout)
        self.assertIn("current", second.stdout)

    def test_unreadable_plugin_files_exit_2_with_the_path(self):
        write(self.demo / "skills" / "folded" / "SKILL.md",
              "---\nname: folded\ndescription: >\n  folded text\n---\n")
        folded = run(self.kit, "--check")
        self.assertEqual(folded.returncode, 2)
        self.assertIn("folded/SKILL.md", folded.stderr)
        self.assertIn("block scalar", folded.stderr)
        (self.demo / "skills" / "folded" / "SKILL.md").unlink()
        write(self.demo / "skills" / "bare" / "notes.md", "no skill file\n")
        bare = run(self.kit, "--check")
        self.assertEqual(bare.returncode, 2)
        self.assertIn("no SKILL.md", bare.stderr)

    def test_the_checked_in_indexes_are_current(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
