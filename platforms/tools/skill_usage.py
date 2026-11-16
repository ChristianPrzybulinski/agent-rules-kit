#!/usr/bin/env python3
"""Skill loads per runtime (KIT-071): no model tokens, standard library only.

Counts, for each skill, the sessions that loaded it among the local transcripts modified in the last N days:
  claude  <claude-dir>/<project>/**/*.jsonl: a Skill call or a typed command with a kit plugin prefix
          (`guardrails:<name>`, or a name the kit's plugin had before, from the marketplace `renames`), or a Read of
          `.../skills/<name>/SKILL.md`; a transcript under `<session>/subagents/` (workflows included) counts toward
          its session. A bare `<name>` call or command is reported apart as `bare` and left out of the session count:
          Claude Code bundles skills with kit names (`review`), and a bare name may also be a vendored copy.
  codex   <codex-dir>/**/rollout-*.jsonl: a tool call whose input names `skills/<name>/SKILL.md`; a skill path in the
          instructions, a message or a tool output is the skill listing, not a load
A shell command that only names a SKILL.md (`grep`, `ls`) also counts, so a session that works on the kit itself
over-counts. A skill preloaded into a subagent (`skills:`) leaves no load in either log and is not counted.
--project keeps Claude project folders and Codex rollouts whose working directory contain the text.
--listings reads each Claude session's first skill listing instead: skills listed, characters, entries without a
description, kit skills listed twice (bare and with a kit prefix; a listing does not tell a bundled skill from a
vendored copy, so a bundled name that matches a kit skill counts too) and kit skills listed without a description.
By default only the kit's own skills (plugins/*/skills/*/) are listed; --all lists every name found.
--rules (KIT-070, #238) reports rule loads instead: for Claude Code, the records the plugin's InstructionsLoaded hook
appends to --rule-log (default ~/.claude/plugins/data/guardrails-ai-kit/instructions-loaded.jsonl, plus its rotated
.1 copy), counted per rule (`.claude/rules/<plugin>-<rule>.md`, and a record of the plugin's path-rule hook, load_reason
kit_hook_path_match (KIT-081 stage 3), under the rule's name; any other file under its file name with --all) as loads,
sessions and loads per load_reason; for Codex, the rollouts with a tool call that names a
kit skill reference (`skills/<skill>/references/<path>.md`), as sessions per `<skill>/<path>`.
Prints a table, or one JSON document with --json.

Usage: skill_usage.py [--days N] [--claude-dir DIR] [--codex-dir DIR] [--project TEXT] [--skill NAME ...] [--all]
                      [--listings | --rules [--rule-log FILE]] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
SKILL_FILE = re.compile(r"skills/([a-z0-9][a-z0-9-]*)/SKILL\.md")
REFERENCE_FILE = re.compile(r"skills/([a-z0-9][a-z0-9-]*)/references/([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.md)")
RULE_LOG = Path.home() / ".claude" / "plugins" / "data" / "guardrails-ai-kit" / "instructions-loaded.jsonl"
LOAD_REASONS = ("session_start", "nested_traversal", "path_glob_match", "include", "compact")
COMMAND = re.compile(r"<command-name>/((?:[a-z0-9-]+:)?[a-z0-9][a-z0-9-]*)</command-name>")
CODEX_CALLS = ("function_call", "custom_tool_call", "local_shell_call")
CLAUDE_METHODS = ("tool", "read", "slash", "bare")


def kit_skills() -> set[str]:
    return {path.parent.name for path in (KIT / "plugins").glob("*/skills/*/SKILL.md")}


def kit_rules() -> set[str]:
    return {path.stem for path in (KIT / "plugins").glob("*/rules/*.md")}


def kit_plugins() -> set[str]:
    """The kit's plugin names now and before its renames (KIT-038, KIT-047, KIT-055)."""
    names = {path.name for path in (KIT / "plugins").iterdir() if path.is_dir()}
    try:
        renames = json.loads((KIT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")).get("renames")
    except (OSError, ValueError):
        renames = None
    return names | set(renames or {})


def skill_key(name: str, plugins: set[str]) -> tuple[str, str]:
    """(key, method) for an invoked name: a kit-prefixed name counts under the bare skill name, another plugin's
    name keeps its prefix, and a bare name is `bare`."""
    plugin, _, short = name.rpartition(":")
    if not plugin:
        return short, "bare"
    return (short if plugin in plugins else name), "qualified"


def recent_files(root: Path, pattern: str, cutoff: float) -> list[Path]:
    if not root.is_dir():
        return []
    files, seen = [], set()
    for path in sorted(root.rglob(pattern)):
        try:
            real = path.resolve()
            if path.is_file() and real not in seen and path.stat().st_mtime >= cutoff:
                seen.add(real)  # a project folder linked under a second name holds the same transcripts
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


def claude_session(path: Path, root: Path) -> str:
    parts = path.relative_to(root).parts
    if "subagents" in parts[:-1]:
        return "/".join(parts[:parts.index("subagents")])
    return Path(*parts).with_suffix("").as_posix()


def scan_claude(path: Path, plugins: set[str]) -> dict[str, set[str]]:
    """Skill key -> the ways this transcript loaded it (tool, read, slash, bare)."""
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
                for match in COMMAND.finditer(text_of(message.get("content"))):
                    key, kind = skill_key(match.group(1), plugins)
                    found[key].add("slash" if kind == "qualified" else "bare")
            if data.get("type") != "assistant" or not isinstance(message.get("content"), list):
                continue
            for block in message["content"]:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                tool_input = block.get("input") if isinstance(block.get("input"), dict) else {}
                if block.get("name") == "Skill" and isinstance(tool_input.get("skill"), str):
                    key, kind = skill_key(tool_input["skill"], plugins)
                    found[key].add("tool" if kind == "qualified" else "bare")
                elif block.get("name") == "Read" and isinstance(tool_input.get("file_path"), str):
                    match = SKILL_FILE.search(tool_input["file_path"])
                    if match:
                        found[match.group(1)].add("read")
    return found


def first_listing(path: Path) -> dict | None:
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if '"skill_listing"' not in line:
                continue
            try:
                attachment = json.loads(line).get("attachment")
            except (ValueError, AttributeError):
                continue
            if isinstance(attachment, dict) and attachment.get("type") == "skill_listing":
                return attachment
    return None


def scan_codex(path: Path, pattern: re.Pattern = SKILL_FILE) -> tuple[set[str], str]:
    """(skills loaded, or `<skill>/<path>` references opened for REFERENCE_FILE, working directory) of one rollout."""
    found: set[str] = set()
    cwd = ""
    needle = "SKILL.md" if pattern is SKILL_FILE else "references/"
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if '"session_meta"' not in line and needle not in line:
                continue
            try:
                record = json.loads(line)
                payload = record.get("payload")
            except (ValueError, AttributeError):
                continue
            if not isinstance(payload, dict):
                continue
            if record.get("type") == "session_meta" and isinstance(payload.get("cwd"), str) and not cwd:
                cwd = payload["cwd"]
            if payload.get("type") in CODEX_CALLS:
                call = json.dumps([payload.get(key) for key in ("arguments", "input", "action")], ensure_ascii=False)
                found.update("/".join(match.groups()) for match in pattern.finditer(call.replace("\\/", "/")))
    return found, cwd


HOOK_REASON = "kit_hook_path_match"  # the plugin's path-rule hook, whose file_path is the plugin's rules/<rule>.md


def rule_key(file_path: str, plugins: set[str], reason: object = None) -> str:
    """A synced rule `.claude/rules/<plugin>-<rule>.md` counts under `<rule>` when the plugin is the kit's (now or
    before a rename), and so does a delivery of the plugin's path-rule hook (KIT-081 stage 3); any other instruction
    file under its file name."""
    path = Path(file_path)
    if reason == HOOK_REASON and path.parent.name == "rules":
        return path.stem
    if path.parent.name == "rules" and path.parent.parent.name == ".claude":
        plugin, separator, short = path.stem.partition("-")
        return short if separator and plugin in plugins else path.stem
    return path.name


def rule_loads(logs: list[Path], days: float, project: str | None = None, now: float | None = None) -> dict:
    cutoff = (time.time() if now is None else now) - days * 86400
    plugins = kit_plugins()
    sessions: set[str] = set()
    rules: dict[str, dict] = defaultdict(lambda: {"loads": 0, "sessions": set(), "reasons": defaultdict(int)})
    for log in logs:
        for path in (log.with_name(log.name + ".1"), log):
            try:
                handle = open(path, encoding="utf-8", errors="replace")
            except OSError:
                continue
            with handle:
                for line in handle:
                    try:
                        record = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(record, dict) or not isinstance(record.get("file_path"), str):
                        continue
                    stamp, cwd = record.get("ts"), record.get("cwd")
                    if not isinstance(stamp, (int, float)) or stamp < cutoff:
                        continue
                    if project and not (isinstance(cwd, str) and project.lower() in cwd.lower()):
                        continue
                    session = str(record.get("session_id"))
                    sessions.add(session)
                    entry = rules[rule_key(record["file_path"], plugins, record.get("load_reason"))]
                    entry["loads"] += 1
                    entry["sessions"].add(session)
                    entry["reasons"][str(record.get("load_reason"))] += 1
    return {"sessions": len(sessions), "rules": {name: {"loads": data["loads"], "sessions": len(data["sessions"]),
                                                        **data["reasons"]} for name, data in rules.items()}}


def codex_references(codex_dir: Path, days: float, project: str | None = None, now: float | None = None) -> dict:
    cutoff = (time.time() if now is None else now) - days * 86400
    sessions, references = 0, defaultdict(int)
    for path in recent_files(codex_dir, "rollout-*.jsonl", cutoff):
        found, cwd = scan_codex(path, REFERENCE_FILE)
        if project and project.lower() not in cwd.lower():
            continue
        sessions += 1
        for key in found:
            references[key] += 1
    return {"sessions": sessions, "references": {key: {"sessions": value} for key, value in sorted(references.items())}}


def rules_report(args) -> dict:
    claude = rule_loads(args.rule_log or [RULE_LOG], args.days, args.project)
    if not args.all:
        claude["rules"] = {name: claude["rules"].get(name, {"loads": 0, "sessions": 0})
                           for name in sorted(kit_rules())}
        for counts in claude["rules"].values():
            counts.setdefault("path_glob_match", 0)
    return {"days": args.days, "project": args.project, "claude": claude,
            "codex": codex_references(args.codex_dir, args.days, args.project)}


def rules_table(result: dict) -> str:
    claude, codex = result["claude"], result["codex"]
    scope = f" in projects matching '{result['project']}'" if result.get("project") else ""
    width = max([len("rule")] + [len(name) for name in claude["rules"]])
    rows = [f"Rule loads, last {result['days']:g} days{scope}: Claude Code sessions with a recorded load "
            f"{claude['sessions']} (InstructionsLoaded log); Codex sessions {codex['sessions']}.",
            f"{'rule':<{width}}  {'loads':>5}  {'sessions':>8}  path_glob_match"]
    rows += [f"{name:<{width}}  {data['loads']:>5}  {data['sessions']:>8}  {data.get('path_glob_match', 0)}"
             for name, data in claude["rules"].items()]
    rows.append("Codex sessions that opened a kit skill reference:")
    rows += [f"  {name}  {data['sessions']}" for name, data in codex["references"].items()] or ["  none"]
    return "\n".join(rows)


def claude_files(claude_dir: Path, project: str | None, cutoff: float) -> list[Path]:
    files = recent_files(claude_dir, "*.jsonl", cutoff)
    if project:
        files = [path for path in files if project.lower() in path.relative_to(claude_dir).parts[0].lower()]
    return files


def empty_counts(runtime: str) -> dict[str, int]:
    return dict.fromkeys(("sessions",) + (CLAUDE_METHODS if runtime == "claude" else ()), 0)


def count(claude_dir: Path, codex_dir: Path, days: float, project: str | None = None, now: float | None = None) -> dict:
    cutoff = (time.time() if now is None else now) - days * 86400
    plugins = kit_plugins()
    claude: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))  # session -> skill -> methods
    for path in claude_files(claude_dir, project, cutoff):
        session = claude[claude_session(path, claude_dir)]
        for skill, methods in scan_claude(path, plugins).items():
            session[skill] |= methods
    codex: dict[str, set[str]] = {}
    for path in recent_files(codex_dir, "rollout-*.jsonl", cutoff):
        skills, cwd = scan_codex(path)
        if not project or project.lower() in cwd.lower():
            codex[path.relative_to(codex_dir).as_posix()] = skills
    claude_skills: dict[str, dict[str, int]] = defaultdict(lambda: empty_counts("claude"))
    for skills in claude.values():
        for skill, methods in skills.items():
            if methods - {"bare"}:
                claude_skills[skill]["sessions"] += 1
            for method in methods:
                claude_skills[skill][method] += 1
    codex_skills: dict[str, dict[str, int]] = defaultdict(lambda: empty_counts("codex"))
    for skills in codex.values():
        for skill in skills:
            codex_skills[skill]["sessions"] += 1
    return {"days": days, "project": project, "runtimes": {
        "claude": {"sessions": len(claude), "skills": dict(claude_skills)},
        "codex": {"sessions": len(codex), "skills": dict(codex_skills)}}}


def select(result: dict, names: set[str] | None) -> dict:
    """Keeps the named skills, each listed with zeros where a runtime never loaded it."""
    found = set().union(*(set(runtime["skills"]) for runtime in result["runtimes"].values()))
    wanted = sorted(found if names is None else names)
    for runtime, data in result["runtimes"].items():
        data["skills"] = {name: data["skills"].get(name, empty_counts(runtime)) for name in wanted}
    return result


def listings(claude_dir: Path, days: float, project: str | None = None, now: float | None = None) -> dict:
    cutoff = (time.time() if now is None else now) - days * 86400
    plugins, kit = kit_plugins(), kit_skills()
    sessions: set[str] = set()
    loaded: set[str] = set()
    first: dict[str, dict] = {}
    for path in claude_files(claude_dir, project, cutoff):
        key = claude_session(path, claude_dir)
        sessions.add(key)
        if any(skill in kit and methods - {"bare"} for skill, methods in scan_claude(path, plugins).items()):
            loaded.add(key)
        if "subagents" not in path.relative_to(claude_dir).parts[:-1] and key not in first:
            listing = first_listing(path)
            if listing is not None:
                first[key] = listing
    sizes, chars, undescribed, twice = [], [], [], []
    with_undescribed = 0
    name_only: dict[str, int] = defaultdict(int)
    for listing in first.values():
        names = [name for name in listing.get("names") or [] if isinstance(name, str)]
        content = str(listing.get("content") or "")
        described = {line[2:].split(": ", 1)[0] for line in content.splitlines() if line.startswith("- ") and ": " in line}
        missing = [name for name in names if name not in described]
        sizes.append(len(names))
        chars.append(len(content))
        undescribed.append(len(missing))
        with_undescribed += bool(missing)
        qualified = {name.rpartition(":")[2] for name in names if name.rpartition(":")[0] in plugins}
        twice.append(len({name for name in names if ":" not in name and name in kit} & qualified))
        for skill in {name.rpartition(":")[2] for name in missing if name.rpartition(":")[2] in kit}:
            name_only[skill] += 1

    def spread(values: list[int]) -> dict[str, int | None]:
        return {"median": statistics.median_high(values) if values else None, "max": max(values, default=None)}

    return {"days": days, "project": project, "sessions": len(sessions), "sessions_with_kit_load": len(loaded),
            "listings": len(first), "skills_listed": spread(sizes), "characters": spread(chars),
            "listings_with_undescribed": with_undescribed, "undescribed": spread(undescribed),
            "listings_with_kit_twice": sum(1 for value in twice if value),
            "kit_twice": spread([value for value in twice if value]),
            "kit_without_description": dict(sorted(name_only.items()))}


def table(result: dict) -> str:
    claude, codex = result["runtimes"]["claude"], result["runtimes"]["codex"]
    width = max([len("skill")] + [len(name) for name in claude["skills"]])
    scope = f" in projects matching '{result['project']}'" if result.get("project") else ""
    rows = [f"Sessions that loaded each skill, transcripts modified in the last {result['days']:g} days{scope}: "
            f"claude {claude['sessions']}, codex {codex['sessions']}.",
            f"{'skill':<{width}}  {'claude':>6}  {'codex':>5}  claude by tool/read/slash, bare apart"]
    for name, counts in claude["skills"].items():
        rows.append(f"{name:<{width}}  {counts['sessions']:>6}  {codex['skills'][name]['sessions']:>5}  "
                    f"{counts['tool']}/{counts['read']}/{counts['slash']}, {counts['bare']}")
    return "\n".join(rows)


def listing_table(result: dict) -> str:
    scope = f" in projects matching '{result['project']}'" if result.get("project") else ""
    return "\n".join([
        f"Claude sessions, transcripts modified in the last {result['days']:g} days{scope}: {result['sessions']}; "
        f"with a kit skill load: {result['sessions_with_kit_load']}; with a skill listing: {result['listings']}.",
        f"skills listed: median {result['skills_listed']['median']}, max {result['skills_listed']['max']}; "
        f"characters: median {result['characters']['median']}, max {result['characters']['max']}.",
        f"listings with entries lacking a description: {result['listings_with_undescribed']} "
        f"(median {result['undescribed']['median']}, max {result['undescribed']['max']} entries).",
        f"listings naming kit skills twice: {result['listings_with_kit_twice']} "
        f"(median {result['kit_twice']['median']}, max {result['kit_twice']['max']} names).",
        "kit skills listed without a description: " + (", ".join(
            f"{name} {value}" for name, value in result["kit_without_description"].items()) or "none") + "."])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=float, default=30.0, help="transcripts modified in the last N days (30)")
    parser.add_argument("--claude-dir", type=Path, default=Path.home() / ".claude" / "projects")
    parser.add_argument("--codex-dir", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument("--project", help="only Claude project folders and Codex working directories with this text")
    parser.add_argument("--skill", action="append", help="list only this skill; repeatable")
    parser.add_argument("--all", action="store_true", help="list every skill name found, not only the kit's")
    parser.add_argument("--listings", action="store_true", help="report the Claude skill listings instead of loads")
    parser.add_argument("--rules", action="store_true", help="report rule loads and Codex reference opens instead")
    parser.add_argument("--rule-log", type=Path, action="append",
                        help="InstructionsLoaded log to read with --rules; repeatable (default: the plugin's)")
    parser.add_argument("--json", action="store_true", help="print one JSON document")
    args = parser.parse_args(argv)
    if args.days <= 0:
        parser.error("--days must be positive")
    if args.rules:
        result = rules_report(args)
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else rules_table(result))
        return 0
    if args.listings:
        result = listings(args.claude_dir, args.days, args.project)
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else listing_table(result))
        return 0
    names = None if args.all else set(args.skill) if args.skill else kit_skills()
    result = select(count(args.claude_dir, args.codex_dir, args.days, args.project), names)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else table(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
