---
id: KIT-080
title: "13.1.0 issue bundle: proof hygiene rule, release-tag install, sync, CI, merge driver and text follow-ups"
status: done
confirmed: "2026-11-16 (owner, the bundle brief: \"close the 22 open issues and release 13.1.0\")"
issue: "#300"
pr: "#301"
---

# KIT-080 — 13.1.0 issue bundle

## Problem and evidence

[FACT] After 13.0.1 the kit had 24 open issues, most of them non-blocking findings of one-round reviews (KIT-077 bar).
One PR closes those that can close inside the kit; the rest stay open with what is left (§ Left open).

## Change

1. Proof checks (#280 option a, #270, #269, #266, #288 item 7): `pr_gates.py` `command_allowed` keeps three
   component rules (`DOTDOT`, `UNPREDICTABLE`, `INLINE_CODE`) instead of the spelling cases; `row-checks.md` says they
   are hygiene, not isolation. `row_checks.py` rule e fails an evidence-only Proof unless `row_checks.evidence_only`;
   rule c names every missing stack; the schema and `sdd-parameters.md` name rule j's `visual_approval`.
2. `spec_trace.py` (#265, #267, #268, #282 item 2): `check` honours `check_spec.py`'s `baseline.json` for one-sided
   FEAT↔REQ links; `sync-status` exits 2 on a `gh` failure or a missing backlog and reads the KIT-068 `Item` cell; the
   pin copies `platforms/ci/schemas/` beside the spec tools.
3. `review_checks.py dod` (#277, #288 items 2, 5, 6, 8) skips a match wholly inside a string literal of a test file.
   #288 item 5, the `needs-off` narrowing to NEED files, is intended and documented.
4. CI (#279, #294, #283 items 6, 7): `test_kit_workflows.py` catches `write-all`, an unlisted job write, a `.yaml`
   workflow and a piped download; Claude Code installs as 2.1.311 by sha-256; `red` reads the PR body through the API
   (`pull-requests: read`), runs the PR's tests without the job's tokens, and times out at 25 min (3 × 460 s, run
   43817751313); `VERSION` and the root manifests run the whole integration layer; `ci-godot.yml` runs `just --no-deps
   test`; `spec-lint.yml` runs the vendored `check_docs_structure.py`. `pull_request` keeps its default types without
   `edited` (#279): an edit would re-run every required job, and `red` reads the current body when it runs.
5. Sync (#271, #299, #282 items 1, 4): see § Release-tag install; the `--check` scans skip `CHANGELOG.md`; in vendored
   mode the location lines name `.claude/skills/guardrails-pinned/skills/<skill>/`; `$HOME/.ai-kit/platforms/` calls are
   pinned and rewritten without inner quotes.
6. `keyed_csv_merge.py` (#283 items 3, 4, 8; stratics#4545 item 4): `records()` reads through `csv.reader` and keeps
   each record's raw text, so `5" screen` merges by key; an open quote at the end still falls back to the text merge.
   The module text states the base-only duplicate and the dropped blank lines. `RECIPE` and `JUST_RECIPE` accept
   variadic, exported and defaulted parameters.
7. Hooks (#274): the `InstructionsLoaded` hook takes `flock` on `instructions-loaded.jsonl.lock` around the size check,
   the rotation and the append.
8. Text (#287, #276, #245, #291, #298, #282 item 3): `PARTIAL` is a declared partial delivery; `review_rounds` is a
   ceiling (default kept: the owner has not decided Stratics' round count); the reviewer runs nothing beyond the
   recorded-result rule; `sdd-plan` § 5 settles decisions from the frontier, one per question; `AGENTS.md` loads
   `sdd-intake` for a new idea in a spec repository, joined into an existing line (60 of 60 lines); the godot rule
   says `*.translation` follows the project's rule, ignored by default; #291 compacts CONTRIBUTING, delivery-steps,
   `sdd-process.md`, the review-loop README and the KIT-034/035 records, adds a hooks table and an index column. The
   PR #260 body gained a corrections section. #291 item 10, a character cap for references, is not added: the
   compaction cut the longest `delivery-steps.md` line from 2,170 to 774 characters, and a cap needs a measured
   baseline over every reference first.
9. Evals (#275, #245): five `rule` cases (`code`, `godot`, `java`, `protocol`, `tests`) whose scaffold copies the kit
   rule into `.claude/rules/`, and the `sdd-intake` trigger case. The two `testing-gdscript-*` behaviours need no case:
   their tools are optional and advisory, in a user-only reference; the `parallelize` trigger case keeps its KIT-070
   reason (0.00 over 5 runs while Claude ran the checks in parallel without the skill).
10. #241, the kit part: the review-loop kit README names the `skills:` preload with plugin-qualified names.

### Release-tag install (#271)

One always-on file serves every project on a machine, so it cannot be pinned per project; #271 accepts a release tag.
`platforms/tools/kit-release.sh` (sourced) holds `kit_release_tag` (the newest `vX.Y.Z` on `origin/main`) and
`codex_kit_ref`. `bootstrap.sh` clones at the tag; `refresh.sh` fetches tags and checks the clone out detached at the
tag, and moves the Codex marketplace ref with a remove, an add and a fresh `codex plugin add` per kit plugin
([FACT] codex-cli 0.164.0 in a throwaway `CODEX_HOME`: a second `marketplace add` with another ref is refused until
a remove; re-adding the plugin replaces its cache version); `doctor.sh` fails when the clone, the Codex ref or
Devin's ref is off the release. Devin keeps a team plugin's ref in its web settings, which no CLI sets.
Rejected: a per-project copy of the always-on file (both runtimes load the global file anyway, so a project would
load two versions), and an opt-in channel (the default would stay unpinned, which #271's Done-when excludes).

## Proof

[FACT] Each changed behaviour has a test that fails on the commit before its group (the PR's `## Red`); locally the
changed modules' tests, `check_kit.py`, `gen_index.py --check`, shellcheck, actionlint and zizmor pass, and the whole
`smoke.sh` passes in 86 s. Evals: written, not run: `claude plugin eval` refuses the Docker Desktop symlinks in
`~/.docker` on this Mac (CONTRIBUTING § Evals), and `evals.yml` has no `ANTHROPIC_API_KEY`.

## Left open

- #241: the consumer part needs the loop children's transcripts and waits for the loop's import into
  `dev-game-studio/review-loop` (Stratics T197 #4482).
- #273: after the release, once `~/.ai-kit` is at the new tag.
- #299, its last clause: Stratics' `sync-project.sh --check` exits 0 after its re-pin to 13.1.0 with no Stratics change;
  the re-pin is the coordinator's, so #299 stays open until that run.
- #271, Claude Code in plugins mode: its marketplace takes a ref (`owner/repo#tag`, [FACT] 2.1.287 in a throwaway
  `HOME`), but a second add with another ref is refused while the first source is declared, and
  `claude plugin marketplace remove` uninstalls the plugin and deletes its data, the rule-load log included. Plugins
  mode stays on `main` until a ref change without that loss exists; until then a plugins-mode session can read the
  release's always-on file beside the head's skills.
- #275 and #245: the cases are written; each stays open until a first eval run records its score (#245 asks for
  the trigger case's pass rate over 5 runs next to `origin/main`).
- Owner decision, optional: the repository setting `sha_pinning_required` (#279), recorded in `OWNER-TODO.md`.

## History

- 2026-11-16: confirmed (owner, bundle brief); implemented on `chore/issue-bundle-13.1`.
- 2026-11-16: done in PR #301 after one independent review round; the items above stay open in their issues.
