#!/usr/bin/env python3
"""Kit release bump (KIT-019). Usage: bump_version.py X.Y.Z [--date YYYY-MM-DD] | --notes X.Y.Z

Bump: refuses unless X.Y.Z is SemVer and greater than VERSION, the working tree is clean and
`## [Unreleased]` in CHANGELOG.md has at least one `- ` entry. Then it writes VERSION, replaces
`"version": "<current>"` in every tracked *plugin.json and *marketplace.json, and inserts
`## [X.Y.Z] - <date>` (today by default) under `## [Unreleased]`. Tagging and publishing stay manual.

--notes X.Y.Z prints that version's CHANGELOG.md section, extracted as .github/workflows/release.yml
does, for `gh release create --notes-file`.
"""
import argparse
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
UNRELEASED = "## [Unreleased]"
MANIFESTS = ("*plugin.json", "*marketplace.json")


def refuse(msg):
    print(f"bump: {msg}", file=sys.stderr)
    sys.exit(1)


def git(*args):
    return subprocess.run(["git", "-C", str(KIT), *args], capture_output=True, text=True,
                          check=True).stdout


def semver(value):
    match = SEMVER_RE.match(value)
    return tuple(int(part) for part in match.groups()) if match else None


def notes(text, version):
    """The awk of release.yml: from the line starting `## [X.Y.Z]` to the next `## [` heading."""
    head, out, on = f"## [{version}]", [], False
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for line in lines:
        if line.startswith(head):
            on = True
        elif on and line.startswith("## ["):
            break
        if on:
            out.append(line + "\n")
    return "".join(out)


def release_changelog(text, new, day):
    lines = text.split("\n")
    if UNRELEASED not in lines:
        refuse(f"CHANGELOG.md has no '{UNRELEASED}' heading")
    start = lines.index(UNRELEASED) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## [")), len(lines))
    body = lines[start:end]
    if not any(line.startswith("- ") for line in body):
        refuse(f"'{UNRELEASED}' in CHANGELOG.md has no entry")
    while body and not body[0].strip():
        body.pop(0)
    return "\n".join(lines[:start] + ["", f"## [{new}] - {day}", ""] + body + lines[end:])


def bump(new, day):
    current = (KIT / "VERSION").read_text(encoding="utf-8").strip()
    if semver(new) is None:
        refuse(f"'{new}' is not SemVer X.Y.Z")
    if semver(current) is None or semver(new) <= semver(current):
        refuse(f"'{new}' is not greater than VERSION '{current}'")
    if git("status", "--porcelain"):
        refuse("the working tree is not clean")
    changelog_path = KIT / "CHANGELOG.md"
    changelog = release_changelog(changelog_path.read_text(encoding="utf-8"), new, day)

    old_field, new_field = f'"version": "{current}"', f'"version": "{new}"'
    fields, files = 0, 0
    for rel in git("ls-files", "-z", "--", *MANIFESTS).split("\0"):
        if not rel:
            continue
        path = KIT / rel
        text = path.read_text(encoding="utf-8")
        count = text.count(old_field)
        if count:
            path.write_text(text.replace(old_field, new_field), encoding="utf-8")
            fields, files = fields + count, files + 1
    (KIT / "VERSION").write_text(new + "\n", encoding="utf-8")
    changelog_path.write_text(changelog, encoding="utf-8")
    print(f"bump: VERSION {current} -> {new}")
    print(f"bump: {fields} version fields in {files} manifests")
    print(f"bump: CHANGELOG.md ## [{new}] - {day}")


def iso_date(value):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        raise argparse.ArgumentTypeError(f"'{value}' is not YYYY-MM-DD")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"'{value}' is not a date") from exc
    return value


def main():
    parser = argparse.ArgumentParser(description="Bump every kit version field for a release.")
    parser.add_argument("version", nargs="?", help="new version X.Y.Z")
    parser.add_argument("--date", type=iso_date, default=date.today().isoformat(),
                        help="CHANGELOG release date (default: today)")
    parser.add_argument("--notes", metavar="X.Y.Z", help="print that version's CHANGELOG section")
    args = parser.parse_args()
    if bool(args.version) == bool(args.notes):
        parser.error("pass either X.Y.Z or --notes X.Y.Z")
    if args.notes:
        section = notes((KIT / "CHANGELOG.md").read_text(encoding="utf-8"), args.notes)
        if not section:
            refuse(f"section ## [{args.notes}] not found in CHANGELOG.md")
        sys.stdout.write(section)
        return
    bump(args.version, args.date)


if __name__ == "__main__":
    main()
