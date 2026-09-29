# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento: [SemVer](https://semver.org/lang/pt-BR/).

## [2.0.0] - 2026-09-29

### Changed
- `AGENTS.md` reescrito no modelo condição→ação, ordenado por meia-vida, com seções Verdade, Ceticismo (>98%), Loop, Craft, Limites (Sempre/Perguntar/Nunca) e tabela de roteamento para skills.
- Regras `00-core`, `10-clean-code`, `20-clean-architecture`, `70-token-efficiency` passam de `always_on` para `model_decision` — o resumo vive no `AGENTS.md`; o detalhe carrega sob demanda (menos tokens por sessão).
- `PROMPT.md` reestruturado como system prompt completo.
- README reescrito com princípios de design baseados em evidência e instalação via script.

### Added
- Skill `skeptic`: verificação adversarial (contra → a favor → veredicto com confiança).
- `templates/java-spring/AGENTS.md` e `templates/godot-2d/AGENTS.md` com stack, comandos, padrões condição→ação e limites.
- `PROMPT-compact.md` (≤1.500 chars) para Custom Instructions do ChatGPT.
- `scripts/install.sh` (instala e valida) e `scripts/to-mdc.sh` (gera `.cursor/rules/*.mdc`).
- Instalação para Cursor (`~/.cursor/rules`) e, opcionalmente (`--claude`), Claude Code (`~/.claude/CLAUDE.md`).

### Removed
- Instalação em `~/.devin/global_rules.md` (duplicava o `~/.config/devin/AGENTS.md` no contexto).

## [1.0.0] - 2026-09-29

### Added
- Estrutura inicial: `AGENTS.md`, regras por domínio, skills `java`, `godot-2d`, `github-cli`, `docs`, `PROMPT.md`.
