#!/usr/bin/env python3
"""guardrails hooks: the project profile keys a hook reads (KIT-087 P2a), `spec_root` and `stacks`, from the kit's
resolver, cached per session.

The hooks hard-coded `docs/spec/` and took every `.gd` file as Godot; they now read the project's profile
(`.ai-kit.yaml`, else its legacy homes) through `platforms/tools/profile.py resolve --json`, the one resolver.

- Resolver: the first `platforms/tools/profile.py` of $AI_KIT_DIR, the kit checkout this plugin runs from, then
  ~/.ai-kit. It runs as its own process with `-S` (no site-packages: the resolver's fallback parser, which resolves
  the same view as pyyaml, at about a third of the start-up) and a timeout.
- Cache: one file per session, $CLAUDE_PLUGIN_DATA/profile/<session_id>.json, maps the project root to the view and
  its key: the modification time and size of the root's `.ai-kit.yaml` and `CLAUDE.md` (the legacy home of
  `stacks`) and of the resolver itself. A changed key resolves again; a failed resolution is cached as no view, so a
  broken profile costs one run per change, not one per tool call. A session's first file prunes the files older than
  PRUNE_DAYS. Without CLAUDE_PLUGIN_DATA every call resolves.
- Failure: `view` returns None on any error (no resolver, a refused profile, a timeout, an unwritable cache), and the
  caller keeps its pre-profile behaviour. A hook never blocks on the profile.

Python 3.9, standard library only: hooks.json runs the system python3.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
RESOLVER = Path("platforms") / "tools" / "profile.py"
FILES = (".ai-kit.yaml", "CLAUDE.md")
STATE = "profile"
PRUNE_DAYS = 3
TIMEOUT_S = 3
UNSAFE = re.compile(r"[^A-Za-z0-9_.-]")


def resolver(env):
    """The kit resolver a hook runs: $AI_KIT_DIR's, this plugin's kit checkout's, then ~/.ai-kit's; None if none."""
    homes = [env.get("AI_KIT_DIR"), str(PLUGIN.parent.parent), os.path.join(os.path.expanduser("~"), ".ai-kit")]
    for home in homes:
        if home:
            tool = Path(home) / RESOLVER
            if tool.is_file():
                return tool
    return None


def top(path):
    """The git top level above `path` (a folder holding `.git`), else `path` itself."""
    here = os.path.realpath(path)
    while not os.path.exists(os.path.join(here, ".git")):
        parent = os.path.dirname(here)
        if parent == here:
            return os.path.realpath(path)
        here = parent
    return here


def stamp(path):
    try:
        info = os.stat(path)
    except OSError:
        return None
    return [info.st_mtime_ns, info.st_size]


def resolve(tool, root):
    """{'spec_root': str, 'stacks': dict} from the resolver, or None when it fails or prints something else."""
    try:
        result = subprocess.run([sys.executable, "-B", "-S", str(tool), "resolve", "--json", root],
                                stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=TIMEOUT_S, cwd=root)
        data = json.loads(result.stdout) if result.returncode == 0 else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("spec_root"), str) \
            or not isinstance(data.get("stacks"), dict):
        return None
    return {"spec_root": data["spec_root"], "stacks": data["stacks"]}


def prune(folder, keep):
    cutoff = time.time() - PRUNE_DAYS * 86400
    with os.scandir(folder) as entries:
        for entry in entries:
            try:
                if entry.name.endswith(".json") and entry.path != str(keep) and entry.stat().st_mtime < cutoff:
                    os.unlink(entry.path)
            except OSError:
                continue


def view(root, env, session=None):
    """The profile keys the hooks read for the project at `root`, cached for the session; None when unknown."""
    try:
        tool = resolver(env)
        if tool is None:
            return None
        root = top(root)
        key = [stamp(os.path.join(root, name)) for name in FILES] + [stamp(tool)]
        data = env.get("CLAUDE_PLUGIN_DATA")
        if not data:
            return resolve(tool, root)
        name = UNSAFE.sub("_", session if isinstance(session, str) else "")[:128] or "unknown"
        cache = Path(data) / STATE / f"{name}.json"
        try:
            entries = json.loads(cache.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            entries = None
        entries = entries if isinstance(entries, dict) else {}
        entry = entries.get(root)
        if isinstance(entry, dict) and entry.get("key") == key:
            return entry.get("view")
        found = resolve(tool, root)
        entries[root] = {"key": key, "view": found}
        cache.parent.mkdir(parents=True, exist_ok=True)
        if not cache.exists():
            try:
                prune(cache.parent, cache)
            except OSError:
                pass
        temp = cache.with_name(f"{cache.name}.{os.getpid()}.tmp")
        temp.write_text(json.dumps(entries), encoding="utf-8")
        os.replace(temp, cache)  # parallel hooks: the last whole write wins, never a torn file
        return found
    except Exception:  # noqa: BLE001 - the profile is advice for a hook, which must never fail on it
        return None


def stacks_of(found, relative):
    """The stacks of the folders of `found['stacks']` that hold the root-relative path `relative`."""
    names = set()
    for folder, value in ((found or {}).get("stacks") or {}).items():
        if folder == "." or relative == folder or relative.startswith(folder.rstrip("/") + "/"):
            names.update([value] if isinstance(value, str) else value if isinstance(value, list) else [])
    return names
