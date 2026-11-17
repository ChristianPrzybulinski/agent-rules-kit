# spec-tools — the kit's spec validators for a project's CI

`action.yml` is a composite action (KIT-081 stage 1): it runs the kit's spec validators (`platforms/ci/validations/`) and schemas (`platforms/ci/schemas/`) from the kit commit the project pins, on the project's `docs/spec`. The project carries no copy of them, and the action fetches no other ref: every path starts at its own checkout (`$GITHUB_ACTION_PATH/../../`).

```yaml
steps:
  - uses: actions/checkout@<SHA>  # vX.Y.Z
    with:
      fetch-depth: 0  # the baseline step and the changed rows read the pull request's base commit
      persist-credentials: false
  - uses: ChristianPrzybulinski/agent-rules-kit/platforms/ci/actions/spec-tools@<40-character SHA>  # vX.Y.Z
    with:
      checks: spec,trace,rows
```

Pin the action by the full commit SHA of a kit release with the version in a comment; `platforms/tools/sync-project.sh` writes `.github/workflows/spec-lint.yml` that way, from the kit commit it runs from. Dependabot or Renovate bumps the line when the kit releases: `platforms/kits/github/README.md` has the configuration. Its path is part of the kit's layout (`docs/design.md`, Layout stability), so a move is a MAJOR release.

| Input | Default | What it does |
|---|---|---|
| `checks` | `spec` | comma-separated: `spec` runs `check_spec.py docs/spec`, `check_docs_structure.py` (it prints `off` and passes unless `sdd.doc_structure.enabled`) and, on a pull request, `check_spec.py --baseline-against` with the base commit's `docs/spec/baseline.json`, which may only shrink (KIT-068), or a line saying why nothing is compared (no base, a base commit missing from the checkout, no baseline there; KIT-083); `trace` runs `spec_trace.py check docs/spec`; `rows` runs `row_checks.py check`, `--changed <base> <head>` on a pull request and `--all` otherwise; `none` only sets the tools up. An unknown name fails the step |
| `base` | the pull request's base commit | where the baseline step and the changed rows start |
| `head` | the pull request's head commit | where the changed rows end |
| `profile` | `.ai-kit.yaml` | the project profile (KIT-087), relative to the repository root: `platforms/tools/profile.py resolve --json` resolves it, each key it does not set from its legacy home (the `sdd:` block, the `CLAUDE.md` sync marker, the gates JSON) or default, and the step exports the view as `AI_KIT_PROFILE_JSON` for a later step; an invalid profile, or a key set differently in the file and a legacy home, fails the step, and a missing file passes with a warning |

The action sets up Python 3.12 with `actions/setup-python` (pinned by SHA), installs `pyyaml` and `jsonschema`, so `check_spec.py` runs its full validation (`CI=1`), and exports `AI_KIT_DIR`, the kit root at the pinned commit, to `$GITHUB_ENV`: a later step of the job runs any other kit tool from there, as the `pr-contract.yml` template runs `"$AI_KIT_DIR/platforms/ci/validations/pr_gates.py"` after the action with `checks: none`. It also links `$HOME/.ai-kit` to that kit root when nothing is at that path (KIT-081 stage 1b), for a project justfile of its own that still imports a kit module as `import '~/.ai-kit/platforms/kits/just/<profile>.just'`, since an import path takes no variable; the kit's templates need no link, as they run `just -f "$AI_KIT_DIR/platforms/kits/just/<profile>.just" -d <folder> <recipe>` (KIT-085: no project justfile). A kit already there stays and must be at the action's commit (KIT-083): the step compares its `HEAD` with the action checkout's `HEAD`, or, since a runner downloads an action as an archive without `.git`, with the SHA the caller pins (`github.action_ref`); it passes with a notice when they are the same and fails when they differ or the action's commit is unknown (a pin by tag), as the justfile would otherwise run that other kit. The `ci-godot.yml` and `ci-java.yml` templates call the action that way before their first `just` step. A session on a developer's machine runs the same validators from the installed kit, `${AI_KIT_DIR:-$HOME/.ai-kit}/platforms/ci/validations/`, through the skills, the post-edit hook and the `docs` stack's `lint` recipe (skill `sdd-implement`).
