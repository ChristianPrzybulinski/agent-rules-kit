---
description: DDD tático e catálogo de design patterns com "quando usar / quando não". Carregar ao modelar domínio, escolher um padrão ou revisar arquitetura de um módulo.
trigger: model_decision
---

# DDD tático e padrões

Padrão se justifica por um problema presente, não por popularidade. Cada uso não óbvio → 1 linha de "porquê" no código ou ADR.

## DDD — o que usar

| Bloco | Use quando | Exemplo |
|---|---|---|
| Value Object | conceito definido pelos atributos, imutável | `Money`, `Position`, `Hp` — `record` com validação no construtor |
| Entity | identidade persiste ao longo do tempo | `Player`, `Creature` |
| Aggregate | invariantes precisam ser garantidas juntas numa transação | `Inventory` (itens + capacidade), `BattleInstance` (turnos + participantes) |
| Domain Event | algo aconteceu e outros módulos reagem | `BattleEnded`, `ItemAcquired` |
| Repository | persistir/recuperar aggregate inteiro | `PlayerRepository` (port no `application`, impl JPA no `adapter`) |
| Domain Service | regra que não pertence a uma entidade | `DamageCalculator` |

Não use: DDD estratégico formal (context maps, ubiquitous language por equipe) com 1 dev; Event Sourcing sem necessidade de reconstruir histórico; CQRS completo antes de haver leitura e escrita com perfis distintos medidos.

## Catálogo — quando sim / quando não

| Padrão | Sim | Não |
|---|---|---|
| Ports & Adapters | sempre na fronteira domínio↔infra | — |
| Command | ações do usuário validadas/enfileiradas/auditadas (`MoveCommand`, `AttackCommand`) | CRUD simples |
| State Machine | estados com transições explícitas (turno de batalha, conexão, quest) | 2 estados booleanos |
| Strategy | variações de algoritmo escolhidas em runtime (efeito de ataque, cálculo de dano por tipo) | 1 implementação |
| Specification | regras de validação combináveis e nomeadas (`PodeEvoluir`, `PodeTrocar`) | `if` único |
| Transactional Outbox | evento precisa sair **se e só se** a transação commitou (recompensa, troca) | evento informativo sem consequência |
| Idempotency Key | operação pode ser reenviada (rede, retry) e não pode duplicar efeito | leitura |
| Factory | criação com invariantes ou múltiplos passos | construtor basta |
| Observer/Signals | desacoplar quem emite de quem reage (Godot: sinais; Java: Domain Events) | chamada direta é clara e local |
| Object Pool | criação cara e frequente medida (projéteis, partículas) | otimização prematura |
| Repository | acesso a aggregate | tabela de lookup estática |

## Anti-padrões a barrar em review

- Singleton para estado de jogo mutável (Godot: autoload virando "god object"; Java: `static` mutável).
- Active Record no domínio (entidade que salva a si mesma).
- Anemic Domain: entidade só com getters/setters e regras no "service".
- Utils/Helpers genéricos crescendo sem dono.
- Herança para reuso de código (use composição).
