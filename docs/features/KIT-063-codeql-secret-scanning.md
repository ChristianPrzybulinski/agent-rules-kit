---
id: KIT-063
title: "CodeQL on dispatch and secret scanning with push protection for the public kit"
status: done
confirmed: "2026-11-13 (owner, chat of the CodeQL evaluation session: \"Sim, pode\")"
issue: "#221"
pr: "#222"
---

# KIT-063 — CodeQL on dispatch and secret scanning with push protection for the public kit

## Problem and evidence

[FACT] The kit has been public under MIT since KIT-025 (#125, merged 2026-11-02). On 2026-11-13,
`gh api repos/ChristianPrzybulinski/agent-rules-kit` showed `visibility: public` and every `security_and_analysis` item
`disabled`. `gh api repos/ChristianPrzybulinski/agent-rules-kit/code-scanning/default-setup` showed
`state: not-configured`, with the detected languages `actions`, `java-kotlin` and `python`. The only secret check was
gitleaks, run locally per PR and by dispatch (`gitleaks.yml`). No static analysis covered the 20 Python files under
`platforms/` or the workflows.

[FACT] Both features are free here and cannot bill the owner's account:

- GitHub's Actions billing page lists "Standard GitHub-hosted runners in public repositories" as free usage that "does
  not reduce the included compute usage". The secret scanning page says "Public repositories: Secret scanning runs
  automatically for free". The GitHub Advanced Security comparison marks code scanning, secret scanning, push protection
  and the CodeQL CLI as available on public repositories without the paid product.
- `gh api "users/ChristianPrzybulinski/settings/billing/usage?year=2026&month=<m>"` lists only the `actions` and
  `git_lfs` products from January to November 2026, with no Code Security or Secret Protection SKU. The kit's Actions
  minutes were billed only in October, while it was private (346 minutes, US$ 0.76 net). November so far: 5 minutes,
  US$ 0.00 net.
- `users/ChristianPrzybulinski/settings/billing/advanced-security` returns 404. That billing endpoint exists only for
  organizations and enterprises, so no Advanced Security meter exists for a user-owned repository.

[FACT] `java-kotlin` comes from `platforms/kits/docker/Dockerfile.java`, which is a Dockerfile. `gh api
repos/ChristianPrzybulinski/agent-rules-kit/languages` counts its 492 bytes as Java. CodeQL supports neither shell nor
GDScript, so the 11 `*.sh` files stay with ShellCheck in `ci.yml`.

[FACT] GitHub's "About setup types for code scanning" page says default setup scans "On each push to the repository's
default branch, or any protected branch", on pull requests against the default branch, and weekly. At the measured
pace of 70 merged PRs from 2026-10-30 to 2026-11-13, that is at least 140 automatic runs in two weeks. KIT-014 allows
no kit workflow on push or pull request.

[HYPOTHESIS] The CodeQL `actions` extractor reads `.github/workflows/*.yml` (the extension its supported-languages page
lists), so the five workflows the kit ships in `platforms/kits/github/workflows/` are not analyzed.

## Change

- Repository settings, set on 2026-11-13 after the owner's OK with `gh api -X PATCH
  repos/ChristianPrzybulinski/agent-rules-kit` and
  `{"security_and_analysis": {"secret_scanning": {"status": "enabled"}, "secret_scanning_push_protection": {"status": "enabled"}}}`.
  `secret_scanning_non_provider_patterns` and `secret_scanning_validity_checks` stay `disabled`, because their price on
  a public repository was not confirmed. Code scanning default setup stays `not-configured`: with default setup on,
  GitHub rejects the advanced-setup SARIF upload.
- `.github/workflows/codeql.yml` (new, `workflow_dispatch` only): CodeQL advanced setup with a `python` and `actions`
  matrix and `build-mode: none`. `github/codeql-action/init` and `analyze` are pinned to commit
  `33d7b85da1a04171e211befe2c739303b9a4c066` (`# v4.39.3`). Skill `security` § 6 says "pin third-party actions by
  commit sha", and #174 keeps only GitHub's `actions/*` on major tags; `github/codeql-action` is outside that set.
  Dependabot's weekly `github-actions` update bumps the pin. The job gets `security-events: write` to upload
  the results, and the checkout keeps no credentials.
- `CONTRIBUTING.md` § CI requirements lists the workflow and when to dispatch it. `README.md` adds it to the
  `.github/` row. `gitleaks.yml` is unchanged.

The SHA was resolved like this: `gh api repos/github/codeql-action/git/matching-refs/tags/v4` lists `v4.39.3` as the
latest `v4.x.y`, and it is an annotated tag object (`f3bbb05694c2f74569081c28664c0866d64dec21`).
`gh api repos/github/codeql-action/git/tags/f3bbb05694c2f74569081c28664c0866d64dec21` resolves it to commit `33d7b85d…`,
tagged 2026-11-04. No `v5` tag exists.

Gitleaks and secret scanning complement each other:

- Gitleaks runs locally before the push and uses generic rules and entropy.
- Secret scanning watches every branch continuously, matches provider patterns and raises alerts in the Security tab.
- Push protection is the only server-side block. The owner's account-level "push protection for users", on by
  default, already blocks the owner's own pushes to public repositories. Repository-level push protection adds an
  alert when someone bypasses it and covers any other pusher.

## Options considered

| Option | Verdict |
|---|---|
| A. Advanced setup on `workflow_dispatch`, `python` + `actions`, plus secret scanning and push protection (chosen) | 0 automatic runs (KIT-014), explicit languages, alerts current as of the last dispatch |
| B. Default setup limited to `python` + `actions` | no workflow file and alerts on every PR, but at least 140 automatic runs in two weeks at the measured pace, against KIT-014 |
| C. Secret scanning only, no CodeQL | nothing to maintain, but no workflow-injection or permission checks and no analysis of the Python tools |

What would prove A wrong:

- The day after the first dispatch, the kit's `Actions Linux` row in the billing usage shows `netAmount` > 0.
- Nobody dispatches it in about 30 days, or across two releases, even though Python or workflow files changed.
- Two dispatches in a row find 0 alerts; then option C was enough.

## Proof

- `gh api repos/ChristianPrzybulinski/agent-rules-kit --jq .security_and_analysis` after the PATCH:
  `secret_scanning` and `secret_scanning_push_protection` are `enabled`.
- The kit gates: `bash platforms/tools/check.sh`, `CI=1 bash platforms/tools/check.sh`,
  `bash platforms/tools/smoke.sh`, `python3 platforms/ci/validations/check_kit.py --links` and
  `gitleaks git --redact --log-opts="origin/main..HEAD"`.
- After the merge, the first `gh workflow run codeql.yml` measures the run's minutes and cost. A dispatch needs the file
  on the default branch.

## History

- 2026-11-13: evaluated in a session started by the owner's CodeQL question and confirmed by the owner in chat ("Sim,
  pode"). Secret scanning and push protection enabled the same day; workflow implemented.
