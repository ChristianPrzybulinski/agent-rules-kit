#!/usr/bin/env python3
"""Fail a change that adds a CHANGELOG line under a released version (KIT-109). Usage:
check_changelog.py [--repo DIR] [--base REV] [--file CHANGELOG.md]

A rebase or merge of a release can land a branch's line inside the new `## [X.Y.Z]` section with no conflict, so the
release notes list a change the published version does not ship. The check reads the diff of the file between the base
and HEAD and fails each added line whose section is not `## [Unreleased]`. A section whose heading the diff adds is a
release in progress (`bump_version.py` writes it), so its lines pass. Standard library, Python 3.9.

Only committed edits are checked: the file is read as HEAD has it and diffed from the base to HEAD, so a CHANGELOG edit
still uncommitted (or staged) in the working tree passes silently until it is committed (#405).

The base is --base, else the merge base with origin/main, else the first parent of HEAD (a pull request's merge commit
in CI, or the commit before a push); with none of them the check says so and passes."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

HEADING = re.compile(r"^## \[(?P<name>[^\]]+)\]")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check)


def rev(repo, name):
    out = git(repo, "rev-parse", "--verify", "--quiet", name + "^{commit}", check=False)
    return out.stdout.strip() if out.returncode == 0 else None


def find_base(repo, explicit):
    head = rev(repo, "HEAD")
    if explicit:
        return rev(repo, explicit)
    if rev(repo, "origin/main"):
        mb = git(repo, "merge-base", "HEAD", "origin/main", check=False).stdout.strip()
        if mb and mb != head:
            return mb
    return rev(repo, "HEAD^1")


def added_lines(repo, base, path):
    """[(line number in HEAD, text)] the diff adds to `path`."""
    diff = git(repo, "diff", "-U0", "--no-color", base, "HEAD", "--", path).stdout
    added, line_no = [], 0
    for raw in diff.splitlines():
        hunk = HUNK.match(raw)
        if hunk:
            line_no = int(hunk.group("start"))
        elif raw.startswith("+") and not raw.startswith("+++"):
            added.append((line_no, raw[1:]))
            line_no += 1
    return added


def check(repo, base, path):
    """The findings, one string per added line under a released version."""
    text = git(repo, "show", f"HEAD:{path}", check=False)
    if text.returncode != 0:
        return []
    lines = text.stdout.splitlines()
    added = added_lines(repo, base, path)
    added_headings = {n for n, t in added if HEADING.match(t)}
    section, sections = None, {}
    for number, line in enumerate(lines, start=1):
        match = HEADING.match(line)
        if match:
            section = (match.group("name"), number)
        sections[number] = section
    findings = []
    for number, text_line in added:
        if not text_line.strip():
            continue
        name, heading_line = sections.get(number) or (None, None)
        if name is None or name.lower() == "unreleased" or heading_line in added_headings:
            continue
        findings.append(f"{path}:{number}: added under [{name}], a released version; move it under [Unreleased]")
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--base", help="the revision to diff from (default: see the module docstring)")
    parser.add_argument("--file", default="CHANGELOG.md")
    args = parser.parse_args(argv)
    base = find_base(args.repo, args.base)
    if not base:
        print("check_changelog: skipped (no base revision: a shallow checkout or a first commit)")
        return 0
    findings = check(args.repo, base, args.file)
    for finding in findings:
        print(f"FAIL: {finding}", file=sys.stderr)
    if findings:
        return 1
    print(f"check_changelog: OK ({args.file} adds nothing under a released version)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
