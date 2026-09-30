# kit java-maven

POM pai com os gates de qualidade do kit. Versões verificadas no Maven Central em 2026-09-29.

## Como usar

1. No projeto, copie `pom-parent.xml` para `server/pom.xml` (ou raiz), ajuste `groupId`/`artifactId`/`version` e liste os módulos em `<modules>`.
2. Estrutura de módulos: ver `rules/java/build-and-dependencies.md` (`domain`, `application`, `adapter-*`, `bootstrap`). Módulos declaram o pai em `<parent>` e **não** declaram versão de dependência.
3. Copie `.java-version` para a raiz do repo.
4. `dependency-check-suppressions.xml` vai na raiz do projeto (o pai referencia por nome).
5. `toolchains.xml.example` → `~/.m2/toolchains.xml` (local, não versionar). Necessário porque o JDK do PATH pode ser ≠ 25 — o enforcer exige `[25,26)`.
6. Wrapper: gere no projeto com `mvn wrapper:wrapper -Dmaven=3.9.16` (binários **não** são distribuídos neste kit).

## Gates

- **Sempre**: `spotless:check` (google-java-format), JaCoCo report, enforcer (Java `[25,26)`, Maven `[3.9,)`, sem dependência duplicada no POM).
- **`domain-gate`** (automático): módulo com o marcador `src/main/java/.domain` (arquivo vazio) ganha JaCoCo `check` 100% linha+branch e PITest `mutationCoverage` (threshold 80, JUnit 5). Opção escolhida por ser declarativa — alternativa: declarar os dois plugins no `pom.xml` do módulo domain.
- **`fast`**: `-Pfast` pula PITest e dependency-check. Testes **não** são pulados (`skipTests` não é tocado).
- **`release`**: `-Prelease` adiciona `requireReleaseDeps` (sem SNAPSHOT).

## CI

`kits/github/workflows/ci-java.yml` roda `spotless:check verify` + dependency-check em job separado.
