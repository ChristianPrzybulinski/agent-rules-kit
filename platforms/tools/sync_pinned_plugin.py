#!/usr/bin/env python3
"""Writes or checks a vendored project's pin of the kit (KIT-072). Called by sync-project.sh.

Usage: sync_pinned_plugin.py preflight <repo>
       sync_pinned_plugin.py write <repo> <kit-dir> <kit-version> [<plain-skill>...]
       sync_pinned_plugin.py settings <repo>
       sync_pinned_plugin.py remove <repo>
       sync_pinned_plugin.py pin <repo> <kit-dir> < sources
       sync_pinned_plugin.py check <repo> <kit-version> < sources

A vendored project (sync-project.sh --vendor-skills) pins the whole kit for Claude Code in two generated folders:

- .claude/ai-kit/ holds the kit hooks as scripts (hooks/<Event>-<group>-<hook>.sh, each the kit hook command verbatim)
  and hooks/hooks.json, the settings fragment that runs them through "${CLAUDE_PROJECT_DIR}". settings merges that
  fragment into .claude/settings.json, so the guard and the other hooks run in every session at the repository root,
  trusted or not and under `claude -p` (Claude Code uses hooks in settings files before the folder is trusted;
  a repository plugin it does not).
- .claude/skills/guardrails-pinned/ is a skills-directory plugin with the kit agents, templates and every kit skill the
  profile does not copy as a plain skill (<plain-skill>), so each kit skill lists once. Claude Code loads it in place
  once the folder is trusted. Its manifest name is not guardrails because an installed guardrails@ai-kit keeps that
  name even while disabled; agent skill preloads are renamed to the name that resolves in the project.

settings also turns guardrails@ai-kit, which follows the kit head, off and the pinned copy on. sync-project.sh calls it
after write succeeded, so a failed write leaves the head plugin on. preflight refuses, before the sync's first write, a
folder of either name that is a symbolic link or carries no generated marker. write replaces a folder when any file
differs. remove deletes both marked folders and the kit hooks and the pinned key from .claude/settings.json (plugins
mode). pin prints the KIT_MANIFEST.json keys of the pin: KIT_COMMIT (the kit commit, "-dirty" when plugins/ has local
changes, empty outside a git checkout), each folder's sha256 per file and, under "copies", the sha256 of each other
vendored copy that sources lists on stdin as "<kit-file> <repo-path>" (sync-project.sh pin_sources: every kit_files
entry). check prints one "sync: ..." line per drift between the pin and the folders, those copies (one changed or gone,
a source the pin lacks), .claude/settings.json (enabledPlugins, the kit hooks), settings.local.json and, only with
AI_KIT_CLAUDE_PROBE=1 and the claude CLI on PATH, the plugins `claude plugin list` shows for the repository; it exits 1
on drift.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import OrderedDict
from pathlib import Path

KIT_PLUGIN = "guardrails"
PINNED = "guardrails-pinned"
HEAD_ID = KIT_PLUGIN + "@ai-kit"
PINNED_ID = PINNED + "@skills-dir"
MARKER = ".agent-rules-kit"
PLUGIN_REL = ".claude/skills/" + PINNED
KIT_REL = ".claude/ai-kit"
HOOK_DIR = KIT_REL + "/hooks"
HOOK_MARK = "/" + HOOK_DIR + "/"  # a settings hook command that contains it is the kit's
PRELOAD = re.compile(r"^(\s*-\s+)" + KIT_PLUGIN + r":([A-Za-z0-9._-]+)\s*$")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scanned_files(directory):
    """sha256 per regular file under directory, keyed by its relative path; links are skipped."""
    files = {}
    for base, dirnames, filenames in os.walk(directory):
        dirnames.sort()
        for filename in sorted(filenames):
            path = os.path.join(base, filename)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            files[os.path.relpath(path, directory).replace(os.sep, "/")] = sha256(path)
    return files


def owned(path):
    """A real folder (not a symbolic link) that carries the generated marker."""
    return path.is_dir() and not path.is_symlink() and (path / MARKER).is_file()


def preflight(repo):
    status = 0
    for rel in (PLUGIN_REL, KIT_REL):
        path = Path(repo, rel)
        if path.is_symlink():
            print(f"sync: {path} is a symbolic link; replace it by hand, the kit's pin writes a real folder there")
            status = 1
        elif path.exists() and not owned(path):
            print(f"sync: {path} exists and is not generated; rename it, the kit's pin needs the name")
            status = 1
    return status


def rename_preloads(text, plain):
    """Renames each guardrails:<skill> item in the agent's frontmatter to the name the project resolves."""
    lines = text.split("\n")
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        return text
    end = lines.index("---", 1)
    for index in range(1, end):
        match = PRELOAD.match(lines[index])
        if match:
            name = match.group(2)
            lines[index] = match.group(1) + (name if name in plain else f"{PINNED}:{name}")
    return "\n".join(lines)


def marker_text(version):
    return f"plugins/{KIT_PLUGIN} kit {version} generated by platforms/tools/sync-project.sh; do not edit\n"


def build_plugin(source, version, plain, dest):
    (dest / ".claude-plugin").mkdir(parents=True)
    manifest = json.loads((source / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    manifest["name"] = PINNED
    (dest / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                                         encoding="utf-8")
    if (source / "templates").is_dir():
        shutil.copytree(source / "templates", dest / "templates")
    (dest / "agents").mkdir()
    for agent in sorted((source / "agents").glob("*.md")):
        text = agent.read_text(encoding="utf-8")
        (dest / "agents" / agent.name).write_text(rename_preloads(text, plain), encoding="utf-8")
    for skill in sorted((source / "skills").iterdir()):
        if (skill / "SKILL.md").is_file() and skill.name not in plain:
            shutil.copytree(skill, dest / "skills" / skill.name)
    (dest / MARKER).write_text(marker_text(version), encoding="utf-8")


def build_kit_dir(source, version, dest):
    """The kit hooks as scripts plus the settings fragment that runs them."""
    hooks = json.loads((source / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    (dest / "hooks").mkdir(parents=True)
    fragment = OrderedDict()
    for event, groups in hooks.items():
        for g, group in enumerate(groups):
            handlers = []
            for h, hook in enumerate(group.get("hooks", [])):
                name = f"{event}-{g}-{h}.sh"
                (dest / "hooks" / name).write_text(
                    "#!/bin/bash\n# generated by agent-rules-kit platforms/tools/sync-project.sh from"
                    f" plugins/{KIT_PLUGIN}/hooks/hooks.json ({event}, group {g}, hook {h}), kit {version}; do not edit\n"
                    + hook["command"] + "\n", encoding="utf-8")
                handler = OrderedDict(type="command", command=f'bash "${{CLAUDE_PROJECT_DIR}}/{HOOK_DIR}/{name}"')
                if "timeout" in hook:
                    handler["timeout"] = hook["timeout"]
                handlers.append(handler)
            entry = OrderedDict()
            if "matcher" in group:
                entry["matcher"] = group["matcher"]
            entry["hooks"] = handlers
            fragment.setdefault(event, []).append(entry)
    (dest / "hooks" / "hooks.json").write_text(json.dumps(fragment, indent=2, ensure_ascii=False) + "\n",
                                               encoding="utf-8")
    (dest / MARKER).write_text(marker_text(version), encoding="utf-8")


def replace_tree(staged, dest):
    if owned(dest) and scanned_files(dest) == scanned_files(staged):
        return False
    if owned(dest):
        shutil.rmtree(dest)
    elif dest.exists() or dest.is_symlink():  # preflight refuses this; never delete what the sync does not own
        raise SystemExit(f"sync: {dest} is not generated; refusing to replace it")
    staged.rename(dest)
    return True


def write(repo, kit, version, plain):
    if preflight(repo):
        return 1
    source = Path(kit, "plugins", KIT_PLUGIN)
    claude = Path(repo, ".claude")
    (claude / "skills").mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".kit-pin-", dir=claude))
    try:
        build_plugin(source, version, set(plain), staging / "plugin")
        build_kit_dir(source, version, staging / "kit")
        changed = [replace_tree(staging / "plugin", Path(repo, PLUGIN_REL)),
                   replace_tree(staging / "kit", Path(repo, KIT_REL))]
        if any(changed):
            print(f"sync: pinned the kit as {PLUGIN_REL} and {KIT_REL} (kit {version})")
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return 0


def load_settings(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle, object_pairs_hook=OrderedDict)
    except FileNotFoundError:
        return OrderedDict()
    if not isinstance(data, dict):
        raise SystemExit(f"sync: {path} is not a JSON object; fix it by hand")
    return data


def save_settings(path, data):
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    try:
        current = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        current = None
    if current != text:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)


def is_kit_handler(handler):
    return isinstance(handler, dict) and HOOK_MARK in str(handler.get("command", ""))


def without_kit_hooks(hooks):
    """The settings hooks with every kit handler removed, and the groups and events that leaves empty."""
    kept = OrderedDict()
    for event, groups in (hooks.items() if isinstance(hooks, dict) else []):
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


def kit_hooks_in(hooks):
    """Only the kit handlers of the settings hooks, as {event: [groups]}, for comparison with the fragment."""
    found = {}
    for event, groups in (hooks.items() if isinstance(hooks, dict) else []):
        for group in groups if isinstance(groups, list) else []:
            if isinstance(group, dict) and isinstance(group.get("hooks"), list):
                handlers = [h for h in group["hooks"] if is_kit_handler(h)]
                if handlers:
                    found.setdefault(event, []).append(dict(group, hooks=handlers))
    return found


def settings(repo):
    path = Path(repo, ".claude", "settings.json")
    fragment = json.loads(Path(repo, HOOK_DIR, "hooks.json").read_text(encoding="utf-8"),
                          object_pairs_hook=OrderedDict)
    data = load_settings(path)
    enabled = data.setdefault("enabledPlugins", OrderedDict())
    enabled[HEAD_ID] = False
    enabled[PINNED_ID] = True
    hooks = without_kit_hooks(data.get("hooks"))
    for event, groups in fragment.items():
        hooks.setdefault(event, []).extend(groups)
    data["hooks"] = hooks
    save_settings(path, data)
    return 0


def remove(repo):
    for rel in (PLUGIN_REL, KIT_REL):
        path = Path(repo, rel)
        if owned(path):
            shutil.rmtree(path)
            print(f"sync: removed {rel} (plugins mode loads guardrails@ai-kit)")
    path = Path(repo, ".claude", "settings.json")
    if path.is_file():
        data = load_settings(path)
        enabled = data.get("enabledPlugins")
        if isinstance(enabled, dict):
            enabled.pop(PINNED_ID, None)
        if "hooks" in data:
            hooks = without_kit_hooks(data["hooks"])
            if hooks:
                data["hooks"] = hooks
            else:
                del data["hooks"]
        save_settings(path, data)
    return 0


def kit_commit(kit):
    def git(*args):
        return subprocess.run(["git", "-C", str(kit), *args], capture_output=True, text=True, check=True).stdout
    try:
        commit = git("rev-parse", "HEAD").strip()
        dirty = git("status", "--porcelain", "--", "plugins").strip()
    except (OSError, subprocess.CalledProcessError):
        return ""
    return commit + ("-dirty" if dirty else "")


def read_sources():
    """(kit file, repo path) per stdin line; none when stdin is a terminal."""
    if sys.stdin is None or sys.stdin.isatty():
        return []
    pairs = []
    for line in sys.stdin.read().splitlines():
        parts = line.split()
        if len(parts) == 2:
            pairs.append((parts[0], parts[1]))
    return pairs


def pin(repo, kit):
    sources = read_sources()
    keys = {}
    if owned(Path(repo, PLUGIN_REL)) and owned(Path(repo, KIT_REL)):
        keys = {"KIT_COMMIT": kit_commit(kit),
                "plugin": {"name": PINNED, "files": scanned_files(Path(repo, PLUGIN_REL))},
                "kit_dir": {"path": KIT_REL, "files": scanned_files(Path(repo, KIT_REL))},
                "copies": {rel: sha256(src) for src, rel in sources}}
    print(json.dumps(keys, sort_keys=True))
    return 0


def read_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def tree_lines(repo, rel, recorded):
    lines = []
    folder = Path(repo, rel)
    if not owned(folder):
        return [f"{rel} carries no {MARKER} marker or is a symbolic link (rerun sync-project.sh)"]
    files = recorded.get("files") if isinstance(recorded, dict) and isinstance(recorded.get("files"), dict) else {}
    found = scanned_files(folder)
    for name in sorted(files):
        if name not in found:
            lines.append(f"{rel}/{name} missing")
        elif found[name] != files[name]:
            lines.append(f"{rel}/{name} diverges from the manifest")
    for name in sorted(set(found) - set(files)):
        lines.append(f"{rel}/{name} not in manifest")
    return lines


def claude_plugins(repo):
    """The plugin list `claude plugin list --json` prints in the repository; None unless AI_KIT_CLAUDE_PROBE=1."""
    if os.environ.get("AI_KIT_CLAUDE_PROBE") != "1" or not shutil.which("claude"):
        return None
    try:
        result = subprocess.run(["claude", "plugin", "list", "--json"], cwd=repo, capture_output=True, text=True,
                                timeout=60, check=False)
        plugins = json.loads(result.stdout) if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, ValueError):
        plugins = None
    if not isinstance(plugins, list):
        print("sync: note: `claude plugin list --json` gave no plugin list; the active plugins are unverified")
        return None
    return [plugin for plugin in plugins if isinstance(plugin, dict)]


def check(repo, version):
    sources = read_sources()
    lines = []
    manifest = read_json(Path(repo, ".claude", "skills", "KIT_MANIFEST.json")) or {}
    if not Path(repo, PLUGIN_REL).exists() or not isinstance(manifest.get("plugin"), dict):
        lines.append(f"{PLUGIN_REL} missing: the kit plugin is not pinned (rerun sync-project.sh)")
    else:
        if not isinstance(manifest.get("KIT_COMMIT"), str):
            lines.append(".claude/skills/KIT_MANIFEST.json records no KIT_COMMIT (rerun sync-project.sh)")
        lines += tree_lines(repo, PLUGIN_REL, manifest["plugin"])
        lines += tree_lines(repo, KIT_REL, manifest.get("kit_dir"))
        plugin_json = read_json(Path(repo, PLUGIN_REL, ".claude-plugin", "plugin.json")) or {}
        if (plugin_json.get("name"), plugin_json.get("version")) != (PINNED, version):
            lines.append(f"{PLUGIN_REL}/.claude-plugin/plugin.json names {plugin_json.get('name')}"
                         f" {plugin_json.get('version')}, kit version {version}")
        copies = manifest.get("copies") if isinstance(manifest.get("copies"), dict) else {}
        for rel in sorted(copies):
            path = Path(repo, rel)
            if path.is_symlink() or not path.is_file():
                lines.append(f"{rel} is pinned but missing")
            elif sha256(path) != copies[rel]:
                lines.append(f"{rel} diverges from the pin")
        for rel in sorted({rel for _, rel in sources} - set(copies)):
            lines.append(f"{rel} is not in the pin (rerun sync-project.sh)")
        project = read_json(Path(repo, ".claude", "settings.json")) or {}
        enabled = project.get("enabledPlugins") if isinstance(project.get("enabledPlugins"), dict) else {}
        parts = []
        if enabled.get(HEAD_ID) is not False:
            parts.append(f"{HEAD_ID}: want false")
        if enabled.get(PINNED_ID) is not True:
            parts.append(f"{PINNED_ID}: want true")
        extra = sorted(k for k in enabled if isinstance(k, str) and k.endswith("@ai-kit") and k != HEAD_ID)
        if extra:
            parts.append("extra: " + ",".join(extra))
        fragment = read_json(Path(repo, HOOK_DIR, "hooks.json"))
        if fragment is not None and kit_hooks_in(project.get("hooks")) != fragment:
            parts.append(f"hooks: want the kit hooks of {HOOK_DIR}/hooks.json")
        if parts:
            lines.append(f".claude/settings.json diverges from the pin ({'; '.join(parts)})")
    local = read_json(Path(repo, ".claude", "settings.local.json")) or {}
    enabled = local.get("enabledPlugins") if isinstance(local.get("enabledPlugins"), dict) else {}
    if enabled.get(HEAD_ID) is True:
        lines.append(f".claude/settings.local.json enables {HEAD_ID}, which loads the kit head beside the pin")
    if enabled.get(PINNED_ID) is False:
        lines.append(f".claude/settings.local.json turns off {PINNED_ID}, the pinned kit")
    for line in lines:
        print("sync: " + line)
    failed = bool(lines)
    plugins = claude_plugins(repo)
    if plugins is not None:
        if any(p.get("id") == HEAD_ID and p.get("enabled") is True for p in plugins):
            print(f"sync: claude loads {HEAD_ID} here, the kit head beside the pin")
            failed = True
        loaded = [p for p in plugins if p.get("id") == PINNED_ID]
        if not loaded:
            print(f"sync: claude lists no {PINNED_ID} here: accept the trust dialog at the main checkout root;"
                  " until then the pinned skills and agents do not load (the kit hooks in .claude/settings.json do)")
            failed = True
        for plugin in loaded:
            errors = [str(e) for e in plugin.get("errors") or []]
            if errors or plugin.get("enabled") is not True:
                print(f"sync: claude does not load {PINNED_ID}: {'; '.join(errors) or 'disabled'}")
                failed = True
            elif plugin.get("version") != version:
                print(f"sync: claude loads {PINNED_ID} {plugin.get('version')}, kit version {version}")
                failed = True
            else:
                print(f"sync: claude loads {PINNED_ID} {version} here")
    return 1 if failed else 0


def main(argv):
    usage = __doc__.split("\n\n")[1]
    if len(argv) < 3:
        sys.exit(usage)
    command, repo = argv[1], argv[2]
    if command == "preflight" and len(argv) == 3:
        return preflight(repo)
    if command == "write" and len(argv) >= 5:
        return write(repo, argv[3], argv[4], argv[5:])
    if command == "settings" and len(argv) == 3:
        return settings(repo)
    if command == "remove" and len(argv) == 3:
        return remove(repo)
    if command == "pin" and len(argv) == 4:
        return pin(repo, argv[3])
    if command == "check" and len(argv) == 4:
        return check(repo, argv[3])
    sys.exit(usage)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
