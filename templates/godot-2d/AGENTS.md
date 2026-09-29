# AGENTS.md — Godot 4 (2D, GDScript)

Substitua os trechos entre [colchetes]. Regras globais do Kit-IA já se aplicam; aqui só o que o agente não consegue inferir.

## Stack

- Godot [4.x] (confirme em `project.godot` → `config/features`). GDScript com tipagem estática obrigatória.
- Testes: [GUT | gdUnit4] em `tests/`. Renderer: [Forward+ | Mobile | Compatibility].
- Pixel art: `rendering/textures/canvas_textures/default_texture_filter = Nearest` (ver `project.godot`).

## Estrutura

```text
res://
├── project.godot
├── autoload/      # GameState, EventBus, AudioManager, SaveManager (singletons)
├── common/        # componentes reutilizáveis (HealthComponent, Hitbox, StateMachine)
├── entities/      # player/, enemies/, items/ — cada um: .tscn + .gd + sprites
├── levels/        # cenas de fase + TileMapLayers
├── ui/            # menus, HUD, telas
├── resources/     # .tres (dados de balanceamento, stats), fontes, temas
├── assets/        # sprites, áudio (fonte bruta)
└── tests/
```

## Comandos

```bash
godot --path . --editor                         # abrir editor
godot --path . --headless --quit                # importa assets/valida projeto (CI)
godot --path . --headless -s addons/gut/gut_cmdln.gd   # rodar GUT (ajuste ao framework)
godot --path . --headless --export-release "[preset]" build/[nome]   # export
```

## Padrões (condição → ação)

- Declarar variável/parâmetro/retorno → sempre com tipo (`var speed: float = 120.0`, `func hit(dmg: int) -> void`).
- Referenciar nó filho → `@onready var sprite: Sprite2D = $Sprite2D`; nunca `get_node` dentro de `_process`.
- Comunicar entre nós não-pais → sinal (ou `EventBus` autoload). `get_parent()` para lógica de jogo é proibido.
- Mover corpo → `_physics_process(delta)`; `CharacterBody2D.move_and_slide()`. Visual/animação → `_process(delta)`.
- Sobrescrever `_ready`/`_process` em classe filha → chame `super()`.
- Parâmetro de tuning → `@export` com range e comentário de uma linha acima.
- Comportamento compartilhado (vida, dano, estado) → componente em `common/` composto na cena; não herança profunda.
- Instanciar cena repetidamente → `preload` em constante; considere pooling se >50 instâncias/frame.
- Mapa → `TileMapLayer` (4.3+); camadas separadas para chão/colisão/decoração.
- Colisão → nomeie layers/masks em `project.godot` (`layer_names/2d_physics`); nunca use números mágicos.
- Save → dados puros (Dictionary/Resource) versionados com `save_version`; nunca referência a Node.
- Feature envolve `.gd` + `.tscn` + `.tres` + `project.godot` → leia todos antes de mudar um.

Exemplo — componente com sinal:

```gdscript
class_name HealthComponent
extends Node

signal died
signal changed(current: int, max_value: int)

## Vida máxima; ajustável por inimigo no editor.
@export_range(1, 999) var max_health: int = 10
var current: int

func _ready() -> void:
    current = max_health

func take_damage(amount: int) -> void:
    current = maxi(current - amount, 0)
    changed.emit(current, max_health)
    if current == 0:
        died.emit()
```

## Git & PR

- `.tscn`/`.tres` são texto: revise o diff; conflitos em UIDs → reimporte, não edite à mão.
- Commite `.godot/` **nunca**; commite `*.import` **sempre**.
- Conventional Commits; PR com GIF/print quando a mudança é visual.

## Limites

- Sempre: rodar `--headless --quit` após mexer em assets; testar cena isolada (F6) antes da fase inteira.
- Perguntar antes: mudar `project.godot` (renderer, física, input map); adicionar addon; mudar formato de save.
- Nunca: lógica em `_process` que pertence a `_physics_process`; `get_parent()` para jogo; editar `.godot/`.

## Mais

- Mecânicas e balanceamento: `docs/design.md`. Decisões: `docs/adr/`.
