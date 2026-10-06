# all/ — ai-kit bundle

Manifest-only plugin: installs every ai-kit plugin except the opt-in `extras` through dependency resolution. No content of its own.
Not included: `extras` (opt-in; install it explicitly).

| Depends on |
|---|
| `core` · `dev-core` · `dev-java` · `dev-godot` · `architect-core` · `architect-sdd` · `quality-core` · `quality-security` · `infra-core` · `infra-persistence` · `infra-github` |

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
