# Design — por que o kit é assim

Os invariantes e a divisão `agents/` · `platforms/` · `docs/` estão em [`../INDEX.md`](../INDEX.md). Aqui ficam os princípios por trás deles — o que motivou cada regra, não a regra em si.

## Princípios

- **Always-on mínimo**: cada linha de `agents/AGENTS.md` só existe se removê-la mudaria um resultado amanhã. Detalhe vive sob demanda (regra/knowledge/skill), carregado pela `description`/`trigger`. Contexto custa tokens e atenção — os dois são finitos.
- **Um lugar para cada coisa**: regra normativa, fato datado, procedimento e forma de artefato são coisas diferentes; misturá-las produz duplicação e drift. O teste rápido do `INDEX.md` decide onde um conteúdo novo mora.
- **Evidência e ceticismo**: o kit inteiro assume que afirmação sem fonte é hipótese. Knowledge notes têm `verified` + `sources`; specs classificam `[FATO]`/`[PROPOSTA]`/`[HIPÓTESE]`. Isso vale para o próprio kit: versões citadas são as que foram conferidas na data marcada.
- **Absorver, não empilhar**: ideias boas de outros repositórios (credits no `CHANGELOG.md`) entram como texto do kit, adaptadas — não como mais uma camada/persona a carregar. Skills de terceiros que não dá para absorver são vendorizadas com lock de commit.
- **Tudo validável**: o que o kit promete é checado por `platforms/tools/check.sh` e pelo CI. Uma regra que não cabe no validador tende a apodrecer; por isso índice, frontmatter, links e limites de linhas são mecânicos.

## O que ficou de fora, e por quê

- `~/.claude/CLAUDE.md` e `~/.devin/global_rules.md` como destinos: duplicariam o AGENTS.md no contexto.
- `npx skills add` nos agentes: instalação não pinada e fora do controle do lock — o kit vendoriza.
- Frameworks de skills (spec-kit CLI, etc.): exigem runtime extra; o kit usa arquivos markdown que qualquer agente lê.
