# Kit maintenance

## Versioning

A release changes [`VERSION`](../VERSION), adds a [`CHANGELOG.md`](../CHANGELOG.md) entry and tags `vX.Y.Z`. `.github/workflows/release.yml` validates tag == `VERSION` and creates the release automatically.

A layout or installation-destination change is a SemVer MAJOR change. There is no separate layout version: migration behavior belongs in `bootstrap.sh`, `doctor.sh` and the release notes.

## Adding content

| Type | Steps |
|---|---|
| rule | create `plugins/ai-kit/rules/<name>.md` with `description`, `trigger: glob|model_decision|manual`, and `globs` for a glob rule; list it in the table of `plugins/ai-kit/INDEX.md` (never add non-rule files to `plugins/ai-kit/rules/` — Devin loads every `.md` there as a rule) |
| skill | copy [`../plugins/ai-kit/templates/kit-skill.md`](../plugins/ai-kit/templates/kit-skill.md) to `plugins/ai-kit/skills/<name>/SKILL.md`; for an exactly `[user]` trigger add `plugins/ai-kit/skills/<name>/agents/openai.yaml` with implicit invocation disabled; add a verbatim description row to `plugins/ai-kit/skills/INDEX.md` |
| reference | copy [`../plugins/ai-kit/templates/kit-reference.md`](../plugins/ai-kit/templates/kit-reference.md) to `plugins/ai-kit/skills/<owner>/references/<topic>.md`; set `kind: fact` with date/sources or `kind: detail`; keep ≤60 lines and link it from `SKILL.md` |
| subagent profile | add `plugins/ai-kit/agents/<name>.md` with frontmatter validated by `platforms/ci/schemas/agent.schema.json`; profiles are local-Devin only |
| template | add `plugins/ai-kit/templates/<prefix>-<name>.md`, then list it in `plugins/ai-kit/templates/INDEX.md` |

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

Hooks are a guard, not a guardrail: they fail open, load only in local Devin and cannot replace user confirmation or the always-on safety boundaries.

## Third-party skills

Pinned sources live in `platforms/kits/third-party/skills.lock`. Update the SHA, license and verification date, then run:

```bash
platforms/tools/vendor.sh
platforms/tools/vendor.sh --check
```

The command regenerates `plugins/ai-kit/skills/<name>/` and its `VENDOR.md`. Remove a vendor by deleting both its lock line and skill folder.

## CI requirements

- `.github/workflows/ci.yml`: ShellCheck on tools/kits, `check.sh`, `smoke.sh`, and `check_kit.py --links`.
- `check_kit.py` also gates allowed tools, user-only Codex policy parity, reference kinds/sources, backtick paths and exact skill-index descriptions.
- `.github/workflows/gitleaks.yml`: secret scan on pushes and pull requests.
- `.github/workflows/release.yml`: tag/version validation and release creation.

## After merging to main

- Devin Cloud needs no manual refresh; it fetches `main` for each session.
- Devin CLI/Desktop re-fetches at app start; run `devin plugins update ai-kit` to force it.
- Codex refreshes through launchd and `platforms/tools/refresh.sh`; run `platforms/tools/doctor.sh` to diagnose local state.

This machine's prerequisites (2026-10-01): Godot 4.7.2 · JDK 25 (`/opt/homebrew/opt/openjdk@25`, keg-only — via `toolchains.xml`) and JDK 27 on PATH · Maven 3.9.16 · Node 26.10.0/npm 11.19.1 · Docker 29 + Compose v5 · gh 2.101 · git-lfs 3.8 · DBeaver · Krita · Devin Desktop with plugin `ai-kit` from `main` · Codex desktop app (CLI not on PATH, so doctor uses app-only mode). System Python 3 has `pyyaml` 6.0.3 and `jsonschema` 4.25.1.
