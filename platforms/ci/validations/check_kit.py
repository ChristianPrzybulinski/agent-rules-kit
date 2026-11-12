#!/usr/bin/env python3
"""Kit validator (multi-plugin layout). Usage: check_kit.py [--links]

Without pyyaml/jsonschema: structural validation + WARN.
With CI=1 in the environment: missing dependencies are an error.
Each failure prints 'FAIL: <file>: <reason>'; exit 1 on any failure.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
PLUGINS_ROOT = KIT / "plugins"
SCHEMAS = KIT / "platforms/ci/schemas"
LINKS_MODE = "--links" in sys.argv
CI = os.environ.get("CI") == "1"

AGENTS_MAX_LINES = 60
DESCRIPTION_MIN = 40
DESCRIPTION_MAX = 160
DESCRIPTIONS_BUDGET = 7200
SKILL_MAX_LINES = 80
REFERENCE_MAX_LINES = 60
RULE_BODY_MAX_LINES = 40

CORE_PLUGIN = "core"
REPO_URL = "https://github.com/ChristianPrzybulinski/agent-rules-kit.git"
NAME_RE = re.compile(r"^[a-z0-9]+(?:[-.][a-z0-9]+)*$")

failures = []
warnings = []
counts = {"plugins": 0, "skills": 0, "rules": 0, "templates": 0, "indexes": 0, "links": 0,
          "hook_cases": 0}

try:
    import yaml
    import jsonschema
    FULL = True
except ImportError:
    FULL = False
    msg = "pyyaml/jsonschema missing; frontmatter validation will be structural."
    if CI:
        failures.append(f"check_kit.py: {msg} (CI=1 requires deps)")
    else:
        warnings.append(msg)


def fail(path, msg):
    failures.append(f"{path}: {msg}")
    print(f"FAIL: {path}: {msg}", file=sys.stderr)


def warn(path, msg):
    warnings.append(f"{path}: {msg}")
    print(f"WARN: {path}: {msg}", file=sys.stderr)


def rel(p):
    return str(Path(p).relative_to(KIT))


def frontmatter(path):
    """Returns (dict, total_lines) or (None, n) if invalid."""
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None, len(lines)
    close = None
    for i, line in enumerate(lines[1:], start=2):
        if line == "---":
            close = i
            break
    if close is None:
        return None, len(lines)
    block = "\n".join(lines[1:close - 1])
    if FULL:
        try:
            data = yaml.safe_load(block) or {}
        except yaml.YAMLError:
            return None, len(lines)
    else:
        data = mini_yaml(block)
    return data if isinstance(data, dict) else None, len(lines)


def mini_yaml(text):
    data, key = {}, None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if re.match(r"^\s+-\s", line) and key:
            data.setdefault(key, []).append(re.sub(r"^\s+-\s*", "", line).strip("'\""))
            continue
        match = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if match:
            key, val = match.group(1), match.group(2).strip()
            if val == "":
                data[key] = []
            elif val.startswith("[") and val.endswith("]"):
                data[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            else:
                data[key] = val.strip("'\"")
    return data


def load_schema(name):
    schema = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    if name == "skill.schema.json":
        schema["properties"]["description"]["minLength"] = DESCRIPTION_MIN
        schema["properties"]["description"]["maxLength"] = DESCRIPTION_MAX
    if name == "rule.schema.json":
        schema["properties"]["description"]["maxLength"] = DESCRIPTION_MAX
    return schema


def validate_schema(path, data, schema_name):
    schema = load_schema(schema_name)
    if FULL:
        try:
            jsonschema.validate(data, schema, format_checker=jsonschema.FormatChecker())
            return True
        except jsonschema.ValidationError as error:
            fail(rel(path), f"schema {schema_name}: {error.message}")
            return False
    ok = True
    for key in schema.get("required", []):
        if key not in data or data[key] in (None, ""):
            fail(rel(path), f"schema {schema_name}: required field '{key}' missing")
            ok = False
    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}))
        for key in data:
            if key not in allowed:
                fail(rel(path), f"schema {schema_name}: field '{key}' not in the schema")
                ok = False
    for key, spec in schema.get("properties", {}).items():
        if key not in data:
            continue
        value = data[key]
        if "enum" in spec and value not in spec["enum"]:
            fail(rel(path), f"schema {schema_name}: '{key}'={value!r} not in {spec['enum']}")
            ok = False
        if "const" in spec and value != spec["const"]:
            fail(rel(path), f"schema {schema_name}: '{key}' != '{spec['const']}'")
            ok = False
        if "pattern" in spec and isinstance(value, str) and not re.match(spec["pattern"], value):
            fail(rel(path), f"schema {schema_name}: '{key}' does not match {spec['pattern']}")
            ok = False
        if "minLength" in spec and isinstance(value, str) and len(value) < spec["minLength"]:
            fail(rel(path), f"schema {schema_name}: '{key}' is shorter than {spec['minLength']}")
            ok = False
        if "maxLength" in spec and isinstance(value, str) and len(value) > spec["maxLength"]:
            fail(rel(path), f"schema {schema_name}: '{key}' is longer than {spec['maxLength']}")
            ok = False
    return ok


def body_line_count(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            return len(lines[index + 1:])
    return len(lines)


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(rel(path), f"invalid JSON: {error}")
        return None


def dep_entry(name):
    return {"source": "git-subdir", "url": REPO_URL, "path": f"plugins/{name}"}


# --- 1. Layout ---
REQUIRED_ROOT_PATHS = [
    "INDEX.md", "README.md", "VERSION", ".devin-plugin/plugin.json",
    ".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json", "plugins", "platforms/tools",
    "platforms/ci/schemas", "platforms/ci/validations", "platforms/kits", "docs",
]
FORBIDDEN_ROOT_PATHS = [
    "AGENTS.md", "rules", "skills", "templates", "agents", "hooks.json", ".mcp.json", "mcp.json",
    "plugin.json", "LAYOUT_VERSION", "platforms/install", "knowledge", "prompts",
]
REQUIRED_PLUGIN_PATHS = [
    "INDEX.md", ".devin-plugin/plugin.json", ".claude-plugin/plugin.json", "plugin.json",
]
ALLOWED_PLUGIN_ENTRIES = {
    "AGENTS.md", "INDEX.md", ".devin-plugin", ".claude-plugin", "plugin.json", "agents", "hooks",
    "rules", "skills", "templates", "evals",
}
for required_path in REQUIRED_ROOT_PATHS:
    if not (KIT / required_path).exists():
        fail(required_path, "layout: required path missing")
for forbidden_path in FORBIDDEN_ROOT_PATHS:
    if (KIT / forbidden_path).exists():
        fail(forbidden_path, "layout: forbidden content at meta-plugin root")

plugins = {}
if PLUGINS_ROOT.exists():
    for entry in sorted(PLUGINS_ROOT.iterdir()):
        if not entry.is_dir():
            fail(rel(entry), "plugins/ entry must be a plugin directory")
            continue
        plugins[entry.name] = entry
        counts["plugins"] += 1

for name, plugin_dir in plugins.items():
    if not NAME_RE.match(name):
        fail(rel(plugin_dir), f"plugin name '{name}' is not lowercase kebab/dot")
    for required_path in REQUIRED_PLUGIN_PATHS:
        if not (plugin_dir / required_path).exists():
            fail(rel(plugin_dir / required_path), "layout: required plugin path missing")
    for entry in sorted(plugin_dir.iterdir()):
        if entry.name not in ALLOWED_PLUGIN_ENTRIES:
            fail(rel(entry), f"reserved/unknown plugin-root entry: {entry.name}")
    if (plugin_dir / "hooks.json").exists():
        fail(rel(plugin_dir / "hooks.json"), "root hooks.json is forbidden; use hooks/hooks.json")
    if name != CORE_PLUGIN:
        if (plugin_dir / "AGENTS.md").exists():
            fail(rel(plugin_dir / "AGENTS.md"), "always-on rules live only in plugins/core/AGENTS.md")
        if (plugin_dir / "hooks").exists():
            fail(rel(plugin_dir / "hooks"), "hooks live only in plugins/core/hooks/")

version = (KIT / "VERSION").read_text(encoding="utf-8").strip() if (KIT / "VERSION").exists() else ""
if version and not re.match(r"^\d+\.\d+\.\d+$", version):
    fail("VERSION", f"'{version}' is not semver")

# --- 2. Manifests and dependency graph ---
manifests = {}
dep_graph = {}
for name, plugin_dir in plugins.items():
    devin_manifest = read_json(plugin_dir / ".devin-plugin/plugin.json")
    claude_manifest = read_json(plugin_dir / ".claude-plugin/plugin.json")
    codex_manifest = read_json(plugin_dir / "plugin.json")
    manifests[name] = {"devin": devin_manifest, "claude": claude_manifest, "codex": codex_manifest}
    for kind, manifest in manifests[name].items():
        if manifest is None:
            continue
        if manifest.get("name") != name:
            fail(rel(plugin_dir / (f".{kind}-plugin/plugin.json" if kind != "codex" else "plugin.json")),
                 f"name '{manifest.get('name')}' != plugin dir '{name}'")
        if version and manifest.get("version") != version:
            fail(rel(plugin_dir), f"{kind} manifest version '{manifest.get('version')}' != VERSION '{version}'")

    devin_deps = []
    if devin_manifest is not None:
        for entry in devin_manifest.get("requiredPlugins") or []:
            path = entry.get("path") if isinstance(entry, dict) else None
            if not path or not path.startswith("plugins/"):
                fail(rel(plugin_dir / ".devin-plugin/plugin.json"),
                     f"requiredPlugins entry is not a plugins/* git-subdir: {entry}")
                continue
            dep = path.removeprefix("plugins/")
            if dep not in plugins:
                fail(rel(plugin_dir / ".devin-plugin/plugin.json"),
                     f"requiredPlugins path '{path}' is not a plugin directory")
            elif dep == name:
                fail(rel(plugin_dir / ".devin-plugin/plugin.json"), "plugin requires itself")
            else:
                devin_deps.append(dep)
            if isinstance(entry, dict) and (entry.get("source") != "git-subdir" or entry.get("url") != REPO_URL):
                fail(rel(plugin_dir / ".devin-plugin/plugin.json"),
                     f"requiredPlugins entry must be a git-subdir of this repo: {entry}")
    dep_graph[name] = sorted(set(devin_deps))

    claude_deps = []
    if claude_manifest is not None:
        for entry in claude_manifest.get("dependencies") or []:
            dep = entry.get("name") if isinstance(entry, dict) else entry
            if dep not in plugins:
                fail(rel(plugin_dir / ".claude-plugin/plugin.json"),
                     f"dependency '{dep}' is not a plugin in this repo")
            else:
                claude_deps.append(dep)
    if sorted(set(claude_deps)) != dep_graph[name]:
        fail(rel(plugin_dir), "Claude dependencies and Devin requiredPlugins name different plugin sets")


# cycle check
visiting, visited = set(), set()
def visit(node, chain):
    if node in visited:
        return
    if node in visiting:
        fail("plugins", f"dependency cycle: {' -> '.join(chain + [node])}")
        return
    visiting.add(node)
    for dep in dep_graph.get(node, []):
        visit(dep, chain + [node])
    visiting.discard(node)
    visited.add(node)
for node in dep_graph:
    visit(node, [])


def reachable(name):
    seen = set()
    stack = list(dep_graph.get(name, []))
    while stack:
        dep = stack.pop()
        if dep in seen:
            continue
        seen.add(dep)
        stack.extend(dep_graph.get(dep, []))
    return seen

# --- 3. Root meta-plugin and marketplaces ---
meta_path = KIT / ".devin-plugin/plugin.json"
meta_manifest = read_json(meta_path) if meta_path.exists() else None
if meta_manifest is not None:
    if meta_manifest.get("name") != "agent-rules-kit":
        fail(rel(meta_path), "name != 'agent-rules-kit'")
    if meta_manifest.get("version") != version:
        fail(rel(meta_path), f"version '{meta_manifest.get('version')}' != VERSION '{version}'")
    # KIT-038: the meta-plugin installs every plugin; there is no bundle and no opt-in plugin
    if meta_manifest.get("requiredPlugins") != [dep_entry(name) for name in sorted(plugins)]:
        fail(rel(meta_path), "requiredPlugins must list the git-subdir entry of every plugin, sorted by name")
    if "optionalPlugins" in meta_manifest:
        fail(rel(meta_path), "optionalPlugins is not used: every plugin is required")

marketplace = read_json(KIT / ".agents/plugins/marketplace.json") if (KIT / ".agents/plugins/marketplace.json").exists() else None
if marketplace is not None:
    entries = marketplace.get("plugins")
    if not isinstance(entries, list):
        fail(".agents/plugins/marketplace.json", "plugins must be an array")
    else:
        seen = {}
        for entry in entries:
            if not isinstance(entry, dict):
                fail(".agents/plugins/marketplace.json", "plugin entry must be an object")
                continue
            seen[entry.get("name")] = (entry.get("source") or {}).get("path")
        if sorted(seen) != sorted(plugins):
            fail(".agents/plugins/marketplace.json",
                 f"entries {sorted(seen)} != plugin dirs {sorted(plugins)}")
        for name, path in seen.items():
            if path != f"./plugins/{name}":
                fail(".agents/plugins/marketplace.json", f"'{name}' source.path != './plugins/{name}'")

claude_marketplace_path = KIT / ".claude-plugin/marketplace.json"
claude_marketplace = read_json(claude_marketplace_path) if claude_marketplace_path.exists() else None
if claude_marketplace is not None:
    if (claude_marketplace.get("renames") or {}).get("ai-kit") != CORE_PLUGIN:
        fail(rel(claude_marketplace_path), f"renames must map 'ai-kit' -> '{CORE_PLUGIN}'")
    entries = claude_marketplace.get("plugins")
    if not isinstance(entries, list):
        fail(rel(claude_marketplace_path), "plugins must be an array")
    else:
        seen = {}
        for entry in entries:
            if not isinstance(entry, dict):
                fail(rel(claude_marketplace_path), "plugin entry must be an object")
                continue
            seen[entry.get("name")] = entry
        if sorted(seen) != sorted(plugins):
            fail(rel(claude_marketplace_path),
                 f"entries {sorted(seen)} != plugin dirs {sorted(plugins)}")
        for name, entry in seen.items():
            if entry.get("source") != f"./plugins/{name}":
                fail(rel(claude_marketplace_path), f"'{name}' source != './plugins/{name}'")
            if version and entry.get("version") != version:
                fail(rel(claude_marketplace_path), f"'{name}' version != VERSION '{version}'")

for script in sorted((KIT / "platforms").rglob("*.sh")):
    if not os.access(script, os.X_OK):
        fail(rel(script), "script missing the executable bit (chmod +x)")


# --- 4. AGENTS.md ---
agents_md = plugins.get(CORE_PLUGIN, PLUGINS_ROOT / CORE_PLUGIN) / "AGENTS.md"
if agents_md.exists():
    agents_lines = len(agents_md.read_text(encoding="utf-8").splitlines())
    if agents_lines > AGENTS_MAX_LINES:
        fail(rel(agents_md), f"{agents_lines} lines (>{AGENTS_MAX_LINES})")
elif CORE_PLUGIN in plugins:
    fail(f"plugins/{CORE_PLUGIN}/AGENTS.md", "core plugin requires AGENTS.md")


# --- 5. Subagents and hooks ---
agent_owners = {}  # profile name -> plugin name
for name, plugin_dir in plugins.items():
    agents_root = plugin_dir / "agents"
    if not agents_root.exists():
        continue
    for profile in sorted(agents_root.iterdir()):
        if not profile.is_file() or profile.suffix != ".md":
            fail(rel(profile), "agents/ holds only *.md profile files; subdirectories are forbidden")
            continue
        data, _ = frontmatter(profile)
        if data is None:
            fail(rel(profile), "missing/invalid frontmatter")
            continue
        validate_schema(profile, data, "agent.schema.json")
        if data.get("name") != profile.stem:
            fail(rel(profile), f"name='{data.get('name')}' != file stem '{profile.stem}'")
        description = data.get("description")
        if not isinstance(description, str) or not DESCRIPTION_MIN <= len(description) <= DESCRIPTION_MAX:
            fail(rel(profile), f"description must be {DESCRIPTION_MIN}-{DESCRIPTION_MAX} characters")
        tools = data.get("allowed-tools")
        if not isinstance(tools, list) or not tools:
            fail(rel(profile), "allowed-tools must be a non-empty list")
        elif not set(tools) <= {"read", "grep", "glob", "exec", "edit", "write"}:
            fail(rel(profile), "allowed-tools contains an unsupported tool")
        claude_tools = data.get("tools")
        tool_names = {"read": "Read", "grep": "Grep", "glob": "Glob", "exec": "Bash", "edit": "Edit", "write": "Write"}
        expected_claude_tools = [tool_names[tool] for tool in tools] if isinstance(tools, list) \
            and all(tool in tool_names for tool in tools) else []
        if not isinstance(claude_tools, list) or claude_tools != expected_claude_tools:
            fail(rel(profile), "tools must map 1:1 and in order from allowed-tools")
        if isinstance(data.get("name"), str):
            if data["name"] in agent_owners:
                fail(rel(profile), f"agent '{data['name']}' already defined in plugin '{agent_owners[data['name']]}'")
            agent_owners[data["name"]] = name

hooks_path = plugins.get(CORE_PLUGIN, PLUGINS_ROOT / CORE_PLUGIN) / "hooks/hooks.json"
guard_commands = []
post_edit_commands = []
session_start_commands = []
if hooks_path.exists():
    hooks_data = read_json(hooks_path)
    if not isinstance(hooks_data, dict) or set(hooks_data) != {"hooks"}:
        fail(rel(hooks_path), "top level must contain only the 'hooks' key")
    else:
        hook_events = hooks_data.get("hooks")
        if not isinstance(hook_events, dict):
            fail(rel(hooks_path), "hooks must be an object")
            hook_events = {}
        unknown_events = set(hook_events) - {"PreToolUse", "PostToolUse", "SessionStart"}
        if unknown_events:
            fail(rel(hooks_path), f"unsupported hooks: {sorted(unknown_events)}")
        pre_tool_hooks = hook_events.get("PreToolUse", [])
        if not isinstance(pre_tool_hooks, list):
            fail(rel(hooks_path), "hooks.PreToolUse must be an array")
        else:
            for group_index, group in enumerate(pre_tool_hooks):
                if not isinstance(group, dict):
                    fail(rel(hooks_path), f"PreToolUse[{group_index}] must be an object")
                    continue
                matcher = group.get("matcher")
                if not isinstance(matcher, str) or not matcher:
                    fail(rel(hooks_path), f"PreToolUse[{group_index}] matcher missing")
                else:
                    try:
                        matches_both_tools = all(re.fullmatch(matcher, tool) for tool in ("exec", "Bash"))
                    except re.error:
                        matches_both_tools = False
                    if not matches_both_tools:
                        fail(rel(hooks_path), f"PreToolUse[{group_index}] matcher must match exec and Bash")
                hooks = group.get("hooks")
                if not isinstance(hooks, list):
                    fail(rel(hooks_path), f"PreToolUse[{group_index}].hooks must be an array")
                    continue
                for hook_index, hook in enumerate(hooks):
                    location = f"PreToolUse[{group_index}].hooks[{hook_index}]"
                    if not isinstance(hook, dict):
                        fail(rel(hooks_path), f"{location} must be an object")
                        continue
                    if hook.get("type") != "command":
                        fail(rel(hooks_path), f"{location} type must be 'command'")
                    timeout = hook.get("timeout")
                    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout > 10:
                        fail(rel(hooks_path), f"{location} timeout must be at most 10")
                    command = hook.get("command")
                    if not isinstance(command, str) or not command:
                        fail(rel(hooks_path), f"{location} command missing")
                    elif isinstance(timeout, (int, float)) and not isinstance(timeout, bool) and timeout <= 10:
                        guard_commands.append((command, timeout))
        post_tool_hooks = hook_events.get("PostToolUse", [])
        if not isinstance(post_tool_hooks, list):
            fail(rel(hooks_path), "hooks.PostToolUse must be an array")
        else:
            for group_index, group in enumerate(post_tool_hooks):
                if not isinstance(group, dict):
                    fail(rel(hooks_path), f"PostToolUse[{group_index}] must be an object")
                    continue
                matcher = group.get("matcher")
                if not isinstance(matcher, str) or not matcher:
                    fail(rel(hooks_path), f"PostToolUse[{group_index}] matcher missing")
                else:
                    try:
                        matches_both_tools = all(re.fullmatch(matcher, tool) for tool in ("Edit", "Write"))
                    except re.error:
                        matches_both_tools = False
                    if not matches_both_tools:
                        fail(rel(hooks_path), f"PostToolUse[{group_index}] matcher must match Edit and Write")
                hooks = group.get("hooks")
                if not isinstance(hooks, list):
                    fail(rel(hooks_path), f"PostToolUse[{group_index}].hooks must be an array")
                    continue
                for hook_index, hook in enumerate(hooks):
                    location = f"PostToolUse[{group_index}].hooks[{hook_index}]"
                    if not isinstance(hook, dict):
                        fail(rel(hooks_path), f"{location} must be an object")
                        continue
                    if hook.get("type") != "command":
                        fail(rel(hooks_path), f"{location} type must be 'command'")
                    timeout = hook.get("timeout")
                    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout > 30:
                        fail(rel(hooks_path), f"{location} timeout must be at most 30")
                    command = hook.get("command")
                    if not isinstance(command, str) or not command:
                        fail(rel(hooks_path), f"{location} command missing")
                    elif isinstance(timeout, (int, float)) and not isinstance(timeout, bool) and timeout <= 30:
                        post_edit_commands.append((command, timeout))
        session_start_hooks = hook_events.get("SessionStart", [])
        if not isinstance(session_start_hooks, list):
            fail(rel(hooks_path), "hooks.SessionStart must be an array")
        else:
            for group_index, group in enumerate(session_start_hooks):
                if not isinstance(group, dict):
                    fail(rel(hooks_path), f"SessionStart[{group_index}] must be an object")
                    continue
                matcher = group.get("matcher")
                try:
                    matches_startup = isinstance(matcher, str) and re.fullmatch(matcher, "startup") is not None
                except re.error:
                    matches_startup = False
                if not matches_startup:
                    fail(rel(hooks_path), f"SessionStart[{group_index}] matcher must match startup")
                hooks = group.get("hooks")
                if not isinstance(hooks, list):
                    fail(rel(hooks_path), f"SessionStart[{group_index}].hooks must be an array")
                    continue
                for hook_index, hook in enumerate(hooks):
                    location = f"SessionStart[{group_index}].hooks[{hook_index}]"
                    if not isinstance(hook, dict):
                        fail(rel(hooks_path), f"{location} must be an object")
                        continue
                    if hook.get("type") != "command":
                        fail(rel(hooks_path), f"{location} type must be 'command'")
                    timeout = hook.get("timeout")
                    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout > 10:
                        fail(rel(hooks_path), f"{location} timeout must be at most 10")
                    command = hook.get("command")
                    if not isinstance(command, str) or not command:
                        fail(rel(hooks_path), f"{location} command missing")
                    elif isinstance(timeout, (int, float)) and not isinstance(timeout, bool) and timeout <= 10:
                        session_start_commands.append((command, timeout))
elif CORE_PLUGIN in plugins:
    fail(f"plugins/{CORE_PLUGIN}/hooks/hooks.json", "core plugin requires hooks/hooks.json")

hook_cases_path = KIT / "platforms/ci/validations/hook_guard_cases.json"
hook_cases = read_json(hook_cases_path) if hook_cases_path.exists() else None
if hook_cases is None:
    if not hook_cases_path.exists():
        fail(rel(hook_cases_path), "hook guard cases missing")
elif not isinstance(hook_cases, dict):
    fail(rel(hook_cases_path), "top level must be an object")
else:
    blocked_cases = hook_cases.get("blocked")
    allowed_cases = hook_cases.get("allowed")
    if not isinstance(blocked_cases, list):
        fail(rel(hook_cases_path), "blocked must be an array")
        blocked_cases = []
    elif len(blocked_cases) < 10:
        fail(rel(hook_cases_path), "blocked must contain at least 10 cases")
    if not isinstance(allowed_cases, list):
        fail(rel(hook_cases_path), "allowed must be an array")
        allowed_cases = []
    elif len(allowed_cases) < 10:
        fail(rel(hook_cases_path), "allowed must contain at least 10 cases")
    for command, timeout in guard_commands:
        for expected, cases in (("blocked", blocked_cases), ("allowed", allowed_cases)):
            for case in cases:
                if not isinstance(case, str):
                    fail(rel(hook_cases_path), f"{expected} case must be a string: {case!r}")
                    continue
                payload = json.dumps({"tool_name": "exec", "tool_input": {"command": case}})
                try:
                    result = subprocess.run(
                        ["bash", "-c", command], input=payload, text=True,
                        capture_output=True, timeout=timeout, check=False)
                except subprocess.TimeoutExpired:
                    fail(rel(hook_cases_path), f"{expected} case timed out: {case}")
                    continue
                if expected == "blocked":
                    try:
                        output = json.loads(result.stdout)
                    except json.JSONDecodeError:
                        output = None
                    if result.returncode != 2 or not isinstance(output, dict) or (output.get("hookSpecificOutput") or {}).get("permissionDecision") != "deny":
                        fail(rel(hook_cases_path), f"blocked case not blocked: {case}")
                elif result.returncode != 0 or result.stdout != "":
                    fail(rel(hook_cases_path), f"allowed case not allowed cleanly: {case}")

post_edit_cases_path = KIT / "platforms/ci/validations/hook_post_edit_cases.json"
post_edit_cases = read_json(post_edit_cases_path) if post_edit_cases_path.exists() else None
if post_edit_cases is None:
    if not post_edit_cases_path.exists():
        fail(rel(post_edit_cases_path), "hook post-edit cases missing")
elif not isinstance(post_edit_cases, dict):
    fail(rel(post_edit_cases_path), "top level must be an object")
else:
    cases = post_edit_cases.get("cases")
    if not isinstance(cases, list):
        fail(rel(post_edit_cases_path), "cases must be an array")
        cases = []
    elif len(cases) < 10:
        fail(rel(post_edit_cases_path), "cases must contain at least 10 cases")
    for command, timeout in post_edit_commands:
        for case in cases:
            if not isinstance(case, dict) or not isinstance(case.get("file"), str):
                fail(rel(post_edit_cases_path), f"post-edit case must be an object with a file: {case!r}")
                continue
            name = case.get("name", case["file"])
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                edited = root / case["file"]
                edited.parent.mkdir(parents=True, exist_ok=True)
                edited.touch()
                bin_dir = root / "bin"
                bin_dir.mkdir()
                for tool, code in (case.get("tools") or {}).items():
                    if tool == "check_spec.py":
                        stub = root / ".github/spec-lint/check_spec.py"
                        stub.parent.mkdir(parents=True, exist_ok=True)
                        stub.write_text(f'import sys\nprint("stub check_spec.py finding")\nsys.exit({code})\n')
                    else:
                        stub = bin_dir / tool
                        stub.write_text(f'#!/bin/sh\necho "stub $0 finding"\nexit {code}\n')
                        stub.chmod(0o755)
                (bin_dir / "python3").symlink_to(sys.executable)
                payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": case["file"]}, "cwd": tmp})
                try:
                    result = subprocess.run(
                        [shutil.which("bash"), "-c", command], input=payload, text=True,
                        capture_output=True, timeout=timeout, cwd=tmp,
                        env={"PATH": str(bin_dir)}, check=False)
                except subprocess.TimeoutExpired:
                    fail(rel(post_edit_cases_path), f"post-edit case '{name}' timed out")
                    continue
                counts["hook_cases"] += 1
                if result.returncode != case.get("exit", 0):
                    fail(rel(post_edit_cases_path), f"post-edit case '{name}': expected exit {case.get('exit', 0)}, got {result.returncode}")
                    continue
                for stream in ("stdout", "stderr"):
                    want = case.get(stream)
                    if want is None:
                        continue
                    got = getattr(result, stream)
                    if (want == "" and got != "") or (want and want not in got):
                        fail(rel(post_edit_cases_path), f"post-edit case '{name}': {stream} expected {want!r}, got {got!r}")

session_start_cases_path = KIT / "platforms/ci/validations/hook_session_start_cases.json"
session_start_cases = read_json(session_start_cases_path) if session_start_cases_path.exists() else None
if session_start_cases is None:
    if not session_start_cases_path.exists():
        fail(rel(session_start_cases_path), "hook session-start cases missing")
elif not isinstance(session_start_cases, dict):
    fail(rel(session_start_cases_path), "top level must be an object")
else:
    cases = session_start_cases.get("cases")
    if not isinstance(cases, list):
        fail(rel(session_start_cases_path), "cases must be an array")
        cases = []
    elif len(cases) < 10:
        fail(rel(session_start_cases_path), "cases must contain at least 10 cases")
    for command, timeout in session_start_commands:
        for case in cases:
            if not isinstance(case, dict) or not isinstance(case.get("warn"), bool):
                fail(rel(session_start_cases_path), f"session-start case must be an object with a boolean warn: {case!r}")
                continue
            name = case.get("name", "?")
            if case.get("xattr") and sys.platform != "darwin":
                continue  # the iCloud Desktop & Documents branch runs on macOS only
            with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as bin_tmp:
                home = Path(tmp)
                # macOS refuses writes to the file-provider attribute, so a stub xattr answers for the case.
                stub = Path(bin_tmp) / "xattr"
                stub.write_text('#!/bin/sh\nfor last; do :; done\ncase "$last" in\n' + "".join(
                    f'  "{home / path}") echo "{value}"; exit 0 ;;\n' for path, value in (case.get("xattr") or {}).items())
                    + "esac\nexit 1\n")
                stub.chmod(0o755)
                # The real interpreter, as in the post-edit cases: under load the macOS /usr/bin/python3 shim's
                # cold start alone can exceed the hook timeout.
                (Path(bin_tmp) / "python3").symlink_to(sys.executable)
                for directory in case.get("dirs") or []:
                    (home / directory).mkdir(parents=True, exist_ok=True)
                for link, target in (case.get("links") or {}).items():
                    (home / link).parent.mkdir(parents=True, exist_ok=True)
                    (home / link).symlink_to(home / target)
                for path, text in (case.get("files") or {}).items():
                    (home / path).parent.mkdir(parents=True, exist_ok=True)
                    (home / path).write_text(text.replace("@HOME@", tmp))
                env = {"PATH": bin_tmp + os.pathsep + os.environ.get("PATH", ""), "HOME": tmp}
                env.update({var: str(home / path) for var, path in (case.get("env") or {}).items()})
                payload = case["stdin"] if "stdin" in case else json.dumps(
                    {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(home / case.get("cwd", ""))})
                try:
                    result = subprocess.run(
                        [shutil.which("bash"), "-c", command], input=payload, text=True,
                        capture_output=True, timeout=timeout, cwd=tmp, env=env, check=False)
                except subprocess.TimeoutExpired:
                    fail(rel(session_start_cases_path), f"session-start case '{name}' timed out")
                    continue
                counts["hook_cases"] += 1
                if result.returncode != 0:
                    fail(rel(session_start_cases_path), f"session-start case '{name}': expected exit 0, got {result.returncode}")
                elif case["warn"]:
                    try:
                        message = json.loads(result.stdout).get("systemMessage") or ""
                    except (json.JSONDecodeError, AttributeError):
                        message = ""
                    if "cloud-synced folder" not in message:
                        fail(rel(session_start_cases_path), f"session-start case '{name}': expected a warning, got {result.stdout!r}")
                elif result.stdout != "":
                    fail(rel(session_start_cases_path), f"session-start case '{name}': expected silence, got {result.stdout!r}")


# --- 6. Skills ---
skill_names = {}
skill_descriptions = []
skill_dirs = set()
skill_plugin = {}  # skill name -> plugin name
per_plugin_budget = {}

for name, plugin_dir in plugins.items():
    skills_root = plugin_dir / "skills"
    if not skills_root.exists():
        continue
    for directory in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        if not (directory / "SKILL.md").exists():
            fail(rel(directory), "SKILL.md missing")
    for skill_file in sorted(skills_root.rglob("SKILL.md")):
        skill_dir = skill_file.parent
        skill_name = skill_dir.name
        skill_dirs.add(skill_dir)
        counts["skills"] += 1
        if skill_dir.parent != skills_root:
            fail(rel(skill_file), "skill must be flat at skills/<name>/SKILL.md")
        if skill_name in skill_names:
            fail(rel(skill_file), f"skill '{skill_name}' already exists in plugin '{skill_names[skill_name]}'")
        skill_names[skill_name] = name
        skill_plugin[skill_name] = name
        data, lines = frontmatter(skill_file)
        if data is None:
            fail(rel(skill_file), "missing/invalid frontmatter")
            continue
        if data.get("name") != skill_name:
            fail(rel(skill_file), f"name='{data.get('name')}' != folder '{skill_name}'")
        description = data.get("description")
        if not isinstance(description, str) or not description:
            fail(rel(skill_file), "description missing or empty")
            description = ""
        skill_descriptions.append((f"{name}:{skill_name}", len(description)))
        per_plugin_budget[name] = per_plugin_budget.get(name, 0) + len(description)
        vendored = (skill_dir / "VENDOR.md").exists()
        if not vendored:
            validate_schema(skill_file, data, "skill.schema.json")
        if "subagent" in data and "agent" in data:
            fail(rel(skill_file), "skill may not set both 'subagent' and 'agent'")
        agent = data.get("agent")
        if agent is not None:
            owner = agent_owners.get(agent)
            if owner is None:
                fail(rel(skill_file), f"agent '{agent}' has no agents/ profile in any plugin")
            elif owner != name and owner not in reachable(name):
                fail(rel(skill_file), f"agent '{agent}' lives in plugin '{owner}' which '{name}' does not require")
        uses_subagent = data.get("subagent") is True or agent is not None
        context_fork = data.get("context") == "fork"
        background_false = "background" in data and data.get("background") is False
        if uses_subagent and not (context_fork and background_false):
            fail(rel(skill_file), "subagent skill requires context: fork and background: false")
        if context_fork and not uses_subagent:
            fail(rel(skill_file), "context: fork requires subagent: true or agent")

        user_only = data.get("triggers") == ["user"]
        codex_policy = skill_dir / "agents/openai.yaml"
        policy_disabled = False
        if codex_policy.exists():
            try:
                policy_data = yaml.safe_load(codex_policy.read_text(encoding="utf-8")) if FULL else None
            except yaml.YAMLError:
                policy_data = None
            if FULL and isinstance(policy_data, dict):
                policy_disabled = (policy_data.get("policy") or {}).get("allow_implicit_invocation") is False
            else:
                policy_disabled = bool(re.search(
                    r"^\s*allow_implicit_invocation:\s*false\s*$",
                    codex_policy.read_text(encoding="utf-8"), re.MULTILINE))
        claude_disabled = data.get("disable-model-invocation") is True
        if not vendored:
            if len({user_only, policy_disabled, claude_disabled}) != 1:
                fail(rel(skill_file), "user-only parity requires triggers [user], Codex policy false, and disable-model-invocation: true")
            if lines > SKILL_MAX_LINES:
                fail(rel(skill_file), f"{lines} lines (>{SKILL_MAX_LINES})")
            if "Use when" not in description:
                fail(rel(skill_file), "description lacks literal 'Use when'")
            if "Not for" not in description:
                warn(rel(skill_file), "description lacks 'Not for'")

    for reference in sorted(skills_root.glob("*/references/*.md")):
        skill_dir = reference.parent.parent
        if (skill_dir / "VENDOR.md").exists():
            continue
        reference_data, reference_lines = frontmatter(reference)
        if reference_data is None:
            fail(rel(reference), "missing/invalid frontmatter")
        else:
            validate_schema(reference, reference_data, "reference.schema.json")
        if reference_lines > REFERENCE_MAX_LINES:
            fail(rel(reference), f"{reference_lines} lines (>{REFERENCE_MAX_LINES})")
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists() or reference.name not in skill_file.read_text(encoding="utf-8"):
            fail(rel(reference), f"'{reference.name}' not referenced in {rel(skill_file)}")

description_total = sum(length for _, length in skill_descriptions)
if description_total > DESCRIPTIONS_BUDGET:
    longest = ", ".join(f"{name}={length}" for name, length in sorted(
        skill_descriptions, key=lambda item: (-item[1], item[0]))[:5])
    fail("skills", f"description budget {description_total} chars (>{DESCRIPTIONS_BUDGET}); longest: {longest}")


# --- 7. Rules ---
rule_files = []
for name, plugin_dir in plugins.items():
    rules_root = plugin_dir / "rules"
    if not rules_root.exists():
        continue
    for stray in sorted(rules_root.iterdir()):
        if stray.name in ("INDEX.md", "README.md") or stray.is_dir():
            fail(rel(stray), "rules/ holds rule files only — Devin loads every .md in it as a rule")
    for rule_file in sorted(rules_root.glob("*.md")):
        rule_files.append((name, rule_file))
        counts["rules"] += 1
        data, _ = frontmatter(rule_file)
        if data is None:
            fail(rel(rule_file), "missing/invalid frontmatter")
            continue
        validate_schema(rule_file, data, "rule.schema.json")
        trigger = data.get("trigger")
        if trigger == "always_on":
            fail(rel(rule_file), "always-on content lives only in plugins/core/AGENTS.md")
        if trigger == "glob" and not data.get("globs"):
            fail(rel(rule_file), "trigger 'glob' requires 'globs'")
        if trigger != "glob" and "globs" in data:
            fail(rel(rule_file), "'globs' is allowed only with trigger 'glob'")
        if data.get("paths") != data.get("globs"):
            fail(rel(rule_file), "paths must equal globs")
        body_lines = body_line_count(rule_file)
        if body_lines > RULE_BODY_MAX_LINES:
            fail(rel(rule_file), f"body has {body_lines} lines (>{RULE_BODY_MAX_LINES})")


# --- 8. Templates ---
SPEC_MAP = {
    "spec-index": "spec.schema.json",
    "spec-feature": "feature.schema.json",
    "spec-requirement-functional": "requirement.schema.json",
    "spec-requirement-non-functional": "requirement.schema.json",
    "spec-decision": "decision.schema.json",
    "spec-debt": "debt.schema.json",
}
for name, plugin_dir in plugins.items():
    templates_root = plugin_dir / "templates"
    if not templates_root.exists():
        continue
    for template in sorted(templates_root.glob("*.md")):
        if template.name == "INDEX.md":
            continue
        counts["templates"] += 1
        if not re.match(r"^(spec|doc|project)-[a-z0-9-]+\.md$", template.name):
            fail(rel(template), f"name '{template.name}' does not match ^(spec|doc|project)-[a-z0-9-]+\\.md$")
        stem = template.stem
        if stem in SPEC_MAP:
            data, _ = frontmatter(template)
            if data is None:
                fail(rel(template), "spec-* template without frontmatter")
            else:
                required = set(load_schema(SPEC_MAP[stem]).get("required", []))
                missing = required - set(data)
                if missing:
                    fail(rel(template), f"frontmatter missing schema-required fields: {sorted(missing)}")


# --- 9. Indexes ---
def plugin_of(path):
    path = Path(path)
    for name, plugin_dir in plugins.items():
        try:
            path.relative_to(plugin_dir)
            return name
        except ValueError:
            pass
    return None


def exempt_dir(directory):
    directory = Path(directory)
    for skill_dir in skill_dirs:
        try:
            directory.relative_to(skill_dir)
            return True
        except ValueError:
            pass
    parts = directory.relative_to(KIT).parts
    if len(parts) > 3 and parts[:2] == ("platforms", "kits"):
        return True
    # plugin content subdirs are covered by the plugin INDEX.md
    if len(parts) >= 2 and parts[0] == "plugins" and parts[1] in plugins:
        return len(parts) > 2
    return False


index_roots = [KIT / "platforms", KIT / "docs", KIT / ".github"] + [
    plugin_dir / "skills" for plugin_dir in plugins.values() if (plugin_dir / "skills").exists()]
for root in index_roots:
    if not root.exists():
        continue
    directories = [root] + [path for path in root.rglob("*") if path.is_dir()]
    for directory in sorted(directories):
        if exempt_dir(directory):
            continue
        has_index = (directory / "INDEX.md").exists()
        has_readme = (directory / "README.md").exists()
        if has_index and has_readme:
            fail(rel(directory), "has INDEX.md and README.md (never both)")
            continue
        if not (has_index or has_readme):
            fail(rel(directory), "no INDEX.md or README.md")
            continue
        counts["indexes"] += 1
        index_file = directory / ("INDEX.md" if has_index else "README.md")
        index_text = index_file.read_text(encoding="utf-8")
        entries = [path.name for path in directory.iterdir()
                   if path.name not in ("INDEX.md", "README.md", ".gitkeep")
                   and not path.name.startswith(".")]
        for entry in entries:
            if entry not in index_text:
                fail(rel(directory), f"entry '{entry}' does not appear in the index")

if not (KIT / "INDEX.md").exists() or not (KIT / "README.md").exists():
    fail(".", "root requires INDEX.md and README.md")

# per-plugin INDEX.md is generated by platforms/tools/gen_index.py; check.sh fails when it is stale
for name, plugin_dir in plugins.items():
    if not (plugin_dir / "INDEX.md").exists():
        fail(rel(plugin_dir), "no INDEX.md (run python3 platforms/tools/gen_index.py)")
    evals_root = plugin_dir / "evals"
    if not evals_root.exists():
        continue
    for entry in sorted(evals_root.iterdir()):
        if entry.name.startswith(".") or entry.name in ("INDEX.md", "README.md", "results", "mocks"):
            continue
        if entry.is_dir():
            if not ((entry / "prompt.md").exists() or (entry / "case.yaml").exists()):
                fail(rel(entry), "eval case without prompt.md or case.yaml")
            if not any((entry / "graders").glob("*.md")):
                fail(rel(entry), "eval case without graders/*.md")


# --- 10. Relative links ---
link_re = re.compile(r"\]\(([^)\s#]+)(#[^)]*)?\)")


def vendor_internal(path):
    owner = plugin_of(path)
    if owner is None:
        return False
    try:
        relative = path.relative_to(plugins[owner])
    except ValueError:
        return False
    return (len(relative.parts) >= 3 and relative.parts[0] == "skills"
            and (plugins[owner] / "skills" / relative.parts[1] / "VENDOR.md").exists())


for markdown_file in sorted(KIT.rglob("*.md")):
    if ".git" in markdown_file.parts or vendor_internal(markdown_file):
        continue
    if markdown_file.parent == KIT / "docs" / "templates" and markdown_file.name.startswith("kit-"):
        continue
    for match in link_re.finditer(markdown_file.read_text(encoding="utf-8")):
        target = match.group(1)
        counts["links"] += 1
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("~/"):
            if LINKS_MODE and not Path(target).expanduser().exists():
                fail(rel(markdown_file), f"broken absolute link: {target}")
            continue
        resolved = (markdown_file.parent / target).resolve()
        if not resolved.exists():
            fail(rel(markdown_file), f"broken link: {target}")

backtick_re = re.compile(
    r"`((?:(?:\.\./|\./)+|references/|templates/|platforms/|plugins/)[^`\s]+\.(?:md|sh|json|yml|yaml))`")
backtick_files = [agents_md, KIT / "INDEX.md", KIT / "README.md"]
backtick_files += list((KIT / "docs").glob("*.md"))
backtick_files += list((KIT / "platforms").rglob("*.md"))
for name, plugin_dir in plugins.items():
    for subdir in ("rules", "skills", "templates"):
        sub_root = plugin_dir / subdir
        if sub_root.exists():
            backtick_files += [p for p in sub_root.rglob("*.md") if not vendor_internal(p)]
    if (plugin_dir / "INDEX.md").exists():
        backtick_files.append(plugin_dir / "INDEX.md")
for markdown_file in sorted(set(path for path in backtick_files if path.exists())):
    owner = plugin_of(markdown_file)
    for match in backtick_re.finditer(markdown_file.read_text(encoding="utf-8")):
        target = match.group(1)
        if "<" in target:
            continue
        if owner is not None and re.match(r"^(?:\.\./)+platforms/", target):
            fail(rel(markdown_file), f"path escapes plugin root: {target}")
            continue
        if target.startswith(("platforms/", "plugins/")):
            base = KIT
        elif target.startswith("templates/") and owner is not None:
            base = plugins[owner]
        else:
            base = markdown_file.parent
        pattern = str(base / target)
        matches = [Path(path).resolve() for path in glob.glob(pattern)]
        if not matches:
            fail(rel(markdown_file), f"broken backtick path: {target}")
            continue
        if owner is not None and not target.startswith(("platforms/", "plugins/")):
            for resolved in matches:
                try:
                    resolved.relative_to(plugins[owner].resolve())
                except ValueError:
                    fail(rel(markdown_file), f"path escapes plugin root: {target}")
                    break


# --- 11. Vendor skills lock ---
lock = KIT / "platforms/kits/third-party/skills.lock"
lock_schema = load_schema("skills-lock.schema.json")
if lock.exists():
    for line_number, line in enumerate(lock.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 7:
            fail(rel(lock), f"line {line_number}: expected 7 |-separated fields (name|plugin|repo|path|sha|license|verified)")
            continue
        obj = dict(zip(["name", "plugin", "repo", "path", "sha", "license", "verified"], parts))
        if FULL:
            try:
                jsonschema.validate(obj, lock_schema, format_checker=jsonschema.FormatChecker())
            except jsonschema.ValidationError as error:
                fail(rel(lock), f"line {line_number}: {error.message}")
        else:
            for key in lock_schema["required"]:
                if not obj.get(key):
                    fail(rel(lock), f"line {line_number}: empty field '{key}'")
            if not re.match(r"^[0-9a-f]{40}$", obj["sha"]):
                fail(rel(lock), f"line {line_number}: invalid sha")
        if obj["plugin"] not in plugins:
            fail(rel(lock), f"line {line_number}: plugin '{obj['plugin']}' is not a plugin directory")
            continue
        owner = skill_plugin.get(obj["name"])
        if owner != obj["plugin"]:
            fail(rel(lock), f"line {line_number}: skill '{obj['name']}' lives in '{owner}', lock says '{obj['plugin']}'")
        vendor_file = plugins[obj["plugin"]] / "skills" / obj["name"] / "VENDOR.md"
        if not vendor_file.exists():
            fail(rel(vendor_file), f"lock skill '{obj['name']}' without VENDOR.md")
        elif f"sha: {obj['sha']}" not in vendor_file.read_text(encoding="utf-8"):
            fail(rel(vendor_file), f"sha diverges from the lock ({obj['sha'][:7]})")


# --- 12. Paragraph duplication ---
duplication_files = []
if agents_md.exists():
    duplication_files.append(agents_md)
for name, plugin_dir in plugins.items():
    for subdir in ("rules", "skills", "templates"):
        sub_root = plugin_dir / subdir
        if sub_root.exists():
            for markdown_file in sub_root.rglob("*.md"):
                if not vendor_internal(markdown_file):
                    duplication_files.append(markdown_file)

seen_paragraphs = {}
for markdown_file in sorted(set(duplication_files)):
    for paragraph in re.split(r"\n\s*\n", markdown_file.read_text(encoding="utf-8")):
        paragraph = paragraph.strip()
        if len(paragraph) >= 120:
            if paragraph in seen_paragraphs:
                warn(rel(markdown_file), f"paragraph duplicated from {seen_paragraphs[paragraph]}")
            else:
                seen_paragraphs[paragraph] = rel(markdown_file)


print(f"check: {'OK' if not failures else 'failed'} ({counts['plugins']} plugins, {counts['skills']} skills, "
      f"{counts['rules']} rules, {counts['templates']} templates, "
      f"{counts['indexes']} indexes, {counts['links']} links, "
      f"{counts['hook_cases']} hook cases)")
sys.exit(1 if failures else 0)
