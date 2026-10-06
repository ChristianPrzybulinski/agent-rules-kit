---
description: Java build, module and dependency rules for Maven, Java 25, quality plugins and dependency changes.
kind: detail
---

# Java — build and dependencies

## Required

- **Maven** with wrapper (`./mvnw`). Gradle is not an option in this kit.
- Fixed Java **LTS** in `pom.xml` (`<maven.compiler.release>25</maven.compiler.release>`) and in `.java-version`/`toolchains.xml`. Never "whatever is installed".
- Dependency versions centralized in the parent POM's `<dependencyManagement>`; modules do not declare versions.
- Framework BOM (`spring-boot-dependencies`, the 4.1.x line pinned in the parent POM; never 3.5.x, out of OSS support) instead of loose versions.

## Multi-module structure (by context)

```text
server/
├── pom.xml                 # parent: pluginManagement, dependencyManagement, gates
├── domain/                 # zero framework dependency; JaCoCo 100% + PITest here
├── application/            # use cases, ports; depends only on domain
├── adapter-in-http/        # controllers, DTOs
├── adapter-in-ws/          # game session (if any)
├── adapter-out-persistence/ # repositories (JdbcClient or JPA, the declared choice), Flyway
└── bootstrap/              # main, Spring config, wiring
```

Inter-module dependency rule verified at build time (`maven-enforcer` `bannedDependencies` or ArchUnit in `domain`).

## Standard plugins (parent POM — see `platforms/kits/java-maven/`)

| Plugin | Role | Gate |
|---|---|---|
| `spotless-maven-plugin` | formatting (google-java-format) | `check` fails if unformatted |
| `jacoco-maven-plugin` | coverage | 100% line/branch in `domain` |
| `pitest-maven` | mutation testing | ≥80% in `domain` |
| `dependency-check-maven` | CVEs | fails on CVSS ≥ 7 |
| `maven-enforcer-plugin` | minimum Java/Maven, no duplicates, no SNAPSHOT in release | fails |
| `versions-maven-plugin` | update report | informational |
| `flyway-maven-plugin` | migrations | — |

## Condition → action

- Add a dependency → (1) already there transitively? (`mvn dependency:tree`), (2) version published ≥7 days, (3) local `dependency-check`, (4) entry in `dependencyManagement`.
- Update a dependency → `mvn versions:display-dependency-updates`; one family per PR (e.g.: only Spring), with green tests.
- Slow build → `mvn -T 1C` and profiles: `-Pfast` skips PITest/Dependency-Check locally; CI runs everything.
- Release → `mvn -B release:prepare release:perform` or version via CI from the commits; never hand-edit the version on release day.
