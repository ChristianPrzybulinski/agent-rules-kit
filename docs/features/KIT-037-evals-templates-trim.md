---
id: KIT-037
title: "Eight trigger eval cases and no doc-* templates in plugins"
status: done
confirmed: "2026-11-11 (owner, chat of the kit review session: \"Sim, Fase 1\")"
issue: "#148"
pr: ""
---

# KIT-037 — Eight trigger eval cases and no doc-* templates in plugins

## Problem and evidence

[FACT] The owner asked on 2026-11-11 for a review of the kit that removes duplication and complexity, and asked
whether the `evals/` folders and the templates inside the plugins earn their place. Phase 1 of the approved proposal
cuts both before phase 2 merges the plugins, so fewer files move.

Eval cases, measured at `origin/main` 770af57:

- 61 cases in 8 plugins: architect-core 6, architect-sdd 6, core 8, dev-core 17, dev-godot 4, dev-java 3,
  infra-github 6, quality-core 11.
- `.github/workflows/evals.yml` has never run (`gh run list --workflow evals.yml` returns 0 runs) and the repository
  holds no secret (`gh secret list` is empty), so no case ran in CI. Local runs need a logged-in CLI (KIT-036).
- In the 31 commits since 2026-10-15, eval files took 1,080 of 5,972 changed lines (18.1%) and 127 of 455 file
  changes (27.9%), because § Evals required three cases for every new or changed skill.
- `claude plugin eval --help` on Claude Code 2.1.287 reads "`--eval-dir <dir>` Directory name (below the plugin) that
  holds the eval cases", so the kept cases cannot move to a root `tests/evals/` as the proposal said; they stay in
  `plugins/<plugin>/evals/`.

Templates, measured at the same commit:

| Template | Lines | Linked from |
|---|---|---|
| `dev-core/templates/doc-bug-report.md` | 31 | skill `investigate`, whose line already named the six fields |
| `dev-core/templates/doc-load-test.md` | 40 | nothing |
| `quality-core/templates/doc-review-checklist.md` | 34 | `platforms/kits/github/README.md`, for its five criteria |
| `architect-core/templates/doc-contract-message.md` | 44 | skill `protocol-contract`, whose § 3 already listed the fields |
| `dev-godot/templates/doc-recovery-report.md` | 40 | skill `asset-import`, whose line already named the counts |

- The vendored copies of `investigate`, `asset-import` and `protocol-contract` in stratics-docs, stratics-client and
  stratics-server link `../../templates/doc-*.md`, but none of those repositories holds `.claude/templates/`: the
  links are already dead there.
- `kit-index.md`, `kit-readme.md`, `kit-reference.md` and `kit-skill.md` shape kit content (an INDEX, a README, a
  reference, a skill), not project content, yet they shipped in the `core` plugin to every project.

## Change

- Eval cases: 61 → 8. One trigger case stays for each of eight critical skills (the proposal kept "up to 8 cases for
  the critical skills"): `core/session-closeout-no-rerun`, `quality-core/validate-implementation-claimed-proof-not-rerun`,
  `infra-github/branching-squash-body`, `dev-java/java-standards-no-field-injection`,
  `dev-godot/godot-standards-boot-exit-code`, `dev-core/code-standards-one-decision-one-place`,
  `dev-core/testing-empty-return-passes` and `architect-core/protocol-contract-required-field-bumps-version`.
  `plugins/architect-sdd/evals/` is gone.
- `docs/maintenance.md` § Evals replaces the three-case rule:

  > A change to the `description` of one of those eight skills reruns its case by hand before the PR. A new skill, or a
  > change to another skill, needs no case (KIT-037).

- `.github/workflows/evals.yml` (manual only) runs the seven plugins that still hold a case.
- Templates: the five `doc-*` files above are deleted. `investigate`, `asset-import` and `protocol-contract` write their
  fields inline (`protocol-contract` § 3 gains the header line and the one-sentence purpose that only the template
  had); `platforms/kits/github/README.md` names the five criteria. The four `kit-*` files move to `docs/templates/`
  with an `INDEX.md`; the `templates/` folders of architect-core, dev-core and quality-core are gone.
- `docs/maintenance.md`: a template exists only for a long artifact a skill links (a spec, a project `AGENTS.md`); a
  short field list goes inline in the skill.
- `platforms/ci/validations/check_kit.py`: a plugin template name matches `^(spec|doc|project)-[a-z0-9-]+\.md$`
  (`kit-` is no longer a plugin prefix), and the link check skips the placeholder links of `docs/templates/kit-*.md`.
- Plugin `INDEX.md` files and the root `INDEX.md` list what remains: 13 plugin templates (11 after phase 2 moves the
  two loop templates to Stratics).

`CHANGELOG.md` gains one line under `[Unreleased]`; `VERSION` does not change.

## Proof

- The counts above: `git ls-tree` of `plugins/*/evals/` and `git log --numstat` at `origin/main` 770af57; `gh run
  list --workflow evals.yml` and `gh secret list`; `claude plugin eval --help` on Claude Code 2.1.287.
- Gates on 2026-11-11 at this branch, from the worktree root:
  - `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: exit 0, "check: OK (14 plugins,
    46 skills, 3 rules, 13 templates, 24 indexes, 136 links, 25 hook cases)" and "✔ Validation passed" (KIT-036: 22
    templates, 23 indexes, 123 links).
  - `bash platforms/tools/smoke.sh`: exit 0, "smoke: OK (46 skills, app fallback, cleanup, symlink safety, manifests,
    sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
  - `python3 platforms/ci/validations/check_kit.py --links`: exit 0, the same "check: OK" line.
  - `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: exit 0, "Ran 94 tests", "OK
    (skipped=1)".
- Not run: the eight kept cases. Their prompts and graders did not change, and the CLI is logged out on this machine
  (KIT-036).

## History

- 2026-11-11: confirmed (owner, chat, "Sim, Fase 1"); issue #148. The proposal put the kept cases in `tests/evals/`;
  the CLI reads cases only below a plugin, so they stay in `plugins/<plugin>/evals/`.
