---
description: ArchUnit rule set for a hexagonal Java service (domain purity, no nondeterminism, layers point inwards) and the Spring Modulith verify() alternative.
kind: detail
---

# Java - ArchUnit rules

## Setup

- Test dependency `com.tngtech.archunit:archunit-junit5` (verify the current version on Maven Central before relying on it). One plain JUnit class, no Spring context:

```java
private static final JavaClasses CLASSES = new ClassFileImporter()
    .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
    .importPackages("com.example.app");
```

## Rules

1. Domain depends only on the JDK and itself:

```java
classes().that(resideInAPackage("com.example.app.domain..")).should()
    .onlyDependOnClassesThat(resideInAPackage("java..").or(resideInAPackage("javax.."))
        .or(resideInAPackage("com.example.app.domain..")));
```

2. No framework or infrastructure imports in domain (extend to `application` if the project chooses): `resideOutsideOfPackages("org.springframework..", "com.fasterxml.jackson..", "tools.jackson..", "java.sql..", "javax.sql..", "jakarta.servlet..", "jakarta.websocket..", "org.postgresql..")`.

3. No nondeterminism - a `DescribedPredicate<JavaMethodCall>` on method calls, plus `callConstructorWhere` the target owner is assignable to `java.util.Random`:

```java
public boolean test(JavaMethodCall call) {
  String o = call.getTargetOwner().getFullName(), n = call.getName();
  return (o.equals("java.lang.Math") && n.equals("random"))
      || (o.equals("java.lang.System") && (n.equals("currentTimeMillis") || n.equals("nanoTime")))
      || (o.startsWith("java.time") && n.equals("now"))
      || o.equals("java.util.concurrent.ThreadLocalRandom")
      || (o.equals("java.util.UUID") && n.equals("randomUUID"))
      || (o.equals("java.time.Clock") && n.startsWith("system"))
      || (o.equals("java.security.SecureRandom") && n.startsWith("getInstance"));
}
```

4. Layers point inwards - `layeredArchitecture().consideringOnlyDependenciesInLayers()` with layers `Domain`, `Application`, `Adapters`, `Infra`; `whereLayer("Domain").mayOnlyBeAccessedByLayers("Application", "Adapters", "Infra")`, `whereLayer("Application").mayOnlyBeAccessedByLayers("Adapters", "Infra")`, `whereLayer("Adapters").mayOnlyBeAccessedByLayers("Infra")`, `whereLayer("Infra").mayNotBeAccessedByAnyLayer()`.

- `.allowEmptyShould(true)` on every rule: ArchUnit 1.x fails a rule whose selection matches no class (`archRule.failOnEmptyShould=true` by default), and a not-yet-populated layer must not break the build. An empty selection then passes vacuously - which is why the negative fixtures below are mandatory.

## Negative fixtures

- Nested `static final class Bad*` violators (one per banned call or import) plus one `GoodPure` class; tests assert `assertThatThrownBy(() -> rule.check(withFixtures)).isInstanceOf(AssertionError.class).hasMessageContaining("Bad...")`. A rule without a failing fixture is not a gate.

## Alternative: Spring Modulith

- `ApplicationModules.of(Application.class).verify()` in one test enforces module boundaries from the package layout (`spring-modulith-starter-test`; verify against https://docs.spring.io/spring-modulith/reference/ before relying on it). Use it when the project is one Spring Boot application split into modules by package; keep ArchUnit when the rules go beyond module dependencies (nondeterminism, banned packages).

## Policy

- Never `@Disabled` or delete an architecture test to make a build pass: fix the dependency, or change the rule in the same PR with the reason.
