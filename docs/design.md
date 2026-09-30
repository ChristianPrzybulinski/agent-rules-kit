# Design — why the kit is like this

The invariants and the `agents/` · `platforms/` · `docs/` split are in [`../INDEX.md`](../INDEX.md). Here are the principles behind them — what motivated each rule, not the rule itself.

## Principles

- **Minimal always-on**: each line of `agents/AGENTS.md` exists only if removing it would change an outcome tomorrow. Detail lives on demand (skill/knowledge), loaded by `description`/`trigger`. Context costs tokens and attention — both are finite.
- **One place for each thing**: a normative rule, a dated fact, a procedure and an artifact's shape are different things; mixing them produces duplication and drift. The `INDEX.md` quick test decides where new content lives.
- **Evidence and skepticism**: the whole kit assumes a claim without a source is a hypothesis. Knowledge notes have `verified` + `sources`; specs classify `[FACT]`/`[PROPOSAL]`/`[HYPOTHESIS]`. This applies to the kit itself: cited versions are the ones verified on the marked date.
- **Absorb, don't stack**: good ideas from other repositories (credits in `CHANGELOG.md`) enter as kit text, adapted — not as one more layer/persona to carry. Third-party skills that cannot be absorbed are vendored with a commit lock.
- **Everything validatable**: what the kit promises is checked by `platforms/tools/check.sh` and CI. A rule that does not fit the validator tends to rot; hence index, frontmatter, links and line limits are mechanical.

## What was left out, and why

- `~/.claude/CLAUDE.md` and `~/.devin/global_rules.md` as destinations: they would duplicate AGENTS.md in the context.
- `npx skills add` on the agents: unpinned installation outside the lock's control — the kit vendors.
- Skill frameworks (spec-kit CLI, etc.): require extra runtime; the kit uses markdown files any agent can read.
