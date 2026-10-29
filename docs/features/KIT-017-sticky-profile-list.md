---
id: KIT-017
title: "sync-project.sh keeps the profile list that KIT_MANIFEST.json records"
status: done
confirmed: "2026-10-29 (brief relayed by the Stratics kit-vendoring session, dev-game-studio/stratics#2927; the owner's merge confirms it)"
issue: "#104"
pr: "#105"
---

# KIT-017 — sync-project.sh keeps the profile list that KIT_MANIFEST.json records

## Problem and evidence

[FACT] KIT-016 (#103, kit `main` 139814f) lets `--profile` take a comma list and records the normalized list as
`profile` in `.claude/skills/KIT_MANIFEST.json`. Only the vendored mode was read back from the manifest: without
`--profile`, `platforms/tools/sync-project.sh` still inferred one profile (`project.godot`, then `pom.xml`, then
`docs/spec/`).

[FACT] The Stratics monorepo vendored the kit with `sync-project.sh --profile docs,godot:client,java:server
--vendor-skills` (dev-game-studio/stratics#2927). Its `.github/agent-kit/README.md` warns that every run must pass the
list, because a bare run forgets it.

[FACT] Reproduction on kit `main` 139814f: a fixture with docs at the root, `client/project.godot` and
`server/pom.xml`, synced with `--profile docs,godot:client,java:server --vendor-skills`. A bare `sync-project.sh
--check <repo>` exits 1 with:

```
sync: profile=docs (inferred)
sync: skills=vendored
sync: .claude/rules/dev-godot-godot.md is generated but not in profile
sync: .claude/rules/dev-java-java.md is generated but not in profile
sync: .claude/skills/KIT_MANIFEST.json profile='docs,godot:client,java:server' expected 'docs' (pass --profile or resync)
sync: .claude/skills manifest skills differ from profile docs (extra: asset-import,characterization-tests,code-standards,docker,git-lfs,godot-standards,investigate,java-standards,postgresql,redis,secure-development,testing,twelve-factor,update-docs,vuln-scan)
```

A bare write run with the same inference removes both rules and those 15 vendored skills, and records `profile='docs'`.

## Change

- `platforms/tools/sync-project.sh`:
  - The profile comes from the first source that has one: `--profile`, then the `profile` that
    `.claude/skills/KIT_MANIFEST.json` records, then inference. A repository without a manifest (every non-vendored
    one) keeps inference unchanged.
  - New `manifest_profile` reads the recorded value. A missing or unreadable manifest, a non-object manifest or a
    missing or non-string `profile` yields nothing, so inference decides.
  - The recorded value goes through `normalize_profile` like an explicit one. An invalid recorded list exits 2 with
    "sync: .claude/skills/KIT_MANIFEST.json records that profile; pass --profile to replace it", before any write.
  - Every run prints the source next to the resolved list, as `skills=vendored` is printed:
    `sync: profile=<list> (--profile)`, `(manifest)` or `(inferred)`. The inferred line is unchanged.
  - An explicit `--profile` still wins: `--check --profile docs` reports the recorded list as divergent, and a write
    run with it replaces the list in the manifest.
- `platforms/ci/validations/test_sync_project.py`: `test_manifest_profile_list_is_sticky` (bare `--check` exits 0,
  bare write run leaves every `.claude/` file byte-identical), `test_explicit_profile_overrides_manifest` (`--check
  --profile docs` exits 1, a write run with it removes the Godot rule and skills and records `docs`) and
  `test_manifest_without_valid_profile` (no recorded `profile` falls back to inference; `docs,rust` exits 2 with the
  repository unchanged).
- `platforms/tools/smoke.sh`: the KIT-016 multi-profile case also runs a bare `--check` (exit 0, `(manifest)`
  reported) and a bare write run (hashes unchanged) under bash 3.2 with the restricted `PATH`.
- `platforms/tools/INDEX.md` and `docs/projects.md`: the profile source order.
- `CHANGELOG.md`: a `### Changed` line.

## Options considered

| Option | Verdict |
|---|---|
| A. Read the recorded list back when `--profile` is absent (chosen) | Same rule as the vendored mode; the manifest already stores the normalized list, so nothing new is written |
| B. Keep inference and leave the warning in each project's README | Every operator and agent must remember the list; one bare run deletes rules and skills |
| C. Record the list in `.claude/settings.json` too, so non-vendored repos are sticky as well | Adds a non-standard key to a file Claude Code owns; no non-vendored multi-profile repository exists today |

Limit: a repository that does not vendor its skills has no manifest, so a multi-profile list there still has to be
passed on every run.

## Proof

- Baseline: the reproduction above, with `origin/main`'s `sync-project.sh` (139814f) on the same fixture.
- `bash platforms/tools/check.sh` (also with `CI=1`): OK (14 plugins, 46 skills, 3 rules, 22 templates, 23 indexes,
  112 links, 12 hook cases).
- `bash platforms/tools/smoke.sh`: "smoke: OK (46 skills, app fallback, cleanup, symlink safety, manifests,
  sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
- `/opt/homebrew/bin/python3.12 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: 70 tests OK
  (1 skipped), three new in `test_sync_project.py`.
- `python3 platforms/ci/validations/check_kit.py --links` and
  `shellcheck platforms/tools/*.sh platforms/kits/*/*.sh platforms/kits/*/scripts/*.sh`: clean.

## History

- 2026-10-29: confirmed (brief relayed by the Stratics kit-vendoring session). Implemented in #105.
