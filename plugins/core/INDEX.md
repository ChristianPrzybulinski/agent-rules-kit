# core/ — ai-kit core — always-on rules, session discipline and kit-authoring

## `skills/`

| Skill | Description |
|---|---|
| `collab-two-humans` | Condition → action rules for two people plus agents on one backlog. Use when a second human joins. Not for solo work. |
| `find-skills` | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill. |
| `parallelize` | Parallel planning for tool calls, long commands and [P] tasks. Use when work has independent steps. Not for product concurrency (skill testing). |
| `session-handoff` | Session handoff record with evidence and next action. Use when switching agent/session or leaving pending work. Not for session summary (skill session-review). |
| `session-review` | Session closeout with evidence and one kit proposal. Use when work is delivered or a session closes. Not for handoff records (skill session-handoff). |
| `sessions` | Session scope and hygiene. Use when starting, changing topics or detecting a long session. Not for recording completed work (skill session-handoff). |
| `skill-creator` | Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy. |
| `tokens` | Response register for code, e-mail, reports, README and governed docs. Use when writing long answers or text for humans. Not for doc policy (skill update-docs). |
## `agents/`


## `hooks/`

- `hooks.json`

## `templates/`

- `doc-session-handoff.md`
- `kit-index.md`
- `kit-readme.md`
- `kit-reference.md`
- `kit-skill.md`


Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
