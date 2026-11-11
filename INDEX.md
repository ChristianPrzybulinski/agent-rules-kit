# agent-rules-kit — repository index

Version: [`VERSION`](VERSION) · History: [`CHANGELOG.md`](CHANGELOG.md).

The repository root is a content-free meta-plugin. Its [manifest](.devin-plugin/plugin.json) requires the `all` bundle through `git-subdir` and lists every content plugin as optional; Codex and Claude Code use root marketplace catalogs listing every plugin.

## Repository roots

| Root | Purpose |
|---|---|
| [`.devin-plugin/plugin.json`](.devin-plugin/plugin.json) | meta-plugin manifest requiring `plugins/core/` through `git-subdir` |
| [`plugins/`](plugins/) | plugin family: core, satellites, the `all` bundle and the opt-in `extras` |
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
| [`plugins/core/`](plugins/core/INDEX.md) | — | always-on rules, hook guard, session and collaboration skills, session handoff template |
| [`plugins/dev-core/`](plugins/dev-core/INDEX.md) | `core` | code patterns: code standards, testing, docs, investigation |
| [`plugins/dev-java/`](plugins/dev-java/INDEX.md) | `dev-core` | `rules/java.md`, Java 25/Spring standards |
| [`plugins/dev-godot/`](plugins/dev-godot/INDEX.md) | `dev-core` | `rules/godot.md`, Godot 2D, asset import |
| [`plugins/architect-core/`](plugins/architect-core/INDEX.md) | `core` | architecture (layers, ports, DDD), protocol contracts, grilling |
| [`plugins/architect-sdd/`](plugins/architect-sdd/INDEX.md) | `architect-core`, `infra-github` | `rules/spec.md`, `researcher` profile, the sdd-* pipeline + journey layer, spec templates |
| [`plugins/quality-core/`](plugins/quality-core/INDEX.md) | `core` | `reviewer` profile, skeptic, validate-implementation |
| [`plugins/quality-security/`](plugins/quality-security/INDEX.md) | `quality-core` | secure development, vulnerability scanning |
| [`plugins/infra-core/`](plugins/infra-core/INDEX.md) | `core` | Docker, Git LFS, twelve-factor |
| [`plugins/infra-persistence/`](plugins/infra-persistence/INDEX.md) | `infra-core` | PostgreSQL, Redis |
| [`plugins/infra-github/`](plugins/infra-github/INDEX.md) | `infra-core` | gh workflow, branching and versioning, review gates |
| [`plugins/extras/`](plugins/extras/INDEX.md) | `core` | opt-in: frontend-design, krita, dbeaver, find-skills, skill-creator (not in `all`) |
| [`plugins/process-loop/`](plugins/process-loop/INDEX.md) | `core`, `infra-github`, `quality-core` | loop orchestrator, verdict reviewer, child implement/fix skills, verdict and batch-report templates |
| [`plugins/all/`](plugins/all/INDEX.md) | all above except `extras` | manifest-only bundle: install everything except `extras` |

## Plugin rules

| File | Trigger | Globs | Loads |
|---|---|---|---|
| [`plugins/dev-java/rules/java.md`](plugins/dev-java/rules/java.md) | `glob` | `**/*.java`, `**/pom.xml` | inline always/never; procedures in `java-standards`, `code-standards`, `testing` |
| [`plugins/dev-godot/rules/godot.md`](plugins/dev-godot/rules/godot.md) | `glob` | `**/*.gd`, `**/*.tscn`, `**/project.godot` | inline always/never; procedures in `godot-standards`, `code-standards`, `testing` |
| [`plugins/architect-sdd/rules/spec.md`](plugins/architect-sdd/rules/spec.md) | `glob` | `docs/spec/**/*.md` | inline always/never; procedures in the `sdd-*` skills and spec templates |

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

- The repository root contains no agent-facing content; `.devin-plugin/plugin.json` requires the `all` bundle and lists every content plugin as optional.
- Every directory under `plugins/` is a plugin with `.devin-plugin/plugin.json`, `.claude-plugin/plugin.json`, `plugin.json` and `INDEX.md`.
- `plugins/core/` is the only plugin with `AGENTS.md` or `hooks/`; `plugins/all/` is the only manifest-only plugin.
- Plugin names are unique across the repo and referenced skills/agents must be reachable through the dependency graph.
- `VERSION`, the meta-plugin manifest and all Devin, Codex and Claude plugin manifests agree.
- Codex and Claude marketplace source paths are `./plugins/<name>`; plugin content has no managed duplicate.
- Every skill and template appears in its plugin's `INDEX.md`; every triggered rule appears in this index.
- `plugins/all/` requires every content plugin except the opt-in `extras`; `check_kit.py` `OPTIONAL_PLUGINS` is the single list of opt-in plugins.
