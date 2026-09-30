# agent-rules-kit

Regras, conhecimento, skills, processos e kits de configuração para agentes de IA (Devin, Windsurf, Cursor, Codex, ChatGPT) trabalhando em Java/Spring, Godot 2D, PostgreSQL, Redis, Docker e GitHub.

## Princípios de design

- **Um always-on curto** (`AGENTS.md`, ≤150 linhas). Evidência (GitHub 2.500 repos, ETH AGENTbench, Augment): qualidade cai acima de ~300 linhas; ganha com condição→ação, exemplos curtos e limites explícitos.
- **Regra ≠ conhecimento ≠ skill ≠ kit**: regra é normativa e curta; conhecimento é factual com fonte e data; skill é procedimento executável; kit é arquivo de configuração pronto.
- **Carregar sob demanda**: tudo fora do `AGENTS.md` entra no contexto só quando o domínio pede (`trigger: model_decision` / `description`).
- **Referenciar, não duplicar**: estilo vive em `pom.xml`/`.editorconfig`/`project.godot`; specs vivem no repo do projeto, não aqui.
- **Toda afirmação classificada**: `[FATO]` `[DECISÃO]` `[PROPOSTA]` `[HIPÓTESE]` `[BLOQUEIO]`.

## Estrutura

```text
├── AGENTS.md                 # always-on global
├── README.md · CHANGELOG.md
├── rules/                    # normativo, por domínio, sob demanda
│   ├── core/          evidence · tokens
│   ├── development/   clean-code · testing (100% domain + PITest ≥80, feliz+triste) · twelve-factor
│   ├── architecture/  clean-architecture · ddd-and-patterns (quando sim / quando não)
│   ├── java/          java · build-and-dependencies (Maven obrigatório, LTS fixo, gates)
│   ├── godot/         godot-2d
│   ├── git/           branching-and-versioning (trunk-based, flags, SemVer, protocol_version) · git-lfs-and-binaries · github-cli
│   ├── security/      secure-development (0 CVE crítica/alta, segredos, authz, LGPD)
│   └── documentation/ documentation · living-docs (DoD documental)
├── knowledge/                # factual, com fonte e data de verificação
│   └── java/ godot/ postgresql/ redis/ docker/ git/
├── skills/                   # executáveis (/nome), agrupadas por domínio
│   ├── core/          skeptic · validate-implementation · vuln-scan
│   ├── java/ godot/   java-standards · godot-standards
│   ├── git/           github-cli · git-lfs
│   ├── docs/          update-docs
│   └── postgresql/ redis/ docker/ dbeaver/ krita/
├── processes/sdd/            # Spec-Driven Development (9 skills sdd-* + README) — adaptado do github/spec-kit
├── kits/                     # configuração pronta para copiar no projeto
│   ├── github/        workflows (ci-java, ci-godot, spec-lint, gitleaks) · PR template · CODEOWNERS · labels
│   ├── java-maven/    pom-parent.xml (Spotless, JaCoCo 100% domain, PITest 80, Dependency-Check CVSS≥7, Enforcer) · toolchains
│   ├── docker/        compose.yml (Postgres 17 + Redis 7, healthchecks) · Dockerfile.java · .env.example
│   ├── git-lfs/       .gitattributes
│   ├── godot/         .gitignore · make_spritesheet.py · dicas de editor
│   └── sdd/           init-spec.sh (cria docs/spec/ no projeto)
├── templates/
│   ├── projects/      java-spring/AGENTS.md · godot-2d/AGENTS.md
│   └── docs/spec/     spec · feature · requirement-functional · requirement-non-functional · decision · debt
├── schemas/                  # JSON Schema dos frontmatters de spec (validados em CI)
├── prompts/                  # chatgpt-compact (≤1.500 chars) · chatgpt-full
└── scripts/
    ├── install/       devin.sh · cursor.sh · windsurf.sh · codex.sh · all.sh
    ├── check.sh       valida o kit; `--spec <dir>` valida um docs/spec
    └── check_spec.py
```

## Instalação

```bash
gh repo clone ChristianPrzybulinski/agent-rules-kit ~/.ai-kit
~/.ai-kit/scripts/install/all.sh      # Devin + Cursor + Windsurf + Codex, depois check.sh
```

| Destino | Conteúdo |
|---|---|
| `~/.config/devin/AGENTS.md` | always-on |
| `~/.devin/rules/<domínio>/*.md` | regras sob demanda |
| `~/.config/devin/skills/<nome>/` | skills + processos (achatados; nomes únicos) |
| `~/.cursor/rules/<domínio>-<nome>.mdc` | regras convertidas |
| `~/.codeium/windsurf/memories/global_rules.md` | always-on |
| `~/.codex/AGENTS.md` | always-on (Codex CLI) |

Não instala em `~/.devin/global_rules.md` nem `~/.claude/CLAUDE.md`: Devin lê ambos como regra global e duplicaria o texto no contexto.

**ChatGPT**: Custom Instructions ← `prompts/chatgpt-compact.md`; GPT/Project ← `prompts/chatgpt-full.md`.

## Uso num projeto

```bash
cp ~/.ai-kit/templates/projects/java-spring/AGENTS.md ./AGENTS.md   # ou godot-2d; preencher [colchetes]
~/.ai-kit/kits/sdd/init-spec.sh .                                    # cria docs/spec/
cp ~/.ai-kit/kits/git-lfs/.gitattributes .                           # ANTES do primeiro binário
mkdir -p .github/workflows && cp ~/.ai-kit/kits/github/workflows/*.yml .github/workflows/
```

Depois, no agente: `/sdd-constitution` → `/sdd-specify <funcionalidade>` → `/sdd-clarify FEAT-001` → `/sdd-audit` → `/sdd-plan` → `/sdd-tasks` → `/sdd-implement` → `/validate-implementation FEAT-001` → `/sdd-to-card`. Detalhes em `processes/sdd/README.md`.

Outras skills: `/skeptic <afirmação>` · `/vuln-scan` · `/git-lfs audit` · `/postgresql migration ...` · `/redis justify ...` · `/docker up`.

## Pré-requisitos verificados nesta máquina (2026-09-29)

Godot 4.7.2 · JDK 25 (`/opt/homebrew/opt/openjdk@25`, keg-only — usar via `toolchains.xml`) e JDK 27 no PATH · Maven 3.9.16 · Docker 29 + Compose v5 · gh 2.101 · git-lfs 3.8 · DBeaver · Krita. Python do sistema 3.9 sem `pyyaml`/`jsonschema` (check de spec roda em modo estrutural; `pip3 install --user pyyaml jsonschema` para validação completa).

## Manutenção

- Linha nova no `AGENTS.md` só se "removê-la mudaria um resultado amanhã".
- Mudança → `CHANGELOG.md` → `scripts/check.sh` → commit Conventional → `scripts/install/all.sh`.
- Versões em `kits/` e `knowledge/` têm data de verificação; revisar a cada release.

## Referências

agents.md · github/spec-kit · Taiizor/agents-md-cookbook · NasserAlbusaidi/claude.md · GoranErhartic/cursor-development-rules · voxmedia/open-agent-toolkit (skeptic) · AKDworks/Godot-Clarity · Common-ka/godot-cursor-rules
