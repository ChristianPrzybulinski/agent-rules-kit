---
id: KIT-019
title: "One command bumps every version field for a kit release"
status: done
confirmed: "2026-10-29 (owner, chat of the kit 11.1.0/11.2.0 release session)"
issue: "#110"
pr: ""
---

# KIT-019 — One command bumps every version field for a kit release

## Problem and evidence

[FACT] A kit release sets one version in three places:
- `VERSION`;
- 57 `"version"` fields across 44 tracked `*plugin.json` and `*marketplace.json` files (`git grep -c '"version": "11.2.0"' origin/main -- '*plugin.json' '*marketplace.json'` at `87e74d5`);
- a `## [X.Y.Z] - YYYY-MM-DD` heading under `## [Unreleased]` in `CHANGELOG.md`.

`platforms/ci/validations/check_kit.py` fails a manifest whose version differs from `VERSION` (its `!= VERSION` checks for plugin manifests, the meta-plugin and the Claude marketplace). Nothing in the kit writes those fields, though: `platforms/tools/` has no bump command, and `docs/maintenance.md` § Versioning names only `VERSION`, the CHANGELOG entry and the tag.

[FACT] On 2026-10-29 the releases 11.1.0 (#106) and 11.2.0 (#109) each needed an ad-hoc Python script in the session scratchpad. The two scripts were identical except for their `OLD, NEW, DATE` constants.

[FACT] `release.yml` did not publish either release: its tag runs were refused by GitHub billing (run 40978925050 on `v11.2.0`, conclusion `failure`). Both releases were created by hand with `gh release create vX.Y.Z --verify-tag --title X.Y.Z --notes-file <file>`, with the notes cut from `CHANGELOG.md` by hand. `docs/maintenance.md` still says the workflow "creates the release automatically" and names no fallback. The release titles drifted as a result: `gh release list` shows `v10.1.0` (the workflow's `$GITHUB_REF_NAME` title) next to `10.2.0` through `11.2.0`.

## Change

- `platforms/tools/bump_version.py X.Y.Z [--date YYYY-MM-DD]` (new, standard library only):
  - It refuses to run unless `X.Y.Z` is SemVer and greater than the current `VERSION`, the working tree is clean, and `## [Unreleased]` has at least one entry.
  - It writes `VERSION`, replaces `"version": "<current>"` in every tracked `*plugin.json` and `*marketplace.json` and prints how many fields it changed.
  - It inserts `## [X.Y.Z] - <date>` (today by default) under `## [Unreleased]`.
  - `--notes X.Y.Z` prints that version's section of `CHANGELOG.md`, with the same extraction as `release.yml`, for `gh release create --notes-file`.
- `platforms/tools/INDEX.md`: a row for the command.
- `docs/maintenance.md` § Versioning: the release steps in order:
  1. bump with the command;
  2. open the release PR `chore(release): publish X.Y.Z`;
  3. after the merge, tag `vX.Y.Z` (annotated);
  4. if `release.yml` does not create the release, run `gh release create vX.Y.Z --verify-tag` with the `--notes` output, using one title format, the workflow's `vX.Y.Z`.
- `platforms/ci/validations/test_bump_version.py` (unittest, listed in that folder's `INDEX.md`) runs on a throwaway copy. A bump leaves `check_kit.py` green; a bump to the current or a lower version is refused; an empty `[Unreleased]` is refused; `--notes` prints the section `release.yml` would print.

Not in scope: GitHub billing (owner), changes to `release.yml`, tagging or publishing from the command, and any scheduled automation.

## Proof

`bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`, `python3 platforms/ci/validations/check_kit.py --links`
and `python3 -m unittest platforms/ci/validations/test_bump_version.py`.

Then a dry bump to the next MINOR on a scratch worktree, after which `check_kit.py` passes and `git diff --stat` lists only `VERSION`, `CHANGELOG.md` and the 44 manifests.

## History

- 2026-10-29: confirmed (owner, chat: "Yes, write KIT-019").
