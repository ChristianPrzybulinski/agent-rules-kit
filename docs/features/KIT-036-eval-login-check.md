---
id: KIT-036
title: "A local eval run checks the CLI login before a score counts"
status: done
confirmed: "2026-11-11 (owner, chat of the ub-mode implementation session: \"aprovo\")"
issue: "#146"
pr: "#147"
---

# KIT-036 — A local eval run checks the CLI login before a score counts

## Problem and evidence

[FACT] On 2026-11-11 the 25 new eval cases of KIT-029 to KIT-033 ran one at a time from their worktrees with the
local command of `docs/maintenance.md` § Evals (`claude plugin eval plugins/<p> --case '<name>' --runs 1 --ablation
none --no-publish --trust-plugin`, plus `--scaffold --allow-tools Bash Edit Write` for the 3 cases with a fixture),
on Claude Code 2.1.287:

| Cases | Exit | Seconds each | `partialReason` | Arm `error` |
|---|---|---|---|---|
| 22 | 2 | 1.1–1.6 | `auth_failed` | "exit 1: Not logged in · Please run /login" |
| 3 (fixture) | 1 | 0.7–1.2 | none | "the Docker (~/.docker, DOCKER_CONFIG) credential store on this machine holds a symbolic link inside it, so the Bash sandbox cannot reliably exclude it — a Bash-granting evaluation cannot run here; …" |

- The 25 runs took 29.0 s together, so the run time was not the cost. Each command's output ended at
  "Wrote …/result.json" and "Report: …/report.html", and each result's `aggregates` read `casesTotal 1`,
  `casesPassed 0`, `overallScore 0`: the same numbers as a skill that fails every grader. The cause was only in the
  JSON, in the top-level `partialReason` and in `cases[0].arms.with[0].error`.
- `claude auth status` printed `"loggedIn": false` and exited 1, inside and outside the Bash sandbox. The symbolic
  links are Docker Desktop's own, in `~/.docker/bin` (docker, docker-compose, docker-credential-desktop,
  docker-credential-osxkeychain, kubectl, kubectl.docker).
- No kit file mentions `claude auth status`, `auth_failed` or `loggedIn` at 49b2137: a case-insensitive
  `git grep` for `auth status`, `auth_failed`, `loggedIn` and `Not logged in` finds only `gh auth status` lines.
  `docs/maintenance.md` § Evals is the one place that gives the local command, and `.github/workflows/evals.yml`
  authenticates with `ANTHROPIC_API_KEY` instead.

The proposal in the session chat asked for an eval runner that checks the login before it starts. The kit has no
runner: the one used that day was a scratch script of the session, and the runs failed in about a second each. What
cost time was telling a zero score that measured nothing from a skill that failed, so the change is one bullet next
to the documented command, not a new script.

## Change

`docs/maintenance.md` § Evals gains one bullet after the local command:

> Before a local run, `claude auth status` must exit 0 (`"loggedIn": true`). Logged out, every case stops before any
> model turn: the command exits 2 in about a second and the result reads `casesPassed: 0` and `overallScore: 0`, like
> a skill that fails every grader; only `partialReason: "auth_failed"` and the arm's `error` ("Not logged in · Please
> run /login") say that nothing ran. A `--scaffold` case also stops, with exit 1, when `~/.docker` holds a symbolic
> link (Docker Desktop's `~/.docker/bin`), which the Bash sandbox cannot exclude. Record such a case as unverified
> with that line, never as a failing skill, and rerun it after `claude auth login`.

`CHANGELOG.md` gains one line under `[Unreleased]`; `VERSION` does not change (documentation only).

## Proof

- The table above, read from each case's `--json` result; `claude auth status` exits 1 and `claude auth --help`
  lists `login`, `logout` and `status`, on Claude Code 2.1.287.
- Gates on 2026-11-11 at this branch, from the worktree root:
  - `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: exit 0, "check: OK (14 plugins,
    46 skills, 3 rules, 22 templates, 23 indexes, 123 links, 25 hook cases)" and "✔ Validation passed".
  - `bash platforms/tools/smoke.sh`: exit 0, "smoke: OK (46 skills, app fallback, cleanup, symlink safety, manifests,
    sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
  - `python3 platforms/ci/validations/check_kit.py --links`: exit 0, the same "check: OK" line.
  - `gitleaks git --redact --log-opts="origin/main..HEAD"`: exit 0, "1 commits scanned", "no leaks found".
- Not run: an eval case. The change adds no skill or case, and the CLI is still logged out on this machine.

## History

- 2026-11-11: confirmed (owner, chat); issue #146. The first proposal asked for a runner that checks the login; the
  kit has no runner, so the rule went next to the documented command.
- 2026-11-11: done in #147.
