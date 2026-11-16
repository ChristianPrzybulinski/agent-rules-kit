#!/usr/bin/env bash
# Moves the kit clone to the newest release, moves the Codex and Claude Code marketplaces to the stable branch once
# (KIT-081), then updates their plugins. Usage: refresh.sh
set -euo pipefail

KIT="${AI_KIT_DIR:-$HOME/.ai-kit}"
# shellcheck source=SCRIPTDIR/codex-bin.sh
source "$(dirname "${BASH_SOURCE[0]}")/codex-bin.sh"
# shellcheck source=SCRIPTDIR/kit-release.sh
source "$(dirname "${BASH_SOURCE[0]}")/kit-release.sh"

warn() {
  printf 'WARN: refresh: %s\n' "$*" >&2
}

fail() {
  printf 'FAIL: refresh: %s\n' "$*" >&2
  exit 1
}

json_contains() {
  local payload="$1"
  local needle="$2"
  python3 - "$needle" "$payload" <<'PY'
import json
import sys

try:
    data = json.loads(sys.argv[2])
except json.JSONDecodeError:
    raise SystemExit(1)
needle = sys.argv[1]
def contains(value):
    if isinstance(value, str):
        return value == needle
    if isinstance(value, list):
        return any(contains(item) for item in value)
    if isinstance(value, dict):
        return any(contains(item) for item in value.values())
    return False
raise SystemExit(0 if contains(data) else 1)
PY
}

# KIT-013: Claude caches a plugin per version, so a kit change without a version bump leaves the cache stale.
# Prints each user-scope <plugin>@ai-kit whose cache differs from its directory in the marketplace clone.
claude_stale_plugins() {
  python3 - "$1" "$2" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

RUNTIME_MARKERS = {".in_use"}

def tree_hash(root):
    digest = hashlib.sha256()
    for directory, dirs, files in os.walk(root):
        if Path(directory) == root:
            # Claude keeps its .in_use process markers at the top of a cache directory.
            dirs[:] = [name for name in dirs if name not in RUNTIME_MARKERS]
            files = [name for name in files if name not in RUNTIME_MARKERS]
        dirs.sort()
        for name in sorted(files):
            path = Path(directory, name)
            relative = path.relative_to(root)
            digest.update(str(relative).encode() + b"\0")
            digest.update(b"link:" + os.readlink(path).encode() if path.is_symlink() else path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()

try:
    marketplaces = json.loads(sys.argv[1])
    plugins = json.loads(sys.argv[2])
except json.JSONDecodeError:
    raise SystemExit(0)
if not isinstance(marketplaces, list) or not isinstance(plugins, list):
    raise SystemExit(0)
location = next((m.get("installLocation") for m in marketplaces if m.get("name") == "ai-kit"), None)
if not location:
    raise SystemExit(0)
try:
    catalog = json.loads(Path(location, ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(0)
sources = {entry.get("name"): entry.get("source") for entry in catalog.get("plugins", [])}
stale = set()
for plugin in plugins:
    name, _, marketplace = str(plugin.get("id", "")).partition("@")
    source = sources.get(name)
    install = plugin.get("installPath")
    if marketplace != "ai-kit" or plugin.get("scope", "user") != "user" or not isinstance(source, str) or not install:
        continue
    source_dir = Path(location, source)
    if source_dir.is_dir() and (not Path(install).is_dir() or tree_hash(source_dir) != tree_hash(Path(install))):
        stale.add(name)
for name in sorted(stale):
    print(name)
PY
}

run_step() {
  local label="$1"
  local output
  shift
  if ! output="$("$@" 2>&1)"; then
    [[ -z "$output" ]] || printf '%s\n' "$output" >&2
    fail "$label"
  fi
}

# KIT-081: copies the files of a plugin data backup back into the data folder and prints the counts. A file the
# reinstall wrote is newer and stays; a rule-load log (*.jsonl) both hold gets the backup's lines first, under the
# lock the InstructionsLoaded hook takes, so a session that logs meanwhile loses no line.
restore_plugin_data() {
  python3 - "$1" "$2" <<'PY'
import fcntl
import os
import shutil
import sys
import tempfile

backup, target = sys.argv[1], sys.argv[2]
restored = merged = kept = 0
for directory, dirs, files in os.walk(backup):
    dirs.sort()
    for name in sorted(files):
        source = os.path.join(directory, name)
        destination = os.path.join(target, os.path.relpath(source, backup))
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        if not os.path.lexists(destination):
            shutil.copy2(source, destination, follow_symlinks=False)
            restored += 1
        elif name.endswith(".jsonl") and os.path.isfile(destination) and not os.path.islink(destination):
            with open(source, "rb") as handle:
                older = handle.read()
            if older and not older.endswith(b"\n"):
                older += b"\n"
            with open(destination + ".lock", "a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                with open(destination, "rb") as handle:
                    newer = handle.read()
                handle, temporary = tempfile.mkstemp(dir=os.path.dirname(destination), prefix=".restore-")
                with os.fdopen(handle, "wb") as out:
                    out.write(older + newer)
                shutil.copymode(destination, temporary)
                os.replace(temporary, destination)
            merged += 1
        else:
            kept += 1
print(f"{restored} restored, {merged} merged, {kept} kept (newer)")
PY
}

# KIT-081: Claude Code keeps a marketplace's ref with its source and has no command that changes it, so the move of
# the ai-kit marketplace to the stable branch is a remove and an add, once per machine. The remove also uninstalls
# the kit plugins and deletes their data folders (the InstructionsLoaded rule-load log among them), so each folder is
# copied to a dated backup first and restored after the install; the backup stays. `--scope user` leaves a project's
# declaration alone when refresh.sh runs inside a repository. Any failure names the commands left and keeps the backup.
claude_move_to_stable() {
  local from="$1"
  local data
  local backup
  local names=()
  local installs=""
  local restore_hint=""
  local name
  local plugin_dir
  local output
  local counts
  data="$(claude_plugins_root)/data"
  backup="${XDG_STATE_HOME:-$HOME/.local/state}/ai-kit/plugin-data-backup/$(date -u +%Y%m%dT%H%M%SZ)"
  for plugin_dir in "$KIT"/plugins/*/; do
    [[ -d "$plugin_dir/.claude-plugin" ]] || continue
    name="$(basename "$plugin_dir")"
    names+=("$name")
    installs="$installs${installs:+ && }claude plugin install $name@ai-kit --scope user"
  done
  [[ "${#names[@]}" -gt 0 ]] || fail "the kit has no Claude plugin to move"
  for name in "${names[@]}"; do
    [[ -d "$data/$name-ai-kit" ]] || continue
    if ! { mkdir -p "$backup" && cp -Rp "$data/$name-ai-kit" "$backup/"; }; then
      fail "cannot back up $data/$name-ai-kit to $backup; claude marketplace ai-kit not moved"
    fi
    printf 'refresh: claude: backed up %s to %s\n' "$data/$name-ai-kit" "$backup/$name-ai-kit"
    restore_hint="; then copy each file of $backup/<plugin>-ai-kit/ that is missing into $data/<plugin>-ai-kit/ (a .jsonl both hold: the backup's lines first)"
  done

  if ! output="$(claude plugin marketplace remove ai-kit --scope user --json 2>&1)"; then
    printf '%s\n' "$output" >&2
    fail "claude marketplace remove failed — run: claude plugin marketplace remove ai-kit --scope user && claude plugin marketplace add $KIT_REPOSITORY#$KIT_STABLE_BRANCH && $installs$restore_hint"
  fi
  printf 'refresh: claude: removed marketplace ai-kit (ref %s)\n' "$from"
  if ! output="$(claude plugin marketplace add "$KIT_REPOSITORY#$KIT_STABLE_BRANCH" --json 2>&1)"; then
    printf '%s\n' "$output" >&2
    fail "claude marketplace add failed — run: claude plugin marketplace add $KIT_REPOSITORY#$KIT_STABLE_BRANCH && $installs$restore_hint"
  fi
  printf 'refresh: claude: added marketplace ai-kit at %s\n' "$KIT_STABLE_BRANCH"
  for name in "${names[@]}"; do
    if ! output="$(claude plugin install "$name@ai-kit" --scope user --json 2>&1)"; then
      printf '%s\n' "$output" >&2
      fail "claude plugin install failed for $name — run: $installs$restore_hint"
    fi
    printf 'refresh: claude: installed %s@ai-kit\n' "$name"
  done
  for name in "${names[@]}"; do
    [[ -d "$backup/$name-ai-kit" ]] || continue
    counts="$(restore_plugin_data "$backup/$name-ai-kit" "$data/$name-ai-kit")" \
      || fail "cannot restore $data/$name-ai-kit from $backup/$name-ai-kit — copy each missing file back by hand (a .jsonl both hold: the backup's lines first)"
    printf 'refresh: claude: restored %s from %s: %s\n' "$data/$name-ai-kit" "$backup/$name-ai-kit" "$counts"
  done
  [[ "$(claude_kit_ref)" == "$KIT_STABLE_BRANCH" ]] \
    || fail "claude marketplace ai-kit was added at $KIT_STABLE_BRANCH but $(claude_plugins_root)/known_marketplaces.json reads ref '$(claude_kit_ref)'"
  printf 'refresh: claude marketplace ai-kit moved from %s to %s%s\n' "$from" "$KIT_STABLE_BRANCH" \
    "${restore_hint:+ (plugin data backup kept at $backup)}"
}

[[ -d "$KIT/.git" ]] || fail "$KIT is not a git clone — run platforms/tools/bootstrap.sh"

# #271: the user install follows the newest release tag, not main: the clone sits detached on it, and the Codex and
# Claude Code marketplaces and Devin's plugin follow the stable branch, which each release moves to its tag (KIT-081).
# KIT-046: the checkout replaces this script, but bash keeps running the copy it opened, so a run that checks out a new
# refresh.sh would finish with the old logic. Hand over once to the new script, which skips the fetch.
if [[ "${AI_KIT_REFRESH_PULLED:-0}" != "1" ]]; then
  run_step "git fetch origin failed" git -C "$KIT" fetch --tags origin
  status="$(git -C "$KIT" status --short)" || fail "cannot read git status"
  if [[ -n "$status" ]]; then
    printf 'FAIL: refresh: working tree is dirty; refusing to update\n%s\n' "$status" >&2
    exit 1
  fi
fi
tag="$(kit_release_tag "$KIT")"
[[ -n "$tag" ]] || fail "no vX.Y.Z release tag on origin/main; the user install follows the newest release"
before="$(git -C "$KIT" rev-parse HEAD)" || fail "cannot read HEAD"
# A run handed over by a refresh.sh from before #271 has pulled main; it moves to the release here.
if [[ "$before" != "$(git -C "$KIT" rev-parse "$tag^{commit}")" ]]; then
  run_step "cannot check out $tag" git -C "$KIT" checkout -q --detach "$tag"
fi
if [[ "${AI_KIT_REFRESH_PULLED:-0}" != "1" ]] && ! git -C "$KIT" diff --quiet "$before" HEAD -- \
    platforms/tools/refresh.sh platforms/tools/codex-bin.sh platforms/tools/kit-release.sh; then
  printf 'refresh: the release changed refresh.sh; running the new version\n'
  exec env AI_KIT_REFRESH_PULLED=1 bash "$KIT/platforms/tools/refresh.sh" "$@"
fi

codex="$(codex_bin || true)"
if [[ -n "$codex" ]]; then
  marketplaces="$("$codex" plugin marketplace list 2>/dev/null || true)"
  if [[ "$marketplaces" == *"ai-kit"* ]]; then
    codex_ref="$(codex_kit_ref)"
    if [[ "$codex_ref" == "$KIT_STABLE_BRANCH" ]]; then
      # KIT-081: the branch moves with each release, so an upgrade reaches the release
      run_step "codex marketplace upgrade failed" "$codex" plugin marketplace upgrade ai-kit
    else
      # Codex keeps a marketplace's source and ref together, so the move to the stable branch is a remove and an add,
      # once; the add of each kit plugin then replaces its cache with the branch's version.
      run_step "codex marketplace remove failed" "$codex" plugin marketplace remove ai-kit
      run_step "codex marketplace add failed — run: codex plugin marketplace add $KIT_REPOSITORY --ref $KIT_STABLE_BRANCH" \
        "$codex" plugin marketplace add "$KIT_REPOSITORY" --ref "$KIT_STABLE_BRANCH"
      for plugin_dir in "$KIT"/plugins/*/; do
        [[ -d "$plugin_dir/.devin-plugin" || -d "$plugin_dir/.claude-plugin" || -f "$plugin_dir/plugin.json" ]] || continue
        plugin_name="$(basename "$plugin_dir")"
        run_step "codex plugin add failed — run: codex plugin add $plugin_name@ai-kit" \
          "$codex" plugin add "$plugin_name@ai-kit"
      done
      printf 'refresh: codex marketplace ai-kit moved from %s to %s\n' "$codex_ref" "$KIT_STABLE_BRANCH"
    fi
  else
    warn "codex marketplace ai-kit not registered — run platforms/tools/bootstrap.sh"
  fi
else
  printf 'skip: refresh: no codex CLI found; Codex marketplace not upgraded\n'
fi

if command -v claude >/dev/null 2>&1; then
  claude_marketplaces="$(claude plugin marketplace list --json 2>/dev/null || true)"
  claude_ref=""
  json_contains "$claude_marketplaces" "ai-kit" && claude_ref="$(claude_kit_ref)"
  if [[ -n "$claude_ref" && "$claude_ref" != "$KIT_STABLE_BRANCH" ]]; then
    claude_move_to_stable "$claude_ref"
  elif [[ -n "$claude_ref" ]]; then
    # KIT-081: the branch moves with each release, so an update reaches the release
    run_step "claude marketplace update failed" claude plugin marketplace update ai-kit --json
    claude_plugins="$(claude plugin list --json 2>/dev/null || true)"
    for plugin_dir in "$KIT"/plugins/*/; do
      plugin_name="$(basename "$plugin_dir")"
      [[ -d "$plugin_dir/.claude-plugin" ]] || continue
      if json_contains "$claude_plugins" "$plugin_name@ai-kit"; then
        run_step "claude plugin update failed for $plugin_name" claude plugin update "$plugin_name@ai-kit" --json
      else
        # KIT-038: a plugin renamed in the marketplace's renames map is enabled but not cached until installed once
        run_step "claude plugin install failed for $plugin_name — run: claude plugin install $plugin_name@ai-kit" \
          claude plugin install "$plugin_name@ai-kit" --json
        printf 'refresh: installed Claude plugin %s@ai-kit\n' "$plugin_name"
      fi
    done
    claude_plugins="$(claude plugin list --json 2>/dev/null || true)"
    stale_plugins="$(claude_stale_plugins "$claude_marketplaces" "$claude_plugins")" \
      || fail "cannot compare Claude plugin caches with the kit"
    for plugin_name in $stale_plugins; do
      run_step "claude plugin uninstall failed for $plugin_name" \
        claude plugin uninstall "$plugin_name@ai-kit" --keep-data --json
      run_step "claude plugin install failed for $plugin_name — run: claude plugin install $plugin_name@ai-kit" \
        claude plugin install "$plugin_name@ai-kit" --json
      printf 'refresh: reinstalled Claude plugin %s@ai-kit (cache differed from the kit)\n' "$plugin_name"
    done
  else
    warn "claude marketplace ai-kit not registered — run platforms/tools/bootstrap.sh"
  fi
else
  # Under launchd PATH is the plist's, not the login shell's; print it so a missing entry shows (KIT-022)
  printf 'skip: refresh: claude CLI not found on PATH %s; Claude plugins not updated\n' "$PATH"
fi

# KIT-055: a pull that renames or removes a kit path leaves the doctor-managed links dangling; repair them once.
broken_link=""
while IFS= read -r -d '' link; do
  target="$(readlink "$link")"
  if [[ "$target" == "$KIT/"* && ! -e "$link" ]]; then
    broken_link="$link"
    break
  fi
done < <(find "$HOME/.claude" "$HOME/.codex" -maxdepth 2 -type l -print0 2>/dev/null)
if [[ -n "$broken_link" ]]; then
  printf 'refresh: kit link %s is broken; running doctor.sh\n' "$broken_link"
  "$KIT/platforms/tools/doctor.sh" || warn "doctor.sh reported failures — run platforms/tools/doctor.sh"
fi

# KIT-056: weekly cross-session audit pre-filter; prints counts only and never fails the refresh.
if [[ "${AI_KIT_SESSION_AUDIT:-1}" != "0" ]]; then
  python3 "$KIT/platforms/tools/session_audit.py" --if-older-days 7 \
    || warn "session_audit.py failed — run python3 $KIT/platforms/tools/session_audit.py"
fi

sha="$(git -C "$KIT" rev-parse --short HEAD)" || fail "cannot read HEAD"
date="$(git -C "$KIT" show -s --format=%cs HEAD)" || fail "cannot read commit date"
printf 'refresh: %s %s %s\n' "$sha" "$date" "$tag"
