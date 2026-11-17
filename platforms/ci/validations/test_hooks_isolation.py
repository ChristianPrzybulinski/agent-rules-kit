"""guardrails hooks run Python isolated (#352): every inline `python3 -c` command in plugins/guardrails/hooks/hooks.json
runs as `python3 -I -c`, so a module planted in the project (the hook's working directory) cannot shadow the standard
library. Without `-I`, `sys.path[0]` is "" for `-c` and a `json.py` in the project runs inside the hook.

The test plants a module for every standard-library name a hook imports, each writing a marker file, runs every inline
hook command through bash from that folder, as Claude Code does, and requires no marker."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py)

KIT = Path(__file__).resolve().parents[3]
PLUGIN = KIT / "plugins" / "guardrails"
HOOKS = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))
INLINE = re.compile(r"python3(?: -[A-Za-z]+)* -c '")
# Standard-library modules the inline hooks import that load from sys.path; a builtin or frozen one (sys, os, time)
# cannot be shadowed from there, so planting it proves nothing.
PLANTED = ("json", "re", "subprocess", "shutil", "pathlib", "importlib", "fcntl")


def inline_hooks():
    """(event, command, timeout) of every hooks.json command that runs `python3` on inline code."""
    return [(event, hook["command"], hook.get("timeout", 10))
            for event, groups in HOOKS["hooks"].items() for group in groups for hook in group["hooks"]
            if INLINE.match(hook["command"])]


class InlineHooksIsolationTest(unittest.TestCase):
    COVERS = ("plugins/guardrails/hooks/**",)

    def test_every_inline_hook_runs_isolated(self):
        commands = inline_hooks()
        self.assertGreaterEqual(len(commands), 7, "the inline hooks of hooks.json")
        for event, command, _ in commands:
            with self.subTest(event=event, command=command[:60]):
                self.assertTrue(command.startswith("python3 -I -c '"), "python3 -I -c, so the cwd is not on sys.path")

    def test_a_module_planted_in_the_project_does_not_run_in_a_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project, data, bin_dir = base / "project", base / "data", base / "bin"
            (project / ".git").mkdir(parents=True)
            (project / "docs" / "spec").mkdir(parents=True)
            (project / "docs" / "spec" / "a.md").write_text("x\n", encoding="utf-8")
            marker = base / "planted"
            for name in PLANTED:
                (project / f"{name}.py").write_text(
                    f"open({str(marker)!r}, 'a').write({name!r} + '\\n')\n", encoding="utf-8")
            bin_dir.mkdir()
            (bin_dir / "python3").symlink_to(sys.executable)
            env = {"PATH": f"{bin_dir}{os.pathsep}/usr/bin{os.pathsep}/bin", "HOME": str(base),
                   "CLAUDE_PLUGIN_ROOT": str(PLUGIN), "CLAUDE_PLUGIN_DATA": str(data), "AI_KIT_DIR": str(KIT),
                   "CLAUDE_PROJECT_DIR": str(project)}
            payload = json.dumps({"session_id": "iso", "cwd": str(project), "source": "startup",
                                  "tool_name": "Edit", "tool_input": {"file_path": "docs/spec/a.md",
                                                                      "command": "git status"},
                                  "file_path": str(project / "CLAUDE.md")})
            for event, command, timeout in inline_hooks():
                with self.subTest(event=event, command=command[:60]):
                    subprocess.run(["bash", "-c", command], input=payload, text=True, capture_output=True,
                                   timeout=timeout, cwd=str(project), env=env, check=False)
                    planted = marker.read_text(encoding="utf-8").split() if marker.exists() else []
                    marker.unlink(missing_ok=True)
                    self.assertEqual(planted, [], f"the hook imported the project's {planted}")


if __name__ == "__main__":
    unittest.main()
