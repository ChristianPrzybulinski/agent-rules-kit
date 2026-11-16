#!/usr/bin/env python3
"""The no-model PR gates — importable module and CI entry point (upstreamed from a consumer project's PR gates).

A review loop imports the pure rule functions from here so the loop and the `pr-contract` GitHub
Actions check enforce the same code. Run as a script it needs no `gh` CLI and no checkout: the report
reads the PR, the linked backlog issue and the head's checks through the REST API with the token from
`GH_TOKEN` (in CI that is a PAT, because a PR repo's GITHUB_TOKEN cannot read the backlog's issues).

    pr_gates.py --config gates.json --repo <name> --pr 14            Markdown report, exit 1 on failure
    pr_gates.py proof-commands --config gates.json --repo <name> --pr 14
                                                                   the allowlisted proof commands, one per line

The config file (JSON) names the GitHub owner, the backlog repository whose issues the PR contract
closes, and the rule inputs:

    {"owner": "org", "backlog_repo": "project-docs",
     "review_context": "org/review",            # optional merge-guard commit status, not CI — dropped
                                               # from the head's check evaluation
     "repos": {"project-docs": {"require_fragment": true}, "project-server": {}},
     "protected_paths": {"contract": ["protocol/**"], "migration": ["**/db/migration/**"]},
     "generated_neighbours": [".uid", ".import", ".translation"],
     "proof_allowlist": ["python3", "grep", "./mvnw"],
     "expected_red_checks": {"<repo>": {"<check name>": {"until_issue_closed": <issue>, "why": "..."}}}}

`owner`, `backlog_repo`, `repos` and `proof_allowlist` are required: a config without one, or with a value of the
wrong type, exits 2 naming the key. `--repo` is the PR's repository name — a key of `repos`. Report rules:
- **no-task**: a body without `Closes <owner>/<backlog_repo>#N` has no task issue to check against, so
  the task gates (Closes link, proof block, the three scope rules, the changelog fragment and the
  proof allowlist) are reported `skip` and only the CI state is evaluated — architect PRs pass.
- **pending CI**: reported as `pending`, not failed — the required checks themselves hold the merge.
  A red check still fails the report.
- The proof commands are not executed here; each repo's `proof` job runs them with its own toolchain.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import posixpath
import re
import shlex
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG: dict = {}
OWNER = ""
BACKLOG = ""
# Optional commit status that is a merge guard, never CI: dropped before `ci_state` reads the head.
REVIEW_CONTEXT: str | None = None
FRAGMENT_RE = re.compile(r"^changelog\.d/[^/]+\.(added|changed|deprecated|removed|fixed|security)\.md$")


REQUIRED_KEYS = ("owner", "backlog_repo", "repos", "proof_allowlist")  # every task PR's report reads the allowlist


def _strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _red_entry(value) -> bool:
    return (isinstance(value, dict) and isinstance(value.get("glob"), str) and isinstance(value.get("command"), str)
            and isinstance(value.get("cwd", "."), str))


# key: (check, the shape it wants). A string where a list belongs is still iterable, so an unchecked value would be
# read per character (`"protected/**"` would protect every path through its `*`).
_CONFIG_SHAPES = {
    "owner": (lambda v: isinstance(v, str), "a string"),
    "backlog_repo": (lambda v: isinstance(v, str), "a string"),
    "review_context": (lambda v: isinstance(v, str), "a string"),
    "repos": (lambda v: isinstance(v, dict) and all(isinstance(r, dict) for r in v.values()),
              "an object mapping each repository name to an object"),
    "protected_paths": (lambda v: isinstance(v, dict) and all(_strings(g) for g in v.values()),
                        "an object mapping each label to a list of globs"),
    "generated_neighbours": (_strings, "a list of strings"),
    "proof_allowlist": (_strings, "a list of strings"),
    "proof_script_runners": (lambda v: isinstance(v, dict) and all(_strings(o) for o in v.values()),
                             "an object mapping a program to a list of option strings"),
    "expected_red_checks": (lambda v: isinstance(v, dict) and all(
        isinstance(checks, dict) and all(isinstance(rule, dict) for rule in checks.values()) for checks in v.values()),
        "an object mapping a repository to {check name: {until_issue_closed, why}}"),
    "red": (lambda v: isinstance(v, list) and all(_red_entry(e) for e in v),
            "a list of {glob, command[, cwd]} objects with string values"),
}


def config_errors(config, required=()) -> list[str]:
    """One message per key of `config` whose value has the wrong type, and per `required` key that is missing; each
    message starts with the key. Keys this module does not know are left alone."""
    if not isinstance(config, dict):
        return [f"the config must be a JSON object, not {type(config).__name__}"]
    errors = [f"{key} is required" for key in required if key not in config]
    for key, (ok, shape) in _CONFIG_SHAPES.items():
        if key in config and not ok(config[key]):
            errors.append(f"{key} must be {shape}, not {json.dumps(config[key])}")
    return errors


class ConfigError(ValueError):
    """A gates config that `config_errors` refuses."""


def configure(path) -> None:
    """Load the gates JSON (the module docstring lists the keys) into the module globals the pure
    helpers and the report read. Called once by `main`; an importer passes the same fields in-line. A config
    `config_errors` refuses raises ConfigError and leaves the globals as they were."""
    global CONFIG, OWNER, BACKLOG, REVIEW_CONTEXT
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = config_errors(data, required=REQUIRED_KEYS)
    if errors:
        raise ConfigError("; ".join(errors))
    CONFIG = data
    OWNER = CONFIG["owner"]
    BACKLOG = CONFIG["backlog_repo"]
    REVIEW_CONTEXT = CONFIG.get("review_context")


# --------------------------------------------------------------------------- pure helpers


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def body_lines(text: str | None) -> list[str]:
    """A PR or issue body's lines, split only on the CommonMark line endings (CRLF, CR, LF): str.splitlines() also
    breaks on VT, FF, \\x1c-\\x1e, NEL, U+2028 and U+2029, which GitHub renders inside a line, so a heading the reader
    never sees could start a section."""
    return re.split(r"\r\n|\r|\n", text or "")


def sections(body: str | None) -> dict[str, str]:
    """Split a markdown body into {heading: text} on `## ` headings (lines as `body_lines` splits them)."""
    out: dict[str, list[str]] = {}
    current = None
    for line in body_lines(body):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            current = m.group(1)
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def parse_files_cell(text: str | None) -> list[str]:
    return re.findall(r"`([^`]+)`", text or "")


def expand_braces(pattern: str) -> list[str]:
    m = re.search(r"\{([^{}]*)\}", pattern)
    if not m:
        return [pattern]
    head, tail = pattern[: m.start()], pattern[m.end():]
    return [x for alt in m.group(1).split(",") for x in expand_braces(head + alt + tail)]


def glob_to_regex(pattern: str) -> str:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return "^" + out + "$"


def path_matches(path: str, pattern: str) -> bool:
    return any(re.match(glob_to_regex(p), path) for p in expand_braces(pattern))


def repo_relative(pattern: str, repo: str) -> str | None:
    prefix = repo + "/"
    return pattern[len(prefix):] if pattern.startswith(prefix) else None


def files_cell(secs: dict[str, str]) -> str | None:
    """The issue's `Files`/`Files (owned areas)` cell — the template renamed the heading 2026-10-06."""
    return next((v for k, v in secs.items() if k.split("(", 1)[0].strip() == "Files"), None)


def generated_neighbour(path: str, patterns: list[str], suffixes: list[str]) -> bool:
    """`path` is generated next to an owned file: same directory, same stem, a generated suffix.
    `.uid`/`.import` append to the source name (`a.gd` → `a.gd.uid`); `.translation` replaces the
    source extension with a locale (`text.csv` → `text.en_US.translation`)."""
    gen = next((s for s in suffixes if path.endswith(s)), None)
    if gen is None:
        return False
    base = path[: -len(gen)]
    for pat in patterns:
        for e in expand_braces(pat):
            if path_matches(base, e):
                return True
            stem = re.sub(r"\.[^./]+$", "", e)
            if stem != e and path_matches(path, f"{stem}.*{gen}"):
                return True
    return False


def scope_violations(changed: list[str], areas: list[str], repo: str,
                     generated_suffixes: list[str] | None = None,
                     extra: tuple[str, ...] = ("changelog.d/**",)) -> list[str]:
    """Rule 1 — owned areas: a changed path is in scope when it matches a glob of the issue's `Files`
    cell, is a generated neighbour of a matched path, or is a `changelog.d/` fragment."""
    patterns = [p for p in (repo_relative(x, repo) for x in areas) if p] + list(extra)
    suffixes = CONFIG.get("generated_neighbours", []) if generated_suffixes is None else generated_suffixes
    return [f for f in changed if not any(path_matches(f, p) for p in patterns)
            and not generated_neighbour(f, patterns, suffixes)]


def protected_violations(changed: list[str], issue_labels: list[str], issue: int | None,
                         protected: dict[str, list[str]]) -> list[str]:
    """Rule 2 — a changed path under a `protected_paths` glob fails unless the issue carries the
    matching label, even when the `Files` cell allows it."""
    ref = f"#{issue}" if issue else "the issue"
    out = []
    for f in changed:
        need = next((label for label, globs in protected.items()
                     if label not in issue_labels and any(path_matches(f, g) for g in globs)), None)
        if need:
            out.append(f"protected path {f} needs label {need} on {ref}")
    return out


def is_generated(path: str, suffixes: list[str]) -> bool:
    return any(path.endswith(s) for s in suffixes)


def overlap_violations(changed: list[str], other_prs: dict[int, list[str]], pr_labels: list[str],
                       suffixes: list[str]) -> list[str]:
    """Rule 3 — the diff must not intersect another open, non-draft PR's diff on a non-generated file,
    unless the PR carries `overlap-ok` (the architect decides at review)."""
    if "overlap-ok" in pr_labels:
        return []
    mine = {f for f in changed if not is_generated(f, suffixes)}
    out = []
    for num, files in sorted(other_prs.items()):
        hits = sorted(f for f in mine & set(files) if not is_generated(f, suffixes))
        if hits:
            out.append(f"overlaps #{num} on {', '.join(hits)}")
    return out


def proof_hash(commands: list[str]) -> str:
    return hashlib.sha256("\n".join(commands).encode("utf-8")).hexdigest()[:16]


def parse_proof(body: str | None) -> list[str]:
    m = re.search(r"```proof[ \t]*(?:\r\n|\r|\n)(.*?)```", body or "", re.S)
    if not m:
        return []
    lines = [ln.strip() for ln in body_lines(m.group(1))]
    return [ln for ln in lines if ln and not ln.startswith("#") and not ln.startswith("<")]


_FORBIDDEN = re.compile(r"\$\(|`|\b(sudo|curl|wget|ssh|scp|rsync|rm|mv|chmod|chown|eval|exec|source|kill|nc)\b")
_SAFE_REDIRECT = re.compile(r"\d?>&\d|\d?>\s*/dev/null|&>\s*/dev/null")


def _mask_quotes(cmd: str) -> str:
    """`cmd` with every character inside quotes replaced by `x` (same length), so `<`, `>`, `|` or `;`
    inside a quoted argument (`grep -q "<suppress "`) are not read as shell syntax."""
    out, quote, i = [], None, 0
    while i < len(cmd):
        ch = cmd[i]
        if quote is None:
            quote = ch if ch in "'\"" else None
            out.append(ch)
        elif quote == '"' and ch == "\\" and i + 1 < len(cmd):
            out.append("xx")
            i += 2
            continue
        elif ch == quote:
            quote = None
            out.append(ch)
        else:
            out.append("x")
        i += 1
    return "".join(out)


_ANCHOR_NAME = re.compile(r"\{[A-Za-z_]\w*\}|[A-Za-z_]\w*")
_PLAIN, _DOUBLE, _SINGLE, _ESCAPED = "plain", "double", "single", "escaped"
DOTDOT = "a `..` path step, refused in a component's proof: name the path from the folder the proof runs in"
UNPREDICTABLE = "shell expansion outside a leading $NAME, ${NAME} or ~/ anchor: quote it or name the path"
INLINE_CODE = "an interpreter given inline code: put the code in a script file and run that"
# Interpreter (its name without a version suffix) -> the option letters and long options that hand it inline code.
_INLINE = {"python": ("c", ()), "bash": ("c", ()), "sh": ("c", ()), "zsh": ("c", ()), "dash": ("c", ()),
           "ksh": ("c", ()), "node": ("ep", ("--eval", "--print")), "perl": ("eE", ()), "ruby": ("e", ()),
           "env": ("S", ("--split-string",))}


def _shell_words(text: str) -> list:
    """The words of one simple command as lists of (quoting, char): `plain` (unquoted), `double` (inside "..."),
    `single` (inside '...') or `escaped` (after a backslash). Unquoted blanks and operators end a word; an unclosed
    quote raises ValueError. shlex drops the quoting, which the component rules need to know what bash expands."""
    words, word, started, i, n = [], [], False, 0, len(text)
    while i < n:
        ch = text[i]
        if ch in " \t\n;&|<>()":
            if started:
                words.append(word)
            word, started, i = [], False, i + 1
        elif ch == "\\":
            if i + 1 < n and text[i + 1] != "\n":
                word.append((_ESCAPED, text[i + 1]))
                started = True
            i += 2
        elif ch == "'":
            end = text.find("'", i + 1)
            if end < 0:
                raise ValueError("unclosed single quote")
            word += [(_SINGLE, c) for c in text[i + 1:end]]
            started, i = True, end + 1
        elif ch == '"':
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n and text[i + 1] in '$`"\\\n':
                    if text[i + 1] != "\n":
                        word.append((_ESCAPED, text[i + 1]))
                    i += 2
                else:
                    word.append((_DOUBLE, text[i]))
                    i += 1
            if i >= n:
                raise ValueError("unclosed double quote")
            started, i = True, i + 1
        else:
            word.append((_PLAIN, ch))
            started, i = True, i + 1
    if started:
        words.append(word)
    return words


def _anchor_end(word: list) -> int | None:
    """The index after a leading `$NAME`, `${NAME}` or `~` anchor, written in one quoting, when it ends the word or a
    `/` follows it; 0 when the word starts with no `$` or unquoted `~`; None for any other leading `$` or `~`
    (`${NAME:-x}`, `$NAMEx`, `$1`, `$'...'`, `~user`, `~+`)."""
    if not word:
        return 0
    kind, ch = word[0]
    if ch == "~" and kind == _PLAIN:
        return 1 if len(word) == 1 or word[1][1] == "/" else None
    if ch != "$" or kind not in (_PLAIN, _DOUBLE):
        return 0
    run, j = [], 1
    while j < len(word) and word[j][0] == kind:
        run.append(word[j][1])
        j += 1
    m = _ANCHOR_NAME.match("".join(run))
    end = 1 + m.end() if m else None
    return end if end is not None and (end == len(word) or word[end][1] == "/") else None


def _expands(word: list) -> bool:
    """Whether bash may expand `word` beyond its leading anchor (`_anchor_end`). Single-quoted and escaped characters
    are literal. Refused after the anchor: a `$` outside single quotes; an unquoted `~` that starts the word or follows
    `=` or `:`; an unquoted `{` with an unquoted `}` after it, other than an empty `{}`; an unquoted `*`, `?` or `[` in
    a path component that starts with `.`, the only kind that can match `.` or `..` (a bracket never matches a leading
    dot)."""
    start = _anchor_end(word)
    if start is None:
        return True
    rest = word[start:]
    for i, (kind, ch) in enumerate(rest):
        if ch == "$" and kind in (_PLAIN, _DOUBLE):
            return True
        if kind != _PLAIN:
            continue
        if ch == "~" and (start + i == 0 or (i and rest[i - 1] in ((_PLAIN, "="), (_PLAIN, ":")))):
            return True
        if ch == "{" and (_PLAIN, "}") in rest[i + 2:]:
            return True
    first, glob = None, False
    for kind, ch in word + [(_PLAIN, "/")]:
        if ch == "/":
            if glob and first == ".":
                return True
            first, glob = None, False
            continue
        first = ch if first is None else first
        glob = glob or (kind == _PLAIN and ch in "*?[")
    return False


def _dotdot(text: str) -> bool:
    """Whether `text` holds a `..` path step: a run of exactly two dots, unless a letter or digit stands on both sides
    (a revision range `A..B`). The quoting does not matter: `grep -f '../x'` reads outside as much as `cat ../x`."""
    for m in re.finditer(r"\.+", text):
        if len(m.group()) != 2:
            continue
        before, after = text[m.start() - 1:m.start()], text[m.end():m.end() + 1]
        if not all(c.isascii() and c.isalnum() for c in (before, after) if c) or not (before and after):
            return True
    return False


def _inline_code(words: list) -> bool:
    """Whether the program (words[0]) is an interpreter of `_INLINE` and a later word hands it inline code: one of
    its long options (alone or with `=value`) or a short-option cluster holding one of its letters (`-c`, `-Ic`)."""
    name = re.sub(r"[\d.]+$", "", posixpath.basename("".join(ch for _, ch in words[0])))
    letters, long_options = _INLINE.get(name, ("", ()))
    for word in words[1:]:
        text = "".join(ch for _, ch in word)
        if any(text == o or text.startswith(o + "=") for o in long_options):
            return True
        if re.fullmatch(r"-[A-Za-z]+", text) and any(letter in text[1:] for letter in letters):
            return True
    return False


def command_allowed(cmd: str, allowlist, cwd: str | None = None) -> tuple[bool, str]:
    """A proof/close_when command may only chain allowlisted programs; no subshells, files or network tools.

    `$(` and backticks are refused even inside quotes: bash expands them inside double quotes. `! git diff` without
    `--quiet` or `--exit-code` is refused: `git diff` exits 0 whether or not it prints, so the negation never passes.
    With `cwd` (KIT-073; the component's folder, `.` for the root) three more rules hold (KIT-080): no interpreter
    given inline code (`_inline_code`), no shell expansion outside a leading anchor (`_expands`) and no `..` path step
    (`_dotdot`). They are hygiene, not isolation: an allowlisted program can still read any file, and an absolute or
    anchored path still reads outside the component."""
    if _FORBIDDEN.search(cmd):
        return False, "forbidden construct"
    rest = _SAFE_REDIRECT.sub(lambda m: " " * len(m.group()), _mask_quotes(cmd))
    if ">" in rest or "<" in rest:
        return False, "redirection other than to /dev/null"
    segments, start = [], 0
    for op in re.finditer(r"\|\||&&|;|\||&", rest):  # a single & starts a background job: another command
        segments.append(cmd[start:op.start()])
        start = op.end()
    segments.append(cmd[start:])
    for segment in segments:
        try:
            tokens = shlex.split(segment)
        except ValueError:
            return False, "unbalanced quotes"
        negated = False
        while tokens and tokens[0] == "!":
            negated, tokens = not negated, tokens[1:]
        if not tokens:
            continue
        if tokens[0] not in allowlist:
            return False, f"'{tokens[0]}' not in allowlist"
        if negated and tokens[:2] == ["git", "diff"] and not {"--quiet", "--exit-code"} & set(tokens):
            return False, "`! git diff` without --quiet or --exit-code never passes; use `git diff --quiet …`"
        if cwd is not None:
            try:
                words = _shell_words(segment)
            except ValueError:
                return False, "unbalanced quotes"
            while words and words[0] == [(_PLAIN, "!")]:
                words = words[1:]
            if _inline_code(words):
                return False, f"{tokens[0]}: {INLINE_CODE}"
            for word in words:
                text = "".join(ch for _, ch in word)
                if _expands(word):
                    return False, f"{text}: {UNPREDICTABLE}"
                if _dotdot(text):
                    return False, f"{text}: {DOTDOT}"
    return True, ""


def label_names(obj: dict) -> list[str]:
    return [lb["name"] for lb in obj.get("labels", [])]


_OK = {"SUCCESS", "SKIPPED", "NEUTRAL"}
_PENDING = {"PENDING", "IN_PROGRESS", "QUEUED", "EXPECTED", "WAITING", "REQUESTED"}


def ci_state(checks: list[dict], expected_red: dict, closed_issues: set[int]) -> str:
    if not checks:
        return "none"
    states = []
    for c in checks:
        s = (c.get("state") or "").upper()
        if s in _OK:
            states.append("green")
        elif s in _PENDING:
            states.append("pending")
        else:
            rule = expected_red.get(c.get("name", ""))
            allowed = rule and rule.get("until_issue_closed") not in closed_issues
            states.append("green" if allowed else "red")
    if "red" in states:
        return "red"
    return "pending" if "pending" in states else "green"


_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[@-_]")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def clean_output(text: str) -> str:
    """Proof output as plain text: ANSI colour codes and other control characters removed. Godot's coloured
    log once reached a gates comment as an invalid JSON escape, and the loop could not read its own result."""
    return _CONTROL.sub("", _ANSI.sub("", text))


def linked_issue(body: str | None) -> int | None:
    m = re.search(r"Closes\s+" + re.escape(f"{OWNER}/{BACKLOG}") + r"#(\d+)", body or "")
    return int(m.group(1)) if m else None


# --------------------------------------------------------------------------- gate rows (loop + CI)


def evaluate_gates(repo: str, *, issue_n: int | None, issue: dict, changed: list[str], proof: list[str],
                   pr_labels: list[str], other_prs: dict[int, list[str]], ci: str) -> list[dict]:
    """The gate rows a review loop posts and the `pr-contract` check reports, as {gate, ok, detail}
    in that order. Fetching differs per caller (the loop uses `gh`, the report the REST API); the
    rules live only here."""
    results: list[dict] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append({"gate": name, "ok": ok, "detail": detail})

    check("contract: Closes link", issue_n is not None, "" if issue_n else f"no `Closes {OWNER}/{BACKLOG}#N`")
    check("contract: proof block", bool(proof), "" if proof else "no ```proof block with commands")
    secs = sections(issue.get("body"))
    violations = scope_violations(changed, parse_files_cell(files_cell(secs)), repo)
    check("scope: owned areas", not violations, ", ".join(violations[:10]))
    protected = protected_violations(changed, label_names(issue), issue_n,
                                   CONFIG.get("protected_paths", {}))
    check("scope: protected paths", not protected, "; ".join(protected[:10]))
    overlap = overlap_violations(changed, other_prs, pr_labels,
                               CONFIG.get("generated_neighbours", []))
    check("scope: no overlap with open PRs", not overlap, "; ".join(overlap[:5]))
    if CONFIG["repos"][repo].get("require_fragment"):
        has_fragment = any(FRAGMENT_RE.match(f) for f in changed)
        check("changelog: fragment, no CHANGELOG.md edit", has_fragment and "CHANGELOG.md" not in changed,
              "" if has_fragment else "missing changelog.d/<id>.<type>.md")
    disallowed = [f"{c} ({why})" for c in proof for ok, why in [command_allowed(c, CONFIG["proof_allowlist"])] if not ok]
    check("proof: commands allowlisted", not disallowed, "; ".join(disallowed))
    check("ci: green on head", ci in ("green", "none"), f"ci={ci}")
    return results


# --------------------------------------------------------------------------- CI report (REST API)

API = "https://api.github.com"
# The reusable workflow's own checks: they are still running while the report is computed, so they
# would read `pending` forever. A `uses:` job reports as `caller / callee` — match the first
# segment too. The configured `review_context` is always excluded (merge guard, not CI).
_SELF_CHECKS = ("contract", "proof")


def _is_self_check(name: str) -> bool:
    return name in _SELF_CHECKS or name.split(" / ")[0] in _SELF_CHECKS
_RUN_OK = {"success": "SUCCESS", "skipped": "SKIPPED", "neutral": "NEUTRAL"}
TASK_GATES = ("contract: Closes link", "contract: proof block", "scope: owned areas",
              "scope: protected paths", "scope: no overlap with open PRs",
              "changelog: fragment, no CHANGELOG.md edit", "proof: commands allowlisted")


def _api(token: str, path: str, params: dict | None = None):
    url = API + path + (("?" + urllib.parse.urlencode(params)) if params else "")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}",
                                               "Accept": "application/vnd.github+json",
                                               "X-GitHub-Api-Version": "2022-11-28",
                                               "User-Agent": "pr-gates"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GET {url}: HTTP {e.code} — {e.read()[:200].decode('utf-8', 'replace')}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"GET {url}: {e.reason}")


def _api_list(token: str, path: str, params: dict | None = None) -> list:
    """Every page of a bare list endpoint (per_page=100, at most 10 pages)."""
    out = []
    for page in range(1, 11):
        items = _api(token, path, {**(params or {}), "per_page": 100, "page": page})
        out += items
        if len(items) < 100:
            break
    return out


def _check_runs(token: str, repo: str, sha: str) -> list[dict]:
    out = []
    for page in range(1, 11):
        data = _api(token, f"/repos/{OWNER}/{repo}/commits/{sha}/check-runs",
                    {"per_page": 100, "page": page})
        page_runs = data.get("check_runs", [])
        out += page_runs
        if len(page_runs) < 100:
            break
    return out


def _closed(token: str, numbers: set[int]) -> set[int]:
    return {n for n in numbers
            if (_api(token, f"/repos/{OWNER}/{BACKLOG}/issues/{n}").get("state") or "").upper() == "CLOSED"}


def _check_entries(token: str, repo: str, sha: str) -> list[dict]:
    """{name, state} per check-run and commit status on `sha`, in the `gh pr checks` shape `ci_state`
    reads; the report's own checks and the configured `review_context` are excluded."""
    entries = []
    for r in _check_runs(token, repo, sha):
        if _is_self_check(r.get("name") or ""):
            continue
        state = _RUN_OK.get(r.get("conclusion"), "FAILURE") if r.get("status") == "completed" else "PENDING"
        entries.append({"name": r.get("name"), "state": state})
    data = _api(token, f"/repos/{OWNER}/{repo}/commits/{sha}/status", {"per_page": 100})
    for s in data.get("statuses", []):
        name = s.get("context") or ""
        if name and not _is_self_check(name) and name != REVIEW_CONTEXT:
            entries.append({"name": name, "state": (s.get("state") or "").upper()})
    return entries


def _ci_row(ci: str) -> dict:
    """CI pending is reported, not failed — unlike the loop, a CI job cannot re-check later, and the
    required checks themselves hold the merge. Red still fails."""
    status = "pass" if ci in ("green", "none") else "pending" if ci == "pending" else "fail"
    return {"gate": "ci: green on head", "status": status,
            "detail": f"ci={ci}" + (" — the required checks hold the merge" if ci == "pending" else "")}


def _ci_state(token: str, repo: str, sha: str) -> str:
    expected = CONFIG.get("expected_red_checks", {}).get(repo, {})
    closed = _closed(token, {r["until_issue_closed"] for r in expected.values()})
    return ci_state(_check_entries(token, repo, sha), expected, closed)


def _open_pr_files(token: str, repo: str, exclude: int) -> dict[int, list[str]]:
    """The changed files of every other open, non-draft PR — the overlap gate's input."""
    prs = _api_list(token, f"/repos/{OWNER}/{repo}/pulls", {"state": "open"})
    return {p["number"]: [f["filename"] for f in _api_list(token, f"/repos/{OWNER}/{repo}/pulls/{p['number']}/files")]
            for p in prs if p["number"] != exclude and not p.get("draft")}


_MARK = {"pass": "✅", "fail": "❌", "skip": "⏭️", "pending": "⏳"}


def gate_report(repo: str, n: int, token: str) -> tuple[str, bool]:
    """The Markdown report the `pr-contract` check writes to the step summary; True when no row failed."""
    pr = _api(token, f"/repos/{OWNER}/{repo}/pulls/{n}")
    head = pr["head"]["sha"]
    body = pr.get("body") or ""
    issue_n = linked_issue(body)
    changed = [f["filename"] for f in _api_list(token, f"/repos/{OWNER}/{repo}/pulls/{n}/files")]
    proof = parse_proof(body)
    rows: list[dict] = []
    if issue_n is None:
        reason = f"no-task: no `Closes {OWNER}/{BACKLOG}#N`"
        rows += [{"gate": name, "status": "skip", "detail": reason} for name in TASK_GATES]
        rows.append(_ci_row(_ci_state(token, repo, head)))
    else:
        issue = _api(token, f"/repos/{OWNER}/{BACKLOG}/issues/{issue_n}")
        ci = _ci_state(token, repo, head)
        for r in evaluate_gates(repo, issue_n=issue_n, issue=issue, changed=changed, proof=proof,
                                pr_labels=label_names(pr), other_prs=_open_pr_files(token, repo, n), ci=ci):
            rows.append(_ci_row(ci) if r["gate"] == "ci: green on head"
                        else {"gate": r["gate"], "status": "pass" if r["ok"] else "fail", "detail": r["detail"]})
    ok = all(r["status"] != "fail" for r in rows)
    lines = [f"## pr-contract — {repo}#{n} on `{head[:9]}`", ""]
    if issue_n is None:
        lines += [f"`no-task` — the body has no `Closes {OWNER}/{BACKLOG}#N`; "
                  "the task gates do not apply to architect PRs.", ""]
    lines += [f"- {_MARK[r['status']]} {r['gate']}" + (f" — {r['detail']}" if r["detail"] else "") for r in rows]
    lines += ["", "**PASSED**" if ok else "**FAILED**"]
    return "\n".join(lines), ok


def proof_commands(repo: str, n: int, token: str) -> tuple[int, list[str]]:
    """(0, commands) when every proof command is allowlisted — the per-repo `proof` job runs them —
    or (1, violations). The allowlist is re-checked here so a PR cannot sneak a command past CI by
    racing the contract job."""
    body = _api(token, f"/repos/{OWNER}/{repo}/pulls/{n}").get("body") or ""
    commands = parse_proof(body)
    bad = [f"{c} ({why})" for c in commands for ok, why in [command_allowed(c, CONFIG["proof_allowlist"])] if not ok]
    return (1, bad) if bad else (0, commands)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="The no-model PR gates as a CI check")
    ap.add_argument("mode", nargs="?", choices=["report", "proof-commands"], default="report",
                    help="report (default): print the Markdown gate report; proof-commands: print the "
                         "PR's proof commands, one per line, after re-checking the allowlist")
    ap.add_argument("--config", required=True, type=Path,
                    help="gates config JSON (see the module docstring for the keys)")
    ap.add_argument("--repo", required=True, help="the PR's repository name — a key of the config's repos")
    ap.add_argument("--pr", type=int, required=True)
    a = ap.parse_args(argv)
    try:
        configure(a.config)
    except (OSError, ValueError) as error:  # ConfigError, a JSON error or an unreadable file: no verdict, exit 2
        print(f"pr_gates: --config {a.config}: {error}", file=sys.stderr)
        return 2
    if a.repo not in CONFIG.get("repos", {}):
        raise SystemExit(f"--repo {a.repo!r} is not a key of the config's repos: "
                         f"{sorted(CONFIG.get('repos', {}))}")
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN is not set — the gates read the PR, its linked issue and the "
                         "head's checks through the GitHub REST API")
    if a.mode == "proof-commands":
        rc, out = proof_commands(a.repo, a.pr, token)
        print("\n".join(out), file=sys.stderr if rc else sys.stdout)
        return rc
    text, ok = gate_report(a.repo, a.pr, token)
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
