---
description: Redis 7.4 para dev local e licenciamento por versão (≤7.2 BSD, 7.4–7.8 RSALv2/SSPLv1, ≥8.0 +AGPLv3). Carregar ao propor cache/sessão ou pinar imagem.
trigger: model_decision
verified: "2026-09-29"
sources:
  - https://redis.io/legal/licenses/
  - https://redis.io/blog/agplv3/
---

# Redis 7 — versão e licença

- Versão escolhida para dev local: **7.4** (última minor 7.x no Docker Hub — tag `redis:7.4`). A linha 7.x não recebe novos features; considerar 8.x em projetos novos.

## Licença (importante)

Fonte: https://redis.io/legal/licenses/ e https://redis.io/blog/agplv3/

| Versão | Licença |
|---|---|
| ≤ 7.2 | BSD-3-Clause |
| 7.4 – 7.8 ("Community Edition") | dual: RSALv2 **ou** SSPLv1 (nenhuma OSI-approved) |
| ≥ 8.0 ("Redis Open Source", GA 2025-05-02) | tripla: RSALv2 **ou** SSPLv1 **ou** AGPLv3 (OSI-approved) |

Ou seja: Redis 7.4+ mudou para RSALv2/SSPLv1 (mar/2024); a partir do 8.0 a AGPLv3 voltou como opção. Para uso local/dev isso não restringe nada; relevante ao distribuir ou oferecer Redis como serviço.
