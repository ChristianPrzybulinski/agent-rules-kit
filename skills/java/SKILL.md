---
name: java
version: "1.0"
description: Aplica padrões Java moderno, Clean Code, Clean Architecture e testes.
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Java Expert

## Ao trabalhar com Java

1. Verifique o baseline do projeto (`pom.xml`, `build.gradle`, `.java-version`).
2. Respeite a estrutura de pacotes existente.
3. Aplique Clean Code e Clean Architecture.
4. Prefira imutabilidade, `Optional`, `Stream`, `record`.
5. Adicione testes com JUnit 5 + AssertJ/Mockito.
6. Não adicione dependências sem verificar compatibilidade.
7. Documente APIs públicas com JavaDoc conciso.

## Verificações padrão

- Nomes em inglês, salvo convenção do projeto.
- Não retorne `null`; use `Optional` ou exceções de domínio.
- Separe entidades de domínio de entidades JPA quando o domínio for crítico.
- Use constructor injection no Spring/Quarkus.
- Evite lógica em controllers; delegue a use cases/services.
