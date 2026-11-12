---
id: KIT-045
title: "Python files get a path rule, and a python profile scopes it in a monorepo"
status: confirmed
confirmed: "2026-11-11 (owner's kit review: Java, Godot and Python first; recommendations approved in chat until revoked)"
issue: "#167"
pr: ""
---

# KIT-045 — Python files get a path rule, and a python profile scopes it in a monorepo

## Problem and evidence

[FACT] At `cb2b07b` the kit had `plugins/dev/rules/java.md` and `plugins/dev/rules/godot.md` and no rule for Python,
which the owner named as the third focus language of the 2026-11-11 kit review. The review of the top 100 repositories
of `quemsah/awesome-claude-plugins` proposed a Python path rule independently in batches 1, 5 (mlflow `python-style`,
verdict adopt) and 9.

[FACT] In Stratics, 639 tracked `.py` files live under `platform/` and 8 under `server/scripts`. Its profile
`docs,godot:client,java:server` gives a dev rule that is not named after a profile the folders of every profile that
includes plugin dev (`rule_scopes` in `sync-project.sh`), so a Python rule alone would render as `client/**/*.py` and
`server/**/*.py` and never load for the review loop or the tools. Measured in `platform/`: `pathlib` in 512 files,
`encoding="utf-8"` in 288, `unittest` in 430 and `pytest` in 0, `shell=True` in 0, `# noqa: E402` after a `sys.path`
insert in about 490 lines. The owner's loop needs Python 3.12 while the macOS `python3` is the Xcode 3.9.

## Change

- New `plugins/dev/rules/python.md` (glob `**/*.py` and `**/pyproject.toml`): interpreter the repo names, standard
  library first, type hints on new or changed signatures, `pathlib` and `encoding="utf-8"`, `subprocess.run` with a
  list and a checked return code, no mutable defaults, narrow `except` with `raise ... from err`, no `assert` for input,
  safe parsing of outside data and `python3 -I` for downloaded files, named `# noqa` codes, the repo's own test
  framework and its literal test tail before "done".
- `platforms/tools/sync-project.sh`: profile `python` (plugins core and dev). `python:<dir>` scopes `rules/python.md` to
  that folder the way `godot:client` scopes the Godot rule; the profile can repeat for several folders.
- `platforms/ci/validations/test_sync_project.py`: the monorepo rule list gains `dev-python.md`;
  `test_python_profile_scopes_the_python_rule` renders `platform/**/*.py` and `tools/**/*.py`, leaves `client/` out of
  the Python rule and `platform/` out of the Godot and Java rules, and `--check` passes with the list in another order.
- `plugins/core/AGENTS.md` Craft line: "`rules/` loads the Java, Godot and Python sets by file glob."; `README.md`,
  `docs/projects.md` and `platforms/tools/README.md` name the profile.

A consumer adds `python:<dir>` to its profile on its next sync (Stratics: `python:platform`).

## Proof

- `test_python_profile_scopes_the_python_rule` fails with `sync: unknown profile 'python'` when `python` is removed from
  `normalize_profile`, and passes with it.
- Kit gates: see the PR body.

## History

- 2026-11-11: confirmed (owner's kit review); issue #167.
