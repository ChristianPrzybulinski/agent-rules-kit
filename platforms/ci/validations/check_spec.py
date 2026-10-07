#!/usr/bin/env python3
"""Validates docs/spec against the kit schemas. Usage: check_spec.py <spec-dir> <schemas-dir>

With pyyaml+jsonschema: full validation. Without them: minimal YAML parser
(flat frontmatter) + structural checks (required, enums, id pattern).
Also validates docs/spec/progress/*.json (executor progress) when the folder exists, and fails on a
merge-conflict marker left in any Markdown file under the spec dir.
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


def mini_yaml(text):
    """Minimal parser: 'k: v', 'k: [a,b]', 'k:' + '- item' lines, ints, null, quoted strings."""
    data, key = {}, None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^-\s+(.*)$", line.strip())
        if m and key is not None:
            data.setdefault(key, []).append(m.group(1).strip().strip('"\''))
            continue
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if not m:
            raise ValueError(f"line outside the format: {line!r}")
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            data[key] = []  # may become a list or stay empty
        elif val in ("null", "~"):
            data[key] = None
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            data[key] = [v.strip().strip('"\'') for v in inner.split(",")] if inner else []
        elif val.isdigit():
            data[key] = int(val)
        else:
            data[key] = val.strip('"\'')
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
                              "priority": ["must", "should", "could", "wont"]},
                    "id": r"^REQ-(F|NF)-\d{3,}$"},
    "decision": {"req": ["id", "title", "status", "date"],
                 "enums": {"status": ["proposed", "approved", "rejected", "superseded"]},
                 "id": r"^(DTEC|DGME|DPRO)-\d{3,}$"},
    "debt": {"req": ["id", "title", "status", "severity", "trigger", "created"],
             "enums": {"status": ["open", "paid", "accepted"],
                       "severity": ["low", "medium", "high", "critical"]},
             "id": r"^DEBT-\d{3,}$"},
}

ID_PREFIX = re.compile(r"^(REQ-NF|REQ-F|FEAT|DTEC|DGME|DPRO|DEBT)-(\d+)")

# Start, base (diff3) and end markers git writes in a conflicted file. A bare "=======" line is not matched:
# it is also a Markdown setext heading underline, and a conflict always carries the start and end markers.
CONFLICT_MARKER = re.compile(r"^(<{7}|\|{7}|>{7})(?: |$)")


def check_conflict_markers(spec_dir):
    """Fails on a merge-conflict marker in any Markdown file under the spec dir (journeys and guides included)."""
    for path in sorted(spec_dir.rglob("*.md")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if CONFLICT_MARKER.match(line):
                fail(f"{path}:{n}: merge-conflict marker {line[:7]!r} left in the file")


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
    spec_dir, schemas_dir = Path(sys.argv[1]), Path(sys.argv[2])
    if not spec_dir.is_dir():
        sys.exit(f"spec dir does not exist: {spec_dir}")
    if not FULL:
        if os.environ.get("CI") == "1":
            sys.exit("FAIL: pyyaml/jsonschema missing (CI=1 requires deps; pip install pyyaml jsonschema)")
        print("WARN: pyyaml/jsonschema missing; spec validation will be structural.", file=sys.stderr)

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
                      ("decisions", "decision"), ("debts", "debt")]:
        d = spec_dir / sub
        if d.is_dir():
            for f in sorted(d.rglob("*.md")):
                targets.append((f, kind))

    ids = {}
    feats, reqs = {}, {}
    for path, kind in targets:
        data = frontmatter(path)
        if data is None or not isinstance(data, dict):
            continue
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
        if kind == "decision" and fid:
            expected = {"tech": "DTEC", "game": "DGME", "process": "DPRO"}.get(str(data.get("kind")))
            if expected and not str(fid).startswith(expected + "-"):
                fail(f"{path}: id {fid} prefix does not match kind {data['kind']!r}")
        if kind == "feature" and fid:
            feats[fid] = data.get("requirements") or []
        if kind == "requirement" and fid:
            reqs[fid] = data.get("features") or []

    progress_files = check_progress(spec_dir / "progress", progress_schema, feats)
    check_conflict_markers(spec_dir)

    # cross-references FEAT <-> REQ
    for fid, rlist in feats.items():
        for r in rlist:
            if r not in reqs:
                fail(f"{ids[fid]}: requirements lists {r} which does not exist")
    for rid, flist in reqs.items():
        if not flist:
            fail(f"{ids[rid]}: {rid} has no FEAT implementing it")
        for f in flist:
            if f not in feats:
                fail(f"{ids[rid]}: features lists {f} which does not exist")
    # both sides agree: a link written on one side only drifts. Together with the non-empty features[]
    # above, this also guarantees every REQ is listed by some FEAT.
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
