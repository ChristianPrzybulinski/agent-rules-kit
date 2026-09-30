# agents/ — what enters the agent's context

Scope: only content that changes an agent behavior. Each file loads on demand via its `description`/`trigger`; the only always-on file is `AGENTS.md`. Definitions and the quick "what goes where" test: [`../INDEX.md`](../INDEX.md).

| Folder | Scope | Limit | Template | Schema |
|---|---|---|---|---|
| `AGENTS.md` | durable discipline, routing to the rest | ≤110 lines | — | — |
| [`knowledge/`](knowledge/INDEX.md) | dated facts with source (versions, quotas, APIs, glossaries) | ≤40 lines each | `templates/kit-knowledge.md` | `knowledge.schema.json` |
| [`skills/`](skills/INDEX.md) | invocable procedures + normative detail (`references/`), by type: `core` · `quality` · `development` · `documentation` · `process` · `tooling` · `vendor` | ≤80 lines (own) | `templates/kit-skill.md` | `skill.schema.json` |
| [`templates/`](templates/INDEX.md) | artifact skeletons: `spec-*` (project docs/spec) · `doc-*` (reports, handoffs, checklists) · `project-*` (project AGENTS.md) · `kit-*` (this kit's content) | — | — | name by regex |
| [`prompts/`](prompts/INDEX.md) | derivatives of `AGENTS.md` for ChatGPT (compact/full) | — | — | — |

## When the agent loads what

| Situation | Loads |
|---|---|
| Every session | `AGENTS.md` (and runs `platforms/tools/refresh.sh --quiet`) |
| Context matches a skill's `description` | the skill (`/name`) — one at a time, the most specific; normative detail in its `references/` |
| Needs a number/version/URL | the domain's knowledge note |
| About to create FEAT/REQ/DEC/DEBT/report | the corresponding template |

Duplication is a bug: if a text appears in two files here, one of them references the other.
