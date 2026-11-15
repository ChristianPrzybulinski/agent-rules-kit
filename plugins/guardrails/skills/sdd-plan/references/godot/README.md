# Godot design references

Facts and rules `sdd-plan` reads when a delivery touches an online Godot 2D client: who decides state, how the client talks to the server and what the frame may cost. The always/never for `*.gd`, `*.tscn` and `project.godot` is rule `godot.md`; coding detail (GDScript pitfalls, generated files, scene-free tests, versions) is skill `sdd-implement`, reference `godot/README.md`.

## How to use

1. Plan § Design: read `authority-and-prediction.md` before placing any rule on the client.
2. Plan § Contract: read `networking-transports.md` for a transport decision and `network-codec.md` for the envelope codec.
3. Plan § Risks or § Observability: read `performance-budget.md` and name the budget numbers.

## Contents

| File | Scope |
|---|---|
| [`authority-and-prediction.md`](authority-and-prediction.md) | server authority, one-step prediction, event queue, `@rpc` rules |
| [`networking-transports.md`](networking-transports.md) | TCP, WebSocket, ENet, UDP and HTTP facts for a transport decision |
| [`network-codec.md`](network-codec.md) | JSON envelope over `WebSocketPeer`: validate then dispatch, heartbeat, reconnect, fixtures |
| [`performance-budget.md`](performance-budget.md) | project-set frame, node and memory budgets and measure-first rules |
