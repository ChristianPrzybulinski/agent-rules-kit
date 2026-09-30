# agent-rules-kit

Regras, conhecimento, skills e ferramentas compartilhadas por agentes de IA (Devin, Cursor, Windsurf, Codex, ChatGPT). Layout v4: `agents/` (o que entra no contexto), `platforms/` (o que roda na máquina/CI), `docs/` (documentação sobre o kit).

**Índice completo: [`INDEX.md`](INDEX.md).** Manter o kit: [`docs/maintenance.md`](docs/maintenance.md).

## Bootstrap (repo privado — precisa de `gh auth login`)

```bash
gh repo clone ChristianPrzybulinski/agent-rules-kit ~/.ai-kit && ~/.ai-kit/platforms/tools/bootstrap.sh
```

Depois, toda sessão: `~/.ai-kit/platforms/tools/refresh.sh --quiet` (o `AGENTS.md` instrui o agente a fazer isso).
