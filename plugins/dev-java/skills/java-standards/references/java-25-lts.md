---
description: Java 25 LTS (GA 2025-09-16, Oracle support until 2030/2033, kit-pinned JDK, Maven toolchains). Load when configuring a Java project or pom.
kind: fact
verified: "2026-09-29"
sources:
  - https://openjdk.org/projects/jdk/25/
---

# Java 25 (LTS) — facts

- Java 25 is an OpenJDK **LTS** release, GA on 2025-09-16. LTS in the Oracle/OpenJDK model: every 2 years (21 → 25 → next expected 29). Source: https://openjdk.org/projects/jdk/25/ and Oracle Java SE Support Roadmap.
- Oracle: Premier Support until Sep/2030, Extended until Sep/2033. Other vendors (Temurin, Amazon Corretto) keep free builds on their own timelines.
- The project pins its JDK, not the machine: `.java-version` (`25`), `pom.xml` `<maven.compiler.release>25</maven.compiler.release>` and `~/.m2/toolchains.xml` copied from `platforms/kits/java-maven/toolchains.xml.example` (the enforcer requires `[25,26)`). CI: `actions/setup-java` with `distribution: temurin` and the `java-version` input of `platforms/kits/github/workflows/ci-java.yml` (default `'25'`). Containers: `maven:3.9-eclipse-temurin-25` build, `eclipse-temurin:25-jre` runtime (`platforms/kits/docker/README.md`). The machine's exact build and path are local state (`java -version`, `mvn -v`) and belong in `docs/machine.local.md`, never a kit fact.

## Finalized (GA) features present in 25

| JEP | Feature | GA in |
|---|---|---|
| 396/420/441 | Records | 16 / `instanceof` pattern 16 / switch patterns 21 |
| 409 | Sealed classes | 17 |
| 440/441 | Record patterns, pattern matching for switch | 21 |
| 444 | Virtual threads | 21 |
| 456 | Unnamed variables & patterns (`_`) | 22 |
| 458/462/463/477 | Simple source files / instance `main` | 25 |
| 511 | Module import declarations | 25 |
| 513 | Flexible constructor bodies | 25 |
| 506 | Scoped values | 25 (GA) |

Note: structured concurrency (JEP 505) was still in **preview** in 25 — do not count as GA.

Canonical JEP-per-release reference: https://openjdk.org/projects/jdk/25/
