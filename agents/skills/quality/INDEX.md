# skills/quality/ — verificação e qualidade

| Skill | Escopo | Quando usar |
|---|---|---|
| `skeptic` | verificação adversarial de afirmação (contra → a favor → veredicto) | algo "parece certo" mas não foi provado |
| `validate-implementation` | confronta entrega com spec/pedido, roda gates, veredicto PRONTO/PARCIAL/NÃO PRONTO | antes de PR ou de dizer "feito" |
| `vuln-scan` | CVEs em deps, segredos no repo, checklist OWASP | PR que toca dep/auth/rede, release |
| `characterization-tests` | testes que fixam comportamento ATUAL de legado | antes de refatorar/migrar/rebalancear |
