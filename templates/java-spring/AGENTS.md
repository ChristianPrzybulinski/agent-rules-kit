# AGENTS.md — Java + Spring Boot

Substitua os trechos entre [colchetes]. Regras globais do Kit-IA já se aplicam; aqui só o que o agente não consegue inferir.

## Stack

- Java [21] LTS, Spring Boot [3.x]. Build via wrapper: `./mvnw` (ou `./gradlew`). Nunca `mvn` global.
- Testes: JUnit 5 + AssertJ + Mockito. Integração: Testcontainers. Formatação: Spotless (fonte da verdade — não duplique estilo aqui).
- Banco: [PostgreSQL]; migrations Flyway em `src/main/resources/db/migration/V*.sql`.

## Estrutura

```text
src/main/java/[com/exemplo/app]
├── domain/         # entidades, value objects, exceções de domínio — sem Spring/JPA
├── application/    # use cases + ports (interfaces)
├── adapter/        # in: controllers, DTOs, mappers | out: repositórios JPA, clients HTTP
└── infrastructure/ # config Spring, beans, segurança
src/test/java       # espelha main
```

## Comandos

```bash
./mvnw spring-boot:run                    # subir local
./mvnw test                               # unit
./mvnw -Dtest=NomeDoTeste test            # um teste
./mvnw verify                             # unit + integração
./mvnw spotless:apply                     # formatar
./mvnw spotless:check verify              # gate antes de commit/PR
```

## Padrões (condição → ação)

- Criar bean → injeção por construtor; classe `final` com campos `private final`. Nunca `@Autowired` em campo.
- Expor endpoint → DTO (`record`) de entrada/saída; entidade JPA nunca sai do adapter.
- Valor pode faltar → `Optional` no retorno; nunca `null`. Parâmetro nunca é `Optional`.
- Erro de negócio → exceção de domínio específica em `domain/`; `@ControllerAdvice` converte para RFC 7807 (`ProblemDetail`).
- Consulta com filtros → `Specification` ou query method nomeado; evite JPQL em string quando houver alternativa tipada.
- Config → `@ConfigurationProperties` + `record`; sem `@Value` espalhado.
- Log → SLF4J com placeholders; nunca concatenar; nunca logar dado sensível.
- Novo teste de domínio → sem `@SpringBootTest`; puro JUnit. `@SpringBootTest` só para integração real.

Exemplo — use case com port:

```java
public final class CriarPedido {
    private final PedidoRepository repo;
    public CriarPedido(PedidoRepository repo) { this.repo = repo; }
    public Pedido executar(NovoPedido cmd) {
        var pedido = Pedido.novo(cmd.clienteId(), cmd.itens());
        return repo.salvar(pedido);
    }
}
```

## Git & PR

1. `git switch -c feat/<nome-curto>` a partir de `main`.
2. Conventional Commits.
3. Antes do push: `./mvnw spotless:check verify` verde.
4. `gh pr create` com: resumo em 1 linha, o que testou, `Closes #N`.

## Limites

- Sempre: migration nova para mudança de schema; teste para bug corrigido; ler `application.yml` antes de assumir config.
- Perguntar antes: mudar `pom.xml`/`build.gradle`; editar migration já aplicada; alterar auto-config do Spring; mudar contrato de API pública.
- Nunca: `@Disabled` para ficar verde; `.env` ou credencial no repo; `ddl-auto=update` em produção.

## Mais

- Fronteiras de camada: `docs/architecture.md`. Decisões: `docs/adr/`.
