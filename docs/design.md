# Design — why the kit is like this

The validated layout and routing test live in [`../INDEX.md`](../INDEX.md). These principles explain the choices behind them.

## Principles

- **Single source: `plugins/` is the plugin family root.** The repository root follows Cognition's team-marketplace pattern: a content-free meta-plugin requires `core` through `git-subdir` and offers the satellites and the `all` bundle as optional. Each plugin directory is consumed directly by Devin, Codex and Claude Code; there is no generated distribution tree.
- **One content tree, three agent families.** Skills, rules, agents and templates are shared across Devin, Codex and Claude Code; per-platform manifests (`plugins/<name>/.devin-plugin`, `.claude-plugin`, `plugin.json`) adapt discovery and dependencies without copying content.
- **Dependency graph, not duplication.** Satellites declare their parent through `requiredPlugins` (Devin) / `dependencies` (Claude): `dev-java`→`dev-core`→`core`. The `all` bundle is manifest-only and resolves to every plugin. Plugin names double as the taxonomy: `family-name`.
- **Shared-key frontmatter.** A file carries each platform's routing keys together: `triggers`/Codex policy/`disable-model-invocation`, `globs`/`paths`, and lowercase/Claude tool names are validated for parity.
- **One hook file.** `hooks/hooks.json` uses Claude's wrapper because both local Devin and Claude Code load it; one command and one case table prevent security drift.
- **Plugin-first on every surface.** Devin Cloud and local Devin consume the repository plugin; Codex and Claude Code consume their marketplace plugins. Machine setup adds only zero-copy instruction/rule symlinks and the temporary Codex compatibility fallback.
- **Minimal always-on context.** `AGENTS.md` keeps only durable routing and boundaries. Procedures and detail load through skills or triggered rules instead of consuming every message.
- **Always-on test.** A line stays in `AGENTS.md` only if the behavior must hold before any skill could trigger—session start, response shape, safety stops or boundaries. Everything else is a skill or a glob rule.
- **Glob over `model_decision`.** A glob rule costs nothing until a matching file is touched; a `model_decision` rule contributes its description on every message. Use it only when no reliable glob exists.
- **Content/tooling separation.** `plugins/*/` contains only plugin manifests and model-facing content; `platforms/`, `docs/` and repository automation stay outside the plugin root.
- **Zero content copies on the machine.** Agent-facing content is reached through plugin caches or symlinks. This prevents duplicate skill names and drift between installed copies.
- **Description budget is a hard gate.** Codex budgets about 8,000 characters for the initial skill list, so the kit reserves at most 7,200 for all skill descriptions.
- **One owner per detail.** A rule routes, a skill executes, a reference holds facts or normative depth, and a template supplies shape. Cross-links replace copied paragraphs.
- **Everything validatable.** Layout, manifests, frontmatter, budgets, indexes, links and vendor locks are mechanical CI gates.

## Codex compatibility fallback

Plugin skills remain installed but may be absent from the model input while [openai/codex#22078](https://github.com/openai/codex/issues/22078) is open. `doctor.sh` probes for `<plugin>:*`; while absent, it maintains skill symlinks from `~/.codex/skills/` to `~/.ai-kit/plugins/*/skills/`, and removes them once the plugins expose the skills. If that directory proves unreadable, the documented one-time administrative fallback is `/etc/codex/skills` pointing to the repository skills. This is a measured compatibility exception, not a second source.

## What was left out, and why

- **Windsurf, Cursor and ChatGPT destinations were left out:** they are outside the initial v6 surface. Windsurf directories were also imported by Devin and helped triple the observed startup context.
- **`~/.agents/skills` for Codex was left out:** Devin reads that location too, producing duplicates beside plugin skills. The fallback uses the Codex-only directory instead.
- **Knowledge notes as `model_decision` rules were left out:** each rule description would tax every message. Notes now live as references owned by the skill that needs them.
- **A built `devin-plugin` branch was left out:** `main` itself is the release and the plugin source.
- **Playbooks were left out:** user-invoked plugin skills cover the same procedures while staying version-controlled and portable across surfaces.
- **Knowledge was left out:** Cognition deprecated it; references now live under the skill that owns and loads them.
- **MCP servers were left out:** tool schemas cost context on every turn, while `gh` covers the GitHub operations this kit needs.
- **Stop and UserPromptSubmit hooks were left out:** Stop can loop, and UserPromptSubmit spends tokens on every turn. The narrow PreToolUse guard is local and best effort.
- **Additional skill frameworks were left out:** markdown procedures avoid another runtime and remain portable across supported agents.
