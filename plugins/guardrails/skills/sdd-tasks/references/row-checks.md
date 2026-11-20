---
description: The checks every task row passes before its spec PR and the cut — size, scope, proof, contract and protected paths. Load when writing or reviewing task rows.
kind: detail
---

# Row checks

Each row passes every check below before its table goes to the spec PR; a row that fails one is fixed first, never inside the implementing PR. The row-check command automates what it can, and its exit 0 is required; the checks it does not cover stay the writer's. With `row_check: null` that command is the kit's `ROWS check FEAT-nnn` (`../../session/references/project-profile.md` § 3; or `--all`, `--changed BASE HEAD`; § Automated rules): it reads the profile's `sdd` section (`PROFILE resolve --section sdd` shows it), checks the rows that are not settled (`--all-rows`: every row) and exits 1 on a FAIL (`--strict` makes the c, f, l and m warnings fail), 2 on a config it cannot use or on an internal error. A project command replaces it.

## Size and order

- **One outcome.** One verifiable outcome, at most 5 areas, one proof, within `task_minutes`; a title needing “and also” is two rows.
- **Plan, not prose.** The Task cell points to `Plan § <section>` and never restates the Plan; `check_spec.py` warns above 1000 characters.
- **Explicit dependencies.** `Depends on` names every row whose merged output this row reads, and the longest chain of own rows is at most `max_chain`; `check_spec.py` fails a longer chain or a cycle.

## Scope (Files)

- **Tests in scope.** `Files` includes the test paths for any new code. A row that adds code without a test path is incomplete.
- **Cited paths.** Every path the Task or Proof cell cites is in `Files`, or is marked `(read-only)` there when the row only reads it.
- **Wiring.** A port, command or entry point that must work outside the tests (a CLI command, a server route, a dependency-injection binding, a registered scene or autoload) has its wiring file in `Files`.
- **Neighbour and build files.** A file the work needs outside the row (a config key, a shared CI workflow) joins `Files`, or the row names the row that owns it; so do `pom.xml`, `application.yml`, `project.godot` or the project's equivalents when the row changes them.
- **Generated neighbours.** `*.uid`, `*.import`, `*.translation` and the project's equivalents of an owned file are implicit: they travel with their source and are never listed (the scope gate `pr_gates.py` admits them once the project's config lists them in `generated_neighbours`; its default is none).
- **Protected paths.** A `Files` path that matches a `protected_paths` entry gives the row's item that entry's label.

## Contract and policy

- **Cross-feature fields.** Every field the row reads from or writes to another FEAT's contract (message, schema, table) exists there with its value domain, and every command it sends has its success reply (`../../sdd-plan/references/contract.md` 1 and 2). A missing one goes back to the owning FEAT's Plan.
- **Regeneration and validators.** A contract change has one regeneration row per consumer, and a new message's producer row and its consumer's validator row share a wave (`contract.md` 3 and 4).
- **Value domains.** Every contract field or table column the row adds names its value domain and the public identifier of any entity it names.
- **Artifact policy.** A row that changes what a committed or generated artifact is (committed or ignored, regenerated or hand-edited, its format or location) cites the decision record that sets that policy.

## Proof

- **Executable proof.** Every proof line runs unattended in CI or the review gates as a deterministic command. A manual check (UI, mail capture) is labelled as such and paired with an automated one.
- **Proof wording.** A proof line contains none of the words the project's gates refuse; the item's `Notes` names the project's allowlist location, never a hard-coded list. Under a component (rule e) it also holds no `..` path step (any `..` but a revision range `A..B` between letters or digits, quoted or not), no shell expansion outside a leading `$NAME`, `${NAME}` or `~/` anchor (a `$`, `~`, `{…}` other than `{}`, or a glob in a name that starts with `.`), and no interpreter given inline code (`python3 -c`, `sh -c`, `node -e`, `perl -e`, `ruby -e`, `env -S`). These rules are hygiene, not isolation: an allowlisted program, an absolute path or an anchored one still reads outside the component; only a sandbox that runs the line could stop that.

## Automated rules

| Rule | Level | Checks | Reads |
|---|---|---|---|
| a | FAIL | the KIT-068 columns and their values; a malformed row skips the rest | — |
| b | FAIL | each Files entry starts at a top-level path or a component name, and the row stays in one component (a contract row that owns the protocol folder only warns) | `components` |
| c | FAIL (WARN for a stack with `level: warn`) | a code path needs a test path of its stack | `row_checks.tests` |
| d | WARN | a listed generated neighbour; an exact asset path where a `**` glob of its folder belongs | gates `generated_neighbours`, `row_checks.assets` |
| e | FAIL (WARN for a manual clause with no automated sibling, or no command at all) | each proof clause runs allowlisted programs only, under the component rules of § Proof (`pr_gates.py` `command_allowed`, the PR gate's own code); a Proof of `evidence:` clauses only fails unless `row_checks.evidence_only` is `true` | gates `proof_allowlist`; `components`; `row_checks.evidence_only` |
| f | WARN | each Depends on token is `—`, a row of the table, `FEAT-nnn Tn` on disk or `#N` | — |
| g | FAIL | each path a proof clause names is in Files of the row or of a same-FEAT dependency | — |
| h | WARN | each message type the Task sends has its schema | `row_checks.protocol.schemas` |
| i | WARN | a row that changes an artifact's policy cites the decision that sets it | `row_checks.artifacts` (JSON list of `{pattern, dec, policy}`) |
| j | WARN | a row with Files on a visual path has one ``evidence: screen `<id>` [states `<s>`, …]`` or ``evidence: motion `<id>` `` clause per capture; each parses, and its catalog file is on `origin/main` or in Files; a greybox block's row is exempt (KIT-094) | `visual_approval` `owner` or `reviewer`, `row_checks.visual`, `passes` |
| k | WARN | a contract row has, per consumer, an open row that depends on it and covers that consumer's tables | `row_checks.protocol.consumers` |
| l, m | WARN | l: four or more open rows share one title shape (a set cut per item), reported once on the first; m: a row of such a set depends on another row of it (KIT-115) | — |

## Example

| Row | Fails | Fix |
|---|---|---|
| T3 `Add /trade route: Plan § Design`, Files `server/trade/TradeService.java` | Wiring: the route is registered in `server/http/Routes.java` | add `server/http/Routes.java` to Files |
| T4 Proof `python3 tools/check.py --file game/content/items.json` | Cited paths: `game/content/items.json` is not in Files | add it as `game/content/items.json (read-only)` |
| T5 Files `client/ui/bag.gd`, `client/ui/bag.gd.uid` | Generated neighbours are listed | drop `client/ui/bag.gd.uid` |
