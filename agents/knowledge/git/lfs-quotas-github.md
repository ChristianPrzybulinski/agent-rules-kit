---
description: Quotas atuais do Git LFS por plano GitHub (Free/Pro 10 GiB, Team 250 GiB). Carregar ao configurar LFS ou avaliar custo de binários.
trigger: model_decision
verified: "2026-09-29"
sources:
  - https://docs.github.com/en/billing/concepts/product-billing/git-lfs
---

# GitHub Git LFS — quotas


| Plano | Storage | Bandwidth/mês |
|---|---|---|
| GitHub Free / Pro / Free for orgs | 10 GiB | 10 GiB |
| Team / Enterprise Cloud | 250 GiB | 250 GiB |

- Storage é medido por uso por hora; bandwidth reseta todo ciclo de cobrança.
- Sem método de pagamento ou budget $0: estourar quota **bloqueia** LFS até o próximo ciclo (não cobra nada).
- Budget aberto: cobrança metered por GiB (bandwidth) e por GiB-mês (storage), sem data packs desde 2024/2025.
- Monitorar: `git lfs ls-files -s` no repo; uso da conta em Settings → Billing.
- Alternativa para acervo grande: manter binários fora do GitHub (ver `rules/git/git-lfs-and-binaries.md`).
