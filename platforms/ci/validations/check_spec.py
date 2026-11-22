#!/usr/bin/env python3
"""Validates docs/spec against the kit schemas.

Usage: check_spec.py [--params | --baseline-init | --baseline-update] [--baseline-against <older.json>]
                     <spec-dir> <schemas-dir>

With pyyaml+jsonschema: full validation. Without them: minimal YAML parser
(frontmatter maps nested by indentation, flow lists and maps) + structural checks (required, enums, id pattern).
The project's process parameters (KIT-067) are the `sdd` section of its `.ai-kit.yaml`, resolved by the kit's
platforms/tools/profile.py; `--params` prints that section (every absent key at its preset or default) as JSON. Since
KIT-087 P4 an `sdd:` block left in spec.md fails (rule sdd-params): its keys belong in `.ai-kit.yaml`. A profile the
resolver refuses fails `--params` and profile.py, not this run (KIT-100).
Also validates docs/spec/progress/*.json (executor progress of FEATs cut before KIT-068) when the folder exists, and
fails on a merge-conflict marker left in any Markdown file under the spec dir. A record's file is named by its id
alone, `DGME-001.md` and `J-01.md` (rule id-file-name, KIT-103), so an autolink's `<num>` reaches it.
A line that starts with `[DECISION] pending owner` in any Markdown file fails (rule pending-decision, KIT-113): an SDD
step wrote it while an owner question stayed unanswered, and the spec PR must not merge until the owner answers.
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

Processes (KIT-090): docs/spec/processes/PROC-nnn.md (top level), checked against process.schema.json: `kind` is
`product` or `tech`. A NEED's `processes` lists existing processes, as its `journeys` lists journeys. Their step tables
are spec_trace.py's. A spec without processes/ is checked as before. Both tools read processes/PROC-*.md and
enablers/ENB-*.md only (NAMED_FILES, #356): a folder README.md is no record, and another Markdown file there fails
(rule id-file), since neither tool would read it. A spec file that is not UTF-8 is one `frontmatter` failure.

Enablers (KIT-095): docs/spec/enablers/ENB-nnn.md (top level), checked against enabler.schema.json (Backstage's
field names `owner`, `system`, `domain`, `providesApis`, `consumesApis`, `dependsOn`). A FEAT, decision or debt's
`enablers` and an ENB's `dependsOn` name existing ENBs (rule enabler-link); a contract id is provided by one ENB only
and each id in `consumesApis` is provided by another ENB (enabler-contract); a FEAT with `kind: enabler` names at least
one ENB and lists no REQ-F (enabler-kind). The ENB tables and the C18 and C19 tool are spec_trace.py's. A spec without
enablers/ and without `enablers` fields is checked as before.

Versioned FEATs (KIT-096): a FEAT whose body has `## Versions` is one use case with one `### <version>` block per
project version, each with a `Status:` line, a `Scope:` line and its own task rows and `#### Closure`. Every block but
the last is delivered or cancelled, the FEAT's `status` is the last block's, every task row sits in a block and a
block's Scope names only REQs the FEAT lists (rule version-block); each open block's table gets the chain checks below,
and more rows than `sdd.max_feat_tasks` in an open block fail (rule block-tasks, held by baseline.json as the block's
row count, like task-chain). A FEAT's `processes` names existing processes, optionally with a step or a step range
(rule feature-process). A NEED delivered by an earlier block of a FEAT stays valid while its next block is open. A FEAT
without `## Versions` is checked as before: more rows than `sdd.max_feat_tasks` only warn.

A FEAT at `validated` or `delivered` carries the History line of the step that moved it (KIT-069, rule
feature-closure), written by spec_trace.py: `sdd-review: validated`, then `sdd-release: delivered` or, under
`release: merge`, `sdd-review: delivered`; a FEAT delivered before that step existed carries `delivered before
sdd-review` instead.

FEAT-only flow (KIT-100): the project profile's `sdd.flow` and `sdd.id_prefix.feature` (read through load_params, so
`.ai-kit.yaml` and the kind preset count; `tooling` sets `feat-only`). A FEAT id is `<prefix>-nnn` (default `FEAT`).
Under `feat-only` a FEAT needs no `requirements`, may name its `issue` and `pr` (`#N` or `OWNER/NAME#N`, or empty), and
is delivered by its merged PR: the History line `- YYYY-MM-DD pr: delivered (<repo>#N merged)` that spec_trace.py
sync-status writes. The full flow with the FEAT prefix checks a FEAT exactly as before.

Task rows (KIT-068): a FEAT's `## Tasks` table (header `| ID | Task | ...`, rows `T<n>`). With `sdd.tracker: none` each
cut item is docs/spec/tasks/TASK-nnn.md (task.schema.json); its `feat` and `rows` and the rows' `Item` cell name
each other. On a FEAT that is not validated, delivered or cancelled, the longest chain of own-FEAT `Depends on` ids
(`FEAT-nnn T1, T2` belongs to FEAT-nnn up to the next `;`) is at most `sdd.max_chain`, and a cycle or an own id that
is not a row fails; more rows than `sdd.max_feat_tasks` and a Task cell over 1000 characters only warn. A `cancelled` row (a re-cut's
history, `sdd-tasks` § 5) answers a `Depends on` but counts toward no limit and joins no chain (#431); a live row
that depends on a cancelled row warns.

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
RULES = ("frontmatter", "schema", "id-file", "id-file-name", "id-duplicate", "decision-kinds", "sdd-params",
         "conflict-marker", "need-link", "need-status", "progress", "link-missing", "link-one-sided", "req-unlisted",
         "task-file", "task-item", "task-chain", "task-cycle", "task-depends", "feature-closure", "needs-off",
         "enabler-link", "enabler-kind", "enabler-contract", "version-block", "block-tasks", "feature-process",
         "pending-decision")
UNBASELINED = ("pending-decision",)  # a RULES id no baseline may hold: it would hide an open owner question (KIT-113)
MEASURED = ("task-chain", "block-tasks")  # the baseline holds the longest chain in rows, not a count of findings


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


NAMED_FILES = {"processes": "PROC-*.md", "enablers": "ENB-*.md"}  # #356: the files both tools read in these folders


def named_files(spec_dir, sub):
    """The record files of processes/ or enablers/ (top level), as check_spec.py and spec_trace.py both read them; a
    folder README.md is no record."""
    folder = Path(spec_dir) / sub
    return sorted(folder.glob(NAMED_FILES[sub])) if folder.is_dir() else []


UNREADABLE = set()  # the paths read_spec_text failed, each once


def read_spec_text(path):
    """A spec file's text, or None after one `not UTF-8` or `unreadable` failure for it (#356: never a traceback)."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        if path not in UNREADABLE:
            UNREADABLE.add(path)
            why = f"not UTF-8 ({e.reason} at byte {e.start})" if isinstance(e, UnicodeDecodeError) else \
                f"unreadable ({e.strerror or e})"
            fail(f"{path}: {why}", "frontmatter", path)
        return None


def frontmatter(path):
    text = read_spec_text(path)
    if text is None:
        return None
    lines = text.splitlines()
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

# Value checks for the project profile (KIT-087): profile.py checks each `.ai-kit.yaml` key against
# profile.schema.json with these, so a bad value names its key with or without jsonschema.
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


def profile_root(spec_dir):
    """The project root whose `.ai-kit.yaml` may describe spec_dir: the folder above it that holds `.git`, else
    `x` for `x/docs/spec`, else None."""
    for folder in [spec_dir, *spec_dir.parents]:
        if (folder / ".git").exists():
            return folder
    return spec_dir.parents[1] if spec_dir.parts[-2:] == ("docs", "spec") else None


def load_sections(spec_dir, schemas_dir, sections):
    """The resolved profile sections for spec_dir's project (KIT-087): (sections, errors), where errors lists each
    refused key or unreadable file; nothing is printed and no failure is kept for this run. profile.py resolves them
    from the root's `.ai-kit.yaml` when it names spec_dir as its spec_root, else every key takes its default; without
    profile.py or its schema each section is {} and one error says so."""
    spec_dir = Path(spec_dir).resolve()
    tool = Path(__file__).resolve().parents[2] / "tools" / "profile.py"
    if not (tool.is_file() and (schemas_dir / "profile.schema.json").is_file()):
        return {name: {} for name in sections}, [f"no {tool} or {schemas_dir / 'profile.schema.json'}: the profile "
                                                 f"sections {', '.join(sections)} take the tools' own defaults"]
    module = profile_module()
    root = profile_root(spec_dir)
    resolved, _, errors = module.resolve(root, ["spec_root", *sections], spec_dir=spec_dir, schemas_dir=schemas_dir)
    if root is not None and (root / resolved["spec_root"]).resolve() != spec_dir:
        if errors:  # not this spec's profile, but its errors stay visible: one note, never a failure here
            print(f"profile: note: {module.FILE} describes spec_root {resolved['spec_root']}, not "
                  f"{module.shown(spec_dir, root)}; its errors were not applied: {'; '.join(errors)}",
                  file=sys.stderr)
        resolved, _, errors = module.resolve(None, list(sections), spec_dir=spec_dir, schemas_dir=schemas_dir)
    return {name: resolved[name] if isinstance(resolved.get(name), dict) else {} for name in sections}, errors


def load_params(spec_dir, schemas_dir):
    """The resolved `sdd` section for another kit tool (row_checks.py, spec_trace.py): (params, errors), as
    load_sections reads it."""
    sections, errors = load_sections(spec_dir, schemas_dir, ["sdd"])
    return sections["sdd"], errors


def load_release(spec_dir, schemas_dir):
    """The resolved `release` section (KIT-096: spec_trace.py reads `versioning` for the version block names); {}
    without profile.py or its schema. A refused profile shows in profile.py resolve and in the tools that read
    `sdd`."""
    return load_sections(spec_dir, schemas_dir, ["release"])[0]["release"]


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
    """check_spec.py --params: the project profile's resolved `sdd` section (KIT-087) as JSON on stdout; exit 1 when
    the profile is refused. The resolver's notes go to stderr as one line."""
    spec_dir = spec_dir.resolve()
    module = profile_module()
    resolved, notes, errors = module.resolve(profile_root(spec_dir), ["sdd"], spec_dir=spec_dir,
                                             schemas_dir=schemas_dir)
    if notes:
        print("; ".join(note[len("profile: "):] if n and note.startswith("profile: ") else note
                        for n, note in enumerate(notes)), file=sys.stderr)
    if errors:
        for error in errors:
            print(f"FAIL: {error} [sdd-params]", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(resolved["sdd"], indent=2, sort_keys=True))


# Start, base (diff3) and end markers git writes in a conflicted file. A bare "=======" line is not matched:
# it is also a Markdown setext heading underline, and a conflict always carries the start and end markers.
CONFLICT_MARKER = re.compile(r"^(<{7}|\|{7}|>{7})(?: |$)")


def check_conflict_markers(spec_dir):
    """Fails on a merge-conflict marker in any Markdown file under the spec dir (journeys and guides included)."""
    for path in sorted(spec_dir.rglob("*.md")):
        for n, line in enumerate((read_spec_text(path) or "").splitlines(), 1):
            if CONFLICT_MARKER.match(line):
                fail(f"{path}:{n}: merge-conflict marker {line[:7]!r} left in the file", "conflict-marker", path)


# KIT-113: the line an SDD step writes when an owner question stayed unanswered and the chain went on with the marked
# recommendation (`[DECISION] pending owner: <option> (asked YYYY-MM-DD HH:MM UTC)`). It starts a line, after at most
# list, quote, numbering, checkbox, heading, table-cell or bold markers, in any case and with any spacing, so a spec that
# quotes the marker in running text or in code does not fail. A paragraph may wrap the opening itself (`[DECISION]
# pending` / `owner:`): the match reads the line and the next PENDING_WRAP lines of its paragraph (up to a blank line,
# each stripped of its indentation and quote marks) as one text, whose whitespace includes the line break; a break
# after `owner` already leaves the first line matching. The owner's answer rewrites the line to
# `[DECISION] <option>, chosen by the owner on YYYY-MM-DD` (sdd-clarify 2, sdd-plan 5), which this does not match; a
# line that keeps `pending owner` in any wording still fails. `[ \t]`, not `\s`, before the marker, so a line of
# markers alone never starts a match that its next line, which starts it too, would report a second time.
PENDING_DECISION = re.compile(
    r"^(?:[ \t]|[-*+>|#_]|\d+[.)]|\[[ xX]\])*\[DECISION\](?:\*\*|__)?\s+pending\s+owner\b", re.I)
PENDING_WRAP = 2  # the opening has three words, so it breaks over at most two line ends


def pending_decision_at(lines, i):
    """True when lines[i] starts the pending marker, alone or wrapped over the next lines of its paragraph."""
    text = lines[i]
    if PENDING_DECISION.match(text):
        return True
    if "[DECISION]" not in text.upper() or not text.strip():
        return False
    for nxt in lines[i + 1:i + 1 + PENDING_WRAP]:
        if not nxt.strip():
            break
        text += "\n" + nxt.lstrip(" \t>")
        if PENDING_DECISION.match(text):
            return True
    return False


def check_pending_decisions(spec_dir):
    """Fails on a `[DECISION] pending owner` line in any Markdown file under the spec dir: the owner has not answered,
    so the spec PR must not merge (KIT-113). The finding names the line the marker starts on."""
    for path in sorted(spec_dir.rglob("*.md")):
        lines = (read_spec_text(path) or "").splitlines()
        for i in range(len(lines)):
            if pending_decision_at(lines, i):
                fail(f"{path}:{i + 1}: [DECISION] pending owner: the owner has not answered; resolve it before the "
                     "merge", "pending-decision", path)


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



# FEAT-only flow (KIT-100). The full flow's FEAT rule stays the one STRUCT holds; apply_flow derives this run's.
FEAT_ONLY = "feat-only"
FEATURE_STRUCT = STRUCT["feature"]
ITEM_REF = r"^(([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#[0-9]+)?$"  # a FEAT's issue or pr: #N, OWNER/NAME#N, or empty
PR_DELIVERED = re.compile(r"^- \d{4}-\d{2}-\d{2} pr: delivered\b", re.M)


def flow_params(spec_dir, schemas_dir):
    """(sdd.flow, sdd.id_prefix.feature) from the profile's resolved sdd section; a refused key is profile.py's
    finding, never one of this run, and leaves its default."""
    start = len(failures)
    try:
        params, _ = load_params(spec_dir, schemas_dir)
    finally:
        del failures[start:]
    prefix = (params.get("id_prefix") or {}).get("feature")
    return (params.get("flow") or "full"), (prefix if isinstance(prefix, str) and prefix else "FEAT")


def apply_flow(schemas, flow, prefix):
    """Sets this run's FEAT rules and returns the flow: the id prefix, and under feat-only an optional `requirements`
    and the `issue` and `pr` fields. The full flow with the FEAT prefix keeps the schema and STRUCT unchanged."""
    STRUCT["feature"] = FEATURE_STRUCT
    if flow != FEAT_ONLY and prefix == "FEAT":
        return flow
    rule = dict(FEATURE_STRUCT, id=rf"^{re.escape(prefix)}-\d{{3,}}$")
    if flow == FEAT_ONLY:
        rule["req"] = [key for key in FEATURE_STRUCT["req"] if key != "requirements"]
    STRUCT["feature"] = rule
    if "feature" in schemas:
        schema = json.loads(json.dumps(schemas["feature"]))
        pattern = f"^{re.escape(prefix)}-[0-9]{{3,}}$"
        schema["properties"]["id"]["pattern"] = pattern
        schema["properties"]["depends_on"]["items"]["pattern"] = pattern
        if flow == FEAT_ONLY:
            schema["required"] = rule["req"]
            for key in ("issue", "pr"):
                schema["properties"][key] = {"type": ["string", "null"], "pattern": ITEM_REF}
        schemas["feature"] = schema
    return flow


def check_closure(path, status, flow):
    """check_feature_closure, except that a feat-only FEAT is also delivered by its merged PR's History line."""
    if flow == FEAT_ONLY and status == "delivered":
        match = re.search(r"(?ms)^## History[ \t]*$(.*?)(?=^## |\Z)", path.read_text(encoding="utf-8"))
        if match and PR_DELIVERED.search(match.group(1)):
            return
    check_feature_closure(path, status)

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


def check_needs(spec_dir: Path, needs: dict, ids: dict, kind_of: dict, feat_status: dict, dec_status: dict,
                versions: dict = None, feat_reqs: dict = None) -> None:
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
                if fid in feat_status and not feat_delivered_for(data, feat_status[fid], (feat_reqs or {}).get(fid),
                                                                 (versions or {}).get(fid)):
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
ROW_CANCELLED = ("cancelled", "superseded")  # superseded is the legacy word (row_checks.py LEGACY)


def task_table(path):
    """The FEAT's task rows: {row id: {column: cell}} from every table whose header starts `| ID | Task |`; a table
    inside an HTML comment is not read (KIT-096), while a comment inside a row's cell stays part of it."""
    header, rows = None, {}
    original = path.read_text(encoding="utf-8")
    lines, blanked = original.splitlines(), blank_comments(original).splitlines()
    for line, seen in zip(lines, blanked) if len(lines) == len(blanked) else zip(blanked, blanked):
        text = line.strip() if seen.strip() else ""
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


def live_rows(rows: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """The rows that are neither `cancelled` nor legacy `superseded`: a re-cut keeps its merged rows as history
    (`sdd-tasks` § 5), and they count toward no row limit and no chain; they still answer a `Depends on`."""
    return {rid: cells for rid, cells in rows.items() if cells.get("Status", "").strip() not in ROW_CANCELLED}


def warn_cancelled_dependencies(fid: str, path: Path, live: dict[str, dict[str, str]],
                                rows: dict[str, dict[str, str]]) -> None:
    """A live dependent must point to the merged row, including across version blocks."""
    cancelled = {int(ROW_ID.match(rid).group(1)) for rid in rows.keys() - live_rows(rows).keys()}
    for rid, cells in live.items():
        for n in sorted(set(own_dependencies(cells.get("Depends on", ""), fid)) & cancelled):
            warn(f"{path}: {rid} Depends on T{n}, which is cancelled: sdd-tasks § 5 moves the dependent to the "
                 "merged row", "task-depends-cancelled")


def check_task_table(fid, path, status, rows, params):
    """An open FEAT's table: longest own Depends on chain and cycles fail; row count and long Task cells warn.
    Cancelled rows answer a Depends on but join no chain and no count."""
    if status in FEAT_HISTORY or not rows:
        return
    label = {int(ROW_ID.match(rid).group(1)): rid for rid in rows}
    every = {int(ROW_ID.match(rid).group(1)): own_dependencies(cells.get("Depends on", ""), fid)
             for rid, cells in rows.items()}
    for n, named in every.items():
        for missing in sorted(set(named) - set(every)):
            fail(f"{path}: {label[n]} Depends on T{missing}, which is not a row of the {fid} task table", "task-depends",
                 path)
    live = live_rows(rows)
    warn_cancelled_dependencies(fid, path, live, rows)
    alive = {int(ROW_ID.match(rid).group(1)) for rid in live}
    deps = {n: [m for m in named if m in alive] for n, named in every.items() if n in alive}
    longest, cycle = chains(deps)
    if cycle:
        fail(f"{path}: Depends on cycle {' → '.join(label[n] for n in cycle)}", "task-cycle", path)
    max_chain = positive(params.get("max_chain"), 4)
    if len(longest) > max_chain:
        fail(f"{path}: longest Depends on chain is {len(longest)} rows ({' → '.join(label[n] for n in longest)}), "
             f"above sdd.max_chain {max_chain}", "task-chain", path, measure=len(longest))
    max_rows = positive(params.get("max_feat_tasks"), 30)
    if len(live) > max_rows:
        warn(f"{path}: {len(live)} task rows, above sdd.max_feat_tasks {max_rows}: sdd-plan § 2 cuts its sets, then "
             f"splits the NEED or opens the next version block", "task-size")
    for rid, cells in live.items():
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


VERSIONS_HEADING = re.compile(r"^## Versions[ \t]*$")
BLOCK_HEADING = re.compile(r"^### (.+?)[ \t]*$")
BLOCK_LINE = re.compile(r"^(Status|Scope):[ \t]*(.*?)[ \t]*$")
BLOCK_ROW = re.compile(r"^\|\s*(T-?\d+)\s*\|")
BLOCK_STATUSES = ("proposed", "planned", "in-progress", "validated", "delivered", "cancelled")
BLOCK_SETTLED = ("delivered", "cancelled")  # what every block but the last one is
REQ_REF = re.compile(r"\bREQ-(?:F|NF)-\d{3,}\b")
FEAT_PROCESS = re.compile(r"^(PROC-\d{3,})(?: ([SA]\d+)(?:\s*[–-]\s*([SA]\d+))?)?$")  # a FEAT `processes` item


def blank_comments(text):
    """text with every HTML comment blanked to its newlines, so line numbers stay."""
    return re.sub(r"(?s)<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text)


TASKS_HEADING = re.compile(r"^##\s+Tasks\s*$")
SECTION_HEADING = re.compile(r"^##\s+(.+?)\s*$")


def task_sections(text):
    """A FEAT's task-table sections for every tool that reads its rows (row_checks.py; KIT-096): a list of (version
    block name or None, line index of the section's first line, section text), [] without one. A FEAT without
    `## Versions` gives its `## Tasks` section, stripped, as pr_gates.sections reads it (the index is the heading's
    plus 2, the position row_checks.py has always reported); a versioned FEAT gives each block's `#### Tasks`
    subsection in file order, HTML comments blanked, so the last one is the open block's and the others answer a
    `Depends on`."""
    blocks = version_blocks(text)
    if blocks is not None:
        out = []
        for block in blocks:
            if block["tasks"] is None:
                continue
            body = [pair for pair in block["tasks"] if pair[1].strip()]
            if not body:
                out.append((block["name"], block["line"], ""))
                continue
            lines = block["tasks"][block["tasks"].index(body[0]):block["tasks"].index(body[-1]) + 1]
            out.append((block["name"], body[0][0], "\n".join(line for _, line in lines)))
        return out
    lines = re.split(r"\r\n|\r|\n", text)
    start = next((n for n, line in enumerate(lines) if TASKS_HEADING.match(line)), None)
    if start is None:
        return []
    body = []
    for line in lines[start + 1:]:
        if SECTION_HEADING.match(line):
            break
        body.append(line)
    return [(None, start + 2, "\n".join(body).strip())]


def version_blocks(text):
    """KIT-096: the `### <version>` blocks under a FEAT's `## Versions`, in file order; None without that section.
    Each is {"name", "line" (0-based, in text), "status", "status_line", "scope", "rows", "closure", "text", "tasks"}:
    its `Status:` and `Scope:` lines, the task row ids its tables hold, whether its `#### Closure` holds a line, its
    text, and the (line index, line) pairs of its `#### Tasks` subsection (None without one). HTML comments are
    blanked first, keeping the line count."""
    lines = blank_comments(text).split("\n")
    start = next((n for n, line in enumerate(lines) if VERSIONS_HEADING.match(line)), None)
    if start is None:
        return None
    blocks, sub = [], None
    for n in range(start + 1, len(lines)):
        line = lines[n]
        if line.startswith("## "):
            break
        heading = BLOCK_HEADING.match(line)
        if heading:
            blocks.append({"name": heading.group(1), "line": n, "status": None, "status_line": None, "scope": "",
                           "rows": [], "closure": False, "text": "", "tasks": None})
            sub = None
            continue
        if not blocks:
            continue
        block = blocks[-1]
        block["text"] += line + "\n"
        if line.startswith("#### "):
            sub = line[5:].strip()
            if sub == "Tasks" and block["tasks"] is None:
                block["tasks"] = []
            continue
        if sub == "Tasks" and isinstance(block["tasks"], list):
            block["tasks"].append((n, line))
        field = BLOCK_LINE.match(line)
        if field and sub is None and field.group(1) == "Status" and block["status_line"] is None:
            block["status"], block["status_line"] = field.group(2), n
        elif field and sub is None and field.group(1) == "Scope":
            block["scope"] = field.group(2)
        row = BLOCK_ROW.match(line.strip())
        if row:
            block["rows"].append(row.group(1))
        if sub == "Closure" and line.strip():
            block["closure"] = True
    return blocks


def check_versions(fid, path, data, rows, params):
    """KIT-096: a FEAT with `## Versions` is one use case with one block per project version. Every block has a
    `Status:`, every one but the last is delivered or cancelled, the FEAT's status is the last block's, every task row
    sits in a block and a block's Scope names only REQs the FEAT lists (rule version-block). Each open block's rows
    are checked as an open FEAT's table, and above sdd.max_feat_tasks they fail (rule block-tasks). Returns the
    blocks, or None for a FEAT without `## Versions`, whose table check_task_table reads as before."""
    blocks = version_blocks(path.read_text(encoding="utf-8"))
    if blocks is None:
        return None
    if not blocks:
        fail(f"{path}: ## Versions holds no `### <version>` block", "version-block", path)
        return blocks
    inside = {rid for block in blocks for rid in block["rows"]}
    for rid in rows:
        if rid not in inside:
            fail(f"{path}: {rid} is outside every version block: a versioned FEAT keeps its task rows in the block of "
                 "its version", "version-block", path)
    listed, names = set(map(str, as_list(data.get("requirements")))), set()
    scoped = {rid for block in blocks for rid in REQ_REF.findall(block["scope"])}
    for rid in sorted(listed - scoped):
        fail(f"{path}: {fid} requirements lists {rid}, which no version block's Scope names: each REQ the use case "
             "implements enters through the Scope of the block that delivers it", "version-block", path)
    for n, block in enumerate(blocks):
        label = f"{fid} {block['name']}"
        if block["name"] in names:
            fail(f"{path}: two version blocks are named {block['name']}", "version-block", path)
        names.add(block["name"])
        if block["status"] not in BLOCK_STATUSES:
            fail(f"{path}: {label} needs a `Status:` line with one of {', '.join(BLOCK_STATUSES)}", "version-block",
                 path)
        elif n < len(blocks) - 1 and block["status"] not in BLOCK_SETTLED:
            fail(f"{path}: {label} is {block['status']}, but only the last version block is open: an earlier block is "
                 "delivered or cancelled", "version-block", path)
        for rid in REQ_REF.findall(block["scope"]):
            if rid not in listed:
                fail(f"{path}: {label} Scope names {rid}, which the FEAT's requirements do not list", "version-block",
                     path)
        if block["status"] not in FEAT_HISTORY:
            check_block_rows(fid, path, label, {rid: rows[rid] for rid in block["rows"] if rid in rows}, rows, params)
    last = blocks[-1]["status"]
    if last in BLOCK_STATUSES and data.get("status") != last:
        fail(f"{path}: status {data.get('status')}, but its last version block {blocks[-1]['name']} is {last}: the "
             "FEAT's status is its open block's", "version-block", path)
    return blocks


def check_block_rows(fid, path, label, rows, every_row, params):
    """An open version block's rows: the check_task_table rules over the block, where a Depends on an earlier block's
    row is satisfied and stays off the chain, and more rows than sdd.max_feat_tasks fail (KIT-096). A cancelled row
    answers a Depends on but joins no chain and no count (#431)."""
    every_rows, rows = rows, live_rows(rows)
    warn_cancelled_dependencies(fid, path, rows, every_row)
    label_of = {int(ROW_ID.match(rid).group(1)): rid for rid in rows}
    known = {int(ROW_ID.match(rid).group(1)) for rid in every_row}
    deps = {}
    for rid, cells in every_rows.items():
        n = int(ROW_ID.match(rid).group(1))
        named = own_dependencies(cells.get("Depends on", ""), fid)
        for missing in sorted(set(named) - known):
            fail(f"{path}: {rid} Depends on T{missing}, which is not a row of the {fid} task table", "task-depends",
                 path)
        if rid in rows:
            deps[n] = [m for m in named if m in label_of]
    longest, cycle = chains(deps)
    if cycle:
        fail(f"{path}: {label}: Depends on cycle {' → '.join(label_of[n] for n in cycle)}", "task-cycle", path)
    max_chain = positive(params.get("max_chain"), 4)
    if len(longest) > max_chain:
        fail(f"{path}: {label}: longest Depends on chain is {len(longest)} rows "
             f"({' → '.join(label_of[n] for n in longest)}), above sdd.max_chain {max_chain}", "task-chain", path,
             measure=len(longest))
    max_rows = positive(params.get("max_feat_tasks"), 30)
    if len(rows) > max_rows:
        fail(f"{path}: {label} has {len(rows)} task rows, above sdd.max_feat_tasks {max_rows}: the rest goes to the "
             "next version block", "block-tasks", path, measure=len(rows))
    for rid, cells in rows.items():
        size = len(cells.get("Task", ""))
        if size > TASK_CELL_MAX:
            warn(f"{path}: {rid} Task cell has {size} characters, above {TASK_CELL_MAX}: point to the Plan section "
                 f"instead of restating it", "task-cell")


def feat_delivered_for(need, status, requirements, blocks):
    """The one rule both tools apply (check_spec.py need-status, spec_trace.py deliver_needs and the `—` waiting rule;
    KIT-096): a FEAT has delivered its part of a NEED when its status is delivered, or, for a versioned FEAT (blocks
    from version_blocks), when the NEED's REQs that the FEAT lists are not empty and all sit in the Scope of a
    delivered block. So the NEED an earlier block delivered stays valid while the next block is open, and a versioned
    FEAT whose delivered blocks hold none of the NEED's REQs has delivered nothing for it."""
    if status == "delivered" or not blocks:
        return status == "delivered"
    share = {str(r) for r in as_list(need.get("requirements"))} & {str(r) for r in requirements or []}
    done = {r for b in blocks if b["status"] == "delivered" for r in REQ_REF.findall(b["scope"])}
    return bool(share) and share <= done


def check_feature_processes(linked, kind_of):
    """A FEAT's `processes` (KIT-096): each item is PROC-nnn, optionally with one step or a range of steps, and names
    an existing process; spec_trace.py checks the steps."""
    for fid, (path, kind, data) in sorted(linked.items()):
        if kind != "feature":
            continue
        for item in map(str, as_list(data.get("processes"))):
            m = FEAT_PROCESS.match(item)
            if not m:
                fail(f"{path}: processes lists {item!r}: write PROC-nnn, PROC-nnn S<a>–S<b>, PROC-nnn S<n> or "
                     "PROC-nnn A<n>", "feature-process", path)
            elif kind_of.get(m.group(1)) != "process":
                fail(f"{path}: processes lists {item}, which names no existing process", "feature-process", path)


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
        if rule in UNBASELINED:
            fail(f"{path}: {rule} may not be held: a baseline would hide an open owner question; resolve the line "
                 f"instead", "baseline", path)
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

    schemas = {}
    for name in STRUCT:
        p = schemas_dir / f"{name}.schema.json"
        if FULL and p.exists():
            schemas[name] = json.loads(p.read_text())
    progress_schema = None
    p = schemas_dir / "progress.schema.json"
    if FULL and p.exists():
        progress_schema = json.loads(p.read_text())
    flow = apply_flow(schemas, *flow_params(spec_dir, schemas_dir))  # KIT-100

    targets = []  # (path, kind)
    if (spec_dir / "spec.md").exists():
        targets.append((spec_dir / "spec.md", "spec"))
    for sub, kind in [("features", "feature"), ("requirements", "requirement"),
                      ("decisions", "decision"), ("debts", "debt"), ("needs", "need"), ("tasks", "task"),
                      ("processes", "process"), ("enablers", "enabler")]:
        d = spec_dir / sub
        if d.is_dir() and sub in NAMED_FILES:
            files = named_files(spec_dir, sub)
            for f in sorted(set(d.glob("*.md")) - set(files)):
                if f.name != "README.md":
                    fail(f"{f}: not read: {sub}/ holds {NAMED_FILES[sub]} files only", "id-file", f)
            targets += [(f, kind) for f in files]
        elif d.is_dir():
            for f in sorted(d.glob("*.md") if sub in ("needs", "tasks") else d.rglob("*.md")):
                targets.append((f, kind))
    if (spec_dir / "journeys").is_dir():  # KIT-103: this script reads journeys by name only (need-link)
        for f in sorted((spec_dir / "journeys").glob("J-*.md")):
            if not re.fullmatch(r"J-\d{2,}", f.stem):  # `J-` and digits alone, any other stem fails
                m = re.match(r"J-\d{2,}", f.stem)
                why = f"the file name carries a slug; rename to {m.group(0)}.md" if m else "the file name is not J-NN.md"
                fail(f"{f}: {why}", "id-file-name", f)

    ids, kind_of = {}, {}
    linked = {}  # id -> (path, kind, frontmatter) of each FEAT, decision, debt and ENB (KIT-095)
    feats, reqs, feat_status, dec_status, needs, tasks, tables = {}, {}, {}, {}, {}, {}, {}
    retired_reqs = set()
    versions = {}  # FEAT id -> its version blocks, None without `## Versions` (KIT-096)
    kinds = None  # spec.md is the first target, so its decision_kinds is read before any decision
    start = len(failures)
    params, _ = load_params(spec_dir, schemas_dir)  # a refused key is profile.py's finding (and --params'), never
    del failures[start:]                            # one of this run (KIT-100): its key keeps its default here
    for path, kind in targets:
        data = frontmatter(path)
        if data is None or not isinstance(data, dict):
            continue
        if kind == "spec":
            kinds = decision_kinds(path, data)
            if "sdd" in data:  # KIT-087 P4: the legacy home is no longer read
                fail(f"{path}: the sdd: block is no longer read (KIT-087 P4); move its keys under sdd: in the "
                     f"project's .ai-kit.yaml (review_rounds as review.rounds, visual_approval as "
                     f"evidence.visual_approval) and delete the block", "sdd-params", path)
                data = {key: value for key, value in data.items() if key != "sdd"}
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
            elif path.stem != str(fid):  # KIT-103: the id alone, so an autolink's `<num>` reaches the file
                fail(f"{path}: the file name carries a slug; rename to {fid}.md", "id-file-name", path)
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
            check_closure(path, data.get("status"), flow)
            tables[str(fid)] = {"path": path, "rows": task_table(path)}
            versions[str(fid)] = check_versions(str(fid), path, data, tables[str(fid)]["rows"], params)
            if versions[str(fid)] is None:
                check_task_table(str(fid), path, data.get("status"), tables[str(fid)]["rows"], params)
        if kind == "requirement" and fid:
            reqs[fid] = data.get("features") or []
            if data.get("status") == "retired":
                retired_reqs.add(str(fid))
        if kind == "need" and fid:
            needs[fid] = data
        if kind == "task" and fid:
            tasks[str(fid)] = data

    progress_files = check_progress(spec_dir / "progress", progress_schema, feats)
    check_conflict_markers(spec_dir)
    check_pending_decisions(spec_dir)
    check_needs(spec_dir, needs, ids, kind_of, feat_status, dec_status, versions, feats)
    check_task_items(tasks, tables, ids)
    check_enablers(linked, kind_of)
    check_feature_processes(linked, kind_of)
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
        if not flist and rid in retired_reqs:
            pass  # KIT-108: a retired REQ is a rule no FEAT delivers any more; its History line names why
        elif not flist and needs_off:
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
        left_out = sum(sum(counts.pop(rule, {}).values()) for rule in UNBASELINED)
        write_baseline(baseline_path, None, counts)
        print(f"baseline: wrote {sum(map(len, counts.values()))} entries to {baseline_path}")
        if left_out:
            print(f"baseline: left out {left_out} pending-decision finding{'' if left_out == 1 else 's'}: a baseline "
                  f"never holds one; resolve the line, it still fails")
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
