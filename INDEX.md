# agent-rules-kit — repository index

Version: [`VERSION`](VERSION) · History: [`CHANGELOG.md`](CHANGELOG.md).

The repository root is a content-free meta-plugin. Its [manifest](.devin-plugin/plugin.json) requires the real `ai-kit` plugin from `plugins/ai-kit/`; Codex and Claude Code use root marketplace catalogs with the same plugin path.

## Repository roots

| Root | Purpose |
|---|---|
| [`.devin-plugin/plugin.json`](.devin-plugin/plugin.json) | meta-plugin manifest requiring `plugins/ai-kit/` through `git-subdir` |
| [`plugins/ai-kit/`](plugins/ai-kit/INDEX.md) | real plugin: global rules, triggered rules, skills, references, templates and manifests |
| [`platforms/`](platforms/INDEX.md) | lifecycle tools, validators and ready-to-copy kits |
| [`docs/`](docs/INDEX.md) | architecture and maintenance documentation |
| [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) | Codex marketplace catalog pointing to `./plugins/ai-kit` |
| [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) | Claude Code marketplace catalog pointing to `./plugins/ai-kit` |
| [`.github/`](.github/README.md) | CI, release and security automation |

## Plugin rules

| File | Trigger | Globs | Loads |
|---|---|---|---|
| [`plugins/ai-kit/rules/java.md`](plugins/ai-kit/rules/java.md) | `glob` | `**/*.java`, `**/pom.xml` | `java-standards`, `clean-code`, `testing` |
| [`plugins/ai-kit/rules/godot.md`](plugins/ai-kit/rules/godot.md) | `glob` | `**/*.gd`, `**/*.tscn`, `**/project.godot` | `godot-standards`, `clean-code`, `testing` |
| [`plugins/ai-kit/rules/spec.md`](plugins/ai-kit/rules/spec.md) | `glob` | `docs/spec/**/*.md` | SDD skills and spec templates |

## What goes where

| Content | Location |
|---|---|
| always-on global behavior | `plugins/ai-kit/AGENTS.md` |
| triggered rule | `plugins/ai-kit/rules/<name>.md` |
| procedure/reference | `plugins/ai-kit/skills/<name>/` |
| artifact skeleton | `plugins/ai-kit/templates/<prefix>-<name>.md` |
| executable/schema/project kit | `platforms/` |
| maintainer guidance | README `Maintainers` section and `docs/maintenance.md` |

## Invariants

- The repository root contains no agent-facing content; `.devin-plugin/plugin.json` only requires the real plugin.
- Every directory under `plugins/` is a plugin with `.devin-plugin/plugin.json`.
- `VERSION`, the meta-plugin manifest and all Devin, Codex and Claude plugin manifests agree.
- Codex and Claude marketplace source paths are `./plugins/ai-kit`; plugin content has no managed duplicate.
- Every skill appears in `plugins/ai-kit/skills/INDEX.md`; every triggered rule appears in this index.
