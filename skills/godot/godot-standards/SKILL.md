---
name: godot-standards
version: "1.0"
description: Aplica padrões de projeto Godot 2D com GDScript, nodes, sinais e autoloads.
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Godot 2D Expert

## Ao trabalhar com Godot 2D

1. Verifique `project.godot`, estrutura de cenas e scripts existentes.
2. Use GDScript tipado (`: Type`) e estilo oficial (snake_case/PascalCase).
3. Prefira sinais a chamadas diretas entre nós.
4. Use `_physics_process(delta)` para movimento/física; `_process(delta)` para efeitos visuais.
5. Organize em `autoload/`, `entities/`, `levels/`, `ui/`, `resources/`, `common/`.
6. Cache referências em `_ready`. Evite `get_parent()` para lógica.
7. Use `@export` para parâmetros ajustáveis e documente acima.
8. Mantenha cenas pequenas e reutilizáveis; prefira composição.
9. Teste lógica de jogo isolada quando possível.
10. Não armazene referências a nós em save.

## Verificações padrão

- `preload` para recursos estáticos; `load` para dinâmicos.
- Groups para identificar múltiplos nós sem acoplamento.
- TileMap/TileSet para mapas 2D.
- Autoloads para estado global e managers.
