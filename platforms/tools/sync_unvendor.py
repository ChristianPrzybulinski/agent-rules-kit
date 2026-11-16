#!/usr/bin/env python3
"""Removes or reports the vendored kit state KIT-081 stage 2b retired. Called by sync-project.sh and doctor.sh.

Usage: sync_unvendor.py remove <repo>
       sync_unvendor.py check <repo>

Until KIT-081 stage 2b, `sync-project.sh --vendor-skills` copied the profile's kit skills into a project and pinned the
kit there (KIT-072). A project now uses the installed guardrails@ai-kit plugin, which follows the kit's `stable`
branch, so that state is a leftover:

- .claude/skills/KIT_MANIFEST.json, the manifest of the copies;
- each .claude/skills/<name>/ folder that carries the generated .agent-rules-kit marker: the plain skill copies and
  guardrails-pinned/, the pinned plugin;
- .claude/ai-kit/ with that marker: the pinned kit hooks and tools;
- in .claude/settings.json, the guardrails-pinned@skills-dir key of enabledPlugins and each hook handler whose command
  runs a script under .claude/ai-kit/hooks/.

Only a real folder (not a symbolic link) with the marker is the kit's. An unmarked folder or a symbolic link is never
read, replaced or deleted, and nothing is read through a symbolic .claude or .claude/skills folder.

remove deletes that state, printing one "sync: removed ..." line per removal, and keeps the project's own hooks and
keys; it writes .claude/settings.json only when it takes a key or a hook out of it (KIT-083). A folder the manifest or
the pin names that is not the kit's is kept with a "sync: kept ..." line.
sync-project.sh runs it after it has turned guardrails@ai-kit on and written the profile list into CLAUDE.md, so a
failure leaves the plugin on and the profile recorded. check prints one "sync: ..." line per leftover and the fix,
and exits 1 when there is one.
"""
import json
import shutil
import sys
from collections import OrderedDict
from pathlib import Path

MARKER = ".agent-rules-kit"
MANIFEST = ".claude/skills/KIT_MANIFEST.json"
PINNED = "guardrails-pinned"
PINNED_ID = PINNED + "@skills-dir"
KIT_DIR = ".claude/ai-kit"
HOOK_MARK = "/" + KIT_DIR + "/hooks/"  # a settings hook command that contains it ran a pinned kit hook
SYNC = "platforms/tools/sync-project.sh"


def owned(path):
    """A real folder (not a symbolic link) that carries the generated marker."""
    return not path.is_symlink() and path.is_dir() and (path / MARKER).is_file()


def real_dir(path):
    return not path.is_symlink() and path.is_dir()


def is_kit_handler(handler):
    return isinstance(handler, dict) and HOOK_MARK in str(handler.get("command", ""))


def without_kit_hooks(hooks):
    """The settings hooks with every kit handler removed, and the groups and events that leaves empty."""
    kept = OrderedDict()
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            kept[event] = groups
            continue
        rest = []
        for group in groups:
            if isinstance(group, dict) and isinstance(group.get("hooks"), list):
                handlers = [h for h in group["hooks"] if not is_kit_handler(h)]
                if not handlers:
                    continue
                if len(handlers) != len(group["hooks"]):
                    group = OrderedDict(group, hooks=handlers)
            rest.append(group)
        if rest:
            kept[event] = rest
    return kept


def kit_handler_count(hooks):
    return sum(1 for groups in hooks.values() if isinstance(groups, list)
               for group in groups if isinstance(group, dict) and isinstance(group.get("hooks"), list)
               for handler in group["hooks"] if is_kit_handler(handler))


def load_settings(repo):
    """The parsed .claude/settings.json when it is a JSON object, else None (sync-project.sh reports the rest)."""
    path = Path(repo, ".claude", "settings.json")
    if path.is_symlink() or not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle, object_pairs_hook=OrderedDict)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def manifest_skills(repo):
    """The skill names KIT_MANIFEST.json lists, to name the ones a project kept as its own."""
    try:
        with open(Path(repo, MANIFEST), encoding="utf-8") as handle:
            skills = json.load(handle).get("skills")
    except (OSError, ValueError, AttributeError):
        return []
    return sorted(name for name in skills if isinstance(name, str)) if isinstance(skills, dict) else []


def leftovers(repo):
    """[(path, what)] for each piece of vendored kit state in the repository, folders first, settings last."""
    found = []
    claude = Path(repo, ".claude")
    if not real_dir(claude):
        return found
    skills = claude / "skills"
    if real_dir(skills):
        for child in sorted(skills.iterdir()):
            if owned(child):
                what = "the pinned kit plugin of KIT-072" if child.name == PINNED else "a vendored kit skill copy"
                found.append((f".claude/skills/{child.name}", what))
        manifest = skills / "KIT_MANIFEST.json"
        if manifest.is_file() and not manifest.is_symlink():
            found.append((MANIFEST, "the manifest of the vendored copies"))
    if owned(Path(repo, KIT_DIR)):
        found.append((KIT_DIR, "the pinned kit hooks and tools of KIT-072"))
    data = load_settings(repo)
    if data is not None:
        enabled = data.get("enabledPlugins")
        if isinstance(enabled, dict) and PINNED_ID in enabled:
            found.append((f".claude/settings.json enabledPlugins {PINNED_ID}", "the pinned plugin's switch"))
        hooks = data.get("hooks")
        count = kit_handler_count(hooks) if isinstance(hooks, dict) else 0
        if count:
            found.append((f".claude/settings.json hooks that run {KIT_DIR}/hooks/",
                          f"{count} pinned kit hook handler{'' if count == 1 else 's'}"))
    return found


def kept(repo):
    """The paths the vendored state names that are not the kit's: never read, replaced or deleted."""
    lines = []
    claude = Path(repo, ".claude")
    if not real_dir(claude):
        return lines
    skills = claude / "skills"
    names = manifest_skills(repo) if real_dir(skills) else []
    for name in sorted(set(names) | {PINNED}):
        path = skills / name
        if (path.exists() or path.is_symlink()) and not owned(path):
            lines.append(f".claude/skills/{name}")
    path = Path(repo, KIT_DIR)
    if (path.exists() or path.is_symlink()) and not owned(path):
        lines.append(KIT_DIR)
    manifest = Path(repo, MANIFEST)
    if manifest.is_symlink():
        lines.append(MANIFEST)
    return lines


def remove(repo):
    state = leftovers(repo)
    if not state:
        return 0
    for rel in kept(repo):
        print(f"sync: kept {rel}: a symbolic link or a folder without the {MARKER} marker is the project's own")
    try:
        for rel, what in state:
            path = Path(repo, rel)
            if rel.startswith(".claude/settings.json"):
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"sync: removed {rel}: {what} (KIT-081 stage 2b)")
    except OSError as error:
        print(f"sync: cannot remove {error.filename}: {error.strerror}; remove it by hand and rerun the sync")
        return 1
    data = load_settings(repo)
    if data is not None:
        changed = False  # the file is written only when a key or hook leaves it (KIT-083)
        enabled = data.get("enabledPlugins")
        if isinstance(enabled, dict) and PINNED_ID in enabled:
            del enabled[PINNED_ID]
            changed = True
            print(f"sync: removed .claude/settings.json enabledPlugins {PINNED_ID}: the pinned plugin's switch (KIT-081 stage 2b)")
        hooks = data.get("hooks")
        count = kit_handler_count(hooks) if isinstance(hooks, dict) else 0
        if count:
            rest = without_kit_hooks(hooks)
            if rest:
                data["hooks"] = rest
            else:
                del data["hooks"]
            changed = True
            print(f"sync: removed .claude/settings.json hooks that run {KIT_DIR}/hooks/: {count} pinned kit hook"
                  f" handler{'' if count == 1 else 's'} (KIT-081 stage 2b); the plugin runs the kit hooks")
        if changed:
            path = Path(repo, ".claude", "settings.json")
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    skills = Path(repo, ".claude", "skills")
    if real_dir(skills) and not any(skills.iterdir()):
        skills.rmdir()  # the vendored sync created it; an empty folder is not tracked anyway
    return 0


def check(repo):
    state = leftovers(repo)
    for rel, what in state:
        print(f"sync: vendored kit state left: {rel}: {what}")
    if state:
        print(f"sync: KIT-081 stage 2b removed the vendored mode: run {SYNC} {repo} once; it removes this state,"
              " keeps the project's own files and leaves guardrails@ai-kit on")
    return 1 if state else 0


def main(argv):
    usage = __doc__.split("\n\n")[1]
    if len(argv) != 3 or argv[1] not in ("remove", "check"):
        sys.exit(usage)
    return remove(argv[2]) if argv[1] == "remove" else check(argv[2])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
