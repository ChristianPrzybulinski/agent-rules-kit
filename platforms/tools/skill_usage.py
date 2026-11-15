#!/usr/bin/env python3
"""Skill loads per runtime (KIT-071): no model tokens, standard library only.

Counts, for each skill, the sessions that loaded it among the local transcripts modified in the last N days:
  claude  <claude-dir>/**/*.jsonl: a Skill tool call (`"skill": "<plugin>:<name>"` or `"<name>"`), a Read of
          `.../skills/<name>/SKILL.md` or a typed `/<name>` or `/<plugin>:<name>` command; a subagent transcript
          (`<session>/subagents/*.jsonl`) counts toward its parent session
  codex   <codex-dir>/**/rollout-*.jsonl: a tool call whose input names `skills/<name>/SKILL.md`; a skill path in the
          instructions, a message or a tool output is the skill listing, not a load
A shell command that only names a SKILL.md (`grep`, `ls`) also counts, so a session that works on the kit itself
over-counts. A skill preloaded into a subagent (`skills:`) leaves no trace in either log and is not counted.
By default only the kit's own skills (plugins/*/skills/*/) are listed; --all lists every name found.
Prints a table, or one JSON document with --json.

Usage: skill_usage.py [--days N] [--claude-dir DIR] [--codex-dir DIR] [--skill NAME ...] [--all] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
SKILL_FILE = re.compile(r"skills/([a-z0-9][a-z0-9-]*)/SKILL\.md")
SLASH = re.compile(r"<command-name>/(?:[a-z0-9-]+:)?([a-z0-9][a-z0-9-]*)</command-name>")
CODEX_CALLS = ("function_call", "custom_tool_call", "local_shell_call")
CLAUDE_METHODS = ("tool", "read", "slash")


def short(name: str) -> str:
    """`guardrails:git` -> `git`."""
    return name.rsplit(":", 1)[-1]


def kit_skills() -> set[str]:
    return {path.parent.name for path in (KIT / "plugins").glob("*/skills/*/SKILL.md")}


def recent_files(root: Path, pattern: str, cutoff: float) -> list[Path]:
    if not root.is_dir():
        return []
    files = []
    for path in sorted(root.rglob(pattern)):
        try:
            if path.is_file() and path.stat().st_mtime >= cutoff:
                files.append(path)
        except OSError:
            continue
    return files


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(block.get("text", "")) for block in content if isinstance(block, dict))
    return ""


def scan_claude(path: Path) -> dict[str, set[str]]:
    """Skill name -> the ways this transcript loaded it (tool, read, slash)."""
    found: dict[str, set[str]] = defaultdict(set)
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if '"tool_use"' not in line and "<command-name>" not in line:
                continue
            try:
                data = json.loads(line)
            except ValueError:
                continue
            if not isinstance(data, dict):
                continue
            message = data.get("message") if isinstance(data.get("message"), dict) else {}
            if data.get("type") == "user":
                for match in SLASH.finditer(text_of(message.get("content"))):
                    found[match.group(1)].add("slash")
            if data.get("type") != "assistant" or not isinstance(message.get("content"), list):
                continue
            for block in message["content"]:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                tool_input = block.get("input") if isinstance(block.get("input"), dict) else {}
                if block.get("name") == "Skill" and isinstance(tool_input.get("skill"), str):
                    found[short(tool_input["skill"])].add("tool")
                elif block.get("name") == "Read" and isinstance(tool_input.get("file_path"), str):
                    match = SKILL_FILE.search(tool_input["file_path"])
                    if match:
                        found[match.group(1)].add("read")
    return found


def scan_codex(path: Path) -> set[str]:
    found: set[str] = set()
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if "SKILL.md" not in line:
                continue
            try:
                payload = json.loads(line).get("payload")
            except (ValueError, AttributeError):
                continue
            if not isinstance(payload, dict) or payload.get("type") not in CODEX_CALLS:
                continue
            call = json.dumps([payload.get(key) for key in ("arguments", "input", "action")], ensure_ascii=False)
            found.update(match.group(1) for match in SKILL_FILE.finditer(call.replace("\\/", "/")))
    return found


def claude_session(path: Path, root: Path) -> str:
    if path.parent.name == "subagents":
        return path.parent.parent.relative_to(root).as_posix()
    return path.with_suffix("").relative_to(root).as_posix()


def count(claude_dir: Path, codex_dir: Path, days: float, now: float | None = None) -> dict:
    cutoff = (time.time() if now is None else now) - days * 86400
    claude: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))  # session -> skill -> methods
    for path in recent_files(claude_dir, "*.jsonl", cutoff):
        session = claude[claude_session(path, claude_dir)]
        for skill, methods in scan_claude(path).items():
            session[skill] |= methods
    codex = {path.relative_to(codex_dir).as_posix(): scan_codex(path)
             for path in recent_files(codex_dir, "rollout-*.jsonl", cutoff)}
    claude_skills: dict[str, dict[str, int]] = defaultdict(lambda: dict.fromkeys(("sessions",) + CLAUDE_METHODS, 0))
    for skills in claude.values():
        for skill, methods in skills.items():
            claude_skills[skill]["sessions"] += 1
            for method in methods:
                claude_skills[skill][method] += 1
    codex_skills: dict[str, dict[str, int]] = defaultdict(lambda: {"sessions": 0})
    for skills in codex.values():
        for skill in skills:
            codex_skills[skill]["sessions"] += 1
    return {"days": days, "runtimes": {
        "claude": {"sessions": len(claude), "skills": dict(claude_skills)},
        "codex": {"sessions": len(codex), "skills": dict(codex_skills)}}}


def select(result: dict, names: set[str] | None) -> dict:
    """Keeps the named skills, each listed with zeros where a runtime never loaded it."""
    found = set().union(*(set(runtime["skills"]) for runtime in result["runtimes"].values()))
    wanted = sorted(found if names is None else names)
    for runtime, data in result["runtimes"].items():
        empty = dict.fromkeys(("sessions",) + (CLAUDE_METHODS if runtime == "claude" else ()), 0)
        data["skills"] = {name: data["skills"].get(name, dict(empty)) for name in wanted}
    return result


def table(result: dict) -> str:
    claude, codex = result["runtimes"]["claude"], result["runtimes"]["codex"]
    width = max([len("skill")] + [len(name) for name in claude["skills"]])
    rows = [f"Sessions that loaded each skill, transcripts modified in the last {result['days']:g} days: "
            f"claude {claude['sessions']}, codex {codex['sessions']}.",
            f"{'skill':<{width}}  {'claude':>6}  {'codex':>5}  claude by tool/read/slash"]
    for name, counts in claude["skills"].items():
        rows.append(f"{name:<{width}}  {counts['sessions']:>6}  {codex['skills'][name]['sessions']:>5}  "
                    f"{counts['tool']}/{counts['read']}/{counts['slash']}")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=float, default=30.0, help="transcripts modified in the last N days (30)")
    parser.add_argument("--claude-dir", type=Path, default=Path.home() / ".claude" / "projects")
    parser.add_argument("--codex-dir", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument("--skill", action="append", help="list only this skill; repeatable")
    parser.add_argument("--all", action="store_true", help="list every skill name found, not only the kit's")
    parser.add_argument("--json", action="store_true", help="print one JSON document")
    args = parser.parse_args(argv)
    if args.days <= 0:
        parser.error("--days must be positive")
    names = None if args.all else set(args.skill) if args.skill else kit_skills()
    result = select(count(args.claude_dir, args.codex_dir, args.days), names)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else table(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
