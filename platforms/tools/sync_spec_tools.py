#!/usr/bin/env python3
"""The spec tools of a project (KIT-081 stage 1). Called by sync-project.sh.

Usage: sync_spec_tools.py remove <repo>
       sync_spec_tools.py check <repo> [--spec] [--workflow NAME]
       sync_spec_tools.py workflow <repo> [--workflow NAME]

Until KIT-081 stage 1, sync-project.sh copied the spec validators and their schemas into a project's
.github/spec-lint/, and the project's CI ran that copy. A project now runs them from the kit: a session from the
installed kit (${AI_KIT_DIR:-$HOME/.ai-kit}/platforms/ci/validations/), its CI through the composite action
platforms/ci/actions/spec-tools, pinned to a kit commit by SHA with the version in a comment.

remove deletes the generated copy, and only it: when .github/spec-lint/README.md, a regular file, starts with the
heading the sync wrote, it deletes the kit-named files (the validators, the schemas, KIT_VERSION, that README and the
validators' byte caches) and then each folder left empty, with one "sync: removed" line; any other file stays, with a
"sync: kept" line. Nothing is read or deleted through a symbolic link. It then warns on stderr about each workflow
line that still names .github/spec-lint/.

check prints one "sync: ..." line per problem and exits 1: a generated copy left; a workflow line that names
.github/spec-lint/ (file:line and the fix); with --spec, no workflow that runs the spec tools (with --workflow, the
named one must).

workflow writes .github/workflows/spec-lint.yml (or the --workflow name) from the kit template, the action pinned to
this kit's commit (git rev-parse HEAD) with `# v<VERSION>`, when no workflow runs the spec tools and the file does
not exist; it exits 1 when the file exists and does not run them, and warns when the kit commit is not the release
tag v<VERSION>.

A workflow runs the spec tools when a line that is not a comment uses the action (any ref) or runs check_spec.py
from $AI_KIT_DIR. Python 3.9 compatible: sync-project.sh runs the system python3.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
TEMPLATE = KIT / "platforms" / "kits" / "github" / "workflows" / "spec-lint.yml"
ACTION = "ChristianPrzybulinski/agent-rules-kit/platforms/ci/actions/spec-tools"
COPY = ".github/spec-lint"
HEADING = "# spec-lint/ — generated copy"  # line 1 of the README every sync since 5.0.0 wrote
VALIDATORS = ("check_spec", "row_checks", "pr_gates", "spec_trace", "check_docs_structure")
SCHEMAS = ("spec", "feature", "requirement", "decision", "debt", "need", "progress", "task", "journey")
KIT_FILES = frozenset(["README.md", "KIT_VERSION"] + [name + ".py" for name in VALIDATORS]
                      + ["schemas/%s.schema.json" % name for name in SCHEMAS])
CACHE = re.compile(r"^__pycache__/(%s)\.[\w.-]+\.pyc$" % "|".join(VALIDATORS))
PIN = re.compile(r"(uses:\s*" + re.escape(ACTION) + r"@)[0-9a-f]{40}(?:[ \t]+#[ \t]*v\S*)?")
RUNS = re.compile(re.escape(ACTION) + r"@|\bAI_KIT_DIR\b.*\bcheck_spec\.py\b")
NAMES_COPY = re.compile(re.escape(COPY) + r"(?![\w.-])")
GUIDE = "platforms/kits/github/README.md"
RUNS_WHAT = "the spec-tools action, or check_spec.py from $AI_KIT_DIR"


def copy_folder(repo):
    """.github/spec-lint as a real folder reached through no symbolic link, else None."""
    github = Path(repo, ".github")
    folder = github / "spec-lint"
    if github.is_symlink() or folder.is_symlink() or not folder.is_dir():
        return None
    return folder


def generated(folder):
    readme = folder / "README.md"
    if readme.is_symlink() or not readme.is_file():
        return False
    try:
        with open(readme, encoding="utf-8", errors="replace") as handle:
            return handle.readline().rstrip("\r\n") == HEADING
    except OSError:
        return False


def entries(folder):
    """(relative path, path, is a kit file) for every file and symbolic link under the folder, never entering a
    symbolic link."""
    found = []
    stack = [folder]
    while stack:
        current = stack.pop()
        for path in sorted(current.iterdir()):
            rel = path.relative_to(folder).as_posix()
            if path.is_dir() and not path.is_symlink():
                stack.append(path)
                continue
            kit = not path.is_symlink() and path.is_file() and (rel in KIT_FILES or bool(CACHE.match(rel)))
            found.append((rel, path, kit))
    return sorted(found)


def workflows(repo):
    folder = Path(repo, ".github", "workflows")
    if not folder.is_dir():
        return []
    return [path for path in sorted(folder.iterdir()) if path.suffix in (".yml", ".yaml") and path.is_file()]


def code_lines(path):
    """(number, line) for each line of a workflow that is not a comment."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [(number, line) for number, line in enumerate(text.splitlines(), 1) if not line.lstrip().startswith("#")]


def runs_spec_tools(path):
    return any(RUNS.search(line) for _, line in code_lines(path))


def copy_callers(repo):
    """'.github/workflows/<file>:<line>' for each workflow line that names .github/spec-lint/."""
    return ["%s:%d" % (path.relative_to(repo).as_posix(), number)
            for path in workflows(repo) for number, line in code_lines(path) if NAMES_COPY.search(line)]


def caller_fix():
    return "run the spec tools through the spec-tools action pinned by SHA (%s)" % GUIDE


def remove(repo):
    folder = copy_folder(repo)
    if folder is not None and generated(folder):
        found = entries(folder)
        removed = 0
        for rel, path, kit in found:
            if kit:
                path.unlink()
                removed += 1
            else:
                print("sync: kept %s/%s: not a kit file; move it if the project still needs it" % (COPY, rel))
        for top, _, _ in os.walk(str(folder), topdown=False):  # never enters a symbolic link
            if not os.listdir(top):
                os.rmdir(top)
        print("sync: removed the generated %s/ (%d kit files): the spec tools run from the kit (KIT-081 stage 1)"
              % (COPY, removed))
    for caller in copy_callers(repo):
        print("sync: warning: %s names %s/, which the kit no longer writes; %s" % (caller, COPY, caller_fix()),
              file=sys.stderr)
    return 0


def check(repo, spec, name):
    problems = []
    folder = copy_folder(repo)
    if folder is not None and generated(folder):
        problems.append("sync: %s/ is the generated copy KIT-081 stage 1 retired; rerun sync-project.sh %s, which "
                        "removes it" % (COPY, repo))
    for caller in copy_callers(repo):
        problems.append("sync: %s names %s/, which the kit no longer writes; %s" % (caller, COPY, caller_fix()))
    if spec:
        if name:
            path = Path(repo, ".github", "workflows", name)
            if not path.is_file():
                problems.append("sync: %s missing" % name)
            elif not runs_spec_tools(path):
                problems.append("sync: %s does not run the spec tools (%s)" % (name, RUNS_WHAT))
        elif not any(runs_spec_tools(path) for path in workflows(repo)):
            problems.append("sync: no workflow under .github/workflows runs the spec tools (%s); sync-project.sh "
                            "%s writes spec-lint.yml" % (RUNS_WHAT, repo))
    for line in problems:
        print(line)
    return 1 if problems else 0


def git(*args):
    result = subprocess.run(["git", "-C", str(KIT), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def workflow(repo, name):
    if any(runs_spec_tools(path) for path in workflows(repo)):
        print("sync: %s already runs the spec tools in CI; kit workflow not written" % repo)
        return 0
    github = Path(repo, ".github")
    folder = github / "workflows"
    target = folder / (name or "spec-lint.yml")
    rel = target.relative_to(repo).as_posix()
    if github.is_symlink() or folder.is_symlink():
        print("sync: %s goes through a symbolic link; not written" % rel, file=sys.stderr)
        return 1
    if target.exists() or target.is_symlink():
        hint = ""
        if target.is_file() and any(NAMES_COPY.search(line) for _, line in code_lines(target)):
            hint = "; replace its %s/ steps with the spec-tools action, or delete it and rerun the sync" % COPY
        print("sync: %s exists and does not run the spec tools; not overwriting%s" % (rel, hint), file=sys.stderr)
        return 1
    sha = git("rev-parse", "HEAD")
    if not sha or not re.match(r"^[0-9a-f]{40}$", sha):
        print("sync: cannot pin the spec-tools action: %s is not a git checkout (git rev-parse HEAD)" % KIT,
              file=sys.stderr)
        return 1
    version = (KIT / "VERSION").read_text(encoding="utf-8").strip()
    text, count = PIN.subn(lambda match: "%s%s  # v%s" % (match.group(1), sha, version),
                           TEMPLATE.read_text(encoding="utf-8"))
    if count != 1:
        print("sync: %s pins the spec-tools action %d times, expected once" % (TEMPLATE, count), file=sys.stderr)
        return 2
    folder.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print("sync: wrote %s: the spec-tools action pinned to %s (v%s)" % (rel, sha, version))
    if "v" + version not in (git("tag", "--points-at", "HEAD") or "").split():
        print("sync: warning: the kit at %s is at %s, which the tag v%s does not name; that pin works once GitHub "
              "has the commit, and a sync from the installed kit (~/.ai-kit, the newest release) pins a release"
              % (KIT, sha[:12], version), file=sys.stderr)
    return 0


def main(argv):
    usage = "usage: sync_spec_tools.py remove|check|workflow <repo> [--spec] [--workflow NAME]"
    if len(argv) < 2 or argv[0] not in ("remove", "check", "workflow"):
        print(usage, file=sys.stderr)
        return 2
    command, repo, rest = argv[0], argv[1], argv[2:]
    spec, name = False, ""
    while rest:
        if rest[0] == "--spec":
            spec, rest = True, rest[1:]
        elif rest[0] == "--workflow" and len(rest) > 1:
            name, rest = rest[1], rest[2:]
        else:
            print(usage, file=sys.stderr)
            return 2
    if command == "remove":
        return remove(repo)
    if command == "check":
        return check(repo, spec, name)
    return workflow(repo, name)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
