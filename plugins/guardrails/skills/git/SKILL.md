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

`main` is the only long-lived branch and stays green. Update it, then create `feature/FEAT-nnn-name` (`fix/`, `docs/`, `chore/` for non-features). Do not create develop or release branches. `spike/<topic>` is the only exception: it is time-boxed (skill sdd-spike), never merged to `main`, and deleted after its report. Before branching, search open PRs and branches on the topic (`gh pr list --search '<topic or #issue>'`, `git branch -r`); build on one that covers it, or name it and stop.

## 2. Keep incomplete work safe

- Merge incomplete behavior only behind a flag defaulting off and recorded in the FEAT.
- A flag continuously on for more than 30 days creates a `DEBT-nnn` removal item.
- Security or integrity rules never hide behind a flag.

## 3. Commit atomically

Use `<type>(<scope>): <imperative description>` with `Refs: FEAT-nnn`, `Closes #n` or `BREAKING CHANGE:` as applicable. One commit represents one coherent change, staged by explicit path (`git add <paths>`), never `git add -A`, `git add .` or `git commit -a`. No AI attribution in the title; a co-author footer follows the project's or the agent platform's attribution setting. The squash commit body states why, what changed, any approach rejected and why, and the proof (the command and its result). After the first review, add each fix as a new commit instead of rewriting reviewed ones.

## 4. Integrate without rewriting history

Except for `spike/` branches, keep the feature current by merging `origin/main` into it (rebase only a branch never pushed), run gates, then use a squash PR so one feature becomes one main commit. Before each push, `git fetch` and check that `git log --oneline origin/main..HEAD` lists only this branch's commits; remove a stray one before pushing. An authorized force-push uses `git push --force-with-lease`, never plain `--force` and never on `main`.

## 5. Select versions

- SemVer: breaking change → MAJOR, compatible feature → MINOR, fix → PATCH; tag `vX.Y.Z` on `main`.
- Pre-release uses `-alpha.N` until releasable.
- Client/server `protocol_version` is a separate integer: compatible optional fields keep it; incompatible changes increment it and require an explicit compatibility window.

## 6. Check local and remote state

Run `git status` and identify the branch/remote. Distinguish connectivity failures from authentication failures:

- DNS errors, timeouts, or `error connecting to api.github.com` do not establish invalid credentials. For authorized reads, use the GitHub connector when it supports the operation; otherwise request narrowly scoped sandbox escalation for the exact CLI command. Do not change persistent permissions.
- Check `gh auth status` through a working network path. Ask the user to run `gh auth login` only when the result establishes missing or invalid authentication. A permission or rate-limit error alone does not justify logging in again.
- Do not blindly retry mutations after an ambiguous failure; first check whether the operation took effect.

## 7. Create the PR

Run required local gates, then use `gh pr create`. The body states what changed, why, the tradeoffs, regressions or follow-ups it leaves and whether a revert fully undoes it, the exact test commands/results with what each proves (`Not tested:` for what none covers), and linked issues (`Closes #n`/`Refs: FEAT-nnn`). Every file in `git diff --stat origin/main...HEAD` is explained by a commit of this branch.

Then wait for the PR checks (`gh pr checks <n> --watch`) and report each check's name and conclusion in the PR, a failing one first. Local gates do not replace CI-only gates such as dependency or secret scans, so the PR is not done while a check is red.

## 8. Review and merge

- Inspect `gh pr checks`, `gh pr view` and review comments.
- Resolve findings and rerun affected gates before merge.
- Merge only after required approvals/checks, using the repository's squash policy.
- After the merge, check the `main` CI run for the merge commit: rerun failed jobs once (`gh run rerun <id> --failed`) only for an infrastructure fault in the log; otherwise fix forward or revert.

## 9. Publish a release

- The user names the bump (patch, minor, major or an exact version); ask when the request does not.
- Before tagging, `git log --first-parent --oneline <previous-tag>..HEAD` lists the merges since the last release; each user-visible one has its CHANGELOG line.
- After `VERSION` and CHANGELOG are ready under §5, use `gh release create vX.Y.Z` with notes from that CHANGELOG section and a compare link (`<previous-tag>...vX.Y.Z`). Then check what users receive, each surface by its own command (the tag's commit, release assets, registry or marketplace version).

## 10. Track binaries with Git LFS

Before editing `.gitattributes`, adding or migrating a large binary or checking quota, read `references/git-lfs-and-binaries.md` (file policy, init, audit, migration, report) and `references/lfs-quotas-github.md` (current quota facts).

Done when: the change has a short-lived branch, atomic Conventional Commits, green squash PR, safe flag state and justified app/protocol versions; authentication is valid, the PR body contains evidence, every PR check is reported by name and passes, reviews pass, merge follows policy, `main` CI passes on the merge commit and any release matches its approved version/tag; LFS work meets the Done line of its reference.
