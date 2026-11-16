#!/usr/bin/env python3
"""Points each profile folder's justfile at the installed kit's just module (KIT-074, KIT-081 stage 1b). Called by
sync-project.sh.

Usage: sync_just.py preflight|write|check <repo> <profile-list>

<profile-list> is sync-project.sh's normalized list (docs,godot:client,java:server). The project carries no copy of
the kit's modules: the justfile of each profile folder holds `import '~/.ai-kit/platforms/kits/just/<profile>.just'`.
just replaces a leading ~/ in an import path with the home folder and runs an imported recipe in the importing
justfile's folder; an import path is a string, never an expression. In CI the kit's spec-tools action links ~/.ai-kit
to the kit at the commit it pins. That line is the only thing the sync writes: a folder with no justfile gets a starter
one holding it, never overwritten; a line that imports kit.just, the module older syncs generated, is rewritten in
place (so is the first one importing another profile's kit module, after a profile switch); a justfile with no kit
import is a warning here and a failure in check. A folder with several profiles gets no import and a warning: just
runs a `mod` module's recipes in the module file's own folder, which is the kit's, and two imports define the same
recipe names. A folder that does not exist gets nothing, and nothing here creates one.

Migration from the copies (KIT-074 until KIT-081 stage 1b): write removes every kit.just and kit-<profile>.just whose
first line carries the generated marker, keeps an unmarked one (a `sync: kept` line in a profile folder) and never
reads or removes a file through a symbolic link; check fails on each marked one left and on a justfile line that
imports kit.just while that file is generated or gone, with file:line and the fix.

preflight refuses, before the sync's first write, a profile folder reached through a symbolic link and a justfile or
.justfile that is a symbolic link (dangling or not) or not a regular file. check prints one "sync: ..." line per
difference and exits 1. The walk for marked modules skips SKIP_DIRS and nested checkouts, as sync_agents_md.py does.
"""
import os
import re
import sys
from pathlib import Path

KIT_HOME = "~/.ai-kit"  # the installed kit; an import path cannot read AI_KIT_DIR, so CI links this path
MARKER = "# agent-rules-kit: generated "  # the first line of a module an older sync generated
SKIP_DIRS = {".git", ".claude", ".godot", "node_modules", "target", "build", "dist", ".venv", "venv", "__pycache__"}
# A parameter may be variadic (+, *), exported ($) or have a default (x="a", #283); `x := 1` is no recipe. An
# unquoted default holds no quote, so each parameter has one parse and a line cannot backtrack exponentially.
RECIPE = re.compile(r"^@?([A-Za-z_][A-Za-z0-9_-]*)(?:[ \t]+[+*$]?[A-Za-z_][A-Za-z0-9_-]*(?:=(?:\"[^\"]*\"|'[^']*'|[^\s:\"']+))?)*[ \t]*:(?![=:])")
KIT_IMPORT = re.compile(r"^\s*import\??\s+(['\"])~/\.ai-kit/platforms/kits/just/([A-Za-z0-9_-]+)\.just\1\s*(#.*)?$")
OLD_IMPORT = re.compile(r"^\s*import\??\s+(['\"])kit\.just\1\s*(#.*)?$")
PATH_TOKEN = re.compile(r"(['\"])(?:kit\.just|~/\.ai-kit/platforms/kits/just/[A-Za-z0-9_-]+\.just)\1")


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


def starter(profile):
    return (f"# This folder's recipes for just (https://just.systems). The import runs the {profile} recipes of the\n"
            "# installed agent-rules-kit (~/.ai-kit; in CI the kit's spec-tools action links it), with no copy in the\n"
            "# project. Add this folder's own recipes below it.\n"
            f"{import_line(profile)}\n")


def marked(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.readline().startswith(MARKER)
    except OSError:
        return False


def module_names(directory):
    return sorted(p for p in directory.iterdir() if p.name == "kit.just" or
                  (p.name.startswith("kit-") and p.name.endswith(".just")))


def generated(repo):
    """Relative paths of every marked kit.just or kit-*.just the walk reaches (never through a symbolic link)."""
    found = []
    for base, dirnames, filenames in os.walk(repo):
        dirnames[:] = sorted(d for d in dirnames
                             if d not in SKIP_DIRS and not os.path.lexists(os.path.join(base, d, ".git")))
        for name in sorted(filenames):
            if name == "kit.just" or (name.startswith("kit-") and name.endswith(".just")):
                path = Path(base) / name
                if path.is_file() and not path.is_symlink() and marked(path):
                    found.append(Path(os.path.relpath(path, repo)).as_posix())
    return found


def justfiles(directory):
    return sorted(p for p in directory.iterdir()
                  if p.name.lower() in ("justfile", ".justfile") and p.is_file() and not p.is_symlink())


def old_module_is_the_kits(directory):
    """True when the folder's kit.just is the generated copy or gone: an import of it then names the kit's file."""
    path = directory / "kit.just"
    return not os.path.lexists(path) or (path.is_file() and not path.is_symlink() and marked(path))


def stale_imports(directory, text):
    """Line numbers of the lines importing kit.just while that file is the kit's copy or gone."""
    if not old_module_is_the_kits(directory):
        return []
    return [n for n, line in enumerate(text.splitlines(), 1) if OLD_IMPORT.match(line)]


def imports_profile(text, profile):
    return any((m := KIT_IMPORT.match(line)) and m.group(2) == profile for line in text.splitlines())


def migrate(directory, text, profile):
    """(new text, [(line number, what changed)]): the first line importing kit.just (the kit's copy) or another
    profile's kit module becomes the import of this profile's module unless one exists; any further kit.just import
    line goes, since kit.just is removed."""
    have = imports_profile(text, profile)
    stale = set(stale_imports(directory, text))
    lines, changes = [], []
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        other = KIT_IMPORT.match(line.rstrip("\r\n"))
        if number in stale and have:
            changes.append((number, "dropped import 'kit.just'; the kit's module is imported"))
            continue
        if (number in stale or (other and other.group(2) != profile)) and not have:
            was = "kit.just" if number in stale else f"the kit's {other.group(2)} module"
            line = PATH_TOKEN.sub(f"'{KIT_HOME}/platforms/kits/just/{profile}.just'", line, count=1)
            changes.append((number, f"imports the kit's {profile} module (was {was})"))
            have = True
        lines.append(line)
    return "".join(lines), changes


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("preflight", "write", "check"):
        sys.exit("usage: sync_just.py preflight|write|check <repo> <profile-list>")
    mode, repo, profiles = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    real_repo = repo.resolve()
    folders = {}
    problems = []
    for folder, names in plan(profiles).items():
        path = repo / folder
        if path.is_symlink() or (path.is_dir() and path.resolve() != real_repo / folder):
            problems.append(f"sync: {folder} goes through a symbolic link; the sync writes no justfile there")
        elif not path.is_dir():
            if mode in ("preflight", "check"):
                print(f"sync: warning: {folder}/ does not exist; no justfile written there", file=sys.stderr)
        else:
            folders[folder] = names
    for folder in folders:  # a justfile is written or edited only as a regular file: never through a link
        for path in sorted((repo / folder).iterdir()):
            if path.name.lower() not in ("justfile", ".justfile"):
                continue
            if path.is_symlink():
                problems.append(f"sync: {rel(folder, path.name)} is a symbolic link; the sync writes no justfile"
                                " through it")
            elif not path.is_file():
                problems.append(f"sync: {rel(folder, path.name)} is not a regular file; the sync writes no starter"
                                " justfile there")
    copies = generated(repo)
    several = {folder: names for folder, names in folders.items() if len(names) > 1}
    for folder, names in several.items():
        if mode in ("write", "check"):
            print(f"sync: warning: {folder}/ has profiles {', '.join(names)}: the sync imports no kit module there"
                  " (just runs a mod module's recipes in the module's own folder, and two imports define the same"
                  f" recipes); import one, such as {import_line(names[0])}, and write the other's recipes, or give"
                  " each profile its own folder", file=sys.stderr)
    if mode == "preflight":
        for line in problems:
            print(line)
        sys.exit(1 if problems else 0)
    if mode == "check":
        failed = list(problems)
        failed += [f"sync: {name} is a copy the kit no longer generates (KIT-081 stage 1b); sync-project.sh removes it"
                   for name in copies]
        for folder, names in folders.items():
            found = justfiles(repo / folder)
            stale = 0
            for path in found:
                for number in stale_imports(repo / folder, path.read_text(encoding="utf-8", errors="replace")):
                    fix = (f"replace the line with {import_line(names[0])} (sync-project.sh does)" if len(names) == 1
                           else "remove the line and import one profile's kit module")
                    failed.append(f"sync: {rel(folder, path.name)}:{number} imports kit.just, which the kit no longer"
                                  f" generates (KIT-081 stage 1b); {fix}")
                    stale += 1
            if len(names) > 1 or stale:
                continue
            if not found:
                failed.append(f"sync: {rel(folder, 'justfile')} missing; it imports the kit's {names[0]} module"
                              f" ({import_line(names[0])})")
            elif not any(imports_profile(p.read_text(encoding="utf-8", errors="replace"), names[0]) for p in found):
                failed.append(f"sync: {rel(folder, found[0].name)} does not import the kit's {names[0]} module; add"
                              f" the line {import_line(names[0])}")
        for line in failed:
            print(line)
        sys.exit(1 if failed else 0)
    if problems:  # write after a skipped preflight: never write through what preflight refuses
        for line in problems:
            print(line)
        sys.exit(1)
    for folder, names in folders.items():
        found = justfiles(repo / folder)
        if len(names) > 1:
            for path in found:
                for number in stale_imports(repo / folder, path.read_text(encoding="utf-8", errors="replace")):
                    print(f"sync: warning: {rel(folder, path.name)}:{number} imports kit.just, which the kit no longer"
                          " generates; remove the line and import one profile's kit module", file=sys.stderr)
            continue
        profile = names[0]
        if not found:
            (repo / rel(folder, "justfile")).write_text(starter(profile), encoding="utf-8")
            print(f"sync: created {rel(folder, 'justfile')} ({import_line(profile)}; the project's own from now on)")
            continue
        for path in found:
            text = path.read_text(encoding="utf-8", errors="replace")
            new, changes = migrate(repo / folder, text, profile)
            if new != text:
                path.write_text(new, encoding="utf-8")
            for number, what in changes:
                print(f"sync: {rel(folder, path.name)}:{number} {what}")
        if not any(imports_profile(p.read_text(encoding="utf-8", errors="replace"), profile) for p in found):
            print(f"sync: warning: {rel(folder, found[0].name)} does not import the kit's {profile} module; add the"
                  f" line {import_line(profile)}", file=sys.stderr)
    for name in copies:
        (repo / name).unlink()
        print(f"sync: removed {name} (the justfile imports the installed kit's module, KIT-081 stage 1b)")
    for folder in folders:
        for path in module_names(repo / folder):
            if os.path.lexists(path) and rel(folder, path.name) not in copies:
                print(f"sync: kept {rel(folder, path.name)} (not generated by the kit; the project's own)")
    print(f"sync: just: the justfiles import the installed kit's modules"
          f" ({', '.join(f'{f} {n[0]}' for f, n in sorted(folders.items()) if len(n) == 1) or 'none'});"
          f" {len(copies)} copies removed")


if __name__ == "__main__":
    main()
