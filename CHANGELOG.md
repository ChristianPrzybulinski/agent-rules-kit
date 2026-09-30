# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Versionamento: [SemVer](https://semver.org/lang/pt-BR/).

## [4.0.0] - 2026-09-30

### Changed
- **Layout v4**: `rules/`, `knowledge/`, `prompts/` → `agents/`; skills por tipo em `agents/skills/<tipo>/`; `processes/sdd/` → `agents/skills/process/`; templates flat em `agents/templates/` (`spec-*`, `doc-*`, `project-*`, `kit-*`); `schemas/`, `scripts/` → `platforms/ci/` e `platforms/tools/`/`platforms/install/`; `kits/` → `platforms/kits/`. Índice mestre: `INDEX.md`.
- **BREAKING**: caminhos públicos mudaram — `scripts/check.sh` → `platforms/tools/check.sh`, `scripts/install/all.sh` → `platforms/install/all.sh`, `templates/docs/spec/*` → `agents/templates/spec-*`. Projetos devem atualizar referências (ex.: `spec-lint.yml`).
- `check.sh` agora delega a `platforms/ci/validations/check_kit.py` (layout, frontmatters, índices, links, lock, duplicação); `--spec` continua em `check_spec.py`.
- `devin.sh`/`codex.sh` instalam skills a partir de `agents/skills/`; `cursor.sh` ignora `INDEX.md`; `all.sh` grava `~/.config/agent-rules-kit/{VERSION,LAYOUT_VERSION}` e ganha `--clean`.
- Releases passam a ser automáticas: tag `v*` → workflow valida `VERSION` e publica release com a seção do changelog.

### Added
- `VERSION`, `LAYOUT_VERSION`; `INDEX.md` raiz + INDEX/README em toda pasta.
- `platforms/tools/`: `bootstrap.sh` (1 comando) e `refresh.sh [--quiet]` (pull + reinstall por versão/layout).
- `.github/`: workflows `ci`, `gitleaks`, `release`; `dependabot.yml`; PR template; CODEOWNERS.
- `platforms/ci/schemas/`: `rule`, `knowledge`, `skill`, `skills-lock` (além dos 5 de spec).
- `agents/rules/core/sessions.md` (higiene de sessão) e `agents/templates/kit-*.md` (templates do próprio kit).
- `docs/`: `design.md` (princípios), `projects.md` (o que vive no projeto), `maintenance.md` (versionar, vendor, CI).
- Frontmatter `knowledge.schema.json` nas 9 notas de `agents/knowledge/`.

## [3.2.0] - 2026-09-30

### Added
- Regra `rules/development/simplicity.md` (escada YAGNI → já existe → stdlib → plataforma → mínimo que funciona; simplificação deliberada com comentário de teto).
- Vendor de 5 skills de terceiros pinadas por commit em `kits/third-party/skills.lock` + `scripts/install/third-party.sh` (clone sparse `--filter=blob:none`, copia diretório inteiro, `VENDOR.md`, `--check`): `grill-me`, `grilling` (mattpocock/skills, MIT); `skill-creator`, `frontend-design` (anthropics/skills, Apache-2.0); `find-skills` (vercel-labs/skills, MIT).
- `codex.sh` instala skills em `~/.codex/skills/<nome>/` com marcador `.agent-rules-kit` (conteúdo do usuário e `.system` preservados).
- Knowledge: `git/worktrees.md` (`git worktree`, quando usar, armadilhas).

### Changed
- `AGENTS.md`: Clean Architecture pragmática (port só em fronteira real), escada da simplicidade no Craft, seção Tokens dividida em duas lentes (técnico vs. texto para pessoas), linhas novas nas Especialidades (`/grill-me`, `skill-creator`, `find-skills`).
- `rules/development/testing.md`: YAGNI fora do domínio — um check executável para lógica não trivial em vez de suíte por função.
- `rules/architecture/clean-architecture.md`: pragmatismo — serviço interno com uma implementação é classe concreta.
- `rules/core/tokens.md`: reescrito para as duas lentes de comunicação.
- `processes/sdd/sdd-implement`: revisão em dois estágios.
- `processes/sdd/sdd-tasks`: tarefas menores.
- `templates/docs/review-checklist.md`: seção "ao receber revisão".
- `devin.sh` copia o diretório inteiro de cada skill (era só `SKILL.md`); inclui `skills/vendor/` no achatamento.
- `all.sh` roda `third-party.sh --check` antes dos demais instaladores.

### Credits
- Ideias absorvidas de JuliusBrussee/caveman, blader/humanizer, DietrichGebert/ponytail, obra/superpowers (todas MIT) — não instaladas; política do kit é absorver, não empilhar personas.

## [3.1.1] - 2026-09-30

### Fixed
- `scripts/check_spec.py`: arquivos `REQ-NF-nnn.md` não eram reconhecidos pelo prefixo de ID (regex `REQ-[FN]`); agora `REQ-NF|REQ-F`.

## [3.1.0] - 2026-09-30

### Added
- Skills: `session-handoff`, `protocol-contract`, `investigate` (core), `characterization-tests` (java), `asset-import` (godot).
- Templates de docs: `session-handoff`, `contract-message`, `recovery-report`, `bug-report`, `review-checklist`, `load-test` em `templates/docs/`.
- Knowledge: `godot/networking-transports.md` (transportes cliente↔servidor em Godot 4 com servidor não-Godot), `legacy/director-lingo-glossary.md` (glossário Director/Lingo para leitura do acervo legado).
- Schema FEAT: campos opcionais `milestone` e `evidence`.

### Changed
- `AGENTS.md`: novas linhas na tabela de Especialidades para as 5 skills novas.
- `templates/docs/spec/feature.md` atualizado junto ao schema.

## [3.0.0] - 2026-09-29

### Changed
- Estrutura reorganizada por domínio: `rules/<domínio>/`, `skills/<domínio>/<nome>/`, `templates/{projects,docs}`, `prompts/`, `scripts/install/`. Skills renomeadas para nomes únicos (`java-standards`, `godot-standards`, `update-docs`) porque o Devin instala skills em pasta plana.
- `AGENTS.md`: seções Testes e Git/docs/versão; roteamento para regras/skills/processo por contexto; gates de segurança (0 CVE crítica/alta, Argon2id, twelve-factor).
- Installers reescritos (`devin.sh`, `cursor.sh`, `windsurf.sh`, `codex.sh`, `all.sh`); `check.sh` valida regras/skills/processos, tamanhos, schemas e, com `--spec`, um `docs/spec` de projeto.

### Added
- Regras: `testing` (100% linha/branch + PITest ≥80% no domínio; integração feliz+triste), `twelve-factor`, `secure-development`, `ddd-and-patterns` (catálogo quando sim/quando não), `branching-and-versioning` (trunk-based, feature flags com expiração, SemVer, `protocol_version`), `git-lfs-and-binaries`, `java/build-and-dependencies` (Maven obrigatório, LTS fixo), `living-docs`.
- Skills: `validate-implementation`, `vuln-scan`, `git-lfs`, `postgresql`, `redis`, `docker`, `dbeaver`, `krita`.
- Processo `sdd` (Spec-Driven Development) adaptado do github/spec-kit: `sdd-constitution`, `sdd-specify`, `sdd-clarify`, `sdd-analyze`, `sdd-audit`, `sdd-plan`, `sdd-tasks`, `sdd-implement`, `sdd-to-card` (GitHub Issues + Projects). Siglas `FEAT/REQ-F/REQ-NF/DEC/DEBT`, status por feature, classificação `[FATO]/[DECISÃO]/[PROPOSTA]/[HIPÓTESE]/[BLOQUEIO]`.
- Templates de spec (`spec`, `feature`, `requirement-functional`, `requirement-non-functional`, `decision`, `debt`) e JSON Schemas correspondentes.
- Kits: `github` (workflows ci-java, ci-godot, spec-lint, gitleaks; PR template; labels), `java-maven` (pom-parent com gates), `docker` (Postgres 17.11 + Redis 7.4), `git-lfs`, `godot`, `sdd/init-spec.sh`.
- `knowledge/` com notas factuais datadas (Java 25 LTS, Godot 4.7, Postgres 17, Redis 7 e licença, Compose v5, quotas LFS).
- Instalação para Codex CLI (`~/.codex/AGENTS.md`).

### Fixed
- Quota do GitHub LFS corrigida para 10 GiB (Free/Pro), conforme docs atuais.

### Removed
- `scripts/install.sh` e `scripts/to-mdc.sh` (substituídos por `scripts/install/*`); instalação em `~/.claude/CLAUDE.md`.

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
