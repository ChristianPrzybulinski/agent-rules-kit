---
id: KIT-039
title: "Merge overlapping skills: 38 become 27"
status: done
confirmed: "2026-11-11 (owner, chat of the kit review session: phase 3 list approved)"
issue: "#154"
pr: "#155"
---

# KIT-039 — Merge overlapping skills: 38 become 27

## Problem and evidence

[FACT] Phase 3 of the kit review the owner approved on 2026-11-11 merges skills that cover one topic. Measured at
KIT-038's head `62b2035` (three plugins):

- 38 skills, 26 of them model-invocable, so 26 descriptions sit in every session's skill list.
- Pairs pointed at each other in their `Not for` clause because they were halves of one topic: `postgresql` ↔ `redis`,
  `secure-development` ↔ `vuln-scan`, `branching-and-versioning` ↔ `github-cli` (and `git-lfs` → `branching-and-versioning`),
  `docker` ↔ `twelve-factor`, `testing` ↔ `characterization-tests`, `tokens` → `update-docs`.
- `validate-implementation`, `review-gates` and `skeptic` each verified a claim someone else made; the first two both
  read a PR's proof.
- `collab-two-humans` was ten condition → action rows that only matter when `session` starts with a second human.
- Rule `dev/rules/godot.md` (27 lines) repeated three passages of skill `godot-standards`: `get_node` in `_process`, the
  movement model and the `.tscn`/UID conflict.

## Change

Every rule is kept; only true repeats are dropped. Skill and reference limits (80 and 60 lines, 160-character
descriptions) hold.

- `core/skills/review` (fork, `reviewer` profile) = `validate-implementation` (completion verdict, §1–§4) +
  `skeptic` (`references/claim-check.md`) + `review-gates` (`references/pr-gates.md`), chosen by argument.
- `dev/skills/testing` absorbs `characterization-tests` as `references/characterization.md`.
- `core/skills/security` = `secure-development` (design rules, §1–§6) + `vuln-scan` (`references/scan.md`, run with a
  scope argument).
- `dev/skills/docker` absorbs `twelve-factor`.
- `dev/skills/persistence` = `postgresql` + `redis`; `references/postgres-18.md` and `references/redis-7.md` move as is.
- `core/skills/git` = `branching-and-versioning` (§1–§5) + `github-cli` (§6–§9) + `git-lfs` (§10 and its two
  references). `platforms/kits/git-lfs/` stays and points at the new reference paths.
- `core/skills/session` takes `collab-two-humans` as `references/two-humans.md`, loaded when a second human joins.
- `tokens` is deleted: the conclusion-first, tag and final-format lines go to `core/AGENTS.md` § Craft; the
  read-only-what-the-outcome-needs and bulk-output-to-a-subagent-or-file lines go to `parallelize` § 2; prose for
  people goes to `code-standards` `references/living-docs.md`.
- `update-docs` folds into `code-standards` § 9 (`references/living-docs.md`); its Done line adds the docs closure.
- `dev/rules/godot.md` drops the three passages above and the clauses that only named other skills (27 → 24 lines).
- The two eval cases follow their skills: `core/evals/review-claimed-proof-not-rerun` and `core/evals/git-squash-body`.
- References to the old names move to the new ones in `AGENTS.md`, the `sdd-*` skills, `asset-import`, `krita`,
  `docs/maintenance.md`, `INDEX.md` and the three plugin `INDEX.md` files.

Behavior that changes:

- `vuln-scan` was user-only and ran forked as `reviewer`; its scan now runs inside `security`, which the model may load,
  in the calling context.
- `skeptic` ran in the calling context; a claim check now runs forked in `review` with the claim as its argument.

Out of scope: `sdd-clarify`/`sdd-check`, manifests and marketplaces (KIT-038), INDEX generation (KIT-040).

## Proof

- `python3 platforms/ci/validations/check_kit.py --links`: OK (3 plugins, 27 skills, 3 rules, 11 templates,
  24 indexes, 127 links, 25 hook cases).
- `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: 94 tests OK, 1 skipped.
- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: passed for every manifest and both
  marketplaces.
- `bash platforms/tools/smoke.sh`: `smoke: OK (27 skills, ...)`.
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: no leaks found.
- Skill counts from `git ls-tree` and the frontmatter: 38 → 27 skills, 12 → 11 user-only, 26 → 16 model-invocable.
- `claude plugin eval plugins/core --case <name> --runs 1 --ablation none --no-publish --trust-plugin` (Claude Code
  2.1.287): `git-squash-body` and `session-closeout-no-rerun` pass. `review-claimed-proof-not-rerun` scores 0.33:
  `skill-fired` passes, `reran-proof` and `verdict` fail because the case grants no Bash; the base's
  `validate-implementation-claimed-proof-not-rerun` scores the same on this host, so the gap predates KIT-039.
- Unverified: the `dev` cases of `testing` and `code-standards`; KIT-038 records that every `dev` case fails
  `skill-fired` with `dependency-unsatisfied` for `core`.

## History

- 2026-11-11: confirmed (owner, phase 3 list).
- 2026-11-11: done in #155 (stacked on #153).
