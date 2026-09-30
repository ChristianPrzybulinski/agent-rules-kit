---
name: dbeaver
version: "1.0"
description: DBeaver para inspecionar o PostgreSQL local — conexão via .env, exportar/importar dados de teste, gerar DDL/ER para documentação, sem tornar-se fonte de mudança de schema (isso é Flyway). Usar quando o humano precisa ver/editar dados ou gerar diagrama.
argument-hint: "[connect | export | er-diagram]"
triggers:
  - user
allowed-tools:
  - read
  - exec
---

# DBeaver

Ferramenta **humana** de inspeção. O agente não opera a GUI; orienta e prepara arquivos. Fonte de verdade do schema é Flyway — mudanças feitas no DBeaver **não** contam até virarem `V<n>__*.sql`.

## connect

1. Ler `.env` do projeto (não imprimir senha): host `127.0.0.1`, porta, db, usuário.
2. DBeaver → Nova conexão → PostgreSQL → preencher; "Show all databases" desligado; salvar senha no keychain do macOS (opção do DBeaver), não em arquivo exportado.
3. Arquivo de conexão do DBeaver (`~/Library/DBeaverData/workspace6/General/.dbeaver/data-sources.json`) **não** vai para o repo.

## export (dados de teste)

- Preferir script SQL versionado em `src/test/resources/fixtures/*.sql` gerado por `pg_dump --data-only --table=<t>` a export da GUI (reproduzível).
- Dados pessoais reais → nunca em fixture. Anonimizar antes.

## er-diagram

- DBeaver → schema → ER Diagram → exportar PNG/SVG para `docs/architecture/er-<data>.svg`.
- Diagrama é derivado: regenerar após migração relevante; anotar versão da migração (`V<n>`) na legenda.

## Não faça

- Alterar schema pela GUI em qualquer ambiente que não seja descartável.
- Rodar `DELETE`/`UPDATE` sem `WHERE` — DBeaver pede confirmação; ainda assim, pergunte antes.
