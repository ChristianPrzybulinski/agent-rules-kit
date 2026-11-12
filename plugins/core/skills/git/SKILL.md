---
name: git
description: "Branch, commit, PR, `gh`, release and LFS policy. Use when creating a branch, commit, PR or release, or adding a large binary. Not for PR gates (skill review)."
argument-hint: "[branch | commit | pr | release | lfs init | lfs audit | lfs migrate <pattern>]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - edit
---

# Git and GitHub

Branch, commit and version policy (§1–§5), the `gh` workflow (§6–§9) and Git LFS (§10).

## 1. Start from releasable main

`main` is the only long-lived branch and stays green. Update it, then create `feature/FEAT-nnn-name` (`fix/`, `docs/`, `chore/` for non-features). Do not create develop or release branches. `spike/<topic>` is the only exception: it is time-boxed (skill sdd-spike), never merged to `main`, and deleted after its report.

## 2. Keep incomplete work safe

- Merge incomplete behavior only behind a flag defaulting off and recorded in the FEAT.
- A flag continuously on for more than 30 days creates a `DEBT-nnn` removal item.
- Security or integrity rules never hide behind a flag.

## 3. Commit atomically

Use `<type>(<scope>): <imperative description>` with `Refs: FEAT-nnn`, `Closes #n` or `BREAKING CHANGE:` as applicable. One commit represents one coherent change; no AI attribution in the title (a co-author footer only if the project requires it). The squash commit body states why, what changed and the proof (the command and its result).

## 4. Integrate without rewriting history

Except for `spike/` branches, rebase the feature onto current `main`, run gates, then use a squash PR so one feature becomes one main commit. Never force-push or rewrite public history without explicit authorization; if an authorized feature-branch rebase requires it, use `git push --force-with-lease`, never plain `--force` and never on `main`.

## 5. Select versions

- SemVer: breaking change → MAJOR, compatible feature → MINOR, fix → PATCH; tag `vX.Y.Z` on `main`.
- Pre-release uses `-alpha.N` until releasable.
- Client/server `protocol_version` is a separate integer: compatible optional fields keep it; incompatible changes increment it and require an explicit compatibility window.

## 6. Check local and remote state

Run `git status` and identify the branch/remote. Distinguish connectivity failures from authentication failures:

- DNS errors, timeouts, or `error connecting to api.github.com` do not establish invalid credentials. For authorized reads, use the GitHub connector when it supports the operation; otherwise request narrowly scoped sandbox escalation for the exact CLI command. Do not change persistent permissions.
- Check `gh auth status` through a working network path. Ask the user to run `gh auth login` only when the result establishes missing or invalid authentication. A permission or rate-limit error alone does not justify logging in again.
- Never print `GH_TOKEN` or `GITHUB_TOKEN`. Do not blindly retry mutations after an ambiguous failure; first check whether the operation took effect.

## 7. Create the PR

Run required local gates, then use `gh pr create`. The body states what changed, why, exact test commands/results and linked issues (`Closes #n`/`Refs: FEAT-nnn`). Do not use a generic generated body without evidence.

Then wait for the PR checks (`gh pr checks <n> --watch`) and add each check's name and conclusion to the PR. A failing check opens that report; never omit it. Local gates do not replace CI-only gates such as dependency or secret scans, so the PR is not done while a check is red.

## 8. Review and merge

- Inspect `gh pr checks`, `gh pr view` and review comments.
- Resolve findings and rerun affected gates before merge.
- Merge only after required approvals/checks, using the repository's squash policy.

## 9. Publish a release

After `VERSION` and CHANGELOG are ready under §5, use `gh release create vX.Y.Z` with curated notes or the approved changelog excerpt; verify the resulting tag/release.

## 10. Track binaries with Git LFS

Before editing `.gitattributes`, adding or migrating a large binary or checking quota, read `references/git-lfs-and-binaries.md` (file policy, init, audit, migration, report) and `references/lfs-quotas-github.md` (current quota facts).

Done when: the change has a short-lived branch, atomic Conventional Commits, green squash PR, safe flag state and justified app/protocol versions; authentication is valid, the PR body contains evidence, every PR check is reported by name and passes, reviews pass, merge follows policy and any release matches its approved version/tag; LFS work meets the Done line of its reference.
