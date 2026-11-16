#!/usr/bin/env python3
"""Writes or checks the generated just modules of a project (KIT-074). Called by sync-project.sh.

Usage: sync_just.py preflight|write|check|list <repo> <kit-version> <profile-list>

<profile-list> is sync-project.sh's normalized list (docs,godot:client,java:server). Each profile folder gets
`kit.just`, generated from platforms/kits/just/<profile>.just and marked on its first line. A folder with several
profiles gets one module per profile (`kit-<profile>.just`, reached as `just kit-<profile> <recipe>`) and a `kit.just`
that loads them and runs fmt, lint, test and verify of every profile that has the recipe. The folder's own justfile
imports kit.just and keeps the project's recipes: a folder with no justfile gets a starter one with the import line,
never overwritten; a justfile without the import is a warning here and a failure in check. A folder that does not
exist gets no module, and nothing here creates one.

preflight refuses, before the sync's first write, a module path that holds a file without the marker or a symbolic
link, and a profile folder reached through a symbolic link. write writes the modules that differ, creates the starter
justfiles and removes marked modules no profile needs any more. check prints one "sync: ..." line per difference and
exits 1. list prints the path of each module the profiles want, one per line, for the KIT-072 pin (sync-project.sh
pin_sources). The walk for stale modules skips SKIP_DIRS and nested checkouts, as sync_agents_md.py does.
"""
import os
import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
MODULES = KIT / "platforms" / "kits" / "just"
MARKER = "# agent-rules-kit: generated "
SHARED = ("fmt", "lint", "test", "verify")
SKIP_DIRS = {".git", ".claude", ".godot", "node_modules", "target", "build", "dist", ".venv", "venv", "__pycache__"}
RECIPE = re.compile(r"^@?([A-Za-z_][A-Za-z0-9_-]*)(?:[ \t][^:=]*)?:(?![=:])")
IMPORT = re.compile(r"^\s*import\??\s+(['\"])kit\.just\1\s*(#.*)?$", re.M)
STARTER = """# This folder's recipes for just (https://just.systems). The kit's recipes come from kit.just, which
# agent-rules-kit's platforms/tools/sync-project.sh writes; add this folder's own recipes below the import.
import 'kit.just'
"""


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


def header(source, version):
    return f"{MARKER}from {source} by platforms/tools/sync-project.sh; kit {version}; do not edit\n"


def module(profile, version):
    return header(f"platforms/kits/just/{profile}.just", version) + (MODULES / f"{profile}.just").read_text(
        encoding="utf-8")


def aggregate(profiles, version):
    lines = [f"{MARKER}for profiles {', '.join(profiles)} by platforms/tools/sync-project.sh; kit {version};"
             " do not edit",
             "# One module per profile (just kit-<profile> <recipe>); a shared recipe name runs every profile that"
             " has it.", ""]
    lines += [f"mod kit-{p} 'kit-{p}.just'" for p in profiles]
    for name in SHARED:
        owners = [p for p in profiles if name in recipes((MODULES / f"{p}.just").read_text(encoding="utf-8"))]
        if owners:
            lines += ["", f"# {name} of {', '.join(owners)}", f"{name}: " + " ".join(f"kit-{p}::{name}" for p in owners)]
    return "\n".join(lines) + "\n"


def expected(folders, version):
    """{relative path: content} of every generated module."""
    files = {}
    for folder, profiles in folders.items():
        if len(profiles) == 1:
            files[rel(folder, "kit.just")] = module(profiles[0], version)
            continue
        files[rel(folder, "kit.just")] = aggregate(profiles, version)
        for profile in profiles:
            files[rel(folder, f"kit-{profile}.just")] = module(profile, version)
    return files


def generated(repo):
    """Relative paths of every marked kit.just or kit-*.just the walk reaches."""
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


def marked(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.readline().startswith(MARKER)
    except OSError:
        return False


def justfiles(directory):
    return sorted(p for p in directory.iterdir() if p.name.lower() in ("justfile", ".justfile") and p.is_file())


def main():
    if len(sys.argv) != 5 or sys.argv[1] not in ("preflight", "write", "check", "list"):
        sys.exit("usage: sync_just.py preflight|write|check|list <repo> <kit-version> <profile-list>")
    mode, repo, version, profiles = sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4]
    real_repo = repo.resolve()
    folders = {}
    problems = []
    for folder, names in plan(profiles).items():
        path = repo / folder
        if path.is_symlink() or (path.is_dir() and path.resolve() != real_repo / folder):
            problems.append(f"sync: {folder} goes through a symbolic link; the sync writes no kit.just there")
        elif not path.is_dir():
            if mode in ("preflight", "check"):
                print(f"sync: warning: {folder}/ does not exist; no kit.just written there", file=sys.stderr)
        else:
            folders[folder] = names
    files = expected(folders, version)
    if mode == "list":
        print("\n".join(sorted(files)))
        return
    for name in files:
        path = repo / name
        if path.is_symlink():
            problems.append(f"sync: {name} is a symbolic link; the sync writes no kit.just through it")
        elif path.exists() and not marked(path):
            problems.append(f"sync: {name} exists and is not generated; rename it or drop the profile that receives"
                            " it (sync-project.sh --profile)")
    stale = [name for name in generated(repo) if name not in files]
    imports = {}
    for folder in folders:
        found = justfiles(repo / folder)
        imports[folder] = (found, any(IMPORT.search(p.read_text(encoding="utf-8", errors="replace")) for p in found))
    if mode == "preflight":
        for line in problems:
            print(line)
        for folder, (found, ok) in imports.items():
            if found and not ok:
                print(f"sync: warning: {rel(folder, found[0].name)} does not import kit.just; add the line"
                      " import 'kit.just'", file=sys.stderr)
        sys.exit(1 if problems else 0)
    if mode == "check":
        failed = list(problems)
        for name, text in files.items():
            path = repo / name
            if not path.is_file():
                failed.append(f"sync: {name} missing")
            elif path.read_text(encoding="utf-8", errors="replace") != text:
                failed.append(f"sync: {name} diverges from the kit")
        failed += [f"sync: {name} is generated but not in profile" for name in stale]
        for folder, (found, ok) in imports.items():
            if not found:
                failed.append(f"sync: {rel(folder, 'justfile')} missing; it imports kit.just")
            elif not ok:
                failed.append(f"sync: {rel(folder, found[0].name)} does not import kit.just")
        for line in failed:
            print(line)
        sys.exit(1 if failed else 0)
    if problems:  # write after a skipped preflight: never write through what preflight refuses
        for line in problems:
            print(line)
        sys.exit(1)
    written = 0
    for name, text in files.items():
        path = repo / name
        if not path.is_file() or path.read_text(encoding="utf-8", errors="replace") != text:
            path.write_text(text, encoding="utf-8")
            written += 1
    for name in stale:
        (repo / name).unlink()
        print(f"sync: removed {name} (not in profile)")
    for folder, (found, _) in imports.items():
        if not found:
            (repo / rel(folder, "justfile")).write_text(STARTER, encoding="utf-8")
            print(f"sync: created {rel(folder, 'justfile')} (imports kit.just; the project's own from now on)")
    print(f"sync: just modules: {written} written, {len(stale)} removed ({', '.join(sorted(files)) or 'none'})")


if __name__ == "__main__":
    main()
