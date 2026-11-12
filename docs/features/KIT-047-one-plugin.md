---
id: KIT-047
title: "One plugin: dev and sdd merge into core"
status: done
confirmed: "2026-11-12 (owner, chat of the kit review session: \"Sim, um só\")"
issue: "#176"
pr: ""
---

# KIT-047 — One plugin: dev and sdd merge into core

## Problem and evidence

[FACT] KIT-038 split the kit into three plugins by audience (`core`, `dev`, `sdd`). On 2026-11-12, `devin plugins list`
on the owner's Mac printed only `core v11.3.0`: Devin CLI never received the `dev` and `sdd` skills, although the README
said the root meta-plugin installs the three.

[FACT] `~/.claude/settings.json` on the same Mac enables `core@ai-kit`, `dev@ai-kit` and `sdd@ai-kit`, and every
Stratics repository enables `core@ai-kit` and vendors the rest, so the split selected nothing for its only user. It still
cost two more manifest sets, a dependency chain, a second name per skill (`/dev:testing`), and the KIT-041
`plugins: [../.., ../../../core]` line in the five `dev` and `sdd` eval cases.

## Change

- `plugins/dev/` and `plugins/sdd/` move into `plugins/core/` (`git mv`: skills, the `godot`, `java`, `python` and `spec`
  rules, the `researcher` agent, eval cases and templates); their manifests and `INDEX.md` files are deleted.
  `plugins/core/INDEX.md` is regenerated.
- `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` list only `core`; the Claude `renames` map
  gains `"dev": "core"` and `"sdd": "core"`, so an installed `dev@ai-kit` or `sdd@ai-kit` migrates on the next refresh,
  and the KIT-038 names that pointed at `dev` or `sdd` (`dev-core`, `architect-sdd`, ...) now point at `core` directly.
  The Devin meta-plugin requires only `plugins/core`.
- `platforms/tools/sync-profiles.txt` (new) has one line per `core` skill and rule with the profiles (`godot`, `java`,
  `python`, `docs`, or `-`) that receive it. `sync-project.sh` reads it instead of the plugin layout: settings enable
  only `core@ai-kit`, rules render as `.claude/rules/core-<rule>.md`, and a generated `dev-*.md` or `sdd-*.md` from an
  older sync is reported by `--check` ("is generated but not in profile") and removed by the sync.
- `check_kit.py` § 11b fails when the map is missing, has a malformed or repeated line, gives a rule `-`, names an
  unknown profile, or misses or invents a `core` skill or rule.
- The five moved eval cases drop the KIT-041 `plugins:` line; `evals.yml` drops the comment that explained it.
- `test_sync_project.py` reads the map, and `test_rule_from_the_old_plugin_name_is_replaced` covers the `dev-godot.md`
  migration; `smoke.sh` uses the `core` paths, the `core` Devin dependency, renames that target only listed plugins, and
  one enabled `@ai-kit` plugin per synced repository.
- README, CONTRIBUTING, `docs/design.md`, `docs/projects.md`, the `platforms/kits` READMEs, `init-spec.sh`,
  `skills.lock` and `platforms/tools/README.md` name the single plugin.

A repository that vendors its skills still loads them twice on a machine where the plugin is installed (`/core:name` and
`/name`), as it did with `dev` and `sdd` enabled at user scope; the vendored copy is the one that reaches cloud sessions.

## Proof

- `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`, with the new migration test: 107 tests,
  `OK (skipped=1)` in four runs; one earlier run reported `FAILED (failures=1)` and its detail was not captured.
- `python3 platforms/ci/validations/check_kit.py --links`; § 11b fired on each injected bad map line.
- `python3 platforms/tools/gen_index.py --check`, `bash platforms/tools/smoke.sh`, `CI=1 bash platforms/tools/check.sh`,
  `platforms/tools/vendor.sh --check`, `claude plugin validate` on the marketplace and the plugin, and `gitleaks`.
- Not run: `claude plugin eval` (billed); the moved cases now match the `core` cases that already run without a
  `plugins:` line.

## History

- 2026-11-12: confirmed (owner, in chat) and implemented.
