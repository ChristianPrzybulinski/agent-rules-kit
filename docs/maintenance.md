# Kit maintenance

## Versioning

A release changes [`VERSION`](../VERSION), adds a [`CHANGELOG.md`](../CHANGELOG.md) entry and tags `vX.Y.Z`. `.github/workflows/release.yml` validates tag == `VERSION` and creates the release automatically.

A layout or installation-destination change is a SemVer MAJOR change. There is no separate layout version: migration behavior belongs in `bootstrap.sh`, `doctor.sh` and the release notes.

## Adding content

| Type | Steps |
|---|---|
| rule | create `plugins/<plugin>/rules/<name>.md` in the owning plugin with `description`, `trigger: glob|model_decision|manual`, and `globs` for a glob rule; list it in the plugin's `INDEX.md` and the root `INDEX.md` rules table (never add non-rule files to `rules/` — Devin loads every `.md` there as a rule) |
| skill | copy [`../plugins/core/templates/kit-skill.md`](../plugins/core/templates/kit-skill.md) to `plugins/<plugin>/skills/<name>/SKILL.md`; user-only means exactly `triggers: [user]`, Codex `agents/openai.yaml` with implicit invocation disabled, and Claude `disable-model-invocation: true`; add the verbatim description to the plugin's `INDEX.md` |
| reference | copy [`../plugins/core/templates/kit-reference.md`](../plugins/core/templates/kit-reference.md) to `plugins/<plugin>/skills/<owner>/references/<topic>.md`; set `kind: fact` with date/sources or `kind: detail`; keep ≤60 lines and link it from `SKILL.md` |
| subagent profile | add `plugins/<plugin>/agents/<name>.md` in the plugin whose skills consume it (reachable through the dependency graph) with frontmatter validated by `platforms/ci/schemas/agent.schema.json`; profiles are local-Devin only |
| template | add `plugins/<plugin>/templates/<prefix>-<name>.md`, then list it in the plugin's `INDEX.md` |
| plugin | create `plugins/<name>/` with `.devin-plugin/plugin.json`, `.claude-plugin/plugin.json`, `plugin.json` and `INDEX.md`; declare `requiredPlugins`/`dependencies` on the plugins it consumes; register it in the root meta-plugin `optionalPlugins`, `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`; add it to `all`'s manifests |

A rule uses this frontmatter shape:

```yaml
---
description: <what loads and when, at most 160 characters>
trigger: glob
globs:
  - "<glob>"
  - "<glob>"
---
```

`globs` must be a YAML sequence: Devin rejects a comma-separated string (`YAML parse error: globs: invalid type: string ..., expected a sequence`).

Use `kit-index.md` for a directory listing or `kit-readme.md` for explanation; never put both in one directory.

A subagent skill sets Devin `subagent: true` or a shared `agent: <profile>`, plus Claude `context: fork` and `background: false`; named profiles must exist under `plugins/<plugin>/agents/` of a plugin reachable through the dependency graph.

Hooks are a guard, not a guardrail: they fail open, load only in local Devin and Claude Code, and cannot replace user confirmation or the always-on safety boundaries.

## Third-party skills

Pinned sources live in `platforms/kits/third-party/skills.lock`. Update the SHA, license and verification date, then run:

```bash
platforms/tools/vendor.sh
platforms/tools/vendor.sh --check
```

The command regenerates `plugins/<plugin>/skills/<name>/` and its `VENDOR.md`, where the plugin comes from the lock's second column. Remove a vendor by deleting both its lock line and skill folder.

## CI requirements

- `.github/workflows/ci.yml`: ShellCheck on tools/kits, `check.sh`, `smoke.sh`, and `check_kit.py --links`.
- Scripts under `platforms/` must parse under bash 3.2 (macOS `/bin/bash`, the `smoke.sh` restricted PATH): avoid unquoted text after a quoted string inside `"$(...)"` — write `"$(basename "$f")"`/`"${f##*/}"` instead of `"$(basename "$f" .md)"`.
- `check.sh` runs `claude plugin validate` on the plugin and marketplace when Claude Code is installed.
- `check_kit.py` also gates allowed tools, three-way user-only/subagent/rule parity, reference kinds/sources, hooks, backtick paths and exact skill-index descriptions.
- `.github/workflows/gitleaks.yml`: secret scan on pushes and pull requests.
- `.github/workflows/release.yml`: tag/version validation and release creation.

## After merging to main

- Devin Cloud needs no manual refresh; it fetches `main` for each session.
- Devin CLI/Desktop re-fetches at app start; run `devin plugins update` to force it.
- Codex and Claude Code refresh through launchd and `platforms/tools/refresh.sh`; run `platforms/tools/doctor.sh` to diagnose local state.
- In Claude Code, use `/doctor prompt-audit` to inspect loaded instructions and `/context` to inspect token cost.

Machine notes live in `docs/machine.local.md`, git-ignored; see `docs/machine.local.md.example`.
