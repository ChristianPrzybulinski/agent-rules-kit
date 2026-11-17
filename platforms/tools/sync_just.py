#!/usr/bin/env python3
"""Removes the justfile lines and files older syncs generated for the kit's just modules (KIT-085; KIT-081 stage 1b;
KIT-074). Called by sync-project.sh.

Usage: sync_just.py write|check <repo> <profile-list>

<profile-list> is sync-project.sh's normalized list (docs,godot:client,java:server). A project keeps no justfile for
the kit's recipes (KIT-085): skill sdd-implement finds a folder's stack in the project profile and runs the installed
kit's module itself, `just -f ~/.ai-kit/platforms/kits/just/<stack>.just -d <folder> <recipe>`, and CI runs the same
form from $AI_KIT_DIR. So the sync writes no justfile and requires no import line. What it removes is only what an
older sync wrote, and only as a regular file reached without a symbolic link:
- a starter justfile, recognized by its whole text: the comment lines a sync wrote (KIT-074 to KIT-080, or KIT-081
  stage 1b) and one kit import line, `import 'kit.just'` (while that kit.just is the kit's copy or gone) or
  `import '~/.ai-kit/platforms/kits/just/<profile>.just'`. Any other line, a project's comment included, keeps the
  file, with a `sync: kept` line when it imports a kit module;
- every kit.just and kit-<profile>.just whose first line carries the generated marker (KIT-074 until stage 1b); an
  unmarked one in a profile folder stays, with a `sync: kept` line;
- in a justfile the project keeps, a line importing kit.just while that file is the kit's copy or gone: in a folder
  with one profile it becomes the import of that profile's kit module (so the project's recipes that depend on the
  kit's still run), or goes when that import is already there; in another folder it is a warning to remove by hand.
check prints one "sync: ..." line per leftover (a starter, a marked copy, a stale kit.just import) and exits 1. The
walk skips SKIP_DIRS, nested checkouts and symbolic links, as sync_agents_md.py does.
"""
import os
import re
import sys
from pathlib import Path

KIT_HOME = "~/.ai-kit"  # the installed kit; the import lines older syncs wrote named this path
MARKER = "# agent-rules-kit: generated "  # the first line of a module an older sync generated
SKIP_DIRS = {".git", ".claude", ".godot", "node_modules", "target", "build", "dist", ".venv", "venv", "__pycache__"}
# A parameter may be variadic (+, *), exported ($) or have a default (x="a", #283); `x := 1` is no recipe. An
# unquoted default holds no quote, so each parameter has one parse and a line cannot backtrack exponentially.
RECIPE = re.compile(r"^@?([A-Za-z_][A-Za-z0-9_-]*)(?:[ \t]+[+*$]?[A-Za-z_][A-Za-z0-9_-]*(?:=(?:\"[^\"]*\"|'[^']*'|[^\s:\"']+))?)*[ \t]*:(?![=:])")
KIT_IMPORT = re.compile(r"^\s*import\??\s+(['\"])~/\.ai-kit/platforms/kits/just/([A-Za-z0-9_-]+)\.just\1\s*(#.*)?$")
OLD_IMPORT = re.compile(r"^\s*import\??\s+(['\"])kit\.just\1\s*(#.*)?$")
PATH_TOKEN = re.compile(r"(['\"])kit\.just\1")
# The comment lines of the starter justfile each generation of the sync wrote, before its one import line.
STARTER_V1 = ("# This folder's recipes for just (https://just.systems). The kit's recipes come from kit.just, which",
              "# agent-rules-kit's platforms/tools/sync-project.sh writes; add this folder's own recipes below the import.")


def starter_v2(profile):
    """KIT-081 stage 1b's starter comment lines (kit 14.0.0 to 15.x)."""
    return (f"# This folder's recipes for just (https://just.systems). The import runs the {profile} recipes of the",
            "# installed agent-rules-kit (~/.ai-kit; in CI the kit's spec-tools action links it), with no copy in the",
            "# project. Add this folder's own recipes below it.")


def recipes(text):
    """The recipe names a just module defines (one recipe header per line at column 0)."""
    return [m.group(1) for m in map(RECIPE.match, text.splitlines()) if m]


def plan(profiles):
    """{folder: [profile, ...]} from the normalized profile list; '.' is the repository root."""
    folders = {}
    for entry in filter(None, profiles.split(",")):
        name, _, folder = entry.partition(":")
        folders.setdefault(folder or ".", [])
        if name not in folders[folder or "."]:
            folders[folder or "."].append(name)
    return {folder: sorted(names) for folder, names in folders.items()}


def rel(folder, name):
    return name if folder == "." else f"{folder}/{name}"


def import_line(profile):
    return f"import '{KIT_HOME}/platforms/kits/just/{profile}.just'"


def run_line(profile, folder):
    """The command skill sdd-implement runs in place of a justfile import (KIT-085)."""
    return f"just -f {KIT_HOME}/platforms/kits/just/{profile}.just -d {folder} <recipe>"


def marked(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.readline().startswith(MARKER)
    except OSError:
        return False


def regular(path):
    return path.is_file() and not path.is_symlink()


def old_module_is_the_kits(directory):
    """True when the folder's kit.just is the generated copy or gone: an import of it then names the kit's file."""
    path = directory / "kit.just"
    return not os.path.lexists(path) or (regular(path) and marked(path))


def is_starter(directory, text):
    """True when the text is a starter justfile a sync wrote: its comment lines and one kit import line, nothing
    else (line endings and trailing blanks aside)."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    if len(lines) < 2:
        return False
    head, last = tuple(lines[:-1]), lines[-1]
    if last == "import 'kit.just'":
        return head == STARTER_V1 and old_module_is_the_kits(directory)
    found = KIT_IMPORT.match(last)
    if not found or last != import_line(found.group(2)):
        return False
    return head in (STARTER_V1, starter_v2(found.group(2)))


def walk(repo):
    """(marked kit.just and kit-*.just copies, justfiles) the walk reaches as regular files, relative to repo, never
    through a symbolic link."""
    copies, found = [], []
    for base, dirnames, filenames in os.walk(repo):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in SKIP_DIRS and not os.path.lexists(os.path.join(base, d, ".git")))
        for name in sorted(filenames):
            path = Path(base) / name
            if not regular(path):
                continue
            relative = Path(os.path.relpath(path, repo)).as_posix()
            if (name == "kit.just" or (name.startswith("kit-") and name.endswith(".just"))) and marked(path):
                copies.append(relative)
            elif name.lower() in ("justfile", ".justfile"):
                found.append(relative)
    return copies, found


def stale_imports(directory, text):
    """Line numbers of the lines importing kit.just while that file is the kit's copy or gone."""
    if not old_module_is_the_kits(directory):
        return []
    return [n for n, line in enumerate(text.splitlines(), 1) if OLD_IMPORT.match(line)]


def imports_profile(text, profile):
    return any((m := KIT_IMPORT.match(line)) and m.group(2) == profile for line in text.splitlines())


def migrate(directory, text, profile):
    """(new text, [(line number, what changed)]): the first line importing kit.just (the kit's copy) becomes the
    import of this profile's kit module unless one exists; any further kit.just import line goes, since kit.just is
    removed. No other line changes."""
    have = imports_profile(text, profile)
    stale = set(stale_imports(directory, text))
    lines, changes = [], []
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        if number in stale and have:
            changes.append((number, "dropped import 'kit.just'; the kit's module is imported"))
            continue
        if number in stale:
            line = PATH_TOKEN.sub(f"'{KIT_HOME}/platforms/kits/just/{profile}.just'", line, count=1)
            changes.append((number, f"imports the kit's {profile} module (was kit.just)"))
            have = True
        lines.append(line)
    return "".join(lines), changes


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("write", "check"):
        sys.exit("usage: sync_just.py write|check <repo> <profile-list>")
    mode, repo, profiles = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    folders = plan(profiles)
    copies, found = walk(repo)
    starters, kept, failed, by_hand, edits = [], [], [], [], []
    for name in found:
        path = repo / name
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == "justfile" and is_starter(path.parent, text):
            starters.append(name)
            continue
        names = folders.get(Path(name).parent.as_posix(), [])
        new = text
        for number in stale_imports(path.parent, text):
            fix = (f"replace the line with {import_line(names[0])} (sync-project.sh does)" if len(names) == 1
                   else "remove the line, or import a kit module")
            line = (f"sync: {name}:{number} imports kit.just, which the kit no longer generates (KIT-081 stage 1b);"
                    f" {fix}")
            failed.append(line)
            if len(names) != 1:
                by_hand.append(line)
        if len(names) == 1:
            new, changes = migrate(path.parent, text, names[0])
            if changes:
                edits.append((name, new, changes))
        if any(KIT_IMPORT.match(line) for line in new.splitlines()):
            kept.append(name)
    if mode == "check":
        failed += [f"sync: {name} is a copy the kit no longer generates (KIT-081 stage 1b); sync-project.sh removes it"
                   for name in copies]
        failed += [f"sync: {name} is the starter justfile an older sync wrote, only the kit import; a project keeps"
                   " no justfile for the kit's recipes (KIT-085: skill sdd-implement runs the module); sync-project.sh"
                   " removes it" for name in starters]
        for line in failed:
            print(line)
        sys.exit(1 if failed else 0)
    for name, new, changes in edits:
        (repo / name).write_text(new, encoding="utf-8")
        for number, what in changes:
            print(f"sync: {name}:{number} {what}")
    for line in by_hand:
        print(line.replace("sync: ", "sync: warning: ", 1), file=sys.stderr)
    for name in starters:
        (repo / name).unlink()
        print(f"sync: removed {name} (the starter an older sync wrote; skill sdd-implement runs the kit's just module,"
              " KIT-085)")
    for name in copies:
        (repo / name).unlink()
        print(f"sync: removed {name} (a kit module copy; skill sdd-implement runs the installed kit's module,"
              " KIT-081 stage 1b, KIT-085)")
    for name in kept:
        print(f"sync: kept {name} (the project's own; it imports a kit module, which still runs while ~/.ai-kit"
              " exists, and no kit step needs it, KIT-085)")
    for folder in folders:
        directory = repo / folder
        if not directory.is_dir() or directory.is_symlink():
            continue
        for path in sorted(directory.iterdir()):
            if (path.name == "kit.just" or (path.name.startswith("kit-") and path.name.endswith(".just"))) \
                    and os.path.lexists(path) and rel(folder, path.name) not in copies:
                print(f"sync: kept {rel(folder, path.name)} (not generated by the kit; the project's own)")
    shown = ", ".join(run_line(n[0], f) for f, n in sorted(folders.items()) if len(n) == 1) or "none"
    print(f"sync: just: no project justfile; skill sdd-implement runs the kit's modules ({shown});"
          f" {len(starters)} starters and {len(copies)} copies removed")


if __name__ == "__main__":
    main()
