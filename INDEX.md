# agent-rules-kit — repository index

Version: [`VERSION`](VERSION) · History: [`CHANGELOG.md`](CHANGELOG.md).

The repository root is a content-free meta-plugin. Its [manifest](.devin-plugin/plugin.json) requires the three plugins (`core`, `dev`, `sdd`) through `git-subdir`; Codex and Claude Code use root marketplace catalogs listing the same three.

## Repository roots

| Root | Purpose |
|---|---|
| [`.devin-plugin/plugin.json`](.devin-plugin/plugin.json) | meta-plugin manifest requiring every plugin through `git-subdir` |
| [`plugins/`](plugins/) | the three plugins: `core`, `dev`, `sdd` |
| [`platforms/`](platforms/INDEX.md) | lifecycle tools, validators and ready-to-copy kits |
| [`docs/`](docs/INDEX.md) | architecture and maintenance documentation |
| [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) | Codex marketplace catalog pointing to `./plugins/*` |
| [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) | Claude Code marketplace catalog pointing to `./plugins/*` |
| [`.github/`](.github/README.md) | CI, release and security automation |
| [`LICENSE`](LICENSE) | MIT; vendored third-party skills keep their own licenses (README § License) |
| [`SECURITY.md`](SECURITY.md) | how to report a vulnerability privately; supported versions and scope |

## Plugins

| Plugin | Requires | Content |
|---|---|---|
| [`plugins/core/`](plugins/core/INDEX.md) | — | always-on rules, hook guard, session and collaboration skills; review (`reviewer` profile, skeptic, validate-implementation); GitHub workflow (gh, branching and versioning, review gates); security (secure development, vulnerability scanning) |
| [`plugins/dev/`](plugins/dev/INDEX.md) | `core` | `rules/java.md`, `rules/godot.md`; code standards, testing, docs, investigation, Java 25/Spring, Godot 2D, asset import, Krita, Docker, Git LFS, twelve-factor, PostgreSQL, Redis |
| [`plugins/sdd/`](plugins/sdd/INDEX.md) | `core` | `rules/spec.md`, `researcher` profile; architecture (layers, ports, DDD), protocol contracts, grilling, the sdd-* pipeline + journey layer, spec templates |

## Plugin rules

| File | Trigger | Globs | Loads |
|---|---|---|---|
| [`plugins/dev/rules/java.md`](plugins/dev/rules/java.md) | `glob` | `**/*.java`, `**/pom.xml` | inline always/never; procedures in `java-standards`, `code-standards`, `testing` |
| [`plugins/dev/rules/godot.md`](plugins/dev/rules/godot.md) | `glob` | `**/*.gd`, `**/*.tscn`, `**/project.godot` | inline always/never; procedures in `godot-standards`, `code-standards`, `testing` |
| [`plugins/sdd/rules/spec.md`](plugins/sdd/rules/spec.md) | `glob` | `docs/spec/**/*.md` | inline always/never; procedures in the `sdd-*` skills and spec templates |

## What goes where

| Content | Location |
|---|---|
| always-on global behavior | `plugins/core/AGENTS.md` |
| hook guard and format/lint hooks | `plugins/core/hooks/hooks.json` |
| triggered rule | `plugins/<plugin>/rules/<name>.md` in the owning plugin |
| procedure/reference | `plugins/<plugin>/skills/<name>/` |
| subagent profile | `plugins/<plugin>/agents/<name>.md` in the plugin whose skills consume it |
| artifact skeleton | `plugins/<plugin>/templates/<prefix>-<name>.md` |
| executable/schema/project kit | `platforms/` |
| maintainer guidance | README `Maintainers` section and `docs/maintenance.md` |

## Invariants

- The repository root contains no agent-facing content; `.devin-plugin/plugin.json` requires every plugin and lists none as optional.
- Every directory under `plugins/` is a plugin with `.devin-plugin/plugin.json`, `.claude-plugin/plugin.json`, `plugin.json` and `INDEX.md`.
- `plugins/core/` is the only plugin with `AGENTS.md` or `hooks/`.
- Plugin names are unique across the repo and referenced skills/agents must be reachable through the dependency graph.
- `VERSION`, the meta-plugin manifest and all Devin, Codex and Claude plugin manifests agree.
- Codex and Claude marketplace source paths are `./plugins/<name>`; plugin content has no managed duplicate.
- Every skill and template appears in its plugin's `INDEX.md`; every triggered rule appears in this index.
- The Claude marketplace `renames` map sends each retired plugin name to its successor (or `null`), so an installed old name migrates on the next session (KIT-038).
