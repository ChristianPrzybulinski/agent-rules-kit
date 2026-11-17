---
description: Resolves the project profile (.ai-kit.yaml) and names the kit tools a skill runs, with their paths. Load at each skill's first step.
kind: detail
---

# Project profile

A project never calls a kit script and never copies a step (KIT-087): the skill reads the project's profile, `.ai-kit.yaml` at its git top level, and runs the kit's tools itself. CI, which runs no skill, uses the kit's composite actions and `$AI_KIT_DIR`.

## 1. Find the kit

`KIT` is the first of these folders that holds `platforms/tools/profile.py`, the order the hooks use (`hook_profile.py`):

1. `$AI_KIT_DIR`;
2. the kit root this plugin runs from: the folder that holds `plugins/guardrails`, two folders above this plugin's own folder, as the hooks resolve it;
3. `~/.ai-kit`, the user install `bootstrap.sh` clones.

None holds it → say so and stop; the install is missing (`bootstrap.sh`), never copy a tool into the project. In the kit's own repository `KIT` is the working tree.

## 2. Resolve the profile

Run from the project root, once per skill run:

```bash
python3 "$KIT/platforms/tools/profile.py" resolve --json [--section <name>] .
```

- Read only the sections the skill's first step names, each at its resolved value: the project's own, else the `project.kind` preset, else the schema default (`$KIT/platforms/ci/schemas/profile.schema.json`, whose `x-read-by` names each key's phase).
- `profile: <key> from legacy <path>` lines on stderr are notes: until KIT-087 P4 a key absent from `.ai-kit.yaml` still comes from its legacy home (the `sdd:` block, the `CLAUDE.md` marker, the gates JSON). A missing file is one warning, and every key keeps its legacy value or default.
- Exit 1 (an unknown key, a value outside the schema, a key set differently in two homes) → report its lines and stop; never guess a value. Fixing the profile is skill `sdd-constitution` § 4.
- `spec_root` (default `docs/spec`) is the spec folder: every step that names `docs/spec` means it.

## 3. The kit tools a skill runs

Each name below is the command a skill step writes; the path always comes from `KIT`, never from a copy in the project.

| Name | Command |
|---|---|
| `PROFILE` | `python3 "$KIT/platforms/tools/profile.py"` |
| `CHECK_SPEC` | `python3 "$KIT/platforms/ci/validations/check_spec.py" <spec_root> "$KIT/platforms/ci/schemas"` (the spec validator) |
| `TRACE` | `python3 "$KIT/platforms/ci/validations/spec_trace.py"` |
| `ROWS` | `python3 "$KIT/platforms/ci/validations/row_checks.py"`, unless `sdd.row_check` names the project's own command |
| `RC` | `python3 "$KIT/platforms/tools/review_checks.py"` |
| `COMPLEXITY` | `python3 "$KIT/platforms/tools/complexity.py"` (advisory) |
| `GD_COVERAGE` | `python3 "$KIT/platforms/tools/gd_coverage.py"` (advisory) |
| `GD_MUTATION` | `python3 "$KIT/platforms/tools/gd_mutation.py"` (advisory) |
| `GD_DUPLICATES` | `python3 "$KIT/platforms/tools/gd_duplicates.py"` (advisory) |
| `AUDIT` | `python3 "$KIT/platforms/tools/session_audit.py"` |
| `SYNC` | `"$KIT/platforms/tools/sync-project.sh"` |
| a stack recipe | `just -f "$KIT/platforms/kits/just/<stack>.just" -d <folder> <recipe>` (`../../sdd-implement/references/recipes.md`) |

In the kit's own repository the spec gate is `platforms/tools/check.sh --spec <spec_root>`, which runs the same validator.
