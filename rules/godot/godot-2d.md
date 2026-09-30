---
description: Regras para desenvolvimento de jogos 2D com Godot e GDScript.
trigger: model_decision
---

# Godot 2D

## Organização do projeto

```text
project/
├── project.godot
├── autoload/           # Singletons globais (GameManager, Audio, Save)
├── common/             # Componentes reutilizáveis
├── entities/           # Cenas de personagens, inimigos, itens
├── levels/             # Mapas/fases
├── ui/                 # Menus, HUD, telas
├── resources/          # Sprites, sons, fontes, tilesets
└── tests/              # Testes de integração/cena quando aplicável
```

## GDScript

- Estilo oficial GDScript: `snake_case` para variáveis/funções/arquivos, `PascalCase` para classes/nós.
- Use tipagem estática (`: Type`) sempre que possível.
- Evite código em `_ready` longo; delegue para funções bem nomeadas.
- Sinais são preferidos a chamadas diretas entre nós para desacoplamento.
- Use `@export` para parâmetros ajustáveis no editor.
- Documente propriedades `@export` com comentários acima.

## Nodes e cenas

- Cenas pequenas e reutilizáveis. Prefira composição a herança profunda.
- Respeite a hierarquia do SceneTree; evite `get_parent()` para lógica de jogo.
- Use Groups para identificar múltiplos nós sem acoplamento.
- Separe visual, física e lógica quando possível.

## Física e processamento

- Use `_physics_process(delta)` para movimento/física; `_process(delta)` para animações/efeitos visuais.
- Evite operações pesadas por frame. Cache referências em `_ready`.
- Use `call_deferred` quando necessário para evitar estados intermediários de física.

## Recursos

- Prefira `Resource` pré-carregados (`preload`) para cenas e scripts reutilizáveis.
- Mantenha texturas e sprites organizados em `res://resources/`.
- Use TileMap/TileSet para mapas 2D; evite posicionar tiles manualmente.

## Save e estado

- Centralize estado global em autoloads.
- Salve em JSON ou Resource personalizado; versione o formato de save.
- Não armazene referências a nós no save.

## Clean Architecture no Godot

- Domínio do jogo (regras, estado, eventos) pode viver em autoloads/classes puras.
- Cenas/nós são adapters/interface; regras de jogo devem ser testáveis isoladamente.
