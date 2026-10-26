---
id: KIT-014
title: "The kit's ci and gitleaks workflows run only on demand (workflow_dispatch)"
status: done
confirmed: "2026-10-26 (owner, Stratics FEAT-101 activation coordination chat)"
issue: "#97"
pr: "#99"
---

# KIT-014 — The kit's ci and gitleaks workflows run only on demand (workflow_dispatch)

## Problem and evidence

[FACT] `.github/workflows/ci.yml` (`on: [push, pull_request]`) and `.github/workflows/gitleaks.yml` (`push`,
`pull_request`) create runs for every kit push and pull request. `gh api repos/ChristianPrzybulinski/agent-rules-kit/actions/runs`
counted 630 runs from 2026-10-01 to 2026-10-11 and 48 from 2026-10-12 to 2026-10-26. That is about 4 runs per PR plus
2 per merge push.

[FACT] Since the Actions billing block, none of those jobs starts: every run since 2026-10-12 ends `failure` with
0 steps, and its annotation reads "The job was not started because recent account payments have failed or your
spending limit needs to be increased". As a result, #91, #93, #95 and #96 merged with red checks that prove nothing.
The proof was the local gates (`check.sh`, `smoke.sh`, `check_kit.py --links`). If billing resumes, the same triggers
spend minutes repeating those gates.

[FACT] The Stratics repositories have created no automatic workflow run since 2026-10-13. Their last runs are on
that day, and stratics-docs `main` has no `push`, `pull_request` or `schedule` trigger (DPRO-011 amendment
2026-10-12c). The kit is the owner's only repository that still triggers Actions automatically. No kit ruleset
requires these checks.

## Change

- `.github/workflows/ci.yml`: `on: workflow_dispatch`. The jobs and steps stay unchanged.
- `.github/workflows/gitleaks.yml`: `on: workflow_dispatch`. The scan keeps `fetch-depth: 0`, so a dispatch scans the
  whole history.
- `.github/PULL_REQUEST_TEMPLATE.md`: a checklist line requiring a local run of `platforms/tools/smoke.sh`,
  `python3 platforms/ci/validations/check_kit.py --links` and
  `gitleaks git --redact --log-opts="origin/main..HEAD"`, clean. Commits are scanned, not the working tree.
- `.github/workflows/INDEX.md` and `docs/maintenance.md` "CI requirements": both workflows are listed as
  `workflow_dispatch only`. The local gates are the proof, and a dispatch is for a check that needs a clean Ubuntu
  runner.
- `.github/README.md`: the workflow list matches the folder. The `devin-plugin.yml` entry is dropped because that file
  no longer exists.
- `CHANGELOG.md`: a `### Changed` line.
- Not changed: `release.yml` (tag `v*`, only at a release), `evals.yml` (already dispatch-only) and
  `.github/dependabot.yml`. Dependabot's weekly update runs (2 since 2026-10-12, both `success`) are a separate
  decision.

## Options considered

| Option | Verdict |
|---|---|
| A. `workflow_dispatch` only, plus local gates in the PR checklist (chosen) | zero automatic runs, matches the Stratics policy, the checks stay one click away |
| B. Keep `pull_request` and drop `push` | still about 2 runs per PR. Blocked runs still show red today, and they spend minutes once billing resumes |
| C. `pull_request` with `paths:` filters | nearly every kit PR touches `platforms/` or `plugins/`, so it saves little and adds a rule to maintain |
| D. Delete both workflows | loses the clean-runner check (Claude Code install, Ubuntu shellcheck) that a dispatch still offers |
| E. Leave as is | red X on every PR, ignored by habit, and minutes spent if billing resumes |

## Proof

- Run `bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh` and
  `python3 platforms/ci/validations/check_kit.py --links`.
- `python3 -c "import yaml; [print(f, yaml.safe_load(open(f))[True]) for f in ('.github/workflows/ci.yml', '.github/workflows/gitleaks.yml')]"`
  prints `workflow_dispatch` for both files. PyYAML reads the `on` key as `True`.
- After the merge, the merge push creates no `ci` or `gitleaks` run.

## History

- 2026-10-26: confirmed (owner, chat), after the Actions usage audit of the four repositories. Proposal merged in
  #98 (`5cbd86f`); implemented in #99.
