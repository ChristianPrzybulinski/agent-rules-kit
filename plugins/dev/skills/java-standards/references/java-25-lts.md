---
description: Java 25 LTS and Spring Boot 4.1.x facts (GA dates, support windows, Java range, project pins, Temurin CI). Load when configuring a Java project, pom or CI.
kind: fact
verified: "2026-10-06"
sources:
  - https://openjdk.org/projects/jdk/25/
  - https://spring.io/projects/spring-boot#support
  - https://docs.spring.io/spring-boot/system-requirements.html
---

# Java 25 (LTS) and Spring Boot 4.1 — facts

- Java 25 is an OpenJDK **LTS** release, GA on 2025-09-16. LTS in the Oracle/OpenJDK model: every 2 years (21 → 25 → next expected 29). Source: https://openjdk.org/projects/jdk/25/ and Oracle Java SE Support Roadmap.
- Oracle: Premier Support until Sep/2030, Extended until Sep/2033. Other vendors (Temurin, Amazon Corretto) keep free builds on their own timelines.
- The project pins its JDK, not the machine: `.java-version` (`25`), `pom.xml` `<maven.compiler.release>25</maven.compiler.release>` and `~/.m2/toolchains.xml` copied from `platforms/kits/java-maven/toolchains.xml.example` (the enforcer requires `[25,26)`). CI: `actions/setup-java` with `distribution: temurin` and the `java-version` input of `platforms/kits/github/workflows/ci-java.yml` (default `'25'`). Containers: `maven:3.9-eclipse-temurin-25` build, `eclipse-temurin:25-jre` runtime (`platforms/kits/docker/README.md`). The machine's exact build and path are local state: check them with `java -version` and `mvn -v` when a task needs them, and record only the project pin.

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

## Spring Boot baseline

- GA line: **4.1.x**; 4.1.1 released 2026-08-20 and the latest 4.1.x GA on Maven Central (verify against https://spring.io/projects/spring-boot#support before bumping). 4.0.x OSS support ends 2026-12-31; 4.1.x OSS support runs to 2027-07-31 (same page); 3.5.x left OSS support on 2026-06-30 (the 3.5 line's last OSS patch). Never start a project on 3.5.x or 4.0.x.
- Boot 4.1.x runs on Java 17 to 26, so Java 25 is inside the window (the 4.1.1 system-requirements page; verify the upper bound before relying on it); `spring-boot-starter-parent:4.1.1` defaults `java.version` to 17, so `<maven.compiler.release>25</maven.compiler.release>` is required.
- Kit pin: the parent POM in `platforms/kits/java-maven/` imports `spring-boot-dependencies:4.1.1`; a project built on `spring-boot-starter-parent` uses the same version. Boot 4 ships Spring Framework 7 (4.1.1 resolves `spring-core 7.0.9`) and Jackson 3 (`tools.jackson`): check artifact names before copying Boot 3 snippets.
