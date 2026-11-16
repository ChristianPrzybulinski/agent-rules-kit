"""platforms/tools/sync_rules.py in-process (KIT-081 stage 3): the .claude/rules copies older syncs wrote go, the
project's own rules stay. A copy is a regular *.md file with the kit's generated marker line; an unmarked file, a
symbolic link and anything reached through a symbolic .claude or .claude/rules are the project's. sync-project.sh's
own wiring (no copy written, the removal after CLAUDE.md carries the marker) is tested in test_sync_project.py."""
import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git

KIT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location("sync_rules_under_test", KIT / "platforms" / "tools" / "sync_rules.py")
sr = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sr)
COPY = """---
description: the {name} rule
trigger: glob
globs:
  - "**/*.gd"
paths:
  - "**/*.gd"
---
<!-- agent-rules-kit: generated from plugins/{plugin}/rules/{name}.md by platforms/tools/sync-project.sh; kit 14.0.0; \
do not edit -->
Kit files this rule names: skill `<skill>`, reference `<file>` is `~/.ai-kit/plugins/guardrails/skills/<skill>/references/<file>`.

- Always follow the {name} rule.
"""


class SyncRulesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "repo"
        self.rules = self.repo / ".claude" / "rules"
        self.rules.mkdir(parents=True)

    def copy(self, name, plugin="guardrails"):
        path = self.rules / f"{plugin}-{name}.md"
        path.write_text(COPY.format(name=name, plugin=plugin), encoding="utf-8")
        return path

    def call(self, mode):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = sr.main(["sync_rules.py", mode, str(self.repo)])
        return code, out.getvalue()

    def test_remove_deletes_every_kit_copy_and_keeps_the_project_rules(self):
        copies = [self.copy("godot"), self.copy("godot", "dev"), self.copy("java", "core")]  # KIT-047, KIT-055 names
        own = self.rules / "my-own.md"
        own.write_text("mine\n", encoding="utf-8")
        named = self.rules / "guardrails-spec.md"  # the project's own file under a kit name: no marker
        named.write_text("---\npaths:\n  - \"x\"\n---\nmine\n", encoding="utf-8")
        code, out = self.call("remove")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines(), [
            "sync: removed .claude/rules/core-java.md: a kit rule copy; the guardrails plugin's hook gives the rule"
            " (KIT-081 stage 3)",
            "sync: removed .claude/rules/dev-godot.md: a kit rule copy; the guardrails plugin's hook gives the rule"
            " (KIT-081 stage 3)",
            "sync: removed .claude/rules/guardrails-godot.md: a kit rule copy; the guardrails plugin's hook gives the"
            " rule (KIT-081 stage 3)",
            "sync: kept .claude/rules/guardrails-spec.md: the project's own (no kit marker, or a symbolic link)",
            "sync: kept .claude/rules/my-own.md: the project's own (no kit marker, or a symbolic link)"])
        self.assertFalse(any(path.exists() for path in copies))
        self.assertEqual((own.read_text(encoding="utf-8"), named.read_text(encoding="utf-8")[-5:]), ("mine\n", "mine\n"))
        self.assertEqual(self.call("check"), (0, ""))
        self.assertEqual(self.call("remove"), (0, ""), "a second sync has nothing to say")

    def test_the_folder_goes_when_only_copies_were_in_it(self):
        self.copy("godot")
        self.assertEqual(self.call("remove")[0], 0)
        self.assertFalse(self.rules.exists())
        self.assertTrue((self.repo / ".claude").is_dir())

    def test_check_names_each_copy_left_and_the_fix(self):
        self.copy("godot")
        self.copy("tests")
        (self.rules / "my-own.md").write_text("mine\n", encoding="utf-8")
        code, out = self.call("check")
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines()[:2], ["sync: kit rule copy left: .claude/rules/guardrails-godot.md",
                                                "sync: kit rule copy left: .claude/rules/guardrails-tests.md"])
        self.assertIn(f"run platforms/tools/sync-project.sh {self.repo} once, which removes the kit-marked copies and"
                      " keeps the project's own rules", out)
        self.assertNotIn("my-own.md", out)

    def test_a_symbolic_link_is_never_followed_or_removed(self):
        outside = self.root / "outside"
        outside.mkdir()
        target = outside / "guardrails-godot.md"
        target.write_text(COPY.format(name="godot", plugin="guardrails"), encoding="utf-8")
        (self.rules / "guardrails-godot.md").symlink_to(target)
        self.copy("java")
        code, out = self.call("remove")
        self.assertEqual(code, 0, out)
        self.assertIn("sync: kept .claude/rules/guardrails-godot.md: the project's own", out)
        self.assertTrue((self.rules / "guardrails-godot.md").is_symlink() and target.is_file())
        self.assertFalse((self.rules / "guardrails-java.md").exists())

    def test_nothing_is_read_through_a_symbolic_rules_or_claude_folder(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "guardrails-godot.md").write_text(COPY.format(name="godot", plugin="guardrails"), encoding="utf-8")
        self.rules.rmdir()
        self.rules.symlink_to(outside)
        self.assertEqual(self.call("check"), (0, ""))
        self.assertEqual(self.call("remove"), (0, ""))
        self.assertTrue((outside / "guardrails-godot.md").is_file())
        other = self.root / "other"
        (other / ".claude").mkdir(parents=True)
        (other / ".claude" / "rules").symlink_to(outside)
        self.repo = self.root / "linked"
        self.repo.mkdir()
        (self.repo / ".claude").symlink_to(other / ".claude")
        self.assertEqual(self.call("remove"), (0, ""))
        self.assertTrue((outside / "guardrails-godot.md").is_file())

    def test_a_marker_quoted_inside_a_line_is_not_a_copy(self):
        own = self.rules / "notes.md"
        own.write_text("We once had `<!-- agent-rules-kit: generated from ...` lines here.\n", encoding="utf-8")
        not_md = self.rules / "guardrails-godot.txt"
        not_md.write_text(COPY.format(name="godot", plugin="guardrails"), encoding="utf-8")
        self.assertEqual(self.call("check"), (0, ""))
        self.assertEqual(self.call("remove"), (0, ""))
        self.assertTrue(own.is_file() and not_md.is_file())

    def test_a_repository_without_rules_is_clean(self):
        self.rules.rmdir()
        self.assertEqual(self.call("check"), (0, ""))
        self.assertEqual(self.call("remove"), (0, ""))

    def test_usage(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            sr.main(["sync_rules.py", "write", str(self.repo)])


if __name__ == "__main__":
    unittest.main()
