#!/usr/bin/env python3
"""Journey traceability for a project's spec directory (journeys <-> FEAT <-> REQ <-> tests).

  spec_trace.py check SPEC             fail on a broken journey link, a FEAT<->REQ asymmetry or a
                                       stale SPEC/traceability.md
  spec_trace.py generate SPEC          rewrite SPEC/traceability.md from the FEAT, REQ and journey files
  spec_trace.py impact SPEC BASE HEAD  markdown: the journey steps and tests a BASE...HEAD diff touches
  spec_trace.py mark-done SPEC FEAT-NNN Tn [--pr REPO#N]
                                       set the task row's Status to `done` and append a History line
  spec_trace.py status SPEC [--write]  derive each FEAT's status from its task rows; fail on a mismatch,
                                       or with --write rewrite `status` and `updated`

Options (before the command): `--repo NAME` (repeatable) adds a clone name a `Proven by` test path may
be rooted at, and `--date` fixes the date written by mark-done/status --write (default: today).

Journeys live in <spec>/journeys/J-NN.md. Every markdown table whose first header cell is `Step` is a
step table. Row ids: `S<n>` main path, `A<n>` alternative path (column `At` names its main step),
`P<n>` prerequisite. Cells: `Rules` holds REQ ids only, `Implemented by` holds `FEAT-nnn Tn` refs only,
`Proven by` holds test refs — `FEAT-nnn Tn` test tasks, backticked paths rooted at a clone name, and an
optional trailing `manual: <check>`.

A test path's first segment names the clone it lives in: the spec's own repository (its directory name)
or a directory beside it — clones sit side by side on the machine that writes journeys — plus any
`--repo` names for clones CI does not check out. A path rooted at the spec's own repository must match
a file in it; other roots are format-checked only until the project's journey CI runs them.

Run it after the frontmatter lint (`check_spec.py`), which this file is synced next to by
platforms/tools/sync-project.sh. Upstreamed from a consumer project's tools/spec-trace implementation;
the generated matrix text is byte-stable on purpose so a synced copy and a project-owned copy compare
equal.
"""
from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml

MATRIX = "traceability.md"

REQ_ID = re.compile(r"REQ-(?:F|NF)-\d{3,}")
TASK_REF = re.compile(r"FEAT-\d{3,} T\d+")
TASK_ROW = re.compile(r"^\| (T\d+) \|")
JOURNEY_FILE = re.compile(r"^(J-\d{2,})(?:-[a-z0-9-]+)?$")
JOURNEY_ID = re.compile(r"^J-\d{2,}$")
STEP_ID = re.compile(r"^[SAP]\d+$")
TEST_PATH = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*)/\S+$")
BACKTICKED = re.compile(r"`([^`]+)`")
MANUAL = re.compile(r"manual:\s*(.+)$")
SEPARATORS = re.compile(r"<br>|[\s,·;—]+")
PR_REF = re.compile(r"^[\w.-]+#\d+$")
UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")
STATUS_FROZEN = ("validated", "cancelled")
JOURNEY_STATUS = ("proposed", "approved", "retired")
JOURNEY_FIELDS = ("id", "title", "status", "owner", "created", "updated")
MAIN_COLUMNS = ("Rules", "Implemented by", "Proven by")


@dataclass
class Step:
    journey: str
    id: str
    at: str | None = None
    rules: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    manual: str | None = None

    @property
    def ref(self):
        return f"{self.journey} {self.id}"


@dataclass
class Spec:
    root: Path        # the clone the spec lives in
    spec_dir: Path    # the spec directory itself (<root>/docs/spec in the usual layout)
    repos: set        # valid test-path roots: own clone name + sibling clones + --repo extras
    feats: dict = field(default_factory=dict)     # FEAT id -> {"path", "requirements", "tasks": {Tn: row}}
    reqs: dict = field(default_factory=dict)      # REQ id -> {"path", "features", "title"}
    journeys: dict = field(default_factory=dict)  # J id -> {"path", "title", "status", "steps"}
    errors: list = field(default_factory=list)

    @property
    def steps(self):
        return [s for j in self.journeys.values() for s in j["steps"]]


def natural_key(text):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


def split_frontmatter(text):
    """Return (frontmatter dict, body) or (None, text) when the file has no closed frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        return None, text
    end = lines.index("---", 1)
    return yaml.safe_load("\n".join(lines[1:end])) or {}, "\n".join(lines[end + 1:])


def task_rows(body):
    rows = {}
    for line in body.splitlines():
        m = TASK_ROW.match(line)
        if m:
            rows[m.group(1)] = line
    return rows


def row_cells(line):
    return [cell.strip() for cell in UNESCAPED_PIPE.split(line.strip())[1:-1]]


def status_column(body):
    """Return the index of the `Status` cell of the task table, or None when it has none."""
    for line in body.splitlines():
        if line.startswith("| ID |"):
            header = row_cells(line)
            if "Status" in header:
                return header.index("Status")
    return None


def task_statuses(body):
    column = status_column(body)
    if column is None:
        return {}
    return {tid: cells[column] for tid, line in task_rows(body).items()
            if len(cells := row_cells(line)) > column}


def repo_root(spec_dir: Path) -> Path:
    """The clone the spec lives in: git's toplevel, else `x/docs/spec` -> `x`, else the spec's parent."""
    shown = subprocess.run(["git", "-C", str(spec_dir), "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
    if shown.returncode == 0:
        return Path(shown.stdout.strip())
    if spec_dir.parent.name == "docs":
        return spec_dir.parent.parent
    return spec_dir.parent


def test_roots(root: Path, extra: Iterable[str]) -> set:
    """The names a `Proven by` path may be rooted at: this clone's directory name, every directory
    beside it (clones sit side by side on the machine that writes journeys) and the --repo extras."""
    roots = {root.name, *extra}
    try:
        roots |= {p.name for p in root.parent.iterdir() if p.is_dir() and not p.name.startswith(".")}
    except OSError:
        pass
    return roots


def load(spec_dir: Path, extra_repos: Iterable[str] = ()) -> Spec:
    spec_dir = spec_dir.resolve()
    root = repo_root(spec_dir)
    spec = Spec(root=root, spec_dir=spec_dir, repos=test_roots(root, extra_repos))
    for path in sorted((spec_dir / "features").glob("FEAT-*.md")):
        data, body = split_frontmatter(path.read_text(encoding="utf-8"))
        if data and data.get("id"):
            spec.feats[data["id"]] = {"path": path, "requirements": data.get("requirements") or [],
                                      "tasks": task_rows(body), "status": data.get("status"),
                                      "task_status": task_statuses(body)}
    for path in sorted((spec_dir / "requirements").rglob("REQ-*.md")):
        data, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        if data and data.get("id"):
            spec.reqs[data["id"]] = {"path": path, "features": data.get("features") or [],
                                     "title": data.get("title", "")}
    for path in sorted((spec_dir / "journeys").glob("J-*.md"), key=lambda p: natural_key(p.name)):
        load_journey(spec, path)
    return spec


def load_journey(spec, path):
    where = path.relative_to(spec.root)
    data, body = split_frontmatter(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        spec.errors.append(f"{where}: frontmatter missing, not closed by --- or not a mapping")
        return
    for key in JOURNEY_FIELDS:
        if key not in data:
            spec.errors.append(f"{where}: required field missing: {key}")
    jid = str(data.get("id", ""))
    name = JOURNEY_FILE.match(path.stem)
    if not JOURNEY_ID.match(jid):
        spec.errors.append(f"{where}: id {jid!r} does not match J-NN")
        return
    if not name or name.group(1) != jid:
        spec.errors.append(f"{where}: id={jid} != file name prefix")
    if data.get("status") not in JOURNEY_STATUS:
        spec.errors.append(f"{where}: status={data.get('status')!r} not in {list(JOURNEY_STATUS)}")
    if jid in spec.journeys:
        spec.errors.append(f"{where}: duplicate id {jid}")
        return
    steps = parse_steps(spec, jid, body)
    spec.journeys[jid] = {"path": path, "title": data.get("title", ""), "status": data.get("status"),
                          "steps": steps}


def markdown_tables(body):
    """Yield (header cells, rows of cells) for every markdown table in body."""
    block = []
    for line in body.splitlines() + [""]:
        if line.startswith("|"):
            block.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        elif block:
            if len(block) >= 2:
                yield block[0], block[2:]
            block = []


def parse_steps(spec, jid, body):
    steps, seen = [], set()
    for header, rows in markdown_tables(body):
        if not header or header[0] != "Step":
            continue
        for cells in rows:
            row = dict(zip(header, cells))
            step = parse_step(spec, jid, row, header)
            if step is None:
                continue
            if step.id in seen:
                spec.errors.append(f"{jid} {step.id}: duplicate step id")
            seen.add(step.id)
            steps.append(step)
    main_ids = {s.id for s in steps if s.id.startswith("S")}
    for step in steps:
        if step.id.startswith("A") and step.at not in main_ids:
            spec.errors.append(f"{step.ref}: At={step.at!r} is not a main step (S<n>) of {jid}")
    if not main_ids:
        spec.errors.append(f"{jid}: no main step (S<n>) found in a Step table")
    return steps


def parse_step(spec, jid, row, header):
    sid = row.get("Step", "")
    if not STEP_ID.match(sid):
        spec.errors.append(f"{jid}: step id {sid!r} does not match S<n>, A<n> or P<n>")
        return None
    step = Step(journey=jid, id=sid, at=row.get("At") or None)
    if "Implemented by" not in header:
        spec.errors.append(f"{step.ref}: table has no 'Implemented by' column")
        return step
    step.tasks = only_ids(spec, step, "Implemented by", row["Implemented by"], TASK_REF)
    if not step.tasks:
        spec.errors.append(f"{step.ref}: Implemented by cites no task (FEAT-nnn Tn)")
    check_tasks(spec, step, step.tasks)
    if sid.startswith("P"):
        return step
    missing = [c for c in MAIN_COLUMNS if c not in header]
    if missing:
        spec.errors.append(f"{step.ref}: table lacks column(s) {missing}")
        return step
    step.rules = only_ids(spec, step, "Rules", row["Rules"], REQ_ID)
    for rid in step.rules:
        if rid not in spec.reqs:
            spec.errors.append(f"{step.ref}: Rules cites {rid}, which does not exist")
    parse_tests(spec, step, row["Proven by"])
    return step


def only_ids(spec, step, column, cell, pattern):
    """Return the ids in cell; anything else in it is an error (journeys cite ids, never values)."""
    ids = pattern.findall(cell)
    rest = SEPARATORS.sub("", pattern.sub("", cell))
    if rest:
        spec.errors.append(f"{step.ref}: {column} holds more than ids: {cell!r}")
    return ids


def check_tasks(spec, step, refs):
    for ref in refs:
        fid, tid = ref.split(" ")
        if fid not in spec.feats:
            spec.errors.append(f"{step.ref}: {ref} names {fid}, which does not exist")
        elif tid not in spec.feats[fid]["tasks"]:
            spec.errors.append(f"{step.ref}: {ref} is not a row of the {fid} task table")


def parse_tests(spec, step, cell):
    manual = MANUAL.search(cell)
    if manual:
        step.manual = manual.group(1).strip()
        cell = cell[:manual.start()]
    paths = BACKTICKED.findall(cell)
    cell = BACKTICKED.sub("", cell)
    tasks = TASK_REF.findall(cell)
    rest = SEPARATORS.sub("", TASK_REF.sub("", cell))
    if rest:
        spec.errors.append(f"{step.ref}: Proven by holds text outside test refs and a trailing manual: {rest!r}")
    check_tasks(spec, step, tasks)
    for path in paths:
        m = TEST_PATH.match(path)
        if not m or m.group(1) not in spec.repos:
            spec.errors.append(f"{step.ref}: test path {path!r} is not rooted at a clone name "
                               f"({', '.join(sorted(spec.repos))}, or a --repo extra)")
        elif m.group(1) == spec.root.name and not any(spec.root.glob(path[len(m.group(1)) + 1:])):
            spec.errors.append(f"{step.ref}: test path {path!r} matches no file in this repository")
    step.tests = tasks + [f"`{p}`" for p in paths]
    if not step.tests and not step.manual:
        spec.errors.append(f"{step.ref}: Proven by cites no test")


def symmetry_errors(spec):
    errors = []
    for fid, feat in spec.feats.items():
        for rid in feat["requirements"]:
            if rid in spec.reqs and fid not in spec.reqs[rid]["features"]:
                errors.append(f"{fid} lists {rid} in requirements, but {rid} does not list {fid} in features")
    for rid, req in spec.reqs.items():
        for fid in req["features"]:
            if fid in spec.feats and rid not in spec.feats[fid]["requirements"]:
                errors.append(f"{rid} lists {fid} in features, but {fid} does not list {rid} in requirements")
    return errors


def tests_of(steps):
    refs = sorted({t for s in steps for t in s.tests}, key=natural_key)
    if any(s.manual for s in steps):
        refs.append("manual")
    return ", ".join(refs) or "—"


def step_list(steps):
    return ", ".join(s.ref for s in steps) or "—"


def render_matrix(spec):
    spec_dir = spec.spec_dir
    lines = [
        "# Traceability matrix",
        "",
        "Generated by `spec_trace.py generate` from the FEAT, REQ and journey files.",
        "Never edit it by hand: `spec_trace.py check` fails when it is stale. These are reverse views",
        "only — the links are written once, in the journeys (journey → rule, task, test) and in FEAT/REQ",
        "frontmatter.",
        "",
        "## Journeys",
        "",
        "| Journey | Title | Status | Main steps | Alternative steps | Prerequisites | Rules cited |",
        "|---|---|---|---|---|---|---|",
    ]
    for jid, journey in spec.journeys.items():
        steps = journey["steps"]
        count = {k: sum(1 for s in steps if s.id.startswith(k)) for k in "SAP"}
        rules = len({r for s in steps for r in s.rules})
        link = journey["path"].relative_to(spec_dir).as_posix()
        lines.append(f"| [{jid}]({link}) | {journey['title']} | {journey['status']} | {count['S']} | "
                     f"{count['A']} | {count['P']} | {rules} |")
    lines += [
        "",
        "## Rules → journeys → tests",
        "",
        "One row per REQ. `—` in Journey steps: no journey proves the rule yet.",
        "",
        "| Rule | Title | FEATs | Journey steps | Tests at those steps |",
        "|---|---|---|---|---|",
    ]
    for rid in sorted(spec.reqs, key=natural_key):
        req = spec.reqs[rid]
        steps = [s for s in spec.steps if rid in s.rules]
        link = req["path"].relative_to(spec_dir).as_posix()
        feats = ", ".join(sorted(req["features"], key=natural_key)) or "—"
        lines.append(f"| [{rid}]({link}) | {req['title']} | {feats} | {step_list(steps)} | {tests_of(steps)} |")
    lines += [
        "",
        "## Tasks → journeys",
        "",
        "Every task a journey cites, in `Implemented by` or as a test task in `Proven by`.",
        "",
        "| Task | Journey steps |",
        "|---|---|",
    ]
    by_task = {}
    for step in spec.steps:
        for ref in step.tasks + [t for t in step.tests if not t.startswith("`")]:
            by_task.setdefault(ref, []).append(step)
    for ref in sorted(by_task, key=natural_key):
        lines.append(f"| {ref} | {step_list(by_task[ref])} |")
    return "\n".join(lines) + "\n"


def check(spec):
    errors = spec.errors + symmetry_errors(spec)
    matrix = spec.spec_dir / MATRIX
    if not matrix.exists() or matrix.read_text(encoding="utf-8") != render_matrix(spec):
        errors.append(f"{matrix} is stale or missing: run spec_trace.py generate on the spec directory")
    return errors


def derived_status(feat):
    """Return the status the task rows imply, or the current one when they imply none."""
    states = list(feat["task_status"].values())
    if feat["status"] in STATUS_FROZEN or "done" not in states:
        return feat["status"]
    return "delivered" if all(state == "done" for state in states) else "in-progress"


def status_errors(spec):
    return [f"{fid}: status={feat['status']!r} but its task rows imply {derived_status(feat)!r}: "
            "run spec_trace.py status --write"
            for fid, feat in spec.feats.items() if derived_status(feat) != feat["status"]]


def rewrite_status(spec, today):
    """Rewrite `status` and `updated` of every FEAT whose rows imply another status; return the ids."""
    changed = []
    for fid, feat in spec.feats.items():
        new = derived_status(feat)
        if new == feat["status"]:
            continue
        text = feat["path"].read_text(encoding="utf-8")
        head, sep, rest = text.partition("\n---\n")
        head = re.sub(r"(?m)^status:.*$", f"status: {new}", head, count=1)
        if re.search(r"(?m)^updated:", head):
            head = re.sub(r"(?m)^updated:.*$", f'updated: "{today}"', head, count=1)
        else:
            head = re.sub(r"(?m)^(status:.*)$", rf'\1\nupdated: "{today}"', head, count=1)
        feat["path"].write_text(head + sep + rest, encoding="utf-8")
        changed.append(f"{fid}: {feat['status']} -> {new}")
    return changed


def mark_done(spec, fid, tid, pr, today):
    """Set the Status cell of a task row to `done` and append a History line; return a message."""
    feat = spec.feats.get(fid)
    if feat is None or tid not in feat["tasks"]:
        raise SystemExit(f"{fid} {tid} is not a task row of a FEAT in {spec.spec_dir}")
    text = feat["path"].read_text(encoding="utf-8")
    _, body = split_frontmatter(text)
    column = status_column(body)
    if column is None:
        raise SystemExit(f"{fid} has no Status column in its task table")
    if feat["task_status"].get(tid) == "done":
        return f"{fid} {tid} is already done"
    old = feat["tasks"][tid]
    pieces = UNESCAPED_PIPE.split(old)
    pieces[column + 1] = " done "
    text = text.replace(old, "|".join(pieces), 1)
    entry = f"- {today} done: {tid}" + (f" ({pr})" if pr else "")
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines) if line == "## History"), None)
    if start is None:
        lines += ["", "## History", "", entry]
    else:
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        last = max((i for i in range(start, end) if lines[i].startswith("- ")), default=start + 1)
        lines.insert(last + 1, entry)
    feat["path"].write_text("\n".join(lines), encoding="utf-8")
    return f"{fid} {tid} -> done"


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def file_at(root, rev, path):
    shown = git(root, "show", f"{rev}:{path.relative_to(root).as_posix()}")
    return shown.stdout if shown.returncode == 0 else ""


def changes(spec, base, head):
    """Return [(label, steps)] for every REQ, FEAT task row, FEAT text or journey the diff changes."""
    try:
        spec_rel = spec.spec_dir.relative_to(spec.root).as_posix()
    except ValueError:
        spec_rel = "."
    diff = git(spec.root, "diff", "--name-only", f"{base}...{head}", "--", spec_rel)
    if diff.returncode != 0:
        raise SystemExit(f"git diff failed: {diff.stderr.strip()}")
    found = []
    for name in diff.stdout.split():
        path = spec.root / name
        stem = path.stem
        if REQ_ID.fullmatch(stem):
            found.append((f"{stem} edited", [s for s in spec.steps if stem in s.rules]))
        elif re.fullmatch(r"FEAT-\d{3,}", stem):
            found += feat_changes(spec, base, head, stem, path)
        elif JOURNEY_FILE.match(stem):
            jid = JOURNEY_FILE.match(stem).group(1)
            found.append((f"{jid} edited", spec.journeys.get(jid, {}).get("steps", [])))
    return found


def feat_changes(spec, base, head, fid, path):
    old_data, old_body = split_frontmatter(file_at(spec.root, base, path))
    new_data, new_body = split_frontmatter(file_at(spec.root, head, path))
    old_rows, new_rows = task_rows(old_body), task_rows(new_body)
    found = []
    for tid in sorted(set(old_rows) | set(new_rows), key=natural_key):
        if old_rows.get(tid) != new_rows.get(tid):
            ref = f"{fid} {tid}"
            found.append((f"{ref} row edited", [s for s in spec.steps if ref in s.tasks or ref in s.tests]))
    outside = [line for line in old_body.splitlines() if not TASK_ROW.match(line)]
    if outside != [line for line in new_body.splitlines() if not TASK_ROW.match(line)] or \
            (old_data or {}).get("requirements") != (new_data or {}).get("requirements"):
        steps = [s for s in spec.steps if any(t.startswith(fid + " ") for t in s.tasks + s.tests)]
        found.append((f"{fid} text outside the task table", steps))
    return found


def render_impact(found):
    lines = ["## Spec impact", ""]
    if not found:
        return "\n".join(lines + ["No REQ, FEAT or journey file changed in this diff.", ""])
    lines += [
        "Each change below names the journey steps the reviewer re-checks and the tests that prove them.",
        "",
        "| Change | Journey steps | Tests at those steps |",
        "|---|---|---|",
    ]
    lines += [f"| {label} | {step_list(steps)} | {tests_of(steps)} |" for label, steps in found if steps]
    orphans = [label for label, steps in found if not steps]
    if orphans:
        lines += ["", "No journey cites: " + "; ".join(orphans) + " — no journey proves these changes yet."]
    return "\n".join(lines) + "\n"


def report(errors, ok_message):
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    if errors:
        return 1
    print(ok_message)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", action="append", default=[], metavar="NAME",
                        help="extra clone name a `Proven by` test path may be rooted at "
                             "(repeatable; for clones CI does not check out)")
    parser.add_argument("--date", default=None, help="date for History and `updated` (default: today)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "generate"):
        p = sub.add_parser(name)
        p.add_argument("spec", type=Path, help="the spec directory (e.g. docs/spec)")
    status = sub.add_parser("status")
    status.add_argument("spec", type=Path, help="the spec directory (e.g. docs/spec)")
    status.add_argument("--write", action="store_true")
    impact = sub.add_parser("impact")
    impact.add_argument("spec", type=Path, help="the spec directory (e.g. docs/spec)")
    impact.add_argument("base")
    impact.add_argument("head")
    done = sub.add_parser("mark-done")
    done.add_argument("spec", type=Path, help="the spec directory (e.g. docs/spec)")
    done.add_argument("feat")
    done.add_argument("task")
    done.add_argument("--pr", help="merged task PR as <repo>#<n>")
    args = parser.parse_args(argv)
    today = args.date or datetime.date.today().isoformat()

    spec = load(args.spec, args.repo)
    matrix = spec.spec_dir / MATRIX
    summary = f"spec-trace: OK ({len(spec.journeys)} journeys, {len(spec.steps)} steps, {len(spec.reqs)} REQs)"
    if args.command == "generate":
        matrix.write_text(render_matrix(spec), encoding="utf-8")
        return report(spec.errors + symmetry_errors(spec), f"wrote {matrix}; " + summary)
    if args.command == "mark-done":
        if args.pr and not PR_REF.match(args.pr):
            raise SystemExit(f"--pr {args.pr!r} is not <repo>#<n>")
        print(mark_done(spec, args.feat, args.task, args.pr, today))
        return 0
    if args.command == "status":
        if args.write:
            changed = rewrite_status(spec, today)
            print("\n".join(changed) or "spec-trace status: nothing to rewrite")
            return 0
        return report(status_errors(spec), f"spec-trace status: OK ({len(spec.feats)} FEATs)")
    if args.command == "impact":
        print(render_impact(changes(spec, args.base, args.head)), end="")
        return 0
    return report(check(spec), summary)


if __name__ == "__main__":
    sys.exit(main())
