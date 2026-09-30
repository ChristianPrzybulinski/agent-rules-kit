# agent-rules-kit

Skills (normative rules included), knowledge and tools shared by AI agents (Devin, Cursor, Windsurf, Codex, ChatGPT). Layout v5: `agents/` (what enters the context), `platforms/` (what runs on the machine/CI), `docs/` (documentation about the kit).

**Full index: [`INDEX.md`](INDEX.md).** Maintaining the kit: [`docs/maintenance.md`](docs/maintenance.md).

## Bootstrap (private repo — requires `gh auth login`)

```bash
gh repo clone ChristianPrzybulinski/agent-rules-kit ~/.ai-kit && ~/.ai-kit/platforms/tools/bootstrap.sh
```

Then, every session: `~/.ai-kit/platforms/tools/refresh.sh --quiet` (the `AGENTS.md` instructs the agent to do this).
