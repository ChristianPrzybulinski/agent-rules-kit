---
name: vuln-scan
version: "1.0"
description: Varredura de vulnerabilidades — CVEs em dependências (Java/Maven, Godot addons, Docker images), segredos no repositório e histórico, e checklist OWASP em endpoints alterados. Usar antes de PR que toca dependências/auth/rede, em release, ou periodicamente.
argument-hint: "[deps | secrets | endpoints | all]  (padrão: all)"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Vuln Scan

Gate do kit: **0 CVEs críticas/altas (CVSS ≥ 7)**, **0 segredos**, endpoints novos com auth/authz/validação. Reporta; não corrige automaticamente (atualizar dependência pode quebrar — isso é uma tarefa normal com testes).

## deps

Java/Maven (obrigatório se houver `pom.xml`):
```bash
./mvnw -q org.owasp:dependency-check-maven:check -DfailBuildOnCVSS=7 -Dformats=JSON,HTML
```
Ler `target/dependency-check-report.json`. Para cada CVE ≥7: dependência, versão, CVE, CVSS, versão corrigida disponível (`./mvnw versions:display-dependency-updates`), caminho transitivo (`./mvnw dependency:tree -Dincludes=<groupId>`).
Falso positivo comprovado → propor entrada em `dependency-check-suppressions.xml` com `<notes>` (motivo + data de revisão em 90 dias). Nunca suprimir sem justificativa.

Docker (se houver `Dockerfile`/`compose`): imagens base fixadas por tag de versão (não `latest`); rodar `docker scout cves <imagem>` se disponível, senão registrar como não verificado.

Godot: addons em `addons/` → origem, versão, licença e última atualização; addon sem fonte rastreável → sinalizar.

## secrets

```bash
gitleaks detect --source . --redact -v      # se instalado
git log -p --all -S 'BEGIN PRIVATE KEY' --oneline | head
```
Sem gitleaks: `grep -rEn '(api[_-]?key|secret|password|token)\s*[:=]\s*["\x27][^"\x27]{8,}' --exclude-dir={.git,target,.godot,node_modules} .` e revisar manualmente; registrar que a varredura foi parcial.
Achado real → **parar tudo**, reportar primeiro, orientar rotação nesta sessão e varredura de irmãos. Nunca imprimir o valor do segredo no relatório.

## endpoints

Para cada endpoint/mensagem de rede no diff (`git diff <base>...HEAD`), tabela:

| Endpoint/Msg | Auth | Authz por entidade | Validação de entrada | Limite tamanho/frequência | Auditoria (se muda estado) | Erro não vaza interno |

Célula sem evidência (código ou teste) = ✗.

## Veredicto

```
Escopo: deps | secrets | endpoints | all
Gate CVE: OK | FALHOU — N críticas, M altas
| Dependência | Versão | CVE | CVSS | Corrigida em | Ação |
Segredos: nenhum | ENCONTRADO (tipo, arquivo, commit — sem valor)
Endpoints: tabela acima
Não verificado: <ferramenta ausente, escopo não coberto>
Próximo passo: <a menor ação que zera o gate>
```
