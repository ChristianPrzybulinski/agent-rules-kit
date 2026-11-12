---
description: Server authority and one-step client prediction rules for an online 2D Godot client, plus @rpc rules when the project uses MultiplayerAPI.
kind: fact
verified: "2026-10-06"
sources:
  - https://docs.godotengine.org/en/stable/tutorials/networking/high_level_multiplayer.html
  - https://docs.godotengine.org/en/stable/classes/class_multiplayerapi.html
---

# Godot 4 - server authority and prediction

- The server decides every state effect: movement, collision, turn order, inventory, economy. The client sends intent and renders confirmed state. Animations never decide outcome.
- Rule: a client feature or task contains no outcome rule; if a rule is needed on the client for feel, it is a prediction and must be reconciled against the server's answer.

## Prediction

- Predict at most one step ahead of the last confirmed state; anything beyond that is visual interpolation toward confirmed data.
- On rejection: snap back to the last confirmed state and drop every queued intent that was never confirmed.
- Confirmed coordinates are never changed by presentation: no tween, lerp or camera writes them.
- Parameter: `movement model` is a project decision recorded in the project `AGENTS.md` or DEC - physics `CharacterBody2D` or tile step, never both (the owning wording lives in SKILL.md section 3). The one-step rule reads the same under either model: a physics body applies one input ahead of confirmation, a tile entity predicts one tile step per intent.

## Event queue

- Server events are consumed in order by a single consumer; a repeated, late or canceled animation never changes outcome.
- The queue is a pure class testable without a scene - see `./testable-game-logic.md`.

## If the project uses MultiplayerAPI

- `@rpc` defaults to `"authority"`, so calls from a non-authority peer are dropped silently; use `"any_peer"` plus validation on the server (RPCMode in class_multiplayerapi).
- Node paths and names must be identical on every peer; never pass Objects or Callables in an RPC.
- Every new `@rpc` needs a server-side validation test.
