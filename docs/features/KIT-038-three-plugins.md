---
id: KIT-038
title: "Three plugins by audience: core, dev and sdd"
status: done
confirmed: "2026-11-11 (owner, chat of the kit review session: \"Sim, Fase 2\")"
issue: "#151"
pr: "#153"
---

# KIT-038 — Three plugins by audience: core, dev and sdd

## Problem and evidence

[FACT] The owner asked on 2026-11-11 for a review of the kit that removes duplication and complexity, and named "too
many plugins" first. Phase 2 of the approved proposal merges the plugins; phase 1 (KIT-037) cut evals and templates
first so fewer files move.

Measured at `origin/main` 1edc0ab:

- 14 plugins: `core`, `quality-core`, `quality-security`, `infra-github`, `infra-core`, `infra-persistence`,
  `dev-core`, `dev-java`, `dev-godot`, `architect-core`, `architect-sdd`, `process-loop`, the manifest-only `all`
  bundle and the opt-in `extras`.
- 42 manifest files (three per plugin) and a `requiredPlugins`/`dependencies` chain (`dev-java` → `dev-core` → `core`)
  that `check_kit.py` had to keep valid, plus an `OPTIONAL_PLUGINS` list for `extras`.
- Every consumer installed `all` anyway: the README told Devin, Codex and Claude users to install it, and
  `sync-project.sh` mapped a Godot repository to 5 plugins, a Java repository to 8 and the spec repository to 5.
- `process-loop` (4 skills, 2 templates) serves only the Stratics review loop, and DPRO-011 amendment 2026-11-01d keeps
  the loop tool in that project.
- `extras` held `dbeaver`, `find-skills`, `frontend-design`, `skill-creator` and `krita`; only `krita` is used by a
  project (the Godot asset pipeline).

## Change

- `plugins/` holds three plugins:
  - `core` (11 skills): `core` + `quality-core` + `quality-security` + `infra-github`, so review, security and the
    GitHub workflow load in every repository.
  - `dev` (14 skills, rules `java.md` and `godot.md`, requires `core`): `dev-core` + `dev-java` + `dev-godot` +
    `infra-core` + `infra-persistence` + `krita`.
  - `sdd` (13 skills, rule `spec.md`, the `researcher` profile, requires `core`): `architect-core` + `architect-sdd`.
- Removed: `all`, `extras` (with `dbeaver`, `find-skills`, `frontend-design`, `skill-creator`) and `process-loop`, whose
  skills move into stratics-docs `.claude/skills/` in a Stratics PR that merges before this one (the `null` rename
  uninstalls `process-loop` at the next session start).
- `.devin-plugin/plugin.json` requires the three plugins and lists none as optional; both marketplaces list them.
- `.claude-plugin/marketplace.json` gains a `renames` map from every retired name to its successor (`null` for `all`,
  `extras` and `process-loop`) and `forceRemoveDeletedPlugins: true`. Checked in a sandbox on Claude Code 2.1.287:
  many-to-one and `null` renames work, `enabledPlugins` is rewritten in every scope, and a renamed plugin loads after
  one `claude plugin install <name>@ai-kit`.
- `bootstrap.sh`, `refresh.sh` and `doctor.sh` loop over `plugins/*` and install a missing plugin, so the rename lands
  without a manual step.
- `sync-project.sh` maps `godot` and `java` to `core dev` and `docs` to `core sdd`. Rules still load only by their own
  file glob.
- `check_kit.py` requires every plugin in the meta-plugin, sorted, with no `optionalPlugins`; `OPTIONAL_PLUGINS` is
  gone.
- `INDEX.md`, `README.md`, `docs/design.md`, `docs/projects.md`, `docs/maintenance.md`, the kits under
  `platforms/kits/`, `skills.lock` and `evals.yml` name the new plugins.

Trade-off: a Godot repository now vendors the Java, Docker, twelve-factor, PostgreSQL and Redis skills, and a Java
repository the Godot, asset-import and Krita skills. Their descriptions sit in the skill list; the Java rule never
loads in a Godot repository, because its glob never matches. Splitting `dev` again would bring back the manifests and
the dependency chain for those few lines.

## Proof

- `python3 platforms/ci/validations/check_kit.py --links`: OK (3 plugins, 38 skills, 3 rules, 11 templates,
  24 indexes, 125 links, 25 hook cases).
- `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: 94 tests OK, 1 skipped.
- `bash platforms/tools/check.sh` and `claude plugin validate`: passed for every manifest and both marketplaces.
- `bash platforms/tools/smoke.sh`: `smoke: OK (38 skills, ...)`, after its `godot,java` check moved from a
  9-plugin to a 2-plugin union (`core`, `dev`).
- `git grep` for the 14 old names outside `CHANGELOG.md`, `docs/features/` and `docs/plans/` finds only the `renames`
  map and the generated rule names `dev-godot.md`/`dev-java.md` (plugin `dev`, rules `godot`/`java`).

## History

- 2026-11-11: confirmed (owner, "Sim, Fase 2").
