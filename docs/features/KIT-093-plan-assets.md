---
id: KIT-093
title: "The FEAT Plan gains an Assets section, checked by sdd-check C15"
status: in-progress
confirmed: "2026-11-16 (owner, chat of the kit session: \"concordo\" with the game-profile evaluation §§ 1-5 and 8.2-8.4, filing \"Sim, abra\"; the E § 17 scope, \"Sim, faça\")"
issue: "#334"
pr: ""
---

# KIT-093 — The FEAT Plan gains an Assets section, checked by sdd-check C15

## Problem and evidence

[FACT] The game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace, "E"),
§§ 2 (stage 3), 9.1 and 17, backlog id G4:

1. No SDD step lists the assets a FEAT needs before the cut: `sdd-implement` `references/assets.md` covers the import
   only, so art, sound and particles surface in task rows, too late to make or buy them (E § 2, stage 3). Stratics
   wrote such a list by hand in its FEAT-039 scope (three CC0 tracks with pinned SHA-256).
2. KIT-088 (6c8fa0f) put `Assets` in the `plan_sections` enum of `spec.schema.json` and `profile.schema.json`, off by
   default and on in the `game` preset, but no skill or template writes the section.
3. Rejected: assets inside Plan § UI (sound and particles are not UI, and a business project would carry them in an
   empty UI section); assets in task rows only (the list appears after the cut).

## Change

- `plugins/guardrails/skills/sdd-plan/references/plan-sections.md`: the `Assets` row in the section table (between UI
  and Flag, as in the enum), the row format `| Asset | Kind | Source | License | Serves |` with a game and a business
  reading of Kind and one example, and the default now "all but `Assets`".
- `plugins/guardrails/templates/spec-feature.md`: a `### Assets` section with that table header and a comment that it
  is written only when `sdd.plan_sections` lists `Assets`.
- `plugins/guardrails/skills/sdd-plan/SKILL.md` § 4: `Assets` in the section order (only when listed), its reference
  row and one bullet (game: animations with frame counts, particles, sounds; business: e-mail templates, copy, icons,
  translations; each with source, license and the REQ or mock it serves).
- `plugins/guardrails/skills/sdd-implement/references/assets.md`: the import starts from the Plan § Assets rows, linked.
- `plugins/guardrails/skills/sdd-check/SKILL.md`: row C15 at the end of the C table, "a Plan § Assets row without its
  source, its license or the REQ or mock it serves (full scope)", severity medium, and C15 in the full scope's list.
- No validator change: `check_spec.py` and the spec schemas validate the `plan_sections` key, which already accepts
  `Assets`, and no FEAT body section.
- Not here: "`sdd-tasks` rows import the listed assets" (issue scope) needs an `sdd-tasks` line, left to a follow-up
  because KIT-086 edits `sdd-tasks` in parallel.

## Proof

[FACT] On branch `feat/kit-093-plan-assets`, macOS:

- `check.sh` and `check.sh --links`: `check: OK (1 plugins, 18 skills, 11 rules, 13 templates, 15 readmes, 161 links,
  63 hook cases, 18 shell scripts)`, `plugin indexes are current`; `plan-sections.md` stays at 57 lines (cap 60).
- `python3.12 -B platforms/tools/run_tests.py --layer unit,contract`: `Ran 270 tests`, `OK (skipped=16)` (gdtoolkit);
  `--layer integration --changed-from origin/main`: `Ran 91 tests`, `OK (skipped=1)` (a non-UTF-8 file name this file
  system refuses).
- Evals: no case covers `sdd-plan`, `sdd-check` or `sdd-implement`, so the `trigger` suite ran: `claude plugin eval
  plugins --tag trigger --runs 1 --ablation none --no-publish --trust-plugin --scaffold` (Claude Code 2.1.287): six
  cases, each 1.00.
- Not run: `sdd-check` C15 against a real game FEAT with an `Assets` section (no consumer uses the section yet).

## History

- 2026-11-16: confirmed (owner, kit chat; issue #334 and its E § 17 update).
- 2026-11-16: implemented on `feat/kit-093-plan-assets`.
