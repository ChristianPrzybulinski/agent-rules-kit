# quality-security/ — ai-kit security — secure design and scanning

## `skills/`

| Skill | Description |
|---|---|
| `secure-development` | Security design for dependencies, auth, endpoints and sensitive data. Use when changing a trust boundary. Not for scanning changes (skill vuln-scan). |
| `vuln-scan` | Scan for CVEs, secrets and changed endpoints. Use when preparing a sensitive PR, release or requested audit. Not for security design (skill secure-development). |

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
