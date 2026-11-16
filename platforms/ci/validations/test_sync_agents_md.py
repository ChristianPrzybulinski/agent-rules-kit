"""platforms/tools/sync_agents_md.py in-process (KIT-077 item 4): the path-rule block logic that test_sync_project.py
checked through a whole sync-project.sh run. The rules are rendered as sync-project.sh renders them (frontmatter with
the project's globs, the generated marker, the body); sync-project.sh's own wiring, and the refusal before its first
write, stay integration tests there."""
import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git

KIT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location("sync_agents_md_under_test",
                                               KIT / "platforms" / "tools" / "sync_agents_md.py")
sam = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sam)
VERSION = "0.0.0"
RULE = """---
description: the {name} rule of the fixture
trigger: glob
globs:
{globs}
paths:
{globs}
---
<!-- agent-rules-kit: generated from plugins/guardrails/rules/{name}.md by platforms/tools/sync-project.sh; kit \
{version}; do not edit -->
Kit files this rule names: skill `<skill>` is `~/.ai-kit/plugins/guardrails/skills/<skill>/`.

- Always follow the {name} rule.
"""


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "AGENTS.md").write_text("# x\n", encoding="utf-8")
        self.rules({"json": ["**/*.json"]})

    def rules(self, rules):
        """Renders {rule name: [globs]} into a fresh rules folder, as sync-project.sh's render_agents_rules does."""
        self.rules_dir = Path(tempfile.mkdtemp(dir=self.root))
        for name, globs in rules.items():
            listed = "\n".join(f'  - "{glob}"' for glob in globs)
            (self.rules_dir / f"guardrails-{name}.md").write_text(
                RULE.format(name=name, globs=listed, version=VERSION), encoding="utf-8")

    def run_mode(self, mode):
        """(exit code, stdout, stderr) of `sync_agents_md.py <mode> <repo> <version> <rules-dir>`, in-process."""
        out, err = io.StringIO(), io.StringIO()
        argv = ["sync_agents_md.py", mode, str(self.repo), VERSION, str(self.rules_dir)]
        saved = sys.argv
        sys.argv = argv
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = sam.main()
        finally:
            sys.argv = saved
        return code, out.getvalue(), err.getvalue()

    def ok(self, mode):
        code, out, err = self.run_mode(mode)
        self.assertEqual(code, 0, out + err)
        return out, err

    def refused(self, mode, message):
        code, out, err = self.run_mode(mode)
        self.assertEqual(code, 1, out + err)
        self.assertIn(message, out)

    def block(self, folder="."):
        return sam.expected_blocks(self.repo, VERSION, self.rules_dir)[folder]

    def text(self, rel):
        return (self.repo / rel).read_text(encoding="utf-8")


class Location(Base):
    def test_the_intro_names_the_kit_clone(self):  # KIT-081 stage 2b: no project copy to name
        block = self.block()
        self.assertIn("A kit skill or reference a rule names is in `~/.ai-kit/plugins/guardrails/skills/<skill>/`.", block)
        self.assertNotIn(".claude/skills/", block)


class LineEndings(Base):
    def test_write_keeps_the_dominant_lf_ending(self):  # was test_agents_md_keeps_the_dominant_line_ending
        (self.repo / "AGENTS.md").write_bytes(b"# x\n\nLF line.\nCRLF line.\r\n")
        self.ok("write")
        data = (self.repo / "AGENTS.md").read_bytes()
        self.assertTrue(data.startswith(b"# x\n\nLF line.\n"), data[:40])
        self.assertNotIn(b"\r", data[data.index(sam.BEGIN.encode()):], "the block takes the dominant LF ending")

    def test_write_keeps_crlf_and_a_second_run_changes_nothing(self):  # was test_agents_md_keeps_crlf_line_endings
        (self.repo / "AGENTS.md").write_bytes(b"# x\r\n\r\nHand-written line.\r\n")
        self.ok("write")
        data = (self.repo / "AGENTS.md").read_bytes()
        self.assertTrue(data.startswith(b"# x\r\n\r\nHand-written line.\r\n\r\n" + sam.BEGIN.encode()), data[:80])
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""), "every line ends in CRLF")
        self.ok("check")
        self.ok("write")
        self.assertEqual(data, (self.repo / "AGENTS.md").read_bytes())


class Removal(Base):
    def test_removing_the_block_keeps_the_blank_line(self):  # was test_agents_md_block_removal_keeps_the_blank_line
        (self.repo / "AGENTS.md").write_text("# x\n\n" + self.block() + "\n\n## After\n\ntext\n", encoding="utf-8")
        (self.repo / "game" / "protocol").mkdir(parents=True)
        self.rules({"json": ["game/protocol/**/*.json"]})  # the rule moved: no block stays at the root
        self.ok("write")
        self.assertEqual(self.text("AGENTS.md"), "# x\n\n## After\n\ntext\n")
        self.assertIn("- Always follow the json rule.", self.text("game/protocol/AGENTS.md"))


class Refusals(Base):
    def test_broken_markers_refuse_every_mode_and_change_nothing(self):  # was test_agents_md_refuses_broken_markers
        broken = "# x\n\n" + self.block().replace(sam.END, "") + "\n"
        (self.repo / "AGENTS.md").write_text(broken, encoding="utf-8")
        for mode in ("preflight", "write", "check"):
            with self.subTest(mode=mode):
                self.refused(mode, "sync: AGENTS.md path-rule block markers are broken")
        self.assertEqual(self.text("AGENTS.md"), broken)

    def test_a_symlinked_agents_md_is_refused(self):  # was test_agents_md_refuses_a_symlinked_agents_md
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "AGENTS.md").write_text("# outside\n", encoding="utf-8")
        (self.repo / "client").mkdir()
        os.symlink(outside / "AGENTS.md", self.repo / "client" / "AGENTS.md")
        self.rules({"godot": ["client/**/*.gd"]})
        for mode in ("preflight", "write"):
            with self.subTest(mode=mode):
                self.refused(mode, "sync: client/AGENTS.md is a symbolic link; the sync writes no path-rule block "
                                   "through it")
        self.assertEqual((outside / "AGENTS.md").read_text(encoding="utf-8"), "# outside\n")

    def test_a_folder_reached_through_a_symlink_is_refused(self):
        """was test_agents_md_refuses_a_folder_reached_through_a_symlink: two targets that resolve to one real folder
        (docs/link -> ../client) would rewrite each other forever."""
        (self.repo / "client").mkdir()
        (self.repo / "docs").mkdir()
        os.symlink("../client", self.repo / "docs" / "link")
        self.rules({"json": ["docs/link/**/*.json"]})
        for mode in ("preflight", "write", "check"):
            with self.subTest(mode=mode):
                self.refused(mode, "sync: docs/link goes through a symbolic link; the sync writes no path-rule block "
                                   "there")
        self.assertFalse((self.repo / "client" / "AGENTS.md").exists())


class Scope(Base):
    def test_a_nested_checkout_keeps_its_own_block(self):  # was test_agents_md_skips_a_nested_checkout
        nested = self.repo / "vendor" / "lib"
        nested.mkdir(parents=True)
        (nested / ".git").write_text("gitdir: /elsewhere/.git/modules/lib\n", encoding="utf-8")
        foreign = "# lib\n\n" + self.block() + "\n"
        (nested / "AGENTS.md").write_text(foreign, encoding="utf-8")
        self.ok("write")
        self.assertEqual((nested / "AGENTS.md").read_text(encoding="utf-8"), foreign,
                         "a nested checkout's block is its own")
        self.ok("check")

    def test_a_missing_folder_gets_no_block(self):  # was test_agents_md_skips_a_missing_folder
        self.rules({"godot": ["client/**/*.gd"], "json": ["**/*.json"]})
        self.ok("write")
        self.assertFalse((self.repo / "client").exists(), "the sync creates no folder")
        self.ok("check")

    def test_a_folder_the_scan_skips_warns_and_still_gets_its_block(self):
        """was test_rule_paths_into_a_skipped_folder_warns"""
        (self.repo / "build" / "gen").mkdir(parents=True)
        self.rules({"json": ["build/gen/**/*.json"]})
        for mode in ("preflight", "check"):
            with self.subTest(mode=mode):
                code, out, err = self.run_mode(mode)
                self.assertIn("sync: warning: build/gen is inside a folder the AGENTS.md scan skips", err)
        self.ok("write")
        self.assertIn("- Always follow the json rule.", self.text("build/gen/AGENTS.md"))


if __name__ == "__main__":
    unittest.main()
