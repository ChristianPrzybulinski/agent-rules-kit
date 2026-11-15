---
id: KIT-076
title: "The kit's ci, gitleaks and CodeQL workflows run on every pull request and push to main as required checks"
status: confirmed
confirmed: "2026-11-15 (owner, chat, relayed by the coordinator session \"Revisão de regras e skills\": \"Revisão + CI verde\")"
issue: "#264"
pr: ""
---

# KIT-076 — The kit's ci, gitleaks and CodeQL workflows run on every pull request and push to main as required checks

This record supersedes KIT-014's trigger rule ("no kit workflow runs on push or pull request") and the
`workflow_dispatch`-only trigger of KIT-063. Both records stay as history.

## Problem and evidence

[FACT] KIT-014's only reason was billing. It counted 678 kit runs from 2026-10-01 to 2026-10-26, and none had started
since 2026-10-12, because the account's Actions payments were blocked. That reason is gone:
`gh api repos/ChristianPrzybulinski/agent-rules-kit` showed `visibility: public` on 2026-11-15. KIT-063 measured that
standard GitHub-hosted runners are free on a public repository: run 43525047799 billed `total_ms: 0`, and the kit's
minutes were billed only in October, while it was still private. The Stratics "zero automatic workflows" rule covers a
different, private repository and does not change.

[FACT] With no automatic run, the kit's CI drifted unnoticed. A dispatch of `ci.yml` on `main` `4f035d1` (run
43761316770) failed at `shellcheck`, and every later step was skipped:

- `SC1091` (info) at `platforms/tools/bootstrap.sh:6`, `doctor.sh:6` and `refresh.sh:6`, which source
  `./codex-bin.sh`: "Not following: ./codex-bin.sh was not specified as input (see shellcheck -x)";
- `SC2086` (info) at `platforms/tools/smoke.sh:884`, the unquoted `$godot_skills`.

Local shellcheck 0.11.0, the version the runner installs, reports the same four findings.

[FACT] The coordinator ran the gates locally and dispatched CodeQL by hand before each merge. On 2026-11-15 the
repository had `allow_auto_merge: false`, no branch protection on `main` and one ruleset, `protect-release-tags`.

[FACT] A green gate is not a review. On #246 every gate was green in all 7 rounds while the independent reviews found
real bypasses (coordinator, 2026-11-15). CI therefore becomes a required check beside the review READY, never instead
of it.

## Change

- `platforms/tools/bootstrap.sh`, `doctor.sh` and `refresh.sh`: a `# shellcheck source=SCRIPTDIR/codex-bin.sh`
  directive above the `source` line. `platforms/tools/smoke.sh` quotes `"$godot_skills"`, which counts the same lines,
  one skill name per line. Shellcheck keeps its default severity and excludes no code.
- `.github/workflows/ci.yml`, `gitleaks.yml` and `codeql.yml` run on `pull_request` to `main`, on `push` to `main` and
  on `workflow_dispatch`. Each one gets:
  - `permissions: contents: read` at the top; only CodeQL's job adds `security-events: write`, for the SARIF upload;
  - `concurrency` per ref (`${{ github.workflow }}-${{ github.ref }}`) with `cancel-in-progress: true`;
  - every action pinned by commit SHA with its version in a comment: `actions/checkout` `3d3c42e` (`v7.0.1`),
    `actions/setup-python` `6d4fd22` (`v7.1.0`) and `github/codeql-action` `33d7b85` (`v4.39.3`). Dependabot's weekly
    `github-actions` update bumps a SHA pin together with its comment;
  - a fixed job `name`, which is the check context, a `timeout-minutes` and no `if:` on the job. Skill `security` § 6
    says a skipped required job reports success.
- The trigger is `pull_request`, never `pull_request_target`: a fork's pull request runs its own workflow copy with a
  read-only token and no secrets.
- `ci.yml` keeps its steps: shellcheck (now with `-x`), the Claude Code install, `check.sh`, the full
  `unittest discover`, `smoke.sh` and `check_kit.py --links`.
- `gitleaks.yml` runs the gitleaks CLI 8.30.1, pinned by version and sha-256, as the KIT-074 template does; it replaces
  `gitleaks/gitleaks-action`. The digest `551f6fc…` matches the `digest` that `gh api
  repos/gitleaks/gitleaks/releases/tags/v8.30.1` reports for `gitleaks_8.30.1_linux_x64.tar.gz`. The checkout keeps
  `fetch-depth: 0` and the scan runs with `--redact`:
  - a pull request scans its own commits (`$BASE_SHA..$HEAD_SHA`, passed through `env:`, never spliced into `run:`);
  - a push to `main` and a dispatch scan the whole history (`--log-opts=HEAD`).

  The step needs no token.
- `codeql.yml` keeps `python` and `actions` with `build-mode: none`. Default setup stays off.
- `platforms/ci/validations/test_kit_workflows.py` (new) pins all of the above for the three workflows: the triggers,
  no `pull_request_target` or `workflow_run` in any kit workflow, the read-only token, the concurrency, the SHA pins,
  the check names, the CodeQL languages and the gitleaks CLI. It also runs the scan step's script against a throwaway
  repository with the local gitleaks:
  - a pull request skips a secret that is already on `main`;
  - a pull request fails on a secret it adds, and the log stays redacted;
  - `push` and `workflow_dispatch` find the old secret.
- Docs: `.github/CONTRIBUTING.md` § CI requirements, the PR template, the root README's `.github/` row, `CHANGELOG.md`
  and a History line in KIT-014 and KIT-063.

Not changed:

- repository settings: the coordinator sets the ruleset and `allow_auto_merge` after this merges;
- `release.yml`, `evals.yml` (it needs a secret that is not set) and `dependabot.yml`;
- the workflows shipped in `platforms/kits/github/workflows/`.

### Required check contexts

The ruleset requires these four contexts, all reported by the GitHub Actions app (integration id 15368):

| Context | Workflow | Job |
|---|---|---|
| `ci` | `.github/workflows/ci.yml` | `check` |
| `gitleaks` | `.github/workflows/gitleaks.yml` | `scan` |
| `codeql (python)` | `.github/workflows/codeql.yml` | `analyze`, matrix `python` |
| `codeql (actions)` | `.github/workflows/codeql.yml` | `analyze`, matrix `actions` |

A job's `name` is its context, so renaming one leaves the ruleset waiting forever for the old name.
`test_kit_workflows.py` fails on such a rename. The merge flow:

1. The independent review returns READY on the head.
2. The coordinator arms auto-merge.
3. GitHub merges once the four checks pass on that head.

## Options considered

| Option | Verdict |
|---|---|
| A. `pull_request` + `push` to `main` + dispatch, the four jobs required, auto-merge armed only after a review READY (chosen) | every PR and every `main` commit gets a clean-runner proof at no cost; a broken gate shows on the PR that breaks it; the review stays the merge decision |
| B. Keep dispatch only and the local gates (KIT-014) | zero runs, but `main`'s CI broke unnoticed (run 43761316770), and the coordinator dispatches by hand before each merge |
| C. Required checks that merge on their own (auto-merge armed when the PR opens) | fewer steps, but on #246 green gates missed bypasses the reviews found in all 7 rounds |
| D. `paths:` filters on the triggers | a required check that a filter skips never reports, so the PR waits forever; nearly every kit PR touches `platforms/` or `plugins/` anyway (KIT-014 option C) |
| E. `pull_request_target` | runs the base workflow with a write token and secrets next to a fork's code; skill `security` § 6 forbids it |

What would prove A wrong:

- the kit's `Actions Linux` row in `settings/billing/usage` shows `netAmount` > 0 for a month after the merge;
- a required check fails on a shared runner for a reason other than the change (for example the hook latency budgets
  in `test_hooks_context.py` and `test_hooks_guard_compact.py`) more than once in ten runs, so required checks block
  sound PRs;
- the `ci` job's time grows until the review READY routinely waits on it.

## Proof

- Local: `bash platforms/tools/check.sh`, `CI=1 bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
  `python3 platforms/ci/validations/check_kit.py --links`, the touched suites,
  `gitleaks git --redact --log-opts="origin/main..HEAD"` and
  `python3 platforms/tools/review_checks.py red` on `test_kit_workflows.py`.
- The shellcheck command of `ci.yml`, with and without `-x`, exits 0, and so does `shellcheck -x` on the three scripts
  from `platforms/tools/`.
- Runner: `workflow_dispatch` runs of `ci.yml` on the branch, and the four checks on the pull request.

## History

- 2026-11-15: confirmed (owner, chat, relayed by the coordinator: "Revisão + CI verde"). Issue #264.
