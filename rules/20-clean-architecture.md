---
description: Detalhes de Clean Architecture (camadas, regra da dependência, ports/adapters, DTOs, exceções). Carregar ao criar módulo, camada ou decidir onde uma classe vive; o resumo já está no AGENTS.md.
trigger: model_decision
---

# Clean Architecture

## Camadas (de fora para dentro)

1. Frameworks & Drivers (UI, DB, APIs externas, bibliotecas).
2. Interface Adapters (controllers, presenters, gateways, DTOs).
3. Use Cases (regras de aplicação, orquestração).
4. Entities (regras de negócio, domínio puro).

## Regra da Dependência

- Dependências apontam **sempre para dentro**.
- Camadas internas não conhecem camadas externas.
- Use interfaces (ports) para inverter dependências.

## Frameworks são detalhes

- O domínio e os use cases não devem depender de Spring, Hibernate, Godot nodes, GDScript específicos, etc.
- Isole adaptadores para trocar frameworks sem tocar no núcleo.

## DTOs e boundaries

- Use DTOs na borda entre camadas. Nunca passe entidades diretamente para a UI/DB sem adaptação.
- Mantenha DTOs enxutos e imutáveis quando possível.

## Testabilidade

- Regras de negócio devem ser testáveis sem banco de dados, sem rede e sem UI.
- Use mocks/fakes para ports, nunca para entidades.

## Exceções

- Exceções de domínio (camada interna) são diferentes de erros de infraestrutura (camada externa).
- Converta exceções externas em exceções de domínio próximas à borda.
