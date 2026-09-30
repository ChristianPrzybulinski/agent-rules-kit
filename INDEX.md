# agent-rules-kit — index

Version: see `VERSION` · Layout: see `LAYOUT_VERSION` (changes → full reinstall) · History: `CHANGELOG.md`.

A kit of rules, knowledge, skills and tools so AI agents (Devin, Cursor, Windsurf, Codex, ChatGPT) work with the same behavior. One place for each thing; nothing duplicated. If content fits two folders, the table below decides.

## The three folders

| Folder | What it is | Who consumes it | Admission rule |
|---|---|---|---|
| [`agents/`](agents/INDEX.md) | Everything that enters **the agent's context**: always-on instructions, skills (normative rules included), facts, templates the agent fills, prompts | the model, in session | Enters only if it changes an agent behavior. Each file has frontmatter with `description` + `trigger` and a line limit. |
| [`platforms/`](platforms/INDEX.md) | Everything that **runs on the machine or in CI**: installers, bootstrap/refresh, validations, schemas, config kits copied into projects | shell, CI, human | Enters only if it is executable or tool configuration. Nothing here is read by the agent as an instruction. |
| [`docs/`](docs/INDEX.md) | Documentation **about the kit**: design principles, what lives in projects, maintenance and versioning | human (and the agent only when maintaining the kit) | Explains the kit; does not instruct the agent in project tasks. |

## Inside `agents/` — do not confuse

| Content | Question it answers | Format | It is not |
|---|---|---|---|
| `AGENTS.md` | "How do I always behave?" | ≤110 lines, always-on, unique | a place for detail |
| `knowledge/` | "What is the verified fact (version, quota, API) and its source?" | factual, dated, ≤40 lines, with URL | a rule or an opinion |
| `skills/` | "How do I execute this task step by step?" and "what MUST/MUST NOT I do in this domain?" | invocable procedure `/name`; normative detail in `references/` | a dated fact |
| `templates/` | "What shape does this artifact have?" | skeleton with `[brackets]`, one per artifact type | ready-made content |
| `prompts/` | "What do I paste into a tool without AGENTS.md support?" | compiled text from AGENTS.md | source of truth (it is derived) |

Quick test: knowledge has a date and a URL; a skill has numbered steps and a "done when" (normative "must/never" detail lives in its `references/`); a template has brackets.

## Inside `platforms/`

| Folder | Scope |
|---|---|
| `install/` | installs `agents/` into the tools (Devin, Cursor, Windsurf, Codex) and vendors external skills |
| `tools/` | `bootstrap.sh` (first time) · `refresh.sh` (every session) · `check.sh` (validates the kit) |
| `ci/` | `schemas/` (JSON Schema for every frontmatter and for project specs) · `validations/` (scripts that CI and `check.sh` run) |
| `kits/` | ready-to-copy files for projects: Maven parent, Compose, workflows, LFS, labels |

## Reading order

1. This file.
2. `agents/AGENTS.md` — what always holds.
3. `agents/INDEX.md` → the skill for your context.
4. Going to create/change the kit? `docs/maintenance.md` first.

## Invariants (validated by `platforms/tools/check.sh` and by CI)

- Every folder has an `INDEX.md` (list + when to use) or a `README.md` (needs to explain more); never both.
- Every file in `agents/` has frontmatter valid against its type's schema and respects the line limit.
- Every relative link points to an existing file; every file in a folder appears in its index.
- No content repeated between `AGENTS.md`, `knowledge/`, `skills/`: summary in `AGENTS.md`, detail in a single place, references elsewhere.
