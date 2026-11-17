#!/usr/bin/env python3
"""Journey traceability for a project's spec directory (journeys <-> FEAT <-> REQ <-> tests).

  spec_trace.py check SPEC             fail on a broken journey link, a FEAT<->REQ asymmetry or a
                                       stale SPEC/traceability.md; with `sdd.spec_index`, also on a REQ or
                                       journey file without a linked row in SPEC/spec.md, or a row linking
                                       a missing one
  spec_trace.py generate SPEC          rewrite SPEC/traceability.md from the FEAT, REQ and journey files
  spec_trace.py impact SPEC BASE HEAD  markdown: the journey steps and tests a BASE...HEAD diff touches
  spec_trace.py checklist SPEC J-NN [J-NN ...] [--out FILE] [--force]
                                       one owner checklist per approved journey, to stdout (never committed)
  spec_trace.py sync-status SPEC [--write] [--backlog OWNER/NAME]
                                       `sdd.tracker: github` only: each task row's Status from its issue and
                                       the PRs that close it (sdd-tasks/references/task-issue.md § States),
                                       then each FEAT's status as `status` derives it; dry run without --write
  spec_trace.py mark-done SPEC FEAT-NNN Tn [--pr REPO#N]
                                       set the task row's Status to `done` and append a History line
  spec_trace.py status SPEC [--write]  derive each FEAT's status from its task rows (in-progress at most);
                                       fail on a mismatch or a validated/delivered FEAT with an open row,
                                       or with --write rewrite `status` and `updated` and add the History
                                       line `status: <old> -> in-progress (<rows>)`, whether a doing or a
                                       done row moved it (intended since #247: every move is recorded)
  spec_trace.py validate SPEC FEAT-NNN --at SHA [--check]
                                       sdd-review: every row done, a `## Closure` record, every step of a
                                       journey its NEEDs list filled; then `validated`, or `delivered` under
                                       `release: merge` (spec.md `sdd:`, the default)
  spec_trace.py deliver SPEC FEAT-NNN --in VERSION
                                       sdd-release: `validated` to `delivered`
  spec_trace.py lint SPEC [FEAT-NNN]   sdd-review's closure lint on FEAT-NNN, or on every validated or
                                       delivered FEAT: stale markers ("Not verified", an Audit "Pending",
                                       [PROPOSAL] in Scope, [HYPOTHESIS] in Open questions or a done row,
                                       "until/once Tn" with Tn done, a Plan row count that differs from the
                                       table) and each listed REQ's proving test missing from its trace row
  spec_trace.py enablers SPEC [--feat FEAT-NNN] [--catalog GLOB ...]
                                       the C18 and C19 findings of sdd-check over the ENBs (KIT-095); off, exit 0,
                                       without SPEC/enablers/

SPEC is optional everywhere and defaults to docs/spec under the working directory, so `impact BASE HEAD`
and `sync-status` run as a review loop calls them. Options (before the command): `--repo NAME` (repeatable)
adds a clone name a `Proven by` test path may be rooted at, and `--date` fixes the date written by
mark-done/status --write/sync-status --write/validate/deliver (default: today).

FEAT status (KIT-069): task rows derive `in-progress` at most. `validated` and `delivered` are written only by
`validate` and `deliver`, each with its History line, which check_spec.py requires; a FEAT that reaches `delivered`
moves each NEED whose listed FEATs are all delivered and cover its REQs to `delivered` too.

Journeys live in <spec>/journeys/J-NN.md. Every markdown table whose first header cell is `Step` is a
step table. Row ids: `S<n>` main path, `A<n>` alternative path (column `At` names its main step),
`P<n>` prerequisite. Cells: `Rules` holds REQ ids only, `Implemented by` holds `FEAT-nnn Tn` refs only,
`Proven by` holds test refs — `FEAT-nnn Tn` test tasks, backticked paths rooted at a clone name, and an
optional trailing `manual: <check>`. Journeys are written in sdd-clarify, before the FEAT and its tasks
exist, so a main or alternative step may hold a literal `—` in `Implemented by` and `Proven by` while a
NEED in <spec>/needs/ that lists the journey in `journeys` is open (not delivered, rejected, merged,
routed or parked, and its listed FEATs have not yet all delivered every REQ it lists); once none is, both cite refs. Without needs/ nothing waits. A prerequisite row, an
empty cell and a journey with no main step always fail.

Processes (KIT-090) live in <spec>/processes/PROC-nnn[-slug].md, frontmatter `id`, `title`, `status`, `owner` and
`kind` (`product` or `tech`). A process holds one reusable functional flow; its step tables follow the journey rules
above (a `—` waits while an open NEED lists the process in `processes`), and one process may cite the tasks of many
FEATs. A journey main or alternative step whose action cell cites `PROC-nnn` (every step) or `PROC-nnn S<a>–S<b>` (the
main steps S<a> to S<b> in table order and the alternatives whose `At` is one of them; a hyphen works too) holds `—` in
Rules, Implemented by and Proven by: it takes the cited steps' rules, tasks and tests, so the matrix, the impact and
the closure expand it. A prerequisite or a process step never cites a process. With processes, traceability.md adds
the Processes, Rules → processes → tests and Tasks → processes views; a spec without processes/ renders it as before.

Enablers (KIT-095) live in <spec>/enablers/ENB-nnn[-slug].md (check_spec.py checks the frontmatter). Each holds the
tables Aggregates (`Rules`: REQ-F ids), Events (`Direction` publishes or consumes, `Contract` an own contract or `—`),
Provided contracts (`Contract`, `Kind` among CONTRACT_KINDS, `Accessed at`, `Schema or file`, `Version`, `Consumers`),
Required contracts (`Contract`, `Kind`, `From`: the ENB that provides it, `Used for`) and Qualities (`Rules`: REQ-NF
ids). `providesApis` and `consumesApis` hold exactly the ids of the two contract tables. An ENB satisfies the REQs its
Aggregates and Qualities rows cite. With enablers, traceability.md adds the Enablers view (each ENB's contracts, the
REQs it satisfies, and the FEATs, decisions and debts whose `enablers` names it: its generated History and Decisions)
and the Contracts view, and is required. `enablers` reports, over the open FEATs or the one --feat names:
  C18 high    a REQ of the FEAT, or a process step whose Rules cite REQs, that no ENB satisfies;
  C19 high    a Plan § Contract reference `ENB-nnn:<contract>` the catalog lacks, or to an ENB the FEAT's `enablers`
              does not list; a file under sdd.row_checks.protocol.schemas or matching a --catalog glob (a migration
              folder, for example) that no `Schema or file` cell covers;
  C19 medium  a provided contract no ENB requires whose Consumers cell is empty or `—`.
It exits 1 on a finding. A spec without enablers/ checks and renders as before.

A test path's first segment names the clone it lives in: the spec's own repository (its directory name)
or a directory beside it — clones sit side by side on the machine that writes journeys — plus any
`--repo` names for clones CI does not check out. A path rooted at the spec's own repository must match
a file in it; other roots are format-checked only until the project's journey CI runs them. With
`sdd.components` (one repository, a folder per component; KIT-073) a path may also start with a component
name or a top-level path of the repository: a path in a component folder other than `.` needs only that
folder, since its row may write the test; any other path must match a file.

sync-status (KIT-073) reads `sdd.github`: the backlog repository (default: the origin remote), the other
repositories whose PRs close its issues, its earlier names, and the blocked and progress labels. It lists
every issue and every PR once per repository through `gh api` (no per-issue request). A row's `Item` cell (KIT-068:
`#N`, or `OWNER/NAME#N` of the backlog or an earlier name) names its issue and wins over any title, so a renamed issue
keeps its row; a row without one falls back to the issues titled `[FEAT-nnn Tn]` or `[FEAT-nnn T1+T2]`. A `gh` failure
or a missing backlog repository exits 2, like a refused `sdd` block (KIT-080). A member issue closed as not planned that a
bundle names in its title (`— bundled with FEAT-nnn Tn #N`) follows the bundle. A row is `done` once a
merged PR closes its issue; a closed issue then keeps the row (a warning) or, closed as not planned, makes it
`cancelled` (a `done` row stays), whatever labels it still carries; an open one is `blocked` with a blocked
label, `doing` with an open PR or a progress label, else `todo`. A `superseded` or `cancelled` row is never
rewritten. It never writes a FEAT's `validated` or `delivered`. --write also refreshes traceability.md, the
Status cell of each FEAT row in spec.md and, where their markers are, the `<!-- sync-status:begin -->` ...
`<!-- sync-status:end -->` block (in-progress FEATs) and the `<!-- sync-counts:begin -->` ...
`<!-- sync-counts:end -->` block (`N FEATs: n `status`, …`, proposed and cancelled FEATs named).

Run it after the frontmatter lint (`check_spec.py`), which this file is synced next to by
platforms/tools/sync-project.sh and which resolves the `sdd` block it reads. Upstreamed from a consumer
project's tools/spec-trace implementation (KIT-073 added sync-status, checklist and the index check).
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Iterable

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_spec  # noqa: E402  (the sdd parameters, resolved against spec.schema.json)

MATRIX = "traceability.md"

REQ_ID = re.compile(r"REQ-(?:F|NF)-\d{3,}")
TASK_REF = re.compile(r"FEAT-\d{3,} T\d+")
TASK_ROW = re.compile(r"^\| (T\d+) \|")
JOURNEY_FILE = re.compile(r"^(J-\d{2,})(?:-[a-z0-9-]+)?$")
JOURNEY_ID = re.compile(r"^J-\d{2,}$")
PROCESS_FILE = re.compile(r"^(PROC-\d{3,})(?:-[a-z0-9-]+)?$")
PROCESS_ID = re.compile(r"^PROC-\d{3,}$")
PROC_CITE = re.compile(r"PROC-\d{3,}(?:\s+[SAP]\d+(?:\s*[–-]\s*[SAP]\d+)?)?")  # what a step's action cell cites
PROC_RANGE = re.compile(r"^(PROC-\d{3,})(?: S(\d+)\s*[–-]\s*S(\d+))?$")  # the forms a citation may take
STEP_ID = re.compile(r"^[SAP]\d+$")
TEST_PATH = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*)/\S+$")
BACKTICKED = re.compile(r"`([^`]+)`")
MANUAL = re.compile(r"manual:\s*(.+)$")
SEPARATORS = re.compile(r"<br>|[\s,·;—]+")
PR_REF = re.compile(r"^[\w.-]+#\d+$")
UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")
STATUS_CLOSED = ("validated", "delivered")
STATUS_FROZEN = STATUS_CLOSED + ("cancelled",)
VALIDATE_FROM = ("clarified", "planned", "in-progress")
ROW_CLOSED = ("done", "superseded", "cancelled")  # superseded: replaced by another row; cancelled: a resync removed
# its work (KIT-068); both close like a done row
NEED_SETTLED = ("delivered", "rejected", "merged", "routed", "parked")
PENDING = "—"
JOURNEY_STATUS = ("proposed", "approved", "retired")
JOURNEY_FIELDS = ("id", "title", "status", "owner", "created", "updated")
PROCESS_FIELDS = ("id", "title", "status", "owner", "kind")
PROCESS_KINDS = ("product", "tech")
MAIN_COLUMNS = ("Rules", "Implemented by", "Proven by")
TEXT_SKIP = ("Step", "At", "Implemented by", "Rules", "Proven by")
STAGE = re.compile(r"\bstage ([A-Z][A-Za-z0-9-]*\d)\b")
INDEX_LINK = re.compile(r"\]\(([^)]+)\)")
ROW_FROZEN = ("superseded", "cancelled")  # sync-status never reopens a dropped row
ISSUE_TITLE = re.compile(r"^\[(FEAT-\d{3,}) (T\d+(?:\+T\d+)*)\]")
SYNC_BEGIN, SYNC_END = "<!-- sync-status:begin -->", "<!-- sync-status:end -->"
COUNTS_BEGIN, COUNTS_END = "<!-- sync-counts:begin -->", "<!-- sync-counts:end -->"
# feature.schema.json `status`, in lifecycle order; the counts line names the FEATs of the LISTED ones
FEAT_STATUSES = ("proposed", "clarified", "planned", "in-progress", "validated", "delivered", "cancelled")
COUNTS_LISTED = ("proposed", "cancelled")
REMOTE = re.compile(r"github\.com[:/]([\w.-]+/[\w.-]+?)(?:\.git)?/?$")
ENABLER_ID = re.compile(r"^ENB-\d{3,}$")  # KIT-095
CONTRACT_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")  # enabler.schema.json providesApis items
CONTRACT_REF = re.compile(r"\b(ENB-\d{3,}):([a-z0-9]+(?:[._-][a-z0-9]+)*)")  # a Plan § Contract reference
CONTRACT_KINDS = ("api", "message", "event", "job", "file", "table", "content", "config")
EVENT_DIRECTIONS = ("publishes", "consumes")


@dataclass
class Step:
    journey: str      # the journey or process (PROC-nnn) the step belongs to
    id: str
    at: str | None = None
    rules: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    manual: str | None = None
    action: str = ""
    cites: str | None = None  # the PROC-nnn a journey step cites; its rules, tasks and tests come from `expands`
    expands: list = field(default_factory=list)

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
    processes: dict = field(default_factory=dict)  # PROC id -> {"path", "title", "status", "kind", "steps"}
    open_needs: dict = field(default_factory=dict)  # J or PROC id -> ids of the open NEEDs whose `journeys` or
    # `processes` list it
    enablers: dict = field(default_factory=dict)  # ENB id -> load_enabler's record (KIT-095)
    enabler_links: dict = field(default_factory=dict)  # ENB id -> {"feature"|"decision"|"debt": [(id, status)]}
    errors: list = field(default_factory=list)
    params: dict = field(default_factory=dict)      # the resolved `sdd` block of spec.md (check_spec.py)
    param_errors: list = field(default_factory=list)

    @property
    def steps(self):
        return [s for j in self.journeys.values() for s in j["steps"]]

    @property
    def process_steps(self):
        return [s for p in self.processes.values() for s in p["steps"]]

    @property
    def all_steps(self):
        """Journey steps, then process steps: the same list as `steps` in a spec without processes."""
        return self.steps + self.process_steps


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


def task_items(body):
    """{Tn: Item cell} of the task table (KIT-068), {} when it has no `Item` column."""
    for line in body.splitlines():
        if line.startswith("| ID |"):
            header = row_cells(line)
            if "Item" not in header:
                return {}
            column = header.index("Item")
            return {tid: cells[column] for tid, row in task_rows(body).items()
                    if len(cells := row_cells(row)) > column}
    return {}


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


def schemas_dir() -> Path:
    """spec.schema.json beside this file (the synced copy) or in the kit's platforms/ci/schemas."""
    return next((d for d in (HERE / "schemas", HERE.parent / "schemas") if (d / "spec.schema.json").is_file()),
                HERE / "schemas")


def load_params(spec_dir: Path) -> tuple:
    """The resolved `sdd` block and the errors check_spec.py reports on it; ({}, [why]) without the schema."""
    folder = schemas_dir()
    if not (folder / "spec.schema.json").is_file():
        return {}, [f"no spec.schema.json beside {Path(__file__).name}"]
    return check_spec.load_params(spec_dir, folder)


def load(spec_dir: Path, extra_repos: Iterable[str] = ()) -> Spec:
    spec_dir = spec_dir.resolve()
    root = repo_root(spec_dir)
    spec = Spec(root=root, spec_dir=spec_dir, repos=test_roots(root, extra_repos))
    spec.params, spec.param_errors = load_params(spec_dir)
    for path in sorted((spec_dir / "features").glob("FEAT-*.md")):
        data, body = split_frontmatter(path.read_text(encoding="utf-8"))
        if data and data.get("id"):
            spec.feats[data["id"]] = {"path": path, "requirements": data.get("requirements") or [],
                                      "tasks": task_rows(body), "status": data.get("status"),
                                      "task_status": task_statuses(body), "task_item": task_items(body),
                                      "title": data.get("title", data["id"])}
    for path in sorted((spec_dir / "requirements").rglob("REQ-*.md")):
        data, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        if data and data.get("id"):
            spec.reqs[data["id"]] = {"path": path, "features": data.get("features") or [],
                                     "title": data.get("title", "")}
    load_open_needs(spec, spec_dir / "needs")
    for path in sorted((spec_dir / "processes").glob("PROC-*.md"), key=lambda p: natural_key(p.name)):
        load_process(spec, path)  # before the journeys, whose steps may cite a process
    for path in sorted((spec_dir / "journeys").glob("J-*.md"), key=lambda p: natural_key(p.name)):
        load_journey(spec, path)
    load_enablers(spec)
    return spec


def listed(data: dict, key: str) -> list:
    value = data.get(key) or []
    return [str(v) for v in (value if isinstance(value, list) else [value])]


def delivered_by_its_feats(spec: Spec, need: dict) -> bool:
    """A NEED whose listed FEATs are all delivered and cover every REQ it lists no longer holds a step's `—`, even
    before its own status moves to delivered (validate or deliver moves it, KIT-069; older NEEDs may lag)."""
    feats = listed(need, "features")
    if not feats or any(spec.feats.get(f, {}).get("status") != "delivered" for f in feats):
        return False
    covered = {str(r) for f in feats for r in spec.feats[f]["requirements"]}
    return set(listed(need, "requirements")) <= covered


def load_open_needs(spec: Spec, needs_dir: Path) -> None:
    """Map each journey and process to the open NEEDs that list it; check_spec.py validates the NEED files."""
    for path in sorted(needs_dir.glob("NEED-*.md")):
        data, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data.get("id") or data.get("status") in NEED_SETTLED:
            continue
        if delivered_by_its_feats(spec, data):
            continue
        for key in ("journeys", "processes"):
            for jid in listed(data, key):
                spec.open_needs.setdefault(jid, []).append(str(data["id"]))


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
    goal = section(body, "Goal")
    spec.journeys[jid] = {"path": path, "title": data.get("title", ""), "status": data.get("status"),
                          "steps": steps, "preconditions": section(body, "Preconditions"),
                          "stage": next(iter(STAGE.findall(goal)), "")}


def load_process(spec, path):
    """A PROC-nnn file (KIT-090): frontmatter as check_spec.py reads it, then its step tables."""
    where = path.relative_to(spec.root)
    data, body = split_frontmatter(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        spec.errors.append(f"{where}: frontmatter missing, not closed by --- or not a mapping")
        return
    for key in PROCESS_FIELDS:
        if key not in data:
            spec.errors.append(f"{where}: required field missing: {key}")
    pid = str(data.get("id", ""))
    name = PROCESS_FILE.match(path.stem)
    if not PROCESS_ID.match(pid):
        spec.errors.append(f"{where}: id {pid!r} does not match PROC-nnn")
        return
    if not name or name.group(1) != pid:
        spec.errors.append(f"{where}: id={pid} != file name prefix")
    if data.get("status") not in JOURNEY_STATUS:
        spec.errors.append(f"{where}: status={data.get('status')!r} not in {list(JOURNEY_STATUS)}")
    if "kind" in data and data.get("kind") not in PROCESS_KINDS:
        spec.errors.append(f"{where}: kind={data.get('kind')!r} not in {list(PROCESS_KINDS)}")
    if pid in spec.processes:
        spec.errors.append(f"{where}: duplicate id {pid}")
        return
    spec.processes[pid] = {"path": path, "title": data.get("title", ""), "status": data.get("status"),
                           "kind": data.get("kind"), "steps": parse_steps(spec, pid, body)}


def section(body, name):
    """The text under `## name` up to the next `## ` heading, stripped; empty when the section is absent."""
    lines, found = [], False
    for line in body.splitlines():
        if line.startswith("## "):
            if found:
                break
            found = line[3:].strip() == name
        elif found:
            lines.append(line)
    return "\n".join(lines).strip()


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
    action = next((v for k, v in row.items() if k not in TEXT_SKIP), "")
    step = Step(journey=jid, id=sid, at=row.get("At") or None, action=action)
    cites = PROC_CITE.findall(action)
    if cites and PROCESS_ID.match(jid):
        spec.errors.append(f"{step.ref}: a process step cannot cite a process ({', '.join(cites)})")
    elif cites:
        return citing_step(spec, step, row, cites)
    if "Implemented by" not in header:
        spec.errors.append(f"{step.ref}: table has no 'Implemented by' column")
        return step
    step.tasks = only_ids(spec, step, "Implemented by", row["Implemented by"], TASK_REF)
    check_tasks(spec, step, step.tasks)
    missing = [c for c in MAIN_COLUMNS if c not in header]
    if sid.startswith("P") or missing:
        if not step.tasks:
            spec.errors.append(f"{step.ref}: Implemented by cites no task (FEAT-nnn Tn)")
        if missing and not sid.startswith("P"):
            spec.errors.append(f"{step.ref}: table lacks column(s) {missing}")
        return step
    step.rules = only_ids(spec, step, "Rules", row["Rules"], REQ_ID)
    for rid in step.rules:
        if rid not in spec.reqs:
            spec.errors.append(f"{step.ref}: Rules cites {rid}, which does not exist")
    cell = row["Implemented by"]
    if not step.tasks and not awaits(spec, step, cell):
        spec.errors.append(f"{step.ref}: Implemented by cites no task (FEAT-nnn Tn){why_due(spec, step, cell)}")
    parse_tests(spec, step, row["Proven by"])
    return step


def citing_step(spec: Spec, step: Step, row: dict, cites: list) -> Step:
    """A journey step that cites a process holds `—` in its own link cells and takes the cited steps' links."""
    if step.id.startswith("P"):
        spec.errors.append(f"{step.ref}: a prerequisite cannot cite a process; it cites its task")
        return step
    if len(cites) > 1:
        spec.errors.append(f"{step.ref}: cites more than one process ({', '.join(cites)}); split the step")
        return step
    cite = re.sub(r"\s+", " ", cites[0])
    if any(row.get(column, "").strip() != PENDING for column in MAIN_COLUMNS):
        spec.errors.append(f"{step.ref}: a step that cites {cite.split()[0]} holds `{PENDING}` in Rules, Implemented by "
                           "and Proven by: the process's steps carry them")
    m = PROC_RANGE.match(cite)
    if not m:
        spec.errors.append(f"{step.ref}: cites {cite!r}: write PROC-nnn or PROC-nnn S<a>–S<b>")
        return step
    step.cites = m.group(1)
    process = spec.processes.get(step.cites)
    if process is None:
        spec.errors.append(f"{step.ref}: cites {step.cites}, which does not exist")
        return step
    steps = process["steps"]
    if m.group(2) is None:
        step.expands = list(steps)
    else:
        main = [s.id for s in steps if s.id.startswith("S")]
        ends = [f"S{m.group(2)}", f"S{m.group(3)}"]
        unknown = [e for e in ends if e not in main]
        if unknown:
            spec.errors.append(f"{step.ref}: {cite}: {unknown[0]} is not a main step of {step.cites}")
            return step
        first, last = main.index(ends[0]), main.index(ends[1])
        if first > last:
            spec.errors.append(f"{step.ref}: {cite}: the range runs backwards")
            return step
        chosen = set(main[first:last + 1])
        step.expands = [s for s in steps if s.id in chosen or (s.id.startswith("A") and s.at in chosen)]
    for attr in ("rules", "tasks", "tests"):
        setattr(step, attr, list(dict.fromkeys(v for s in step.expands for v in getattr(s, attr))))
    step.manual = "; ".join(s.manual for s in step.expands if s.manual) or None
    return step


def awaits(spec: Spec, step: Step, cell: str) -> bool:
    """A literal `—` waits for the FEAT, its tasks and tests while an open NEED lists the step's journey or process."""
    return cell.strip() == PENDING and bool(spec.open_needs.get(step.journey))


def why_due(spec: Spec, step: Step, cell: str) -> str:
    """Why a `—` no longer waits; empty for any other cell, whose message stays as on main."""
    if cell.strip() != PENDING or spec.open_needs.get(step.journey):
        return ""
    noun = "process" if PROCESS_ID.match(step.journey) else "journey"
    return (f"; `{PENDING}` waits only while a NEED listing the {noun} is open: no open NEED lists {step.journey} "
            f"(a NEED whose listed FEATs are all delivered and cover every REQ it lists counts as settled)")


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


def parse_tests(spec: Spec, step: Step, cell: str) -> None:
    pending, due = awaits(spec, step, cell), why_due(spec, step, cell)
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
        if component_path_error(spec, step, path) is not None:
            continue
        m = TEST_PATH.match(path)
        if not m or m.group(1) not in spec.repos:
            spec.errors.append(f"{step.ref}: test path {path!r} is not rooted at a clone name "
                               f"({', '.join(sorted(spec.repos))}, or a --repo extra)")
        elif m.group(1) == spec.root.name and not any(spec.root.glob(path[len(m.group(1)) + 1:])):
            spec.errors.append(f"{step.ref}: test path {path!r} matches no file in this repository")
    step.tests = tasks + [f"`{p}`" for p in paths]
    if not step.tests and not step.manual and not pending:
        spec.errors.append(f"{step.ref}: Proven by cites no test{due}")


def component_path_error(spec: Spec, step: Step, path: str):
    """With `sdd.components`: None when the path is not this repository's (the clone-name rules decide), else ""
    when it is valid, or the error it records. A path starts with a component name (read as its folder) or a
    top-level entry of the repository; one in a component folder other than `.` needs only that folder (its row may
    write the test), any other must match a file."""
    components = spec.params.get("components") or {}
    if not components:
        return None
    head, sep, rest = path.partition("/")
    folder = components.get(head)
    normal = path if folder is None else (rest if folder == "." else f"{folder}{sep}{rest}")
    parts = normal.split("/")
    if folder is None and not (head and (spec.root / head).exists() and head != spec.root.name):
        return None
    folders = {f for f in components.values() if f != "."}
    if any(p in {"", ".", "..", ".git"} for p in parts) or re.search(r"\s", path) or \
            not (spec.root / parts[0]).exists():
        error = (f"{step.ref}: test path {path!r} is not rooted at a component ({', '.join(sorted(components))}) "
                 "or a top-level path of this repository")
    elif parts[0] not in folders and not any(spec.root.glob(normal)):
        error = f"{step.ref}: test path {path!r} matches no file in this repository"
    else:
        return ""
    spec.errors.append(error)
    return error


def baseline_held(spec_dir: Path, rule: str) -> dict:
    """{artifact: n} that check_spec.py's baseline.json holds for `rule`; {} without the file or for an entry
    check_spec.py refuses (it fails such a file itself)."""
    try:
        keys = json.loads((spec_dir / check_spec.BASELINE).read_text(encoding="utf-8"))["rules"][rule]
    except (OSError, ValueError, KeyError, TypeError):
        return {}
    if not isinstance(keys, dict):
        return {}
    return {k: n for k, n in keys.items() if isinstance(n, int) and not isinstance(n, bool) and n >= 1}


def symmetry_errors(spec):
    """The FEAT<->REQ links written on one side only, minus those check_spec.py's baseline holds under
    `link-one-sided` (#265): each finding is keyed by the artifact that lists the other, as check_spec.py keys it,
    and an artifact's findings are held while their count is at most the baseline's."""
    found = []
    for fid, feat in spec.feats.items():
        for rid in feat["requirements"]:
            if rid in spec.reqs and fid not in spec.reqs[rid]["features"]:
                found.append((check_spec.artifact_key(feat["path"]),
                              f"{fid} lists {rid} in requirements, but {rid} does not list {fid} in features"))
    for rid, req in spec.reqs.items():
        for fid in req["features"]:
            if fid in spec.feats and rid not in spec.feats[fid]["requirements"]:
                found.append((check_spec.artifact_key(req["path"]),
                              f"{rid} lists {fid} in features, but {fid} does not list {rid} in requirements"))
    held = baseline_held(spec.spec_dir, "link-one-sided")
    counts = {}
    for key, _ in found:
        counts[key] = counts.get(key, 0) + 1
    return [message for key, message in found if not (held.get(key) and counts[key] <= held[key])]


def tests_of(steps):
    refs = sorted({t for s in steps for t in s.tests}, key=natural_key)
    if any(s.manual for s in steps):
        refs.append("manual")
    return ", ".join(refs) or "—"


def step_list(steps):
    return ", ".join(s.ref for s in steps) or "—"


def render_matrix(spec):
    spec_dir = spec.spec_dir
    sources = "FEAT, REQ, journey and process files" if spec.processes else "FEAT, REQ and journey files"
    lines = [
        "# Traceability matrix",
        "",
        f"Generated by `spec_trace.py generate` from the {sources}.",
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
    if spec.processes:
        lines += process_views(spec)
    if spec.enablers:
        lines += enabler_views(spec)
    return "\n".join(lines) + "\n"


def process_views(spec):
    """The matrix sections a spec with processes adds (KIT-090): Processes, Rules → processes → tests and
    Tasks → processes, the view a review reads for the task of a code PR that serves a process."""
    lines = [
        "",
        "## Processes",
        "",
        "`Cited by`: the journey steps that cite the process, whole or a range of its steps.",
        "",
        "| Process | Title | Kind | Status | Main steps | Alternative steps | Rules cited | Cited by |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for pid, process in spec.processes.items():
        steps = process["steps"]
        count = {k: sum(1 for s in steps if s.id.startswith(k)) for k in "SA"}
        rules = len({r for s in steps for r in s.rules})
        link = process["path"].relative_to(spec.spec_dir).as_posix()
        cited = [s for s in spec.steps if s.cites == pid]
        lines.append(f"| [{pid}]({link}) | {process['title']} | {process['kind']} | {process['status']} | "
                     f"{count['S']} | {count['A']} | {rules} | {step_list(cited)} |")
    lines += [
        "",
        "## Rules → processes → tests",
        "",
        "Every REQ a process step cites.",
        "",
        "| Rule | Title | FEATs | Process steps | Tests at those steps |",
        "|---|---|---|---|---|",
    ]
    for rid in sorted({r for s in spec.process_steps for r in s.rules}, key=natural_key):
        steps = [s for s in spec.process_steps if rid in s.rules]
        req = spec.reqs.get(rid)
        if req is None:
            continue  # check reports the unknown id
        link = req["path"].relative_to(spec.spec_dir).as_posix()
        feats = ", ".join(sorted(req["features"], key=natural_key)) or "—"
        lines.append(f"| [{rid}]({link}) | {req['title']} | {feats} | {step_list(steps)} | {tests_of(steps)} |")
    lines += [
        "",
        "## Tasks → processes",
        "",
        "Every task a process cites, in `Implemented by` or as a test task in `Proven by`.",
        "",
        "| Task | Process steps |",
        "|---|---|",
    ]
    by_task = {}
    for step in spec.process_steps:
        for ref in step.tasks + [t for t in step.tests if not t.startswith("`")]:
            by_task.setdefault(ref, []).append(step)
    for ref in sorted(by_task, key=natural_key):
        lines.append(f"| {ref} | {step_list(by_task[ref])} |")
    return lines


def section_rows(body, name, first):
    """The rows, as {header: cell}, of every table under `## name` whose first header cell is `first`."""
    return [dict(zip(header, cells)) for header, rows in markdown_tables(section(body, name))
            if header and header[0] == first for cells in rows]


def rule_ids(spec, eid, table, cell, prefix):
    """The REQ ids of an ENB Rules cell (`—` or empty: none); text other than ids, an unknown id or an id of the other
    REQ type is an error."""
    tokens = [t for t in SEPARATORS.split(cell) if t]
    ids = [t for t in tokens if REQ_ID.fullmatch(t)]
    if len(ids) != len(tokens):
        spec.errors.append(f"{eid}: {table} Rules holds more than REQ ids: {cell!r}")
    for rid in ids:
        if not rid.startswith(prefix):
            spec.errors.append(f"{eid}: {table} cites {rid}; it holds {prefix[:-1]} ids only")
        elif rid not in spec.reqs:
            spec.errors.append(f"{eid}: {table} cites {rid}, which does not exist")
    return {rid for rid in ids if rid.startswith(prefix)}


def contract_rows(spec, eid, data, body, table, field_name):
    """{contract id: row} of one contract table, checked against its frontmatter list (the same ids both sides)."""
    rows = {}
    for row in section_rows(body, table, "Contract"):
        api = row.get("Contract", "")
        if not CONTRACT_ID.match(api):
            spec.errors.append(f"{eid}: {table} contract id {api!r} does not match {CONTRACT_ID.pattern}")
            continue
        if api in rows:
            spec.errors.append(f"{eid}: {table} lists {api} twice")
        if row.get("Kind") not in CONTRACT_KINDS:
            spec.errors.append(f"{eid}: {api} kind {row.get('Kind')!r} is not one of {', '.join(CONTRACT_KINDS)}")
        rows[api] = row
    declared = listed(data, field_name)
    for api in declared:
        if api not in rows:
            spec.errors.append(f"{eid}: {field_name} lists {api}, which no {table} row holds")
    for api in rows:
        if api not in declared:
            spec.errors.append(f"{eid}: {table} row {api} is missing from {field_name}")
    return rows


def load_enabler(spec, path):
    """An ENB-nnn file (KIT-095): its contract tables, events and the REQs its Aggregates and Qualities satisfy."""
    data, body = split_frontmatter(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        spec.errors.append(f"{path.relative_to(spec.root)}: frontmatter missing, not closed by --- or not a mapping")
        return
    eid = str(data.get("id", ""))
    if not ENABLER_ID.match(eid) or eid in spec.enablers:
        return  # check_spec.py reports the id and the duplicate
    provides = contract_rows(spec, eid, data, body, "Provided contracts", "providesApis")
    requires = contract_rows(spec, eid, data, body, "Required contracts", "consumesApis")
    satisfies = set()
    for row in section_rows(body, "Aggregates", "Aggregate"):
        satisfies |= rule_ids(spec, eid, "Aggregates", row.get("Rules", ""), "REQ-F-")
    for row in section_rows(body, "Qualities", "Quality"):
        satisfies |= rule_ids(spec, eid, "Qualities", row.get("Rules", ""), "REQ-NF-")
    for row in section_rows(body, "Events", "Event"):
        direction, api = row.get("Direction", ""), row.get("Contract", "")
        if direction not in EVENT_DIRECTIONS:
            spec.errors.append(f"{eid}: event {row.get('Event')} direction {direction!r} is not publishes or consumes")
        elif api not in ("", PENDING) and api not in (provides if direction == "publishes" else requires):
            table = "Provided" if direction == "publishes" else "Required"
            spec.errors.append(f"{eid}: event {row.get('Event')} {direction} {api}, which is not a {table} contract")
    catalog = [p for row in provides.values() for p in BACKTICKED.findall(row.get("Schema or file", ""))]
    spec.enablers[eid] = {"path": path, "title": data.get("title", ""), "status": data.get("status"),
                          "owner": data.get("owner", ""), "domain": data.get("domain") or PENDING,
                          "provides": provides, "requires": requires, "satisfies": satisfies, "catalog": catalog}


def load_enablers(spec):
    """enablers/ (KIT-095): every ENB, the provider of each required contract, and the FEATs, decisions and debts
    whose `enablers` names each ENB; nothing without the folder."""
    folder = spec.spec_dir / "enablers"
    if not folder.is_dir():
        return
    for path in sorted(folder.glob("ENB-*.md"), key=lambda p: natural_key(p.name)):
        load_enabler(spec, path)
    providers = {api: eid for eid, enabler in spec.enablers.items() for api in enabler["provides"]}
    for eid, enabler in spec.enablers.items():
        for api, row in enabler["requires"].items():
            source = row.get("From", "")
            if api in providers and source != providers[api]:
                spec.errors.append(f"{eid}: Required contract {api} is From {source}, but {providers[api]} provides it")
    spec.enabler_links = {eid: {"feature": [], "decision": [], "debt": []} for eid in spec.enablers}
    for sub, kind in (("features", "feature"), ("decisions", "decision"), ("debts", "debt")):
        for path in sorted((spec.spec_dir / sub).rglob("*.md"), key=lambda p: natural_key(p.name)):
            data, _ = split_frontmatter(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not data.get("id"):
                continue
            for eid in listed(data, "enablers"):
                if eid in spec.enabler_links:
                    spec.enabler_links[eid][kind].append((str(data["id"]), data.get("status")))


def enabler_views(spec):
    """The matrix sections a spec with enablers adds (KIT-095): Enablers, with each ENB's generated History (FEATs)
    and Decisions (decisions and debts), and Contracts, the catalog across ENBs."""
    lines = [
        "",
        "## Enablers",
        "",
        "`FEATs` (History), `Decisions` and `Debts`: the records whose `enablers` names the ENB.",
        "",
        "| Enabler | Title | Owner | Domain | Provides | Consumes | Satisfies | FEATs | Decisions | Debts |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for eid, enabler in spec.enablers.items():
        links = spec.enabler_links[eid]
        link = enabler["path"].relative_to(spec.spec_dir).as_posix()
        feats = ", ".join(f"{fid} ({status})" for fid, status in sorted(links["feature"], key=lambda f: natural_key(f[0])))
        lines.append(" ".join([
            f"| [{eid}]({link}) | {enabler['title']} | {enabler['owner']} | {enabler['domain']} |",
            f"{', '.join(sorted(enabler['provides'])) or PENDING} |",
            f"{', '.join(sorted(enabler['requires'])) or PENDING} |",
            f"{', '.join(sorted(enabler['satisfies'], key=natural_key)) or PENDING} |",
            f"{feats or PENDING} |",
            f"{', '.join(sorted((d for d, _ in links['decision']), key=natural_key)) or PENDING} |",
            f"{', '.join(sorted((d for d, _ in links['debt']), key=natural_key)) or PENDING} |"]))
    lines += [
        "",
        "## Contracts",
        "",
        "Every provided contract; `Consumed by`: the ENBs whose Required contracts list it.",
        "",
        "| Contract | Kind | Provided by | Consumed by | Accessed at | Schema or file | Version |",
        "|---|---|---|---|---|---|---|",
    ]
    rows = sorted((api, eid, row) for eid, enabler in spec.enablers.items() for api, row in enabler["provides"].items())
    for api, eid, row in rows:
        consumers = [other for other, enabler in spec.enablers.items() if api in enabler["requires"]]
        lines.append(f"| {api} | {row.get('Kind', '')} | {eid} | {', '.join(consumers) or PENDING} | "
                     f"{row.get('Accessed at', '')} | {row.get('Schema or file', '')} | {row.get('Version', '')} |")
    return lines


def plan_contract(body):
    """The text of a FEAT's `### Contract` Plan section, up to the next `### ` or `## ` heading."""
    lines, found = [], False
    for line in body.splitlines():
        if line.startswith(("## ", "### ")):
            if found:
                break
            found = line.strip() == "### Contract"
        elif found:
            lines.append(line)
    return "\n".join(lines)


def catalog_files(spec, globs):
    """Repository paths the catalog must cover: every file under sdd.row_checks.protocol.schemas and every file a
    --catalog glob (rooted at the repository) matches."""
    protocol = (spec.params.get("row_checks") or {}).get("protocol") or {}
    patterns = [f"{protocol['schemas'].rstrip('/')}/**/*"] if protocol.get("schemas") else []
    found = set()
    for pattern in patterns + list(globs):
        found |= {p.relative_to(spec.root).as_posix() for p in spec.root.glob(pattern)
                  if p.is_file() and not any(part.startswith(".") for part in p.relative_to(spec.root).parts)}
    return sorted(found)


def covered(path, catalog):
    return any(fnmatchcase(path, p) or path == p or path.startswith(p.rstrip("/") + "/") for p in catalog)


def enabler_findings(spec, fid=None, globs=()):
    """C18 and C19 (KIT-095) over the open FEATs, or the one `fid` names; each finding is `C<n> <severity>: text`."""
    scope = [fid] if fid else [f for f, feat in spec.feats.items() if feat["status"] not in STATUS_FROZEN]
    satisfied = {rid for enabler in spec.enablers.values() for rid in enabler["satisfies"]}
    findings = []
    for f in scope:
        for rid in spec.feats[f]["requirements"]:
            if rid not in satisfied:
                findings.append(f"C18 high: {rid} ({f}) has no ENB that satisfies it in Aggregates or Qualities")
    in_scope = {r for f in scope for r in spec.feats[f]["requirements"]}
    for step in spec.process_steps:
        if not step.rules or any(r in satisfied for r in step.rules):
            continue
        if fid is None or in_scope & set(step.rules) or any(t.startswith(f"{fid} ") for t in step.tasks):
            findings.append(f"C18 high: {step.ref} cites {', '.join(step.rules)}, which no ENB satisfies")
    for f in scope:
        data, body = split_frontmatter(spec.feats[f]["path"].read_text(encoding="utf-8"))
        names = listed(data or {}, "enablers")
        for eid, api in dict.fromkeys(CONTRACT_REF.findall(plan_contract(body))):
            ref = f"{eid}:{api}"
            if eid not in spec.enablers:
                findings.append(f"C19 high: {f} Plan § Contract cites {ref}, which is not an existing enabler")
            elif api not in spec.enablers[eid]["provides"]:
                findings.append(f"C19 high: {f} Plan § Contract cites {ref}, which {eid} Provided contracts lacks")
            if eid not in names:
                findings.append(f"C19 high: {f} Plan § Contract cites {ref}, but {f} enablers does not list {eid}")
    consumed = {api for enabler in spec.enablers.values() for api in enabler["requires"]}
    for eid, enabler in spec.enablers.items():
        for api, row in enabler["provides"].items():
            if api not in consumed and row.get("Consumers", "").strip() in ("", PENDING):
                findings.append(f"C19 medium: {eid} {api} has no consumer and no public mark")
    catalog = [p for enabler in spec.enablers.values() for p in enabler["catalog"]]
    for path in catalog_files(spec, globs):
        if not covered(path, catalog):
            findings.append(f"C19 high: {path} is in no ENB catalog (Schema or file)")
    return findings


def enablers_command(spec, fid, globs):
    """`spec_trace.py enablers`: print the C18 and C19 findings; exit 1 on any, 0 when clean or off."""
    if not (spec.spec_dir / "enablers").is_dir():
        print("enablers: off (no enablers/ folder; C18 and C19 apply once it exists)")
        return 0
    if fid and fid not in spec.feats:
        return report([f"{fid} does not exist in features/"], "")
    bad = [g for g in globs if g.startswith("/") or ".." in Path(g).parts]
    if bad:
        return report([f"--catalog {g!r} must be a glob rooted at the repository" for g in bad], "")
    findings = enabler_findings(spec, fid, globs)
    for finding in findings:
        print(finding)
    if findings:
        return 1
    contracts = sum(len(e["provides"]) for e in spec.enablers.values())
    print(f"enablers: OK ({len(spec.enablers)} enablers, {contracts} contracts)")
    return 0


def journeys_on(spec) -> bool:
    """`sdd.journeys`; absent = on when the spec has a journeys/ folder."""
    value = spec.params.get("journeys")
    return value if isinstance(value, bool) else (spec.spec_dir / "journeys").is_dir()


def check(spec):
    errors = spec.errors + symmetry_errors(spec)
    if spec.params.get("spec_index"):
        errors += index_errors(spec)
    matrix = spec.spec_dir / MATRIX
    # The matrix is required with journeys or processes and kept fresh once it exists; a project with none needs none.
    if (journeys_on(spec) or (spec.spec_dir / "processes").is_dir() or (spec.spec_dir / "enablers").is_dir()
            or matrix.exists()) and (
            not matrix.exists() or matrix.read_text(encoding="utf-8") != render_matrix(spec)):
        errors.append(f"{matrix} is stale or missing: run spec_trace.py generate on the spec directory")
    return errors


def index_errors(spec):
    """`sdd.spec_index`: every functional and non-functional REQ file and every journey file has a linked table row in
    spec.md, and each such link points to an existing file. Paths are relative to the spec directory."""
    index = spec.spec_dir / "spec.md"
    if not index.exists():
        return ["spec.md is missing"]
    base = spec.spec_dir.resolve()
    indexed, errors = set(), []
    for line in index.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        for match in INDEX_LINK.finditer(line):
            target = match.group(1).split("#", 1)[0]
            if not target or "://" in target:
                continue
            path = (index.parent / target).resolve()
            try:
                rel = path.relative_to(base).as_posix()
            except ValueError:
                continue
            if not re.match(r"^(requirements/functional/REQ-F-|requirements/non-functional/REQ-NF-|journeys/J-)"
                            r".*\.md$", rel):
                continue
            if path.is_file():
                indexed.add(path)
            else:
                errors.append(f"spec.md: link points to missing file {rel}")
    candidates = [*(base / "requirements" / "functional").glob("REQ-F-*.md"),
                  *(base / "requirements" / "non-functional").glob("REQ-NF-*.md"), *(base / "journeys").glob("J-*.md")]
    errors += [f"{path.relative_to(base).as_posix()} has no row in spec.md"
               for path in sorted(candidates) if path.resolve() not in indexed]
    return errors


def open_rows(feat):
    """`Tn state` for each row that is not closed."""
    return [f"{tid} {state}" for tid, state in feat["task_status"].items() if state not in ROW_CLOSED]


ROW_STARTED = ("doing", "done")  # a row whose work has begun (KIT-068 states): it moves the FEAT to in-progress


def started_rows(feat):
    """`Tn state` for each row whose work has begun."""
    return [f"{tid} {state}" for tid, state in feat["task_status"].items() if state in ROW_STARTED]


def derived_status(feat):
    """Return the status the task rows imply (in-progress at most), or the current one when they imply none: a
    `doing` or `done` row means the work has begun. A validated FEAT with an open row (a refused release filed one)
    goes back to in-progress, so sdd-review runs again."""
    if feat["status"] == "validated" and open_rows(feat):
        return "in-progress"
    if feat["status"] in STATUS_FROZEN or not started_rows(feat):
        return feat["status"]
    return "in-progress"


def status_errors(spec):
    errors = [f"{fid}: status={feat['status']!r} but its task rows imply {derived_status(feat)!r}: "
              "run spec_trace.py status --write"
              for fid, feat in spec.feats.items() if derived_status(feat) != feat["status"]]
    errors += [f"{fid}: status={feat['status']!r} but {tid} is {state!r}: sdd-review closes a FEAT only when "
               "every row is done"
               for fid, feat in spec.feats.items() if feat["status"] in STATUS_CLOSED
               for tid, state in feat["task_status"].items() if state not in ROW_CLOSED]
    return errors


def set_status(path, new, today):
    """Rewrite the frontmatter `status` and `updated` of a FEAT or NEED file."""
    text = path.read_text(encoding="utf-8")
    head, sep, rest = text.partition("\n---\n")
    head = re.sub(r"(?m)^status:.*$", f"status: {new}", head, count=1)
    if re.search(r"(?m)^updated:", head):
        head = re.sub(r"(?m)^updated:.*$", f'updated: "{today}"', head, count=1)
    else:
        head = re.sub(r"(?m)^(status:.*)$", rf'\1\nupdated: "{today}"', head, count=1)
    path.write_text(head + sep + rest, encoding="utf-8")


def append_history(path, entry):
    """Append `entry` after the last line of the file's `## History` list (a new section when it has none)."""
    lines = path.read_text(encoding="utf-8").split("\n")
    start = next((i for i, line in enumerate(lines) if line == "## History"), None)
    if start is None:
        lines += ["", "## History", "", entry]
    else:
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        last = max((i for i in range(start, end) if lines[i].startswith("- ")), default=start + 1)
        while last + 1 < end and lines[last + 1].startswith((" ", "\t")) and lines[last + 1].strip():
            last += 1  # past the bullet's continuation lines, so the new line never splits it
        lines.insert(last + 1, entry)
    path.write_text("\n".join(lines), encoding="utf-8")


def rewrite_status(spec, today):
    """Rewrite `status` and `updated` of every FEAT whose rows imply another status; return the ids."""
    changed = []
    for fid, feat in spec.feats.items():
        new = derived_status(feat)
        if new == feat["status"]:
            continue
        set_status(feat["path"], new, today)
        if feat["status"] == "validated":
            append_history(feat["path"], f"- {today} status: validated -> in-progress (reopened: "
                                         f"{', '.join(open_rows(feat))})")
        else:
            append_history(feat["path"], f"- {today} status: {feat['status']} -> in-progress "
                                         f"({', '.join(started_rows(feat))})")
        changed.append(f"{fid}: {feat['status']} -> {new}")
    return changed


def release_mode(spec_dir):
    """The project's `sdd: release` from spec.md (KIT-067), `merge` when absent."""
    path = spec_dir / "spec.md"
    data = split_frontmatter(path.read_text(encoding="utf-8"))[0] if path.exists() else None
    sdd = data.get("sdd") if isinstance(data, dict) else None
    return sdd.get("release", "merge") if isinstance(sdd, dict) else "merge"


def load_needs(spec_dir):
    """Every NEED file, settled or open: NEED id -> (path, frontmatter)."""
    needs = {}
    for path in sorted((spec_dir / "needs").glob("NEED-*.md")):
        data, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("id"):
            needs[str(data["id"])] = (path, data)
    return needs


CLOSURE_LINE = re.compile(r"^- \d{4}-\d{2}-\d{2} (sdd-review|sdd-release): (validated|delivered)\b", re.M)
LEGACY_DELIVERED = re.compile(r"^- \d{4}-\d{2}-\d{2} delivered before sdd-review\b", re.M)


def has_history_line(path, status):
    """True when the FEAT's History holds the line check_spec.py requires for `status` (rule feature-closure)."""
    match = re.search(r"(?ms)^## History[ \t]*$(.*?)(?=^## |\Z)", path.read_text(encoding="utf-8"))
    history = match.group(1) if match else ""
    marks = {m.groups() for m in CLOSURE_LINE.finditer(history)}
    if status == "validated":
        return ("sdd-review", "validated") in marks
    return bool(marks & {("sdd-release", "delivered"), ("sdd-review", "delivered")} or LEGACY_DELIVERED.search(history))


def has_closure(path):
    """True when the FEAT's `## Closure` section holds a line outside HTML comments."""
    text = re.sub(r"(?s)<!--.*?-->", "", path.read_text(encoding="utf-8"))
    match = re.search(r"(?ms)^## Closure[ \t]*$(.*?)(?=^## |\Z)", text)
    return bool(match and match.group(1).strip())


def closure_gaps(spec, fid, needs):
    """What keeps sdd-review from closing the FEAT: open rows, no closure record, unfilled journey steps."""
    feat = spec.feats[fid]
    gaps = [] if feat["task_status"] else [f"{fid} has no task row with a Status cell"]
    gaps += [f"{fid} {tid} is {state}: every row is done before sdd-review"
             for tid, state in feat["task_status"].items() if state not in ROW_CLOSED]
    if not has_closure(feat["path"]):
        gaps.append(f"{fid} has no `## Closure` record: sdd-review writes it before validate")
    for nid, (_, need) in needs.items():
        if fid not in listed(need, "features"):
            continue
        seen = set()

        def unfilled(step, via):
            missing = [c for c, ok in (("Implemented by", step.tasks), ("Proven by", step.tests or step.manual))
                       if not ok]
            if missing and not step.id.startswith("P") and step.ref not in seen:
                seen.add(step.ref)
                gaps.append(f"{step.ref}: {' and '.join(missing)} still `{PENDING}`; {nid}, which lists {fid}, "
                            f"lists {via}")

        for jid in listed(need, "journeys"):
            journey = spec.journeys.get(jid)
            if journey is None:
                gaps.append(f"{nid} lists {jid}, which has no journey file")
                continue
            for step in journey["steps"]:
                if step.cites:  # a step that cites a process is filled when the steps it expands to are
                    for cited in step.expands:
                        unfilled(cited, f"{jid} ({step.ref} cites it)")
                else:
                    unfilled(step, jid)
        for pid in listed(need, "processes"):
            process = spec.processes.get(pid)
            if process is None:
                gaps.append(f"{nid} lists {pid}, which has no process file")
                continue
            for step in process["steps"]:
                unfilled(step, pid)
    return gaps


def deliver_needs(spec, fid, step, today, needs):
    """Move each open NEED that lists fid, and whose FEATs are now all delivered and cover its REQs, to delivered."""
    spec.feats[fid]["status"] = "delivered"
    moved = []
    for nid, (path, need) in needs.items():
        if fid in listed(need, "features") and need.get("status") not in NEED_SETTLED \
                and delivered_by_its_feats(spec, need):
            set_status(path, "delivered", today)
            append_history(path, f"- {today} {step}: delivered ({', '.join(listed(need, 'features'))})")
            moved.append(f"{nid}: {need.get('status')} -> delivered")
    return moved


def validate(spec, fid, ref, today, check_only):
    """sdd-review's status move; returns the exit code."""
    feat = spec.feats.get(fid)
    if feat is None:
        raise SystemExit(f"{fid} is not a FEAT in {spec.spec_dir}")
    mode = release_mode(spec.spec_dir)
    target = "delivered" if mode == "merge" else "validated"
    already = feat["status"] == target
    if already and has_history_line(feat["path"], target):
        print(f"{fid} is already {target}")
        return 0
    if not already and feat["status"] not in VALIDATE_FROM:
        return report([f"{fid} is {feat['status']}: sdd-review validates a FEAT that is "
                       f"{', '.join(VALIDATE_FROM)}"], "")
    needs = load_needs(spec.spec_dir)
    gaps = closure_gaps(spec, fid, needs)
    if gaps or check_only:
        return report(gaps, f"{fid}: ready to validate ({target} under release: {mode})")
    suffix = " (release: merge)" if target == "delivered" else ""
    if already:
        append_history(feat["path"], f"- {today} sdd-review: {target} at {ref}{suffix}")
        print(f"{fid}: already {target} without its History line; added it (sdd-review at {ref})")
        return 0
    set_status(feat["path"], target, today)
    append_history(feat["path"], f"- {today} sdd-review: {target} at {ref}{suffix}")
    print(f"{fid}: {feat['status']} -> {target} (sdd-review at {ref}, release: {mode})")
    for line in deliver_needs(spec, fid, "sdd-review", today, needs) if target == "delivered" else []:
        print(line)
    return 0


NUMBER_WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                "eleven": 11, "twelve": 12}
ROW_COUNT = re.compile(r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\s+(?:task\s+)?rows\b", re.I)
CONDITIONAL = re.compile(r"\b(until|once)\s+(?:(FEAT-\d{3,})\s+)?(T\d+)\b", re.I)


def sections(body):
    """{heading: text} of a markdown body split on `## ` headings, HTML comments removed."""
    out, current = {}, None
    for line in re.sub(r"(?s)<!--.*?-->", "", body).splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def proving_tokens(path):
    """The tests a REQ's `Proving test` line names: backticked names reduced to their stem, else task refs."""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^- Proving test:(.*?)(?=^- |^#|\Z)", text)
    if not match:
        return []
    spans = BACKTICKED.findall(match.group(1))
    if spans:
        return [Path(span.split()[0]).name.split(".")[0] for span in spans if span.split()]
    return TASK_REF.findall(match.group(1))


SENTENCE_END = re.compile(r"[.!?;)\]`'\"»]\s*$")  # a colon introduces the bullet's continuation, so it ends nothing


# The one-line History bullets this tool writes: complete as written, though some end on a sha, a version or a row id.
TOOL_LINE = re.compile(r"^- \d{4}-\d{2}-\d{2} (sdd-review: (validated|delivered) at \S+( \(release: merge\))?"
                       r"|sdd-release: delivered in \S+|done: T\d+( \([^()]*\))?|delivered before sdd-review"
                       r"|status: validated -> in-progress \(reopened: [^()]*\)|[\w-]+: delivered \([^()]*\))\s*$")


def complete(line):
    return bool(SENTENCE_END.search(line) or TOOL_LINE.match(line))


def history_splits(fid, history):
    """A History bullet that stops mid-sentence, then one or more complete bullets (each ends a sentence or is a line
    this tool writes), then an indented line: those bullets were inserted inside the first one (the calibration's
    FEAT-097; consumer FEAT-004 and FEAT-021 hold several). An incomplete bullet before the indented line owns it, so a
    one-line bullet merely left unterminated is not flagged (consumer FEAT-030 at d23561cba)."""
    lines, found = history.splitlines(), []
    for i, first in enumerate(lines):
        if not first.startswith("- ") or complete(first):
            continue
        j = i + 1
        while j < len(lines) and lines[j].startswith("- ") and complete(lines[j]):
            j += 1
        n = j - i - 1
        if n and j < len(lines) and lines[j].startswith((" ", "\t")) and lines[j].strip():
            found.append(f"{fid}: History bullet '{first[:48].strip()}…' is split by "
                         f"{'the line' if n == 1 else f'{n} lines'} inserted after it ('{lines[i + 1][:48].strip()}…'): "
                         f"move {'that line' if n == 1 else 'them'} below the bullet's last line")
    return found


def lint_feat(spec, fid):
    """Stale markers and trace gaps on one FEAT."""
    feat = spec.feats[fid]
    _, body = split_frontmatter(feat["path"].read_text(encoding="utf-8"))
    secs, found = sections(body), []
    for title, text in secs.items():
        for line in text.splitlines():
            if "Not verified" in line:
                found.append(f"{fid}: 'Not verified' left in {title}: {line.strip()}")
    if re.search(r"\bpending\b", secs.get("Audit", ""), re.I):
        found.append(f"{fid}: Audit still says Pending")
    found += [f"{fid}: [PROPOSAL] in Scope: {line.strip()}" for line in secs.get("Scope", "").splitlines()
              if "[PROPOSAL]" in line]
    found += [f"{fid}: [HYPOTHESIS] in Open questions: {line.strip()}"
              for line in secs.get("Open questions", "").splitlines() if "[HYPOTHESIS]" in line]
    found += history_splits(fid, secs.get("History", ""))
    found += [f"{fid}: [HYPOTHESIS] in done row {tid}" for tid, row in feat["tasks"].items()
              if "[HYPOTHESIS]" in row and feat["task_status"].get(tid) in ROW_CLOSED]
    for title, text in secs.items():
        if title == "History":
            continue
        for m in CONDITIONAL.finditer(text):
            other = spec.feats.get(m.group(2) or fid, {})
            state = other.get("task_status", {}).get(m.group(3))
            if state in ROW_CLOSED:
                found.append(f"{fid}: '{m.group(1)} {m.group(3)}' but {m.group(3)} is {state} ({title}): rewrite it as "
                             "the current fact or delete it")
    for m in ROW_COUNT.finditer(secs.get("Plan", "")):
        said = int(m.group(1)) if m.group(1).isdigit() else NUMBER_WORDS[m.group(1).lower()]
        if said != len(feat["tasks"]):
            found.append(f"{fid}: Plan says {said} rows, the task table has {len(feat['tasks'])}")
    if spec.journeys or spec.processes:
        for rid in feat["requirements"]:
            if rid not in spec.reqs:
                continue
            cell = tests_of([s for s in spec.all_steps if rid in s.rules])
            for token in proving_tokens(spec.reqs[rid]["path"]):
                if cell == "—":
                    found.append(f"{rid}: its trace row lists no test (proving test {token}, {fid})")
                    break
                if token not in cell:
                    found.append(f"{rid}: proving test {token} is not in its trace row ({cell})")
    return found


def lint(spec, fid):
    """The closure lint on fid, or on every validated or delivered FEAT; returns the exit code."""
    if fid and fid not in spec.feats:
        raise SystemExit(f"{fid} is not a FEAT in {spec.spec_dir}")
    targets = [fid] if fid else [f for f, feat in spec.feats.items() if feat["status"] in STATUS_CLOSED]
    found = [line for target in targets for line in lint_feat(spec, target)]
    return report(found, f"spec-trace lint: OK ({len(targets)} FEATs)")


def deliver(spec, fid, ref, today):
    """sdd-release's status move; returns the exit code."""
    feat = spec.feats.get(fid)
    if feat is None:
        raise SystemExit(f"{fid} is not a FEAT in {spec.spec_dir}")
    if feat["status"] == "delivered":
        print(f"{fid} is already delivered")
        return 0
    if feat["status"] != "validated":
        return report([f"{fid} is {feat['status']}: sdd-review validates it first (spec_trace.py validate)"], "")
    set_status(feat["path"], "delivered", today)
    append_history(feat["path"], f"- {today} sdd-release: delivered in {ref}")
    print(f"{fid}: validated -> delivered (sdd-release in {ref})")
    for line in deliver_needs(spec, fid, "sdd-release", today, load_needs(spec.spec_dir)):
        print(line)
    return 0


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
    feat["path"].write_text(text.replace(old, "|".join(pieces), 1), encoding="utf-8")
    append_history(feat["path"], f"- {today} done: {tid}" + (f" ({pr})" if pr else ""))
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
            found.append((f"{stem} edited", [s for s in spec.all_steps if stem in s.rules]))
        elif re.fullmatch(r"FEAT-\d{3,}", stem):
            found += feat_changes(spec, base, head, stem, path)
        elif JOURNEY_FILE.match(stem):
            jid = JOURNEY_FILE.match(stem).group(1)
            found.append((f"{jid} edited", spec.journeys.get(jid, {}).get("steps", [])))
        elif PROCESS_FILE.match(stem):
            pid = PROCESS_FILE.match(stem).group(1)
            found.append((f"{pid} edited", spec.processes.get(pid, {}).get("steps", [])
                          + [s for s in spec.steps if s.cites == pid]))
    return found


def feat_changes(spec, base, head, fid, path):
    old_data, old_body = split_frontmatter(file_at(spec.root, base, path))
    new_data, new_body = split_frontmatter(file_at(spec.root, head, path))
    old_rows, new_rows = task_rows(old_body), task_rows(new_body)
    found = []
    for tid in sorted(set(old_rows) | set(new_rows), key=natural_key):
        if old_rows.get(tid) != new_rows.get(tid):
            ref = f"{fid} {tid}"
            found.append((f"{ref} row edited", [s for s in spec.all_steps if ref in s.tasks or ref in s.tests]))
    outside = [line for line in old_body.splitlines() if not TASK_ROW.match(line)]
    if outside != [line for line in new_body.splitlines() if not TASK_ROW.match(line)] or \
            (old_data or {}).get("requirements") != (new_data or {}).get("requirements"):
        steps = [s for s in spec.all_steps if any(t.startswith(fid + " ") for t in s.tasks + s.tests)]
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


def task_status(spec, ref):
    fid, tid = ref.split(" ")
    return spec.feats.get(fid, {}).get("task_status", {}).get(tid, "unknown")


def cell(text):
    return (text or "—").replace("|", "\\|").replace("\n", "<br>")


def render_checklist(spec, jid):
    j = spec.journeys[jid]
    rel = j["path"].relative_to(spec.root).as_posix()
    lines = [f"# {jid} — {j['title']}", "",
             f"Generated from `{rel}` by `spec_trace.py checklist`; steps are not hand-edited.", ""]
    if j["stage"]:
        lines += [f"Stage: {j['stage']}", ""]
    lines += ["## Preconditions", "", j["preconditions"], "", "## Steps", "",
              "| Step | At | Do and expect | Rules | Automated proof | Manual check | "
              "Evidence (date, build, version, result) |", "|---|---|---|---|---|---|---|"]
    for s in j["steps"]:
        if s.id.startswith("P"):
            continue
        rules = "<br>".join(f"{r} — {spec.reqs[r]['title']}" for r in s.rules)
        lines.append("| " + " | ".join([s.id, cell(s.at), cell(s.action), cell(rules),
                                        cell("<br>".join(s.tests)), cell(s.manual), ""]) + " |")
    lines += ["", "## Prerequisites", "", "| Step | Needs | Task | Status |", "|---|---|---|---|"]
    for s in (s for s in j["steps"] if s.id.startswith("P")):
        lines.append("| " + " | ".join([s.id, cell(s.action), cell("<br>".join(s.tasks)),
                                        cell("<br>".join(task_status(spec, t) for t in s.tasks))]) + " |")
    return "\n".join(lines) + "\n"


def checklist(spec, ids, out, force):
    """One checklist per approved journey, in id order; any error of those journeys fails before writing."""
    ids = sorted(set(ids), key=natural_key)
    errors = []
    for jid in ids:
        j = spec.journeys.get(jid)
        if j is None:
            errors.append(f"{jid}: unknown journey")
            continue
        if j["status"] != "approved":
            errors.append(f"{jid}: status is {j['status']!r}, only approved journeys have a checklist")
        rel = j["path"].relative_to(spec.root).as_posix()
        errors += [e for e in spec.errors if e.startswith((f"{jid} ", f"{jid}:", rel))]
    if not errors and out and Path(out).exists() and not force:
        errors.append(f"{out} exists; pass --force to overwrite it")
    if errors:
        return report(errors, "")
    text = "\n".join(render_checklist(spec, jid) for jid in ids)
    if out:
        Path(out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


# --------------------------------------------------------------------------- sync-status (KIT-073)


def origin_repo(root: Path):
    shown = git(root, "remote", "get-url", "origin")
    m = REMOTE.search(shown.stdout.strip()) if shown.returncode == 0 else None
    return m.group(1) if m else None


def github_settings(spec_dir: Path, repo: str | None = None) -> dict:
    """`sdd.github` resolved: the backlog repository (`repo`, else the origin remote), the PR repositories, earlier
    names and labels."""
    params, _ = load_params(Path(spec_dir).resolve())
    settings = dict(params.get("github") or {})
    settings["repo"] = repo or settings.get("repo") or origin_repo(repo_root(Path(spec_dir).resolve()))
    for key, default in (("pr_repos", []), ("aliases", []), ("blocked_labels", ["blocked"]),
                         ("progress_labels", ["status:in-progress"])):
        settings[key] = list(settings.get(key) or default)
    return settings


def run_gh(*args):
    """One `gh api` REST call (GraphQL and `--paginate` fail through some proxies)."""
    return subprocess.run(["gh", "api", *args], capture_output=True, text=True)


class SyncError(RuntimeError):
    """sync-status cannot run: a `gh` call failed or no backlog repository is known. main() exits 2 (#267)."""


def gh_json(query, gh=run_gh):
    res = gh(query)
    if res.returncode != 0:
        raise SyncError(f"gh api {query} failed: {res.stderr.strip()}")
    try:
        return json.loads(res.stdout)
    except ValueError as error:
        raise SyncError(f"gh api {query} returned no JSON: {error}")


def gh_paged(query, gh=run_gh):
    """All pages of a REST list, `&page=N` by hand until an empty page."""
    sep = "&" if "?" in query else "?"
    out, page = [], 1
    while True:
        chunk = gh_json(f"{query}{sep}per_page=100&page={page}", gh)
        if not chunk:
            return out
        out += chunk
        page += 1


def bundle_members(issue: dict) -> list:
    """The primary row and the members a ` — bundled with ` title suffix records, in that order: `FEAT-nnn Tn #N`
    members, or bare `#N` numbers for a bundle with no rows."""
    title = issue.get("title") or ""
    own = re.match(r"^\[(FEAT-\d{3,}) (T\d+)\]", title)
    _, sep, suffix = title.partition(" — bundled with ")
    if not sep:
        return []
    if re.fullmatch(r"#\d+(?:, #\d+)*", suffix):
        head = (own[1], own[2], int(issue["number"])) if own else (None, None, int(issue["number"]))
        refs = [head] + [(None, None, int(n)) for n in re.findall(r"#(\d+)", suffix)]
        return refs if len({n for _, _, n in refs}) == len(refs) else []
    if not own or not re.fullmatch(r"FEAT-\d{3,} T\d+ #\d+(?:, FEAT-\d{3,} T\d+ #\d+)*", suffix):
        return []
    members = re.findall(r"\b(FEAT-\d{3,}) (T\d+) #(\d+)\b", suffix)
    refs = [(own[1], own[2], int(issue["number"]))] + [(f, tid, int(n)) for f, tid, n in members]
    return refs if len({n for _, _, n in refs}) == len(refs) else []


def issue_sections(body):
    out, current = {}, None
    for line in (body or "").splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            current = m.group(1)
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def bundle_redirects(issues: list) -> dict:
    """A member closed as not planned follows its bundle when its title names the member row and its `## Repository`
    section equals the bundle's; never an unrelated closed issue."""
    by_number = {i["number"]: i for i in issues}
    out = {}
    for primary in issues:
        for feat, tid, n in bundle_members(primary)[1:]:
            member = by_number.get(n, {})
            reason = member.get("stateReason", member.get("state_reason", "")) or ""
            named = feat is None or (member.get("title") or "").startswith(f"[{feat} {tid}]")
            if (member.get("state", "").lower() == "closed" and reason.lower() == "not_planned" and named
                    and issue_sections(member.get("body")).get("Repository") ==
                    issue_sections(primary.get("body")).get("Repository")):
                out[n] = primary
    return out


def task_issues(repo, gh=run_gh):
    """(`{'FEAT-NNN Tn': [record, ...]}` by issue title, `{number: record}` for every issue), each record
    {number, state, reason, labels[, bundle]}: a fix round may keep the title, so a row can have several issues; a
    row's Item cell reads the second map."""
    found, by_number = {}, {}
    items = [i for i in gh_paged(f"repos/{repo}/issues?state=all", gh) if "pull_request" not in i]
    redirects = bundle_redirects(items)
    for item in items:
        primary = redirects.get(item["number"])
        effective = primary or item
        record = {"number": item["number"], "state": effective["state"],
                  "reason": (effective.get("state_reason") or effective.get("stateReason") or "").lower(),
                  "labels": [lb["name"] for lb in effective.get("labels") or []]}
        if primary:
            record["bundle"] = primary["number"]
        by_number[item["number"]] = record
        m = ISSUE_TITLE.match(item.get("title") or "")
        if m:
            for tid in m.group(2).split("+"):
                found.setdefault(f"{m.group(1)} {tid}", []).append(record)
    return found, by_number


def item_issue(cell, settings):
    """The backlog issue number a row's Item cell names (`#N`, or `OWNER/NAME#N` of the backlog repository or one of
    its earlier names), else None (`—`, a TASK file, another repository)."""
    m = re.fullmatch(r"([\w.-]+/[\w.-]+)?#(\d+)", (cell or "").strip())
    if not m or (m.group(1) and m.group(1) not in {settings["repo"], *settings["aliases"]}):
        return None
    return int(m.group(2))


def merge_issues(group):
    """One view of a row's issues: any open issue means open, and only open issues lend their labels (a closed
    issue's stale `blocked` says nothing about the open one); closed as not planned only when every one is."""
    closed = [i for i in group if i["state"] != "open"]
    return {"number": group[0]["number"], "labels": sorted({lb for i in group if i["state"] == "open"
                                                            for lb in i["labels"]}),
            "state": "open" if len(closed) < len(group) else "closed",
            "reason": "not_planned" if closed and all(i["reason"] == "not_planned" for i in closed) else ""}


def closing_prs(settings, gh=run_gh):
    """`{issue number: [{ref, state, merged}]}` from one paged `pulls?state=all` listing per repository: a PR body's
    `Closes <backlog or earlier name>#N`, and `Closes #N` inside the backlog repository only."""
    repo = settings["repo"]
    pr_repos = [repo, *[r for r in settings["pr_repos"] if r != repo]]
    aliases = {repo, *settings["aliases"]}
    full = re.compile(r"Closes\s+(?:" + "|".join(re.escape(name) for name in sorted(aliases)) + r")#(\d+)\b")
    short = re.compile(r"Closes\s+#(\d+)\b")
    with ThreadPoolExecutor(max_workers=len(pr_repos)) as pool:
        listings = list(pool.map(lambda r: gh_paged(f"repos/{r}/pulls?state=all", gh), pr_repos))
    out = {}
    for pr_repo, pulls in zip(pr_repos, listings):
        for pr in pulls:
            body = pr.get("body") or ""
            numbers = {int(n) for n in full.findall(body)}
            if pr_repo == repo:
                numbers |= {int(n) for n in short.findall(body)}
            for number in numbers:
                out.setdefault(number, []).append({"ref": f"{pr_repo.split('/')[-1]}#{pr['number']}",
                                                   "state": pr.get("state"), "merged": pr.get("merged_at") is not None})
    return out


def derive_task_status(current, issue, prs, settings):
    """(new status, refs or reasons, warn?): the GitHub state of one row; the first match wins."""
    if current in ROW_FROZEN:
        return current, [], False
    if issue is None:
        return current, ["no issue"], False
    merged = sorted({p["ref"] for p in prs if p["merged"]}, key=natural_key)
    if merged:
        return "done", merged, False
    if issue["state"] == "closed":  # before any label: a closed issue may keep a stale blocked or progress label
        if issue["reason"] == "not_planned" and current == "done":  # a recorded delivery outranks a stray issue
            return current, ["closed as not planned, but the row is done"], True
        if issue["reason"] == "not_planned":
            return "cancelled", ["closed as not planned"], False
        return current, ["closed without a merged PR"], True
    labels = set(issue["labels"])
    blocked = labels & set(settings["blocked_labels"])
    if blocked:
        return "blocked", [f"label:{lb}" for lb in sorted(blocked)], False
    open_prs = sorted({p["ref"] for p in prs if p["state"] == "open"}, key=natural_key)
    progress = labels & set(settings["progress_labels"])
    if open_prs or progress:
        return "doing", open_prs or [f"label:{lb}" for lb in sorted(progress)], False
    return "todo", [], False


def sync_status(spec, settings, write, today, gh=run_gh):
    """Each row's Status and each FEAT's status from GitHub; with `write`, written to the files."""
    repo = settings["repo"]
    if not repo:
        raise SyncError("no backlog repository: set sdd.github.repo, pass --backlog or add an origin remote on GitHub")
    with ThreadPoolExecutor(max_workers=2) as pool:
        issues_job = pool.submit(task_issues, repo, gh)
        closing = closing_prs(settings, gh)
        issues, by_number = issues_job.result()
    lines, changed = [], {}
    for fid in sorted(spec.feats, key=natural_key):
        feat = spec.feats[fid]
        for tid in sorted(feat["task_status"], key=natural_key):
            key = f"{fid} {tid}"
            number = item_issue(feat.get("task_item", {}).get(tid), settings)
            group = [by_number[number]] if number in by_number else issues.get(key, [])
            if len(group) > 1:
                lines.append(f"WARN {key}: task issues " + ", ".join(f"#{i['number']}" for i in group)
                             + " — evidence merged")
            issue = merge_issues(group) if group else None
            prs = [p for i in group for n in {i["number"], i.get("bundle", i["number"])} for p in closing.get(n, [])]
            current = feat["task_status"][tid]
            new, via, warn = derive_task_status(current, issue, prs, settings)
            if warn:
                lines.append(f"WARN {key}: {repo.split('/')[-1]}#{issue['number']} {via[0]}")
            elif via == ["no issue"]:
                lines.append(f"{key}: {current} (no issue)")
            if new != current:
                feat["task_status"][tid] = new
                changed.setdefault(fid, []).append((tid, current, new, via))
                lines.append(f"{key}: {current} -> {new}" + (f" ({', '.join(via)})" if via else ""))
        new_status = derived_status(feat)
        if new_status != feat["status"]:
            lines.append(f"{fid}: {feat['status']} -> {new_status}")
            feat["sync_status"] = new_status
    if not write:
        print("\n".join(lines) or "sync-status: everything already derived")
        return 0
    written = apply_sync(spec, changed, today)
    print("\n".join(lines))
    print(f"sync-status: wrote {written} file(s)")
    return 0


def task_header(body):
    """The cells of the task-table header (the `| ID |` table with a `Status` column), or None."""
    for line in body.splitlines():
        if line.startswith("| ID |"):
            header = row_cells(line)
            if "Status" in header:
                return header
    return None


def rewrite_frontmatter(text, status, today):
    """Set `status` (unless None) and `updated` in the raw frontmatter, never a YAML round trip."""
    head, sep, rest = text.partition("\n---\n")
    if status:
        head = re.sub(r"(?m)^status:.*$", f"status: {status}", head, count=1)
    if re.search(r"(?m)^updated:", head):
        head = re.sub(r"(?m)^updated:.*$", f'updated: "{today}"', head, count=1)
    elif status:
        head = re.sub(r"(?m)^(status:.*)$", rf'\1\nupdated: "{today}"', head, count=1)
    return head + sep + rest


def apply_sync(spec, changed, today):
    """Write the derived status into the FEAT files, traceability.md and spec.md; return the file count."""
    written = 0
    fids = set(changed) | {f for f, ft in spec.feats.items() if "sync_status" in ft}
    for fid in sorted(fids, key=natural_key):
        feat = spec.feats[fid]
        text = feat["path"].read_text(encoding="utf-8")
        header = task_header(split_frontmatter(text)[1])
        for tid, old, new, via in changed.get(fid, []):
            line = feat["tasks"][tid]
            if len(row_cells(line)) != len(header):
                raise SystemExit(f"{fid} {tid}: row has not the header's cell count; refusing to write")
            pieces = UNESCAPED_PIPE.split(line)
            pieces[header.index("Status") + 1] = f" {new} "
            text = text.replace(line, "|".join(pieces), 1)
        new_status = feat.get("sync_status")
        if new_status and new_status != feat["status"]:
            feat["status"] = new_status
        feat["path"].write_text(rewrite_frontmatter(text, new_status, today), encoding="utf-8")
        if fid in changed:
            detail = "; ".join(f"{tid} {old} -> {new}" + (f" via {', '.join(via)}" if via else "")
                               for tid, old, new, via in changed[fid])
            append_history(feat["path"], f"- {today} sync: status derived from GitHub ({detail}).")
        written += 1
    matrix = spec.spec_dir / MATRIX
    if spec.journeys or spec.processes or matrix.exists():
        rendered = render_matrix(spec)
        if not matrix.exists() or matrix.read_text(encoding="utf-8") != rendered:
            matrix.write_text(rendered, encoding="utf-8")
            written += 1
    return written + (1 if sync_index(spec, today) else 0)


def id_ranges(ids):
    """['FEAT-005', 'FEAT-006', 'FEAT-007', 'FEAT-009'] -> ['FEAT-005–FEAT-007', 'FEAT-009']: a run of three or more
    consecutive numbers collapses to a range."""
    out, run = [], []

    def flush():
        out.extend([f"{run[0]}–{run[-1]}"] if len(run) > 2 else run)

    for fid in sorted(ids, key=natural_key):
        number = int(re.sub(r"\D", "", fid) or 0)
        if run and number != int(re.sub(r"\D", "", run[-1]) or 0) + 1:
            flush()
            run = []
        run.append(fid)
    if run:
        flush()
    return out


def counts_line(spec):
    """`N FEATs: n `status`, …` in lifecycle order, zero counts left out, the proposed and cancelled FEATs named."""
    by_status = {}
    for fid in sorted(spec.feats, key=natural_key):
        by_status.setdefault(str(spec.feats[fid]["status"]), []).append(fid)
    order = list(FEAT_STATUSES) + sorted(s for s in by_status if s not in FEAT_STATUSES)
    parts = [f"{len(by_status[s])} `{s}`" + (f" ({', '.join(id_ranges(by_status[s]))})" if s in COUNTS_LISTED else "")
             for s in order if s in by_status]
    total = len(spec.feats)
    return f"{total} FEAT{'' if total == 1 else 's'}" + (": " + ", ".join(parts) if parts else "") + "."


def sync_index(spec, today):
    """spec.md: the Status cell of each FEAT row (a table row linking features/FEAT-nnn under a header with a Status
    column), the sync-status block (the in-progress FEATs with their done rows) and the sync-counts block (the FEAT
    counts per status, `counts_line`); a block is written only where its markers are."""
    path = spec.spec_dir / "spec.md"
    if not path.exists():
        return False
    original = path.read_text(encoding="utf-8")
    lines, column = original.split("\n"), None
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            column = None
            continue
        cells = row_cells(line)
        if "Status" in cells and column is None:
            column = cells.index("Status")
            continue
        m = re.match(r"^\[(FEAT-\d{3,})\]\(features/", cells[0]) if cells else None
        if column is None or not m or m.group(1) not in spec.feats or len(cells) <= column:
            continue
        status = spec.feats[m.group(1)]["status"]
        if cells[column] != status:
            pieces = UNESCAPED_PIPE.split(line)
            pieces[column + 1] = f" {status} "
            lines[i] = "|".join(pieces)
    text = "\n".join(lines)
    if SYNC_BEGIN in text and SYNC_END in text:
        listing = []
        for fid in sorted(spec.feats, key=natural_key):
            feat = spec.feats[fid]
            if feat["status"] == "in-progress":
                done = sum(1 for s in feat["task_status"].values() if s == "done")
                listing.append(f"- {fid} {feat['title']} ({done}/{len(feat['task_status'])} done)")
        block = SYNC_BEGIN + "\n" + ("\n".join(listing) or "- none") + "\n" + SYNC_END
        text = re.sub(re.escape(SYNC_BEGIN) + ".*?" + re.escape(SYNC_END), lambda _: block, text, count=1,
                      flags=re.DOTALL)
    if COUNTS_BEGIN in text and COUNTS_END in text:
        block = COUNTS_BEGIN + "\n" + counts_line(spec) + "\n" + COUNTS_END
        text = re.sub(re.escape(COUNTS_BEGIN) + ".*?" + re.escape(COUNTS_END), lambda _: block, text, count=1,
                      flags=re.DOTALL)
    if text == original:
        return False
    path.write_text(rewrite_frontmatter(text, None, today), encoding="utf-8")
    return True


def report(errors, ok_message):
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    if errors:
        return 1
    print(ok_message)
    return 0


DEFAULT_SPEC = Path("docs/spec")
SPEC_HELP = "the spec directory (default: docs/spec under the working directory)"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", action="append", default=[], metavar="NAME",
                        help="extra clone name a `Proven by` test path may be rooted at "
                             "(repeatable; for clones CI does not check out)")
    parser.add_argument("--date", default=None, help="date for History and `updated` (default: today)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "generate"):
        sub.add_parser(name).add_argument("spec", type=Path, nargs="?", help=SPEC_HELP)
    status = sub.add_parser("status")
    status.add_argument("spec", type=Path, nargs="?", help=SPEC_HELP)
    status.add_argument("--write", action="store_true")
    impact = sub.add_parser("impact")
    impact.add_argument("spec", type=Path, nargs="?", help=SPEC_HELP)
    impact.add_argument("base")
    impact.add_argument("head")
    done = sub.add_parser("mark-done")
    done.add_argument("spec", type=Path, nargs="?", help=SPEC_HELP)
    done.add_argument("feat")
    done.add_argument("task")
    done.add_argument("--pr", help="merged task PR as <repo>#<n>")
    closing = sub.add_parser("validate")
    closing.add_argument("spec", type=Path, nargs="?", help=SPEC_HELP)
    closing.add_argument("feat")
    closing.add_argument("--at", required=True, help="the main commit sdd-review ran the closure on")
    closing.add_argument("--check", action="store_true", help="report the gaps only; write nothing")
    release = sub.add_parser("deliver")
    release.add_argument("spec", type=Path, nargs="?", help=SPEC_HELP)
    release.add_argument("feat")
    release.add_argument("--in", dest="version", required=True, help="the release that delivered it")
    linting = sub.add_parser("lint")
    linting.add_argument("spec", type=Path, nargs="?", help=SPEC_HELP)
    linting.add_argument("feat", nargs="?", help="the FEAT to lint (default: every validated or delivered one)")
    sync = sub.add_parser("sync-status", help="row and FEAT status from GitHub (sdd.tracker: github)")
    sync.add_argument("spec", type=Path, nargs="?", help=SPEC_HELP)
    sync.add_argument("--write", action="store_true")
    sync.add_argument("--backlog", metavar="OWNER/NAME", help="the backlog repository (default: sdd.github.repo, "
                                                               "else the origin remote)")
    enb = sub.add_parser("enablers", help="sdd-check C18 and C19 over the ENBs (KIT-095)")
    enb.add_argument("spec", type=Path, nargs="?", help=SPEC_HELP)
    enb.add_argument("--feat", metavar="FEAT-NNN", help="one FEAT's scope (default: every open FEAT)")
    enb.add_argument("--catalog", action="append", default=[], metavar="GLOB",
                     help="files the catalog must cover, rooted at the repository (repeatable; a migration folder)")
    chk = sub.add_parser("checklist", help="owner checklist of approved journeys, to stdout")
    chk.add_argument("spec", type=Path, nargs="?", help=SPEC_HELP)
    chk.add_argument("journeys", nargs="*", metavar="J-NN")
    chk.add_argument("--out", help="write the checklist to FILE instead of stdout")
    chk.add_argument("--force", action="store_true", help="overwrite --out when it exists")
    args = parser.parse_args(argv)
    today = args.date or datetime.date.today().isoformat()
    if args.spec is not None and re.fullmatch(r"J-\d{2,}", str(args.spec)) and args.command == "checklist":
        args.journeys, args.spec = [str(args.spec), *args.journeys], None
    if args.spec is not None and re.fullmatch(r"FEAT-\d{3,}", str(args.spec)) and args.command == "lint":
        args.feat, args.spec = str(args.spec), None
    spec_dir = args.spec or DEFAULT_SPEC
    if not spec_dir.is_dir():
        return report([f"spec dir does not exist: {spec_dir}"], "")

    spec = load(spec_dir, args.repo)
    matrix = spec.spec_dir / MATRIX
    summary = f"spec-trace: OK ({len(spec.journeys)} journeys, {len(spec.steps)} steps, {len(spec.reqs)} REQs)"
    if spec.processes:
        summary = (f"spec-trace: OK ({len(spec.journeys)} journeys, {len(spec.processes)} processes, "
                   f"{len(spec.all_steps)} steps, {len(spec.reqs)} REQs)")
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
    if args.command == "sync-status":
        if spec.param_errors:
            print("FAIL: spec.md sdd block refused (check_spec.py --params): " + "; ".join(spec.param_errors),
                  file=sys.stderr)
            return 2
        if spec.params.get("tracker", "github") != "github":
            print(f"FAIL: sync-status reads GitHub issues, and sdd.tracker is {spec.params.get('tracker')}: task "
                  "status lives in the TASK files", file=sys.stderr)
            return 2
        try:
            return sync_status(spec, github_settings(spec.spec_dir, args.backlog), args.write, today)
        except SyncError as error:
            print(f"FAIL: sync-status: {error}", file=sys.stderr)
            return 2
    if args.command == "checklist":
        if not args.journeys:
            return report(["checklist needs one or more journey ids (J-NN)"], "")
        return checklist(spec, args.journeys, args.out, args.force)
    if args.command == "validate":
        return validate(spec, args.feat, args.at, today, args.check)
    if args.command == "deliver":
        return deliver(spec, args.feat, args.version, today)
    if args.command == "lint":
        return lint(spec, args.feat)
    if args.command == "enablers":
        return enablers_command(spec, args.feat, args.catalog)
    if args.command == "impact":
        print(render_impact(changes(spec, args.base, args.head)), end="")
        return 0
    return report(check(spec), summary)


if __name__ == "__main__":
    sys.exit(main())
