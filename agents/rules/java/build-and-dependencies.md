---
description: Java — Maven obrigatório, versão LTS fixa, estrutura multi-módulo, plugins de qualidade (Spotless, JaCoCo, PITest, Dependency-Check, Enforcer). Carregar ao criar projeto Java, mexer em pom.xml ou configurar CI.
trigger: model_decision
---

# Java — build e dependências

## Obrigatório

- **Maven** com wrapper (`./mvnw`). Gradle não é opção neste kit.
- Java **LTS** fixo no `pom.xml` (`<maven.compiler.release>25</maven.compiler.release>`) e em `.java-version`/`toolchains.xml`. Nunca "o que estiver instalado".
- Versões de dependências centralizadas no `<dependencyManagement>` do POM pai; módulos não declaram versão.
- BOM do framework (`spring-boot-dependencies`) em vez de versões soltas.

## Estrutura multi-módulo (por contexto)

```text
server/
├── pom.xml                 # pai: pluginManagement, dependencyManagement, gates
├── domain/                 # zero dependência de framework; JaCoCo 100% + PITest aqui
├── application/            # use cases, ports; depende só de domain
├── adapter-in-http/        # controllers, DTOs
├── adapter-in-ws/          # sessão de jogo (se houver)
├── adapter-out-jpa/        # repositórios, entidades JPA, Flyway
└── bootstrap/              # main, config Spring, wiring
```

Regra de dependência entre módulos verificada no build (`maven-enforcer` `bannedDependencies` ou ArchUnit em `domain`).

## Plugins padrão (POM pai — ver `kits/java-maven/`)

| Plugin | Papel | Gate |
|---|---|---|
| `spotless-maven-plugin` | formatação (google-java-format) | `check` falha se desformatado |
| `jacoco-maven-plugin` | cobertura | 100% linha/branch em `domain` |
| `pitest-maven` | mutation testing | ≥80% em `domain` |
| `dependency-check-maven` | CVEs | falha CVSS ≥ 7 |
| `maven-enforcer-plugin` | Java/Maven mínimos, sem duplicatas, sem SNAPSHOT em release | falha |
| `versions-maven-plugin` | relatório de atualizações | informativo |
| `flyway-maven-plugin` | migrações | — |

## Condição → ação

- Adicionar dependência → (1) já existe transitiva? (`mvn dependency:tree`), (2) versão ≥7 dias publicada, (3) `dependency-check` local, (4) entrada no `dependencyManagement`.
- Atualizar dependência → `mvn versions:display-dependency-updates`; uma família por PR (ex.: só Spring), com testes verdes.
- Build lento → `mvn -T 1C` e perfis: `-Pfast` pula PITest/Dependency-Check localmente; CI roda tudo.
- Release → `mvn -B release:prepare release:perform` ou versão pelo CI a partir dos commits; nunca editar versão à mão no dia.
