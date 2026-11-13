#!/usr/bin/env python3
"""Cross-session audit pre-filter (KIT-056): no model tokens, standard library only.

Reads the Claude Code transcripts (<claude-dir>/*/*.jsonl) and Codex rollouts (<codex-dir>/**/rollout-*.jsonl)
that grew since the last run, from the byte offsets kept in the state directory, and writes one redacted extract
for the `session` skill's `audit` mode:
  owner   owner-typed messages of at most 600 chars with a correction cue: redacted excerpts of at most 300 chars
  kit     `Kit [PROPOSAL]` blocks the agent wrote: first 4 lines, redacted
  errors  normalized tool errors seen in 2 or more sessions: session count and example session ids
  memory  Claude memory entries cited, read and written: session counts
  guard   commands the `ai-kit guard` hook blocked: count per kind; `rm -rf` and `find -delete` by target class
A session listed in <state>/exclude.txt (id prefix or title substring, one per line; Claude titles from the
transcript, Codex titles from <codex-dir>/../session_index.jsonl and state_*.sqlite, also under $CODEX_SQLITE_HOME or
`sqlite_home`) or with a personal-topic keyword in any owner message, from the session's first line, is skipped
whole, and its entries leave the older extracts too: each extract has an index-<stamp>.json of what every session
added, so its counts are rebuilt without it. A keyword with a work meaning counts only next to a word that confirms
the personal meaning; <state>/keywords.txt adds `word` or `word: confirm, confirm` lines, and a change to it
re-checks the sessions in the kept extracts (one whose transcript is gone is dropped). Exclusions reach kept sessions
whose transcript is gone too. When exclude.txt has entries and the Codex titles cannot be read, Codex files wait for
a later run (`codex_deferred`). Prints one JSON line of counts only. Every file it writes has mode 0600, and a run
deletes the temporary files and orphan indexes an interrupted one left.

Usage: session_audit.py [--state DIR] [--claude-dir DIR] [--codex-dir DIR] [--if-older-days N] [--first-run-days N]
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import re
import shlex
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path

KEEP_EXTRACTS = 4
OWNER_MAX = 600
EXCERPT_MAX = 300
KIT_MAX = 600
ERRORS_MAX = 60
EXAMPLES = 5
CONFIRM_WINDOW = 6
SECRET_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"AGE-SECRET-KEY-[0-9A-Z]+"),
    re.compile(r"""(?i)\b(password|passwd|senha|secret|token|api[_-]?key)\b"""
               r"""((?:\s+[\w-]+){0,3}?\s*(?:[:=]\s*(?:(?:is|was|é|e|era)\s+)?|\s(?:is|was|é|e|era)\s+))(?:"[^"\n]*"|'[^'\n]*'|\S+)"""),
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),
    re.compile(r"\b[A-Za-z0-9+/_-]{40,}={0,2}"),
]
# Matched on accent-stripped lowercase text.
CUE = re.compile(
    r"\b(nao (era|e|foi|faca|precisa|quero|pode)|errad[oa]|de novo|outra vez|ja (disse|falei|pedi|expliquei)|"
    r"eu (disse|pedi|falei)|pare\b|para de|nunca\b|sempre\b|por que (voce|vc)|lembr[ea]|regra|esqueceu|"
    r"i said|i told you|wrong\b|again\b|stop\b|never\b|always\b)"
)
PERSONAL_PLAIN = (
    "salario", "salarios", "holerite", "holerites", "irpf", "imposto de renda", "declaracao de imposto",
    "plano de saude", "consulta medica", "medico", "medica", "salary", "payslip", "tax return",
)
PERSONAL_CONFIRM = {
    "banco": ("conta", "cartao", "extrato", "pix", "agencia", "saldo", "fatura", "transferencia", "boleto"),
    "bancos": ("conta", "cartao", "extrato", "pix", "agencia", "saldo", "fatura", "transferencia", "boleto"),
    "investimento": ("acoes", "fii", "cdb", "tesouro", "rendimento", "corretora", "dividendos"),
    "investimentos": ("acoes", "fii", "cdb", "tesouro", "rendimento", "corretora", "dividendos"),
    "bank": ("account", "card", "statement", "balance", "transfer"),
}
WORK_PHRASES = re.compile(r"\bbancos? de (dados|testes|imagens)\b")
NORM = [
    (re.compile(r"/[\w./@+~-]+"), "<path>"),
    (re.compile(r"\b[0-9a-f]{7,40}\b"), "<sha>"),
    (re.compile(r"\d+"), "N"),
    (re.compile(r"\s+"), " "),
]
EXIT_LINE = re.compile(r"(?i)^exit code -?\d+$")
TAG = re.compile(r"</?[a-z_]+>")
DENIAL = re.compile(r"(?i)(doesn't want to proceed|has been denied|rejected by the user|user declined|interrupted by)")
GUARD = re.compile(r"ai-kit guard: ([a-z][a-z0-9 <>|.-]{0,30}?) is destructive", re.I)
KIT_BLOCK = re.compile(r"(?m)^[ \t>*`_-]*Kit \[PROPOSAL\]")
TOOL_ID = re.compile(r'"id":"(toolu_[A-Za-z0-9_]+)"')
CODEX_ID = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl$")
TEMP_ROOT = r"(?:/tmp|/private/tmp|/var/folders)"
TEMP_PATH = re.compile(r"^(?:" + TEMP_ROOT + r"|\$TMPDIR|\$\{TMPDIR(?::?-" + TEMP_ROOT + r"[^}]*)?\})(?:/|$)")
PARENT_STEP = re.compile(r"(?:^|/)\.\.(?:/|$)")
ASSIGN = re.compile(r"(?:^|[\s;&|(])(?:export\s+|local\s+|readonly\s+)?([A-Za-z_]\w*)=[\"']?(\$\(\s*mktemp\b[^)]*\)|[^\s;&|\"']*)")
SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", "|&", ";;"}
REDIRECT = re.compile(r"^[<>&]*[<>][<>&]*$")


def fold(text: str) -> str:
    """Lowercase without accents, for keyword and cue matching."""
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        if pattern.groups >= 2:
            text = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}<redacted>", text)
        else:
            text = pattern.sub(lambda m: f"<redacted:{len(m.group(0))}>", text)
    return text.replace(str(Path.home()), "~")


def normalize_error(text: str) -> str:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) > 1 and EXIT_LINE.match(lines[0]):
        lines = lines[1:]
    first = TAG.sub("", redact(lines[0])) if lines else ""
    for pattern, repl in NORM:
        first = pattern.sub(repl, first)
    return first.strip()[:120].lower()


def texts(content):
    if isinstance(content, str):
        yield content
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") in ("text", "Text", "input_text", "output_text"):
                yield str(block.get("text", ""))


def load_keywords(state: Path):
    plain = [fold(word) for word in PERSONAL_PLAIN]
    confirm = {fold(word): {fold(c) for c in words} for word, words in PERSONAL_CONFIRM.items()}
    path = state / "keywords.txt"
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            word, _, confirms = line.partition(":")
            if not word.strip():
                continue
            words = {fold(c.strip()) for c in confirms.split(",") if c.strip()}
            if words:
                confirm[fold(word.strip())] = words
            else:
                plain.append(fold(word.strip()))
    return [re.compile(r"\b" + re.escape(word) + r"\b") for word in plain], confirm


def keywords_digest(keywords) -> str:
    plain, confirm = keywords
    payload = json.dumps([sorted(p.pattern for p in plain), sorted((k, sorted(v)) for k, v in confirm.items())])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def is_personal(text: str, keywords) -> bool:
    plain, confirm = keywords
    folded = WORK_PHRASES.sub(" ", fold(text))
    if any(pattern.search(folded) for pattern in plain):
        return True
    tokens = re.findall(r"\w+", folded)
    for i, token in enumerate(tokens):
        words = confirm.get(token)
        if words and words & set(tokens[max(0, i - CONFIRM_WINDOW):i + CONFIRM_WINDOW + 1]):
            return True
    return False


def load_excludes(state: Path):
    path = state / "exclude.txt"
    if not path.is_file():
        return []
    entries = (raw.split("#", 1)[0].strip() for raw in path.read_text(encoding="utf-8").splitlines())
    return [entry for entry in entries if entry]


def codex_db_homes(home: Path) -> list:
    """Where Codex keeps state_*.sqlite: its home, $CODEX_SQLITE_HOME and `sqlite_home` in config.toml."""
    homes = [home]
    if os.environ.get("CODEX_SQLITE_HOME"):
        homes.append(Path(os.path.expanduser(os.environ["CODEX_SQLITE_HOME"])))
    try:
        found = re.search(r"(?m)^\s*sqlite_home\s*=\s*[\"']([^\"']+)[\"']",
                          (home / "config.toml").read_text(encoding="utf-8"))
    except OSError:
        found = None
    if found:
        homes.append(Path(os.path.expanduser(found.group(1))))
    return homes


def codex_titles(homes: list):
    """Codex thread names by id from session_index.jsonl (older threads) and the threads table of state_*.sqlite.

    The second value is False when a database exists but its titles cannot be read.
    """
    titles = collections.defaultdict(list)
    ok = True
    home = homes[0]
    index = home / "session_index.jsonl"
    if index.is_file():
        for raw in index.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                data = json.loads(raw)
            except ValueError:
                continue
            if isinstance(data, dict) and data.get("id") and data.get("thread_name"):
                titles[str(data["id"])].append(str(data["thread_name"]))
    for db in sorted({db.resolve() for folder in homes for db in folder.glob("state_*.sqlite")}):
        try:
            con = sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)
            try:
                columns = [c for c in ("name", "title")
                           if c in {row[1] for row in con.execute("pragma table_info(threads)")}]
                if not columns:
                    ok = False
                for row in con.execute("select id, " + ", ".join(columns) + " from threads") if columns else ():
                    titles[str(row[0])].extend(str(value) for value in row[1:] if value)
            finally:
                con.close()
        except sqlite3.Error:
            ok = False
    return {sid: " | ".join(names) for sid, names in titles.items()}, ok


def excluded(sid: str, title: str, entries) -> bool:
    """An entry of 8 or more characters matches a session id prefix; any entry matches a title substring."""
    bare = sid[3:] if sid.startswith("cx-") else sid
    folded = fold(title)
    return any((len(e) >= 8 and (sid.startswith(e) or bare.startswith(e))) or (title and fold(e) in folded)
               for e in entries)


def temp_target(target: str, temp_vars) -> bool:
    if PARENT_STEP.search(target):
        return False
    if TEMP_PATH.match(target) or "scratchpad" in target:
        return True
    var = re.match(r"\$\{?([A-Za-z_]\w*)", target)
    return bool(var) and var.group(1) in temp_vars


def temp_vars(command: str) -> set:
    """Variables the command assigns a temporary path to: mktemp, a temp prefix or an earlier such variable."""
    found = set()
    for match in ASSIGN.finditer(command):
        value = match.group(2)
        if re.match(r"\$\(\s*mktemp\b", value) or temp_target(value, found):
            found.add(match.group(1))
    return found


def classify_targets(command: str, tool: str) -> str:
    """'temp' when every target of every `rm`/`find` in the command is a temporary path, else 'other'."""
    variables = temp_vars(command)
    try:
        lexer = shlex.shlex(command.replace("\\\n", " ").replace("\n", " ; "), posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return "other"
    targets, i = [], 0
    while i < len(tokens):
        if os.path.basename(tokens[i]) == tool:
            j = i + 1
            while j < len(tokens) and tokens[j] not in SEPARATORS:
                arg = tokens[j]
                if REDIRECT.match(arg):
                    j += 2
                    continue
                if arg.isdigit() and j + 1 < len(tokens) and REDIRECT.match(tokens[j + 1]):
                    j += 1
                    continue
                if tool == "rm" and not arg.startswith("-"):
                    targets.append(arg)
                elif tool == "find":
                    if arg.startswith("-") or arg in ("!", "\\("):
                        break
                    targets.append(arg)
                j += 1
            i = j
        i += 1
    return "temp" if targets and all(temp_target(t, variables) for t in targets) else "other"


class Session:
    def __init__(self, sid: str, title: str = ""):
        self.sid = sid
        self.title = title
        self.personal = False
        self.owner_msgs = 0
        self.owner = []
        self.kit = []
        self.errors = set()
        self.cited = set()
        self.read = set()
        self.written = set()
        self.guard = []

    def owner_text(self, text: str, keywords, injected: bool = False):
        """Every owner message is checked for personal words; an injected one (instructions) gives no excerpt."""
        if is_personal(text, keywords):
            self.personal = True
        if injected:
            return
        self.owner_msgs += 1
        if len(text) <= OWNER_MAX and CUE.search(fold(text)):
            excerpt = redact(text.strip())[:EXCERPT_MAX]
            if excerpt not in self.owner:
                self.owner.append(excerpt)

    def kit_text(self, text: str):
        found = KIT_BLOCK.search(text)
        if found:
            block = redact("\n".join(text[found.start():].strip().splitlines()[:4]))[:KIT_MAX]
            if block not in self.kit:
                self.kit.append(block)

    def error_text(self, text: str):
        if not DENIAL.search(text[:300]):
            key = normalize_error(text)
            if key:
                self.errors.add(key)


def read_new_lines(path: Path, record: dict, end=None):
    """Yields complete lines after the stored offset, up to `end` when given; updates the record in place."""
    stat = path.stat()
    if record.get("inode") != stat.st_ino or stat.st_size < record.get("offset", 0):
        record["offset"] = 0
    record["inode"] = stat.st_ino
    with open(path, "rb") as handle:
        handle.seek(record["offset"])
        for raw in handle:
            if (end is not None and record["offset"] >= end) or not raw.endswith(b"\n"):
                break
            record["offset"] += len(raw)
            yield raw.decode("utf-8", errors="replace")


def scan_claude(path: Path, session: Session, record: dict, slugs, keywords, counters, end=None):
    pending = collections.OrderedDict()
    for line in read_new_lines(path, record, end):
        counters["lines"] += 1
        assistant = '"type":"assistant"' in line
        if assistant and slugs is not None:
            session.cited.update(m.group(0) for m in slugs.finditer(line))
        if assistant and '"name":"Bash"' in line:
            for tool_id in TOOL_ID.findall(line):
                pending[tool_id] = line
                if len(pending) > 200:
                    pending.popitem(last=False)
        human = '"kind":"human"' in line
        kit = assistant and "Kit [PROPOSAL]" in line
        error = '"is_error":true' in line
        memory = assistant and "/memory/" in line
        title = '"custom-title"' in line
        if not (human or kit or error or memory or title):
            continue
        try:
            data = json.loads(line)
        except ValueError:
            continue
        kind = data.get("type")
        message = data.get("message") or {}
        if title and kind == "custom-title":
            session.title = str(data.get("customTitle") or "")
            record["title"] = session.title
        origin = data.get("origin")
        if human and kind == "user" and isinstance(origin, dict) and origin.get("kind") == "human":
            text = "\n".join(texts(message.get("content")))
            if text.strip():
                session.owner_text(text, keywords)
        if kind == "assistant":
            for block in message.get("content") or []:
                if not isinstance(block, dict):
                    continue
                if kit and block.get("type") == "text":
                    session.kit_text(str(block.get("text", "")))
                if memory and block.get("type") == "tool_use":
                    file_path = str((block.get("input") or {}).get("file_path", ""))
                    if "/memory/" in file_path and file_path.endswith(".md"):
                        slug = Path(file_path).stem
                        (session.read if block.get("name") == "Read" else session.written).add(slug)
        if error and kind == "user" and isinstance(message.get("content"), list):
            for block in message["content"]:
                if not (isinstance(block, dict) and block.get("type") == "tool_result" and block.get("is_error")):
                    continue
                body = block["content"] if isinstance(block.get("content"), str) else "\n".join(texts(block.get("content")))
                guard = GUARD.search(body)
                if guard:
                    session.guard.append((guard.group(1), guard_class(guard.group(1), block.get("tool_use_id"), pending)))
                else:
                    session.error_text(body)


def guard_class(name: str, tool_id, pending) -> str:
    tool = {"rm -rf": "rm", "find -delete": "find"}.get(name)
    if not tool:
        return "n/a"
    line = pending.get(tool_id)
    if line is None:
        return "other"
    try:
        blocks = json.loads(line).get("message", {}).get("content") or []
    except ValueError:
        return "other"
    for block in blocks:
        if isinstance(block, dict) and block.get("id") == tool_id:
            return classify_targets(str((block.get("input") or {}).get("command", "")), tool)
    return "other"


def scan_codex(path: Path, session: Session, record: dict, keywords, counters, end=None):
    for line in read_new_lines(path, record, end):
        counters["lines"] += 1
        if not any(key in line for key in ("user_message", "UserMessage", "Kit [PROPOSAL]", "CommandExecution")):
            continue
        try:
            payload = json.loads(line).get("payload") or {}
        except ValueError:
            continue
        kind = payload.get("type")
        item = payload.get("item") if kind == "item_completed" else None
        if kind == "user_message":
            session.owner_text(str(payload.get("message", "")), keywords)
        elif kind == "agent_message":
            session.kit_text(str(payload.get("message", "")))
        elif kind == "message" and payload.get("role") == "assistant":
            for text in texts(payload.get("content")):
                session.kit_text(text)
        elif isinstance(item, dict) and item.get("type") == "UserMessage":
            text = "\n".join(texts(item.get("content")))
            if text.strip():
                session.owner_text(text, keywords, injected=text.lstrip().startswith(("#", "<")))
        elif isinstance(item, dict) and item.get("type") == "AgentMessage":
            for text in texts(item.get("content")):
                session.kit_text(text)
        elif isinstance(item, dict) and item.get("type") == "CommandExecution":
            if item.get("status") == "failed" or item.get("exit_code") not in (0, None):
                session.error_text(str(item.get("aggregated_output") or ""))


def write_private(path: Path, data) -> int:
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            json.dump(data, handle, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return path.stat().st_size


def remove_leftovers(state: Path):
    """Deletes what an interrupted run left: temporary files and an index whose extract was never written."""
    for path in state.glob("*.tmp"):
        path.unlink(missing_ok=True)
    for path in state.glob("index-*.json"):
        if not path.with_name("extract-" + path.name[len("index-"):]).is_file():
            path.unlink(missing_ok=True)


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def index_path(extract: Path) -> Path:
    return extract.with_name("index-" + extract.name[len("extract-"):])


def retained_sids(state: Path) -> set:
    """Sessions that reached a kept extract: its owner and kit entries and every session its index lists."""
    sids = set()
    for path in state.glob("extract-*.json"):
        data = read_json(path, {})
        if isinstance(data, dict):
            sids.update(entry["s"] for key in ("owner", "kit") for entry in data.get(key, [])
                        if isinstance(entry, dict) and isinstance(entry.get("s"), str))
        index = read_json(index_path(path), {})
        if isinstance(index, dict):
            sids.update(sid for sid in index if isinstance(sid, str))
    return sids


def purge_extracts(state: Path, sids: set):
    """Removes newly skipped sessions from the extracts of earlier runs and rebuilds their counts from the index.

    An extract without its index cannot be rebuilt exactly, so it is deleted.
    """
    for path in sorted(state.glob("extract-*.json")):
        data = read_json(path, None)
        index = read_json(index_path(path), None)
        if not isinstance(data, dict) or not isinstance(index, dict):
            path.unlink(missing_ok=True)
            index_path(path).unlink(missing_ok=True)
            continue
        owner_kit = {entry.get("s") for key in ("owner", "kit") for entry in data.get(key, []) if isinstance(entry, dict)}
        if not sids & (owner_kit | index.keys()):
            continue
        for key in ("owner", "kit"):
            data[key] = [entry for entry in data.get(key, []) if entry.get("s") not in sids]
        for sid in sids:
            index.pop(sid, None)
        data["sessions"] = len(index)
        data.update(aggregate(index))
        write_private(path, data)
        write_private(index_path(path), index)


def memory_slugs(claude_dir: Path):
    slugs = sorted({p.stem for p in claude_dir.glob("*/memory/*.md") if p.name != "MEMORY.md"}, key=len, reverse=True)
    return re.compile(r"\b(" + "|".join(map(re.escape, slugs)) + r")\b") if slugs else None


def aggregate(index: dict) -> dict:
    """The errors, memory and guard sections from what each session added."""
    errors = collections.defaultdict(list)
    memory = collections.defaultdict(lambda: {"cited": [], "read": 0, "written": 0})
    guard = collections.defaultdict(lambda: {"blocks": 0, "sessions": set(), "temp": 0, "other": 0})
    for sid, added in index.items():
        for key in added.get("errors", []):
            errors[key].append(sid)
        for slug in added.get("cited", []):
            memory[slug]["cited"].append(sid)
        for slug in added.get("read", []):
            memory[slug]["read"] += 1
        for slug in added.get("written", []):
            memory[slug]["written"] += 1
        for name, target in added.get("guard", []):
            entry = guard[name]
            entry["blocks"] += 1
            entry["sessions"].add(sid)
            if target in ("temp", "other"):
                entry[target] += 1
    repeated = sorted(((k, v) for k, v in errors.items() if len(v) >= 2), key=lambda kv: (-len(kv[1]), kv[0]))
    return {
        "errors": [{"e": k, "sessions": len(v), "examples": v[:EXAMPLES]} for k, v in repeated[:ERRORS_MAX]],
        "memory": sorted(
            ({"slug": k, "cited": len(v["cited"]), "read": v["read"], "written": v["written"],
              "examples": v["cited"][:EXAMPLES]} for k, v in memory.items()),
            key=lambda entry: (-entry["cited"], entry["slug"]),
        ),
        "guard": sorted(
            ({"kind": k, "blocks": v["blocks"], "sessions": len(v["sessions"]), "temp": v["temp"], "other": v["other"]}
             for k, v in guard.items()),
            key=lambda entry: -entry["blocks"],
        ),
    }


def build_extract(sessions, since):
    """The extract and its index: what each session added, error keys limited to those the extract lists."""
    index = {s.sid: {"errors": sorted(s.errors), "cited": sorted(s.cited), "read": sorted(s.read),
                     "written": sorted(s.written), "guard": [list(g) for g in s.guard]} for s in sessions}
    extract = {
        "version": 1,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "since": since,
        "sessions": len(sessions),
        "owner": [{"s": s.sid, "t": t} for s in sessions for t in s.owner],
        "kit": [{"s": s.sid, "t": t} for s in sessions for t in s.kit],
        **aggregate(index),
    }
    kept = {entry["e"] for entry in extract["errors"]}
    for added in index.values():
        added["errors"] = [key for key in added["errors"] if key in kept]
    return extract, index


def check_prefix(path: Path, sid: str, source: str, end: int, keywords) -> Session:
    """Reads lines [0, end) of a session again for its title and personal words only; nothing else is kept."""
    session = Session(sid)
    record = {"offset": 0, "inode": path.stat().st_ino}
    if source == "claude":
        scan_claude(path, session, record, None, keywords, collections.Counter(), end)
    else:
        scan_codex(path, session, record, keywords, collections.Counter(), end)
    return session


def default_state() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "ai-kit" / "session-audit"


def default_codex() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "sessions"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--state", type=Path, default=default_state())
    parser.add_argument("--claude-dir", type=Path, default=Path.home() / ".claude" / "projects")
    parser.add_argument("--codex-dir", type=Path, default=default_codex())
    parser.add_argument("--if-older-days", type=float, help="skip the run while the last stamp is newer than N days")
    parser.add_argument("--first-run-days", type=float, default=7.0,
                        help="on a file never seen, read it only when modified in the last N days (first run) "
                             "or since the last run")
    args = parser.parse_args(argv)
    state = args.state
    stamp = state / "last-run"
    now = time.time()
    if args.if_older_days is not None and stamp.is_file():
        age = (now - stamp.stat().st_mtime) / 86400
        if age < args.if_older_days:
            print(json.dumps({"ran": 0, "age_days": round(age, 2)}))
            return 0
    started = time.monotonic()
    state.mkdir(parents=True, exist_ok=True)
    os.chmod(state, 0o700)
    offsets = read_json(state / "offsets.json", {})
    skipped = read_json(state / "skipped.json", {})
    since_epoch = stamp.stat().st_mtime if stamp.is_file() else now - args.first_run_days * 86400
    since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(since_epoch)) if stamp.is_file() else None
    excludes = load_excludes(state)
    keywords = load_keywords(state)
    digest = keywords_digest(keywords)
    remove_leftovers(state)
    titles, titles_ok = codex_titles(codex_db_homes(args.codex_dir.parent))
    retained = retained_sids(state)
    slugs = memory_slugs(args.claude_dir)

    def title_of(sid: str, record: dict) -> str:
        return titles.get(sid[3:], "") if sid.startswith("cx-") else record.get("title", "")
    files = [(p, p.stem, "claude") for p in sorted(args.claude_dir.glob("*/*.jsonl"))]
    for p in sorted(Path(f) for f in glob.glob(str(args.codex_dir / "**" / "rollout-*.jsonl"), recursive=True)):
        match = CODEX_ID.search(p.name)
        files.append((p, "cx-" + (match.group(1) if match else p.stem), "codex"))
    counters = collections.Counter()
    sessions, newly_skipped = [], set()
    present = {sid for _, sid, _ in files}
    for sid in sorted(set(offsets) | retained):
        if sid in skipped:
            continue
        record = offsets.get(sid, {})
        if excluded(sid, title_of(sid, record), excludes):
            skipped[sid] = "excluded"
            newly_skipped.add(sid)
        elif sid in retained and sid not in present and record.get("checked") != digest:
            # A kept session whose transcript left the disk cannot be checked against new keywords: drop it.
            skipped[sid] = "gone"
            newly_skipped.add(sid)
    for path, sid, source in files:
        counters["files"] += 1
        record = offsets.get(sid)
        size = path.stat().st_size
        if record is None:
            record = offsets[sid] = {"offset": 0}
            if path.stat().st_mtime < since_epoch:
                record.update(offset=size, inode=path.stat().st_ino)
                continue
        if sid in skipped:
            record.update(offset=size, inode=path.stat().st_ino)
            continue
        grew = not (size == record.get("offset") and path.stat().st_ino == record.get("inode"))
        before = record.get("offset", 0) if path.stat().st_ino == record.get("inode") else 0
        # The lines before the offset were never checked under these keywords (a new keyword, or a file first seen
        # mid-way): check them before new lines reach an extract, and now for a session a kept extract holds.
        if record.get("checked") != digest and before > 0 and (grew or sid in retained):
            prior = check_prefix(path, sid, source, before, keywords)
            if source == "claude" and prior.title:
                record["title"] = prior.title
            record["checked"] = digest
            if prior.personal or excluded(sid, title_of(sid, record), excludes):
                skipped[sid] = "personal" if prior.personal else "excluded"
                newly_skipped.add(sid)
                record.update(offset=size, inode=path.stat().st_ino)
                continue
        if not grew:
            continue
        if source == "codex" and excludes and not titles_ok:
            # Codex titles could not be read, so a title in exclude.txt cannot be matched yet: the new lines wait
            # for a later run (the keyword and id checks above already ran). A new file keeps its offset-0 record.
            counters["codex_deferred"] += 1
            continue
        counters["files_read"] += 1
        session = Session(sid, title_of(sid, record))
        if source == "claude":
            scan_claude(path, session, record, slugs, keywords, counters)
        else:
            scan_codex(path, session, record, keywords, counters)
        counters["bytes"] += max(record["offset"] - before, 0)
        record["checked"] = digest
        counters["owner_msgs"] += session.owner_msgs
        if excluded(sid, session.title, excludes) or session.personal:
            skipped[sid] = "personal" if session.personal else "excluded"
            newly_skipped.add(sid)
            continue
        sessions.append(session)
    if newly_skipped:
        purge_extracts(state, newly_skipped)
    extract, index = build_extract(sessions, since)
    name = "extract-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(now)) + ".json"
    write_private(index_path(state / name), index)
    extract_bytes = write_private(state / name, extract)
    for old in sorted(state.glob("extract-*.json"))[:-KEEP_EXTRACTS]:
        old.unlink()
        index_path(old).unlink(missing_ok=True)
    live = present | retained_sids(state)
    write_private(state / "offsets.json", {sid: rec for sid, rec in offsets.items() if sid in live})
    write_private(state / "skipped.json", skipped)
    fd = os.open(stamp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    os.close(fd)
    os.utime(stamp, (now, now))
    print(json.dumps({
        "ran": 1,
        "files": counters["files"],
        "files_read": counters["files_read"],
        "bytes": counters["bytes"],
        "lines": counters["lines"],
        "sessions": len(sessions),
        "skipped_sessions": len(newly_skipped),
        "owner_msgs": counters["owner_msgs"],
        "owner_cues": len(extract["owner"]),
        "kit_blocks": len(extract["kit"]),
        "error_kinds_2plus": len(extract["errors"]),
        "memory_slugs_cited": sum(1 for entry in extract["memory"] if entry["cited"]),
        "guard_blocks": sum(entry["blocks"] for entry in extract["guard"]),
        "codex_deferred": counters["codex_deferred"],
        "extract_bytes": extract_bytes,
        "seconds": round(time.monotonic() - started, 2),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
