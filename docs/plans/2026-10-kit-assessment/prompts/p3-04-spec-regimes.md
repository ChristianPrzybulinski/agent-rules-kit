# P3-04 — Two spec regimes: spec-anchored contracts, spec-first features

Phase: 3 · Repos: kit (agent-rules-kit), stratics-docs · Branch to create: docs/p3-04-spec-regimes from main (one branch per repo, same name) · Depends on: P2-08 (stratics-docs steps 6-9 only; kit steps 1-5 may run before it) · Effort: ~3 h

## Goal

Make the SDD process state which spec artifacts are maintained for the life of the product (spec-anchored: protocol schemas and examples, content schemas, decisions, requirements, journeys, the `spec.md` index) and which are written to cut the work and then frozen as history (spec-first: FEAT bodies and task tables, whose status is derived by tooling, never typed). The kit's `sdd-process.md` gains a `Regimes` section, `sdd-constitution` and the `spec-index.md` template tell every new project to declare the regimes, and the `spec-feature.md` template marks `status` and the task `State` column as derived. Stratics-docs declares the regimes in `docs/spec/spec.md` by an owner-approved PR. Measurable result: the kit no longer asks a session to keep 52 FEATs "alive"; after this change `grep -rl "spec-anchored" plugins/architect-sdd | wc -l` in the kit prints 3 and stratics-docs `docs/spec/spec.md` carries one regime statement that the owner approved.

## Why

- assessment §4.6: the Stratics spec has ~9.5k lines for ~3k lines of new code; task tables hold 128 `todo` rows and 3 `done` after ~35 merged implementation PRs; the PR template asks for "FEAT status updated" while `CONTRIBUTING.md` forbids editing `docs/spec/**`, so the status rule exists only to be violated.
- assessment §5.1 (SDD row): Böckeler/Thoughtworks (2025-10, 2026-02) distinguish spec-first (write and discard), spec-anchored (maintain) and spec-as-source; Spec Kit is criticized for a "sea of markdown, rigid gates" and OpenSpec positions itself as light; verdict for the kit: "excess: spec-anchored only for contracts (protocol, schemas, DECs); spec-first per task for the rest".
- assessment §6 item E0: adopt the two regimes so the obligation to maintain 52 FEATs disappears and effort concentrates where an error costs two teams (contracts between repos and people).
- kit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:43` describes one forward-moving status for every FEAT and says nothing about who moves it or which artifacts must stay current; the template `plugins/architect-sdd/templates/spec-feature.md:60` ships a `State` column with no owner.
- stratics-docs `docs/spec/spec.md:13` still says "No development has started" and `:62` says the in-progress FEAT is "none yet" with 35 implementation PRs merged (P2-08 fixes the numbers; this prompt fixes the rule that let them rot).
- stratics-docs `docs/spec/traceability.md:3-4` already applies the pattern for reverse views ("Never edit it by hand: `spec_trace.py check` fails when it is stale"); the regime statement generalizes it.

## Current state

Line numbers and quotes are main at 2026-10-06, before P1-08/P2-08; after them anchor on the quoted text, expect the ten-column task header in `spec-feature.md` and the sync-status marker block plus a DPRO-014 row in `spec.md`.

kit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` (58 lines; the validator caps references at 60 lines including frontmatter, `platforms/ci/validations/check_kit.py:27` and `:633`):

```
plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:10: ## Entry points
plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:12: - Vague idea → `/grilling` first, then `sdd-specify` when problem/value is describable.
plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:13: - Described feature → `sdd-specify`; new project/principles → `sdd-constitution`.
plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:39: ## Identifiers and status
plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:43: Feature status moves forward: `proposed → clarified → planned → in-progress → validated → delivered` (or `cancelled`). `delivered` means merged to `main` with no flag or the flag on.
plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:47: ## Project layout
```

kit `plugins/architect-sdd/skills/sdd-constitution/SKILL.md` (42 lines; cap 80):

```
plugins/architect-sdd/skills/sdd-constitution/SKILL.md:27: - Keep repository `AGENTS.md` within 150 lines: Stack, Commands, Structure, condition→action Patterns, Always/Ask/Never boundaries, Sessions and pointers to detail.
plugins/architect-sdd/skills/sdd-constitution/SKILL.md:32: Create `docs/spec/spec.md` with a three-line vision, explicit out-of-scope, glossary and empty FEAT/REQ/DEC/DEBT indexes. Create `features/`, `requirements/{functional,non-functional}/`, `decisions/` and `debts/`.
```

kit `plugins/architect-sdd/templates/spec-index.md` (63 lines; copied verbatim to `docs/spec/spec.md` by `platforms/kits/sdd/init-spec.sh:19`):

```
plugins/architect-sdd/templates/spec-index.md:11: Cover and index. The source of truth for each subject lives in the linked files; here only vision, scope and indexes. Classify claims: `[FACT]` `[DECISION]` `[PROPOSAL]` `[HYPOTHESIS]` `[BLOCKER]`.
plugins/architect-sdd/templates/spec-index.md:36: 4. The `FEAT` in progress (status `in-progress`)
```

kit `plugins/architect-sdd/templates/spec-feature.md` (68 lines):

```
plugins/architect-sdd/templates/spec-feature.md:4: status: proposed
plugins/architect-sdd/templates/spec-feature.md:58: <!-- filled by sdd-tasks -->
plugins/architect-sdd/templates/spec-feature.md:60: | ID | Task | Files | Proof of completion | Covers | Depends on | State |
```

stratics-docs `docs/spec/spec.md` (242 lines; frontmatter schema `.github/spec-lint/schemas/spec.schema.json` has `additionalProperties: false`, so no new frontmatter key):

```
docs/spec/spec.md:6: updated: "2026-10-05"
docs/spec/spec.md:56: ## Reading order for a new session
docs/spec/spec.md:64: ## Indexes
docs/spec/spec.md:167: Player-visible flows (DPRO-013). Each step cites rule ids, tasks and tests; the reverse views (rule → journeys → tests, task → journeys) are generated into traceability.md (markdown link to `traceability.md`) by `tools/spec-trace/spec_trace.py` — never edited by hand.
docs/spec/spec.md:206: | DPRO-013 (link to `decisions/DPRO-013-journey-layer.md`) | Journey layer: J-NN journeys cite rule ids, tasks and tests; rules promoted to REQ-F; reverse views generated | process | approved | 2026-10-05 |
```

stratics-docs `docs/spec/decisions/`: DPRO-001..013 exist on main today (`ls docs/spec/decisions/DPRO-*`); P2-08 adds `DPRO-014-derived-status.md`, so after P2-08 the next free process id is DPRO-015. Always compute it as highest `ls docs/spec/decisions/DPRO-*` + 1 (ids are never reused, `sdd-process.md:41`). New file, only if the owner asks for a decision: `docs/spec/decisions/DPRO-<next>-spec-regimes.md` (new file), listed in the Decisions table of `docs/spec/spec.md`.

## Change

Kit (branch docs/p3-04-spec-regimes in agent-rules-kit):

1. Edit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md`. Free four lines first: delete the `## Entry points` section (lines 10-14 on main: heading, blank, two bullets, blank) and add this one line immediately after the paragraph line that starts `Repeat `implement`` (after P1-08 it ends "before merge."), with no blank line between them so it joins that paragraph (58 - 5 + 1 + 6 = 60 lines on main; the target is 60 or fewer, not exactly 60): `Entry: vague idea → `/grilling` then `sdd-specify`; described feature → `sdd-specify`; new project or principles → `sdd-constitution`.` If P3-05 is already merged, keep its lane in that folded line as `; feel question → `sdd-spike``. Then insert, before `## Project layout`, this section verbatim, followed by one blank line (6 lines in total; drop that trailing blank line if the file would exceed 60; if it still exceeds 60, remove the blank line between `## Regimes` and its intro line (CommonMark allows a heading followed directly by a paragraph); never remove a bullet):

```
## Regimes

Two regimes, after Böckeler/Thoughtworks (2025-10: spec-first, spec-anchored, spec-as-source; the kit has no spec-as-source):
- spec-anchored: maintained and validated for the life of the product: `protocol/` schemas and examples, content schemas, decisions (DTEC/DGME/DPRO), requirements (REQ-F/REQ-NF), journeys (where the project has them) and the `spec.md` index. Every change is a reviewed PR.
- spec-first: FEAT bodies and task tables. Written to cut the work, frozen as history once delivered; FEAT `status` and task `State` are derived by tooling from GitHub, never edited by hand.
```

   Change the line starting `Feature status moves forward` to end with: `... (or `cancelled`). From `in-progress` on the value is derived (see Regimes). `delivered` means merged to `main` with no flag or the flag on.` Keep the file at 60 lines or fewer, frontmatter included; keep `kind: detail` (no `verified`/`sources` needed).

2. Edit `plugins/architect-sdd/skills/sdd-constitution/SKILL.md`: after line 27 add the bullet `- Add one line to `AGENTS.md` naming the spec regimes: which `docs/spec` artifacts are spec-anchored (maintained) and that FEAT/task status is derived, never typed.`; after the `Create docs/spec/spec.md ...` paragraph add the paragraph `Declare the two regimes in `spec.md` (see `references/sdd-process.md`, Regimes): spec-anchored for contracts, decisions, requirements, journeys and the index; spec-first for FEAT bodies and task tables.` The description in frontmatter and in `plugins/architect-sdd/INDEX.md` stay unchanged.

3. Edit `plugins/architect-sdd/templates/spec-index.md`: after line 11 insert a blank line and these two lines verbatim:

```
Regimes: spec-anchored (maintained and validated for the life of the product) = protocol schemas and examples, content schemas, decisions, requirements, journeys (where the project has them) and this index.
Spec-first (written to cut the work, then frozen as history) = FEAT bodies and task tables; their status is derived by tooling from merged PRs, never edited by hand.
```

   Change line 36 to `4. The `FEAT` in progress (status `in-progress`, derived)`.

4. Edit `plugins/architect-sdd/templates/spec-feature.md`: do not put a `#` comment inside the frontmatter (the validator's fallback parser `platforms/ci/validations/check_kit.py:90 mini_yaml` keeps `# ...` inside the value when PyYAML is absent). Instead insert, right after the closing `---` on line 15, the line `<!-- status: proposed, clarified and planned are set by the SDD steps; in-progress, validated and delivered are derived from GitHub by tooling. Never edit status by hand. -->`, and replace line 58 with `<!-- filled by sdd-tasks; State is derived from the task issue (merged PR = done) and never edited by hand -->`. Schemas under `platforms/ci/schemas/` stay unchanged.

5. `CHANGELOG.md`: add under `## [Unreleased]` / `### Changed` one bullet: what (Regimes section, two template notes, derived-status comments), why (assessment §4.6 and §6 E0: 128 `todo` rows after 35 merged PRs; nobody may edit status), proof (the four gate commands with their final lines).

Stratics-docs (branch docs/p3-04-spec-regimes in stratics-docs). Steps 6-9 run in the architect (Claude) session or by the owner: `docs/spec/**` is not Devin-editable (`CONTRIBUTING.md:168`). A Devin executor does the kit half only and reports the stratics-docs half as a blocker in `next step`.

6. Edit `docs/spec/spec.md`: insert a new section between `## Reading order for a new session` and `## Indexes`, immediately before the `## Indexes` heading, separated by one blank line on each side (line 64 on main today; later if P2-08's sync-status marker block is present; never split that marker block):

```
## Regimes

[PROPOSAL] Regimes: spec-anchored (maintained and validated for the life of the product): `../../protocol/` schemas and examples, `../../content/schema/`, `decisions/`, `requirements/`, `journeys/` and this index; spec-first (written to cut the work, then frozen as history): FEAT bodies and task tables under `features/`; their `status` and task rows are derived from merged PRs by `tools/spec-trace/spec_trace.py sync-status` (DPRO-014), never edited by hand. Approved DECs are never edited; a change is a new DEC that supersedes.
```

   Set `updated:` (line 6) to the PR date. Keep the claim tag `[PROPOSAL]`; the owner changes it to `[DECISION]` in review or asks for a decision record.
7. Only if the owner asks for a decision: compute `<nnn>` as highest `ls docs/spec/decisions/DPRO-*` + 1 (DPRO-015 after P2-08), then create `docs/spec/decisions/DPRO-<nnn>-spec-regimes.md` (new file) from the kit template `plugins/architect-sdd/templates/spec-decision.md` with `id: DPRO-<nnn>`, `kind: process`, `status: proposed`, `deciders: "product"`, `features: []`; add a Decisions row to `docs/spec/spec.md` after the last DPRO row of the Decisions table (not at a fixed line number) whose first cell is the id linked to `decisions/DPRO-<nnn>-spec-regimes.md` (same markdown link form as the DPRO-013 row), then the title `Two spec regimes: spec-anchored contracts, spec-first features`, `process`, `proposed`, `<date>`. Do not set `approved` yourself.
8. Add `changelog.d/p3-04-spec-regimes.changed.md` (new file; branch slug as id per `changelog.d/README.md:7-9`) with one line: `- [PROPOSAL] docs/spec/spec.md: Regimes section; spec-anchored (protocol, content schemas, DECs, REQs, journeys, index) vs spec-first (FEAT bodies, task tables, status derived by tooling).`
9. Open the PR with the repo template (What / Why / How I tested / Proof / Checklist); in `Proof` use only commands whose first word is in `ops/review-loop/config.json` `proof_allowlist` (`python3`, `grep`, `test`, ...). Request the owner's review.

## Out of scope

- Deriving status from GitHub, rewriting FEAT frontmatter, `spec.md:13` and `:62` prose, and the PR checklist line "FEAT status updated" (P2-08).
- `sdd-implement/SKILL.md:22` and `:43` are replaced by P1-08 step 8 (§1 and §4); P2-08 does not touch the kit (p2-08-derived-spec-status.md:130). Residual after P1-08: `sdd-implement` says `mark `done` when the PR merges` and `sdd-tasks/SKILL.md:38` lists hand states (`todo`, `doing`, `done`, `blocked`); this prompt leaves them and names them in `next step` as the last hand-typed status in the kit.
- Merging `sdd-analyze` and `sdd-audit` (P3-06); the spike lane (P3-05); stale kit paths in stratics-docs (P1-02).
- Other edits of `sdd-process.md`: P1-08 (line 24, step rows 7/9), P3-06 (steps 3-4, renumbering), P3-05 (`sdd-spike` entry), P3-10 (precedence sentence on the status line). Whichever lands second re-anchors on the quoted text; this prompt keeps a merged P3-05 lane in the folded Entry line (step 1).
- Editing any approved DEC (DPRO-009 included), the journeys, `traceability.md`, the spec-lint schemas or `spec_trace.py`.
- The kit `VERSION` file, plugin descriptions and the 10.x layout.

## Acceptance criteria

- [ ] kit: `wc -l plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` prints 60 or less; `grep -c "^## Regimes" plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` prints 1; `grep -c "Entry points" plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` prints 0.
- [ ] kit: `grep -l "spec-anchored" plugins/architect-sdd/skills/sdd-constitution/SKILL.md plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md plugins/architect-sdd/templates/spec-index.md` lists all 3 files; `grep -c "derived" plugins/architect-sdd/templates/spec-feature.md` prints 2; `grep -c "^#" plugins/architect-sdd/templates/spec-feature.md` is unchanged versus main (no comment inside the frontmatter).
- [ ] kit: `wc -l plugins/architect-sdd/skills/sdd-constitution/SKILL.md` prints 80 or less; `git diff main -- plugins/architect-sdd/INDEX.md platforms/ci/schemas VERSION` is empty.
- [ ] kit: `platforms/tools/check.sh` ends with the OK summary; `platforms/tools/smoke.sh` exits 0; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` prints `OK`; `python3 platforms/ci/validations/check_kit.py --links` prints no `FAIL:` line naming a file this PR touches (if it exits non-zero only on other `docs/plans` prompts, paste those lines under `unverified`).
- [ ] kit: `sed -n '/^## \[Unreleased\]/,/^## \[1/p' CHANGELOG.md | grep -c "Regimes"` prints at least 1; `python3 platforms/ci/validations/check_kit.py` prints no `FAIL:` line naming a file this PR touches.
- [ ] stratics-docs: `grep -c "^## Regimes" docs/spec/spec.md` prints 1; `grep -ci "spec-anchored" docs/spec/spec.md` prints 1, or 2 if step 7 ran (the Regimes paragraph plus the DPRO-<nnn> row title); `python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas` exits 0; `python3 tools/spec-trace/spec_trace.py check` exits 0.
- [ ] stratics-docs: `test -f changelog.d/p3-04-spec-regimes.changed.md` exits 0; `git diff main --stat -- docs/spec/decisions docs/spec/journeys docs/spec/traceability.md` is empty unless step 7 ran, in which case it lists only `DPRO-<nnn>-spec-regimes.md` with `status: proposed`.
- [ ] stratics-docs: the PR body has What, Why, How I tested with pasted output, a `proof` block and the checklist; the owner is the reviewer.

## Conventions

- Everything committed is in English; plain ASCII punctuation in new text, except `→` in `sdd-process.md`, kept because the existing Entry points and status line already use it.
- No layout or path change: `plugins/`, `platforms/`, `docs/` and the templates keep their paths; template names keep matching `^(spec|doc|project|kit)-[a-z0-9-]+\.md$`.
- `VERSION` untouched; `CHANGELOG.md` gets a `## [Unreleased]` entry with what, why and proof.
- `plugins/architect-sdd/INDEX.md` lists the skill `sdd-constitution` and the two templates; references are not listed (the validator requires only skills and templates there); it changes only if a file is added (none planned).
- Skill description unchanged (40-160 chars, "Use when ... Not for ..."), so the 7,200-char budget (6,803 today) is untouched; `SKILL.md` 80 lines or fewer; the reference 60 lines or fewer with frontmatter `kind: detail`.
- `sdd-constitution` stays user-only: `triggers: [user]`, `disable-model-invocation: true`, `agents/openai.yaml` with `policy.allow_implicit_invocation: false`; do not touch them.
- Conventional Commits with `Refs: P3-04` (kit) and `Refs: DPRO-009, P2-08` (stratics-docs); PR body = What / Why / How I tested (literal output) / Refs; stratics-docs adds the `Proof` block and the `changelog.d` fragment, never a direct `CHANGELOG.md` edit (DPRO-011).
- Gates, kit: `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`. Gates, stratics-docs: `python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas`; `python3 tools/spec-trace/spec_trace.py check`.
- Source to cite in the kit text: Böckeler, "Understanding Spec-Driven Development" (martinfowler.com, 2025-10) for the three-level taxonomy; verify the exact title and URL against martinfowler.com before relying on it, and do not add a URL you did not open. If martinfowler.com cannot be opened (it is egress-blocked for some agent environments, assessment §9.3), keep the attribution exactly as assessment §5.1 states it (Böckeler/Thoughtworks, 2025-10), add no URL, and list the source under `unverified`.

## Report back

Final message in three blocks: `done` (every path created or edited per repo, plus each gate command with its literal last lines and the PR URLs), `unverified` (anything not run, for example the owner's choice between `[DECISION]` and a DPRO-<nnn> record, or a source you could not open), `next step` (what P2-08 or the owner must do before the regimes are enforced, and the last hand-typed status left in the kit: `mark `done` when the PR merges` in `sdd-implement` after P1-08 and the `States:` line in `sdd-tasks/SKILL.md`). End with the proposed one-line CHANGELOG entry, for example: `- SDD: two spec regimes (spec-anchored contracts, decisions, requirements, journeys, index; spec-first FEAT bodies and task tables with derived status) in sdd-process.md, sdd-constitution and the spec-index/spec-feature templates. Evidence: assessment §4.6, §6 E0; 128 todo rows after 35 merged PRs in stratics-docs.`
