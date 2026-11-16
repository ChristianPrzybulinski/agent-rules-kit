# gitleaks — the kit's secret scan for a project's CI

`action.yml` is a composite action (KIT-084): it installs the gitleaks CLI at a pinned version, checked against its sha-256, and scans the checked-out repository with every value redacted. A project calls it as a step of any job, pinned by commit SHA, so the scan stays in the kit and each run bills one job. A reusable workflow cannot serve that: GitHub calls one across repositories only from a repository's `.github/workflows/`, so the kit's `platforms/kits/github/workflows/gitleaks.yml` template is a file to copy, and that template now calls this action.

```yaml
steps:
  - uses: actions/checkout@<SHA>  # vX.Y.Z
    with:
      fetch-depth: 0  # the whole history, and a pull request's base commit
      persist-credentials: false
  - uses: ChristianPrzybulinski/agent-rules-kit/platforms/ci/actions/gitleaks@<40-character SHA>  # vX.Y.Z
    with:
      config: ''  # optional
```

| Input | Default | What it does |
|---|---|---|
| `config` | `''` | a gitleaks config, as a path in the repository; empty: `.gitleaks.toml` at the root when present, else gitleaks' built-in rules. `.gitleaksignore` at the root (reviewed fingerprints) always applies |

- **Range by event.** On a `pull_request` the scan reads the pull request's commits (`base..head`), so a secret already on the base branch does not fail every pull request; the step fails with an error when the base commit is not in the checkout (`fetch-depth: 0` fetches it). On a push, a dispatch or any other event it reads the whole history of the checked-out ref (`--log-opts=HEAD`). A finding fails the step (`--exit-code 1`), and `--redact` keeps its value out of the log.
- **The pin.** The CLI version and sha-256 are the ones the kit's own `.github/workflows/gitleaks.yml` installs; a test (`platforms/ci/validations/test_gitleaks_template.py`) keeps them equal, and `test_kit_workflows.py` holds the kit's CI jobs that run the gitleaks tests to the same pin. The CLI, not `gitleaks/gitleaks-action`: in an organization's repository that action needs a `GITLEAKS_LICENSE` secret and exits 1 before scanning without one.
- **Updates.** Pin the action by a kit release's full commit SHA with the version in a comment; Dependabot or Renovate bumps the line when the kit releases, as for the spec-tools action (`platforms/kits/github/README.md` has the configuration). The kit's own Dependabot and its zizmor job cover this folder.

The local scan before a pull request is the `security` skill's `scan.md` reference: `gitleaks git --redact --log-opts="origin/main..HEAD"`.
