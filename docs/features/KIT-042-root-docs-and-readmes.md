---
id: KIT-042
title: "Root docs fold into README and CONTRIBUTING; only the generated plugin indexes stay"
status: done
confirmed: "2026-11-11 (owner's kit review, night brief items 1, 2, 3, 4 and 6; recommendations approved in chat until revoked)"
issue: "#160"
pr: ""
---

# KIT-042 — Root docs fold into README and CONTRIBUTING; only the generated plugin indexes stay

## Problem and evidence

[FACT] At `ddebe86` the repository held 14 `INDEX.md` files: the three generated `plugins/<name>/INDEX.md`
(KIT-040), the root `INDEX.md` next to `README.md`, and 10 hand-written folder indexes in `platforms/`, `docs/` and
`.github/workflows/`. `check_kit.py` section 9 only checked that every entry's name appears in its folder's index, so
`platforms/INDEX.md` still had a "How agents consume v6" table naming the `all` bundle that KIT-038 removed. GitHub
renders a folder's `README.md` in the tree view but not its `INDEX.md`, and no skill or tool reads these files.
`platforms/ci/` and `.github/` already had a `README.md` that repeated their subfolders' indexes.

The kit's contributor guide lived at `docs/maintenance.md`, linked from line 5 of `README.md` next to `INDEX.md`, so
a reader had three root files to open before a change. `docs/machine.local.md.example` asked each machine to keep a
git-ignored facts file; `~/.ai-kit/docs/machine.local.md` does not exist on the owner's Mac, and the two skill lines
that pointed at it (`godot-4-versions.md`, `java-25-lts.md`) meant a project's file, not the kit's.

The root keeps no `AGENTS.md` or `CLAUDE.md`: `check_kit.py` refuses a root `AGENTS.md` because the root is the Devin
meta-plugin (`50dbc77`), so every Devin session would load it on top of `plugins/core/AGENTS.md`.

## Change

- `docs/maintenance.md` → `CONTRIBUTING.md`, which gains "What goes where" and "Invariants" from the root
  `INDEX.md`; the invariant that every triggered rule appears in the root index is dropped (`gen_index.py` lists rules
  in the plugin index). `VERSION` stays: `check_kit.py`, `bump_version.py` and `release.yml` read it.
- `README.md` gains a version line and a Layout table (the three plugins, `platforms/`, `docs/`, the manifests,
  `.github/`), and its maintenance paragraph points at `CONTRIBUTING.md`.
- Deleted: root `INDEX.md`, `platforms/INDEX.md`, `platforms/ci/schemas/INDEX.md`,
  `platforms/ci/validations/INDEX.md`, `.github/workflows/INDEX.md`, `docs/INDEX.md`, `docs/templates/INDEX.md`,
  `docs/templates/kit-index.md` and `docs/machine.local.md.example`. Renamed to `README.md`: `platforms/tools/`,
  `platforms/kits/`, `platforms/kits/sdd/`, `platforms/kits/third-party/`.
- `check_kit.py`: `CONTRIBUTING.md` replaces `INDEX.md` among the required root paths; section 9 no longer requires an
  index per folder, checks a folder `README.md` for every entry name only when the README exists, and fails on any
  `INDEX.md` outside `plugins/<name>/`; the summary line counts `readmes`.
- Links that named `docs/maintenance.md` (`docs/design.md`, `session` skill and `kit-proposal.md`,
  `platforms/tools/README.md`) now name `CONTRIBUTING.md`; the PR template drops the index-listing clause; the two
  skill references say to check `godot --version` or `java -version` and `mvn -v` when a task needs them.

## Proof

- `python3 platforms/ci/validations/check_kit.py --links` reads
  `check: OK (3 plugins, 27 skills, 3 rules, 11 templates, 15 readmes, 74 links, 25 hook cases)`.
- `test_check_kit_readmes.py`: a copy with a new `docs/notes/` folder and no README passes; a copy with `docs/INDEX.md`, an unlisted `platforms/tools/` script and no `CONTRIBUTING.md` fails with each message (2 tests, 14 s).
- Gates: see the PR body.

## History

- 2026-11-11: confirmed (owner's kit review); issue #160.
