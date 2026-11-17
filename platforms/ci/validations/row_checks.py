#!/usr/bin/env python3
"""Task-row checks before the cut (KIT-073): rules a-k of sdd-tasks/references/row-checks.md, driven by the
project's `sdd:` block in docs/spec/spec.md.

    row_checks.py check [--spec DIR] FEAT-NNN ... | --all | --changed BASE HEAD [--all-rows] [--strict]

`--spec` defaults to docs/spec under the working directory; a FEAT-NNN id names <spec>/features/FEAT-NNN.md, a path
names that file. Only rows that are not settled (todo, or a Status the kit does not know) are checked unless
--all-rows; --strict turns the c and f warnings into FAIL. Exit 1 iff a FAIL was printed, 2 on a usage error or an
`sdd` block that check_spec.py refuses.

Rules (FAIL or WARN; the key each one reads, a rule whose key is null or empty is off):
  a FAIL  the kit columns (KIT-068) and their values; a malformed row skips the other rules
  b FAIL  every Files entry starts at a top-level path of the repository or a `components` name; a row stays in one
          component (a contract row that owns `row_checks.protocol.folder` only warns)
  c       a Files entry that matches a `row_checks.tests` code glob needs a test path of that stack
  d WARN  a listed generated neighbour (gates `generated_neighbours`); an exact `row_checks.assets` path
  e       each proof clause runs allowlisted programs only (gates `proof_allowlist`; without it, the refused
          constructs only), under the component rules (`components`: no `..`, no expansion outside a leading anchor,
          no inline code); a Proof of `evidence:` clauses only fails unless `row_checks.evidence_only` is true
  f WARN  each Depends on token is —, Tn of the table, FEAT-NNN Tn of that FEAT on disk, or #N
  g FAIL  each path a proof clause names is covered by the Files of the row or of a same-FEAT dependency
  h WARN  a message type the Task sends exists as `row_checks.protocol.schemas`/<type>.json
  i WARN  a row that changes the policy of an artifact in the `row_checks.artifacts` registry cites its decision
  j WARN  with `visual_approval` owner or reviewer, a `row_checks.visual` path needs an `evidence:` clause; each clause
          parses, and its catalog file exists on origin/main or is covered by Files
  k WARN  a todo or doing row that owns the protocol folder has, per consumer, an open row that depends on it and
          covers one of that consumer's tables (the contract row itself counts)

The proof predicates come from pr_gates.py beside this file, the same code the PR gates run, so a row is judged before
the cut by the rules its PR's proof block meets later. Upstreamed from a consumer project's row linter.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import posixpath
import re
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_spec  # noqa: E402
import pr_gates  # noqa: E402
from pr_gates import command_allowed, expand_braces, parse_files_cell, path_matches  # noqa: E402

COLUMNS = ("ID", "Task", "Files", "Proof of completion", "Covers", "Depends on", "Status", "Complexity", "Model",
           "Wave", "Item")
STATUSES = ("todo", "doing", "blocked", "done", "cancelled")
LEGACY = {"in-progress": "doing", "superseded": "cancelled"}  # row words of tables written before KIT-068
SETTLED = {"doing", "blocked", "done", "cancelled"}
OPEN = {"todo", "doing"}
COMPLEXITIES = ("Low", "Med", "High")
MODELS = ("small", "mid", "top")
ITEM = re.compile(r"^(—|-|#\d+|[\w.-]+/[\w.-]+#\d+|TASK-\d{3,})$")

FAIL, WARN = "FAIL", "WARN"
LEVELS = {"a": FAIL, "b": FAIL, "c": WARN, "d": WARN, "e": FAIL, "f": WARN, "g": FAIL, "h": WARN, "i": WARN,
          "j": WARN, "k": WARN}
STRICT_PROMOTED = {"c", "f"}

PATH_EXTS = ("java", "gd", "tscn", "tres", "json", "sql", "yml", "yaml", "xml", "md", "py", "png", "csv", "wav",
             "import", "uid", "translation", "properties", "txt", "sh")
SEGMENT = r"[\w.\-*{},]+"
PATH_TOKEN = re.compile(rf"(?<![\w/.~$:\-])({SEGMENT}(?:/{SEGMENT})+)")
AUTOMATED_HINT = re.compile(r"\b(unit|tests?|suite|gdunit4?|green|ci|lint|check)\b", re.I)


class UsageError(Exception):
    """A configuration or command line the tool cannot use: exit 2."""


class _Any:
    """The allowlist when the project names no gates file: every program passes, the refused constructs still fail."""

    def __contains__(self, item):
        return True


@dataclass
class Finding:
    level: str
    feat: str
    task: str
    cell: str
    message: str
    rule: str = ""

    def render(self) -> str:
        where = f"{self.feat} {self.task}".strip()
        text = f"{self.level}: {where}: " + " ".join(x for x in (self.cell, self.message) if x)
        return text + (f" [{self.rule}]" if self.rule else "")


@dataclass
class Config:
    root: Path
    spec_dir: Path
    params: dict
    components: dict = field(default_factory=dict)
    allowlist: object = field(default_factory=_Any)
    runners: dict = field(default_factory=dict)
    evidence_only: bool = False
    neighbours: tuple = ()
    tests: list = field(default_factory=list)
    assets: dict | None = None
    protocol: dict | None = None
    artifacts: list = field(default_factory=list)
    visual: dict | None = None
    catalog_ref: str | None = None  # "origin/main" when the repository has it, for rule j's catalog check


@dataclass
class Row:
    feat: str
    line_no: int
    cells: list
    header: list
    siblings: dict = field(default_factory=dict)
    cfg: Config | None = None

    def get(self, name: str) -> str:
        if name not in self.header:
            return ""
        i = self.header.index(name)
        return self.cells[i] if i < len(self.cells) else ""

    @property
    def task_id(self) -> str:
        return self.cells[0] if self.cells else "?"

    @property
    def status(self) -> str:
        value = self.get("Status")
        return LEGACY.get(value, value)

    @property
    def files(self) -> list:
        return parse_files_cell(self.get("Files"))

    @property
    def normalized_files(self) -> list:
        return [normalize(path, self.cfg) for path in self.files]


# --------------------------------------------------------------------------- configuration


def schemas_dir() -> Path:
    """spec.schema.json beside this file (the synced copy) or in the kit's platforms/ci/schemas."""
    for folder in (HERE / "schemas", HERE.parent / "schemas"):
        if (folder / "spec.schema.json").is_file():
            return folder
    raise UsageError(f"no spec.schema.json in {HERE / 'schemas'} or {HERE.parent / 'schemas'}")


def repo_root(spec_dir: Path) -> Path:
    """The clone the spec lives in: git's toplevel, else `x/docs/spec` -> `x`, else the spec's parent."""
    shown = subprocess.run(["git", "-C", str(spec_dir), "rev-parse", "--show-toplevel"], capture_output=True,
                           text=True)
    if shown.returncode == 0:
        return Path(shown.stdout.strip()).resolve()
    return spec_dir.parent.parent if spec_dir.parent.name == "docs" else spec_dir.parent


def read_json(root: Path, rel: str | None, key: str):
    if not rel:
        return None
    path = root / rel
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise UsageError(f"sdd.row_checks.{key} {rel}: {error}")


def _strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def checked_gates(gates, rel: str) -> dict:
    """The gates config, refused with a usage error unless each key row_checks.py reads has its shape: a crash here
    would exit 1, the FAIL code, and an unusable config would check nothing."""
    where = f"sdd.row_checks.gates {rel}"
    if not isinstance(gates, dict):
        raise UsageError(f"{where}: must be an object, not {type(gates).__name__}")
    for key in ("proof_allowlist", "generated_neighbours"):
        if key in gates and not _strings(gates[key]):
            raise UsageError(f"{where}: {key} must be a list of strings")
    runners = gates.get("proof_script_runners", {})
    if not isinstance(runners, dict) or not all(_strings(v) for v in runners.values()):
        raise UsageError(f"{where}: proof_script_runners must map a program to a list of option strings")
    return gates


def checked_artifacts(artifacts, rel: str) -> list:
    """The artifact-policy registry: a list of {pattern, dec, policy} strings, else a usage error."""
    where = f"sdd.row_checks.artifacts {rel}"
    if not isinstance(artifacts, list):
        raise UsageError(f"{where}: must be a list of {{pattern, dec, policy}} entries, not {type(artifacts).__name__}")
    for n, entry in enumerate(artifacts, 1):
        if not isinstance(entry, dict):
            raise UsageError(f"{where}: entry {n} must be an object with the strings pattern, dec and policy")
        missing = [k for k in ("pattern", "dec", "policy") if not isinstance(entry.get(k), str)]
        if missing:
            raise UsageError(f"{where}: entry {n} needs the strings {', '.join(missing)}")
    return artifacts


def load_config(spec_dir) -> Config:
    spec_dir = Path(spec_dir).resolve()
    if not spec_dir.is_dir():
        raise UsageError(f"spec dir does not exist: {spec_dir}")
    params, errors = check_spec.load_params(spec_dir, schemas_dir())
    if errors:
        raise UsageError("the profile's sdd section refused (profile.py resolve --section sdd): " + "; ".join(errors))
    root = repo_root(spec_dir)
    rc = params.get("row_checks") or {}
    gates = read_json(root, rc.get("gates"), "gates")
    gates = checked_gates(gates, rc["gates"]) if rc.get("gates") else {}
    cfg = Config(root=root, spec_dir=spec_dir, params=params, components=dict(params.get("components") or {}))
    if gates.get("proof_allowlist"):
        cfg.allowlist = list(gates["proof_allowlist"])
    cfg.runners = dict(gates.get("proof_script_runners") or {})
    cfg.evidence_only = rc.get("evidence_only") is True
    cfg.neighbours = tuple(gates.get("generated_neighbours") or ())
    cfg.tests = [t for t in rc.get("tests") or [] if isinstance(t, dict) and t.get("code") and t.get("tests")]
    cfg.assets = rc.get("assets") or None
    cfg.protocol = rc.get("protocol") or None
    artifacts = read_json(root, rc.get("artifacts"), "artifacts")
    cfg.artifacts = checked_artifacts(artifacts, rc["artifacts"]) if rc.get("artifacts") else []
    if params.get("visual_approval") in ("owner", "reviewer"):
        cfg.visual = rc.get("visual") or None
    has_main = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "--quiet", "origin/main^{commit}"],
                              capture_output=True).returncode == 0
    cfg.catalog_ref = "origin/main" if has_main else None
    return cfg


# --------------------------------------------------------------------------- paths


def normalize(path: str, cfg: Config | None) -> str:
    """A Files entry that starts with a component name (`backend/x`) as its folder path (`server/x`)."""
    if cfg is None:
        return path
    head, sep, rest = path.partition("/")
    folder = cfg.components.get(head)
    if folder is None:
        return path
    if folder == ".":
        return rest if sep else "."
    return folder + sep + rest


def component_of(path: str, cfg: Config) -> str | None:
    """The component whose folder holds a normalized path; the `.` component owns every other path."""
    best, size = None, -1
    for name, folder in cfg.components.items():
        if folder == ".":
            if size < 0:
                best, size = name, 0
        elif (path == folder or path.startswith(folder + "/")) and len(folder) > size:
            best, size = name, len(folder)
    return best


def folder_of(component: str | None, cfg: Config) -> str:
    return cfg.components.get(component, ".") if component else "."


def row_component(row: Row) -> str | None:
    """The one component of a row whose Files stay in one, else None."""
    owners = {component_of(p, row.cfg) for p in row.normalized_files}
    return next(iter(owners)) if len(owners) == 1 else None


def literal_prefix(pattern: str) -> str:
    """The folders of a glob before its first wildcard: `client/ui/**` -> `client/ui/`."""
    cut = min([i for i in (pattern.find(c) for c in "*?{[") if i >= 0] or [len(pattern)])
    head = pattern[:cut]
    return head[: head.rfind("/") + 1]


def overlaps(entry: str, glob: str) -> bool:
    """A Files entry owns some path the glob names: the entry matches the glob, or the entry is a glob and a sample
    file in its folder with the glob's file name pattern matches both."""
    for e in expand_braces(entry):
        if path_matches(e, glob):
            return True
        if not re.search(r"[*?\[]", e):
            continue
        last = glob.rsplit("/", 1)[-1]
        name = "sample" + (last[last.index("*") + 1:] if last.startswith("*") and "." in last else "")
        sample = literal_prefix(e) + name
        if path_matches(sample, e) and path_matches(sample, glob):
            return True
    return False


def capture_regex(glob: str) -> str:
    """glob_to_regex with each `*` and `**` captured, so a tests glob can name them as $1, $2..."""
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out, i = out + "(?:(.*)/)?", i + 3
        elif glob.startswith("**", i):
            out, i = out + "(.*)", i + 2
        elif glob[i] == "*":
            out, i = out + "([^/]*)", i + 1
        elif glob[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(glob[i]), i + 1
    return "^" + out + "$"


def code_match(entry: str, glob: str):
    """The wildcard values when a Files entry adds code under the glob (literally, or as a glob covering a sample file
    of it), else None."""
    for e in expand_braces(entry):
        m = re.match(capture_regex(glob), e)
        if m:
            return [g or "" for g in m.groups()]
    if overlaps(entry, glob):
        last = glob.rsplit("/", 1)[-1]
        name = "sample" + (last[last.index("*") + 1:] if last.startswith("*") and "." in last else "")
        m = re.match(capture_regex(glob), literal_prefix(entry) + name)
        if m:
            return [g or "" for g in m.groups()]
    return None


def fill(template: str, values: list) -> str:
    return re.sub(r"\$(\d+)", lambda m: values[int(m.group(1)) - 1] if int(m.group(1)) <= len(values) else "",
                  template)


# --------------------------------------------------------------------------- parsing


def split_cells(line: str) -> list:
    """The cells of a table row; a Markdown-escaped pipe (`\\|`) inside a cell is a literal `|`."""
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def parse_rows(feat: str, text: str, cfg: Config) -> list | None:
    """The rows a check lints (header starting `| ID |`): the `## Tasks` table, or a versioned FEAT's open (last)
    version block `#### Tasks` table, whose `Depends on` the earlier blocks' rows answer too (KIT-096); the sections
    come from check_spec.task_sections. None when that section holds no such table."""
    sections = check_spec.task_sections(text)
    blocks = check_spec.version_blocks(text)
    if not sections or (blocks and blocks[-1]["tasks"] is None):
        return None  # a versioned FEAT whose open block has no `#### Tasks` has no open rows
    table, rows, header = {}, None, None
    for _, first, body in sections:
        rows, header = section_rows(feat, first, body, cfg)
        table.update({r.task_id: r for r in rows})
    if header is None:
        return None
    for r in table.values():
        r.siblings = table
    return rows


def section_rows(feat: str, first: int, body: str, cfg: Config) -> tuple:
    """(rows, header) of the task table in one section whose first line has index `first`."""
    rows, header = [], None
    for offset, line in enumerate(body.splitlines()):
        if not line.startswith("|"):
            continue
        cells = split_cells(line)
        if cells and cells[0] == "ID":
            header = cells
            continue
        if header is None or (cells and set(cells[0]) <= set("-: ")):
            continue
        if cells and re.fullmatch(r"T\d+", cells[0]):
            rows.append(Row(feat, first + offset, cells, header, cfg=cfg))
    return rows, header


def parse_feat(path: Path, cfg: Config) -> list | None:
    return parse_rows(path.stem, path.read_text(encoding="utf-8"), cfg)


def split_clauses(cell: str) -> list:
    """Split a proof cell on `;` outside backticks."""
    out, buf, inside = [], [], False
    for ch in cell:
        if ch == "`":
            inside = not inside
        if ch == ";" and not inside:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    out.append("".join(buf).strip())
    return [c for c in out if c]


def command_shaped(text: str, cfg: Config) -> bool:
    first = text.split(None, 1)[0] if text.split() else ""
    return bool(first) and (first in cfg.allowlist or first.startswith(("./", "~/", "!")))


def clause_commands(clause: str, cfg: Config) -> tuple:
    """(whole clause is a command, inline backticked commands of a prose clause)."""
    if clause.startswith("`") and clause.endswith("`") and clause.count("`") == 2:
        return command_shaped(clause[1:-1].strip(), cfg), []
    spans = re.findall(r"`([^`]+)`", clause)
    return False, [s.strip() for s in spans if " " in s.strip() and command_shaped(s.strip(), cfg)]


def short(text: str, n: int = 48) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


# --------------------------------------------------------------------------- rules


def header_finding(rows: list) -> list:
    """Rule a, once per table: the header holds the kit columns in the kit order."""
    header = rows[0].header
    if list(header) == list(COLUMNS):
        return []
    missing = [c for c in COLUMNS if c not in header]
    extra = [c for c in header if c not in COLUMNS]
    parts = ([f"lacks {', '.join(missing)}"] if missing else []) + ([f"has {', '.join(extra)}"] if extra else [])
    detail = "; ".join(parts) or "lists the kit columns in another order"
    return [Finding(LEVELS["a"], rows[0].feat, "", "Tasks", f"table header {detail}: the kit columns are "
                    f"{' | '.join(COLUMNS)} (sdd-tasks § 3)", "a")]


def rule_a(row: Row, cfg: Config | None = None) -> list:
    f = lambda cell, msg: Finding(LEVELS["a"], row.feat, row.task_id, cell, msg, "a")  # noqa: E731
    if len(row.cells) != len(row.header):
        return [f("row", f"has {len(row.cells)} cells, expected {len(row.header)}")]
    checks = [("Status", lambda v: v in STATUSES, "one of " + "|".join(STATUSES)),
              ("Complexity", lambda v: v in COMPLEXITIES, "one of " + "|".join(COMPLEXITIES)),
              ("Model", lambda v: v in MODELS, "one of " + "|".join(MODELS)),
              ("Wave", lambda v: re.fullmatch(r"\d+", v) is not None, "an integer"),
              ("Item", lambda v: ITEM.match(v) is not None, "—, #N, owner/repo#N or TASK-nnn")]
    return [f(cell, f"'{row.get(cell)}' must be {want}") for cell, ok, want in checks
            if cell in row.header and not ok(row.get(cell))]


def owns_protocol(row: Row) -> bool:
    folder = (row.cfg.protocol or {}).get("folder")
    return bool(folder) and any(path_matches(p, folder.rstrip("/") + "/**") for p in row.normalized_files)


def rule_b(row: Row, cfg: Config | None = None) -> list:
    f = lambda msg: Finding(LEVELS["b"], row.feat, row.task_id, "Files", msg, "b")  # noqa: E731
    cfg = cfg or row.cfg
    if not row.files:
        return [f("has no backticked path entry")]
    out = []
    for entry in row.files:
        if entry.split("/", 1)[0] in cfg.components:
            continue
        parts = entry.split("/")
        known = (cfg.root / parts[0]).is_dir() if len(parts) > 1 else (cfg.root / parts[0]).is_file()
        if not (all(p not in {"", ".", "..", ".git"} for p in parts) and known):
            names = ", ".join(f"{n}/" for n in sorted(cfg.components))
            out.append(f(f"entry '{entry}' does not start at a top-level path of the repository"
                         + (f" or a component name ({names})" if names else "")))
    if out or not cfg.components:
        return out
    owners = sorted({component_of(p, cfg) or "(no component)" for p in row.normalized_files})
    if len(owners) > 1:
        finding = f(f"spans {' and '.join(owners)}: split the row")
        if owns_protocol(row):
            finding.level = WARN
            finding.message += ("; a contract row may span components to regenerate its consumers' tables (rule k), "
                                "when the project's cut accepts it")
        out.append(finding)
    return out


def tables(cfg: Config) -> set:
    return {normalize(t, cfg) for paths in ((cfg.protocol or {}).get("consumers") or {}).values() for t in paths}


def rule_c(row: Row, cfg: Config | None = None) -> list:
    cfg = cfg or row.cfg
    files = row.normalized_files
    generated = tables(cfg)
    missing, level = [], LEVELS["c"]
    for stack in cfg.tests:
        excluded = list(stack.get("exclude") or [])
        for entry in files:
            if entry in generated or any(path_matches(entry, x) for x in excluded):
                continue
            values = next((v for v in (code_match(entry, g) for g in stack["code"]) if v is not None), None)
            if values is None:
                continue
            tests = fill(stack["tests"], values)
            sample = fill(stack.get("sample") or tests.replace("**", "x").replace("*", "sample"), values)
            if not any(path_matches(e, tests) or path_matches(sample, e) for e in files):
                if tests not in missing:
                    missing.append(tests)
                if stack.get("level", "fail") == "fail":
                    level = FAIL
    if not missing:
        return []
    return [Finding(level, row.feat, row.task_id, "Files", f"adds code but lists no test path ({', '.join(missing)})",
                    "c")]


def rule_d(row: Row, cfg: Config | None = None) -> list:
    cfg, files, out = cfg or row.cfg, row.normalized_files, []
    for entry in files:
        if cfg.neighbours and entry.endswith(cfg.neighbours):
            out.append(Finding(LEVELS["d"], row.feat, row.task_id, "Files",
                               f"lists the generated neighbour '{entry}': neighbours are implicit and never listed "
                               "(drop it)", "d"))
    assets = cfg.assets or {}
    suffixes = tuple(assets.get("suffixes") or ())
    for entry in files:
        if not suffixes or not any(path_matches(entry, p) for p in assets.get("paths") or []):
            continue
        for e in expand_braces(entry):
            if not e.endswith(suffixes):
                continue
            if not any("**" in o and path_matches(e, o) for o in files if o != entry):
                out.append(Finding(LEVELS["d"], row.feat, row.task_id, "Files",
                                   f"'{entry}' is an exact asset path; name the owned directory as a ** glob (its "
                                   "generated neighbours are implicit)", "d"))
                break
    return out


def rule_e(row: Row, cfg: Config | None = None) -> list:
    cfg = cfg or row.cfg
    clauses = split_clauses(row.get("Proof of completion"))
    out = []
    f = lambda level, msg: Finding(level, row.feat, row.task_id, "Proof of completion", msg, "e")  # noqa: E731
    cwd = None
    if cfg.components and not rule_b(row, cfg):
        cwd = folder_of(row_component(row), cfg)
    any_command, shapes = False, {}
    for n, clause in enumerate(clauses, 1):
        if clause.startswith("evidence:"):
            continue
        whole, inline = clause_commands(clause, cfg)
        label = f"clause {n} '{short(clause.strip('`'))}'"
        if clause.count("`") % 2:
            out.append(f(FAIL, f"{label} (unbalanced backtick)"))
            shapes[n] = False
            continue
        candidates = ([clause[1:-1].strip()] if whole else []) + inline
        any_command = any_command or bool(candidates)
        problem = None
        for cmd in candidates:
            ok, why = command_allowed(cmd, cfg.allowlist, cwd=cwd)
            if not ok:
                problem = why
                break
        if problem is None and not whole:
            # prose: the refused words and `$(` still count, backticks are code spans here
            if pr_gates._FORBIDDEN.search(clause.replace("`", "")) or "$(" in clause:
                problem = "forbidden construct"
        if problem:
            out.append(f(FAIL, f"{label} ({problem})"))
        shapes[n] = (whole or bool(inline) or bool(AUTOMATED_HINT.search(clause))) and "manual" not in clause.lower()
    for n, clause in enumerate(clauses, 1):
        if n in shapes and "manual" in clause.lower() and not any(ok for k, ok in shapes.items() if k != n):
            out.append(f(WARN, f"clause {n} '{short(clause.strip('`'))}' is manual with no automated sibling clause"))
    if clauses and all(c.startswith("evidence:") for c in clauses) and not cfg.evidence_only:
        out.append(f(FAIL, "holds only evidence: clauses: add a runnable proof clause, or set "
                           "row_checks.evidence_only to true where an approved capture is the whole proof"))
    elif any(not c.startswith("evidence:") for c in clauses) and not any_command:
        out.append(f(WARN, "has no command-shaped clause (the PR proof block will have to invent one)"))
    if not clauses:
        out.append(f(WARN, "is empty"))
    return out


_DEP_TOKEN = re.compile(r"FEAT-\d+|T\d+|#\d+")


def parse_depends(cell: str) -> tuple:
    """([(feat or '', 'Tn' | '#N')], recognised). `FEAT-006 T0, T2; FEAT-008 T1` -> 006 T0, 006 T2, 008 T1."""
    refs = []
    for segment in cell.split(";"):
        current = ""
        for tok in _DEP_TOKEN.findall(segment):
            if tok.startswith("FEAT-"):
                current = tok
            elif tok.startswith("#"):
                refs.append(("", tok))
            else:
                refs.append((current, tok))
    stripped = cell.strip().strip("`")
    return refs, bool(refs) or stripped in {"—", "-", "–", ""}


def feat_ids(feat: str, cfg: Config):
    path = cfg.spec_dir / "features" / f"{feat}.md"
    if not path.exists():
        return None
    return {r.task_id for r in parse_feat(path, cfg) or []}


def rule_f(row: Row, cfg: Config | None = None) -> list:
    f = lambda msg: Finding(LEVELS["f"], row.feat, row.task_id, "Depends on", msg, "f")  # noqa: E731
    refs, ok = parse_depends(row.get("Depends on"))
    if not ok:
        return [f(f"'{short(row.get('Depends on'))}' is not —, Tn, FEAT-NNN Tn or #N")]
    out = []
    for feat, ref in refs:
        if ref.startswith("#"):
            continue
        if not feat or feat == row.feat:
            if ref not in row.siblings:
                out.append(f(f"{ref} is not in the {row.feat} table"))
        else:
            ids = feat_ids(feat, cfg or row.cfg)
            if ids is None:
                out.append(f(f"{feat} not found under {(cfg or row.cfg).spec_dir.name}/features/"))
            elif ref not in ids:
                out.append(f(f"{feat} {ref} is not in that FEAT's table"))
    return out


def proof_tools(text: str, cfg: Config) -> set:
    """The tools a proof's commands run, which are no deliverables: a command's first token (after `!`), the script
    after `python3` or a script runner (gates `proof_script_runners`, e.g. godot `-s`), and `-s` of a unittest run."""
    import shlex
    out = set()
    for span in re.findall(r"`([^`]+)`", text or ""):
        try:
            toks = shlex.split(span)
        except ValueError:
            toks = span.split()
        if toks[:1] == ["!"]:
            toks = toks[1:]
        if not toks or not (toks[0] in cfg.allowlist or toks[0].startswith(("./", "~/"))):
            continue
        out.add(toks[0])
        runner_flags = cfg.runners.get(toks[0])
        if (toks[0] == "python3" or runner_flags is not None) and len(toks) > 1:
            out.add(toks[1])
        if runner_flags:
            out.update(b for a, b in zip(toks, toks[1:]) if a in runner_flags)
        if toks[0] == "python3" and "unittest" in toks:
            out.update(b for a, b in zip(toks, toks[1:]) if a == "-s")
    return out


def proof_paths(clause: str, cfg: Config) -> list:
    """Path-shaped tokens a proof clause names; the program and the script it runs are not deliverables."""
    whole, _ = clause_commands(clause, cfg)
    text = clause.strip("`") if whole else clause
    skip = proof_tools(clause, cfg)
    out = []
    for m in PATH_TOKEN.finditer(text):
        tok = m.group(1).rstrip(".,").lstrip(",")
        last = tok.rsplit("/", 1)[-1]
        if tok in skip or "://" in tok or not re.search(r"\.(" + "|".join(PATH_EXTS) + r")$", last):
            continue
        out.append(tok)
    return out


def rule_g(row: Row, cfg: Config | None = None) -> list:
    """Every path a proof clause names is a path the row (or a same-FEAT dependency) delivers."""
    cfg = cfg or row.cfg
    globs = list(row.normalized_files)
    for feat, ref in parse_depends(row.get("Depends on"))[0]:
        dep = row.siblings.get(ref) if (not feat or feat == row.feat) and not ref.startswith("#") else None
        if dep is not None:
            globs += dep.normalized_files
    folder = folder_of(row_component(row), cfg) if cfg.components else "."
    out = []
    for n, clause in enumerate(split_clauses(row.get("Proof of completion")), 1):
        if clause.count("`") % 2:
            continue
        for tok in proof_paths(clause, cfg):
            candidates = [normalize(tok, cfg)] + ([posixpath.join(folder, tok)] if folder != "." else [])
            if not any(path_matches(c, g) for c in candidates for g in globs):
                out.append(Finding(LEVELS["g"], row.feat, row.task_id, "Proof of completion",
                                   f"clause {n} names '{tok}', which no Files entry of the row or its dependencies "
                                   "covers", "g"))
    return out


_SENDS = re.compile(r"\b(sends|replies)\b|→|->")
_TYPE = re.compile(r"^[a-z][a-z0-9_]*$")
_SEND_FIRST = re.compile(r"\s*`([^`]+)`")
_SEND_NEXT = re.compile(r"(?:\s*(?:,|/|\band\b|\bor\b))+\s*`([^`]+)`")


def _send_run(task: str, start: int) -> list:
    """The backticked tokens of the run that opens at `start`: one right after the trigger (whitespace only between),
    then more through `,`, `/`, `and` or `or` — `sends `a`, `b` and `c`` reads three."""
    m = _SEND_FIRST.match(task, start)
    if not m:
        return []
    out, pos = [m.group(1)], m.end()
    while True:
        m = _SEND_NEXT.match(task, pos)
        if not m:
            return out
        out.append(m.group(1))
        pos = m.end()


def rule_h(row: Row, cfg: Config | None = None) -> list:
    """A message type is read only where it is sent. An arrow whose left side's last backticked token names no schema
    is a value map (`user` → `self`) and is skipped."""
    cfg = cfg or row.cfg
    folder = (cfg.protocol or {}).get("schemas")
    if not folder:
        return []
    schemas = cfg.root / folder
    task, out, seen = row.get("Task"), [], set()
    for m in _SENDS.finditer(task):
        if m.group(1) is None:
            left = re.search(r"`([^`]+)`[^`]*$", task[: m.start()])
            if left and not (schemas / f"{left.group(1)}.json").exists():
                continue
        for tok in _send_run(task, m.end()):
            if _TYPE.match(tok) and tok not in seen:
                seen.add(tok)
                if not (schemas / f"{tok}.json").exists():
                    out.append(Finding(LEVELS["h"], row.feat, row.task_id, "Task",
                                       f"names message type '{tok}' but {folder}/{tok}.json does not exist (fine "
                                       "when this row or an earlier one creates it)", "h"))
    return out


_POLICY_FILES = (".gitignore", ".gitattributes")
# Policy terms of the Task cell: whole words, any case. `merge=` ends in a non-word char, so it keeps no right boundary
# and matches `merge=union`/`merge=ours`.
_POLICY_TERMS = ("git-ignore", "gitignore", "untrack", "from the index", "committed", "commit it", "commit them",
                 "lfs", "by hand", "merge=")
POLICY_TERM = re.compile("|".join(r"(?<!\w)" + r"\s+".join(re.escape(w) for w in t.split())
                                  + (r"(?!\w)" if t[-1].isalnum() else "") for t in _POLICY_TERMS), re.I)


def artifact_match(token: str, pattern: str, cfg: Config) -> bool:
    """A Files entry or Task token (after a component name) names a governed artifact: its basename `fnmatch`es a
    pattern without `/`, it matches a pattern with `/`, or it is the pattern's bare extension (`.translation`)."""
    t = token.strip().strip(".,;:)\"'")
    head, sep, rest = t.partition("/")
    if sep and head in cfg.components:
        t = rest
    if not t:
        return False
    if "/" in pattern:
        return path_matches(t, pattern)
    base = t.rsplit("/", 1)[-1]
    return fnmatch.fnmatch(base, pattern) or (pattern.startswith("*") and base == pattern[1:])


def rule_i(row: Row, cfg: Config | None = None) -> list:
    cfg = cfg or row.cfg
    files, task = row.files, row.get("Task")
    if not cfg.artifacts or not (any(f.rsplit("/", 1)[-1] in _POLICY_FILES for f in files) or POLICY_TERM.search(task)):
        return []
    tokens = [("Task", w) for m in re.findall(r"`([^`]+)`", task) for w in m.split()] + [("Files", f) for f in files]
    out = []
    for entry in cfg.artifacts:
        hit = next(((cell, tok) for cell, tok in tokens if artifact_match(tok, entry["pattern"], cfg)), None)
        if hit and entry["dec"] not in task:
            out.append(Finding(LEVELS["i"], row.feat, row.task_id, hit[0],
                               f"names '{hit[1]}', governed by {entry['dec']} ({entry['policy']}), but cites no "
                               f"{entry['dec']}", "i"))
    return out


_EVIDENCE_RE = re.compile(r"evidence:\s+(?P<kind>screen|motion)\s+`(?P<id>[a-z0-9][a-z0-9-]*)`"
                          r"(?:\s+states\s+(?P<states>`[a-z0-9_]+`(?:\s*,\s*`[a-z0-9_]+`)*))?")


def evidence_clauses(proof: str) -> tuple:
    """The `evidence:` clauses of a proof as {kind, id, states}, and one error per clause that breaks the grammar
    `evidence: screen|motion `<id>` [states `<s>`, ...]` (a motion takes no states)."""
    clauses, errors = [], []
    for text in split_clauses(proof):
        if not text.startswith("evidence:"):
            continue
        m = _EVIDENCE_RE.fullmatch(" ".join(text.split()))
        if not m or (m["kind"] == "motion" and m["states"]):
            errors.append(f"evidence: bad clause '{text}'")
        else:
            states = re.findall(r"`([^`]+)`", m["states"]) if m["states"] else None
            clauses.append({"kind": m["kind"], "id": m["id"], "states": states})
    return clauses, errors


def rule_j(row: Row, cfg: Config | None = None) -> list:
    cfg = cfg or row.cfg
    visual = cfg.visual
    if not visual:
        return []
    f = lambda cell, msg: Finding(LEVELS["j"], row.feat, row.task_id, cell, msg, "j")  # noqa: E731
    proof = row.get("Proof of completion")
    clauses = split_clauses(proof)
    evidence, errors = evidence_clauses(proof)
    out = [f("", err) for err in errors]
    owned = [e for entry in row.normalized_files for e in expand_braces(entry)
             if not any(path_matches(e, p) for p in visual.get("ignore") or [])]
    hit = next((e for e in owned if any(path_matches(e, p) for p in visual.get("paths") or [])), None)
    if hit and not any(c.startswith("evidence:") for c in clauses):
        out.append(f("Files", f"entry '{hit}' is a visual or motion path, and the Proof has no `evidence:` clause"))
    catalog = visual.get("catalog") or {}
    if cfg.catalog_ref is None:
        return out
    for c in evidence:
        template = catalog.get(c["kind"])
        if not template:
            continue
        rel = template.replace("$id", c["id"])
        on_main = subprocess.run(["git", "-C", str(cfg.root), "cat-file", "-e", f"{cfg.catalog_ref}:{rel}"],
                                 capture_output=True).returncode == 0
        if not on_main and not any(path_matches(rel, e) for e in row.normalized_files):
            out.append(f("Proof of completion", f"clause '{c['kind']} `{c['id']}`' has no catalog file {rel} on "
                                                f"{cfg.catalog_ref}, and no Files entry covers it"))
    return out


def covers_tables(row: Row, consumer: str) -> bool:
    paths = ((row.cfg.protocol or {}).get("consumers") or {}).get(consumer) or []
    return any(path_matches(normalize(t, row.cfg), e) for e in row.normalized_files for t in paths)


def rule_k(row: Row, cfg: Config | None = None) -> list:
    """A todo or doing row whose Files own the protocol folder needs, in the same FEAT, a todo or doing row per
    consumer that depends on it and covers one of that consumer's tables; the contract row's own Files count."""
    cfg = cfg or row.cfg
    consumers = ((cfg.protocol or {}).get("consumers") or {})
    if row.status not in OPEN or not consumers or not owns_protocol(row):
        return []
    rows = [r for r in row.siblings.values() if r.status in OPEN and r is not row
            and any((not feat or feat == row.feat) and ref == row.task_id
                    for feat, ref in parse_depends(r.get("Depends on"))[0])] + [row]
    return [Finding(LEVELS["k"], row.feat, row.task_id, "", f"contract row {row.task_id} has no {consumer} "
                    "regeneration row", "k")
            for consumer in consumers if not any(covers_tables(r, consumer) for r in rows)]


RULES = [rule_b, rule_c, rule_d, rule_e, rule_f, rule_g, rule_h, rule_i, rule_j, rule_k]


def lint(rows: list, cfg: Config, strict: bool = False, all_rows: bool = False) -> tuple:
    """(findings, rows checked). Only rows that are not settled unless `all_rows`."""
    findings, linted, headers = [], 0, set()
    for row in rows:
        row.cfg = cfg
        if not all_rows and len(row.cells) == len(row.header) and row.status in SETTLED:
            continue
        linted += 1
        if row.feat not in headers:
            headers.add(row.feat)
            findings += header_finding([row])
        base = rule_a(row, cfg)
        if base:  # a malformed row skips the other rules
            findings += base
            continue
        for rule in RULES:
            findings += rule(row, cfg)
    if strict:
        for fd in findings:
            if fd.rule in STRICT_PROMOTED:
                fd.level = FAIL
    return findings, linted


# --------------------------------------------------------------------------- command line


def resolve_targets(args, cfg: Config) -> tuple:
    paths, notes = [], []
    features = cfg.spec_dir / "features"
    for item in args.feats:
        p = features / f"{item}.md" if re.fullmatch(r"FEAT-\d+", item) else Path(item)
        if not p.exists():
            notes.append(Finding(FAIL, p.stem, "", "", "file not found"))
        else:
            paths.append(p)
    if args.all:
        paths += sorted(features.glob("FEAT-*.md"))
    if args.changed:
        base, head = args.changed
        out = subprocess.run(["git", "-C", str(cfg.root), "diff", "--name-only", base, head], capture_output=True,
                             text=True)
        if out.returncode != 0:
            notes.append(Finding(FAIL, "git", "", "", f"diff {base} {head} failed: {out.stderr.strip()}"))
        for name in out.stdout.splitlines():
            path = cfg.root / name
            if path.parent.resolve() == features.resolve() and re.fullmatch(r"FEAT-\d+\.md", path.name) \
                    and path.exists():
                paths.append(path)
    seen, uniq = set(), []
    for p in paths:
        if p.resolve() not in seen:
            seen.add(p.resolve())
            uniq.append(p)
    return uniq, notes


def catalog_note(rows: list, cfg: Config) -> str | None:
    """Rule j's catalog check reads origin/main; without it the check is skipped and the output says so."""
    if cfg.visual is None or cfg.catalog_ref is not None:
        return None
    if not any(evidence_clauses(r.get("Proof of completion"))[0] for r in rows):
        return None
    return "row-checks: rule j catalog check skipped: no origin/main in this repository"


def cmd_check(args) -> int:
    if not (args.feats or args.all or args.changed):
        print("row-checks: name a FEAT, or pass --all or --changed BASE HEAD", file=sys.stderr)
        return 2
    cfg = load_config(args.spec)
    paths, findings = resolve_targets(args, cfg)
    total, every = 0, []
    for path in paths:
        rows = parse_feat(path, cfg)
        if rows is None:
            findings.append(Finding(WARN, path.stem, "", "", "no Tasks table"))
            continue
        found, linted = lint(rows, cfg, args.strict, args.all_rows)
        every += [r for r in rows if args.all_rows or r.status not in SETTLED]
        findings += found
        total += linted
    for fd in findings:
        print(fd.render())
    note = catalog_note(every, cfg)
    if note:
        print(note)
    fails = sum(f.level == FAIL for f in findings)
    warns = sum(f.level == WARN for f in findings)
    print(f"row-checks: {total} rows, {fails} fail, {warns} warn")
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="row_checks.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check the Tasks table of FEATs")
    c.add_argument("feats", nargs="*", help="FEAT-NNN ids, or paths to FEAT files")
    c.add_argument("--spec", type=Path, default=Path("docs/spec"), help="the spec directory (default: docs/spec)")
    c.add_argument("--all", action="store_true", help="every FEAT-*.md under <spec>/features")
    c.add_argument("--changed", nargs=2, metavar=("BASE", "HEAD"), help="FEAT files in git diff BASE HEAD")
    c.add_argument("--all-rows", action="store_true", help="check rows of any Status, not only open ones")
    c.add_argument("--strict", action="store_true", help="promote the c and f warnings to FAIL")
    args = ap.parse_args(argv)
    try:
        return cmd_check(args)
    except UsageError as error:
        print(f"row-checks: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # noqa: BLE001  exit 1 means FAIL rows; a crash must never read as one, nor as clean
        traceback.print_exc()
        print(f"row-checks: internal error: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
