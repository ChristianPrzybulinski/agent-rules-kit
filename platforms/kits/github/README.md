# kit github

CI, PR and label governance templates for GitHub Actions.

## How to use

| File | Destination in the project |
|---|---|
| `workflows/*.yml` | `.github/workflows/` |
| `PULL_REQUEST_TEMPLATE.md` | `.github/PULL_REQUEST_TEMPLATE.md` |
| `REVIEW.md` | `REVIEW.md` at the repository root (read by hosted Claude Code Review; also the checklist for any reviewer) |
| `ISSUE_TEMPLATE/task.md` | `.github/ISSUE_TEMPLATE/task.md` (one issue per task row or bundle, filled verbatim by the `sdd-tasks` cut) |
| `labels.json` | reference for `scripts/labels-sync.sh` |
| `scripts/labels-sync.sh` | run from anywhere inside the repo: `bash platforms/kits/github/scripts/labels-sync.sh` |

`ci-java.yml` and `ci-godot.yml` are **reusable** workflows (`on: workflow_call`). Each step runs a recipe the project's justfile imports from the kit's module (`import '~/.ai-kit/platforms/kits/just/<profile>.just'`, written by `sync-project.sh`; KIT-074), so CI and a developer run the same command. Before its first `just` step each job calls the spec-tools action with `checks: none`, which links `$HOME/.ai-kit` to the kit at the commit it pins (KIT-081 stage 1b: no copy in the project; an import path takes no variable), then installs `just` 1.58.0 from its release tarball checked against its sha-256. The template's pin is the same release as `spec-lint.yml`'s, which predates the link step, so until a release ships it, pin the commit `sync-project.sh` writes into `spec-lint.yml`. Copy them to the project's `.github/workflows/` and call them from a thin project workflow:

```yaml
# .github/workflows/ci.yml
name: ci
on:
  pull_request:
  workflow_dispatch:
jobs:
  java:
    uses: ./.github/workflows/ci-java.yml
    secrets:
      NVD_API_KEY: ${{ secrets.NVD_API_KEY }}
  godot:
    uses: ./.github/workflows/ci-godot.yml
    # with:
    #   godot-version: '4.7.2'
    #   test-runner: 'gdunit4'   # or 'gut'
```

## Notes

- `ci-java.yml` assumes the Maven wrapper (`./mvnw`), JDK 25 Temurin and the `platforms/kits/java-maven/pom-parent.xml` gates (Spotless, JaCoCo, PITest). Its `changes` job skips build/tests on docs-only diffs and runs `dependency-check` only when build files change; the mojo is pinned (`dependency-check-maven:13.0.0`, supports `nvdApiKeyEnvironmentVariable`), `NVD_API_KEY` is a required secret, and the NVD data cache is saved even when the gate fails.
- `ci-godot.yml` runs in `barichello/godot-ci:<godot-version>`. The boot-proof step (`just boot`) runs `--import` first (`--quit` skips the import scan), then fails when the `--quit` log has `SCRIPT ERROR`, `Parse Error`, `Parser Error` or `Can't load script`, because that exit code is 0 after a script error. The `test-runner` input reaches `just test` as `GODOT_TEST_RUNNER` and selects gdUnit4 (`addons/gdUnit4`, default) or GUT (`addons/gut`); a missing runner addon, no test suite or zero executed test cases fails the build — tests are never silently skipped — and `reports/` plus the runner log upload as the `godot-test-reports` artifact. Its `changes` job exposes `code`/`export` outputs so the caller can gate a manual export job (requires `export_presets.cfg` committed to the repo). LFS objects restore from a cache keyed on the LFS file list. The `lint` job needs `requirements-gdtoolkit.txt` and `.gdlintrc` at the project root (from `platforms/kits/godot/`).
- `spec-lint.yml` validates `docs/spec/**` with the kit's spec tools through the composite action `platforms/ci/actions/spec-tools` (KIT-081 stage 1), which runs the kit's validators and schemas from the commit its `uses:` line pins: the project carries no copy, and the job needs no token and checks out no other repository. `platforms/tools/sync-project.sh` writes it into a project with `docs/spec` whose CI runs no spec tools, the action pinned to the kit commit the sync runs from; the template's own pin is a kit release, which the kit's Dependabot moves to each new one; until a release ships the action (the first after 13.1.0), that pin predates it, so take the file from the sync. On a pull request it also runs `check_spec.py --baseline-against` with the base commit's `docs/spec/baseline.json`, so a baseline that gains an entry or a higher value fails (KIT-068); `checks: spec,trace,rows` adds `spec_trace.py check` and the row checks. The action's README lists its inputs.
- `pr-contract.yml` is a **reusable** workflow running the no-model PR gates (`platforms/ci/validations/pr_gates.py`). `pr_gates.py` comes from the kit commit the spec-tools action pins (the action runs with `checks: none` and exports `AI_KIT_DIR`); the gates config comes from the gates repository checked out at a protected ref (`gates-ref`, never the PR head — the job holds the secret), and the job needs a `GATES_TOKEN` able to read the backlog repo's issues; `repo`, `gates-repo` and `config` (default `.github/pr-gates.json`) are inputs, and `proof-commands` is the output the caller's `proof` job runs. The `script` input went with KIT-081 stage 1: a caller that passes it fails until the line is removed.
- `gitleaks.yml` calls the kit's gitleaks composite action (`platforms/ci/actions/gitleaks`, KIT-084), pinned by SHA like the spec-tools action, so the scan and its pin live in the kit; a project may instead add the action as a step of an existing job and keep one billed job per run (a reusable workflow cannot be called across repositories from a kit path). The action runs the gitleaks CLI at a pinned version and sha-256 (8.30.1, the kit's own scan's pin), not `gitleaks/gitleaks-action`, which in an organization's repository needs a `GITLEAKS_LICENSE` secret and exits 1 before scanning without one (KIT-074). A pull request scans its own commits (base..head), a push and a dispatch the whole history of the checked-out ref (`fetch-depth: 0`); it redacts every value in the log (`--redact`), takes a `config` input (a path in the repository; without it `.gitleaks.toml` at the root when present, else the built-in rules) and applies `.gitleaksignore` at the root. Triggers: push, pull request, dispatch and `workflow_call`; keep the ones the project's CI policy allows. The scan standard is `plugins/guardrails/skills/security/references/scan.md`.
- `changelog-consolidate.yml` and `spec-status-sync.yml` open a pull request from a kit tool's output (KIT-084). The first runs `changelog_fragments.py --repo-dir .`, which moves the `changelog.d/<id>.<type>.md` fragments into `CHANGELOG.md` → `## [Unreleased]` and names every malformed line before it writes; the second runs `spec_trace.py sync-status --write` for a spec whose `sdd.tracker` is `github`. Each runs the tool from `$AI_KIT_DIR` after the spec-tools action (`checks: none`), opens or refreshes one pull request on a fixed branch (`chore/changelog-consolidate`, `chore/spec-sync-status`) only when the tool changed a file, and never merges it; the body is inline in the template. Both run on dispatch only; a comment in each shows the `schedule:` lines to add. The kit tool ships since 15.0.0; a pin older than that fails the changelog step with "can't open file".
- Those two templates need the repository secret `PR_BOT_TOKEN`: GitHub starts no workflow for a pull request the job's own `GITHUB_TOKEN` opens, so its required checks would never run. Use a fine-grained personal access token (or a GitHub App token) limited to the repositories it touches, with **Contents: read and write** and **Pull requests: read and write** on the project's repository; for `spec-status-sync.yml` also **Issues: read** and **Pull requests: read** on the backlog repository and each repository `sdd.github` names. The checkout keeps no credential (`persist-credentials: false`); only the step that pushes and opens the pull request holds the token, through a git credential helper that reads it from the environment, and the sync step reads the issues with it. Store it as an Actions secret, never in a file.
- Every template pins its actions by commit SHA with the version in a comment (the kit's Dependabot keeps them current; a project's own Dependabot does once copied), sets `persist-credentials: false` on its checkouts except `ci-godot.yml`'s test job, whose `git lfs pull` needs the credential, passes inputs to `run:` through `env:`, and sets `timeout-minutes` from measured green runs of a consumer project: 3 × the longest, rounded up to 5 minutes, at least 5. `ci-java.yml`'s `dependency-check` takes GitHub's 360-minute limit, since a cold NVD sync took 13,987 s. A larger project raises a timeout from its own runs. The kit lints every template with actionlint and zizmor (KIT-076).
- `ISSUE_TEMPLATE/task.md` is the body contract the `sdd-tasks` cut fills (`TASK-nnn` files with `tracker: none` carry the same fields); the `Directive` tiers map to vendor models in the project, never in the kit.
- `REVIEW.md` holds the five review criteria (scope, correctness, architecture, security, docs) without project-specific gates; a project adds its own gates (coverage, mutation score, contract version field) under the matching heading. Each line ends with the rule, skill section or reference that holds it; `sdd-constitution` § 5 writes the project's copy and removes the lines a project gate already enforces (KIT-067). Hosted Claude Code Review (Team/Enterprise) reads it from the repository root; the local `/code-review` command does not (it reads `CLAUDE.md`); both facts checked against code.claude.com/docs/en/code-review on 2026-10-06.

## The kit pin in a project's CI (KIT-081, option B)

A project's workflows reach the kit only through the spec-tools action, pinned to a full commit SHA with the release in a comment:

```yaml
- uses: ChristianPrzybulinski/agent-rules-kit/platforms/ci/actions/spec-tools@<40-character SHA>  # vX.Y.Z
```

The SHA is the pin: GitHub recommends a full-length commit SHA as the only immutable reference to an action, and a tag can move. The comment names the release, which is how Dependabot and Renovate tell which version the SHA is and rewrite both on a bump. `sync-project.sh` writes the line from the kit it runs from (`git rev-parse HEAD`, and `VERSION` for the comment), so a sync from `~/.ai-kit`, which follows the newest release, pins a release; from another commit it warns that the commit must be on GitHub.

Let a bot bump the pin when the kit releases, so no project PR rewrites copies (each bump is one line) and a red bump shows the kit change that broke the project before it lands. Dependabot's `github-actions` ecosystem updates a `uses:` ref pinned by SHA with a version comment, the SHA and the comment together:

```yaml
# .github/dependabot.yml in the project
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    groups:
      agent-rules-kit:
        patterns: ["ChristianPrzybulinski/agent-rules-kit*"]
    cooldown:
      default-days: 2  # a release can be withdrawn before the project takes it
```

Dependabot opens the pull request and never merges it: turn auto-merge on for it (`gh pr merge --auto --squash` from a workflow that runs only for `dependabot[bot]`), so it merges once the required checks pass. Renovate does both from its config: the `helpers:pinGitHubActionDigests` preset keeps actions pinned by digest with the version comment, and a `packageRules` entry for the kit with `"automerge": true` merges a green bump. Either way the bump changes the workflow file, so its `paths` filter must include the file itself (the `spec-lint.yml` template does), or the check the bump updates never runs on it.

Moving from the copy an older sync wrote: run `sync-project.sh <repo>` once; it removes the generated copy (kit-named files only, and keeps any other file with a `sync: kept` line), writes `spec-lint.yml` when no workflow runs the spec tools, and names each workflow line that still runs the old copy. Replace those steps with the action (`checks: spec,trace,rows` covers `check_spec.py`, the doc-structure check, the baseline, `spec_trace.py check` and the row checks), or run another kit tool after it from `$AI_KIT_DIR` (`python3 "$AI_KIT_DIR/platforms/ci/validations/spec_trace.py" sync-status --write`, as the `spec-status-sync.yml` template does), then add the Dependabot or Renovate entry. `sync-project.sh --check` passes once no generated copy and no workflow line naming it is left.
