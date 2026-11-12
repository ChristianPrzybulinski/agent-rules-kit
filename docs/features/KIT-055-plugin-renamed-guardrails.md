---
id: KIT-055
title: "The kit plugin is renamed from core to guardrails"
status: done
confirmed: "2026-11-12 (owner, chat of the kit backlog review session: \"Sim, plugins/guardrails\")"
issue: "#188"
pr: "#197"
---

# KIT-055 — The kit plugin is renamed from core to guardrails

## Problem and evidence

[FACT] Since KIT-047 the kit ships one plugin, `core` (`plugins/core`, marketplace `ai-kit`, 11.3.0). The name only told
it apart from `dev` and `sdd`, which no longer exist. The owner asked for the content to live in one plugin named
`guardrails` and, offered "rename in place" against "move the content to the repository root", chose
`plugins/guardrails`; the root was rejected because `docs/design.md` keeps `docs/` and `platforms/` out of the plugin
root (issue #188).

[FACT] Codex keeps a removed plugin's table. In a throwaway `CODEX_HOME` with `codex-cli 0.164.0`, after the marketplace
dropped `core`: `codex plugin list` no longer printed `core@ai-kit`, printed `guardrails@ai-kit  not installed`, and
`codex plugin remove core@ai-kit` exited 0 and deleted the `[plugins."core@ai-kit"]` table and its cache. The old
bootstrap and doctor check (`*"guardrails@ai-kit"*` as a substring of that list) accepted the `not installed` line, so
neither would have installed the new name. After `codex plugin add guardrails@ai-kit` the list printed
`guardrails@ai-kit  installed, enabled  11.3.0  <path>` and `codex debug prompt-input` exposed 16 `guardrails:` skills.

[FACT] `claude plugin list --json` (Claude Code 2.1.287) on the owner's Mac holds 16 project-scope `core@ai-kit`
records, one per repository that enabled it in `.claude/settings.json`; the marketplace `renames` map migrates the
user-scope install, and each project record follows its repository's next sync.

## Change

- `plugins/core/` → `plugins/guardrails/` (`git mv`); the `name` in its three manifests is `guardrails`, so skills are
  `/guardrails:<skill>` and agents `guardrails:<agent>`; `INDEX.md` is regenerated.
- `.claude-plugin/marketplace.json` lists `guardrails` at `./plugins/guardrails`; `renames` gains
  `"core": "guardrails"`, and every older name that pointed at `core` points at `guardrails`.
  `.agents/plugins/marketplace.json` lists `guardrails`; the Devin meta-plugin `agent-rules-kit` requires
  `plugins/guardrails`.
- `doctor.sh` derives the current plugin names from `plugins/*/`: on Codex it runs `codex plugin remove <name>@ai-kit`
  for each `[plugins."<name>@ai-kit"]` table the kit no longer ships (`fix:` on success, `FAIL` with the command
  otherwise); on Claude it warns about each such record with the command for its scope; the Devin check accepts any kit
  plugin name. The Codex install check in `doctor.sh` and `bootstrap.sh` matches `<name>@ai-kit` followed by
  `installed` at the start of a line. The existing link repair re-points `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`
  and the Codex skill fallbacks from `plugins/core`, and replaces each `~/.claude/rules/core-<rule>.md` link with
  `guardrails-<rule>.md`.
- `refresh.sh` runs `doctor.sh` once when a kit link under `~/.claude` or `~/.codex` points into the kit at a path that
  no longer exists, which is what the pull of this change leaves behind.
- `sync-project.sh` enables `guardrails@ai-kit`, writes `.claude/rules/guardrails-<rule>.md`, reports and removes a
  marked `core-*.md`, reports `extra: core@ai-kit` in `--check`, and lists `plugins/core/` among the stale kit paths a
  consumer's `*.md` must not cite.
- `check_kit.py` names the plugin once (`KIT_PLUGIN`) and fails a `renames` key that is a current plugin or a target
  that is neither `null` nor a plugin directory.
- `smoke.sh`: the Codex stub lists every kit plugin as installed or `not installed` like the real CLI and implements
  `plugin remove`; the run seeds a `core@ai-kit` table and checks its removal, a former `plugins/core/AGENTS.md` link, a
  Claude `core@ai-kit` warning and a dangling link repaired by `refresh.sh`. `test_sync_project.py` covers the
  `core-godot.md` and `core@ai-kit` migrations.
- `docs/design.md` records this rename as the owner-approved exception to the layout freeze; README, CONTRIBUTING,
  `docs/projects.md`, `SECURITY.md`, the PR template, the `platforms/kits` READMEs, `init-spec.sh`, `skills.lock`,
  `sync-profiles.txt` and `platforms/tools/README.md` name `guardrails`.

Unchanged: marketplace `ai-kit`, guard prefix `ai-kit guard:`, Devin meta-plugin `agent-rules-kit` and the install
destinations. Older `KIT-0nn` records and released CHANGELOG entries keep the `core` paths of their time.

## Proof

On `61f8ad1` (base `3876ad5`), every command exit 0:

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`;
- `bash platforms/tools/smoke.sh`, with the Codex removal, AGENTS.md re-point, Claude warning and refresh repair cases;
- `python3 platforms/ci/validations/check_kit.py --links` (1 plugin, 27 skills, 84 links);
- `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: 185 tests, `OK (skipped=1)`, with the
  two `test_sync_project.py` migration tests;
- `python3 platforms/tools/gen_index.py --check`, `bash platforms/tools/vendor.sh --check`,
  `claude plugin validate plugins/guardrails` and `gitleaks git --redact --log-opts=origin/main..HEAD`.

Not run: `claude plugin eval` (billed), and the `renames` migration on a real Claude user-scope install, which is the
KIT-038 and KIT-047 mechanism.

## History

- 2026-11-12: confirmed (owner, in chat) and implemented.
