#!/usr/bin/env python3
"""changelog.d fragments: move them into CHANGELOG.md → ## [Unreleased], or only validate them (KIT-084).

  changelog_fragments.py --repo-dir DIR           move every fragment's bullets into CHANGELOG.md, delete the fragments
  changelog_fragments.py --repo-dir DIR --check   validate the fragments and CHANGELOG.md; write nothing

A fragment is `changelog.d/<id>.<type>.md`, <type> one of added, changed, deprecated, removed, fixed, security
(`changelog.d/README.md` is not one). Its body is bullets: a `- ` line opens one, an indented non-blank line continues
the open one, a blank line is skipped; any other line is malformed. A consolidation appends each fragment's bullets, in
file-name order, to the `### <Type>` section of `## [Unreleased]` (created when missing, in the order above) and deletes
the fragment.

Every problem is named in one failure before anything is written: each malformed line of each fragment, each `*.md` in
`changelog.d/` whose name is no fragment name (it would be deleted with its bullets lost), and a CHANGELOG.md that is
missing or has no `## [Unreleased]` line while fragments wait. Exit 1 with `<n> malformed fragment line(s), nothing
written:` and one `changelog.d/<file>:<line>: <why>` per problem on stderr, or the CHANGELOG.md line. On success it
prints `{"fragments": [...], "entries": <n>}` as JSON; `--check` prints what a consolidation would move. Exit 2 on a
usage error.

Stdlib only. A session runs it from the installed kit (`just changelog` in a project whose justfile imports the kit's
docs module), a project's CI from `$AI_KIT_DIR` after the spec-tools action (the `changelog-consolidate.yml` template).
Upstreamed from a consumer project's consolidator; `parse_fragment` keeps that tool's rules and messages.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KINDS = ["added", "changed", "deprecated", "removed", "fixed", "security"]
FRAGMENT_NAME_RE = re.compile(r"^.+\.(" + "|".join(KINDS) + r")\.md$")
UNRELEASED = "## [Unreleased]\n"
UNRELEASED_LINE = re.compile(r"(?m)^## \[Unreleased\]\n")


def parse_fragment(text: str) -> tuple[list[str], list[str]]:
    """The bullets of a `changelog.d` fragment, each with its wrapped lines, and its problems as `<line>: <why>`: a `- `
    line opens a bullet, an indented non-blank line continues the open one, a blank line is skipped, any other line is a
    problem."""
    bullets: list[str] = []
    problems: list[str] = []
    for n, ln in enumerate(text.splitlines(), 1):
        if ln.startswith("- "):
            bullets.append(ln)
        elif not ln.strip():
            continue
        elif ln[0] in " \t" and bullets:
            bullets[-1] += "\n" + ln
        else:
            problems.append(f"{n}: neither a `- ` bullet nor an indented line that wraps one: {ln!r}")
    if not bullets and not problems:
        problems.append("1: no `- ` bullet")
    return bullets, problems


def read_fragments(repo_dir: Path) -> tuple[list[Path], dict[str, list[str]]]:
    """The fragment files and their bullets by type. Raises SystemExit naming every problem of every fragment."""
    frag_dir = repo_dir / "changelog.d"
    groups: dict[str, list[str]] = {k: [] for k in KINDS}
    files = sorted(p for p in frag_dir.glob("*.md") if p.name != "README.md") if frag_dir.is_dir() else []
    problems: list[str] = []
    for p in files:
        m = FRAGMENT_NAME_RE.match(p.name)
        if not m:
            problems.append(f"changelog.d/{p.name}:1: not a fragment name: <id>.<type>.md, <type> one of "
                            + ", ".join(KINDS))
            continue
        try:
            bullets, bad = parse_fragment(p.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            bullets, bad = [], ["1: not UTF-8"]
        groups[m.group(1)] += bullets
        problems += [f"changelog.d/{p.name}:{b}" for b in bad]
    if problems:
        raise SystemExit(f"{len(problems)} malformed fragment line(s), nothing written:\n" + "\n".join(problems))
    return files, groups


def read_changelog(repo_dir: Path) -> tuple[str, int]:
    """CHANGELOG.md's text and where its `## [Unreleased]` line starts. Raises SystemExit when either is missing: a
    heading without its newline at the end of the file took the bullets nowhere while the fragments were deleted."""
    changelog = repo_dir / "CHANGELOG.md"
    if not changelog.is_file():
        raise SystemExit("CHANGELOG.md is missing, nothing written")
    text = changelog.read_text(encoding="utf-8")
    found = UNRELEASED_LINE.search(text)
    if not found:
        raise SystemExit("CHANGELOG.md has no `## [Unreleased]` line, nothing written")
    return text, found.start()


def summary(files: list[Path], groups: dict[str, list[str]]) -> dict:
    return {"fragments": [p.name for p in files], "entries": sum(len(v) for v in groups.values())}


def check(repo_dir: Path) -> dict:
    """What `consolidate_changelog` would move, writing nothing. Raises SystemExit on the problems it would refuse."""
    files, groups = read_fragments(repo_dir)
    if files:
        read_changelog(repo_dir)
    return summary(files, groups)


def consolidate_changelog(repo_dir: Path) -> dict:
    """Moves every `changelog.d` fragment's bullets into `CHANGELOG.md` → `## [Unreleased]` and deletes the fragments.
    Every problem (`read_fragments`, `read_changelog`) is named in one SystemExit before anything is written. Returns
    `{"fragments": [<file name>, ...], "entries": <bullet count>}`."""
    files, groups = read_fragments(repo_dir)
    if not files:
        return summary(files, groups)
    text, start = read_changelog(repo_dir)
    nxt = text.find("\n## [", start + 1)
    block = text[start: nxt if nxt != -1 else len(text)]
    for kind in reversed(KINDS):
        if not groups[kind]:
            continue
        head = f"### {kind.capitalize()}\n"
        entries = "\n".join(groups[kind]) + "\n"
        block = block.replace(head, head + entries, 1) if head in block else \
            block.replace(UNRELEASED, f"{UNRELEASED}\n{head}{entries}", 1)
    (repo_dir / "CHANGELOG.md").write_text(text[:start] + block + (text[nxt:] if nxt != -1 else ""), encoding="utf-8")
    for p in files:
        p.unlink()
    return summary(files, groups)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="move changelog.d fragments into CHANGELOG.md → ## [Unreleased]")
    ap.add_argument("--repo-dir", required=True, help="the checkout holding changelog.d/ and CHANGELOG.md")
    ap.add_argument("--check", action="store_true", help="validate the fragments and CHANGELOG.md; write nothing")
    args = ap.parse_args(argv)
    run = check if args.check else consolidate_changelog
    print(json.dumps(run(Path(args.repo_dir)), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
