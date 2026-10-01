#!/usr/bin/env python3
"""Kit validator (layout v5). Usage: check_kit.py [--links]

Without pyyaml/jsonschema: structural validation + WARN.
With CI=1 in the environment: missing dependencies are an error.
Each failure prints 'FAIL: <file>: <reason>'; exit 1 on any failure.
"""
import os
import re
import sys
import json
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
SCHEMAS = KIT / "platforms/ci/schemas"
LINKS_MODE = "--links" in sys.argv
CI = os.environ.get("CI") == "1"

failures = []
warnings = []
counts = {"knowledge": 0, "skills": 0, "templates": 0, "indexes": 0, "links": 0}

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
    for i, l in enumerate(lines[1:], start=2):
        if l == "---":
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
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val == "":
                data[key] = []
            elif val.startswith("[") and val.endswith("]"):
                data[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            else:
                data[key] = val.strip("'\"")
    return data


def load_schema(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def validate_schema(path, data, schema_name):
    schema = load_schema(schema_name)
    if FULL:
        try:
            jsonschema.validate(data, schema, format_checker=jsonschema.FormatChecker())
            return True
        except jsonschema.ValidationError as e:
            fail(rel(path), f"schema {schema_name}: {e.message}")
            return False
    # structural: required present + additionalProperties
    ok = True
    for k in schema.get("required", []):
        if k not in data or data[k] in (None, ""):
            fail(rel(path), f"schema {schema_name}: required field '{k}' missing")
            ok = False
    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}))
        for k in data:
            if k not in allowed:
                fail(rel(path), f"schema {schema_name}: field '{k}' not in the schema")
                ok = False
    for k, spec in schema.get("properties", {}).items():
        if k in data and "enum" in spec and data[k] not in spec["enum"]:
            fail(rel(path), f"schema {schema_name}: '{k}'={data[k]!r} not in {spec['enum']}")
            ok = False
        if k in data and "const" in spec and data[k] != spec["const"]:
            fail(rel(path), f"schema {schema_name}: '{k}' != '{spec['const']}'")
            ok = False
        if k in data and "pattern" in spec and isinstance(data[k], str) \
                and not re.match(spec["pattern"], data[k]):
            fail(rel(path), f"schema {schema_name}: '{k}' does not match {spec['pattern']}")
            ok = False
    return ok


# --- 1. Layout ---
REQUIRED_PATHS = [
    "INDEX.md", "VERSION", "LAYOUT_VERSION", "agents/AGENTS.md",
    "agents/knowledge", "agents/skills", "agents/templates", "agents/prompts",
    "platforms/install", "platforms/tools", "platforms/ci/schemas", "platforms/ci/validations",
    "platforms/kits", "docs",
]
FORBIDDEN_ROOT = ["rules", "skills", "schemas", "scripts", "kits", "templates", "processes", "knowledge", "prompts"]
FORBIDDEN_PATHS = ["agents/rules"]  # layout v5: rules became skills
for p in REQUIRED_PATHS:
    if not (KIT / p).exists():
        fail(p, "layout: required path missing")
for p in FORBIDDEN_ROOT:
    if (KIT / p).exists():
        fail(p, "layout: first-level folder forbidden in layout v5")
for p in FORBIDDEN_PATHS:
    if (KIT / p).exists():
        fail(p, "layout: path forbidden in layout v5 (rules are skills now)")
ver = (KIT / "VERSION").read_text().strip() if (KIT / "VERSION").exists() else ""
if ver and not re.match(r"^\d+\.\d+\.\d+$", ver):
    fail("VERSION", f"'{ver}' is not semver")
lv = (KIT / "LAYOUT_VERSION").read_text().strip() if (KIT / "LAYOUT_VERSION").exists() else ""
if lv and not lv.isdigit():
    fail("LAYOUT_VERSION", f"'{lv}' is not an integer")
for sh in sorted((KIT / "platforms").rglob("*.sh")):
    if not os.access(sh, os.X_OK):
        fail(rel(sh), "script missing the executable bit (chmod +x)")

# --- 2. AGENTS.md ---
agents_md = KIT / "agents/AGENTS.md"
if agents_md.exists():
    n = len(agents_md.read_text(encoding="utf-8").splitlines())
    if n > 110:
        fail("agents/AGENTS.md", f"{n} lines (>110)")

# --- 4. Knowledge ---
for f in sorted((KIT / "agents/knowledge").rglob("*.md")):
    if f.name in ("INDEX.md", "README.md"):
        continue
    data, lines = frontmatter(f)
    counts["knowledge"] += 1
    if data is None:
        fail(rel(f), "missing/invalid frontmatter")
        continue
    validate_schema(f, data, "knowledge.schema.json")
    if lines > 40:
        fail(rel(f), f"{lines} lines (>40)")
    for l in f.read_text(encoding="utf-8").splitlines():
        if re.match(r"^-\s*(Must|Never|Always)\b", l):
            warn(rel(f), "normative line ('Must/Never/Always') — normative text is a rule, not knowledge")

# --- 5. Skills ---
SKILL_TYPES = {"core", "quality", "development", "documentation", "process", "tooling", "vendor"}
skill_names = set()
for f in sorted((KIT / "agents/skills").rglob("SKILL.md")):
    name_dir = f.parent.name
    tipo = f.parent.parent.name
    counts["skills"] += 1
    if tipo not in SKILL_TYPES:
        fail(rel(f), f"type '{tipo}' not in {sorted(SKILL_TYPES)}")
    if name_dir in skill_names:
        fail(rel(f), f"duplicate skill name '{name_dir}'")
    skill_names.add(name_dir)
    data, lines = frontmatter(f)
    if data is None:
        fail(rel(f), "missing/invalid frontmatter")
        continue
    if data.get("name") != name_dir:
        fail(rel(f), f"name='{data.get('name')}' != folder '{name_dir}'")
    if tipo == "vendor":
        if "description" not in data:
            fail(rel(f), "vendor without description")
        vend = f.parent / "VENDOR.md"
        if not vend.exists():
            fail(rel(vend), "VENDOR.md missing")
        continue
    validate_schema(f, data, "skill.schema.json")
    if lines > 80:
        fail(rel(f), f"{lines} lines (>80)")
    desc = str(data.get("description", ""))
    if "Use" not in desc:
        fail(rel(f), "description lacks 'Use'")
    if "Do not use" not in desc:
        warn(rel(f), "description lacks 'Do not use'")

# references/ inside own skills: ≤60 lines and linked by name from the SKILL.md
for f in sorted((KIT / "agents/skills").rglob("references/*.md")):
    if "vendor" in f.relative_to(KIT).parts:
        continue
    n = len(f.read_text(encoding="utf-8").splitlines())
    if n > 60:
        fail(rel(f), f"{n} lines (>60)")
    skill_md = f.parent.parent / "SKILL.md"
    if not skill_md.exists() or f.name not in skill_md.read_text(encoding="utf-8"):
        fail(rel(f), f"'{f.name}' not referenced in {rel(skill_md)}")

# --- 6. Templates ---
templates_index = (KIT / "agents/templates/INDEX.md")
index_text = templates_index.read_text(encoding="utf-8") if templates_index.exists() else ""
SPEC_MAP = {"spec-index": "spec.schema.json", "spec-feature": "feature.schema.json",
            "spec-requirement-functional": "requirement.schema.json",
            "spec-requirement-non-functional": "requirement.schema.json",
            "spec-decision": "decision.schema.json", "spec-debt": "debt.schema.json"}
for f in sorted((KIT / "agents/templates").glob("*.md")):
    if f.name == "INDEX.md":
        continue
    counts["templates"] += 1
    if not re.match(r"^(spec|doc|project|kit)-[a-z0-9-]+\.md$", f.name):
        fail(rel(f), f"name '{f.name}' does not match ^(spec|doc|project|kit)-[a-z0-9-]+\\.md$")
    if f.name not in index_text:
        fail(rel(f), "not listed in agents/templates/INDEX.md")
    stem = f.name[:-3]
    if stem in SPEC_MAP:
        data, _ = frontmatter(f)
        if data is None:
            fail(rel(f), "spec-* template without frontmatter")
        else:
            required = set(load_schema(SPEC_MAP[stem]).get("required", []))
            missing = required - set(data.keys())
            if missing:
                fail(rel(f), f"frontmatter missing schema-required fields: {sorted(missing)}")

# --- 7. Indexes ---
def skill_dirs():
    out = set()
    for f in (KIT / "agents/skills").rglob("SKILL.md"):
        out.add(f.parent)
    return out

SKILL_DIRS = skill_dirs()

def exempt_dir(d):
    d = Path(d)
    if d in SKILL_DIRS:
        return True
    for s in SKILL_DIRS:  # internal skill content (including vendor)
        try:
            d.relative_to(s)
            return True
        except ValueError:
            pass
    parts = d.relative_to(KIT).parts
    # domain subfolders in knowledge/ are covered by the parent INDEX
    if len(parts) == 3 and parts[0] == "agents" and parts[1] == "knowledge":
        return True
    # inner subfolders of platforms/kits/<kit>/ (<kit> itself is NOT exempt)
    if len(parts) > 3 and parts[:2] == ("platforms", "kits"):
        return True
    return False

index_dirs = []
for base in ("agents", "platforms", "docs", ".github"):
    b = KIT / base
    if not b.exists():
        continue
    for d in sorted([b] + [p for p in b.rglob("*") if p.is_dir()]):
        if exempt_dir(d):
            continue
        has_i = (d / "INDEX.md").exists()
        has_r = (d / "README.md").exists()
        if has_i and has_r:
            fail(rel(d), "has INDEX.md and README.md (never both)")
            continue
        if not (has_i or has_r):
            fail(rel(d), "no INDEX.md or README.md")
            continue
        counts["indexes"] += 1
        index_dirs.append(d)
        idx_text = (d / ("INDEX.md" if has_i else "README.md")).read_text(encoding="utf-8")
        entries = [p.name for p in d.iterdir()
                   if p.name not in ("INDEX.md", "README.md", ".gitkeep") and not p.name.startswith(".")]
        # for knowledge/, the domain subfolders' files count too
        if d.relative_to(KIT).parts in [("agents", "knowledge")]:
            for sub in d.iterdir():
                if sub.is_dir():
                    entries += [p.name for p in sub.iterdir() if p.suffix == ".md"]
        for e in entries:
            if e not in idx_text:
                fail(rel(d), f"entry '{e}' does not appear in the index")

# root: INDEX.md + README.md are deliberate (README = GitHub convention)
if not (KIT / "INDEX.md").exists() or not (KIT / "README.md").exists():
    fail(".", "root requires INDEX.md and README.md")

# --- 8. Relative links ---
link_re = re.compile(r"\]\(([^)\s#]+)(#[^)]*)?\)")
vendor_internal = lambda p: "vendor" in p.relative_to(KIT).parts[:3] and len(p.relative_to(KIT).parts) > 3 and p.relative_to(KIT).parts[2] == "skills"
for f in sorted(KIT.rglob("*.md")):
    if ".git" in f.parts:
        continue
    rp = f.relative_to(KIT)
    if rp.parts[:2] == ("agents", "skills") and len(rp.parts) > 3 and rp.parts[2] == "vendor":
        continue  # internal vendor content
    if rp.parts[:2] == ("agents", "templates") and f.name.startswith("kit-"):
        continue  # the kit's own skeletons: links are placeholders
    for m in link_re.finditer(f.read_text(encoding="utf-8")):
        target = m.group(1)
        counts["links"] += 1
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("~/"):
            if LINKS_MODE:
                p = Path(target).expanduser()
                if not p.exists():
                    fail(rel(f), f"broken absolute link: {target}")
            continue
        resolved = (f.parent / target).resolve()
        if not resolved.exists():
            fail(rel(f), f"broken link: {target}")

# --- 9. Vendor skills lock ---
lock = KIT / "platforms/kits/third-party/skills.lock"
lock_schema = load_schema("skills-lock.schema.json")
if lock.exists():
    for i, line in enumerate(lock.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 6:
            fail(rel(lock), f"line {i}: expected 6 |-separated fields")
            continue
        obj = dict(zip(["name", "repo", "path", "sha", "license", "verified"], parts))
        if FULL:
            try:
                jsonschema.validate(obj, lock_schema, format_checker=jsonschema.FormatChecker())
            except jsonschema.ValidationError as e:
                fail(rel(lock), f"line {i}: {e.message}")
        else:
            for k in lock_schema["required"]:
                if not obj.get(k):
                    fail(rel(lock), f"line {i}: empty field '{k}'")
            if not re.match(r"^[0-9a-f]{40}$", obj["sha"]):
                fail(rel(lock), f"line {i}: invalid sha")
        vend = KIT / "agents/skills/vendor" / obj["name"] / "VENDOR.md"
        if not vend.exists():
            fail(rel(vend), f"lock skill '{obj['name']}' without VENDOR.md")
        elif f"sha: {obj['sha']}" not in vend.read_text(encoding="utf-8"):
            fail(rel(vend), f"sha diverges from the lock ({obj['sha'][:7]})")

# --- 10. Paragraph duplication in agents/ ---
seen_par = {}
for f in sorted((KIT / "agents").rglob("*.md")):
    rp = f.relative_to(KIT)
    if len(rp.parts) > 3 and rp.parts[1] == "skills" and rp.parts[2] == "vendor":
        continue
    for par in re.split(r"\n\s*\n", f.read_text(encoding="utf-8")):
        par = par.strip()
        if len(par) >= 120:
            if par in seen_par:
                warn(rel(f), f"paragraph duplicated from {seen_par[par]}")
            else:
                seen_par[par] = rel(f)

# --- 11. Compact prompt ---
pc = KIT / "agents/prompts/chatgpt-compact.md"
if pc.exists():
    text = pc.read_text(encoding="utf-8")
    body = text.split("---", 1)[-1] if "---" in text else text
    if len(body) > 1500:
        fail(rel(pc), f"{len(body)} chars (>1500)")

print(f"check: {'OK' if not failures else 'failed'} ({counts['knowledge']} knowledge, "
      f"{counts['skills']} skills, {counts['templates']} templates, {counts['indexes']} indexes, {counts['links']} links)")
sys.exit(1 if failures else 0)
