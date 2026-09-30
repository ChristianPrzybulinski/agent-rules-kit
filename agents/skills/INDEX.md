# skills/ — procedimentos invocáveis, por tipo

Escopo: como executar uma tarefa passo a passo (`/nome`), com entradas, saídas e "pronto quando". Regra genérica → `../rules/`; fato → `../knowledge/`. Devin instala achatado por basename — nomes de skill são únicos no kit inteiro.

| Tipo | Pasta | Contém |
|---|---|---|
| qualidade | [`quality/`](quality/INDEX.md) | verificação, investigação, testes de caracterização, vulnerabilidades |
| desenvolvimento | [`development/`](development/INDEX.md) | stacks, import de assets, contrato de protocolo |
| documentação | [`documentation/`](documentation/INDEX.md) | docs do projeto, passagem de sessão |
| processo | [`process/`](process/README.md) | SDD — 9 etapas `sdd-*` |
| ferramentas | [`tooling/`](tooling/INDEX.md) | CLIs e serviços (gh, lfs, postgres, redis, docker, dbeaver, krita) |
| vendor | [`vendor/`](vendor/INDEX.md) | skills de terceiros pinadas por commit (ver `../../platforms/kits/third-party/`) |

## Todas as skills

| Skill | Tipo | Quando usar |
|---|---|---|
| `skeptic` | quality | afirmação duvidosa → veredito com confiança |
| `validate-implementation` | quality | "está pronto?" antes de PR/fechar tarefa |
| `vuln-scan` | quality | CVEs, segredos, OWASP antes de PR/release |
| `characterization-tests` | quality | fixar comportamento atual de legado antes de refatorar |
| `investigate` | development | bug/lentidão/incidente até causa raiz |
| `java-standards` | development | código Java, pom.xml |
| `godot-standards` | development | GDScript, nodes, cenas |
| `asset-import` | development | sprites/tilesets/mapas externos → Godot, com manifesto |
| `protocol-contract` | development | criar/evoluir mensagem cliente↔servidor |
| `update-docs` | documentation | README, CHANGELOG, ADR, semver |
| `session-handoff` | documentation | fim de sessão, troca de agente |
| `sdd-constitution` → `sdd-to-card` | process | funcionalidade nova ponta a ponta (ver `process/README.md`) |
| `github-cli` | tooling | branches, PRs, releases via `gh` |
| `git-lfs` | tooling | binários, .gitattributes, quota |
| `postgresql` | tooling | schema, migrações, diagnóstico |
| `redis` | tooling | cache, sessão, fila leve |
| `docker` | tooling | compose local, Dockerfile, diagnóstico |
| `dbeaver` | tooling | inspecionar Postgres local |
| `krita` | tooling | pixel art e retoque de sprites |
| `grill-me` / `grilling` | vendor | entrevista implacável para afiar plano (só por comando) |
| `skill-creator` | vendor | criar/avaliar skill |
| `find-skills` | vendor | descobrir skill existente para uma tarefa |
| `frontend-design` | vendor | direção visual de UI |
