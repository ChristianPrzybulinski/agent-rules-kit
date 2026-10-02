# Design — why the kit is like this

The validated layout and routing test live in [`../INDEX.md`](../INDEX.md). These principles explain the choices behind them.

## Principles

- **Single source: the repository is the plugin.** `main` contains the manifests, always-on instructions, rules, skills, references and templates consumed by each supported agent. There is no generated distribution tree.
- **Plugin-first on every surface.** Devin Cloud and local Devin consume the repository plugin; Codex consumes its marketplace plugin. Machine setup adds only the always-on symlink and the temporary Codex compatibility fallback.
- **Minimal always-on context.** `AGENTS.md` keeps only durable routing and boundaries. Procedures and detail load through skills or triggered rules instead of consuming every message.
- **Always-on test.** A line stays in `AGENTS.md` only if the behavior must hold before any skill could trigger—session start, response shape, safety stops or boundaries. Everything else is a skill or a glob rule.
- **Glob over `model_decision`.** A glob rule costs nothing until a matching file is touched; a `model_decision` rule contributes its description on every message. Use it only when no reliable glob exists.
- **Zero content copies on the machine.** Agent-facing content is reached through plugin caches or symlinks. This prevents duplicate skill names and drift between installed copies.
- **Description budget is a hard gate.** Codex budgets about 8,000 characters for the initial skill list, so the kit reserves at most 7,200 for all skill descriptions.
- **One owner per detail.** A rule routes, a skill executes, a reference holds facts or normative depth, and a template supplies shape. Cross-links replace copied paragraphs.
- **Everything validatable.** Layout, manifests, frontmatter, budgets, indexes, links and vendor locks are mechanical CI gates.

## Codex compatibility fallback

Plugin skills remain installed but may be absent from the model input while [openai/codex#22078](https://github.com/openai/codex/issues/22078) is open. `doctor.sh` probes for `ai-kit:*`; while absent, it maintains skill symlinks under `~/.codex/skills/`, and removes them once the plugin exposes the skills. If that directory proves unreadable, the documented one-time administrative fallback is `/etc/codex/skills` pointing to the repository skills. This is a measured compatibility exception, not a second source.

## What was left out, and why

- **Windsurf, Cursor and ChatGPT destinations were left out:** they are outside the initial v6 surface. Windsurf directories were also imported by Devin and helped triple the observed startup context.
- **`~/.agents/skills` for Codex was left out:** Devin reads that location too, producing duplicates beside plugin skills. The fallback uses the Codex-only directory instead.
- **Knowledge notes as `model_decision` rules were left out:** each rule description would tax every message. Notes now live as references owned by the skill that needs them.
- **A built `devin-plugin` branch was left out:** `main` itself is the release and the plugin source.
- **Additional skill frameworks were left out:** markdown procedures avoid another runtime and remain portable across supported agents.
