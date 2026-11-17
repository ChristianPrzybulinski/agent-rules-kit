#!/usr/bin/env python3
"""Every authored folder says what belongs in it (KIT-074; opt-in through `sdd.doc_structure` in .ai-kit.yaml).

From `git ls-files` (the index, so a sparse checkout is checked whole), fail when

1. an authored folder (any folder holding tracked files, except the repository root, the folders the kit generates
   and the globs of the exempt file) has no `README.md`, or its README does not start with a `# ` title or lacks one
   of the configured headings (a heading line may carry more words after it);
2. with `done_index` on, a `done/` folder has no `INDEX.md`, or its INDEX does not name every direct child (file or
   folder) other than `README.md` and `INDEX.md`.

Always exempt: `.github` itself (GitHub shows a `.github/README.md` on the repository page in place of the root
README; its subfolders are still checked) and the Claude Code folders (`.claude` itself, which holds the settings
platforms/tools/sync-project.sh generates, and `.claude/rules` and `.claude/skills`, where older syncs wrote copies and a
project keeps its own, with their interiors). `.github/spec-lint` and
`.github/merge-drivers` are no longer among them (KIT-081 stages 1 and 1b: the sync removes the copies it once wrote
there), so a project that keeps files in one says what belongs there. The exempt file holds one fnmatch glob per line against the folder path from the repository
root (`*` also matches `/`; a glob ending in `/**` exempts the folders below a folder, not the folder itself); `#`
starts a comment line. A missing exempt file exempts nothing.

Parameters (`sdd.doc_structure` of the project profile, which check_spec.py --params resolves, defaults included; the
check runs only where docs/spec/spec.md exists): `enabled` (false: the check prints
"off" and exits 0), `exempt` (the exempt file, from the repository root), `headings`, `done_index`.

Usage:  check_docs_structure.py [--root DIR] [--list]
Reports every problem as a `FAIL:` line; exit 1 on any failure, 2 on a refused profile, 0 otherwise. --list prints
the authored folders it requires. Stdlib only. A project runs it from the kit (KIT-081 stage 1): the installed kit's
platforms/ci/validations/, or the spec-tools action in CI; it reads check_spec.py beside it and the kit's schemas.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import posixpath
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_HEADINGS = ("## What goes here", "## What does not go here")
GENERATED = (".claude", ".claude/rules", ".claude/rules/**", ".claude/skills", ".claude/skills/**", ".github")


def load_exempt(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def tracked(root: Path) -> list[str]:
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True).stdout
    return [path for path in out.decode("utf-8", "surrogateescape").split("\0") if path]


def read_index(root: Path, path: str) -> str:
    """The staged content of a tracked file (works in a sparse worktree where the file is not on disk)."""
    result = subprocess.run(["git", "-C", str(root), "show", f":{path}"], capture_output=True)
    return result.stdout.decode("utf-8", "replace") if result.returncode == 0 else ""


def folders(files: list[str]) -> set[str]:
    out: set[str] = set()
    for path in files:
        folder = posixpath.dirname(path)
        while folder:
            out.add(folder)
            folder = posixpath.dirname(folder)
    return out


def required(files: list[str], exempt: list[str]) -> list[str]:
    globs = list(GENERATED) + list(exempt)
    return sorted(d for d in folders(files) if not any(fnmatch.fnmatchcase(d, g) for g in globs))


def readme_problems(text: str, headings: tuple[str, ...] | list[str] = DEFAULT_HEADINGS) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines()]
    first = next((line for line in lines if line.strip()), "")
    out = []
    if not first.startswith("# "):
        out.append("does not start with a `# ` title")
    for heading in headings:
        if not any(line == heading or line.startswith(heading + " ") for line in lines):
            out.append(f"lacks the heading `{heading}`")
    return out


def check(root: Path, exempt: list[str], headings: tuple[str, ...] | list[str] = DEFAULT_HEADINGS,
          done_index: bool = True) -> tuple[list[str], list[str]]:
    files = tracked(root)
    fileset = set(files)
    req = required(files, exempt)
    fails: list[str] = []
    for folder in req:
        readme = f"{folder}/README.md"
        if readme not in fileset:
            fails.append(f"FAIL: {folder}/ has no README.md")
            continue
        for problem in readme_problems(read_index(root, readme), headings):
            fails.append(f"FAIL: {readme} {problem}")
        if done_index and posixpath.basename(folder) == "done":
            index = f"{folder}/INDEX.md"
            if index not in fileset:
                fails.append(f"FAIL: {folder}/ has no INDEX.md")
                continue
            text = read_index(root, index)
            children = sorted({f[len(folder) + 1:].split("/")[0] for f in files if f.startswith(folder + "/")}
                              - {"README.md", "INDEX.md"})
            for child in children:
                if child not in text:
                    fails.append(f"FAIL: {index} does not list `{child}`")
    return req, fails


def params(spec_dir: Path) -> dict:
    """The resolved `sdd.doc_structure` of the project profile, through check_spec.py --params beside this file.
    Raises ValueError with check_spec.py's report when the profile is refused."""
    schemas = HERE / "schemas" if (HERE / "schemas").is_dir() else HERE.parent / "schemas"
    result = subprocess.run([sys.executable, "-B", str(HERE / "check_spec.py"), "--params", str(spec_dir),
                             str(schemas)], capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError((result.stdout + result.stderr).strip())
    return json.loads(result.stdout)["doc_structure"]


def toplevel(start: Path) -> Path:
    result = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return Path(result.stdout.strip()) if result.returncode == 0 else start


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="README and done/INDEX.md check (KIT-074); see the module text")
    parser.add_argument("--root", type=Path, help="the repository (default: the one holding the current folder)")
    parser.add_argument("--list", action="store_true", help="print the authored folders the check requires")
    args = parser.parse_args(argv)  # exits 2 on a usage error
    root = args.root or toplevel(Path.cwd())
    spec_dir = root / "docs" / "spec"
    try:
        given = params(spec_dir) if (spec_dir / "spec.md").is_file() else {"enabled": False}
    except ValueError as err:
        print(f"doc-structure: .ai-kit.yaml sdd.doc_structure is invalid:\n{err}")
        return 2
    if given.get("enabled") is not True:
        print("doc-structure: off (.ai-kit.yaml sdd.doc_structure.enabled is not true)")
        return 0
    exempt_path = root / given["exempt"]
    req, fails = check(root, load_exempt(exempt_path), given["headings"], given["done_index"])
    if args.list:
        print("\n".join(req))
    for line in fails:
        print(line)
    if not exempt_path.is_file():
        print(f"doc-structure: no exempt file at {given['exempt']}")
    print(f"doc-structure: {len(req)} authored folders, {len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
