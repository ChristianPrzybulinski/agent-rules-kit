# agent-rules-kit — index

Version: [`VERSION`](VERSION) · History: [`CHANGELOG.md`](CHANGELOG.md).

The repository root is the distributable plugin: [`.devin-plugin/plugin.json`](.devin-plugin/plugin.json) defines the Devin plugin, while [`plugin.json`](plugin.json) and [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) define the Codex plugin and marketplace entry.

## Roots

| Root | Purpose | Context rule |
|---|---|---|
| [`AGENTS.md`](AGENTS.md) | always-on global behavior | one file, at most `AGENTS_MAX_LINES` from the validator |
| [`rules/`](rules/INDEX.md) | Devin triggered rules (`glob`, `model_decision`, `manual`) | `always_on` is forbidden; use `AGENTS.md` instead |
| [`skills/`](skills/INDEX.md) | flat invocable procedures and their references | descriptions are 40–160 characters; total ≤7,200 characters |
| [`templates/`](templates/INDEX.md) | artifact skeletons used by skills | shape only, not duplicated guidance |
| [`platforms/`](platforms/INDEX.md) | lifecycle tools, CI validators and ready-to-copy kits | executable or tool configuration |
| [`docs/`](docs/INDEX.md) | architecture and maintenance documentation | explanation for maintainers |

The description budget is a hard gate because Codex limits its initial skills list to roughly 8,000 characters and may shorten or omit skills beyond it.

## What goes where

| Content | Quick test | Location |
|---|---|---|
| rule | guidance triggered by a file glob or explicit rule trigger | `rules/<name>.md` |
| skill | a procedure the model or user invokes | `skills/<name>/SKILL.md` |
| reference | a dated fact or normative detail owned and linked by one skill | `skills/<name>/references/<topic>.md` |
| template | a reusable artifact skeleton with placeholders | `templates/<prefix>-<name>.md` |

## Reading order

1. This index for the layout and invariants.
2. [`AGENTS.md`](AGENTS.md) for always-on behavior.
3. [`rules/INDEX.md`](rules/INDEX.md) or [`skills/INDEX.md`](skills/INDEX.md) for contextual detail.
4. [`docs/maintenance.md`](docs/maintenance.md) before changing the kit.

## Invariants

- `VERSION`, `.devin-plugin/plugin.json`, and `plugin.json` have the same semantic version.
- Every skill folder appears in `skills/INDEX.md`; every rule file appears in `rules/INDEX.md`.
- Skill descriptions and reference sizes stay within their validator budgets.
- Relative links resolve, and each non-skill folder has exactly one `INDEX.md` or `README.md`.
- The repository is the source of truth: plugins, caches and symlinks consume it without managed content copies elsewhere on the machine.
