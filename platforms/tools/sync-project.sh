#!/usr/bin/env bash
# Syncs the agent configuration with a project and connects its CI to the kit's spec tools (KIT-081: no copy).
# Usage: sync-project.sh [--profile <profile>[,<profile>...]] [--workflow <file>] <repo-dir>
#                                                          writes .github/workflows/spec-lint.yml (repos with docs/spec
#                                                          whose CI runs no spec tools), removes a generated
#                                                          .github/spec-lint/ (KIT-081 stage 1),
#                                                          CLAUDE.md (imports AGENTS.md; its marker records the
#                                                          profile list),
#                                                          .claude/settings.json (ai-kit marketplace at
#                                                          ref stable (KIT-081) +
#                                                          enabledPlugins guardrails@ai-kit +
#                                                          includeGitInstructions false) and
#                                                          .claude/rules/guardrails-<rule>.md (the profile's
#                                                          path rules, marked as generated)
#        sync-project.sh --check [--profile <profile>[,<profile>...]] [--workflow <file>] <repo-dir>
#                                                          compares all of them with the kit and scans the
#                                                          repo's *.md for obsolete kit paths and
#                                                          citations of skills KIT-070 removed;
#                                                          exit 1 on any divergence or stale citation
# --profile selects the kit rules copied into .claude/rules/: platforms/tools/sync-profiles.txt names the profiles that
# receive each one (KIT-047). Without it the list the generated CLAUDE.md marker records is used, then (a repository
# synced in the vendored mode before KIT-081 stage 2b) the list .claude/skills/KIT_MANIFEST.json records; a repo with
# neither gets the profile inferred, first match wins: project.godot (godot), pom.xml (java), docs/spec/ (docs). The
# run prints which source won.
# <profile> is godot|java|docs|python, optionally followed by :<dir>. A comma list syncs the union
# of its profiles' rules, for a monorepo such as
# docs,godot:client,java:server,python:platform. The :<dir> suffix scopes the globs/paths of the rule named
# after that profile to <dir>/ ("**/*.gd" renders as "client/**/*.gd"; java:server leaves the
# godot rule alone), and any other rule to the folders of every profile that receives the rule.
# The list is stored sorted and deduplicated, which is the form the CLAUDE.md marker records.
# A .claude/rules/*.md destination that exists without the generated marker refuses
# the sync before any write; a marked file that falls out of the profile is removed.
# The project uses the installed guardrails@ai-kit plugin, which follows the kit's stable branch (KIT-081): the
# settings enable only that plugin (the kit ships one, KIT-047). The vendored mode (--vendor-skills, KIT-072) is gone:
# the flag exits 2, and a repository that still holds its state (KIT_MANIFEST.json, the .claude/skills/ copies and
# guardrails-pinned/ marked .agent-rules-kit, .claude/ai-kit/, the pinned hooks and key in .claude/settings.json) is
# migrated by platforms/tools/sync_unvendor.py: install removes only the kit-marked folders and the kit's settings
# entries, after the plugin is on and CLAUDE.md records the profile list, and --check reports each leftover. An
# unmarked folder or a symbolic link is never read, replaced or deleted.
# docs/spec/spec.md may set sdd.rule_paths, kit rule name -> folders (KIT-067): it scopes that rule's globs
# like :<dir> does and wins over the profile folders; "." keeps the whole repository. A key that names no kit
# rule, or an sdd block check_spec.py refuses, stops both modes before any write (exit 2).
# Each rendered rule's body also goes into a generated block in the AGENTS.md of each folder its globs start in
# (platforms/tools/sync_agents_md.py), for runtimes that load no rule by path. A rule named after a profile
# (godot, java, python) gets that block only when $PROFILE has that profile or sdd.rule_paths lists it. A folder
# that does not exist gets no block; --check reports a missing, diverging or stale block.
# Each profile folder gets a generated kit.just from platforms/kits/just/<profile>.just (platforms/tools/sync_just.py,
# KIT-074): the folder's own justfile imports it (a folder without one gets a starter justfile), a folder with several
# profiles gets kit-<profile>.just modules and a kit.just that runs the shared recipes of each; --check reports a
# missing, diverging or stale module and a justfile that does not import kit.just. A godot profile also vendors the
# keyed-CSV merge driver into .github/merge-drivers/ and prints its one-time git config step (never run here).
# The spec tools run from the kit (KIT-081 stage 1, platforms/tools/sync_spec_tools.py): sessions call the installed
# kit's validators, and the project's CI the composite action platforms/ci/actions/spec-tools pinned by commit SHA.
# Install removes the .github/spec-lint/ copy an older sync generated (its README marker, kit-named files only; any
# other file stays) and, in a repo with docs/spec whose CI runs no spec tools, writes spec-lint.yml from the kit
# template with the action pinned to this kit's commit. --check fails on a generated copy left, on a workflow line
# naming .github/spec-lint/, and with docs/spec on no workflow running the spec tools (the action, or check_spec.py
# from $AI_KIT_DIR). --workflow names the CI file that must run them; install writes the template under that name
# when it is missing.
# Both modes print "sync: warning: ..." on stderr when <repo-dir> resolves into a cloud-synced
# folder (the plugin's SessionStart hook decides; KIT-021); the exit code does not change.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# The kit's one plugin (KIT-047), named guardrails since KIT-055.
KIT_PLUGIN="guardrails"
# KIT-081 stage 2b: removes or reports the state the retired vendored mode (KIT-072) left in a repository.
UNVENDOR_TOOL="$KIT_DIR/platforms/tools/sync_unvendor.py"
# KIT-081 stage 1: the spec tools run from the kit; removes the old copy, writes or checks the CI workflow.
SPEC_TOOLS="$KIT_DIR/platforms/tools/sync_spec_tools.py"

MODE="install"
PROFILE=""
WORKFLOW=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check" ;;
    --profile) PROFILE="${2:?usage: sync-project.sh [--check] [--profile <profile>[,<profile>...]] [--workflow <file>] <repo-dir>}"; shift ;;
    --workflow) WORKFLOW="${2:?usage: sync-project.sh [--check] [--profile <profile>[,<profile>...]] [--workflow <file>] <repo-dir>}"; shift ;;
    --vendor-skills)
      echo "sync: --vendor-skills was removed in KIT-081 stage 2b: a project uses the installed guardrails@ai-kit plugin; run sync-project.sh <repo-dir> without it, which also migrates a vendored repository" >&2
      exit 2 ;;
    --) shift; break ;;
    *) break ;;
  esac
  shift
done
REPO="${1:?usage: sync-project.sh [--check] [--profile <profile>[,<profile>...]] [--workflow <file>] <repo-dir>}"
CLAUDE_MARKER="generated by agent-rules-kit sync-project.sh"
RULE_PATHS=""  # "<rule> <dir>..." lines from docs/spec/spec.md sdd.rule_paths (KIT-067)
MERGE_DRIVER_SRC="$KIT_DIR/platforms/kits/godot/scripts/keyed_csv_merge.py"
MERGE_DRIVER_REL=".github/merge-drivers/keyed_csv_merge.py"  # vendored for a godot profile (KIT-074)
MERGE_DRIVER_HEADER='"""Keyed-CSV git merge driver (agent-rules-kit KIT-074)' # how line 2 of a vendored copy starts
SYNC_TMP="$(mktemp -d)"
trap 'find "$SYNC_TMP" -delete' EXIT
RULE_MARKER_PREFIX='<!-- agent-rules-kit: generated from '
# The line under the marker of each .claude/rules copy: Claude Code has no other path to a kit reference a rule names
# (sdd-implement and sdd-plan are user-only skills). sync_agents_md.py drops it from the AGENTS.md block, whose intro
# says the same once per folder.
# shellcheck disable=SC2016  # literal Markdown backticks
RULE_LOCATION='Kit files this rule names: skill `<skill>`, reference `<file>` is `~/.ai-kit/plugins/guardrails/skills/<skill>/references/<file>`.'
version="$(cat "$KIT_DIR/VERSION")"

if [[ -n "$WORKFLOW" && ( "$WORKFLOW" == */* || "$WORKFLOW" == .* ) ]]; then
  echo "sync: --workflow must be a plain file name under .github/workflows/" >&2
  exit 2
fi

merge_driver_wanted() { # a godot profile gets the keyed-CSV merge driver (KIT-074)
  profile_entries "$PROFILE" | cut -d' ' -f1 | grep -qx godot
}

merge_driver_marked() { # the vendored driver's docstring line names the kit; any other file is the project's, even
  # one that mentions the kit elsewhere (KIT-079)
  [[ -f "$REPO/$MERGE_DRIVER_REL" ]] &&
    [[ "$(sed -n 2p "$REPO/$MERGE_DRIVER_REL")" == "$MERGE_DRIVER_HEADER"* ]]
}

rule_files() { # prints "src rel-dest" for every kit rule the map gives to a profile in $PROFILE
  local name
  while read -r name; do
    echo "$KIT_DIR/plugins/$KIT_PLUGIN/rules/$name .claude/rules/$KIT_PLUGIN-$name"
  done < <(map_selected rules)
}

render_rule() { # $1 = kit rule file, $2 = output path: frontmatter (first --- through the
  # closing ---) copied byte-for-byte, then the generated marker and the RULE_LOCATION line, then the body unchanged;
  # when rule_scopes names folders, each globs/paths item "<glob>" becomes one
  # "<dir>/<glob>" item per folder
  local src="$1" out="$2" line glob dir scopes
  local separators=0 in_list=0
  scopes="$(rule_scopes "$PROFILE" "$src")"
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$separators" -eq 1 && "$scopes" != . ]]; then
      case "$line" in
        globs:|paths:) in_list=1 ;;
        " "*) ;;
        *) in_list=0 ;;
      esac
      if [[ "$in_list" == 1 && "$line" == '  - "'*'"' ]]; then
        glob="${line#  - \"}"
        glob="${glob%\"}"
        for dir in $scopes; do printf '  - "%s/%s"\n' "$dir" "$glob"; done
        continue
      fi
    fi
    printf '%s\n' "$line"
    if [[ "$line" == "---" ]]; then
      separators=$((separators + 1))
      if [[ "$separators" -eq 2 ]]; then
        printf '%s\n' "<!-- agent-rules-kit: generated from ${src#"$KIT_DIR"/} by platforms/tools/sync-project.sh; kit $(cat "$KIT_DIR/VERSION"); do not edit -->"
        printf '%s\n' "$RULE_LOCATION"
      fi
    fi
  done < "$src" > "$out"
}

infer_profile() { # $1 = repo dir
  if [[ -f "$1/project.godot" ]]; then echo godot
  elif [[ -f "$1/pom.xml" ]]; then echo java
  elif [[ -d "$1/docs/spec" ]]; then echo docs
  else echo "sync: cannot infer profile for $1 (no project.godot, pom.xml or docs/spec); pass --profile godot|java|docs|python" >&2; return 1
  fi
}

claude_profile() { # $1 = CLAUDE.md; prints the profile list its generated marker records (KIT-081 stage 2b), or
  # nothing when the file is missing, hand-written or from a sync before the marker carried one
  [[ -f "$1" ]] || return 0
  sed -n '1s/^<!-- generated by agent-rules-kit sync-project\.sh v[^;]*; profile \([^; ]*\); AGENTS\.md is the source -->$/\1/p' "$1"
}

manifest_profile() { # prints the profile list the KIT_MANIFEST.json of a repository synced in the vendored mode before
  # KIT-081 stage 2b records, or nothing when the file is missing, unreadable, records none or is reached through a
  # symbolic link (sync_unvendor.py never reads through one either)
  local manifest="$REPO/.claude/skills/KIT_MANIFEST.json"
  [[ -f "$manifest" && ! -L "$REPO/.claude" && ! -L "$REPO/.claude/skills" && ! -L "$manifest" ]] || return 0
  python3 - "$manifest" <<'PY'
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        profile = json.load(handle).get("profile")
except (OSError, ValueError, AttributeError):
    profile = None
print(profile if isinstance(profile, str) else "")
PY
}

normalize_profile() { # $1 = --profile value; prints its entries sorted, deduplicated and
  # comma-joined, or fails on an unknown profile or a folder that leaves the repo
  local entry name dir
  local dir_re='^[A-Za-z0-9._-]+(/[A-Za-z0-9._-]+)*$'
  printf '%s\n' "$1" | tr ',' '\n' | while IFS= read -r entry; do
    name="${entry%%:*}"
    case "$name" in
      godot|java|docs|python) ;;
      *) echo "sync: unknown profile '$name' (expected godot|java|docs|python, optionally :<dir>, comma-separated)" >&2; exit 1 ;;
    esac
    if [[ "$entry" == *:* ]]; then
      dir="${entry#*:}"
      dir="${dir%/}"
      if [[ ! "$dir" =~ $dir_re || "/$dir/" == */../* || "/$dir/" == */./* ]]; then
        echo "sync: profile folder '${entry#*:}' must be a relative path inside the repo" >&2
        exit 1
      fi
      echo "$name:$dir"
    else
      echo "$name"
    fi
  done | LC_ALL=C sort -u | paste -s -d , -
}

profile_entries() { # $1 = normalized profile list; prints "<name> <dir>" per entry, dir . for the root
  local entry
  printf '%s\n' "$1" | tr ',' '\n' | while IFS= read -r entry; do
    if [[ "$entry" == *:* ]]; then echo "${entry%%:*} ${entry#*:}"; else echo "$entry ."; fi
  done
}

PROFILE_MAP="$KIT_DIR/platforms/tools/sync-profiles.txt"

map_entries() { # $1 = skills|rules; prints "<name> <profile>..." per map line of that kind, where the
  # single profile "-" means no profile receives it (check_kit.py keeps the map complete)
  awk -F'|' -v kind="$1/" '
    /^[[:space:]]*(#|$)/ { next }
    {
      key = $1; profiles = $2
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", key)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", profiles)
      if (index(key, kind) == 1) print substr(key, length(kind) + 1), profiles
    }' "$PROFILE_MAP"
}

map_selected() { # $1 = skills|rules; prints each name of that kind whose map profiles include a
  # profile of $PROFILE, in map order
  local name profiles profile names
  names=" $(profile_entries "$PROFILE" | cut -d' ' -f1 | tr '\n' ' ')"
  while read -r name profiles; do
    for profile in $profiles; do
      case "$names" in *" $profile "*) echo "$name"; break ;; esac
    done
  done < <(map_entries "$1")
}

rule_scopes() { # $1 = normalized profile list, $2 = kit rule file; a rule named after a profile
  # (rules/godot.md and profile godot) takes only that profile's folders, so java:server never
  # scopes the godot rule; any other rule takes the folders of every entry whose profile receives
  # it in the map, or . when one of them covers the repo root
  local file="${2##*/}" stack name dir scopes="" receivers paths
  stack="${file%.md}"
  # sdd.rule_paths names this rule's folders (KIT-067) and wins over the profiles; "." is the whole repository
  paths="$(printf '%s\n' "$RULE_PATHS" | awk -v stack="$stack" '$1 == stack { $1 = ""; print substr($0, 2); exit }')"
  if [[ -n "$paths" ]]; then
    case " $paths " in *" . "*) echo .; return 0 ;; esac
    echo "$paths"
    return 0
  fi
  while read -r name dir; do
    [[ "$name" == "$stack" ]] || continue
    if [[ "$dir" == . ]]; then echo .; return 0; fi
    case " $scopes " in *" $dir "*) ;; *) scopes="$scopes${scopes:+ }$dir" ;; esac
  done < <(profile_entries "$1")
  if [[ -n "$scopes" ]]; then echo "$scopes"; return 0; fi
  receivers=" $(map_entries rules | awk -v file="$file" '$1 == file { $1 = ""; print }') "
  while read -r name dir; do
    case "$receivers" in *" $name "*) ;; *) continue ;; esac
    if [[ "$dir" == . ]]; then echo .; return 0; fi
    case " $scopes " in *" $dir "*) ;; *) scopes="$scopes${scopes:+ }$dir" ;; esac
  done < <(profile_entries "$1")
  echo "${scopes:-.}"
}

agents_block_wanted() { # $1 = kit rule file; a rule named after a profile goes into an AGENTS.md block only
  # when $PROFILE has that profile or sdd.rule_paths lists the rule: the map sends the godot, java and python rules
  # to every code profile, which a path rule loads only on a match but an AGENTS.md block would load every session
  local stack="${1##*/}"
  stack="${stack%.md}"
  case "$stack" in godot|java|python) ;; *) return 0 ;; esac
  profile_entries "$PROFILE" | cut -d' ' -f1 | grep -qx "$stack" && return 0
  printf '%s\n' "$RULE_PATHS" | awk -v stack="$stack" '$1 == stack { found = 1 } END { exit !found }'
}

render_agents_rules() { # renders every rule an AGENTS.md block carries into a fresh folder under $SYNC_TMP
  # and prints that folder
  local src rel dir
  dir="$(mktemp -d "$SYNC_TMP/agents.XXXXXX")"
  while read -r src rel; do
    agents_block_wanted "$src" || continue
    render_rule "$src" "$dir/${rel##*/}"
  done < <(rule_files)
  echo "$dir"
}

# Obsolete kit paths (layouts 1.x to 11.x). A consumer line that must keep one
# (historical citation) appends the marker "<!-- kit-path-ok -->".
# .claude/ is skipped: generated kit copies there are verified by their own
# manifest and repo-owned content under .claude/ is not a kit citation. legacy/, docs/sessions/ and every
# CHANGELOG.md are history: an old entry names the paths and skills that were current then (#299).
STALE_KIT_PATHS='agents/skills/|agents/rules/|agents/knowledge/|rules/godot/|rules/java/|rules/git/|kits/java-maven/|kits/github/|platforms/install/|knowledge/|processes/sdd/|plugins/ai-kit/|plugins/core/|plugins/sdd/|plugins/dev/|plugins/architect-|plugins/all/|plugins/dev-|plugins/extras/|plugins/infra-|plugins/process-loop/|plugins/quality-'
STALE_OPT_OUT='<!-- kit-path-ok -->'

scan_stale_kit_paths() { # $1 = repo dir; prints one line per stale citation; returns 1 if any
  local hits
  hits="$(grep -rnE --include='*.md' --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.claude \
      "(^|[^/A-Za-z0-9_.-])($STALE_KIT_PATHS)" "$1" 2>/dev/null \
    | sed "s|^${1%/}/||" \
    | grep -vE '^([^:]*/)?((legacy|docs/sessions)/|CHANGELOG\.md:)' \
    | grep -vF -- "$STALE_OPT_OUT" || true)"
  [[ -n "$hits" ]] || return 0
  printf '%s\n' "$hits" | sed 's|^|sync: stale kit path: |'
  echo "sync: the 10.x layout is frozen (docs/design.md, Layout stability); fix the citation or append $STALE_OPT_OUT"
  return 1
}

# Kit skills removed by KIT-070 (the standards moved into rules and the sdd-plan and sdd-implement references).
# A consumer citation of one dangles after a resync. Every form is caught, backticks optional: skill x, x skill,
# x § n, guardrails:x, a skills/x/ or x/references/ path, the /x command; a hyphenated name (code-standards,
# protocol-contract, ...) anywhere as a whole word. A plain word (testing, architecture, persistence, grilling)
# counts only in one of those forms, so "our testing strategy" stays clean. Same exclusions and opt-out marker as
# the stale path scan.
REMOVED_KIT_SKILLS='architecture|code-standards|godot-standards|java-standards|testing|persistence|protocol-contract|asset-import|grilling'

removed_kit_skill_hits() { # $1 = repo dir; prints "path:line:text" for each citation of a removed kit skill
  # (outside "$(...)": bash 3.2 misparses a heredoc with quotes or backticks inside a command substitution, KIT-060)
  python3 - "$1" "$REMOVED_KIT_SKILLS" "$STALE_OPT_OUT" <<'PY'
import os
import re
import sys

root, names, opt_out = sys.argv[1], sys.argv[2].split("|"), sys.argv[3]
sys.stdout.reconfigure(errors="backslashreplace")  # a non-UTF-8 locale or file name never stops the scan
hyphenated = [name for name in names if "-" in name]
any_name = "|".join(map(re.escape, names))
tick = "`?"
forms = [
    rf"(?i:\bskills?)\s+{tick}(?:{any_name}){tick}(?![\w-])",            # skill x, skills `x`
    rf"(?<![\w-]){tick}(?:{any_name}){tick}\s+skill\b",                    # x skill, `x` skill
    rf"(?<![\w-]){tick}(?:{any_name}){tick}\s*§\s*\d",                     # x § 6, `x` § 6
    rf"\bguardrails:(?:{any_name})(?![\w-])",                              # guardrails:x
    rf"(?<![\w.-])(?:[\w.-]+/)*skills/(?:{any_name})/",                    # .../skills/x/...
    rf"(?<![\w.-])(?:{any_name})/(?:references/|SKILL\.md)",               # x/references/..., x/SKILL.md
    rf"(?<![\w./-])/(?:{any_name})(?![\w/-])",                             # the /x command
    rf"(?<![\w-])(?:{'|'.join(map(re.escape, hyphenated))})(?![\w-]|\.[A-Za-z])",  # a hyphenated name anywhere
]
pattern = re.compile("|".join(f"(?:{form})" for form in forms))
skip_dirs = {".git", "node_modules", ".claude"}
excluded = re.compile(r"^([^/]*/)*((legacy|docs/sessions)/|CHANGELOG\.md$)")
for top, dirs, files in os.walk(root):
    dirs[:] = sorted(d for d in dirs if d not in skip_dirs)
    for name in sorted(files):
        if not name.endswith(".md"):
            continue
        path = os.path.join(top, name)
        relative = os.path.relpath(path, root)
        if excluded.match(relative):
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                for number, line in enumerate(handle, 1):
                    if pattern.search(line) and opt_out not in line:
                        print(f"{relative}:{number}:{line.rstrip()}")
        except OSError:
            continue
PY
}

scan_removed_kit_skills() { # $1 = repo dir; prints one line per citation of a removed kit skill; returns 1 if any
  local hits
  hits="$(removed_kit_skill_hits "$1")" || { echo "sync: removed-skill scan failed"; return 1; }
  [[ -n "$hits" ]] || return 0
  printf '%s\n' "$hits" | sed 's|^|sync: removed kit skill: |'
  echo "sync: KIT-070 moved these skills into path rules and the sdd-plan and sdd-implement references (kit CHANGELOG, migration note); fix the citation or append $STALE_OPT_OUT"
  return 1
}

warn_synced_folder() { # $1 = repo dir; reruns the plugin's SessionStart hook for it and prints its warning
  python3 - "$KIT_DIR/plugins/guardrails/hooks/hooks.json" "$1" <<'PY' || true
import json, subprocess, sys
for group in json.load(open(sys.argv[1]))["hooks"].get("SessionStart", []):
    for hook in group.get("hooks", []):
        try:
            result = subprocess.run(["bash", "-c", hook["command"]], input=json.dumps({"cwd": sys.argv[2]}),
                                    stdout=subprocess.PIPE, universal_newlines=True, timeout=hook.get("timeout", 10))
            message = json.loads(result.stdout).get("systemMessage")
        except (subprocess.TimeoutExpired, ValueError):
            message = None  # best effort, like the hook itself: a slow or silent detector prints nothing
        if message:
            print("sync: warning: " + message, file=sys.stderr)
PY
}

# One detector for both callers: the warning comes from the same hook command that
# Claude Code and Devin run at session start (KIT-021).
warn_synced_folder "$REPO"

# The repo profile selects the rules; check and install both need it. The list is sticky: without --profile, the list
# the CLAUDE.md marker records wins, then (migration from the vendored mode, KIT-081 stage 2b) the one
# KIT_MANIFEST.json records, then inference, so a bare run keeps a monorepo's union (KIT-017).
if [[ -n "$PROFILE" ]]; then
  profile_source="--profile"
elif PROFILE="$(claude_profile "$REPO/CLAUDE.md")" && [[ -n "$PROFILE" ]]; then
  profile_source="CLAUDE.md"
elif PROFILE="$(manifest_profile)" && [[ -n "$PROFILE" ]]; then
  profile_source="manifest"
else
  PROFILE="$(infer_profile "$REPO")"
  profile_source="inferred"
fi
PROFILE="$(normalize_profile "$PROFILE")" || {
  case "$profile_source" in
    CLAUDE.md) echo "sync: CLAUDE.md records that profile; pass --profile to replace it" >&2 ;;
    manifest) echo "sync: .claude/skills/KIT_MANIFEST.json records that profile; pass --profile to replace it" >&2 ;;
  esac
  exit 2
}
echo "sync: profile=$PROFILE ($profile_source)"

# The project's sdd parameters (KIT-067): check_spec.py resolves and checks the block, so an invalid one refuses
# both modes before any write. CI is cleared for that call: without pyyaml it parses the block structurally.
if [[ -f "$REPO/docs/spec/spec.md" ]]; then
  if ! CI='' python3 "$KIT_DIR/platforms/ci/validations/check_spec.py" --params "$REPO/docs/spec" \
      "$KIT_DIR/platforms/ci/schemas" >"$SYNC_TMP/params.json" 2>"$SYNC_TMP/params.err"; then
    grep -v '^WARN: ' "$SYNC_TMP/params.err" >&2 || true
    echo "sync: fix the sdd block in $REPO/docs/spec/spec.md (skill sdd-constitution, references/sdd-parameters.md), then rerun" >&2
    exit 2
  fi
  python3 - "$SYNC_TMP/params.json" "$KIT_DIR/plugins/$KIT_PLUGIN/rules" >"$SYNC_TMP/rule-paths" <<'PY' || exit 2
import json, os, sys
params = json.load(open(sys.argv[1], encoding="utf-8"))
kit_rules = sorted(name[:-3] for name in os.listdir(sys.argv[2]) if name.endswith(".md"))
bad = False
for rule, dirs in sorted(params.get("rule_paths", {}).items()):
    if rule not in kit_rules:
        print(f"sync: docs/spec/spec.md sdd.rule_paths names rule {rule!r}, which the kit does not ship"
              f" ({', '.join(kit_rules)})", file=sys.stderr)
        bad = True
    print(rule, *dirs)
sys.exit(1 if bad else 0)
PY
  RULE_PATHS="$(cat "$SYNC_TMP/rule-paths")"
  # An entry for a rule the profile does not receive changes nothing; say so instead of passing in silence.
  received=" $(map_selected rules | tr '\n' ' ')"
  while read -r rule _; do
    [[ -n "$rule" ]] || continue
    case "$received" in
      *" $rule.md "*) ;;
      *) echo "sync: warning: sdd.rule_paths.$rule does nothing: profile $PROFILE receives no rules/$rule.md" >&2 ;;
    esac
  done <<< "$RULE_PATHS"
fi

# The kit ships one plugin (KIT-047); the project enables it (KIT-081 stage 2b: no vendored mode).
SETTINGS_PLUGINS="$KIT_PLUGIN"

if [[ "$MODE" == check ]]; then
  FAILED=0
  expected="$(cat "$KIT_DIR/VERSION")"
  # KIT-081 stage 1: no generated .github/spec-lint/ and no workflow line naming it; a repo with docs/spec also needs a
  # workflow that runs the spec tools. Elsewhere the CLAUDE.md/settings/rules checks below decide the verdict.
  spec_args=()
  [[ -d "$REPO/docs/spec" ]] && spec_args+=(--spec)
  [[ -n "$WORKFLOW" ]] && spec_args+=(--workflow "$WORKFLOW")
  python3 "$SPEC_TOOLS" check "$REPO" ${spec_args[@]+"${spec_args[@]}"} || FAILED=1
  python3 "$KIT_DIR/platforms/tools/sync_just.py" check "$REPO" "$expected" "$PROFILE" || FAILED=1
  if merge_driver_wanted; then
    if [[ ! -f "$REPO/$MERGE_DRIVER_REL" ]]; then
      echo "sync: $MERGE_DRIVER_REL missing"; FAILED=1
    elif ! cmp -s "$MERGE_DRIVER_SRC" "$REPO/$MERGE_DRIVER_REL"; then
      echo "sync: $MERGE_DRIVER_REL diverges from the kit"; FAILED=1
    fi
  elif merge_driver_marked; then
    echo "sync: $MERGE_DRIVER_REL is generated but not in profile"; FAILED=1
  fi
  scan_stale_kit_paths "$REPO" || FAILED=1
  scan_removed_kit_skills "$REPO" || FAILED=1
  claude_file="$REPO/CLAUDE.md"
  recorded="$(claude_profile "$claude_file")"
  if [[ -n "$recorded" && "$recorded" != "$PROFILE" ]]; then
    echo "sync: CLAUDE.md records profile '$recorded' expected '$PROFILE' (pass --profile or rerun sync-project.sh)"
    FAILED=1
  elif [[ ! -f "$claude_file" ]] \
      || ! grep -qF "$CLAUDE_MARKER v$expected; profile $PROFILE;" "$claude_file" \
      || [[ "$(grep -v '^<!--' "$claude_file" || true)" != "@AGENTS.md" ]]; then
    echo "sync: CLAUDE.md missing or diverges (rerun sync-project.sh)"
    FAILED=1
  fi
  AI_KIT_PLUGINS="$SETTINGS_PLUGINS" python3 - "$REPO/.claude/settings.json" "$PROFILE" <<'PY' || FAILED=1
import json, os, sys
path, profile = sys.argv[1], sys.argv[2]
want = {name + "@ai-kit" for name in os.environ.get("AI_KIT_PLUGINS", "").split()}
# KIT-081: the user's marketplace follows the stable branch; a project source without that ref conflicts with it
market = {"source": {"source": "github", "repo": "ChristianPrzybulinski/agent-rules-kit", "ref": "stable"}}
try:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
except (OSError, ValueError):
    data = None
if not isinstance(data, dict):
    data = None
parts = []
if data is None:
    parts.append("missing" + (": " + ",".join(sorted(want)) if want else ""))
else:
    markets = data.get("extraKnownMarketplaces")
    if not isinstance(markets, dict) or markets.get("ai-kit") != market:
        parts.append("marketplace: ai-kit")
    enabled = data.get("enabledPlugins")
    if not isinstance(enabled, dict):
        enabled = {}
    have = {key for key in enabled if isinstance(key, str) and key.endswith("@ai-kit")}
    missing = sorted((want - have) | {key for key in have & want if enabled[key] is not True})
    extra = sorted(have - want)
    if missing:
        parts.append("missing: " + ",".join(missing))
    if extra:
        parts.append("extra: " + ",".join(extra))
    if data.get("includeGitInstructions") is not False:
        parts.append("includeGitInstructions: want false")
if parts:
    print(f"sync: .claude/settings.json diverges for profile {profile} ({'; '.join(parts)})")
    sys.exit(1)
PY
  rule_tmp="$(mktemp)"
  rule_names=""
  while read -r src rel; do
    rule_names="$rule_names${rel##*/} "
    dst="$REPO/$rel"
    render_rule "$src" "$rule_tmp"
    if [[ ! -f "$dst" ]]; then
      echo "sync: $rel missing"
      FAILED=1
    elif ! cmp -s "$rule_tmp" "$dst"; then
      echo "sync: $rel diverges from the kit"
      FAILED=1
    fi
  done < <(rule_files)
  rm -f "$rule_tmp"
  for dst in "$REPO/.claude/rules/"*.md; do
    [[ -f "$dst" ]] || continue
    grep -qF "$RULE_MARKER_PREFIX" "$dst" || continue
    case " $rule_names" in
      *" ${dst##*/} "*) ;;
      *)
        echo "sync: .claude/rules/${dst##*/} is generated but not in profile"
        FAILED=1
        ;;
    esac
  done
  # KIT-081 stage 2b: the state the retired vendored mode left (copies, the pin, its settings entries) fails the check
  python3 "$UNVENDOR_TOOL" check "$REPO" || FAILED=1
  python3 "$KIT_DIR/platforms/tools/sync_agents_md.py" check "$REPO" "$expected" "$(render_agents_rules)" || FAILED=1
  if [[ $FAILED -eq 0 ]]; then echo "sync: $REPO consistent with kit $expected"; else exit 1; fi
  exit 0
fi

# Every refusal runs before the first write, so a rejected repo is left untouched.
if [[ -f "$REPO/CLAUDE.md" ]] && ! grep -qF "$CLAUDE_MARKER" "$REPO/CLAUDE.md"; then
  echo "sync: $REPO/CLAUDE.md exists and is not generated; move its content into AGENTS.md and delete it, then rerun"
  exit 1
fi
if [[ ! -f "$REPO/AGENTS.md" ]]; then
  echo "sync: $REPO/AGENTS.md missing; the generated CLAUDE.md imports it"
  exit 1
fi
if [[ -f "$REPO/.claude/settings.json" ]]; then
  python3 -c 'import json,sys; json.load(open(sys.argv[1], encoding="utf-8"))' "$REPO/.claude/settings.json" 2>/dev/null \
    || { echo "sync: $REPO/.claude/settings.json is not valid JSON; fix it by hand"; exit 1; }
fi
# A .claude/rules destination that exists without the generated marker is repo-owned;
# refuse before the first write instead of overwriting it.
while read -r src rel; do
  dst="$REPO/$rel"
  if [[ -e "$dst" ]] && ! grep -qF "$RULE_MARKER_PREFIX" "$dst"; then
    echo "sync: $dst exists and is not generated; move it by hand"
    exit 1
  fi
done < <(rule_files)
# A target AGENTS.md that is a symbolic link, or one whose path-rule block markers are broken, refuses here too.
AGENTS_RULES="$(render_agents_rules)"
python3 "$KIT_DIR/platforms/tools/sync_agents_md.py" preflight "$REPO" "$version" "$AGENTS_RULES" || exit 1
# A kit.just or kit-<profile>.just path holding the project's own file, or a profile folder reached through a symbolic
# link, refuses here (KIT-074); so does a hand-written file at the merge driver's path.
python3 "$KIT_DIR/platforms/tools/sync_just.py" preflight "$REPO" "$version" "$PROFILE" || exit 1
if merge_driver_wanted; then
  if [[ -L "$REPO/.github" || -L "$REPO/.github/merge-drivers" || -L "$REPO/$MERGE_DRIVER_REL" ]]; then
    echo "sync: $REPO/$MERGE_DRIVER_REL goes through a symbolic link; move it by hand"
    exit 1
  fi
  if [[ -e "$REPO/$MERGE_DRIVER_REL" ]] && ! merge_driver_marked; then
    echo "sync: $REPO/$MERGE_DRIVER_REL exists and is not generated; move it by hand"
    exit 1
  fi
fi

mkdir -p "$REPO/.claude"
# Plugin names arrive through AI_KIT_PLUGINS: the heredoc occupies stdin.
AI_KIT_PLUGINS="$SETTINGS_PLUGINS" python3 - "$REPO/.claude/settings.json" <<'PY'
import json, os, sys
from collections import OrderedDict
path = sys.argv[1]
plugins = os.environ.get("AI_KIT_PLUGINS", "").split()
try:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh, object_pairs_hook=OrderedDict)
except FileNotFoundError:
    data = OrderedDict()
except json.JSONDecodeError:
    print(f"sync: {path} is not valid JSON; fix it by hand"); sys.exit(1)
markets = data.setdefault("extraKnownMarketplaces", OrderedDict())
# KIT-081: the user's marketplace follows the stable branch; a project source without that ref conflicts with it
markets["ai-kit"] = OrderedDict(source=OrderedDict(source="github", repo="ChristianPrzybulinski/agent-rules-kit",
                                                   ref="stable"))
enabled = data.setdefault("enabledPlugins", OrderedDict())
for key in [k for k in enabled if k.endswith("@ai-kit")]:
    del enabled[key]
for name in plugins:
    enabled[name + "@ai-kit"] = True
# KIT-071: Claude Code's built-in commit and PR instructions compete with skill git.
data["includeGitInstructions"] = False
text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
try:
    current = open(path, encoding="utf-8").read()
except FileNotFoundError:
    current = None
if current != text:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
PY

# The profile's path rules render into .claude/rules/<plugin>-<rule>.md; only
# marker-carrying files the profile no longer receives are removed (dev-*.md and
# sdd-*.md from kits before KIT-047, core-*.md before KIT-055, among them).
mkdir -p "$REPO/.claude/rules"
rules_written=0
rules_removed=0
rule_names=""
rule_tmp="$(mktemp)"
while read -r src rel; do
  dst="$REPO/$rel"
  rule_names="$rule_names${rel##*/} "
  render_rule "$src" "$rule_tmp"
  if [[ ! -f "$dst" ]] || ! cmp -s "$rule_tmp" "$dst"; then
    cat "$rule_tmp" > "$dst"
    rules_written=$((rules_written + 1))
  fi
done < <(rule_files)
rm -f "$rule_tmp"
for dst in "$REPO/.claude/rules/"*.md; do
  [[ -f "$dst" ]] || continue
  grep -qF "$RULE_MARKER_PREFIX" "$dst" || continue
  case " $rule_names" in
    *" ${dst##*/} "*) ;;
    *)
      rm -f "$dst"
      rules_removed=$((rules_removed + 1))
      ;;
  esac
done

# Each folder's AGENTS.md carries the rules of its folder for runtimes that load no rule by path (KIT-067).
python3 "$KIT_DIR/platforms/tools/sync_agents_md.py" write "$REPO" "$version" "$AGENTS_RULES"

# Each profile folder's kit.just (KIT-074); the project's justfile imports it.
python3 "$KIT_DIR/platforms/tools/sync_just.py" write "$REPO" "$version" "$PROFILE"

# The keyed-CSV merge driver for a godot profile (KIT-074). git config is per clone and never versioned, so the
# sync only prints the step; a clone without it merges the CSV as text, which still shows a conflict.
if merge_driver_wanted; then
  mkdir -p "$REPO/.github/merge-drivers"
  cmp -s "$MERGE_DRIVER_SRC" "$REPO/$MERGE_DRIVER_REL" || cp "$MERGE_DRIVER_SRC" "$REPO/$MERGE_DRIVER_REL"
  if ! git -C "$REPO" config --get merge.keyed-csv.driver >/dev/null 2>&1; then
    echo "sync: $MERGE_DRIVER_REL vendored; configure it once in each clone (git config is not versioned):"
    echo "sync:   git config merge.keyed-csv.name 'keyed CSV merge'"
    echo "sync:   git config merge.keyed-csv.driver 'python3 $MERGE_DRIVER_REL --marker-size %L --path %P %O %A %B'"
    echo "sync:   and one .gitattributes line per CSV: <path or glob> merge=keyed-csv (platforms/kits/godot/README.md)"
  fi
elif merge_driver_marked; then
  rm -f "$REPO/$MERGE_DRIVER_REL"
  rmdir "$REPO/.github/merge-drivers" 2>/dev/null || true
  echo "sync: removed $MERGE_DRIVER_REL (no godot profile)"
fi

# The marker records the profile list, which a sync without --profile reuses (KIT-081 stage 2b).
claude_body="<!-- $CLAUDE_MARKER v$version; profile $PROFILE; AGENTS.md is the source -->
@AGENTS.md"
if [[ ! -f "$REPO/CLAUDE.md" ]] || [[ "$(cat "$REPO/CLAUDE.md")" != "$claude_body" ]]; then
  printf '%s\n' "$claude_body" > "$REPO/CLAUDE.md"
fi

# KIT-081 stage 2b: a repository synced in the vendored mode loses the kit-marked copies, the pin and the pin's
# settings entries; guardrails@ai-kit is already on and CLAUDE.md records the profile, so a failure here loses neither.
python3 "$UNVENDOR_TOOL" remove "$REPO"

# KIT-081 stage 1: the .github/spec-lint/ copy an older sync generated goes (kit-named files only); the spec tools run
# from the kit. A repo with docs/spec whose CI runs no spec tools gets spec-lint.yml, the action pinned to this kit.
python3 "$SPEC_TOOLS" remove "$REPO"
spec_note=""
if [[ -d "$REPO/docs/spec" ]]; then
  python3 "$SPEC_TOOLS" workflow "$REPO" ${WORKFLOW:+--workflow "$WORKFLOW"} || exit 1
  spec_note="spec tools, "
else
  echo "sync: no docs/spec, spec tools skipped"
fi
echo "sync: $REPO <- kit $version (profile $PROFILE: ${spec_note}CLAUDE.md, .claude/settings.json, .claude/rules [$rules_written written, $rules_removed removed])"
