"""platforms/tools/sync_pinned_plugin.py in-process: the kit tool calls a vendored copy rewrites to the pin (#282)."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git

KIT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location("sync_pinned_plugin_under_test",
                                               KIT / "platforms" / "tools" / "sync_pinned_plugin.py")
spp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(spp)
TOP = "$(git rev-parse --show-toplevel)"


class ToolCall(unittest.TestCase):
    def test_every_home_form_is_recognised(self):  # #282 item 4: the $HOME forms were neither pinned nor rewritten
        for text in ("python3 ~/.ai-kit/platforms/tools/x.py", 'python3 "$HOME/.ai-kit/platforms/tools/x.py"',
                     "python3 ${HOME}/.ai-kit/platforms/tools/x.py"):
            with self.subTest(text=text):
                self.assertEqual(spp.TOOL_CALL.findall(text), ["tools/x.py"])

    def test_each_form_keeps_its_quoting(self):
        cases = {
            "python3 ~/.ai-kit/platforms/tools/x.py": f'python3 "{TOP}"/.claude/ai-kit/platforms/tools/x.py',
            'python3 "$HOME/.ai-kit/platforms/tools/x.py" a': f'python3 "{TOP}/.claude/ai-kit/platforms/tools/x.py" a',
            "python3 ${HOME}/.ai-kit/platforms/tools/x.py": f"python3 {TOP}/.claude/ai-kit/platforms/tools/x.py",
        }
        for text, want in cases.items():
            with self.subTest(text=text):
                self.assertEqual(spp.pinned_text(text), want)

    def test_a_kit_source_path_is_not_a_tool_call(self):
        text = "edit ~/.ai-kit/plugins/guardrails/rules/x.md and $HOME/.ai-kit/VERSION"
        self.assertEqual(spp.TOOL_CALL.findall(text), [])
        self.assertEqual(spp.pinned_text(text), text)

    def test_rewrite_changes_a_file_with_only_a_home_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "rule.md")
            path.write_text('run "$HOME/.ai-kit/platforms/tools/x.py"\n', encoding="utf-8")
            self.assertEqual(spp.rewrite([tmp]), 0)
            self.assertEqual(path.read_text(encoding="utf-8"), f'run "{TOP}/.claude/ai-kit/platforms/tools/x.py"\n')


if __name__ == "__main__":
    unittest.main()
