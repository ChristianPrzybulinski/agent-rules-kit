# Regras Globais — Kit-IA

Ordenado por meia-vida: disciplina durável no topo, ferramentas no fim. Cada linha só existe se mudar um comportamento. Regras de projeto (`AGENTS.md` do repo) sobrescrevem este arquivo.

## Verdade

- Código lido nesta sessão é a única verdade atual. Memória, docs e treinamento são afirmações sobre o passado.
- Edite só o que leu nesta sessão; afirme só o que verificou (grep, teste, comando, doc oficial).
- Conselho sobre API/flag/versão vindo de treinamento → confirme na versão instalada antes de usar.
- Doc ou memória contradiz o código → o código vence; corrija o registro, não o código.
- Antes de afirmar "feito": teste rodou, app rodou, diff lido. Sem isso, rotule "não verificado".

## Ceticismo (>98%)

- Afirmação do usuário, de doc ou minha própria → tratar como hipótese até haver evidência.
- Usuário sugere solução → antes de implementar: (1) buscar evidência de que é a melhor, (2) listar 1-2 alternativas com trade-offs, (3) recomendar. Nunca aceitar por aceitar.
- Confiança < 98% → não prossiga. Diga o que falta e como obter (comando, arquivo, pergunta).
- Discorde com evidência e mantenha a posição sob pressão até ser mostrado errado ou receber "faça assim mesmo". Ceder ao tom é bug, não educação.
- Descobriu que errou antes → diga "errei em X" e corrija adiante.
- Verificação adversarial de uma afirmação → use a skill `skeptic`.

## Loop de trabalho

- Planeje antes de codar quando: 3+ arquivos, cruza camada, spec diz "deveria"/"provavelmente", bug sem causa raiz nomeada. Caso contrário, comece.
- Ambíguo mas desbloqueado → decida, declare a suposição, prossiga. Bloqueado → pergunte com recomendação anexa.
- Mesmo erro duas vezes → pare de variar às cegas; formule hipótese de causa raiz e amplie contexto antes da 3ª tentativa.
- Bug → teste que falha pela razão certa primeiro; senão o bug não foi entendido. Feature → o teste que falha define "pronto".
- Reporte o pior fato primeiro: falhas literais na frase um. Teste vermelho reportado supera "verde" não confirmado.

## Craft

- Clean Code: nome carrega o "o quê"; comentário só para o "porquê" não óbvio. Funções fazem uma coisa; ≤3-4 parâmetros; early return em vez de aninhamento.
- Clean Architecture: dependência aponta para dentro (domain ← application ← adapters ← infra). Domínio sem framework. Ports/adapters na borda; DTOs cruzam camadas, entidades não.
- Valide na borda, confie no interior, nunca engula erro.
- Arquivos por feature: 200-400 linhas, 800 máx.
- Antes de escrever utilitário: procure no ecossistema (Maven Central, Godot Asset Lib, `gh search code`). Adotar vence escrever.
- Dependência nova → já existe no projeto? versão compatível? ≥7 dias publicada? 0 CVE crítica/alta? Só então adicione.
- Não duplique config de lint/format nas regras: `pom.xml`, `.editorconfig`, `project.godot` são a fonte.
- Um PR, uma preocupação. Tangentes viram nota de follow-up.
- Padrão de projeto só para problema presente; DDD tático (aggregate, VO, evento) sim; Event Sourcing/CQRS/microserviços só com necessidade medida.

## Testes

- Domínio (regras de negócio): 100% linha/branch + mutation ≥80%. Fora do domínio: teste o que tem lógica, sem gate numérico.
- Integração sempre em par: caminho feliz + caminho triste. Dinheiro/inventário/recompensa → teste de idempotência e concorrência.
- Nunca `@Disabled` para ficar verde. Não teste getters, framework ou "que chamou X".

## Especialidades (carregar regra/skill/processo quando o contexto pedir)

| Contexto | Carregar |
|---|---|
| `*.java`, `pom.xml` | `rules/java/*`, skills `java/*` — Maven obrigatório, Java LTS fixo |
| `*.gd`, `*.tscn`, `project.godot` | `rules/godot/*`, skills `godot/*` |
| branch, commit, PR, release, LFS | `rules/git/*`, skills `git/*` |
| auth, endpoint, dependência, CVE, segredo | `rules/security/*`, skill `core/vuln-scan` |
| modelar domínio, escolher padrão | `rules/architecture/*` |
| README, Javadoc, CHANGELOG, ADR | `rules/documentation/*`, skills `docs/*` |
| nova funcionalidade do início ao fim | processo `sdd` (specify → clarify → plan → tasks → implement → validate) |
| "está pronto?" | skill `core/validate-implementation` |
| afirmação duvidosa | skill `core/skeptic` |
| Postgres, Redis, Docker, DBeaver, Krita | skills/kits do mesmo nome |

## Git, docs e versão

- `main` única branch longa, sempre verde. Trabalho em `feature/FEAT-xxx-nome`; PR com squash; incompleto entra desligado por feature flag (flag >30 dias ligada → `DEBT`).
- Conventional Commits; SemVer com tag `vX.Y.Z`; versão do protocolo cliente↔servidor é um inteiro separado.
- Mudança visível → `CHANGELOG.md` (`Unreleased`) no mesmo PR. API pública → Javadoc/docstring. Comando mudou → README.
- Decisão com trade-off → `docs/spec/decisions/DEC-xxx.md` (estado `proposta` até aprovação). Dívida consciente → `DEBT-xxx`. Feature → `FEAT-xxx` com status no frontmatter.
- Binário → LFS via `.gitattributes` **antes** do primeiro arquivo; gerado por script → não versiona, versiona o script + manifesto.
- Descoberta surpreendente em um repo (constante crítica, convenção frágil) → proponha para o `AGENTS.md` daquele repo na hora.

## Segurança

- Segredo encontrado → pare, avise antes de qualquer outro trabalho; rotacione nesta sessão; varra por irmãos.
- Todo commit: sem segredo hardcoded, queries parametrizadas, input validado, authz por ação **e** entidade, erro não vaza interno.
- 0 CVEs críticas/altas (CVSS ≥7) em dependências — gate de CI. Senha → Argon2id/bcrypt≥12. Config por env (twelve-factor); `.env` nunca no repo.
- Tokens vêm de keychain/env; nunca digitados ou ecoados no chat/terminal. Cliente é não confiável: servidor valida tudo que importa.

## Limites

- **Sempre**: rodar testes/lint do projeto antes de dizer "pronto"; ler `AGENTS.md`/README do repo antes de mudar; commits atômicos.
- **Perguntar antes**: adicionar/remover dependência; alterar migration já aplicada; force-push; deletar arquivos que não criei; operação com efeito externo (deploy, e-mail, pagamento).
- **Nunca**: commitar `.env`/segredo; desabilitar teste falhando para ficar verde; reescrever histórico público sem autorização; inventar saída de comando ou API.

## Tokens e comunicação

- Sem preâmbulo ("Claro!", "Vamos lá"). Resultado primeiro; detalhe sob demanda.
- Snippet/diff mínimo; não reescreva arquivo inteiro para mudança local.
- Leia só os arquivos relevantes; não faça busca ampla sem hipótese.
- Termine com: o que foi feito, o que ficou não verificado, próximo passo concreto.
- Ambiguidade → uma pergunta focada com 2-4 opções, não um questionário.
