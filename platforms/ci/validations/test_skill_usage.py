"""platforms/tools/skill_usage.py on synthetic Claude Code transcripts and Codex rollouts (KIT-071): what counts as a
load (a kit-prefixed Skill call or command, a Read of SKILL.md, a Codex tool call naming SKILL.md), what stays apart (a
bare name, which can be a bundled Claude Code skill such as `review`), what does not count (the skill listing, plain
text, tool output), subagents and workflow transcripts folded into their session, the day window, the project filter,
the kit-only default and the --listings report."""
import contextlib
import io
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import skill_usage  # noqa: E402  (the tool lives outside this folder)


def assistant(*blocks):
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}}


def tool_use(name, **tool_input):
    return {"type": "tool_use", "id": "t", "name": name, "input": tool_input}


def user(content):
    return {"type": "user", "message": {"role": "user", "content": content}}


def codex(payload_type, **fields):
    return {"type": "response_item", "payload": {"type": payload_type, **fields}}


def listing(entries):
    """A skill_listing attachment; an entry without a description is (name, None)."""
    lines = [f"- {name}: {text}" if text else f"- {name}" for name, text in entries]
    return {"type": "attachment", "attachment": {"type": "skill_listing", "isInitial": True,
                                                 "names": [name for name, _ in entries],
                                                 "skillCount": len(entries), "content": "\n".join(lines)}}


def write_jsonl(path, records, age_days=0.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [record if isinstance(record, str) else json.dumps(record) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    stamp = time.time() - age_days * 86400
    os.utime(path, (stamp, stamp))


class SkillUsageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.claude, self.codex = root / "claude", root / "codex"
        project = self.claude / "-Users-x-shop"
        write_jsonl(project / "s1.jsonl", [
            listing([("git", "bare copy"), ("guardrails:git", "Branch policy."), ("guardrails:review", None),
                     ("anthropic-skills:pdf", "PDF files.")]),
            {"type": "system", "content": "skills: plugins/guardrails/skills/docker/SKILL.md"},
            user("please read skills/testing/SKILL.md later"),
            assistant(tool_use("Skill", skill="guardrails:git")),
            assistant(tool_use("Read", file_path="/k/plugins/guardrails/skills/review/SKILL.md")),
            assistant(tool_use("Read", file_path="/k/plugins/guardrails/skills/review/references/x.md")),
            user("<command-message>session</command-message>\n<command-name>/guardrails:session</command-name>"),
            user([{"type": "text", "text": "<command-name>/clear</command-name>"}]),
            "{not json",
            assistant(tool_use("Skill", skill="guardrails:git")),
        ])
        write_jsonl(project / "s1" / "subagents" / "agent-a.jsonl", [assistant(tool_use("Skill", skill="guardrails:testing"))])
        write_jsonl(project / "s1" / "subagents" / "workflows" / "wf_1" / "agent-b.jsonl",
                    [assistant(tool_use("Skill", skill="core:investigate"))])
        write_jsonl(project / "s2.jsonl", [
            listing([("guardrails:git", "Branch policy."), ("guardrails:session", None), ("review", "Bundled.")]),
            assistant(tool_use("Skill", skill="guardrails:git")),
            assistant(tool_use("Skill", skill="review")),
            assistant(tool_use("Skill", skill="spark:review")),
        ])
        write_jsonl(project / "old.jsonl", [assistant(tool_use("Skill", skill="guardrails:parallelize"))], age_days=40)
        write_jsonl(self.claude / "-Users-x-blog" / "b1.jsonl", [assistant(tool_use("Skill", skill="guardrails:security"))])
        day = self.codex / "2026" / "11" / "14"
        write_jsonl(day / "rollout-a.jsonl", [
            {"type": "session_meta", "payload": {"cwd": "/Users/x/shop", "base_instructions":
                                                 "read skills/session/SKILL.md when starting"}},
            codex("message", role="user", content=[{"type": "input_text", "text": "skills/review/SKILL.md"}]),
            codex("custom_tool_call", name="exec", input="cat /c/plugins/guardrails/skills/session/SKILL.md"),
            codex("function_call", name="shell", arguments=json.dumps({"command": ["sed", "-n", "1,80p",
                                                                                    "skills/git/SKILL.md"]})),
            codex("custom_tool_call_output", output="see skills/docker/SKILL.md"),
        ])
        write_jsonl(day / "rollout-b.jsonl", [
            {"type": "session_meta", "payload": {"cwd": "/Users/x/blog"}},
            codex("local_shell_call", action={"command": ["cat", "skills/session/SKILL.md"]})])
        write_jsonl(day / "notes.jsonl", [codex("custom_tool_call", input="cat skills/git/SKILL.md")])

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = skill_usage.main(["--claude-dir", str(self.claude), "--codex-dir", str(self.codex), *args])
        return code, out.getvalue()

    def test_counts_loads_per_runtime(self):
        code, out = self.run_tool("--all", "--json")
        self.assertEqual(code, 0)
        result = json.loads(out)
        claude, codex_data = result["runtimes"]["claude"], result["runtimes"]["codex"]
        self.assertEqual((claude["sessions"], codex_data["sessions"]), (3, 2))  # s1 with its subagents, s2, b1
        self.assertEqual(claude["skills"]["git"], {"sessions": 2, "tool": 2, "read": 0, "slash": 0, "bare": 0})
        self.assertEqual(claude["skills"]["review"], {"sessions": 1, "tool": 0, "read": 1, "slash": 0, "bare": 1})
        self.assertEqual(claude["skills"]["session"], {"sessions": 1, "tool": 0, "read": 0, "slash": 1, "bare": 0})
        self.assertEqual(claude["skills"]["testing"]["sessions"], 1)  # the subagent counts for s1
        self.assertEqual(claude["skills"]["investigate"]["sessions"], 1)  # a workflow agent, under a pre-KIT-055 name
        self.assertEqual(claude["skills"]["spark:review"]["tool"], 1)  # another plugin's skill keeps its prefix
        self.assertEqual(claude["skills"]["clear"], {"sessions": 0, "tool": 0, "read": 0, "slash": 0, "bare": 1})
        self.assertEqual(codex_data["skills"]["session"], {"sessions": 2})
        self.assertEqual(codex_data["skills"]["git"], {"sessions": 1})
        self.assertNotIn("docker", claude["skills"])  # named only in the listing and in tool output
        self.assertNotIn("parallelize", claude["skills"])  # its transcript is older than the window
        self.assertEqual(codex_data["skills"]["review"]["sessions"], 0)  # named only in a user message

    def test_linked_project_folder_counts_once(self):
        (self.claude / "-Users-x-shop-moved").symlink_to(self.claude / "-Users-x-shop", target_is_directory=True)
        result = json.loads(self.run_tool("--json")[1])
        self.assertEqual(result["runtimes"]["claude"]["sessions"], 3)
        self.assertEqual(result["runtimes"]["claude"]["skills"]["git"]["sessions"], 2)
        self.assertEqual(json.loads(self.run_tool("--listings", "--json")[1])["listings"], 2)

    def test_day_window(self):
        result = json.loads(self.run_tool("--all", "--json", "--days", "60")[1])
        self.assertEqual(result["runtimes"]["claude"]["sessions"], 4)
        self.assertEqual(result["runtimes"]["claude"]["skills"]["parallelize"]["sessions"], 1)

    def test_project_filter(self):
        result = json.loads(self.run_tool("--project", "SHOP", "--json")[1])
        self.assertEqual((result["runtimes"]["claude"]["sessions"], result["runtimes"]["codex"]["sessions"]), (2, 1))
        self.assertEqual(result["runtimes"]["claude"]["skills"]["security"]["sessions"], 0)
        self.assertEqual(result["runtimes"]["codex"]["skills"]["session"]["sessions"], 1)

    def test_kit_skills_by_default(self):
        result = json.loads(self.run_tool("--json")[1])
        names = set(result["runtimes"]["claude"]["skills"])
        self.assertEqual(names, skill_usage.kit_skills())
        self.assertIn("git", names)
        self.assertNotIn("clear", names)
        self.assertNotIn("spark:review", names)

    def test_named_skills_and_table(self):
        code, out = self.run_tool("--skill", "git", "--skill", "investigate")
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertIn("claude 3, codex 2", lines[0])
        self.assertEqual([line.split()[:3] for line in lines[2:]], [["git", "2", "1"], ["investigate", "1", "0"]])

    def test_listings(self):
        result = json.loads(self.run_tool("--listings", "--project", "shop", "--json")[1])
        self.assertEqual((result["sessions"], result["sessions_with_kit_load"], result["listings"]), (2, 2, 2))
        self.assertEqual(result["skills_listed"], {"median": 4, "max": 4})
        self.assertEqual(result["listings_with_undescribed"], 2)
        self.assertEqual(result["undescribed"], {"median": 1, "max": 1})
        self.assertEqual(result["listings_with_kit_twice"], 1)  # s1 lists git bare and as guardrails:git
        self.assertEqual(result["kit_twice"], {"median": 1, "max": 1})
        self.assertEqual(result["kit_without_description"], {"review": 1, "session": 1})
        code, out = self.run_tool("--listings")
        self.assertEqual(code, 0)
        self.assertIn("with a skill listing: 2", out)

    def test_missing_directories(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            skill_usage.main(["--claude-dir", str(self.claude / "none"), "--codex-dir", str(self.codex / "none"),
                              "--skill", "git", "--json"])
        result = json.loads(out.getvalue())
        self.assertEqual(result["runtimes"]["claude"]["sessions"], 0)
        self.assertEqual(result["runtimes"]["codex"]["skills"]["git"], {"sessions": 0})

    def test_rejects_non_positive_days(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            skill_usage.main(["--days", "0"])


if __name__ == "__main__":
    unittest.main()
