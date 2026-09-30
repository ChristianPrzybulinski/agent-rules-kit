---
description: Desenvolvimento seguro — CVEs, segredos, OWASP Top 10, autenticação, autorização, dados pessoais, auditoria. Carregar ao mexer em dependências, auth, endpoints, persistência de dados sensíveis ou CI.
trigger: model_decision
---

# Desenvolvimento seguro

## Gates (falham o build/PR)

- **0 CVEs críticas ou altas** em dependências: OWASP Dependency-Check (Java) no CI, `failBuildOnCVSS=7`. Falso positivo → suppression com justificativa e data de revisão.
- Segredo detectado no diff (gitleaks/`gh secret scanning`) → PR bloqueado.
- Dependência nova só com versão publicada há ≥7 dias (supply chain).

## Segredos e credenciais

- Fonte: variável de ambiente ou keychain. Nunca em código, yml, log, commit, chat.
- `.env.example` versionado com placeholders; `.env` no `.gitignore`.
- Segredo vazou → rotacionar **nesta sessão**, depois varrer histórico (`gitleaks detect`) e irmãos.

## Autenticação e sessão

- Senha → Argon2id (preferido) ou bcrypt cost ≥ 12. Nunca MD5/SHA-1/SHA-256 puro.
- Token de sessão: aleatório ≥128 bits, expira, revogável, nunca em URL/log.
- Recuperação de acesso: token de uso único, curto, enviado fora de banda.

## Autorização

- Por ação **e** por entidade: "pode mover *este* personagem", não "está logado".
- Servidor é autoritativo: cliente envia intenção, servidor valida invariantes e decide resultado.
- Ferramenta administrativa: papel explícito + auditoria de cada uso.

## Entrada e saída

- Validar na borda (tamanho, tipo, faixa, enum). Rejeitar, não "sanitizar e seguir".
- SQL só parametrizado. Sem concatenação, sem `nativeQuery` com string montada.
- Erro para o cliente: código + mensagem genérica. Stack trace, SQL, caminho interno → só no log.

## Dados pessoais (LGPD)

- Coletar o mínimo. E-mail e IP são pessoais. Não copiar dados reais do legado para fixtures.
- Log de auditoria: quem, quando, o quê, resultado. Sem senha, token ou payload sensível.

## Condição → ação

- Novo endpoint → checklist: auth? authz por entidade? validação? rate limit? log de auditoria se muda estado?
- Dependência nova → `mvn dependency-check:check` local antes do PR.
- Mensagem de rede nova → limite de tamanho e frequência definidos no contrato.
