---
description: Regras para documentação, changelog, versionamento e ADRs.
trigger: model_decision
---

# Documentação

## README.md

- Propósito do projeto.
- Como rodar (pré-requisitos, instalação, comandos).
- Como testar.
- Estrutura de diretórios resumida.
- Licença e contribuição (se aberto).

## CHANGELOG.md

- Siga [Keep a Changelog](https://keepachangelog.com/).
- Seções: Added, Changed, Deprecated, Removed, Fixed, Security.
- Versões em ordem decrescente. A versão mais recente no topo.
- Cada entrada deve ser compreensível sem acessar o código.

```markdown
## [1.2.3] - 2026-09-29
### Added
- Suporte a autenticação OAuth2.

### Fixed
- Corrige vazamento de conexão no pool Hikari.
```

## Versionamento

- Use SemVer: MAJOR.MINOR.PATCH.
- MAJOR: mudanças incompatíveis.
- MINOR: funcionalidades compatíveis.
- PATCH: correções.
- Tags Git: `v1.2.3`.

## ADRs

- Decisões arquiteturais importantes vão em `docs/adr/0001-titulo-da-decisao.md`.
- Estrutura: contexto, decisão, consequências.

## Commits

- Conventional Commits: `type(scope): descrição`.
- Tipos: feat, fix, docs, style, refactor, test, chore.
- Corpo opcional para detalhes; footer para breaking changes e issue references.

## Comentários no código

- Evite comentários explicativos desnecessários.
- Documente APIs públicas (JavaDoc, docstrings GDScript).
- Explique o "porquê", não o "o quê".
