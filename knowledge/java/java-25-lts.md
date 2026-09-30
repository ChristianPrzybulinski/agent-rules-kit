# Java 25 (LTS) — fatos

Verificado: 2026-09-29.

- Java 25 é um release **LTS** do OpenJDK, GA em 2025-09-16. LTS no modelo Oracle/OpenJDK: a cada 2 anos (21 → 25 → próximo previsto 29). Fonte: https://openjdk.org/projects/jdk/25/ e Oracle Java SE Support Roadmap.
- Oracle: Premier Support até set/2030, Extended até set/2033. Outros vendors (Temurin, Amazon Corretto) mantêm builds gratuitos por prazos próprios.
- Instalado nesta máquina: OpenJDK **25.0.4.1** via Homebrew (`brew install openjdk@25`, keg-only, `/opt/homebrew/opt/openjdk@25`).

## Features finalizadas (GA) presentes em 25

| JEP | Feature | GA em |
|---|---|---|
| 396/420/441 | Records | 16 / pattern `instanceof` 16 / switch patterns 21 |
| 409 | Sealed classes | 17 |
| 440/441 | Record patterns, pattern matching for switch | 21 |
| 444 | Virtual threads | 21 |
| 456 | Unnamed variables & patterns (`_`) | 22 |
| 458/462/463/477 | Simple source files / instance `main` | 25 |
| 511 | Module import declarations | 25 |
| 513 | Flexible constructor bodies | 25 |
| 506 | Scoped values | 25 (GA) |

Nota: structured concurrency (JEP 505) seguia em **preview** no 25 — não contar como GA.

Referência canônica de JEPs por release: https://openjdk.org/projects/jdk/25/
