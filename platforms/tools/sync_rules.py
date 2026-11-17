#!/usr/bin/env python3
"""Removes or reports the .claude/rules copies of the kit's path rules (KIT-081 stage 3). Called by sync-project.sh.

Usage: sync_rules.py remove <repo>
       sync_rules.py check <repo>

Until KIT-081 stage 3, sync-project.sh rendered each kit rule a profile receives into .claude/rules/<plugin>-<rule>.md,
since Claude Code loads a path rule by itself only from a project's .claude/rules/. The guardrails plugin's hook
(plugins/guardrails/hooks/path_rules.py) now gives the rule when a tool call reads or edits a matching file, so a copy
is a leftover. A copy is the kit's when it is a regular *.md file of .claude/rules/ (not a symbolic link) whose line
right after the frontmatter's closing `---` starts with the marker the sync wrote there; that covers the file names of every plugin the kit
had (guardrails-, core-, dev-, sdd-). Any other entry of .claude/rules/ is the project's own: it is never read through
a link, replaced or deleted, and nothing is read through a symbolic .claude or .claude/rules.

remove deletes each kit copy with one "sync: removed" line and, when it removed one, prints a "sync: kept" line for
every other entry and removes the folder if that left it empty. sync-project.sh runs it after CLAUDE.md carries the
marker the hook needs, so no session is left without the rules. check prints one line per copy left and the fix,
and exits 1 when there is one.

The AGENTS.md path-rule blocks stay (sync_agents_md.py): Codex reads only AGENTS.md, and a Codex equivalent of the
hook waits for a Codex probe (KIT-081). Python 3.9 compatible: sync-project.sh runs the system python3.
"""
import sys
from pathlib import Path

MARKER = "<!-- agent-rules-kit: generated from "  # the line render_rule wrote under each copy's frontmatter
RULES = ".claude/rules"
SYNC = "platforms/tools/sync-project.sh"


def real_dir(path):
    return not path.is_symlink() and path.is_dir()


def is_copy(path):
    """A regular *.md file, not a symbolic link, whose marker line is where render_rule wrote it: right after the
    closing `---` of a frontmatter that opens on line 1. A marker line anywhere else is the project's own text."""
    if path.is_symlink() or not path.is_file() or path.suffix != ".md":
        return False
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            if handle.readline().rstrip("\r\n") != "---":
                return False
            for line in handle:
                if line.rstrip("\r\n") == "---":
                    return handle.readline().startswith(MARKER)
            return False
    except OSError:
        return False


def entries(repo):
    """(the kit copies, the project's own entries) of .claude/rules/ by name, each sorted; both empty when the folder
    is missing or it or .claude is a symbolic link."""
    claude = Path(repo, ".claude")
    folder = claude / "rules"
    if not real_dir(claude) or not real_dir(folder):
        return [], []
    copies, own = [], []
    for entry in sorted(folder.iterdir()):
        (copies if is_copy(entry) else own).append(entry.name)
    return copies, own


def remove(repo):
    copies, own = entries(repo)
    if not copies:
        return 0
    folder = Path(repo, RULES)
    try:
        for name in copies:
            (folder / name).unlink()
            print(f"sync: removed {RULES}/{name}: a kit rule copy; the guardrails plugin's hook gives the rule"
                  " (KIT-081 stage 3)")
    except OSError as error:
        print(f"sync: cannot remove {error.filename}: {error.strerror}; remove it by hand and rerun the sync")
        return 1
    for name in own:
        print(f"sync: kept {RULES}/{name}: the project's own (no kit marker, or a symbolic link)")
    if not own:
        folder.rmdir()  # the sync created it; an empty folder is not tracked anyway
    return 0


def check(repo):
    copies, _ = entries(repo)
    for name in copies:
        print(f"sync: kit rule copy left: {RULES}/{name}")
    if copies:
        print(f"sync: KIT-081 stage 3: the guardrails plugin's hook gives the kit's path rules; run {SYNC} {repo} once,"
              " which removes the kit-marked copies and keeps the project's own rules")
    return 1 if copies else 0


def main(argv):
    usage = __doc__.split("\n\n")[1]
    if len(argv) != 3 or argv[1] not in ("remove", "check"):
        sys.exit(usage)
    return remove(argv[2]) if argv[1] == "remove" else check(argv[2])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
