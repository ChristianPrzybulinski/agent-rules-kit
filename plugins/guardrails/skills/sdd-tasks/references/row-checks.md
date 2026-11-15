---
description: The checks every task row passes before its spec PR and the cut — size, scope, proof, contract and protected paths. Load when writing or reviewing task rows.
kind: detail
---

# Row checks

Each row passes every check below before its table goes to the spec PR; a row that fails one is fixed first, never inside the implementing PR. The project's `row_check` command, when set, automates what it can, and its exit 0 is required; the checks it does not cover stay the writer's.

## Size and order

- **One outcome.** One verifiable outcome, at most 5 areas, one proof, within `task_minutes`; a title needing “and also” is two rows.
- **Plan, not prose.** The Task cell points to `Plan § <section>` and never restates the Plan; `check_spec.py` warns above 1000 characters.
- **Explicit dependencies.** `Depends on` names every row whose merged output this row reads, and the longest chain of own rows is at most `max_chain`; `check_spec.py` fails a longer chain or a cycle.

## Scope (Files)

- **Tests in scope.** `Files` includes the test paths for any new code. A row that adds code without a test path is incomplete.
- **Cited paths.** Every path the Task or Proof cell cites is in `Files`, or is marked `(read-only)` there when the row only reads it.
- **Wiring.** A port, command or entry point that must work outside the tests (a CLI command, a server route, a dependency-injection binding, a registered scene or autoload) has its wiring file in `Files`.
- **Neighbour files.** A file the work needs outside the row (a config key, a shared CI workflow) joins `Files`, or the row names the row that owns it.
- **Build files.** `pom.xml`, `application.yml`, `project.godot` or the project's equivalents join `Files` when the row changes them.
- **Generated neighbours.** `*.uid`, `*.import`, `*.translation` and the project's equivalents of an owned file are implicit: they travel with their source and are never listed (the scope gate `pr_gates.py` admits them once the project's config lists them in `generated_neighbours`; its default is none).
- **Protected paths.** A `Files` path that matches a `protected_paths` entry gives the row's item that entry's label.

## Contract and policy

- **Cross-feature fields.** Every field the row reads from or writes to another FEAT's contract (message, schema, table) exists there with its value domain, and every command it sends has its success reply (`../../sdd-plan/references/contract.md` 1 and 2). A missing one goes back to the owning FEAT's Plan.
- **Regeneration and validators.** A contract change has one regeneration row per consumer, and a new message's producer row and its consumer's validator row share a wave (`contract.md` 3 and 4).
- **Value domains.** Every contract field or table column the row adds names its value domain and the public identifier of any entity it names.
- **Artifact policy.** A row that changes what a committed or generated artifact is (committed or ignored, regenerated or hand-edited, its format or location) cites the decision record that sets that policy.

## Proof

- **Executable proof.** Every proof line runs unattended in CI or the review gates as a deterministic command. A manual check (UI, mail capture) is labelled as such and paired with an automated one.
- **Proof wording.** A proof line contains none of the words the project's gates refuse; the item's `Notes` names the project's allowlist location, never a hard-coded list.

## Example

| Row | Fails | Fix |
|---|---|---|
| T3 `Add /trade route: Plan § Design`, Files `server/trade/TradeService.java` | Wiring: the route is registered in `server/http/Routes.java` | add `server/http/Routes.java` to Files |
| T4 Proof `python3 tools/check.py --file game/content/items.json` | Cited paths: `game/content/items.json` is not in Files | add it as `game/content/items.json (read-only)` |
| T5 Files `client/ui/bag.gd`, `client/ui/bag.gd.uid` | Generated neighbours are listed | drop `client/ui/bag.gd.uid` |
