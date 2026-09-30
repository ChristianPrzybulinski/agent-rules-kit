# rules/ — normativo por domínio

Escopo: o que o agente DEVE/NÃO DEVE fazer, sob demanda (≤60 linhas cada). Resumo always-on: `../AGENTS.md`. Fatos datados não vão aqui — vão em `../knowledge/`.

| Domínio | Regra | Quando carregar |
|---|---|---|
| `architecture/` | `clean-architecture.md` | criar módulo/camada, decidir onde uma classe vive |
| `architecture/` | `ddd-and-patterns.md` | modelar domínio, escolher padrão (quando usar / quando não) |
| `core/` | `evidence.md` | avaliar proposta, confiança <98%, ceticismo |
| `core/` | `sessions.md` | início de sessão, sessão longa, pedido fora de contexto |
| `core/` | `tokens.md` | escolher registro de resposta (técnico vs. texto para pessoas) |
| `development/` | `clean-code.md` | escrever/revisar código de produção |
| `development/` | `simplicity.md` | desenhar solução, PR grande demais, decidir se teste é necessário |
| `development/` | `testing.md` | criar testes, configurar gates de cobertura/mutation |
| `development/` | `twelve-factor.md` | configurar app, Docker, env vars, deploy |
| `documentation/` | `documentation.md` | README, changelog, ADR, versionamento |
| `documentation/` | `living-docs.md` | fechar tarefa/PR — docs atualizados no mesmo commit |
| `git/` | `branching-and-versioning.md` | branch, commit, PR, release, versão de protocolo |
| `git/` | `git-lfs-and-binaries.md` | adicionar assets/binários/exports ao repo |
| `git/` | `github-cli.md` | fluxos com `gh` e git |
| `godot/` | `godot-2d.md` | `*.gd`, `*.tscn`, `project.godot` |
| `java/` | `build-and-dependencies.md` | `pom.xml`, projeto Maven, plugins de qualidade |
| `java/` | `java.md` | código Java moderno, Clean Code |
| `security/` | `secure-development.md` | dependências, auth, endpoints, dados sensíveis |
