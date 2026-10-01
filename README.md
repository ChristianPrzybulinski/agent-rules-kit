# agent-rules-kit

Skills (normative rules included), knowledge and tools shared by AI agents (Devin, Cursor, Windsurf, Codex, ChatGPT). Layout v5: `agents/` (what enters the context), `platforms/` (what runs on the machine/CI), `docs/` (documentation about the kit).

**Full index: [`INDEX.md`](INDEX.md).** Maintaining the kit: [`docs/maintenance.md`](docs/maintenance.md).

## Bootstrap (private repo — requires `gh auth login`)

```bash
gh repo clone ChristianPrzybulinski/agent-rules-kit ~/.ai-kit && ~/.ai-kit/platforms/tools/bootstrap.sh
```

Private repo: `refresh.sh` pulls with plain `git` — run `gh auth setup-git` once so git reuses the `gh` credentials (otherwise it warns and keeps the local state).

Then, every session: `~/.ai-kit/platforms/tools/refresh.sh --quiet` (the `AGENTS.md` instructs the agent to do this).

## Devin plugin (cloud sessions, no bootstrap)

On every push to `main`, CI publishes the kit as the Devin plugin `ai-kit` to the generated `devin-plugin` branch: `AGENTS.md` as an always-on rule plus every skill (`/ai-kit:<skill>`). Install it once (personal or org scope) from `https://github.com/ChristianPrzybulinski/agent-rules-kit` at ref `devin-plugin`. Unpinned, it follows the branch; `devin plugins update ai-kit` re-fetches. Build locally with `platforms/install/devin-plugin.sh <out-dir>`.
