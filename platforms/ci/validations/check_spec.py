#!/usr/bin/env python3
"""Validates docs/spec against the kit schemas.

Usage: check_spec.py [--params | --baseline-init | --baseline-update] [--baseline-against <older.json>]
                     <spec-dir> <schemas-dir>

With pyyaml+jsonschema: full validation. Without them: minimal YAML parser
(frontmatter maps nested by indentation, flow lists and maps) + structural checks (required, enums, id pattern).
spec.md may set `sdd`, the project's process parameters (KIT-067): each key is checked against spec.schema.json in
both modes, and `--params` prints the resolved block (every absent key at its schema default) as JSON.
Also validates docs/spec/progress/*.json (executor progress of FEATs cut before KIT-068) when the folder exists, and
fails on a merge-conflict marker left in any Markdown file under the spec dir.
Decision ids are DEC-nnn unless spec.md declares `decision_kinds` (kind -> id prefix, e.g.
`{tech: TEC, product: PRD}`); then each decision's `kind` must be declared and its id carries that kind's prefix.
NEED-nnn intake records (docs/spec/needs/, top level only: NEED-nnn-data/ folders hold evidence) link forward only:
every listed id must exist with the right kind, a refined or delivered NEED names what it became, and a delivered one
lists only delivered FEATs, or, for a decision NEED with no FEAT, an approved decision. A REQ that no FEAT implements
yet must be listed by an open NEED, not a delivered, rejected, merged, routed or parked one (REQs are written before
the FEAT that delivers them). With `sdd.needs: false` the project keeps no NEED file (rule needs-off) and every REQ
needs a FEAT, the rule before KIT-066: clarify's REQs land in the change that creates their FEAT. The rule reads the
Markdown files at the top of needs/, each one a NEED record, not the folder (#288, intended): an empty needs/ folder,
or one that keeps only NEED-nnn-data/ evidence, passes.

Processes (KIT-090): docs/spec/processes/PROC-nnn-slug.md (top level), checked against process.schema.json: `kind` is
`product` or `tech`. A NEED's `processes` lists existing processes, as its `journeys` lists journeys. Their step tables
are spec_trace.py's. A spec without processes/ is checked as before.

Enablers (KIT-095): docs/spec/enablers/ENB-nnn-slug.md (top level), checked against enabler.schema.json (Backstage's
field names `owner`, `system`, `domain`, `providesApis`, `consumesApis`, `dependsOn`). A FEAT, decision or debt's
`enablers` and an ENB's `dependsOn` name existing ENBs (rule enabler-link); a contract id is provided by one ENB only
and each id in `consumesApis` is provided by another ENB (enabler-contract); a FEAT with `kind: enabler` names at least
one ENB and lists no REQ-F (enabler-kind). The ENB tables and the C18 and C19 tool are spec_trace.py's. A spec without
enablers/ and without `enablers` fields is checked as before.

A FEAT at `validated` or `delivered` carries the History line of the step that moved it (KIT-069, rule
feature-closure), written by spec_trace.py: `sdd-review: validated`, then `sdd-release: delivered` or, under
`release: merge`, `sdd-review: delivered`; a FEAT delivered before that step existed carries `delivered before
sdd-review` instead.

Task rows (KIT-068): a FEAT's `## Tasks` table (header `| ID | Task | ...`, rows `T<n>`). With `sdd.tracker: none` each
cut item is docs/spec/tasks/TASK-nnn-slug.md (task.schema.json); its `feat` and `rows` and the rows' `Item` cell name
each other. On a FEAT that is not validated, delivered or cancelled, the longest chain of own-FEAT `Depends on` ids
(`FEAT-nnn T1, T2` belongs to FEAT-nnn up to the next `;`) is at most `sdd.max_chain`, and a cycle or an own id that
is not a row fails; more rows than `sdd.max_feat_tasks` and a Task cell over 1000 characters only warn.

Every failure carries a rule id (RULES) and its artifact (the id in the file name, else the path under the spec dir).
docs/spec/baseline.json, `{"rules": {rule: {artifact: n}}}`, holds old findings so they neither block nor hide new
ones; n is the number of findings, except for task-chain, where it is the held chain length in rows (a held chain that
grows fails). A held finding prints as BASELINE on stdout, a finding above its n fails, and an n above what is found
fails until --baseline-update lowers it. The file only shrinks: --baseline-init writes it once, --baseline-update never
adds or raises an entry, and --baseline-against fails when the file adds or raises an entry over an older copy (for
example `git show origin/main:docs/spec/baseline.json`; the spec-lint.yml template runs it on every pull request) and
skips when that copy does not exist. sdd-check rows (C<n>, Q<n>) may hold entries too; this script
keeps them and leaves their comparison to `sdd-check all`.
"""
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
    from jsonschema import validate as js_validate, FormatChecker
    FULL = True
except ImportError:
    FULL = False

failures = []  # (rule, artifact key, message); report() prints them once the baseline is applied
SPEC_DIR = None  # set by main(); a finding's key is relative to it

# Rule ids a baseline may hold; each fail() call names one.
RULES = ("frontmatter", "schema", "id-file", "id-duplicate", "decision-kinds", "sdd-params", "conflict-marker",
         "need-link", "need-status", "progress", "link-missing", "link-one-sided", "req-unlisted", "task-file",
         "task-item", "task-chain", "task-cycle", "task-depends", "feature-closure", "needs-off", "enabler-link",
         "enabler-kind", "enabler-contract")
MEASURED = ("task-chain",)  # the baseline holds the longest chain in rows, not a count of findings


def artifact_key(path):
    """A finding's baseline key: the artifact id its file name carries, else its path under the spec dir."""
    path = Path(path)
    m = ID_PREFIX.match(path.stem)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    if SPEC_DIR is not None:
        try:
            return path.relative_to(SPEC_DIR).as_posix()
        except ValueError:
            pass
    return path.as_posix()


def fail(msg, rule, path, measure=1):
    failures.append((rule, artifact_key(path), msg, measure))


def warn(msg, rule):
    print(f"WARN: {msg} [{rule}]", file=sys.stderr)


def report(blocking, held=()):
    for rule, _, msg, *_ in held:
        print(f"BASELINE: {msg} [{rule}]")
    for rule, _, msg, *_ in blocking:
        print(f"FAIL: {msg} [{rule}]", file=sys.stderr)


YAML_TRUE = {"true", "True", "TRUE", "yes", "Yes", "YES", "on", "On", "ON"}
YAML_FALSE = {"false", "False", "FALSE", "no", "No", "NO", "off", "Off", "OFF"}
MINI_KEY = re.compile(r"""^("[^"]*"|'[^']*'|[^\s"'#\-\[\]{},][^:]*?):(?:\s+(.*))?$""")


def mini_scalar(text):
    """A plain or quoted scalar: quoted text, null/~, YAML booleans, integers, else the text itself. Quoted text loses
    only its own pair of quotes, so 'a "b"' keeps the inner quotes, and a single-quoted '' reads as one ' (as in
    pyyaml); an unclosed quote is outside the format."""
    text = text.strip()
    if text[:1] in ("'", '"'):
        if len(text) < 2 or text[-1] != text[0]:
            raise ValueError(f"unclosed quote: {text!r}")
        inner = text[1:-1]
        return inner.replace("''", "'") if text[0] == "'" else inner
    if text in ("null", "Null", "NULL", "~"):
        return None
    if text in YAML_TRUE:
        return True
    if text in YAML_FALSE:
        return False
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def strip_comment(val):
    """Drops a trailing comment as YAML does: from a '#' at the start or after a space, outside quoted text. A quote
    opens quoted text at the value's start or, inside a flow list or map, after '[', '{', ',' or ':'."""
    quote, depth, prev, i = None, 0, "", 0
    while i < len(val):
        ch = val[i]
        if quote:
            if ch == "\\" and quote == '"':
                i += 1
            elif ch == quote and quote == "'" and val[i + 1:i + 2] == "'":
                i += 1
            elif ch == quote:
                quote = None
        elif ch == "#" and (i == 0 or val[i - 1] in " \t"):
            return val[:i].rstrip()
        elif ch in "]}" and depth:
            depth -= 1
        elif prev == "" or (depth and prev in "[{,:"):
            if ch in "'\"":
                quote = ch
            elif ch in "[{":
                depth += 1
        if not quote and ch not in " \t":
            prev = ch
        i += 1
    return val


def _skip_spaces(text, i):
    while i < len(text) and text[i] == " ":
        i += 1
    return i


def _flow_scalar(text, i, stops, convert=True):
    i = _skip_spaces(text, i)
    if i < len(text) and text[i] in ("'", '"'):
        end = text.find(text[i], i + 1)
        if end < 0:
            raise ValueError("unclosed quote")
        return text[i + 1:end], end + 1
    start = i
    while i < len(text) and text[i] not in stops:
        i += 1
    raw = text[start:i].strip()
    return (mini_scalar(raw) if convert else raw), i


def _flow_value(text, i, stops):
    """Parses one flow value ([..], {..} or a scalar) from text[i:]; returns (value, index after it)."""
    i = _skip_spaces(text, i)
    if i < len(text) and text[i] in "[{":
        closing = "]" if text[i] == "[" else "}"
        result = [] if closing == "]" else {}
        i = _skip_spaces(text, i + 1)
        if i < len(text) and text[i] == closing:
            return result, i + 1
        while True:
            if closing == "]":
                item, i = _flow_value(text, i, ",]")
                result.append(item)
            else:
                key, i = _flow_scalar(text, i, ":", convert=False)
                if i >= len(text) or text[i] != ":":
                    raise ValueError("map entry without ':'")
                result[key], i = _flow_value(text, i + 1, ",}")
            i = _skip_spaces(text, i)
            if i < len(text) and text[i] == ",":
                i += 1
            elif i < len(text) and text[i] == closing:
                return result, i + 1
            else:
                raise ValueError(f"expected ',' or {closing!r}")
    return _flow_scalar(text, i, stops)


def mini_value(val, line):
    if (val[0], val[-1]) in (("[", "]"), ("{", "}")):
        try:
            value, end = _flow_value(val, 0, "")
        except ValueError as e:
            raise ValueError(f"map outside the format: {line!r} ({e})")
        if val[end:].strip():
            raise ValueError(f"map outside the format: {line!r}")
        return value
    return mini_scalar(val)


def _mini_list(lines, pos, indent):
    items = []
    while pos < len(lines) and lines[pos][0] == indent and (lines[pos][1] == "-" or lines[pos][1].startswith("- ")):
        item = strip_comment(lines[pos][1][1:].strip())
        items.append(mini_value(item, lines[pos][1]) if item else None)
        pos += 1
    return items, pos


def _mini_map(lines, pos, indent):
    data = {}
    while pos < len(lines) and lines[pos][0] >= indent:
        ind, line = lines[pos]
        m = MINI_KEY.match(line) if ind == indent else None
        if not m:
            raise ValueError(f"line outside the format: {line!r}")
        key, val = m.group(1), strip_comment((m.group(2) or "").strip())
        if key[:1] in ("'", '"'):
            key = key[1:-1]
        pos += 1
        nxt = lines[pos] if pos < len(lines) else None
        if val:
            data[key] = mini_value(val, line)
        elif nxt and nxt[0] >= indent and (nxt[1] == "-" or nxt[1].startswith("- ")):
            data[key], pos = _mini_list(lines, pos, nxt[0])
        elif nxt and nxt[0] > indent:
            data[key], pos = _mini_map(lines, pos, nxt[0])
        else:
            data[key] = None  # an empty value is null, as in pyyaml
    return data, pos


def mini_yaml(text):
    """Minimal parser: 'k: v' maps nested by indentation, '- item' lists, flow [..] and {..} (nested), ints,
    booleans, null (null, Null, NULL, ~ or an empty value) and quoted strings; comment lines, trailing comments and
    blank lines are skipped."""
    lines = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append((len(raw) - len(raw.lstrip(" ")), stripped))
    data, pos = _mini_map(lines, 0, 0)
    if pos < len(lines):
        raise ValueError(f"line outside the format: {lines[pos][1]!r}")
    return data


def frontmatter(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        fail(f"{path}: frontmatter does not start with --- on line 1", "frontmatter", path)
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        fail(f"{path}: frontmatter without closing ---", "frontmatter", path)
        return None
    text = "\n".join(lines[1:end])
    try:
        return load_yaml(text) or {}
    except ValueError as e:
        fail(f"{path}: invalid YAML: {e}" if FULL else f"{path}: invalid frontmatter ({e})", "frontmatter", path)
        return None


def load_yaml(text):
    """YAML text in the subset the kit reads: pyyaml in the full mode, else mini_yaml; a parse error raises ValueError
    in both. platforms/tools/profile.py reads .ai-kit.yaml through it (KIT-087)."""
    if FULL:
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise ValueError(str(e)) from e
    return mini_yaml(text)


# Structural check (fallback without jsonschema): required, enums, id pattern.
STRUCT = {
    "spec": {"req": ["project", "version", "updated"], "enums": {}, "id": None},
    "feature": {"req": ["id", "title", "status", "requirements", "created"],
                "enums": {"status": ["proposed", "clarified", "planned", "in-progress",
                                     "validated", "delivered", "cancelled"],
                          "kind": ["feature", "enabler"]},
                "id": r"^FEAT-\d{3,}$"},
    "requirement": {"req": ["id", "title", "type", "priority", "features", "created"],
                    "enums": {"type": ["functional", "non-functional"],
                              "priority": ["must", "should", "could", "wont"],
                              "status": ["proposed", "approved", "retired"]},
                    "id": r"^REQ-(F|NF)-\d{3,}$"},
    "decision": {"req": ["id", "title", "status", "date"],
                 "enums": {"status": ["proposed", "approved", "rejected", "superseded"]},
                 "id": r"^[A-Z][A-Z0-9]{1,7}-\d{3,}$"},
    "debt": {"req": ["id", "title", "status", "severity", "trigger", "created"],
             "enums": {"status": ["open", "paid", "accepted"],
                       "severity": ["low", "medium", "high", "critical"]},
             "id": r"^DEBT-\d{3,}$"},
    "need": {"req": ["id", "title", "type", "status", "origin", "created"],
             "enums": {"type": ["new", "improvement", "fix", "content", "platform", "decision"],
                       "status": ["proposed", "triaged", "specified", "refined", "delivered",
                                  "rejected", "merged", "routed", "parked"]},
             "id": r"^NEED-\d{3,}$"},
    "task": {"req": ["id", "feat", "rows", "title", "status", "created"],
             "enums": {"status": ["todo", "doing", "blocked", "done", "cancelled"]},
             "id": r"^TASK-\d{3,}$"},
    "process": {"req": ["id", "title", "status", "owner", "kind"],
                "enums": {"status": ["proposed", "approved", "retired"], "kind": ["product", "tech"]},
                "id": r"^PROC-\d{3,}$"},
    "enabler": {"req": ["id", "title", "status", "owner"],
                "enums": {"status": ["proposed", "approved", "retired"]},
                "id": r"^ENB-\d{3,}$"},
}

ID_PREFIX = re.compile(r"^(REQ-NF|REQ-F|[A-Z][A-Z0-9]{1,7})-(\d+)")

# Decision kinds: spec.md may declare `decision_kinds` (kind -> id prefix); without it every decision is DEC-nnn.
DEFAULT_DECISION_PREFIX = "DEC"
DECISION_KIND = re.compile(r"^[a-z][a-z0-9-]*$")
DECISION_PREFIX = re.compile(r"^[A-Z][A-Z0-9]{1,7}$")
RESERVED_PREFIXES = {"FEAT", "REQ", "DEBT", "J", "NEED", "TASK", "PROC", "ENB"}


def decision_kinds(path, data):
    """Returns the {kind: prefix} map spec.md declares, or None when it declares none."""
    if "decision_kinds" not in data:
        return None
    declared = data["decision_kinds"]
    if not isinstance(declared, dict) or not declared:
        fail(f"{path}: decision_kinds must map each decision kind to its id prefix, e.g. {{tech: TEC}}", "decision-kinds", path)
        return {}
    kinds, owners = {}, {}
    for kind, prefix in declared.items():
        kind, prefix = str(kind), str(prefix)
        if not DECISION_KIND.match(kind):
            fail(f"{path}: decision kind {kind!r} does not match {DECISION_KIND.pattern}", "decision-kinds", path)
        if not DECISION_PREFIX.match(prefix) or prefix in RESERVED_PREFIXES:
            fail(f"{path}: decision prefix {prefix!r} must match {DECISION_PREFIX.pattern} "
                 f"and not be one of {sorted(RESERVED_PREFIXES)}", "decision-kinds", path)
        if prefix in owners:
            fail(f"{path}: decision prefix {prefix} is declared for both {owners[prefix]!r} and {kind!r}", "decision-kinds", path)
        owners[prefix] = kind
        kinds[kind] = prefix
    return kinds


def check_decision(path, data, fid, kinds):
    prefix = str(fid).split("-", 1)[0]
    if kinds is None:
        if prefix != DEFAULT_DECISION_PREFIX:
            fail(f"{path}: id {fid}: a decision id is {DEFAULT_DECISION_PREFIX}-nnn unless spec.md declares "
                 f"decision_kinds", "decision-kinds", path)
        return
    kind = data.get("kind")
    if kind is None:
        fail(f"{path}: kind missing; spec.md decision_kinds declares {sorted(kinds)}", "decision-kinds", path)
    elif str(kind) not in kinds:
        fail(f"{path}: kind {kind!r} is not in spec.md decision_kinds {sorted(kinds)}", "decision-kinds", path)
    elif prefix != kinds[str(kind)]:
        fail(f"{path}: id {fid} prefix does not match kind {kind!r} ({kinds[str(kind)]}-nnn)", "decision-kinds", path)

# Project process parameters: spec.md may set `sdd` (KIT-067). spec.schema.json is the single source of its keys,
# values and defaults; the checks below read it in both modes, so a bad value names its key with or without jsonschema.
TYPE_NAMES = {"boolean": "a boolean", "integer": "an integer", "string": "a string", "null": "null",
              "array": "a list", "object": "a map"}


def is_type(value, name):
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    expected = {"boolean": bool, "string": str, "array": list, "object": dict}.get(name)
    return value is None if name == "null" else isinstance(value, expected)


def check_value(path, name, value, rule):
    """Checks one value against the JSON Schema subset the `sdd` block uses; returns False after a failure."""
    types = rule.get("type")
    if types is not None:
        types = types if isinstance(types, list) else [types]
        if not any(is_type(value, t) for t in types):
            fail(f"{path}: {name} must be {' or '.join(TYPE_NAMES[t] for t in types)}, not {value!r}", "sdd-params", path)
            return False
    if "enum" in rule and not any(value == v and type(value) is type(v) for v in rule["enum"]):
        fail(f"{path}: {name} {value!r} is not one of {rule['enum']}", "sdd-params", path)
        return False
    ok = True
    if is_type(value, "integer") and "minimum" in rule and value < rule["minimum"]:
        fail(f"{path}: {name} {value} is below the minimum {rule['minimum']}", "sdd-params", path)
        ok = False
    if is_type(value, "integer") and "maximum" in rule and value > rule["maximum"]:
        fail(f"{path}: {name} {value} is above the maximum {rule['maximum']}", "sdd-params", path)
        ok = False
    if isinstance(value, str):
        if len(value) < rule.get("minLength", 0):
            fail(f"{path}: {name} must not be empty", "sdd-params", path)
            ok = False
        if "pattern" in rule and not re.search(rule["pattern"], value):
            fail(f"{path}: {name} {value!r} does not match {rule['pattern']}", "sdd-params", path)
            ok = False
    if isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            fail(f"{path}: {name} must list at least {rule['minItems']} item", "sdd-params", path)
            ok = False
        seen = [json.dumps(item, sort_keys=True) for item in value]
        if rule.get("uniqueItems") and len(set(seen)) != len(seen):
            fail(f"{path}: {name} lists an item twice", "sdd-params", path)
            ok = False
        for item in value:
            ok = check_value(path, f"{name} item", item, rule.get("items", {})) and ok
        if "const" in rule.get("contains", {}) and rule["contains"]["const"] not in value:
            fail(f"{path}: {name} must include {rule['contains']['const']!r}", "sdd-params", path)
            ok = False
    for sub in rule.get("allOf", []):
        ok = check_value(path, name, value, sub) and ok
    if isinstance(value, dict):
        props, extra = rule.get("properties", {}), rule.get("additionalProperties", True)
        key_pattern = rule.get("propertyNames", {}).get("pattern")
        patterns = rule.get("patternProperties", {})  # the profile's x-<name> keys (KIT-087)
        for key, item in value.items():
            key = str(key)
            matched = [sub for pattern, sub in patterns.items() if re.search(pattern, key)]
            if matched:
                for sub in matched:
                    ok = check_value(path, f"{name}.{key}", item, sub) and ok
            elif key_pattern and not re.search(key_pattern, key):
                fail(f"{path}: {name} key {key!r} does not match {key_pattern}", "sdd-params", path)
                ok = False
            elif key in props:
                ok = check_value(path, f"{name}.{key}", item, props[key]) and ok
            elif extra is False:
                fail(f"{path}: {name}.{key} is not a known key; known: {sorted(props)}", "sdd-params", path)
                ok = False
            elif isinstance(extra, dict):
                ok = check_value(path, f"{name}.{key}", item, extra) and ok
    return ok


def sdd_params(path, data, spec_schema, spec_dir):
    """Checks spec.md's `sdd` block and returns it resolved: every absent key at its schema default; `journeys`
    without a value is on when spec_dir/journeys exists (the behavior before the parameter)."""
    rule = spec_schema.get("properties", {}).get("sdd")
    if rule is None:
        return {}
    if "sdd" in data:
        check_value(path, "sdd", data["sdd"], rule)
    given = data.get("sdd") if isinstance(data.get("sdd"), dict) else {}
    resolved = {}
    for key, prop in rule["properties"].items():
        if key == "journeys":
            default = (spec_dir / "journeys").is_dir()
        elif "properties" in prop:
            default = {sub: subprop.get("default") for sub, subprop in prop["properties"].items()}
        else:
            default = prop.get("default")
        value = given.get(key, default)
        if "properties" in prop and isinstance(value, dict):
            value = {**default, **value}
        resolved[key] = value
    return resolved


def profile_root(spec_dir):
    """The project root whose `.ai-kit.yaml` may describe spec_dir: the folder above it that holds `.git`, else
    `x` for `x/docs/spec`, else None."""
    for folder in [spec_dir, *spec_dir.parents]:
        if (folder / ".git").exists():
            return folder
    return spec_dir.parents[1] if spec_dir.parts[-2:] == ("docs", "spec") else None


def load_params(spec_dir, schemas_dir):
    """The resolved `sdd` section for another kit tool (row_checks.py, spec_trace.py): (params, errors), where errors
    lists each refused key, conflict or unreadable file; nothing is printed and no failure is kept for this run.
    KIT-087 P2b: profile.py resolves it, `.ai-kit.yaml` first, then the legacy `sdd:` block, when the root's profile
    names spec_dir as its spec_root; otherwise, or without profile.py and its schema, the legacy block alone."""
    spec_dir = Path(spec_dir).resolve()
    tool = Path(__file__).resolve().parents[2] / "tools" / "profile.py"
    if tool.is_file() and (schemas_dir / "profile.schema.json").is_file():
        module = profile_module()
        root = profile_root(spec_dir)
        resolved, _, errors = module.resolve(root, ["spec_root", "sdd"], spec_dir=spec_dir, schemas_dir=schemas_dir)
        if root is not None and (root / resolved["spec_root"]).resolve() != spec_dir:
            if errors:  # not this spec's profile, but its errors stay visible: one note, never a failure here
                print(f"profile: note: {module.FILE} describes spec_root {resolved['spec_root']}, not "
                      f"{module.shown(spec_dir, root)}; its errors were not applied: {'; '.join(errors)}",
                      file=sys.stderr)
            resolved, _, errors = module.resolve(None, ["sdd"], spec_dir=spec_dir, schemas_dir=schemas_dir)
        return resolved["sdd"], errors
    start = len(failures)
    index = spec_dir / "spec.md"
    data = frontmatter(index) if index.exists() else {}
    spec_schema = json.loads((schemas_dir / "spec.schema.json").read_text(encoding="utf-8"))
    resolved = sdd_params(index, data if isinstance(data, dict) else {}, spec_schema, spec_dir)
    errors = [msg for _, _, msg, *_ in failures[start:]]
    del failures[start:]
    return resolved, errors


def profile_module():
    """platforms/tools/profile.py (KIT-087), which resolves the project profile with this module's parser and checks.
    This module registers itself as check_spec first, so both share one failure list."""
    sys.modules.setdefault("check_spec", sys.modules[__name__])
    module = sys.modules.get("kit_profile")
    if module is None:
        import importlib.util
        path = Path(__file__).resolve().parents[2] / "tools" / "profile.py"
        spec = importlib.util.spec_from_file_location("kit_profile", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["kit_profile"] = module
        spec.loader.exec_module(module)
    return module


def print_params(spec_dir, schemas_dir):
    """check_spec.py --params: the resolved `sdd` block as JSON on stdout; exit 1 when the block is invalid. It prints
    profile.py's `sdd` section (KIT-087): `.ai-kit.yaml` first when spec_dir is <root>/docs/spec, then the legacy
    `sdd:` block in spec.md. The notes go to stderr as one line (KIT-087 P2a): a legacy project's keys are counted
    and named there, not printed one per line. The output keeps the keys spec.schema.json defines; `profile.py resolve
    --section sdd` also prints the profile-only ones."""
    spec_dir = spec_dir.resolve()
    root = spec_dir.parents[1] if spec_dir.parts[-2:] == ("docs", "spec") else None
    module = profile_module()
    resolved, notes, errors = module.resolve(root, ["sdd"], spec_dir=spec_dir, schemas_dir=schemas_dir)
    if notes:
        print("; ".join(note[len("profile: "):] if n and note.startswith("profile: ") else note
                        for n, note in enumerate(module.summary(notes))), file=sys.stderr)
    if errors:
        for error in errors:
            print(f"FAIL: {error} [sdd-params]", file=sys.stderr)
        sys.exit(1)
    keys = json.loads((schemas_dir / "spec.schema.json").read_text())["properties"]["sdd"]["properties"]
    print(json.dumps({k: v for k, v in resolved["sdd"].items() if k in keys}, indent=2, sort_keys=True))


# Start, base (diff3) and end markers git writes in a conflicted file. A bare "=======" line is not matched:
# it is also a Markdown setext heading underline, and a conflict always carries the start and end markers.
CONFLICT_MARKER = re.compile(r"^(<{7}|\|{7}|>{7})(?: |$)")


def check_conflict_markers(spec_dir):
    """Fails on a merge-conflict marker in any Markdown file under the spec dir (journeys and guides included)."""
    for path in sorted(spec_dir.rglob("*.md")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if CONFLICT_MARKER.match(line):
                fail(f"{path}:{n}: merge-conflict marker {line[:7]!r} left in the file", "conflict-marker", path)


CLOSURE_LINE = re.compile(r"^- \d{4}-\d{2}-\d{2} (sdd-review|sdd-release): (validated|delivered)\b", re.M)
LEGACY_DELIVERED = re.compile(r"^- \d{4}-\d{2}-\d{2} delivered before sdd-review\b", re.M)


def check_feature_closure(path, status):
    """validated is set only by sdd-review, delivered only by sdd-release or by sdd-review under release: merge."""
    if status not in ("validated", "delivered"):
        return
    match = re.search(r"(?ms)^## History[ \t]*$(.*?)(?=^## |\Z)", path.read_text(encoding="utf-8"))
    history = match.group(1) if match else ""
    marks = {m.groups() for m in CLOSURE_LINE.finditer(history)}
    if status == "validated" and ("sdd-review", "validated") not in marks:
        fail(f"{path}: status validated needs the History line sdd-review writes "
             "('- YYYY-MM-DD sdd-review: validated at <sha>'): run spec_trace.py validate", "feature-closure", path)
    if status == "delivered" and not (marks & {("sdd-release", "delivered"), ("sdd-review", "delivered")}
                                      or LEGACY_DELIVERED.search(history)):
        fail(f"{path}: status delivered needs the History line sdd-release writes "
             "('- YYYY-MM-DD sdd-release: delivered in <version>'): run spec_trace.py deliver, or validate under "
             "release: merge", "feature-closure", path)


NEED_LINKS = {"requirements": "requirement", "decisions": "decision", "debts": "debt", "features": "feature",
              "processes": "process"}
NEED_PRODUCT_LINKS = ("requirements", "journeys", "decisions")  # the message names these, as before KIT-090
NEED_PROCESS_LINK = "processes"  # a refined NEED that changed only a process is backed too (KIT-090)
NEED_CLOSED = ("rejected", "merged", "routed", "parked")
NEED_SETTLED = NEED_CLOSED + ("delivered",)  # a NEED in one of these no longer holds a REQ for a future FEAT
JOURNEY_FILE = re.compile(r"^(J-\d{2,})(?:-[a-z0-9-]+)?$")


def as_list(value):
    if isinstance(value, list):
        return value
    return [] if value in (None, "") else [value]


def check_needs(spec_dir: Path, needs: dict, ids: dict, kind_of: dict, feat_status: dict, dec_status: dict) -> None:
    """A NEED links forward only: listed ids exist with the right kind; status refined/delivered is backed by links."""
    journeys = set()
    if (spec_dir / "journeys").is_dir():
        for path in (spec_dir / "journeys").glob("J-*.md"):
            m = JOURNEY_FILE.match(path.stem)
            if m:
                journeys.add(m.group(1))
    for nid, data in needs.items():
        path = ids[nid]
        for field, kind in NEED_LINKS.items():
            for link in as_list(data.get(field)):
                if kind_of.get(str(link)) != kind:
                    fail(f"{path}: {field} lists {link}, which is not an existing {kind}", "need-link", path)
        for link in as_list(data.get("journeys")):
            if str(link) not in journeys:
                fail(f"{path}: journeys lists {link}, which has no file under journeys/", "need-link", path)
        parent = data.get("parent")
        if parent and str(parent) == nid:
            fail(f"{path}: parent is the NEED itself", "need-link", path)
        elif parent and kind_of.get(str(parent)) != "need":
            fail(f"{path}: parent {parent} is not an existing NEED", "need-link", path)
        status = data.get("status")
        if status in ("refined", "delivered") and not any(as_list(data.get(f))
                                                          for f in NEED_PRODUCT_LINKS + (NEED_PROCESS_LINK,)):
            fail(f"{path}: status {status} needs at least one link in {', '.join(NEED_PRODUCT_LINKS)}", "need-status", path)
        if status == "delivered":
            delivered_by = as_list(data.get("features"))
            decided = [d for d in as_list(data.get("decisions")) if dec_status.get(str(d)) == "approved"]
            if not delivered_by and not (data.get("type") == "decision" and decided):
                fail(f"{path}: status delivered needs the features that delivered it "
                     f"(a decision NEED with no FEAT: an approved decision)", "need-status", path)
            for fid in delivered_by:
                if fid in feat_status and feat_status[fid] != "delivered":
                    fail(f"{path}: status delivered, but {fid} is {feat_status[fid]}", "need-status", path)


ENABLER_LINKED = ("feature", "decision", "debt", "enabler")  # the kinds whose frontmatter may name ENBs (KIT-095)


def check_enablers(linked: dict, kind_of: dict) -> None:
    """KIT-095 frontmatter links: `enablers` and `dependsOn` name existing ENBs, a contract id has one provider and
    every consumed id another ENB's, and a FEAT of kind enabler names an ENB and implements no REQ-F."""
    providers = {}
    for eid, (path, kind, data) in sorted(linked.items()):
        if kind != "enabler":
            continue
        for api in map(str, as_list(data.get("providesApis"))):
            if api in providers:
                fail(f"{path}: providesApis lists {api}, which {providers[api]} provides too", "enabler-contract", path)
            else:
                providers[api] = eid
    for lid, (path, kind, data) in sorted(linked.items()):
        field = "dependsOn" if kind == "enabler" else "enablers"
        for link in map(str, as_list(data.get(field))):
            if kind == "enabler" and link == lid:
                fail(f"{path}: dependsOn lists the enabler itself", "enabler-link", path)
            elif kind_of.get(link) != "enabler":
                fail(f"{path}: {field} lists {link}, which is not an existing enabler", "enabler-link", path)
        if kind == "enabler":
            for api in map(str, as_list(data.get("consumesApis"))):
                if providers.get(api, lid) == lid:
                    fail(f"{path}: consumesApis lists {api}, which no other enabler provides", "enabler-contract",
                         path)
        if kind == "feature" and data.get("kind") == "enabler":
            if not as_list(data.get("enablers")):
                fail(f"{path}: kind enabler needs at least one ENB in enablers", "enabler-kind", path)
            functional = [str(r) for r in as_list(data.get("requirements")) if str(r).startswith("REQ-F-")]
            if functional:
                fail(f"{path}: kind enabler implements no REQ-F, but requirements lists {', '.join(functional)}",
                     "enabler-kind", path)


PROGRESS_TASK_KEYS = ("id", "title", "files", "proof", "passes", "notes")


def check_progress_structure(path, data):
    """No-jsonschema fallback: required keys, FEAT id shape, task keys and boolean passes."""
    if not isinstance(data, dict):
        fail(f"{path}: progress must be a JSON object", "progress", path)
        return
    for k in ("feat", "generated", "tasks"):
        if k not in data:
            fail(f"{path}: required field missing: {k}", "progress", path)
    if "feat" in data and not re.match(r"^FEAT-\d{3,}$", str(data["feat"])):
        fail(f"{path}: feat {data['feat']!r} does not match ^FEAT-\\d{{3,}}$", "progress", path)
    tasks = data.get("tasks")
    if "tasks" in data and (not isinstance(tasks, list) or not tasks):
        fail(f"{path}: tasks must be a non-empty list", "progress", path)
    for task in tasks if isinstance(tasks, list) else []:
        if not isinstance(task, dict):
            fail(f"{path}: every task must be an object", "progress", path)
            continue
        for k in PROGRESS_TASK_KEYS:
            if k not in task:
                fail(f"{path}: task {task.get('id', '?')}: required field missing: {k}", "progress", path)
        if "passes" in task and not isinstance(task["passes"], bool):
            fail(f"{path}: task {task.get('id', '?')}: passes must be a boolean", "progress", path)


def check_progress(pdir, schema, feats):
    """Validates every docs/spec/progress/*.json; returns how many files were read."""
    if not pdir.is_dir():
        return 0
    count = 0
    for path in sorted(pdir.glob("*.json")):
        count += 1
        try:
            data = json.loads(path.read_text())
        except ValueError as e:
            fail(f"{path}: invalid JSON: {e}", "progress", path)
            continue
        if schema is not None:
            try:
                js_validate(data, schema, format_checker=FormatChecker())
            except Exception as e:
                fail(f"{path}: schema progress: {getattr(e, 'message', e)}", "progress", path)
        else:
            check_progress_structure(path, data)
        if not isinstance(data, dict) or not isinstance(data.get("feat"), str):
            continue
        if path.stem != data["feat"]:
            fail(f"{path}: feat {data['feat']} != file name", "progress", path)
        if data["feat"] not in feats:
            fail(f"{path}: feat {data['feat']} does not exist in features/", "progress", path)
        seen = set()
        for task in data.get("tasks") if isinstance(data.get("tasks"), list) else []:
            tid = task.get("id") if isinstance(task, dict) else None
            if isinstance(tid, str):
                if tid in seen:
                    fail(f"{path}: duplicate task id {tid}", "progress", path)
                seen.add(tid)
    return count


PIPE = re.compile(r"(?<!\\)\|")
ROW_ID = re.compile(r"^T-?(\d+)$")
TASK_ID = re.compile(r"^TASK-\d{3,}$")
DEP_TOKEN = re.compile(r"\b(FEAT-\d{3,} )?T-?(\d+)\b")
FEAT_HISTORY = ("validated", "delivered", "cancelled")  # spec-first: the task table is frozen history
TASK_CELL_MAX = 1000


def task_table(path):
    """The FEAT's task rows: {row id: {column: cell}} from every table whose header starts `| ID | Task |`."""
    header, rows = None, {}
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text.startswith("|"):
            header = None
            continue
        cells = [cell.strip() for cell in PIPE.split(text)[1:-1]]
        if cells[:2] == ["ID", "Task"]:
            header = cells
        elif header and cells and ROW_ID.match(cells[0]):
            rows[cells[0]] = dict(zip(header, cells))
    return rows


def own_dependencies(cell, fid):
    """Row numbers of the FEAT's own rows a `Depends on` cell names: `FEAT-nnn T1, T2` stays FEAT-nnn up to `;`."""
    found = []
    for group in cell.split(";"):
        current = fid
        for m in DEP_TOKEN.finditer(group):
            current = m.group(1).strip() if m.group(1) else current
            if current == fid:
                found.append(int(m.group(2)))
    return found


def chains(deps):
    """Returns (longest chain of row numbers, first cycle found or None) over {row: [rows it depends on]}."""
    memo, cycles = {}, []

    def walk(n, stack):
        if n in memo:
            return memo[n]
        if n in stack:
            cycles.append(stack[stack.index(n):] + [n])
            return []
        best = []
        for m in deps.get(n, ()):
            if m in deps:
                path = walk(m, stack + [n])
                best = path if len(path) > len(best) else best
        memo[n] = best + [n]
        return memo[n]

    longest = []
    for n in deps:
        path = walk(n, [])
        longest = path if len(path) > len(longest) else longest
    return longest, (cycles[0] if cycles else None)


def positive(value, default):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 1 else default


def check_task_table(fid, path, status, rows, params):
    """An open FEAT's table: longest own Depends on chain and cycles fail; row count and long Task cells warn."""
    if status in FEAT_HISTORY or not rows:
        return
    label = {int(ROW_ID.match(rid).group(1)): rid for rid in rows}
    deps = {int(ROW_ID.match(rid).group(1)): own_dependencies(cells.get("Depends on", ""), fid)
            for rid, cells in rows.items()}
    for n, named in deps.items():
        for missing in sorted(set(named) - set(deps)):
            fail(f"{path}: {label[n]} Depends on T{missing}, which is not a row of the {fid} task table", "task-depends",
                 path)
    longest, cycle = chains(deps)
    if cycle:
        fail(f"{path}: Depends on cycle {' → '.join(label[n] for n in cycle)}", "task-cycle", path)
    max_chain = positive(params.get("max_chain"), 4)
    if len(longest) > max_chain:
        fail(f"{path}: longest Depends on chain is {len(longest)} rows ({' → '.join(label[n] for n in longest)}), "
             f"above sdd.max_chain {max_chain}", "task-chain", path, measure=len(longest))
    max_rows = positive(params.get("max_feat_tasks"), 30)
    if len(rows) > max_rows:
        warn(f"{path}: {len(rows)} task rows, above sdd.max_feat_tasks {max_rows}: sdd-plan splits the NEED into "
             f"several FEATs", "task-size")
    for rid, cells in rows.items():
        size = len(cells.get("Task", ""))
        if size > TASK_CELL_MAX:
            warn(f"{path}: {rid} Task cell has {size} characters, above {TASK_CELL_MAX}: point to the Plan section "
                 f"instead of restating it", "task-cell")


def check_task_items(tasks, tables, ids):
    """TASK-nnn files and the FEAT rows' Item cells name each other (tracker: none)."""
    for tid, data in tasks.items():
        path, fid = ids[tid], str(data.get("feat"))
        if fid not in tables:
            fail(f"{path}: feat {fid} does not exist in features/", "task-file", path)
            continue
        table = tables[fid]["rows"]
        for rid in map(str, as_list(data.get("rows"))):
            if rid not in table:
                fail(f"{path}: row {rid} is not a row of the {fid} task table", "task-file", path)
            elif table[rid].get("Item", "") != tid:
                fail(f"{path}: {fid} {rid} Item is {table[rid].get('Item', '')!r}, not {tid}", "task-item", path)
    for fid, table in tables.items():
        path = table["path"]
        for rid, cells in table["rows"].items():
            item = cells.get("Item", "")
            if not TASK_ID.match(item):
                continue
            if item not in tasks:
                fail(f"{path}: {rid} Item {item} has no file under tasks/", "task-item", path)
            elif str(tasks[item].get("feat")) != fid:
                fail(f"{path}: {rid} Item {item}, but {item} feat is {tasks[item].get('feat')}", "task-item", path)
            elif rid not in map(str, as_list(tasks[item].get("rows"))):
                fail(f"{path}: {rid} Item {item}, but {item} rows does not list {rid}", "task-item", path)


BASELINE = "baseline.json"
CHECK_ROW = re.compile(r"^[CQ]\d+$")  # sdd-check rows; sdd-check all compares them


def read_baseline(path):
    """Returns (file data, {rule: {key: count}}), or (None, {}) without the file; a bad entry fails rule baseline."""
    if not path.exists():
        return None, {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        fail(f"{path}: invalid JSON: {e}", "baseline", path)
        return None, {}
    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, dict):
        fail(f"{path}: must be {{\"rules\": {{rule: {{artifact: count}}}}}}", "baseline", path)
        return None, {}
    held = {}
    for rule, keys in rules.items():
        if rule not in RULES and not CHECK_ROW.match(str(rule)):
            fail(f"{path}: unknown rule {rule!r}; check_spec.py rules are {', '.join(RULES)}, sdd-check rows "
                 f"C<n> and Q<n>", "baseline", path)
            continue
        if not isinstance(keys, dict):
            fail(f"{path}: {rule} must map each artifact to its count", "baseline", path)
            continue
        for key, count in keys.items():
            if not isinstance(count, int) or isinstance(count, bool) or count < 1:
                fail(f"{path}: {rule} {key} must be an integer of at least 1", "baseline", path)
            else:
                held.setdefault(rule, {})[key] = count
    return data, held


def found_counts():
    """{rule: {artifact: n}}: the number of findings, or for a MEASURED rule the largest measure found."""
    counts = {}
    for rule, key, _, measure in failures:
        if rule in RULES:
            keys = counts.setdefault(rule, {})
            keys[key] = max(keys.get(key, 0), measure) if rule in MEASURED else keys.get(key, 0) + 1
    return counts


def write_baseline(path, data, rules):
    data = dict(data or {})
    data["rules"] = {rule: dict(sorted(keys.items())) for rule, keys in sorted(rules.items()) if keys}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def lowered(held, counts):
    """The baseline --baseline-update writes: each of this script's entries at most what is found; never more."""
    rules = {}
    for rule, keys in held.items():
        for key, count in keys.items():
            kept = count if rule not in RULES else min(count, counts.get(rule, {}).get(key, 0))
            if kept:
                rules.setdefault(rule, {})[key] = kept
            if kept != count:
                print(f"baseline: {rule} {key} lowered from {count} to {kept}")
    return rules


def apply_baseline(path, held, counts):
    """Splits the failures into (blocking, held); a count that differs from what is found fails rule baseline."""
    blocking, kept = [], []
    for finding in failures:
        rule, key = finding[0], finding[1]
        allowed = held.get(rule, {}).get(key, 0)
        (kept if allowed and counts[rule][key] <= allowed else blocking).append(finding)
    for rule, keys in held.items():
        if rule not in RULES:
            continue
        for key, allowed in keys.items():
            n = counts.get(rule, {}).get(key, 0)
            if rule in MEASURED:
                holds, found = f"a {allowed}-row {rule}", ("none" if n == 0 else f"{n} rows")
            else:
                holds, found = f"{allowed} {rule} finding{'' if allowed == 1 else 's'}", str(n)
            if n < allowed:
                blocking.append(("baseline", BASELINE, f"{path} holds {holds} for {key}, found {found}: lower it with "
                                 f"check_spec.py --baseline-update", 1))
            elif n > allowed:
                blocking.append(("baseline", BASELINE, f"{path} holds {holds} for {key}, found {found}", 1))
    return blocking, kept


def check_against(path, held, older_path):
    """--baseline-against: the baseline may only shrink, so an entry added or raised over the older copy fails."""
    if not older_path.exists():
        print(f"baseline: no older baseline at {older_path}; nothing to compare")
        return []
    try:
        older = json.loads(older_path.read_text(encoding="utf-8")).get("rules", {})
    except (OSError, ValueError, AttributeError) as e:
        return [("baseline", BASELINE, f"{older_path}: cannot read the older baseline: {e}", 1)]
    findings = []
    for rule, keys in held.items():
        for key, count in keys.items():
            before = older.get(rule, {}).get(key) if isinstance(older.get(rule), dict) else None
            if before is None:
                findings.append(("baseline", BASELINE, f"{path} adds {rule} {key}", 1))
            elif count > before:
                findings.append(("baseline", BASELINE, f"{path} raises {rule} {key} from {before} to {count}", 1))
    return findings


USAGE = ("usage: check_spec.py [--params | --baseline-init | --baseline-update] [--baseline-against <older.json>] "
         "<spec-dir> <schemas-dir>")


def parse_args(argv):
    opts, args, rest = {"against": None}, [], list(argv)
    while rest:
        arg = rest.pop(0)
        if arg in ("--params", "--baseline-init", "--baseline-update"):
            opts[arg] = True
        elif arg == "--baseline-against" and rest:
            opts["against"] = Path(rest.pop(0))
        elif arg.startswith("--"):
            sys.exit(USAGE)
        else:
            args.append(arg)
    modes = [m for m in ("--params", "--baseline-init", "--baseline-update") if opts.get(m)]
    if len(args) != 2 or len(modes) > 1:
        sys.exit(USAGE)
    return opts, Path(args[0]), Path(args[1])


def main():
    global SPEC_DIR
    opts, spec_dir, schemas_dir = parse_args(sys.argv[1:])
    SPEC_DIR = spec_dir
    if not spec_dir.is_dir():
        sys.exit(f"spec dir does not exist: {spec_dir}")
    if not FULL:
        if os.environ.get("CI") == "1":
            sys.exit("FAIL: pyyaml/jsonschema missing (CI=1 requires deps; pip install pyyaml jsonschema)")
        print("WARN: pyyaml/jsonschema missing; spec validation will be structural.", file=sys.stderr)
    if opts.get("--params"):
        print_params(spec_dir, schemas_dir)
        return
    spec_schema = json.loads((schemas_dir / "spec.schema.json").read_text())

    schemas = {}
    for name in STRUCT:
        p = schemas_dir / f"{name}.schema.json"
        if FULL and p.exists():
            schemas[name] = json.loads(p.read_text())
    progress_schema = None
    p = schemas_dir / "progress.schema.json"
    if FULL and p.exists():
        progress_schema = json.loads(p.read_text())

    targets = []  # (path, kind)
    if (spec_dir / "spec.md").exists():
        targets.append((spec_dir / "spec.md", "spec"))
    for sub, kind in [("features", "feature"), ("requirements", "requirement"),
                      ("decisions", "decision"), ("debts", "debt"), ("needs", "need"), ("tasks", "task"),
                      ("processes", "process"), ("enablers", "enabler")]:
        d = spec_dir / sub
        if d.is_dir():
            for f in sorted(d.glob("*.md") if sub in ("needs", "tasks", "processes", "enablers") else d.rglob("*.md")):
                targets.append((f, kind))

    ids, kind_of = {}, {}
    linked = {}  # id -> (path, kind, frontmatter) of each FEAT, decision, debt and ENB (KIT-095)
    feats, reqs, feat_status, dec_status, needs, tasks, tables = {}, {}, {}, {}, {}, {}, {}
    kinds = None  # spec.md is the first target, so its decision_kinds is read before any decision
    params = sdd_params(spec_dir / "spec.md", {}, spec_schema, spec_dir)
    for path, kind in targets:
        data = frontmatter(path)
        if data is None or not isinstance(data, dict):
            continue
        if kind == "spec":
            kinds = decision_kinds(path, data)
            params = sdd_params(path, data, spec_schema, spec_dir)
        if FULL and kind in schemas:
            try:
                js_validate(data, schemas[kind], format_checker=FormatChecker())
            except Exception as e:
                fail(f"{path}: schema {kind}: {getattr(e, 'message', e)}", "schema", path)
        else:
            rule = STRUCT[kind]
            for k in rule["req"]:
                if k not in data:
                    fail(f"{path}: required field missing: {k}", "schema", path)
            for k, allowed in rule["enums"].items():
                if k in data and data[k] not in allowed:
                    fail(f"{path}: {k}={data[k]!r} not in {allowed}", "schema", path)
            if rule["id"] and "id" in data and not re.match(rule["id"], str(data["id"])):
                fail(f"{path}: id {data['id']!r} does not match {rule['id']}", "schema", path)

        fid = data.get("id")
        if fid:
            m = ID_PREFIX.match(path.stem)
            if not m or f"{m.group(1)}-{m.group(2)}" != str(fid):
                fail(f"{path}: id={fid} != file name prefix", "id-file", path)
            if fid in ids:
                fail(f"{path}: duplicate id {fid} (also in {ids[fid]})", "id-duplicate", path)
            ids[fid] = path
            kind_of[str(fid)] = kind
        if kind in ENABLER_LINKED and fid:
            linked[str(fid)] = (path, kind, data)
        if kind == "decision" and fid:
            check_decision(path, data, fid, kinds)
            dec_status[str(fid)] = data.get("status")
        if kind == "feature" and fid:
            feats[fid] = data.get("requirements") or []
            feat_status[fid] = data.get("status")
            check_feature_closure(path, data.get("status"))
            tables[str(fid)] = {"path": path, "rows": task_table(path)}
            check_task_table(str(fid), path, data.get("status"), tables[str(fid)]["rows"], params)
        if kind == "requirement" and fid:
            reqs[fid] = data.get("features") or []
        if kind == "need" and fid:
            needs[fid] = data
        if kind == "task" and fid:
            tasks[str(fid)] = data

    progress_files = check_progress(spec_dir / "progress", progress_schema, feats)
    check_conflict_markers(spec_dir)
    check_needs(spec_dir, needs, ids, kind_of, feat_status, dec_status)
    check_task_items(tasks, tables, ids)
    check_enablers(linked, kind_of)
    needs_off = params.get("needs") is False  # KIT-075: the front chain runs without NEED files
    if needs_off:
        for path, kind in targets:
            if kind == "need":
                fail(f"{path}: sdd.needs is false, so the project keeps no NEED files under needs/ (the request goes "
                     "into the FEAT's Problem section)", "needs-off", path)

    # cross-references FEAT <-> REQ
    for fid, rlist in feats.items():
        for r in rlist:
            if r not in reqs:
                fail(f"{ids[fid]}: requirements lists {r} which does not exist", "link-missing", ids[fid])
    need_reqs = set() if needs_off else {str(r) for data in needs.values() if data.get("status") not in NEED_SETTLED
                                         for r in as_list(data.get("requirements"))}
    settled_reqs = {str(r): nid for nid, data in needs.items() if data.get("status") in NEED_SETTLED
                    for r in as_list(data.get("requirements"))}
    for rid, flist in reqs.items():
        if not flist and needs_off:
            fail(f"{ids[rid]}: {rid} has no FEAT implementing it (sdd.needs: false: a REQ lands in the change that "
                 "creates its FEAT)", "req-unlisted", ids[rid])
        elif not flist and rid not in need_reqs:
            closed = f" ({settled_reqs[rid]} lists it but is closed or delivered)" if rid in settled_reqs else ""
            fail(f"{ids[rid]}: {rid} has no FEAT implementing it and no NEED listing it{closed}", "req-unlisted", ids[rid])
        for f in flist:
            if f not in feats:
                fail(f"{ids[rid]}: features lists {f} which does not exist", "link-missing", ids[rid])
    # both sides agree: a link written on one side only drifts. Together with the check above, every REQ is
    # listed by some FEAT, or by an open NEED until sdd-plan creates the FEAT that delivers it.
    for fid, rlist in feats.items():
        for r in rlist:
            if r in reqs and fid not in reqs[r]:
                fail(f"{ids[fid]}: requirements lists {r}, but {r} features does not list {fid}", "link-one-sided", ids[fid])
    for rid, flist in reqs.items():
        for f in flist:
            if f in feats and rid not in feats[f]:
                fail(f"{ids[rid]}: features lists {f}, but {f} requirements does not list {rid}", "link-one-sided", ids[rid])

    baseline_path = spec_dir / BASELINE
    counts = found_counts()
    if opts.get("--baseline-init"):
        if baseline_path.exists():
            report([("baseline", BASELINE, f"{baseline_path} exists and may only shrink: --baseline-update lowers "
                     f"it", 1)])
            sys.exit(1)
        write_baseline(baseline_path, None, counts)
        print(f"baseline: wrote {sum(map(len, counts.values()))} entries to {baseline_path}")
    data, held = read_baseline(baseline_path)
    if opts.get("--baseline-update") and data is not None:
        held = lowered(held, counts)
        write_baseline(baseline_path, data, held)
    blocking, kept = apply_baseline(baseline_path, held, counts)
    if opts["against"] is not None:
        blocking += check_against(baseline_path, held, opts["against"])
    report(blocking, kept)
    if blocking:
        sys.exit(1)
    held_note = f"; {len(kept)} finding{'' if len(kept) == 1 else 's'} held by {BASELINE}" if kept else ""
    print(f"spec: OK ({len(ids)} artifacts{held_note})")
    if progress_files:
        print(f"progress: OK ({progress_files} files)")


if __name__ == "__main__":
    main()
