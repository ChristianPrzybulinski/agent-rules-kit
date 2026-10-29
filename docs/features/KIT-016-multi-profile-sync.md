---
id: KIT-016
title: "sync-project.sh syncs a monorepo with a comma list of profiles"
status: done
confirmed: "2026-10-29 (owner, brief relayed by the Stratics FEAT-100 T12 follow-up session)"
issue: "#102"
pr: ""
---

# KIT-016 — sync-project.sh syncs a monorepo with a comma list of profiles

## Problem and evidence

[FACT] `platforms/tools/sync-project.sh` accepted exactly one profile: `--profile godot|java|docs`. Each profile names a
plugin set, and the plugin set decides which plugins `.claude/settings.json` enables, which rules are generated into
`.claude/rules/`, and which skills `--vendor-skills` copies into `.claude/skills/`.

[FACT] The Stratics monorepo (dev-game-studio/stratics) keeps its docs at the root, the Godot client in `client/` and
the Java server in `server/`. FEAT-100 T12 (dev-game-studio/stratics#2767, merge commit fa6e56c) moved the client and
server rules to the root `.claude/rules/` with folder-scoped globs: `dev-godot-godot.md` lists `"client/**/*.gd"`,
`"client/**/*.tscn"` and `"client/**/project.godot"`, and `dev-java-java.md` lists `"server/**/*.java"` and
`"server/**/pom.xml"`.

[FACT] On Stratics `main` 9f8b338 (a disposable sparse worktree), `sync-project.sh --check --profile docs
--vendor-skills` exits 1 with:

```
sync: .claude/rules/dev-godot-godot.md is generated but not in profile
sync: .claude/rules/dev-java-java.md is generated but not in profile
```

A write run with the same profile would delete both rules. A run with `godot` or `java` would drop the other stack and
write the rule back with the unscoped `**/*.gd` or `**/*.java`. No single profile can describe the repository.

## Change

- `platforms/tools/sync-project.sh`:
  - `--profile` takes a comma list. Each entry is `godot|java|docs`, optionally followed by `:<dir>`, as in
    `docs,godot:client,java:server`. `normalize_profile` sorts and deduplicates the list and drops a trailing `/`.
    It exits 2 on an unknown profile or an empty entry. It also exits 2 on a folder that is absolute or contains
    `..` or `.`; the message says the folder "must be a relative path inside the repo". `KIT_MANIFEST.json` records
    the normalized list as `profile`.
  - `profile_plugins` returns the union of the entries' plugin lists, in first-occurrence order. Its callers are
    `rule_files`, `skill_dirs` and `SETTINGS_PLUGINS`. The settings plugin set, the generated rules, the vendored
    skills and the "generated but not in profile" removal check therefore all follow the union. Vendored mode still
    enables only `core@ai-kit`, and `core` skills are still never vendored (KIT-002).
  - `render_rule` scopes a rule when every entry that brings its plugin has a folder. Each `globs:` or `paths:` item
    `"<glob>"` then becomes one `"<dir>/<glob>"` item per folder. If any entry that brings the plugin is unscoped,
    the rule stays as the kit wrote it. The kit has three rules today, in `architect-sdd`, `dev-godot` and
    `dev-java`. With `docs,godot:client,java:server`, the `architect-sdd` rule keeps `"docs/spec/**/*.md"` and the
    other two are scoped.
  - `infer_profile` is unchanged: without `--profile` the first match wins, and the result is a one-entry list.
- `platforms/tools/smoke.sh`: a multi-profile case under bash 3.2 with the restricted `PATH`. It installs
  `docs,godot:client,java:server` with `--vendor-skills` and checks the three rules, the scoped lines and the
  vendored union skills. A reordered list with a duplicate gives identical hashes. `--check` with the list passes,
  `--check --profile docs` reports the removal, a `../client` folder is refused with the repository unchanged, and a
  non-vendored `godot,java` enables exactly 9 kit plugins.
- `platforms/ci/validations/test_sync_project.py`: `test_multi_profile_union_and_folder_scope` (rules, scoped lines,
  settings union, `--check`) and `test_multi_profile_rejects_unknown_profile_and_outside_folder` (`docs,rust`,
  `godot:../client`, `godot:/client`, `docs,`).
- `platforms/tools/INDEX.md` and `docs/projects.md`: the comma list and the `:<dir>` scope.
- `CHANGELOG.md`: an `### Added` line.

## Options considered

| Option | Verdict |
|---|---|
| A. A comma list with an optional `:<dir>` scope per entry (chosen) | Any mix of stacks in any folders, and no project's layout lives in the kit |
| B. A named `monorepo` profile | It hard-codes one repository's composition (docs + Godot in `client/` + Java in `server/`) into the kit, and each other mix of stacks or folders needs a new name |
| C. A comma list without `:<dir>` | It renders `**/*.gd`, so `--check` reports the T12 rules as divergent and a write sync widens them back to the whole repository |
| D. One sync run per profile | Each run removes the other profiles' rules and rewrites the settings and the manifest |

## Proof

- `bash platforms/tools/check.sh`: OK (14 plugins, 46 skills, 3 rules, 22 templates, 23 indexes, 111 links, 12 hook
  cases).
- `bash platforms/tools/smoke.sh`: "smoke: OK (… vendored skills, multi-profile sync, no-spec repo)".
- `python3.12 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: 67 tests OK (1 skipped).
- `python3 platforms/ci/validations/check_kit.py --links` and the CI's
  `shellcheck platforms/tools/*.sh platforms/kits/*/*.sh platforms/kits/*/scripts/*.sh`: clean.
- Stratics `main` 9f8b338, disposable sparse worktree, `--check` only:
  `sync-project.sh --check --profile docs,godot:client,java:server --vendor-skills` prints no rule, settings or
  `CLAUDE.md` divergence. It still exits 1 on Stratics state that the kit does not own: the manifest records
  `profile='docs'`, and 15 union skills (`godot-standards`, `java-standards`, `code-standards`, …) are not vendored.
  A write sync with the list in a Stratics session records the list and vendors them.

## History

- 2026-10-29: confirmed (owner, brief relayed by the Stratics FEAT-100 T12 follow-up session). Implemented on
  `kit/multi-profile-sync`.
