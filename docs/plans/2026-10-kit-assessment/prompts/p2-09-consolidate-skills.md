# P2-09 — Consolidate overlapping skills (code-standards, architecture, session)

Phase: 2 · Repos: kit (agent-rules-kit) · Branch to create: feat/p2-09-consolidate-skills from main · Depends on: P2-03 (the two `plugins/core/AGENTS.md` pointer lines are edited after P2-03 has reordered the file) · Effort: ~4 h

## Goal

Replace seven overlapping skills by three: `plugins/dev-core/skills/clean-code` + `simplicity` become `plugins/dev-core/skills/code-standards`; `plugins/architect-core/skills/clean-architecture` + `ddd-and-patterns` become `plugins/architect-core/skills/architecture`; `plugins/core/skills/sessions` + `session-review` + `session-handoff` become `plugins/core/skills/session` (argument `start | review | handoff <topic>`). Every pointer to an old name is updated, nothing else in the kit changes. Measurable result: 43 skills become 39, 31 model-invocable become 28, the description budget drops from 6,803 to about 6,210 characters, `grep` for the seven old names outside `CHANGELOG.md` and `docs/plans/` prints 0 lines, and all four kit gates stay green.

## Why

- assessment §4.7: 31 of 43 skills are model-invocable; `clean-code`, `simplicity`, `testing`, `clean-architecture` and `ddd-and-patterns` "cover the same 'write good code' territory" and `godot-standards`/`java-standards` reference them in a chain; probable result: the right skill does not load, or three load with redundant advice.
- assessment §6 F1 (the authoritative shape of this change): `clean-code` + `simplicity` -> `code-standards`; `clean-architecture` + `ddd-and-patterns` -> `architecture`; `sessions` + `session-review` + `session-handoff` -> `session` with `/session handoff`. Reason given there: Devin Cloud activates one skill at a time and Claude picks among the descriptions; overlap reduces the hit rate. Verify the Devin claim against docs.devin.ai product-guides/skills before quoting it in the CHANGELOG.
- assessment §5 (Skills row): the format is right (body <= 80 lines, descriptions <= 160) but the number of model-invocable skills is the excess.
- Measured on v10.1.0 (`python3` over `plugins/*/skills/*/SKILL.md`): 43 skills, 31 without `disable-model-invocation: true`, 6,803 description characters; the seven skills to merge carry 1,064 of them (154, 157, 149, 148, 148, 149, 159).
- The pairs already point at each other as the "Not for" neighbour, proof that they are one topic split in two: `plugins/architect-core/skills/clean-architecture/SKILL.md:3` ends `Not for pattern choice (skill ddd-and-patterns).` and `ddd-and-patterns/SKILL.md:3` ends `Not for layer placement (skill clean-architecture).`; `sessions/SKILL.md:3`, `session-review/SKILL.md:3` and `session-handoff/SKILL.md:3` each name one of the other two.
- The merged bodies exceed 80 lines (47 + 53, 48 + 53, 44 + 61 + 38), so the tables and procedures that are read only at one step move to `references/` (`check_kit.py:26` `SKILL_MAX_LINES = 80`, `:27` `REFERENCE_MAX_LINES = 60`).

## Current state

Skills to merge (kit, v10.1.0), each a single `SKILL.md` except `session-handoff`, which also has `agents/openai.yaml`:

```
plugins/dev-core/skills/clean-code/SKILL.md:3:description: Code rules for names, functions and comments. Use when naming, editing functions, writing comments or reviewing code. Not for test policy (skill testing).
plugins/dev-core/skills/simplicity/SKILL.md:3:description: YAGNI ladder for the smallest change. Use when choosing a dependency, reviewing an oversized PR or adding an abstraction. Not for test gates (skill testing).
plugins/architect-core/skills/clean-architecture/SKILL.md:3:description: Clean Architecture layer and port placement. Use when defining layers, ports or where a class lives. Not for pattern choice (skill ddd-and-patterns).
plugins/architect-core/skills/ddd-and-patterns/SKILL.md:3:description: Tactical DDD and pattern selection. Use when defining an aggregate or choosing a design pattern. Not for layer placement (skill clean-architecture).
plugins/core/skills/sessions/SKILL.md:3:description: Session scope and hygiene. Use when starting, changing topics or detecting a long session. Not for recording completed work (skill session-handoff).
plugins/core/skills/session-review/SKILL.md:3:description: Session closeout with evidence and one kit proposal. Use when work is delivered or a session closes. Not for handoff records (skill session-handoff).
plugins/core/skills/session-handoff/SKILL.md:3:description: Session handoff record with evidence and next action. Use when switching agent/session or leaving pending work. Not for session summary (skill session-review).
plugins/core/skills/session-handoff/SKILL.md:5-7:triggers:\n  - user\ndisable-model-invocation: true
plugins/core/skills/session-handoff/SKILL.md:18:Use `../../templates/doc-session-handoff.md`; the record must let a new session continue without this conversation.
plugins/core/skills/session-handoff/agents/openai.yaml:1-2:policy:\n  allow_implicit_invocation: false
```

Pointers that name the old skills (re-derive line numbers with `grep -n` before editing; P2-03 reorders `AGENTS.md` and P2-02 rewrites the two rule bodies):

```
plugins/core/AGENTS.md:23:- End: summary (done · unverified · next step) + at most **one** kit proposal with evidence from this session, asked before written. Detail: skills `sessions`, `session-review`, `session-handoff`.
plugins/core/AGENTS.md:35:- Standards are skills: `clean-code`, `clean-architecture`, `simplicity`, `ddd-and-patterns`, `testing`, `branching-and-versioning`, `update-docs`, `git-lfs`. Load the one the task touches; `rules/` loads the Java and Godot sets by file glob.
plugins/dev-godot/rules/godot.md:2:description: Load Godot 2D standards, Clean Code, and testing guidance for Godot project files.
plugins/dev-godot/rules/godot.md:14:Load skill `godot-standards`; it points to `clean-code` and `testing`.
plugins/dev-java/rules/java.md:2:description: Load Java standards, Clean Code, and testing guidance for Java and Maven files.
plugins/dev-java/rules/java.md:12:Load skill `java-standards`; it points to `clean-code` and `testing`.
plugins/dev-godot/skills/godot-standards/SKILL.md:17:Names and functions: read skill `clean-code`. Test gates and coverage: read skill `testing`.
plugins/dev-java/skills/java-standards/SKILL.md:17:Names and functions: read skill `clean-code`. Test gates and coverage: read skill `testing`.
plugins/core/INDEX.md:9-11:| `session-handoff` | ... |  | `session-review` | ... |  | `sessions` | ... |
plugins/dev-core/INDEX.md:8:| `clean-code` | ... |      plugins/dev-core/INDEX.md:11:| `simplicity` | ... |
plugins/architect-core/INDEX.md:7-8:| `clean-architecture` | ... |  | `ddd-and-patterns` | ... |
INDEX.md:24:| [`plugins/dev-core/`](plugins/dev-core/INDEX.md) | `core` | code patterns: clean code, simplicity, testing, docs, investigation |
INDEX.md:40:| [`plugins/dev-java/rules/java.md`](plugins/dev-java/rules/java.md) | `glob` | `**/*.java`, `**/pom.xml` | `java-standards`, `clean-code`, `testing` |
INDEX.md:41:| [`plugins/dev-godot/rules/godot.md`](plugins/dev-godot/rules/godot.md) | `glob` | `**/*.gd`, `**/*.tscn`, `**/project.godot` | `godot-standards`, `clean-code`, `testing` |
plugins/dev-core/plugin.json:5:  "description": "ai-kit dev patterns: clean code, simplicity, testing, docs and investigation skills"
```

The same description string sits at `plugins/dev-core/.claude-plugin/plugin.json:4`, `plugins/dev-core/.devin-plugin/plugin.json:4` and `.claude-plugin/marketplace.json:23`. `platforms/tools/`, `README.md`, `docs/maintenance.md` and `docs/projects.md` name none of the seven skills (`docs/projects.md:11` and `plugins/core/INDEX.md:23` name the template `doc-session-handoff.md`, which stays). The stratics repos' `AGENTS.md` files name none of them.

Gates that define the constraints (do not edit): `check_kit.py:24` `DESCRIPTION_MAX = 160`, `:25` `DESCRIPTIONS_BUDGET = 7200`, `:614-616` user-only parity (`triggers: [user]`, Codex policy `allow_implicit_invocation: false` and `disable-model-invocation: true` must all agree, so a model-invocable skill may not ship an `agents/openai.yaml` that disables implicit invocation), `:624-637` every `references/*.md` needs frontmatter per `platforms/ci/schemas/reference.schema.json`, <= 60 lines, and its file name must appear in the owning `SKILL.md`; `:787-792` each plugin `INDEX.md` row `| \`<skill>\` | <description> |` must equal the frontmatter verbatim. New files: `plugins/dev-core/skills/code-standards/SKILL.md`, `.../code-standards/references/yagni-ladder.md`, `plugins/architect-core/skills/architecture/SKILL.md`, `.../architecture/references/pattern-catalog.md`, `plugins/core/skills/session/SKILL.md`, `.../session/references/kit-proposal.md`, `.../session/references/handoff-record.md` (all new files; the skills are listed in their plugin `INDEX.md`, references are reached from `SKILL.md` and are not listed in any index).

## Change

1. Confirm P2-03 is merged: `git log --oneline main -- plugins/core/AGENTS.md` shows its commit and `grep -n '^## Boundaries' plugins/core/AGENTS.md` prints a line number below `## Truth`. If not, stop and report.
2. Create `plugins/dev-core/skills/code-standards/SKILL.md` (kit, new file) from `clean-code` and `simplicity`, <= 80 lines, frontmatter exactly:
   ```yaml
   ---
   name: code-standards
   description: Names, functions, comments, errors and the YAGNI ladder. Use when writing or reviewing code or adding a dependency. Not for test policy (skill testing).
   triggers:
     - user
     - model
   allowed-tools:
     - read
     - grep
     - glob
     - exec
     - edit
   ---
   ```
   Body outline (keep every rule of both sources; merge, do not paraphrase away a threshold): 1 Read local conventions and the whole touched flow (clean-code §1 + simplicity §1); 2 Name literally (clean-code §2); 3 Keep functions focused (clean-code §3); 4 Handle comments and errors (clean-code §4); 5 Stop at the first sufficient rung (the seven rungs of simplicity §2 as one numbered list, plus "choose the higher rung when two work"); 6 Reject speculative structure and protect non-negotiable behavior (simplicity §4 and §5, including the `// simplified: <ceiling>; <when/how to evolve>` marker and `DEBT-xxx`); 7 Control file growth and review the diff (clean-code §5 and §6, with the `[code] -> skipped: X; add when Y.` report line from simplicity §6); Done when: one sentence combining both sources. Move simplicity §3 (search before adding a utility or dependency: Maven Central, Godot Asset Library, `gh search code`, the five dependency checks) to `references/yagni-ladder.md` (new file, `kind: detail`, <= 60 lines, description <= 160) and cite it from step 5 as `references/yagni-ladder.md`.
3. Create `plugins/architect-core/skills/architecture/SKILL.md` (kit, new file) from `clean-architecture` and `ddd-and-patterns`, <= 80 lines, same frontmatter shape with `name: architecture`, `allowed-tools: read, grep, glob, edit` and this description verbatim (160 chars):
   ```text
   Layers, ports, DDD blocks and pattern choice. Use when placing a class, defining an aggregate or picking a pattern. Not for contracts (skill protocol-contract).
   ```
   Body outline: 1 Map the dependency direction; 2 Place boundaries; 3 Justify each port (the three reasons); 4 Structure by behavior; 5 Name the present problem, then pick the smallest building block or pattern from `references/pattern-catalog.md`; 6 Block accidental patterns and speculative architectures (ddd §4 plus "no Event Sourcing, CQRS or microservices without a measured need"); 7 Verify the boundary; Done when. Move the two tables of ddd-and-patterns §2 and §3 unchanged to `references/pattern-catalog.md` (new file, `kind: detail`, <= 60 lines).
4. Create `plugins/core/skills/session/SKILL.md` (kit, new file) from the three session skills, <= 80 lines, frontmatter:
   ```yaml
   ---
   name: session
   description: Session start, closeout review and handoff record. Use when starting, changing topic, closing or leaving pending work. Not for parallelism (skill parallelize).
   argument-hint: "[start | review | handoff <topic>]"
   triggers:
     - user
     - model
   allowed-tools:
     - read
     - grep
     - glob
     - exec
     - edit
   ---
   ```
   Decision (justified, not optional): one skill, model-invocable, no `agents/openai.yaml` and no `disable-model-invocation`. The parity gate (`check_kit.py:614-616`) makes "model-invocable for start/review but Codex-policy-off for handoff" impossible inside one skill, and keeping `session-handoff` separate would keep the three-way description overlap the assessment measured. The user-only semantics survive as a body rule: the handoff record is written only when invoked as `session handoff <topic>`, or when the user asks for a handoff in words; a model-triggered load runs `start` or `review` and may only suggest `handoff`. Body: one sentence naming the three modes; `## start` (sessions §1 to §5, condensed: one outcome, plan threshold, protect scope, exhausted-session signals, agent tier); `## review` (session-review §1 summary of six lines and §3 decide whether to propose, pointing to `references/kit-proposal.md` for the signal table and the proposal block); `## handoff` (session-handoff §2 to §4 condensed, keeping `Use \`../../templates/doc-session-handoff.md\`` and `docs/sessions/YYYY-MM-DD-topic.md`, pointing to `references/handoff-record.md`); `## Rules` (the write gate above; "Do not edit the kit in the same turn as the proposal"; dirty tree is a blocker); Done when. References (new files, `kind: detail`, <= 60 lines each): `references/kit-proposal.md` = session-review §2 table, the search-before-proposing step (keep its current `~/.ai-kit/...` wording; P2-01 owns it), §4 proposal block and §5; `references/handoff-record.md` = session-handoff §1 collect, §3 continuation action, §4 completeness checklist.
5. Delete the seven old skill directories, including `plugins/core/skills/session-handoff/agents/openai.yaml` (kit): `git rm -r` on each `plugins/<plugin>/skills/<old-name>/`.
6. Edit `plugins/core/AGENTS.md` (kit) after P2-03: the `End:` bullet ends `Detail: skill \`session\`.`; the `Standards are skills:` bullet becomes `- Standards are skills: \`code-standards\`, \`architecture\`, \`testing\`, \`branching-and-versioning\`, \`update-docs\`, \`git-lfs\`. Load the one the task touches; \`rules/\` loads the Java and Godot sets by file glob.`; if P2-03 added the compaction bullet with `Detail: skill \`session-handoff\``, change it to `skill \`session\``. The file keeps `# Global Rules — AI Kit` as line 1 and stays <= 60 lines; no other line changes.
7. Edit the rule files (kit): `plugins/dev-godot/rules/godot.md:2` and `plugins/dev-java/rules/java.md:2` replace `Clean Code` with `code standards`; the body line becomes `it points to \`code-standards\` and \`testing\`.` If P2-02 has already replaced these bodies, replace only the skill name inside its new wording.
8. Edit `plugins/dev-godot/skills/godot-standards/SKILL.md:17` and `plugins/dev-java/skills/java-standards/SKILL.md:17` (kit) to `Names, functions and the smallest change: read skill \`code-standards\`. Test gates and coverage: read skill \`testing\`.` (line stays one line; both files stay <= 80 lines: 47 and 53 today).
9. Edit the three plugin `INDEX.md` files (kit): remove the old rows, add `| \`code-standards\` | <description> |`, `| \`architecture\` | <description> |`, `| \`session\` | <description> |` in alphabetical position with the description byte-for-byte from the frontmatter.
10. Edit root `INDEX.md` (kit): line 24 Content cell becomes `code patterns: code standards, testing, docs, investigation`; line 27 becomes `architecture (layers, ports, DDD), protocol contracts, grilling`; lines 40 and 41 replace `\`clean-code\`` with `\`code-standards\`` (if P2-02 rewrote the Loads cells, replace the name inside its wording).
11. Edit the dev-core description in `plugins/dev-core/plugin.json`, `plugins/dev-core/.claude-plugin/plugin.json`, `plugins/dev-core/.devin-plugin/plugin.json` and `.claude-plugin/marketplace.json:23` (kit) to `ai-kit dev patterns: code standards, testing, docs and investigation skills` (same string in all four).
12. Edit `CHANGELOG.md` (kit) under `## [Unreleased]` / `### Changed`: the bullet from Report back, followed by an indented migration table with rows `clean-code -> code-standards`, `simplicity -> code-standards`, `clean-architecture -> architecture`, `ddd-and-patterns -> architecture`, `sessions -> session start`, `session-review -> session review`, `session-handoff -> session handoff <topic>` (user-invoked names change: `/session-review` becomes `/session review`).
13. Do not touch `VERSION`, `check_kit.py`, `platforms/tools/*`, any hook file, any other skill body, or any path outside the files named above.

## Out of scope

- Moving `frontend-design`, `find-skills`, `krita`, `dbeaver`, `skill-creator` to an extras plugin: P2-10. Simplifying `tokens`: P2-11. Merging `sdd-analyze` and `sdd-audit`: P3-06.
- The wording of the rule bodies (always/never constraints) and the root `INDEX.md` Loads cells: P2-02; this prompt only swaps the skill name inside whatever text is there.
- The `~/.ai-kit/plugins/...` search paths copied into `references/kit-proposal.md`: P2-01 replaces them; copy them unchanged here.
- Vendoring skills into `.claude/skills` and its acceptance check that names `session-handoff/agents/openai.yaml`: P2-06 (its executor must point that check at another user-only skill, for example `grilling`). Applying the result to the Stratics repos: P2-15.
- `plugins/core/AGENTS.md` section order and the Boundaries/Session lines added by P2-03, and the 98% rule (P1-03): edit only the two pointer bullets named in step 6.
- Skill evals that would measure the hit rate before and after: P3-09.

## Acceptance criteria

- [ ] `ls -d plugins/*/skills/*/ | wc -l` prints `39`; `ls plugins/dev-core/skills plugins/architect-core/skills plugins/core/skills` shows `code-standards`, `architecture`, `session` and none of the seven old names.
- [ ] `grep -rn 'clean-code\|simplicity\|clean-architecture\|ddd-and-patterns\|session-review\|session-handoff\|\`sessions\`' plugins platforms README.md INDEX.md docs/*.md .claude-plugin .agents | grep -v 'doc-session-handoff'` prints nothing.
- [ ] `test ! -e plugins/core/skills/session/agents/openai.yaml && echo gone` prints `gone`; `grep -c 'disable-model-invocation' plugins/core/skills/session/SKILL.md` prints `0`.
- [ ] `for f in plugins/*/skills/{code-standards,architecture,session}/SKILL.md; do wc -l < "$f"; done` prints three numbers <= 80; `for f in plugins/*/skills/{code-standards,architecture,session}/references/*.md; do wc -l < "$f"; done` prints four numbers <= 60, and each of those files starts with `---` and contains `kind: detail`.
- [ ] `grep -c 'references/yagni-ladder.md' plugins/dev-core/skills/code-standards/SKILL.md`, `grep -c 'references/pattern-catalog.md' plugins/architect-core/skills/architecture/SKILL.md`, `grep -c 'references/kit-proposal.md' plugins/core/skills/session/SKILL.md` and `grep -c 'references/handoff-record.md' plugins/core/skills/session/SKILL.md` each print >= 1; `grep -c '\.\./\.\./templates/doc-session-handoff.md' plugins/core/skills/session/SKILL.md` prints `1`.
- [ ] `grep -c 'argument-hint: "\[start | review | handoff <topic>\]"' plugins/core/skills/session/SKILL.md` prints `1`; `grep -c 'only when invoked as' plugins/core/skills/session/SKILL.md` prints `1`.
- [ ] `python3 -c "import re,glob;t=sum(len(re.search(r'^description:\s*(.*)$',open(f).read(),re.M).group(1).strip().strip('\"')) for f in glob.glob('plugins/*/skills/*/SKILL.md'));print(t)"` prints a number <= 6,300 (6,210 expected) and `grep -L 'disable-model-invocation: true' plugins/*/skills/*/SKILL.md | wc -l` prints `28`.
- [ ] `grep -c 'Detail: skill \`session\`' plugins/core/AGENTS.md` prints `1` (or `2` if P2-03's compaction bullet exists); `grep -c 'Standards are skills: \`code-standards\`, \`architecture\`, \`testing\`' plugins/core/AGENTS.md` prints `1`; `head -n 1 plugins/core/AGENTS.md` prints `# Global Rules — AI Kit`; `wc -l < plugins/core/AGENTS.md` prints <= 60.
- [ ] `grep -c 'code-standards' plugins/dev-godot/rules/godot.md plugins/dev-java/rules/java.md plugins/dev-godot/skills/godot-standards/SKILL.md plugins/dev-java/skills/java-standards/SKILL.md INDEX.md` prints `1` for each of the first four files and `2` for `INDEX.md`.
- [ ] `grep -c 'code standards, testing, docs and investigation skills' plugins/dev-core/plugin.json plugins/dev-core/.claude-plugin/plugin.json plugins/dev-core/.devin-plugin/plugin.json .claude-plugin/marketplace.json` prints `1` for each file.
- [ ] `platforms/tools/check.sh` exits 0 (covers schema, parity, line limits, budget, INDEX rows and reference links); `platforms/tools/smoke.sh` exits 0; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` reports `OK`; `python3 platforms/ci/validations/check_kit.py --links` exits 0.
- [ ] `grep -n 'P2-09' CHANGELOG.md` finds the bullet above `## [10.1.0]` and `grep -c -- '-> session handoff' CHANGELOG.md` prints `1`.
- [ ] `git diff --stat main --name-status` lists only: 7 added files (3 `SKILL.md`, 4 references), 8 deleted files, and modified `plugins/core/AGENTS.md`, the 2 rule files, the 2 standards skills, 3 plugin `INDEX.md`, root `INDEX.md`, 3 dev-core manifests, `.claude-plugin/marketplace.json`, `CHANGELOG.md`.

## Conventions

- Everything committed is in English.
- No layout or path change: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths (new skills follow `plugins/<plugin>/skills/<name>/SKILL.md` and `references/<topic>.md`).
- `VERSION` untouched (no release in this task); the user-invoked name change is recorded in the CHANGELOG migration table for the next release notes.
- `CHANGELOG.md` gets a `## [Unreleased]` entry written with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name: the three plugin `INDEX.md` tables carry the new rows and drop the old ones; references are not index entries (`check_kit.py:767-792`).
- Skill description 40-160 chars in the form `<what>. Use when <trigger>. Not for <neighbor> (skill <x>).`, copied verbatim into the plugin `INDEX.md` table; all descriptions together <= 7,200 chars (6,803 today, about 6,210 after).
- `SKILL.md` <= 80 lines; references <= 60 lines with frontmatter (`kind: detail` needs only `description` and `kind`; do not use `kind: fact`, nothing here is a dated external fact).
- Rule frontmatter = `description` <= 160 + `trigger: glob` + `globs` + `paths` as YAML sequences (only the description text changes in the two rules).
- `plugins/core/AGENTS.md` <= 60 lines and it keeps the header line `# Global Rules — AI Kit`.
- User-only skill = `triggers: [user]` + `disable-model-invocation: true` + `agents/openai.yaml` with `policy.allow_implicit_invocation: false`; the merged `session` is model-invocable, so it carries none of the three (parity gate). No subagent skill is touched; no hook or `agents/*.md` profile changes.
- `allowed-tools` are lowercase (`read`, `grep`, `glob`, `exec`, `edit`).
- Gates when the kit is touched: `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`.
- Conventional Commits with Refs, for example `feat(skills): merge clean-code+simplicity, clean-architecture+ddd-and-patterns, sessions+session-review+session-handoff` with body `Refs: P2-09, assessment §4.7, §6 F1`.
- PR body = What / Why / How I tested (literal output of the four gates, the skill count, the budget number and the empty old-name grep) / Refs.
- Nothing here needs Claude-only tools; Devin or Claude Code can execute it with read, grep, edit and shell. `argument-hint` and `disable-model-invocation` are Claude Code frontmatter keys accepted by `platforms/ci/schemas/skill.schema.json`; Devin and Codex ignore them.

## Report back

Final message format:

- done: the three new `SKILL.md` paths with their line counts and description lengths, the four references with line counts, the eight deleted paths, every edited pointer file with the final line number of its changed line; then every command run (the four gates, `ls -d plugins/*/skills/*/ | wc -l`, the budget one-liner, the `grep -L ... | wc -l` count, the old-name grep) with its literal output.
- unverified: anything not reproduced (for example `claude plugin validate` skipped because `claude` is not on PATH, which `check.sh` reports; the Devin "one skill at a time" claim if docs.devin.ai was not opened; the skill-selection hit rate itself, which only P3-09 evals can measure).
- next step: P2-10 (extras plugin), P2-06 (update its openai.yaml acceptance check to a surviving user-only skill), P2-15 (apply to the Stratics repos), P3-09 (evals that compare hit rate before and after).
- Proposed CHANGELOG line (under `### Changed`):
  `- Skills consolidated 43 -> 39 (model-invocable 31 -> 28, descriptions 6,803 -> ~6,210 of 7,200): \`clean-code\` + \`simplicity\` -> \`code-standards\` (dev-core), \`clean-architecture\` + \`ddd-and-patterns\` -> \`architecture\` (architect-core), \`sessions\` + \`session-review\` + \`session-handoff\` -> \`session\` (core, \`/session start | review | handoff <topic>\`; the handoff record is written only on explicit request, the skill is model-invocable so Codex policy and \`disable-model-invocation\` are dropped per the parity gate). Tables and procedures moved to \`references/\`. Why: the merged pairs named each other as "Not for" neighbours and Devin Cloud loads one skill at a time (assessment §4.7, §6 F1). Proof: old-name grep empty outside CHANGELOG and docs/plans; check.sh, smoke.sh, unittest and --links green. Migration (user-invoked names): see table below (P2-09).`
