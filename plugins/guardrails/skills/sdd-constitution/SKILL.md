---
name: sdd-constitution
description: SDD step 0 — constitution, spec index, parameters, REVIEW.md. Use when starting a project or changing principles. Not for one feature (skill sdd-specify).
argument-hint: "[product description and stack, or 'review']"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - exec
---

# SDD 0 — Constitution

Process: `references/sdd-process.md`. Parameters: `references/sdd-parameters.md`. Our pattern (SysML link names, DDD, Backstage for ENBs, SAFe): `references/pattern.md`. Templates: `../../templates/spec-index-business.md`, `../../templates/spec-index-game.md` and `../../templates/project-agents-*.md`.

## 1. Inspect before creating

Resolve the project profile first (`../session/references/project-profile.md`): `project`, `stacks`, `spec_root` (every `docs/spec` here) and `sdd`; a refused profile is fixed in § 4 before anything else.

Read the README, repository structure and stack manifests. If `AGENTS.md`, `REVIEW.md` or `docs/spec/` exists, review and propose a diff instead of overwriting it. Ask for missing product choices such as language, engine or database.

## 2. Write the project constitution

- Select the closest project template and replace placeholders only with verified versions, commands and paths.
- Keep repository `AGENTS.md` within 150 lines: Stack, Commands, Structure, condition→action Patterns, Always/Ask/Never boundaries, Sessions and pointers to detail. The path-rule blocks `sync-project.sh` generates in it do not count.
- Add one line to `AGENTS.md` naming the spec regimes: which `docs/spec` artifacts are spec-anchored (maintained) and that FEAT/task status is derived, never typed.
- Do not copy the kit's global rules or the `sdd-*` steps into the project: the project keeps its parameters, its own patterns and the exceptions it lists.

## 3. Initialize the spec

Create `docs/spec/spec.md` from the template `"$KIT/platforms/kits/sdd/init-spec.sh"` copies (the script, not this step, picks `spec-index-game.md`, `spec-index-tooling.md` or `spec-index-business.md` by the profile's `project.kind`) with a three-line vision, explicit out-of-scope and empty NEED/FEAT/REQ/DEC/DEBT indexes; the tooling one is a one-paragraph index with no NEED or REQ index. No template carries an `sdd:` block: the parameters live in `.ai-kit.yaml` (§ 4), and `check_spec.py` fails on a block left in `spec.md` (KIT-087 P4). Create `needs/` and `requirements/{functional,non-functional}/` (not under `sdd.flow: feat-only`), `features/`, `decisions/` and `debts/`, and `enablers/` when the product has bounded contexts or technical capabilities whose contracts other parts use (a business or game project; a tooling project, whose product is its own files, usually keeps none): the folder turns the enabler checks on. Decision ids are `DEC-nnn`; when the project numbers decisions per kind, declare the kinds once in `spec.md` (`decision_kinds: {tech: TEC, product: PRD}`) and `check_spec.py` enforces kind and prefix.

Declare the two regimes in `spec.md` (see `references/sdd-process.md`, Regimes): spec-anchored for contracts, decisions, requirements, journeys and the index; spec-first for NEED files, FEAT bodies and task tables.

- Vision sections: read `sdd.vision_sections` from `PROFILE resolve --section sdd` (`check_spec.py --params` leaves it out). Keep each optional section it lists (Pillars, Core loop, Direction, References), delete the others, and add any other heading it lists after References with one placeholder line. Fill them with product in the register `references/sdd-process.md` § Register gives, from facts and approved decisions only: three to five Pillars (`P1`…; product principles for a business project), each with what it rules out, so triage can cite one; a Core loop as actions and visible results; a Direction line per aspect with the mock or reference that holds it; References with what each gives and leaves.
- First-delivery scope is counted: each item carries a number (screens, roles, integrations, regions; for a game, maps, characters, items, quests). Out of scope: one line per refused or deferred area, with why and `never` or the milestone that reopens it, so `sdd-specify` can cite the line.
- Glossary: one row per domain term the product already uses (README, code folder and module names, legacy docs), one sentence each with its source. Process terms (NEED, REQ, FEAT) stay out: the kit defines them. `sdd-clarify` later adds every domain term a REQ uses.
- Architecture: the base architecture in one line, with the decision that records it (§ 6), and one row per area with its rooted paths and what it holds. Areas are the parts a change is counted against: `sdd-tasks` sizes a task row by the areas it touches, `sdd-plan` places the design in them. Take them from the repository's top folders and modules, not from a target layout. With `enablers/`, the table is the ENB index: one row per enabler, whose Area cell links its `enablers/ENB-nnn-slug.md` file, Paths holds its code paths and Holds its bounded context in one line, written from `../../templates/spec-enabler.md` (DDD context, aggregates citing REQ-F ids, events, provided and required contracts by kind, qualities citing REQ-NF ids, code; Backstage's `owner`, `system`, `domain`, `providesApis`, `consumesApis`, `dependsOn`), one ENB per bounded context the code already has. The ENB's Code section is the home of the paths; the row's Paths cell repeats them, and `sdd-tasks` sizes a row by the ENB it changes. A part outside every context (build, tooling) keeps a plain area row.

## 4. Set the process parameters

Write the `sdd` section of the project's `.ai-kit.yaml` at the git top level (with `project.kind` and `stacks`, if the file is new); `references/sdd-parameters.md` says what each key changes and which step reads it. Set a key only on a fact or a product choice: `tracker: none` when the project cuts no issues, `journeys: true` when it keeps journeys, `rule_paths` when its folders differ from the `stacks` folders, `protected_paths` for the paths its review gate labels; `review.rounds` and `evidence.visual_approval` are their own sections. Leave every other key out, so it takes its kind preset or default, and say so in one line. Then run `PROFILE resolve --section sdd` and read the resolved section back to product.

## 5. Write the review criteria

Copy the kit's `platforms/kits/github/REVIEW.md` to `REVIEW.md` at the repository root: the project's quality definition of done, read by every reviewer and by hosted Claude Code Review. Each criterion line ends with the rule, skill section or reference that holds it.

- Remove each line a project gate already enforces (CI job, hook, PR gate script, linter, spec validator), and name that gate under "Do not report", so a reviewer spends no finding on it.
- Add a project criterion only with the skill section or the project decision that holds its rule; a line with neither waits for one.
- Keep the five headings (Scope, Correctness, Architecture, Security, Docs), so findings group the same way in every project.

## 6. Record existing decisions

For an already-approved product decision, create one decision record (`DEC-nnn`, or the prefix of its kind when `docs/spec/spec.md` declares `decision_kinds`) with `status: approved` and its source. Unknown numeric targets remain hypotheses with a measurement method.

## 7. Validate

Run the project spec validator (`CHECK_SPEC`), `PROFILE resolve` (exit 0, no conflict), `SYNC --check <repo>` and one real build/test command. Mark only observed commands and versions as facts.

Done when: project principles change behavior, `spec.md` validates and `.ai-kit.yaml` resolves, the glossary, architecture areas, counted scope and each vision section `sdd.vision_sections` lists are filled, `REVIEW.md` has no line a gate enforces, required folders exist, and no version, command, path or target was invented.
