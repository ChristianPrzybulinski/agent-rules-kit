# dev/ — ai-kit dev — code, tests, Java, Godot, infra and persistence

Rules load by file glob: `rules/java.md` for Java files, `rules/godot.md` for Godot files.

## `skills/`

| Skill | Description |
|---|---|
| `asset-import` | Godot asset import with manifests and reproducible transforms. Use when bringing sprites, tilesets or maps into Godot. Not for drawing art (skill krita). |
| `code-standards` | Code names, functions, errors, YAGNI and doc closure. Use when writing or reviewing code, adding a dependency or updating docs. Not for tests (skill testing). |
| `docker` | Docker, Compose and Twelve-Factor config. Use when editing compose, Dockerfile, env or deploy config, or fixing a container. Not for data (skill persistence). |
| `godot-standards` | Godot 2D and typed GDScript standards. Use when editing *.gd, *.tscn, project.godot or GDScript scenes. Not for asset import (skill asset-import). |
| `investigate` | Root-cause investigation with reproduction. Use when a bug, slow behavior or incident has no named cause. Not for implementing fixes (skill sdd-implement). |
| `java-standards` | Java 25, Spring/Quarkus and JUnit standards. Use when editing *.java, pom.xml, Spring/Quarkus code or JUnit tests. Not for general test policy (skill testing). |
| `krita` | Krita pixel-art workflow. Use when editing pixel art, retouching sprites or defining sprite export. Not for Godot import (skill asset-import). |
| `persistence` | PostgreSQL and Redis rules. Use when changing a schema, migration or index, reading EXPLAIN or locks, or designing cache keys. Not for Compose (skill docker). |
| `testing` | Test policy, gates and characterization tests. Use when setting coverage/mutation gates, choosing tests or pinning legacy code. Not for verdicts (skill review). |

## `rules/`

- `godot.md`
- `java.md`

## `templates/`

- `project-agents-godot-2d.md`
- `project-agents-java-spring.md`

## `evals/`

- `code-standards-one-decision-one-place`
- `godot-standards-boot-exit-code`
- `java-standards-no-field-injection`
- `testing-empty-return-passes`

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
