---
id: KIT-076
title: "The kit's ci, gitleaks and CodeQL workflows run on every pull request and push to main as required checks, with linted, pinned and time-bounded workflows"
status: done
confirmed: "2026-11-15 (owner, chat, relayed by the coordinator session \"Revisão de regras e skills\": \"Revisão + CI verde\")"
issue: "#264"
pr: "#272"
---

# KIT-076 — The kit's ci, gitleaks and CodeQL workflows run on every pull request and push to main as required checks, with linted, pinned and time-bounded workflows

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
- Docs: `.github/CONTRIBUTING.md` § CI requirements, the PR template, the root README's `.github/` row,
  `platforms/kits/github/README.md`, `CHANGELOG.md` and a History line in KIT-014 and KIT-063.

Not changed:

- repository settings: the coordinator sets the ruleset, `allow_auto_merge` and Dependabot security updates after
  this merges.

### Widened: five Actions practices

The owner widened this record on 2026-11-15 (chat, relayed by the coordinator, "Sim, inclua").

1. **actionlint and zizmor.** `ci.yml` gains the `workflow-lint` job, a required check. It runs actionlint 1.7.12 and
   zizmor 1.32.0, each pinned by version and sha-256; the digests match the `digest` GitHub's release API reports for
   `actionlint_1.7.12_linux_amd64.tar.gz` and `zizmor-x86_64-unknown-linux-gnu.tar.gz`. They lint
   `.github/workflows/*.yml` and `platforms/kits/github/workflows/*.yml`, the templates every consumer copies.
   - actionlint runs shellcheck on `run:` scripts, which `ubuntu-latest` ships.
   - zizmor runs at its default persona with online audits. The audits read public action metadata with the job's
     read-only token, which also checks that each SHA pin is a commit of the named repository.
   - On `4f035d1`, zizmor 1.32.0 found 71 findings in the ten files. Every one is fixed, and no config or ignore
     comment silences any:
     - every action pinned by commit SHA with a version comment;
     - every checkout states `persist-credentials`: `false`, or `true` with its reason in `ci-godot.yml`'s test job,
       whose `git lfs pull` authenticates with it (zizmor accepts an explicit `true`);
     - `pr-contract.yml` passes `inputs.script`, `inputs.config` and `inputs.repo` through `env:` instead of
       `${{ }}` in `run:` (`template-injection`);
     - read-only top-level `permissions` (`contents: read`, or `{}` where the job needs nothing), and
       `release.yml`'s `contents: write` moved to its one job.
   - The pedantic persona still lists 18, which the gate does not run:
     - 11 jobs without a `name`;
     - 4 workflows without job-level `concurrency`; for the reusable templates the caller's workflow owns it;
     - `ci-godot.yml`'s `container` tag, which follows the `godot-version` input, so a digest pin would fix one
       Godot version.
2. **`timeout-minutes` on every job**, in both folders. The rule is 3 × the longest measured green run of the job,
   rounded up to 5 minutes, with a 5-minute floor; GitHub's 360-minute job limit for hosted runners is the ceiling. The
   factor 3 covers the shared-runner spread measured here: the unit-test step took 277 s, 354 s and 433 s on nearly the
   same tree.
   The table below lists each value and its basis.
3. **A weekly CodeQL `schedule`** (`23 5 * * 1`, Mondays 05:23 UTC) beside `pull_request` and `push`. It reruns new
   queries on a quiet `main`. GitHub's "Events that trigger workflows" page says scheduled workflows run on the latest
   commit of the default branch, and that "in a public repository, scheduled workflows are automatically disabled when
   no repository activity has occurred in 60 days". `.github/CONTRIBUTING.md` says so and names the Actions tab to
   re-enable it.
4. **Dependabot covers the templates.** `.github/dependabot.yml` adds a `github-actions` entry for
   `/platforms/kits/github/workflows` beside `/`.
   - GitHub's "Dependabot options reference" says only that with `/` Dependabot searches `/.github/workflows` and the
     root `action.yml`; it does not describe any other directory.
   - Dependabot's source does (`dependabot/dependabot-core`, `github_actions/lib/dependabot/github_actions/
     file_fetcher.rb`, last changed in `51cb2e3` on 2026-10-14). For a `directory` other than `/` it sets
     `workflows_dir = "."` and fetches every file in that folder matching `/\.ya?ml$/`. So the entry reads the five
     templates.
   - What would prove this wrong: no Dependabot pull request or log line ever names a file under
     `platforms/kits/github/workflows/` after an action release. The fallback would be a test that fails when a
     template pins a different SHA for an action that `.github/workflows/` also uses.
5. **Dependabot security updates** are a repository setting, so this PR does not change them. They are a coordinator
   step after the merge (see below).

| Job | Timeout (min) | Longest measured green run | Basis |
|---|---|---|---|
| `ci.yml` `ci` | 30 | 573 s | PR #272 run 43767721133; seven green runs from 360 s to 573 s |
| `ci.yml` `workflow-lint` | 5 | 9 s | dispatch run 43767714175; three green runs |
| `gitleaks.yml` `gitleaks` | 5 | 10 s | full-history dispatch run 43762692739 |
| `codeql.yml` `codeql (python)`, `codeql (actions)` | 5 | 55 s | PR #272 run 43762637246 |
| `release.yml` `release` | 5 | 13 s | `v12.1.0` run 43531254664 (2 green runs) |
| `evals.yml` `eval` | 360 | none | never run: the `ANTHROPIC_API_KEY` secret is not set; GitHub's limit written out until the first green run |
| `ci-godot.yml` `changes` | 5 | 7 s | a consumer project, 9 green runs |
| `ci-godot.yml` `import-and-test` | 45 | 828 s | the consumer's current Godot test job (1 green run); the template's own job peaked at 122 s in 50 runs |
| `ci-godot.yml` `lint` | 5 | 70 s | the consumer's current lint job; 18 s in 5 earlier runs |
| `ci-java.yml` `changes` | 5 | 40 s | a consumer project, 5 green runs |
| `ci-java.yml` `build` | 10 | 105 s | a consumer project, 85 green runs |
| `ci-java.yml` `dependency-check` | 360 | 13,987 s | a cold NVD sync, 83 green runs; 3 × exceeds GitHub's limit, so the limit (the old 150 was below a measured green run) |
| `gitleaks.yml` (template) `scan` | 5 | 21 s | this kit's own runs of the same `gitleaks/gitleaks-action`, 97 green runs |
| `pr-contract.yml` `contract` | 5 | 42 s | a consumer project, 15 green runs |
| `spec-lint.yml` `validate` | 5 | 60 s | a consumer job that runs the same `check_spec.py` steps plus gitleaks and more, 100 green runs |

### Required check contexts

The ruleset requires these five contexts, all reported by the GitHub Actions app (integration id 15368):

| Context | Workflow | Job |
|---|---|---|
| `ci` | `.github/workflows/ci.yml` | `check` |
| `workflow-lint` | `.github/workflows/ci.yml` | `workflow-lint` |
| `gitleaks` | `.github/workflows/gitleaks.yml` | `scan` |
| `codeql (python)` | `.github/workflows/codeql.yml` | `analyze`, matrix `python` |
| `codeql (actions)` | `.github/workflows/codeql.yml` | `analyze`, matrix `actions` |

A job's `name` is its context, so renaming one leaves the ruleset waiting forever for the old name.
`test_kit_workflows.py` fails on such a rename. The merge flow:

1. The independent review returns READY on the head.
2. The coordinator arms auto-merge.
3. GitHub merges once the five checks pass on that head.

Coordinator steps after the merge, none of them in this PR:

- a ruleset on `main` that requires the five contexts above;
- `allow_auto_merge`;
- Dependabot security updates (`security_and_analysis.dependabot_security_updates`), together with the vulnerability
  alerts they need.

## Options considered

| Option | Verdict |
|---|---|
| A. `pull_request` + `push` to `main` + dispatch, the five jobs required, auto-merge armed only after a review READY (chosen) | every PR and every `main` commit gets a clean-runner proof at no cost; a broken gate shows on the PR that breaks it; the review stays the merge decision |
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

Runner (`ubuntu-latest`), every run `success` and billed 0 ms (`actions/runs/<id>/timing`):

- The shellcheck fix alone, `ci.yml` dispatched on `1e6d9bf` with the old triggers: run 43761925204, 531 tests.
- The final shape, on `275535b`:
  - `ci.yml` dispatch, run 43767714175: `ci` in 461 s and `workflow-lint` in 9 s. `ci` covers shellcheck `-x`, the
    Claude Code install, `check.sh` with `claude plugin validate`, the full `unittest discover`, `smoke.sh` and
    `--links`;
  - the pull request #272's checks: `ci` and `workflow-lint` in run 43767721133 (573 s and 6 s), `codeql (python)`
    and `codeql (actions)` in run 43767721003 (50 s and 36 s), and `gitleaks` in run 43767721036 (5 s). GitHub's
    code-scanning check `CodeQL` passed as well.
- `workflow-lint` on `2186fca`, run 43766325153: both tarballs passed `sha256sum -c`, actionlint printed nothing and
  exited 0, and zizmor logged "completed" for each of the ten files, then "No findings to report. Good job! (18
  suppressed)".
- `gitleaks`:
  - on the pull request (run 43762637237), the range was the PR's commits `4f035d1..9004eb6` (4 commits, no leaks);
  - dispatched (run 43762692739), the range was `HEAD`: 186 commits, no leaks.
- The hook latency tests in `test_hooks_context.py` and `test_hooks_guard_compact.py` passed within their budgets in
  every run.
- On the runner, 63 tests skip: 60 already skip on `main`, and the 3 `GitleaksRange` tests need gitleaks on `PATH`.

Local (macOS, python3 3.9.6, shellcheck 0.11.0, gitleaks 8.30.1, zizmor 1.32.0), all exit 0:

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`;
- `bash platforms/tools/smoke.sh`;
- `python3 platforms/ci/validations/check_kit.py --links`;
- `python3 -B -m unittest platforms.ci.validations.test_kit_workflows platforms.ci.validations.test_check_kit_readmes`;
- `python3 -B -m unittest platforms.ci.validations.test_sync_project`, the suite that reads the templates;
- the full `unittest discover` at `9004eb6` (542 tests, OK);
- zizmor with online audits over the ten files: no findings;
- the shellcheck command of `ci.yml`, with and without `-x`;
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: no leaks;
- `python3 platforms/tools/review_checks.py red --base origin/main --head HEAD --run "python3 -B -m unittest {tests}"`:
  `red: OK — 54 of 54 failing tests are Red on base, and head passes`.

Not tested:

- a push to `main` and the weekly schedule; actionlint checked the cron syntax;
- a fork's pull request;
- `cancel-in-progress` with two pushes in flight;
- a Dependabot run on the templates folder, which comes after the merge;
- the template changes inside a consumer project. zizmor, actionlint and `test_sync_project` cover them in the kit.

## History

- 2026-11-15: confirmed (owner, chat, relayed by the coordinator: "Revisão + CI verde"). Issue #264.
- 2026-11-15: implemented in #272; the runner proof is above.
- 2026-11-15: widened by the owner ("Sim, inclua", relayed by the coordinator): the five Actions practices above.
