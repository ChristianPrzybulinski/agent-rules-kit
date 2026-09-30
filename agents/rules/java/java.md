---
description: Regras específicas para desenvolvimento Java moderno, Clean Code e Clean Architecture. Carregar em código `*.java`.
trigger: model_decision
---

# Java

## Estilo e linguagem

- Use Java 17+ como baseline. Prefira `var` quando o tipo é óbvio.
- Use `Optional` para valores que podem ser ausentes; evite retornar `null`.
- Prefira `Stream` e `Collectors` para transformações; evite loops imperativos quando funcional é mais claro.
- Use `record` para DTOs/imutáveis quando aplicável.
- Use `sealed` classes/interfaces e pattern matching quando ajudar a modelar o domínio.

## Estrutura de pacotes (Clean Architecture)

```text
com.exemplo.projeto
├── domain          # Entities, value objects, domain services, exceptions
├── application     # Use cases, ports (interfaces de entrada/saída)
├── infrastructure  # Implementações de ports: DB, HTTP, mensageria
└── adapter         # Controllers, presenters, CLI, web
```

- Pacotes não devem depender de frameworks externos no domínio/application.

## Frameworks

- **Spring Boot**: use constructor injection, evite `@Autowired` em campos, prefira `@ConfigurationProperties` para config.
- **Quarkus**: priorize injeção de construtor e `@ApplicationScoped`.
- **Jakarta EE / JPA**: mantenha entidades de persistência na infraestrutura; entidades de domínio são separadas quando necessário.

## Testes

- Use JUnit 5 + AssertJ/Mockito.
- Nomeie testes em português ou inglês, mas consistentemente: `deveCalcularTotalQuandoAdicionarItem` / `shouldCalculateTotalWhenAddingItem`.
- Teste unidades de domínio sem Spring Context. Testes de integração com `@SpringBootTest` só quando necessário.

## Dependências

- Não adicione bibliotecas sem justificativa. Verifique `pom.xml` / `build.gradle` existentes.
- Prefira bibliotecas do ecossistema padrão (SLF4J, Jackson, etc.).
- Valide a compatibilidade de versão com o Java do projeto.

## Logging e exceções

- Use SLF4J. Não logue dados sensíveis.
- Crie exceções de domínio específicas. Não use `RuntimeException` genérica.
- Evite capturar exceções silenciosamente.
