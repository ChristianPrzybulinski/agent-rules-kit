#!/usr/bin/env bash
# Syncs the spec validator and the agent configuration with a project (a copy, no link to the kit).
# Usage: sync-project.sh [--profile <profile>[,<profile>...]] [--vendor-skills] [--workflow <file>] <repo-dir>
#                                                          installs/updates .github/spec-lint/ (repos with docs/spec only),
#                                                          CLAUDE.md (imports AGENTS.md),
#                                                          .claude/settings.json (ai-kit marketplace +
#                                                          enabledPlugins guardrails@ai-kit +
#                                                          includeGitInstructions false) and
#                                                          .claude/rules/guardrails-<rule>.md (the profile's
#                                                          path rules, marked as generated); with
#                                                          --vendor-skills also .claude/skills/<name>/
#                                                          (whole skill directories, .agent-rules-kit
#                                                          marker, KIT_MANIFEST.json hashes)
#        sync-project.sh --check [--profile <profile>[,<profile>...]] [--vendor-skills] [--workflow <file>] <repo-dir>
#                                                          compares all of them with the kit and scans the
#                                                          repo's *.md for obsolete kit paths and
#                                                          citations of skills KIT-070 removed;
#                                                          exit 1 on any divergence or stale citation
# --profile selects the kit rules copied into .claude/rules/ and the kit skills copied into
# .claude/skills/: platforms/tools/sync-profiles.txt names the profiles that receive each one
# (KIT-047). Without it the list that .claude/skills/KIT_MANIFEST.json
# records is used; a repo without a manifest gets the profile inferred, first match wins:
# project.godot (godot), pom.xml (java), docs/spec/ (docs). The run prints which source won.
# <profile> is godot|java|docs|python, optionally followed by :<dir>. A comma list syncs the union
# of its profiles' rules and skills, for a monorepo such as
# docs,godot:client,java:server,python:platform. The :<dir> suffix scopes the globs/paths of the rule named
# after that profile to <dir>/ ("**/*.gd" renders as "client/**/*.gd"; java:server leaves the
# godot rule alone), and any other rule to the folders of every profile that receives the rule.
# The list is stored sorted and deduplicated, which is the form KIT_MANIFEST.json
# records.
# A .claude/rules/*.md destination that exists without the generated marker refuses
# the sync before any write; a marked file that falls out of the profile is removed.
# --vendor-skills copies the profile's plugins/guardrails/skills/<name>/ directories whole (the always-on
# skills, "-" in the map, excepted: they load from the enabled plugin)
# into .claude/skills/<name>/, marks each copy with .agent-rules-kit and writes
# KIT_MANIFEST.json (kit version, profile, plugin, sha256 per file). The manifest is
# sticky: once it exists a bare sync-project.sh <repo> keeps the vendored mode and the
# recorded profile list. A
# .claude/skills/<name>/ directory without the marker is never read, replaced or
# deleted - its presence refuses the sync before any write. Plugins mode enables only
# guardrails@ai-kit in .claude/settings.json (the kit ships one plugin, KIT-047). Vendored mode pins
# the whole kit (KIT-072, written by platforms/tools/sync_pinned_plugin.py): .claude/ai-kit/hooks/ holds
# the kit hooks as scripts that .claude/settings.json "hooks" runs, so the guard needs no folder trust;
# .claude/ai-kit/platforms/ holds the kit tools the skills and rules call, and the vendored copies call
# them there instead of in ~/.ai-kit (pin_rewrite);
# .claude/skills/guardrails-pinned/ is a skills-directory plugin with the kit agents, templates and
# every skill not copied as a plain skill; KIT_MANIFEST.json records the kit commit and the hashes; and
# once both are written .claude/settings.json sets guardrails@ai-kit, which follows the kit head, to
# false and guardrails-pinned@skills-dir to true, so each kit skill lists once and a kit merge changes
# nothing in the project until the next sync. --check also reports a settings.local.json that
# re-enables the head and, with AI_KIT_CLAUDE_PROBE=1, the plugins Claude Code lists for the repository.
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
# docs/spec/spec.md sdd.doc_structure.enabled vendors check_docs_structure.py into .github/spec-lint/ (KIT-074).
# --workflow names the CI file that must run check_spec.py. Without it, --check
# accepts any file under .github/workflows/ containing check_spec.py, and install
# copies the kit workflow (as spec-lint.yml) only if the project has none.
# Both modes print "sync: warning: ..." on stderr when <repo-dir> resolves into a cloud-synced
# folder (the plugin's SessionStart hook decides; KIT-021); the exit code does not change.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# The kit's one plugin (KIT-047), named guardrails since KIT-055.
KIT_PLUGIN="guardrails"
# A vendored project's pinned copy of it (KIT-072); platforms/tools/sync_pinned_plugin.py owns the folder.
PINNED_PLUGIN="guardrails-pinned"
PIN_TOOL="$KIT_DIR/platforms/tools/sync_pinned_plugin.py"

MODE="install"
PROFILE=""
WORKFLOW=""
VENDOR_FLAG=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check" ;;
    --profile) PROFILE="${2:?usage: sync-project.sh [--check] [--profile <profile>[,<profile>...]] [--vendor-skills] [--workflow <file>] <repo-dir>}"; shift ;;
    --workflow) WORKFLOW="${2:?usage: sync-project.sh [--check] [--profile <profile>[,<profile>...]] [--vendor-skills] [--workflow <file>] <repo-dir>}"; shift ;;
    --vendor-skills) VENDOR_FLAG=1 ;;
    --) shift; break ;;
    *) break ;;
  esac
  shift
done
REPO="${1:?usage: sync-project.sh [--check] [--profile <profile>[,<profile>...]] [--vendor-skills] [--workflow <file>] <repo-dir>}"
DEST="$REPO/.github/spec-lint"
SCHEMAS="spec feature requirement decision debt need progress task"
CLAUDE_MARKER="generated by agent-rules-kit sync-project.sh"
RULE_PATHS=""  # "<rule> <dir>..." lines from docs/spec/spec.md sdd.rule_paths (KIT-067)
DOC_STRUCTURE=0  # 1 when docs/spec/spec.md sets sdd.doc_structure.enabled (KIT-074)
MERGE_DRIVER_SRC="$KIT_DIR/platforms/kits/godot/scripts/keyed_csv_merge.py"
MERGE_DRIVER_REL=".github/merge-drivers/keyed_csv_merge.py"  # vendored for a godot profile (KIT-074)
SYNC_TMP="$(mktemp -d)"
trap 'find "$SYNC_TMP" -delete' EXIT
RULE_MARKER_PREFIX='<!-- agent-rules-kit: generated from '
# The line under the marker of each .claude/rules copy: Claude Code has no other path to a kit reference a rule names
# (sdd-implement and sdd-plan are user-only skills). sync_agents_md.py drops it from the AGENTS.md block, whose intro
# says the same once per folder.
# shellcheck disable=SC2016  # literal Markdown backticks
RULE_LOCATION='Kit files this rule names: skill `<skill>`, reference `<file>` is `.claude/skills/<skill>/references/<file>` when this repository vendors the skill, else `~/.ai-kit/plugins/guardrails/skills/<skill>/references/<file>`.'
version="$(cat "$KIT_DIR/VERSION")"

if [[ -n "$WORKFLOW" && ( "$WORKFLOW" == */* || "$WORKFLOW" == .* ) ]]; then
  echo "sync: --workflow must be a plain file name under .github/workflows/" >&2
  exit 2
fi

hash_file() { shasum -a 256 "$1" | cut -d' ' -f1; }

kit_files() { # prints "src rel-dest"
  echo "$KIT_DIR/platforms/ci/validations/check_spec.py check_spec.py"
  # The task-row checks (KIT-073) and the proof predicates they share with the PR gates.
  echo "$KIT_DIR/platforms/ci/validations/row_checks.py row_checks.py"
  echo "$KIT_DIR/platforms/ci/validations/pr_gates.py pr_gates.py"
  # The trace tool goes to every project: sync-status, status and impact need no journeys, and its check asks
  # for traceability.md only when journeys are on or the file exists.
  echo "$KIT_DIR/platforms/ci/validations/spec_trace.py spec_trace.py"
  for s in $SCHEMAS; do
    echo "$KIT_DIR/platforms/ci/schemas/$s.schema.json schemas/$s.schema.json"
  done
  # Journeys are opt-in: only a project with docs/spec/journeys gets the journey schema.
  if [[ -d "$REPO/docs/spec/journeys" ]]; then
    echo "$KIT_DIR/platforms/ci/schemas/journey.schema.json schemas/journey.schema.json"
  fi
  # The README and done/INDEX.md check is opt-in (sdd.doc_structure.enabled, KIT-074).
  if [[ "$DOC_STRUCTURE" == 1 ]]; then
    echo "$KIT_DIR/platforms/ci/validations/check_docs_structure.py check_docs_structure.py"
  fi
}

merge_driver_wanted() { # a godot profile gets the keyed-CSV merge driver (KIT-074)
  profile_entries "$PROFILE" | cut -d' ' -f1 | grep -qx godot
}

merge_driver_marked() { # the vendored driver names the kit; a file without the name is the project's
  grep -qF 'agent-rules-kit' "$REPO/$MERGE_DRIVER_REL" 2>/dev/null
}

# KIT-072: the pin, in one block so merges stay mechanical; platforms/tools/sync_pinned_plugin.py does the work.
pin_sources() { # prints "src repo-path" for every copy the sync vendors outside .claude/skills: each file kit_files
  # lists, under .github/spec-lint/, so a file a later kit adds to kit_files is pinned and checked with the rest
  local src rel
  if [[ -d "$REPO/docs/spec" ]]; then
    kit_files | while read -r src rel; do echo "$src .github/spec-lint/$rel"; done
  fi
  # KIT-074: the keyed-CSV merge driver, a byte copy of its kit source, and each generated just module. A module is
  # rendered (a marked header, or an aggregate of several profiles), so its source is the file the sync wrote, which
  # pin_record reads after the write; sync_just.py check compares its content with the kit.
  if merge_driver_wanted; then echo "$MERGE_DRIVER_SRC $MERGE_DRIVER_REL"; fi
  python3 "$KIT_DIR/platforms/tools/sync_just.py" list "$REPO" - "$PROFILE" |
    while read -r rel; do echo "$REPO/$rel $rel"; done
}
pin_preflight() { python3 "$PIN_TOOL" preflight "$REPO"; }
pin_write() { python3 "$PIN_TOOL" write "$REPO" "$KIT_DIR" "$version" "$@"; } # "$@": the skills copied as plain skills
pin_settings() { python3 "$PIN_TOOL" settings "$REPO"; } # after pin_write: the kit hooks on, the head off
pin_record() { pin_sources | python3 "$PIN_TOOL" pin "$REPO" "$KIT_DIR"; } # KIT_MANIFEST.json keys of the pin
pin_check() { pin_sources | python3 "$PIN_TOOL" check "$REPO" "$1"; }
pin_remove() { python3 "$PIN_TOOL" remove "$REPO"; }
pin_rewrite() { # vendored mode: the copies call the tools pinned under .claude/ai-kit/platforms/, not the kit clone
  [[ "${VENDOR:-0}" != 1 ]] || python3 "$PIN_TOOL" rewrite "$@"
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
  pin_rewrite "$out"  # KIT-072: in vendored mode the rule calls the pinned tools
}

has_check_spec_workflow() { # any project workflow that runs check_spec.py
  local wf
  for wf in "$REPO"/.github/workflows/*; do
    [[ -f "$wf" ]] && grep -q "check_spec\.py" "$wf" && return 0
  done
  return 1
}

infer_profile() { # $1 = repo dir
  if [[ -f "$1/project.godot" ]]; then echo godot
  elif [[ -f "$1/pom.xml" ]]; then echo java
  elif [[ -d "$1/docs/spec" ]]; then echo docs
  else echo "sync: cannot infer profile for $1 (no project.godot, pom.xml or docs/spec); pass --profile godot|java|docs|python" >&2; return 1
  fi
}

manifest_profile() { # $1 = KIT_MANIFEST.json; prints the profile list it records, or nothing
  # when the file is missing, unreadable or records none
  [[ -f "$1" ]] || return 0
  python3 - "$1" <<'PY'
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

skill_dirs() { # prints "<plugin> <name>" for every kit skill the map gives to a profile in $PROFILE;
  # the always-on skills ("-") stay out: the plugin is enabled in .claude/settings.json (its guard hook
  # lives only in the plugin), so they load from the plugin (KIT-002)
  local name
  while read -r name; do
    echo "$KIT_PLUGIN $name"
  done < <(map_selected skills)
}

# Obsolete kit paths (layouts 1.x to 11.x). A consumer line that must keep one
# (historical citation) appends the marker "<!-- kit-path-ok -->".
# .claude/ is skipped: generated kit copies there are verified by their own
# manifest and repo-owned content under .claude/ is not a kit citation.
STALE_KIT_PATHS='agents/skills/|agents/rules/|agents/knowledge/|rules/godot/|rules/java/|rules/git/|kits/java-maven/|kits/github/|platforms/install/|knowledge/|processes/sdd/|plugins/ai-kit/|plugins/core/|plugins/sdd/|plugins/dev/|plugins/architect-|plugins/all/|plugins/dev-|plugins/extras/|plugins/infra-|plugins/process-loop/|plugins/quality-'
STALE_OPT_OUT='<!-- kit-path-ok -->'

scan_stale_kit_paths() { # $1 = repo dir; prints one line per stale citation; returns 1 if any
  local hits
  hits="$(grep -rnE --include='*.md' --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.claude \
      "(^|[^/A-Za-z0-9_.-])($STALE_KIT_PATHS)" "$1" 2>/dev/null \
    | sed "s|^${1%/}/||" \
    | grep -vE '^([^:]*/)?(legacy|docs/sessions)/' \
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
excluded = re.compile(r"^([^/]*/)*(legacy|docs/sessions)/")
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

# The repo profile selects the plugin set; check and install both need it. The list is
# sticky like the vendored mode below: without --profile, the list KIT_MANIFEST.json
# records wins over inference, so a bare run keeps a monorepo's union (KIT-017).
if [[ -n "$PROFILE" ]]; then
  profile_source="--profile"
elif PROFILE="$(manifest_profile "$REPO/.claude/skills/KIT_MANIFEST.json")" && [[ -n "$PROFILE" ]]; then
  profile_source="manifest"
else
  PROFILE="$(infer_profile "$REPO")"
  profile_source="inferred"
fi
PROFILE="$(normalize_profile "$PROFILE")" || {
  [[ "$profile_source" != manifest ]] \
    || echo "sync: .claude/skills/KIT_MANIFEST.json records that profile; pass --profile to replace it" >&2
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
  DOC_STRUCTURE="$(python3 -c 'import json, sys; print(1 if json.load(open(sys.argv[1], encoding="utf-8")).get("doc_structure", {}).get("enabled") is True else 0)' "$SYNC_TMP/params.json")"
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

# --vendor-skills is sticky: an existing manifest keeps the repo vendored without
# the flag, so init-spec.sh and a bare `sync-project.sh <repo>` preserve the mode.
VENDOR=0
if [[ "$VENDOR_FLAG" == 1 || -f "$REPO/.claude/skills/KIT_MANIFEST.json" ]]; then
  VENDOR=1
fi
vendored_skills=0
vendored_files=0
# The kit ships one plugin (KIT-047). Plugins mode enables it; in vendored mode the pin sets enabledPlugins
# (pin_settings, pin_check), which turns it off once the pinned copy is written (KIT-072).
SETTINGS_PLUGINS="$KIT_PLUGIN"
export AI_KIT_PINNED="$VENDOR"
if [[ "$VENDOR" == 1 ]]; then echo "sync: skills=vendored"; else echo "sync: skills=plugins"; fi

if [[ "$MODE" == check ]]; then
  FAILED=0
  expected="$(cat "$KIT_DIR/VERSION")"
  # The spec validator belongs to repos with docs/spec only; elsewhere the
  # CLAUDE.md/settings/rules/skills checks below decide the verdict.
  if [[ -d "$REPO/docs/spec" ]]; then
    actual="$(cat "$DEST/KIT_VERSION" 2>/dev/null || echo '')"
    [[ "$actual" == "$expected" ]] || { echo "sync: $REPO KIT_VERSION='$actual' kit='$expected'"; FAILED=1; }
    kit_files | while read -r src rel; do
      dst="$DEST/$rel"
      if [[ ! -f "$dst" ]]; then echo "sync: $dst missing"; exit 1; fi
      [[ "$(hash_file "$src")" == "$(hash_file "$dst")" ]] || { echo "sync: $rel diverges from the kit"; exit 1; }
    done || FAILED=1
    if [[ -n "$WORKFLOW" ]]; then
      wf="$REPO/.github/workflows/$WORKFLOW"
      if [[ ! -f "$wf" ]]; then
        echo "sync: $WORKFLOW missing"; FAILED=1
      elif ! grep -q "check_spec\.py" "$wf"; then
        echo "sync: $WORKFLOW does not run check_spec.py"; FAILED=1
      fi
    elif ! has_check_spec_workflow; then
      echo "sync: no workflow under .github/workflows runs check_spec.py"; FAILED=1
    fi
    if [[ "$DOC_STRUCTURE" != 1 && -f "$DEST/check_docs_structure.py" ]]; then
      echo "sync: .github/spec-lint/check_docs_structure.py is generated but sdd.doc_structure is off"; FAILED=1
    fi
  fi
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
  if [[ ! -f "$claude_file" ]] \
      || ! grep -qF "$CLAUDE_MARKER v$expected;" "$claude_file" \
      || [[ "$(grep -v '^<!--' "$claude_file" || true)" != "@AGENTS.md" ]]; then
    echo "sync: CLAUDE.md missing or diverges (rerun sync-project.sh)"
    FAILED=1
  fi
  AI_KIT_PLUGINS="$SETTINGS_PLUGINS" python3 - "$REPO/.claude/settings.json" "$PROFILE" <<'PY' || FAILED=1
import json, os, sys
path, profile = sys.argv[1], sys.argv[2]
pinned = os.environ.get("AI_KIT_PINNED") == "1"  # KIT-072: then pin_check owns enabledPlugins
want = set() if pinned else {name + "@ai-kit" for name in os.environ.get("AI_KIT_PLUGINS", "").split()}
market = {"source": {"source": "github", "repo": "ChristianPrzybulinski/agent-rules-kit"}}
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
    have = {key for key in enabled if isinstance(key, str) and key.endswith("@ai-kit") and not pinned}
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
  if [[ -f "$REPO/.claude/skills/KIT_MANIFEST.json" ]]; then
    # The vendored tree verifies against its manifest, never against the kit
    # directories: unmarked skills under .claude/skills are not even opened.
    SKILL_DIRS="$(skill_dirs)" PINNED_PLUGIN="$PINNED_PLUGIN" python3 - "$REPO/.claude/skills" "$expected" "$PROFILE" <<'PY' || FAILED=1
import hashlib, json, os, sys

root, version, profile = sys.argv[1], sys.argv[2], sys.argv[3]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scanned_files(directory):  # relative path per regular file, links skipped
    found = []
    for base, dirnames, filenames in os.walk(directory):
        dirnames.sort()
        for filename in sorted(filenames):
            path = os.path.join(base, filename)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            found.append(os.path.relpath(path, directory).replace(os.sep, "/"))
    return found


try:
    with open(os.path.join(root, "KIT_MANIFEST.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
except (OSError, ValueError):
    print("sync: .claude/skills/KIT_MANIFEST.json is not valid JSON; resync")
    sys.exit(1)
if not isinstance(manifest, dict):
    print("sync: .claude/skills/KIT_MANIFEST.json is not a JSON object; resync")
    sys.exit(1)
failed = False


def report(line):
    global failed
    failed = True
    print("sync: " + line)


got_version = manifest.get("KIT_VERSION")
if got_version != version:
    report(f".claude/skills/KIT_MANIFEST.json KIT_VERSION='{got_version}' kit='{version}'")
got_profile = manifest.get("profile")
if got_profile != profile:
    report(f".claude/skills/KIT_MANIFEST.json profile='{got_profile}'"
           f" expected '{profile}' (pass --profile or resync)")
skills = manifest.get("skills")
if not isinstance(skills, dict):
    skills = {}
want = sorted({line.split()[-1] for line in os.environ.get("SKILL_DIRS", "").splitlines() if line.strip()})
missing = sorted(set(want) - set(skills))
extra = sorted(set(skills) - set(want))
if missing or extra:
    parts = []
    if missing:
        parts.append("missing: " + ",".join(missing))
    if extra:
        parts.append("extra: " + ",".join(extra))
    report(f".claude/skills manifest skills differ from profile {profile} ({'; '.join(parts)})")
for name in sorted(skills):
    entry = skills[name]
    files = entry.get("files") if isinstance(entry, dict) else None
    if not isinstance(files, dict):
        continue
    for rel in sorted(files):
        norm = os.path.normpath(rel)
        if norm.startswith("..") or os.path.isabs(norm):
            continue
        target = os.path.join(root, name, norm)
        if os.path.islink(target) or not os.path.isfile(target):
            report(f".claude/skills/{name}/{rel} missing")
        elif sha256(target) != files[rel]:
            report(f".claude/skills/{name}/{rel} diverges from the manifest")
for name in sorted(os.listdir(root)):
    directory = os.path.join(root, name)
    if not os.path.isdir(directory) or name == os.environ.get("PINNED_PLUGIN"):  # KIT-072: sync_pinned_plugin.py checks it
        continue
    if not os.path.isfile(os.path.join(directory, ".agent-rules-kit")):
        continue
    entry = skills.get(name)
    if not isinstance(entry, dict):
        report(f".claude/skills/{name} is generated but not in manifest")
        continue
    listed = entry.get("files")
    listed = set(listed) if isinstance(listed, dict) else set()
    for rel in scanned_files(directory):
        if rel not in listed:
            report(f".claude/skills/{name}/{rel} not in manifest")
sys.exit(1 if failed else 0)
PY
    # KIT-072: the pinned plugin copy, the local settings and the plugins Claude Code lists for the repository
    pin_check "$expected" || FAILED=1
  elif [[ "$VENDOR" == 1 ]]; then
    echo "sync: .claude/skills/KIT_MANIFEST.json missing (run sync-project.sh --vendor-skills)"
    FAILED=1
  fi
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
# The same refusal applies to vendored skill destinations: a .claude/skills/<name>
# without the .agent-rules-kit marker is repo-owned, so the sync stops here, before
# any write, leaving the repo exactly as it was.
if [[ "$VENDOR" == 1 ]]; then
  if [[ -e "$REPO/.claude/skills" && ! -d "$REPO/.claude/skills" ]]; then
    echo "sync: $REPO/.claude/skills exists and is not a directory; move it by hand"
    exit 1
  fi
  while read -r plugin name; do
    [[ -n "$plugin" ]] || continue
    dst="$REPO/.claude/skills/$name"
    if [[ -e "$dst" || -L "$dst" ]] && [[ ! -f "$dst/.agent-rules-kit" ]]; then
      echo "sync: $dst exists and is not generated; rename it or drop the profile that receives it (platforms/tools/sync-profiles.txt)"
      exit 1
    fi
  done < <(skill_dirs)
  # KIT-072: the pin's folders follow the same rule (exit 1); settings it cannot merge into exit 2
  pin_preflight || exit $?
fi

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
markets["ai-kit"] = OrderedDict(source=OrderedDict(source="github", repo="ChristianPrzybulinski/agent-rules-kit"))
enabled = data.setdefault("enabledPlugins", OrderedDict())
pinned = os.environ.get("AI_KIT_PINNED") == "1"  # KIT-072: then pin_settings sets them, after the pinned copy
for key in [k for k in enabled if k.endswith("@ai-kit") and not pinned]:
    del enabled[key]
for name in [] if pinned else plugins:
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

# In vendored mode each profile skill directory is copied whole (SKILL.md,
# references/, agents/, scripts/, VENDOR.md, LICENSE.txt) and marked
# .agent-rules-kit; a copy is replaced only when diff finds drift, and marked
# directories that fall out of the profile are removed. Unmarked directories
# are never touched - the collision refusal above already stopped the sync.
if [[ "$VENDOR" == 1 ]]; then
  mkdir -p "$REPO/.claude/skills"
  skill_tmp="$(mktemp -d)"
  skill_names=""
  while read -r plugin name; do
    [[ -n "$plugin" ]] || continue
    skill_names="$skill_names$name "
    vendored_skills=$((vendored_skills + 1))
    cp -R "$KIT_DIR/plugins/$plugin/skills/$name" "$skill_tmp/$name"
    pin_rewrite "$skill_tmp/$name"  # KIT-072: the copy calls the pinned tools
    printf '%s\n' "plugins/$plugin/skills/$name kit $version generated by platforms/tools/sync-project.sh; do not edit" \
      > "$skill_tmp/$name/.agent-rules-kit"
    vendored_files=$((vendored_files + $(find "$skill_tmp/$name" -type f | wc -l)))
    dst="$REPO/.claude/skills/$name"
    if [[ ! -d "$dst" ]]; then
      mv "$skill_tmp/$name" "$dst"
    elif ! diff -r -q "$skill_tmp/$name" "$dst" >/dev/null; then
      find "$dst" -delete
      mv "$skill_tmp/$name" "$dst"
    fi
  done < <(skill_dirs)
  for dst in "$REPO/.claude/skills"/*/; do
    [[ -d "$dst" && -f "$dst/.agent-rules-kit" ]] || continue
    name="${dst%/}"
    name="${name##*/}"
    [[ "$name" != "$PINNED_PLUGIN" ]] || continue
    case " $skill_names" in
      *" $name "*) ;;
      *)
        find "${dst%/}" -delete
        echo "sync: removed .claude/skills/$name (not in profile)"
        ;;
    esac
  done
  # KIT-072: the kit hooks and the rest of the kit plugin (agents, the skills not copied above) as the pin;
  # only once it is written does pin_settings turn guardrails@ai-kit off
  # shellcheck disable=SC2086
  pin_write $skill_names
  pin_settings
  AI_KIT_PIN="$(pin_record)" PINNED_PLUGIN="$PINNED_PLUGIN" \
    python3 - "$REPO/.claude/skills" "$version" "$PROFILE" <<'PY'
import hashlib, json, os, sys

root, version, profile = sys.argv[1], sys.argv[2], sys.argv[3]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scanned_files(directory):  # sha256 per regular file, links skipped
    files = {}
    for base, dirnames, filenames in os.walk(directory):
        dirnames.sort()
        for filename in sorted(filenames):
            path = os.path.join(base, filename)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            rel = os.path.relpath(path, directory).replace(os.sep, "/")
            files[rel] = sha256(path)
    return files


skills = {}
for name in sorted(os.listdir(root)):
    directory = os.path.join(root, name)
    marker = os.path.join(directory, ".agent-rules-kit")
    if not os.path.isdir(directory) or not os.path.isfile(marker) or name == os.environ.get("PINNED_PLUGIN"):
        continue
    with open(marker, encoding="utf-8") as handle:
        parts = handle.readline().split()
    token = parts[0] if parts else ""
    fields = token.split("/")
    plugin = fields[1] if len(fields) == 4 and fields[0] == "plugins" and fields[2] == "skills" else ""
    skills[name] = {"plugin": plugin, "files": scanned_files(directory)}
manifest = {"KIT_VERSION": version,
            "generator": "platforms/tools/sync-project.sh",
            "profile": profile,
            "skills": skills}
manifest.update(json.loads(os.environ.get("AI_KIT_PIN") or "{}"))  # KIT-072: KIT_COMMIT and the plugin copy
text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
path = os.path.join(root, "KIT_MANIFEST.json")
try:
    with open(path, encoding="utf-8") as handle:
        current = handle.read()
except OSError:
    current = None
if current != text:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
PY
  find "$skill_tmp" -delete
else
  pin_remove  # KIT-072: plugins mode loads guardrails@ai-kit, so no pinned copy beside it
fi

claude_body="<!-- $CLAUDE_MARKER v$version; AGENTS.md is the source -->
@AGENTS.md"
if [[ ! -f "$REPO/CLAUDE.md" ]] || [[ "$(cat "$REPO/CLAUDE.md")" != "$claude_body" ]]; then
  printf '%s\n' "$claude_body" > "$REPO/CLAUDE.md"
fi

spec_lint_note=""
if [[ -d "$REPO/docs/spec" ]]; then
  mkdir -p "$DEST/schemas"
  kit_files | while read -r src rel; do cp "$src" "$DEST/$rel"; done
  # sdd.doc_structure turned off again: its copy goes (.github/spec-lint/ is generated whole)
  [[ "$DOC_STRUCTURE" == 1 ]] || rm -f "$DEST/check_docs_structure.py"
  cat "$KIT_DIR/VERSION" > "$DEST/KIT_VERSION"
  mkdir -p "$REPO/.github/workflows"
  if has_check_spec_workflow; then
    echo "sync: $REPO already runs check_spec.py in CI; kit workflow not copied"
  else
    wf="$REPO/.github/workflows/${WORKFLOW:-spec-lint.yml}"
    [[ ! -f "$wf" ]] || { echo "sync: $wf exists and does not run check_spec.py; not overwriting" >&2; exit 1; }
    cp "$KIT_DIR/platforms/kits/github/workflows/spec-lint.yml" "$wf"
  fi
  cat > "$DEST/README.md" <<EOF
# spec-lint/ — generated copy

Generated by \`platforms/tools/sync-project.sh\` from agent-rules-kit v$(cat "$KIT_DIR/VERSION").
Do not edit — update by running the sync again. \`KIT_VERSION\` records the source version.

\`CLAUDE.md\` and \`.claude/settings.json\` at the repo root are generated by the same sync;
\`AGENTS.md\` is the source of instructions. The plugins listed in \`enabledPlugins\` load in
each collaborator's local Claude Code after they trust the folder; CI runs load them only
when the runner has trusted the folder (\`hasTrustDialogAccepted\`), and cloud sessions do
not load them.
EOF
  if [[ "$VENDOR" == 1 ]]; then
    cat >> "$DEST/README.md" <<'EOF'

`.claude/skills/` holds a copy of the kit skills for this profile, each directory marked
`.agent-rules-kit` and listed with hashes in `KIT_MANIFEST.json`; do not edit.
`.claude/ai-kit/hooks/` holds the kit hooks at the same version, which `.claude/settings.json`
`hooks` runs in every session at the repo root. `.claude/skills/guardrails-pinned/` holds the
kit agents and the other skills, which Claude Code loads as `guardrails-pinned@skills-dir`
once the main checkout root is trusted. `enabledPlugins` turns off `guardrails@ai-kit`, which
follows the kit head, so the project uses the kit version it synced until the next sync
(KIT-072). Devin reads `.claude/skills/`
as well (verify against the docs.devin.ai skills overview before relying on it) and recommends `.agents/skills/`, which this sync does
not generate.
EOF
  fi
  spec_lint_note="spec-lint, "
else
  echo "sync: no docs/spec, spec-lint skipped"
fi
skills_note=""
if [[ "$VENDOR" == 1 ]]; then
  skills_note=", .claude/skills ($vendored_skills skills, $vendored_files files)"
fi
echo "sync: $REPO <- kit $version (profile $PROFILE: ${spec_lint_note}CLAUDE.md, .claude/settings.json, .claude/rules [$rules_written written, $rules_removed removed]$skills_note)"
