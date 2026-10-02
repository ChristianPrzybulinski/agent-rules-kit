# agent-rules-kit — repository index

Version: [`VERSION`](VERSION) · History: [`CHANGELOG.md`](CHANGELOG.md).

The repository separates plugin content from maintenance tooling. Devin installs `ChristianPrzybulinski/agent-rules-kit#kit`; Codex reads the root marketplace catalog, whose plugin path is `./kit`.

## Repository roots

| Root | Purpose |
|---|---|
| [`kit/`](kit/INDEX.md) | `ai-kit` plugin root: global rules, triggered rules, skills, references, templates and manifests |
| [`AGENTS.md`](AGENTS.md) | project rules for maintaining this repository |
| [`platforms/`](platforms/INDEX.md) | lifecycle tools, validators and ready-to-copy kits |
| [`docs/`](docs/INDEX.md) | architecture and maintenance documentation |
| [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) | Codex marketplace catalog pointing to `./kit` |
| [`.github/`](.github/README.md) | CI, release and security automation |

## Plugin rules

| File | Trigger | Globs | Loads |
|---|---|---|---|
| [`kit/rules/java.md`](kit/rules/java.md) | `glob` | `**/*.java`, `**/pom.xml` | `java-standards`, `clean-code`, `testing` |
| [`kit/rules/godot.md`](kit/rules/godot.md) | `glob` | `**/*.gd`, `**/*.tscn`, `**/project.godot` | `godot-standards`, `clean-code`, `testing` |
| [`kit/rules/spec.md`](kit/rules/spec.md) | `glob` | `docs/spec/**/*.md` | SDD skills and spec templates |

## What goes where

| Content | Location |
|---|---|
| always-on global behavior | `kit/AGENTS.md` |
| triggered rule | `kit/rules/<name>.md` |
| procedure/reference | `kit/skills/<name>/` |
| artifact skeleton | `kit/templates/<prefix>-<name>.md` |
| repository maintenance rule | root `AGENTS.md` |
| executable/schema/project kit | `platforms/` |

## Invariants

- Nothing except the plugin manifests and documented content roots enters `kit/`.
- `VERSION`, `kit/.devin-plugin/plugin.json` and `kit/plugin.json` agree.
- Marketplace source path is `./kit`; plugin content has no managed duplicate outside the repository.
- Every skill appears in `kit/skills/INDEX.md`; every triggered rule appears in this index.
- `platforms/tools/check.sh` and `platforms/tools/smoke.sh` pass before a PR.
