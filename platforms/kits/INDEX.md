# kits/ — arquivos prontos para copiar em projetos

Escopo: configuração e templates de infra que um projeto copia (não são lidos pelo agente como instrução — instrução é `agents/`).

| Kit | Conteúdo | Quando usar |
|---|---|---|
| `docker/` | compose PostgreSQL+Redis, Dockerfile.java multi-stage, init SQL, .env.example | infra local do projeto |
| `git-lfs/` | `.gitattributes` pronto | antes do primeiro binário no repo |
| `github/` | workflows (spec-lint, gitleaks, ci-java/godot reutilizáveis), PR template, CODEOWNERS, labels + sync | todo repo novo |
| `godot/` | `.gitignore` Godot, hints de editor, `make_spritesheet.py` | projeto Godot |
| `java-maven/` | pom parent com gates, toolchains, suppressions, `.java-version` | projeto Java/Maven |
| `sdd/` | `init-spec.sh` — cria `docs/spec/` a partir de `agents/templates/spec-*` | bootstrap de spec no projeto |
| `third-party/` | `skills.lock` — skills externas pinadas por commit | regenerar `agents/skills/vendor/` |
