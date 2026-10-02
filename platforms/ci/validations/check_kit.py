#!/usr/bin/env python3
"""Kit validator (layout v6). Usage: check_kit.py [--links]

Without pyyaml/jsonschema: structural validation + WARN.
With CI=1 in the environment: missing dependencies are an error.
Each failure prints 'FAIL: <file>: <reason>'; exit 1 on any failure.
"""
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
PLUGIN = KIT / "plugins/ai-kit"
SCHEMAS = KIT / "platforms/ci/schemas"
LINKS_MODE = "--links" in sys.argv
CI = os.environ.get("CI") == "1"

AGENTS_MAX_LINES = 60
DESCRIPTION_MIN = 40
DESCRIPTION_MAX = 160
DESCRIPTIONS_BUDGET = 7200
SKILL_MAX_LINES = 80
REFERENCE_MAX_LINES = 60
RULE_BODY_MAX_LINES = 12

failures = []
warnings = []
counts = {"skills": 0, "rules": 0, "templates": 0, "indexes": 0, "links": 0}

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


# --- 1. Layout ---
REQUIRED_ROOT_PATHS = [
    "INDEX.md", "README.md", "VERSION", ".devin-plugin/plugin.json",
    ".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json", "plugins", "platforms/tools",
    "platforms/ci/schemas", "platforms/ci/validations", "platforms/kits", "docs",
]
REQUIRED_PLUGIN_PATHS = [
    "AGENTS.md", "INDEX.md", ".devin-plugin/plugin.json", ".claude-plugin/plugin.json",
    "plugin.json", "agents", "hooks/hooks.json", "rules", "skills", "templates",
]
FORBIDDEN_ROOT_PATHS = [
    "AGENTS.md", "rules", "skills", "templates", "agents", "hooks.json", ".mcp.json", "mcp.json",
    "plugin.json", "LAYOUT_VERSION", "platforms/install", "knowledge", "prompts",
]
for required_path in REQUIRED_ROOT_PATHS:
    if not (KIT / required_path).exists():
        fail(required_path, "layout: required path missing")
for required_path in REQUIRED_PLUGIN_PATHS:
    if not (PLUGIN / required_path).exists():
        fail(f"plugins/ai-kit/{required_path}", "layout: required plugin path missing")
for forbidden_path in FORBIDDEN_ROOT_PATHS:
    if (KIT / forbidden_path).exists():
        fail(forbidden_path, "layout: forbidden content at meta-plugin root")

plugins_root = KIT / "plugins"
if plugins_root.exists():
    for entry in sorted(plugins_root.iterdir()):
        if not entry.is_dir():
            fail(rel(entry), "plugins/ entry must be a plugin directory")
        elif not (entry / ".devin-plugin/plugin.json").exists():
            fail(rel(entry), "plugin directory missing .devin-plugin/plugin.json")

allowed_plugin_entries = {
    "AGENTS.md", "INDEX.md", ".devin-plugin", ".claude-plugin", "plugin.json", "agents", "hooks",
    "rules", "skills", "templates",
}
if PLUGIN.exists():
    for entry in sorted(PLUGIN.iterdir()):
        if entry.name not in allowed_plugin_entries:
            fail(rel(entry), f"reserved/unknown plugin-root entry: {entry.name}")
legacy_hooks_path = PLUGIN / "hooks.json"
if legacy_hooks_path.exists():
    fail(rel(legacy_hooks_path), "root hooks.json is forbidden; use hooks/hooks.json")

version = (KIT / "VERSION").read_text(encoding="utf-8").strip() if (KIT / "VERSION").exists() else ""
if version and not re.match(r"^\d+\.\d+\.\d+$", version):
    fail("VERSION", f"'{version}' is not semver")

required_plugin = {
    "source": "git-subdir",
    "url": "https://github.com/ChristianPrzybulinski/agent-rules-kit.git",
    "path": "plugins/ai-kit",
}
meta_path = KIT / ".devin-plugin/plugin.json"
meta_manifest = read_json(meta_path) if meta_path.exists() else None
if meta_manifest is not None:
    if meta_manifest.get("name") != "agent-rules-kit":
        fail(rel(meta_path), "name != 'agent-rules-kit'")
    if meta_manifest.get("version") != version:
        fail(rel(meta_path), f"version '{meta_manifest.get('version')}' != VERSION '{version}'")
    if meta_manifest.get("requiredPlugins") != [required_plugin]:
        fail(rel(meta_path), "requiredPlugins must contain exactly the ai-kit git-subdir entry")

if plugins_root.exists():
    for plugin_directory in sorted(path for path in plugins_root.iterdir() if path.is_dir()):
        for manifest_path in (
                plugin_directory / ".devin-plugin/plugin.json",
                plugin_directory / ".claude-plugin/plugin.json",
                plugin_directory / "plugin.json"):
            if not manifest_path.exists():
                continue
            manifest = read_json(manifest_path)
            if manifest is not None and manifest.get("version") != version:
                fail(rel(manifest_path), f"version '{manifest.get('version')}' != VERSION '{version}'")

marketplace = read_json(KIT / ".agents/plugins/marketplace.json") if (KIT / ".agents/plugins/marketplace.json").exists() else None
if marketplace is not None:
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins or not isinstance(plugins[0], dict):
        fail(".agents/plugins/marketplace.json", "plugins[0] missing")
    else:
        if plugins[0].get("name") != "ai-kit":
            fail(".agents/plugins/marketplace.json", "plugins[0].name != 'ai-kit'")
        source = plugins[0].get("source") or {}
        if source.get("path") != "./plugins/ai-kit":
            fail(".agents/plugins/marketplace.json", "plugins[0].source.path != './plugins/ai-kit'")

claude_manifest_path = PLUGIN / ".claude-plugin/plugin.json"
claude_manifest = read_json(claude_manifest_path) if claude_manifest_path.exists() else None
if claude_manifest is not None:
    if claude_manifest.get("name") != "ai-kit":
        fail(rel(claude_manifest_path), "name != 'ai-kit'")
    if claude_manifest.get("version") != version:
        fail(rel(claude_manifest_path), f"version '{claude_manifest.get('version')}' != VERSION '{version}'")

claude_marketplace_path = KIT / ".claude-plugin/marketplace.json"
claude_marketplace = read_json(claude_marketplace_path) if claude_marketplace_path.exists() else None
if claude_marketplace is not None:
    entries = claude_marketplace.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
        fail(rel(claude_marketplace_path), "plugins must contain exactly one entry")
    elif claude_manifest is not None:
        entry = entries[0]
        if entry.get("name") != claude_manifest.get("name"):
            fail(rel(claude_marketplace_path), "plugin name differs from Claude plugin manifest")
        if entry.get("source") != "./plugins/ai-kit":
            fail(rel(claude_marketplace_path), "plugin source != './plugins/ai-kit'")
        if entry.get("version") != version:
            fail(rel(claude_marketplace_path), f"plugin version '{entry.get('version')}' != VERSION '{version}'")

for script in sorted((KIT / "platforms").rglob("*.sh")):
    if not os.access(script, os.X_OK):
        fail(rel(script), "script missing the executable bit (chmod +x)")


# --- 2. AGENTS.md ---
agents_md = PLUGIN / "AGENTS.md"
if agents_md.exists():
    agents_lines = len(agents_md.read_text(encoding="utf-8").splitlines())
    if agents_lines > AGENTS_MAX_LINES:
        fail("plugins/ai-kit/AGENTS.md", f"{agents_lines} lines (>{AGENTS_MAX_LINES})")


# --- 3. Subagents and hooks ---
agents_root = PLUGIN / "agents"
agent_names = set()
if agents_root.exists():
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
            agent_names.add(data["name"])

hooks_path = PLUGIN / "hooks/hooks.json"
guard_commands = []
if hooks_path.exists():
    hooks_data = read_json(hooks_path)
    if not isinstance(hooks_data, dict) or set(hooks_data) != {"hooks"}:
        fail(rel(hooks_path), "top level must contain only the 'hooks' key")
    else:
        hook_events = hooks_data.get("hooks")
        if not isinstance(hook_events, dict):
            fail(rel(hooks_path), "hooks must be an object")
            hook_events = {}
        unknown_events = set(hook_events) - {"PreToolUse"}
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
                    if result.returncode != 2 or not isinstance(output, dict) or output.get("decision") != "block":
                        fail(rel(hook_cases_path), f"blocked case not blocked: {case}")
                elif result.returncode != 0 or result.stdout != "":
                    fail(rel(hook_cases_path), f"allowed case not allowed cleanly: {case}")


# --- 4. Skills ---
skills_root = PLUGIN / "skills"
skill_names = set()
skill_descriptions = []
skill_description_text = {}
skill_dirs = set()
if skills_root.exists():
    for directory in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        if not (directory / "SKILL.md").exists():
            fail(rel(directory), "SKILL.md missing")
    for skill_file in sorted(skills_root.rglob("SKILL.md")):
        skill_dir = skill_file.parent
        name = skill_dir.name
        skill_dirs.add(skill_dir)
        counts["skills"] += 1
        if skill_dir.parent != skills_root:
            fail(rel(skill_file), "skill must be flat at skills/<name>/SKILL.md")
        if name in skill_names:
            fail(rel(skill_file), f"duplicate skill name '{name}'")
        skill_names.add(name)
        data, lines = frontmatter(skill_file)
        if data is None:
            fail(rel(skill_file), "missing/invalid frontmatter")
            continue
        if data.get("name") != name:
            fail(rel(skill_file), f"name='{data.get('name')}' != folder '{name}'")
        description = data.get("description")
        if not isinstance(description, str) or not description:
            fail(rel(skill_file), "description missing or empty")
            description = ""
        skill_descriptions.append((name, len(description)))
        skill_description_text[name] = description
        if (skill_dir / "VENDOR.md").exists():
            continue
        validate_schema(skill_file, data, "skill.schema.json")
        if "subagent" in data and "agent" in data:
            fail(rel(skill_file), "skill may not set both 'subagent' and 'agent'")
        agent = data.get("agent")
        if agent is not None and agent not in agent_names:
            fail(rel(skill_file), f"agent '{agent}' has no plugins/ai-kit/agents profile")
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


# --- 5. Rules ---
rules_root = PLUGIN / "rules"
for rule_file in sorted(rules_root.glob("*.md")) if rules_root.exists() else []:
    counts["rules"] += 1
    data, _ = frontmatter(rule_file)
    if data is None:
        fail(rel(rule_file), "missing/invalid frontmatter")
        continue
    validate_schema(rule_file, data, "rule.schema.json")
    trigger = data.get("trigger")
    if trigger == "always_on":
        fail(rel(rule_file), "always-on content lives only in AGENTS.md")
    if trigger == "glob" and not data.get("globs"):
        fail(rel(rule_file), "trigger 'glob' requires 'globs'")
    if trigger != "glob" and "globs" in data:
        fail(rel(rule_file), "'globs' is allowed only with trigger 'glob'")
    if data.get("paths") != data.get("globs"):
        fail(rel(rule_file), "paths must equal globs")
    body_lines = body_line_count(rule_file)
    if body_lines > RULE_BODY_MAX_LINES:
        fail(rel(rule_file), f"body has {body_lines} lines (>{RULE_BODY_MAX_LINES})")


# --- 6. Templates ---
templates_root = PLUGIN / "templates"
templates_index = templates_root / "INDEX.md"
templates_index_text = templates_index.read_text(encoding="utf-8") if templates_index.exists() else ""
SPEC_MAP = {
    "spec-index": "spec.schema.json",
    "spec-feature": "feature.schema.json",
    "spec-requirement-functional": "requirement.schema.json",
    "spec-requirement-non-functional": "requirement.schema.json",
    "spec-decision": "decision.schema.json",
    "spec-debt": "debt.schema.json",
}
for template in sorted(templates_root.glob("*.md")) if templates_root.exists() else []:
    if template.name == "INDEX.md":
        continue
    counts["templates"] += 1
    if not re.match(r"^(spec|doc|project|kit)-[a-z0-9-]+\.md$", template.name):
        fail(rel(template), f"name '{template.name}' does not match ^(spec|doc|project|kit)-[a-z0-9-]+\\.md$")
    if template.name not in templates_index_text:
        fail(rel(template), "not listed in templates/INDEX.md")
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


# --- 7. Indexes ---
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
    return False


for root in (skills_root, templates_root, KIT / "platforms", KIT / "docs", KIT / ".github"):
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

skills_index = skills_root / "INDEX.md"
skills_index_text = skills_index.read_text(encoding="utf-8") if skills_index.exists() else ""
indexed_descriptions = {}
for line in skills_index_text.splitlines():
    match = re.match(r"^\| `([a-z0-9-]+)` \| (.*) \|$", line)
    if match:
        indexed_descriptions[match.group(1)] = match.group(2)
for skill_dir in sorted(skill_dirs):
    name = skill_dir.name
    if name not in indexed_descriptions:
        fail(rel(skills_index), f"skill '{name}' missing from index")
    elif indexed_descriptions[name] != skill_description_text.get(name):
        fail(rel(skills_index), f"skill '{name}' description differs from frontmatter")

plugin_index = PLUGIN / "INDEX.md"
plugin_index_text = plugin_index.read_text(encoding="utf-8") if plugin_index.exists() else ""
for rule_file in sorted(rules_root.glob("*.md")) if rules_root.exists() else []:
    if f"rules/{rule_file.name}" not in plugin_index_text:
        fail(rel(plugin_index), f"rule 'rules/{rule_file.name}' missing from plugin index")
for stray in sorted(rules_root.iterdir()) if rules_root.exists() else []:
    if stray.name in ("INDEX.md", "README.md") or stray.is_dir():
        fail(rel(stray), "rules/ holds rule files only — Devin loads every .md in it as a rule")


# --- 8. Relative links ---
link_re = re.compile(r"\]\(([^)\s#]+)(#[^)]*)?\)")


def vendor_internal(path):
    try:
        relative = path.relative_to(PLUGIN)
    except ValueError:
        return False
    return (len(relative.parts) >= 2 and relative.parts[0] == "skills"
            and (skills_root / relative.parts[1] / "VENDOR.md").exists())


for markdown_file in sorted(KIT.rglob("*.md")):
    if ".git" in markdown_file.parts or vendor_internal(markdown_file):
        continue
    try:
        plugin_relative = markdown_file.relative_to(PLUGIN)
    except ValueError:
        plugin_relative = None
    if (plugin_relative is not None and plugin_relative.parts
            and plugin_relative.parts[0] == "templates" and markdown_file.name.startswith("kit-")):
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
backtick_files = [
    agents_md, KIT / "INDEX.md", KIT / "README.md", plugin_index, templates_root / "INDEX.md",
]
backtick_files += list(rules_root.rglob("*.md"))
backtick_files += list((KIT / "docs").glob("*.md"))
backtick_files += list((KIT / "platforms").rglob("*.md"))
for markdown_file in skills_root.rglob("*.md"):
    if not vendor_internal(markdown_file):
        backtick_files.append(markdown_file)
for markdown_file in sorted(set(path for path in backtick_files if path.exists())):
    if markdown_file.parent == templates_root and markdown_file.name.startswith("kit-"):
        continue
    try:
        markdown_file.relative_to(PLUGIN)
        inside_plugin = True
    except ValueError:
        inside_plugin = False
    for match in backtick_re.finditer(markdown_file.read_text(encoding="utf-8")):
        target = match.group(1)
        if "<" in target:
            continue
        if inside_plugin and re.match(r"^(?:\.\./)+platforms/", target):
            fail(rel(markdown_file), f"path escapes plugin root: {target}")
            continue
        if target.startswith(("platforms/", "plugins/")):
            base = KIT
        elif target.startswith("templates/"):
            base = PLUGIN
        else:
            base = markdown_file.parent
        pattern = str(base / target)
        matches = [Path(path).resolve() for path in glob.glob(pattern)]
        if not matches:
            fail(rel(markdown_file), f"broken backtick path: {target}")
            continue
        if inside_plugin and not target.startswith(("platforms/", "plugins/")):
            for resolved in matches:
                try:
                    resolved.relative_to(PLUGIN.resolve())
                except ValueError:
                    fail(rel(markdown_file), f"path escapes plugin root: {target}")
                    break


# --- 9. Vendor skills lock ---
lock = KIT / "platforms/kits/third-party/skills.lock"
lock_schema = load_schema("skills-lock.schema.json")
if lock.exists():
    for line_number, line in enumerate(lock.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 6:
            fail(rel(lock), f"line {line_number}: expected 6 |-separated fields")
            continue
        obj = dict(zip(["name", "repo", "path", "sha", "license", "verified"], parts))
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
        vendor_file = skills_root / obj["name"] / "VENDOR.md"
        if not vendor_file.exists():
            fail(rel(vendor_file), f"lock skill '{obj['name']}' without VENDOR.md")
        elif f"sha: {obj['sha']}" not in vendor_file.read_text(encoding="utf-8"):
            fail(rel(vendor_file), f"sha diverges from the lock ({obj['sha'][:7]})")


# --- 10. Paragraph duplication ---
duplication_files = []
if agents_md.exists():
    duplication_files.append(agents_md)
for root in (rules_root, skills_root, templates_root):
    if root.exists():
        for markdown_file in root.rglob("*.md"):
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


print(f"check: {'OK' if not failures else 'failed'} ({counts['skills']} skills, "
      f"{counts['rules']} rules, {counts['templates']} templates, "
      f"{counts['indexes']} indexes, {counts['links']} links)")
sys.exit(1 if failures else 0)
