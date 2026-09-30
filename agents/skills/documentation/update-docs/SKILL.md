---
name: update-docs
version: "1.0"
description: Atualiza README, CHANGELOG, ADRs e versionamento semântico. Usar ao fechar mudança visível ou preparar release.
triggers:
  - user
  - model
allowed-tools:
  - read
  - write
  - edit
---

# Documentation Expert

## Sempre

1. Mantenha `README.md` sincronizado com o estado do projeto.
2. Atualize `CHANGELOG.md` (Keep a Changelog) a cada mudança relevante.
3. Registre decisões arquiteturais em `docs/adr/XXXX-titulo.md`.
4. Use Conventional Commits e SemVer.

## CHANGELOG

- Formato: `## [X.Y.Z] - YYYY-MM-DD`
- Seções: Added, Changed, Deprecated, Removed, Fixed, Security.
- Cada entrada descreve o impacto para o usuário, não o código.

## README

- Propósito, instalação, uso, testes, estrutura, licença/contribuição.

## ADR

1. Contexto
2. Decisão
3. Consequências

## Versionamento

- MAJOR: breaking changes.
- MINOR: funcionalidades compatíveis.
- PATCH: correções.
- Tags Git: `vX.Y.Z`.
