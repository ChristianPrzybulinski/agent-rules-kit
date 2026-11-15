#!/usr/bin/env python3
"""Validates docs/spec against the kit schemas. Usage: check_spec.py [--params] <spec-dir> <schemas-dir>

With pyyaml+jsonschema: full validation. Without them: minimal YAML parser
(frontmatter maps nested by indentation, flow lists and maps) + structural checks (required, enums, id pattern).
spec.md may set `sdd`, the project's process parameters (KIT-067): each key is checked against spec.schema.json in
both modes, and `--params` prints the resolved block (every absent key at its schema default) as JSON.
Also validates docs/spec/progress/*.json (executor progress) when the folder exists, and fails on a
merge-conflict marker left in any Markdown file under the spec dir.
Decision ids are DEC-nnn unless spec.md declares `decision_kinds` (kind -> id prefix, e.g.
`{tech: TEC, product: PRD}`); then each decision's `kind` must be declared and its id carries that kind's prefix.
NEED-nnn intake records (docs/spec/needs/, top level only: NEED-nnn-data/ folders hold evidence) link forward only:
every listed id must exist with the right kind, a refined or delivered NEED names what it became, and a delivered one
lists only delivered FEATs, or, for a decision NEED with no FEAT, an approved decision. A REQ that no FEAT implements
yet must be listed by an open NEED, not a delivered, rejected, merged, routed or parked one (REQs are written before
the FEAT that delivers them).
A FEAT at `validated` or `delivered` carries the History line of the step that moved it (KIT-069), written by
spec_trace.py: `sdd-review: validated`, then `sdd-release: delivered` or, under `release: merge`, `sdd-review:
delivered`; a FEAT delivered before that step existed carries `delivered before sdd-review` instead.
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

failures = []


def fail(msg):
    failures.append(msg)
    print(f"FAIL: {msg}", file=sys.stderr)


YAML_TRUE = {"true", "True", "TRUE", "yes", "Yes", "YES", "on", "On", "ON"}
YAML_FALSE = {"false", "False", "FALSE", "no", "No", "NO", "off", "Off", "OFF"}
MINI_KEY = re.compile(r"""^("[^"]*"|'[^']*'|[^\s"'#\-\[\]{},][^:]*?):(?:\s+(.*))?$""")


def mini_scalar(text):
    """A plain or quoted scalar: quoted text, null/~, YAML booleans, integers, else the text itself."""
    text = text.strip()
    if text[:1] in ("'", '"'):
        return text.strip("\"'")
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
    """Drops a trailing comment as YAML does: after a quoted value's closing quote, else from a '#' after a space."""
    if val.startswith("#"):
        return ""
    if val[:1] in ("'", '"'):
        end = val.find(val[0], 1)
        rest = val[end + 1:].strip() if end > 0 else ""
        return val[:end + 1] if end > 0 and (not rest or rest.startswith("#")) else val
    return re.sub(r"\s+#.*$", "", val)


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
        fail(f"{path}: frontmatter does not start with --- on line 1")
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        fail(f"{path}: frontmatter without closing ---")
        return None
    text = "\n".join(lines[1:end])
    if FULL:
        try:
            return yaml.safe_load(text) or {}
        except yaml.YAMLError as e:
            fail(f"{path}: invalid YAML: {e}")
            return None
    try:
        return mini_yaml(text)
    except ValueError as e:
        fail(f"{path}: invalid frontmatter ({e})")
        return None


# Structural check (fallback without jsonschema): required, enums, id pattern.
STRUCT = {
    "spec": {"req": ["project", "version", "updated"], "enums": {}, "id": None},
    "feature": {"req": ["id", "title", "status", "requirements", "created"],
                "enums": {"status": ["proposed", "clarified", "planned", "in-progress",
                                     "validated", "delivered", "cancelled"]},
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
}

ID_PREFIX = re.compile(r"^(REQ-NF|REQ-F|[A-Z][A-Z0-9]{1,7})-(\d+)")

# Decision kinds: spec.md may declare `decision_kinds` (kind -> id prefix); without it every decision is DEC-nnn.
DEFAULT_DECISION_PREFIX = "DEC"
DECISION_KIND = re.compile(r"^[a-z][a-z0-9-]*$")
DECISION_PREFIX = re.compile(r"^[A-Z][A-Z0-9]{1,7}$")
RESERVED_PREFIXES = {"FEAT", "REQ", "DEBT", "J", "NEED"}


def decision_kinds(path, data):
    """Returns the {kind: prefix} map spec.md declares, or None when it declares none."""
    if "decision_kinds" not in data:
        return None
    declared = data["decision_kinds"]
    if not isinstance(declared, dict) or not declared:
        fail(f"{path}: decision_kinds must map each decision kind to its id prefix, e.g. {{tech: TEC}}")
        return {}
    kinds, owners = {}, {}
    for kind, prefix in declared.items():
        kind, prefix = str(kind), str(prefix)
        if not DECISION_KIND.match(kind):
            fail(f"{path}: decision kind {kind!r} does not match {DECISION_KIND.pattern}")
        if not DECISION_PREFIX.match(prefix) or prefix in RESERVED_PREFIXES:
            fail(f"{path}: decision prefix {prefix!r} must match {DECISION_PREFIX.pattern} "
                 f"and not be one of {sorted(RESERVED_PREFIXES)}")
        if prefix in owners:
            fail(f"{path}: decision prefix {prefix} is declared for both {owners[prefix]!r} and {kind!r}")
        owners[prefix] = kind
        kinds[kind] = prefix
    return kinds


def check_decision(path, data, fid, kinds):
    prefix = str(fid).split("-", 1)[0]
    if kinds is None:
        if prefix != DEFAULT_DECISION_PREFIX:
            fail(f"{path}: id {fid}: a decision id is {DEFAULT_DECISION_PREFIX}-nnn unless spec.md declares "
                 f"decision_kinds")
        return
    kind = data.get("kind")
    if kind is None:
        fail(f"{path}: kind missing; spec.md decision_kinds declares {sorted(kinds)}")
    elif str(kind) not in kinds:
        fail(f"{path}: kind {kind!r} is not in spec.md decision_kinds {sorted(kinds)}")
    elif prefix != kinds[str(kind)]:
        fail(f"{path}: id {fid} prefix does not match kind {kind!r} ({kinds[str(kind)]}-nnn)")

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
            fail(f"{path}: {name} must be {' or '.join(TYPE_NAMES[t] for t in types)}, not {value!r}")
            return False
    if "enum" in rule and not any(value == v and type(value) is type(v) for v in rule["enum"]):
        fail(f"{path}: {name} {value!r} is not one of {rule['enum']}")
        return False
    ok = True
    if is_type(value, "integer") and "minimum" in rule and value < rule["minimum"]:
        fail(f"{path}: {name} {value} is below the minimum {rule['minimum']}")
        ok = False
    if isinstance(value, str):
        if len(value) < rule.get("minLength", 0):
            fail(f"{path}: {name} must not be empty")
            ok = False
        if "pattern" in rule and not re.search(rule["pattern"], value):
            fail(f"{path}: {name} {value!r} does not match {rule['pattern']}")
            ok = False
    if isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            fail(f"{path}: {name} must list at least {rule['minItems']} item")
            ok = False
        seen = [json.dumps(item, sort_keys=True) for item in value]
        if rule.get("uniqueItems") and len(set(seen)) != len(seen):
            fail(f"{path}: {name} lists an item twice")
            ok = False
        for item in value:
            ok = check_value(path, f"{name} item", item, rule.get("items", {})) and ok
        if "const" in rule.get("contains", {}) and rule["contains"]["const"] not in value:
            fail(f"{path}: {name} must include {rule['contains']['const']!r}")
            ok = False
    for sub in rule.get("allOf", []):
        ok = check_value(path, name, value, sub) and ok
    if isinstance(value, dict):
        props, extra = rule.get("properties", {}), rule.get("additionalProperties", True)
        key_pattern = rule.get("propertyNames", {}).get("pattern")
        for key, item in value.items():
            key = str(key)
            if key_pattern and not re.search(key_pattern, key):
                fail(f"{path}: {name} key {key!r} does not match {key_pattern}")
                ok = False
            elif key in props:
                ok = check_value(path, f"{name}.{key}", item, props[key]) and ok
            elif extra is False:
                fail(f"{path}: {name}.{key} is not a known key; known: {sorted(props)}")
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


def print_params(spec_dir, schemas_dir):
    """check_spec.py --params: the resolved `sdd` block as JSON on stdout; exit 1 when the block is invalid."""
    index = spec_dir / "spec.md"
    data = frontmatter(index) if index.exists() else {}
    spec_schema = json.loads((schemas_dir / "spec.schema.json").read_text())
    resolved = sdd_params(index, data if isinstance(data, dict) else {}, spec_schema, spec_dir)
    if failures or data is None:
        sys.exit(1)
    print(json.dumps(resolved, indent=2, sort_keys=True))


# Start, base (diff3) and end markers git writes in a conflicted file. A bare "=======" line is not matched:
# it is also a Markdown setext heading underline, and a conflict always carries the start and end markers.
CONFLICT_MARKER = re.compile(r"^(<{7}|\|{7}|>{7})(?: |$)")


def check_conflict_markers(spec_dir):
    """Fails on a merge-conflict marker in any Markdown file under the spec dir (journeys and guides included)."""
    for path in sorted(spec_dir.rglob("*.md")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if CONFLICT_MARKER.match(line):
                fail(f"{path}:{n}: merge-conflict marker {line[:7]!r} left in the file")


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
             "('- YYYY-MM-DD sdd-review: validated at <sha>'): run spec_trace.py validate")
    if status == "delivered" and not (marks & {("sdd-release", "delivered"), ("sdd-review", "delivered")}
                                      or LEGACY_DELIVERED.search(history)):
        fail(f"{path}: status delivered needs the History line sdd-release writes "
             "('- YYYY-MM-DD sdd-release: delivered in <version>'): run spec_trace.py deliver, or validate under "
             "release: merge")


NEED_LINKS = {"requirements": "requirement", "decisions": "decision", "debts": "debt", "features": "feature"}
NEED_PRODUCT_LINKS = ("requirements", "journeys", "decisions")
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
                    fail(f"{path}: {field} lists {link}, which is not an existing {kind}")
        for link in as_list(data.get("journeys")):
            if str(link) not in journeys:
                fail(f"{path}: journeys lists {link}, which has no file under journeys/")
        parent = data.get("parent")
        if parent and str(parent) == nid:
            fail(f"{path}: parent is the NEED itself")
        elif parent and kind_of.get(str(parent)) != "need":
            fail(f"{path}: parent {parent} is not an existing NEED")
        status = data.get("status")
        if status in ("refined", "delivered") and not any(as_list(data.get(f)) for f in NEED_PRODUCT_LINKS):
            fail(f"{path}: status {status} needs at least one link in {', '.join(NEED_PRODUCT_LINKS)}")
        if status == "delivered":
            delivered_by = as_list(data.get("features"))
            decided = [d for d in as_list(data.get("decisions")) if dec_status.get(str(d)) == "approved"]
            if not delivered_by and not (data.get("type") == "decision" and decided):
                fail(f"{path}: status delivered needs the features that delivered it "
                     f"(a decision NEED with no FEAT: an approved decision)")
            for fid in delivered_by:
                if fid in feat_status and feat_status[fid] != "delivered":
                    fail(f"{path}: status delivered, but {fid} is {feat_status[fid]}")


PROGRESS_TASK_KEYS = ("id", "title", "files", "proof", "passes", "notes")


def check_progress_structure(path, data):
    """No-jsonschema fallback: required keys, FEAT id shape, task keys and boolean passes."""
    if not isinstance(data, dict):
        fail(f"{path}: progress must be a JSON object")
        return
    for k in ("feat", "generated", "tasks"):
        if k not in data:
            fail(f"{path}: required field missing: {k}")
    if "feat" in data and not re.match(r"^FEAT-\d{3,}$", str(data["feat"])):
        fail(f"{path}: feat {data['feat']!r} does not match ^FEAT-\\d{{3,}}$")
    tasks = data.get("tasks")
    if "tasks" in data and (not isinstance(tasks, list) or not tasks):
        fail(f"{path}: tasks must be a non-empty list")
    for task in tasks if isinstance(tasks, list) else []:
        if not isinstance(task, dict):
            fail(f"{path}: every task must be an object")
            continue
        for k in PROGRESS_TASK_KEYS:
            if k not in task:
                fail(f"{path}: task {task.get('id', '?')}: required field missing: {k}")
        if "passes" in task and not isinstance(task["passes"], bool):
            fail(f"{path}: task {task.get('id', '?')}: passes must be a boolean")


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
            fail(f"{path}: invalid JSON: {e}")
            continue
        if schema is not None:
            try:
                js_validate(data, schema, format_checker=FormatChecker())
            except Exception as e:
                fail(f"{path}: schema progress: {getattr(e, 'message', e)}")
        else:
            check_progress_structure(path, data)
        if not isinstance(data, dict) or not isinstance(data.get("feat"), str):
            continue
        if path.stem != data["feat"]:
            fail(f"{path}: feat {data['feat']} != file name")
        if data["feat"] not in feats:
            fail(f"{path}: feat {data['feat']} does not exist in features/")
        seen = set()
        for task in data.get("tasks") if isinstance(data.get("tasks"), list) else []:
            tid = task.get("id") if isinstance(task, dict) else None
            if isinstance(tid, str):
                if tid in seen:
                    fail(f"{path}: duplicate task id {tid}")
                seen.add(tid)
    return count


def main():
    args = sys.argv[1:]
    params = bool(args) and args[0] == "--params"
    if params:
        args = args[1:]
    if len(args) != 2:
        sys.exit("usage: check_spec.py [--params] <spec-dir> <schemas-dir>")
    spec_dir, schemas_dir = Path(args[0]), Path(args[1])
    if not spec_dir.is_dir():
        sys.exit(f"spec dir does not exist: {spec_dir}")
    if not FULL:
        if os.environ.get("CI") == "1":
            sys.exit("FAIL: pyyaml/jsonschema missing (CI=1 requires deps; pip install pyyaml jsonschema)")
        print("WARN: pyyaml/jsonschema missing; spec validation will be structural.", file=sys.stderr)
    if params:
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
                      ("decisions", "decision"), ("debts", "debt"), ("needs", "need")]:
        d = spec_dir / sub
        if d.is_dir():
            for f in sorted(d.glob("*.md") if sub == "needs" else d.rglob("*.md")):
                targets.append((f, kind))

    ids, kind_of = {}, {}
    feats, reqs, feat_status, dec_status, needs = {}, {}, {}, {}, {}
    kinds = None  # spec.md is the first target, so its decision_kinds is read before any decision
    for path, kind in targets:
        data = frontmatter(path)
        if data is None or not isinstance(data, dict):
            continue
        if kind == "spec":
            kinds = decision_kinds(path, data)
            sdd_params(path, data, spec_schema, spec_dir)
        if FULL and kind in schemas:
            try:
                js_validate(data, schemas[kind], format_checker=FormatChecker())
            except Exception as e:
                fail(f"{path}: schema {kind}: {getattr(e, 'message', e)}")
        else:
            rule = STRUCT[kind]
            for k in rule["req"]:
                if k not in data:
                    fail(f"{path}: required field missing: {k}")
            for k, allowed in rule["enums"].items():
                if k in data and data[k] not in allowed:
                    fail(f"{path}: {k}={data[k]!r} not in {allowed}")
            if rule["id"] and "id" in data and not re.match(rule["id"], str(data["id"])):
                fail(f"{path}: id {data['id']!r} does not match {rule['id']}")

        fid = data.get("id")
        if fid:
            m = ID_PREFIX.match(path.stem)
            if not m or f"{m.group(1)}-{m.group(2)}" != str(fid):
                fail(f"{path}: id={fid} != file name prefix")
            if fid in ids:
                fail(f"{path}: duplicate id {fid} (also in {ids[fid]})")
            ids[fid] = path
            kind_of[str(fid)] = kind
        if kind == "decision" and fid:
            check_decision(path, data, fid, kinds)
            dec_status[str(fid)] = data.get("status")
        if kind == "feature" and fid:
            feats[fid] = data.get("requirements") or []
            feat_status[fid] = data.get("status")
            check_feature_closure(path, data.get("status"))
        if kind == "requirement" and fid:
            reqs[fid] = data.get("features") or []
        if kind == "need" and fid:
            needs[fid] = data

    progress_files = check_progress(spec_dir / "progress", progress_schema, feats)
    check_conflict_markers(spec_dir)
    check_needs(spec_dir, needs, ids, kind_of, feat_status, dec_status)

    # cross-references FEAT <-> REQ
    for fid, rlist in feats.items():
        for r in rlist:
            if r not in reqs:
                fail(f"{ids[fid]}: requirements lists {r} which does not exist")
    need_reqs = {str(r) for data in needs.values() if data.get("status") not in NEED_SETTLED
                 for r in as_list(data.get("requirements"))}
    settled_reqs = {str(r): nid for nid, data in needs.items() if data.get("status") in NEED_SETTLED
                    for r in as_list(data.get("requirements"))}
    for rid, flist in reqs.items():
        if not flist and rid not in need_reqs:
            closed = f" ({settled_reqs[rid]} lists it but is closed or delivered)" if rid in settled_reqs else ""
            fail(f"{ids[rid]}: {rid} has no FEAT implementing it and no NEED listing it{closed}")
        for f in flist:
            if f not in feats:
                fail(f"{ids[rid]}: features lists {f} which does not exist")
    # both sides agree: a link written on one side only drifts. Together with the check above, every REQ is
    # listed by some FEAT, or by an open NEED until sdd-plan creates the FEAT that delivers it.
    for fid, rlist in feats.items():
        for r in rlist:
            if r in reqs and fid not in reqs[r]:
                fail(f"{ids[fid]}: requirements lists {r}, but {r} features does not list {fid}")
    for rid, flist in reqs.items():
        for f in flist:
            if f in feats and rid not in feats[f]:
                fail(f"{ids[rid]}: features lists {f}, but {f} requirements does not list {rid}")

    if failures:
        sys.exit(1)
    print(f"spec: OK ({len(ids)} artifacts)")
    if progress_files:
        print(f"progress: OK ({progress_files} files)")


if __name__ == "__main__":
    main()
