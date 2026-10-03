# infra-core/ — ai-kit infra — runtime and operations

## `skills/`

| Skill | Description |
|---|---|
| `docker` | Docker and Compose workflow. Use when editing compose, a Dockerfile or diagnosing a container that will not start. Not for app config (skill twelve-factor). |
| `git-lfs` | Git LFS policy. Use when editing .gitattributes, adding/migrating a large binary or checking quota. Not for branch policy (skill branching-and-versioning). |
| `twelve-factor` | Twelve-Factor application configuration. Use when changing config, env vars, deploy behavior or Docker app config. Not for container mechanics (skill docker). |

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
