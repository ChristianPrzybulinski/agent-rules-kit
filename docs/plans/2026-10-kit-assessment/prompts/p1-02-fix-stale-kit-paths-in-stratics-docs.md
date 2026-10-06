# P1-02 — Fix stale kit paths cited in stratics-docs

Phase: 1 · Repos: stratics-docs · Branch to create: docs/p1-02-stale-kit-paths from main · Depends on: none (P1-01 adds the kit-side gate; this prompt fixes the citations it will catch) · Effort: ~1 h

## Goal

Every reference from stratics-docs to a file inside agent-rules-kit resolves on kit main at version 10.1.0 (layout 10.x: `plugins/<plugin>/...`, `platforms/...`). Today 4 lines in 3 files cite the pre-8.0 layout (`agents/skills/`, `rules/godot/`, `rules/java/`, `kits/java-maven/`), none of which exists any more. After this task a repo-wide grep for the obsolete prefixes (excluding the historical archives `legacy/` and `docs/sessions/`) returns 0 hits, both spec gates stay green, and the two approved DECs keep their status, date and decision text, gaining only an editorial History line.

## Why

- assessment §4.1: the kit shipped 10 MAJOR versions between 2026-09-29 and 2026-10-04 with layout changes in 4.0, 6.0, 8.0, 9.0 and 10.0; consumer repos did not follow, so an agent reading a DEC is sent to a path that does not exist.
- assessment §6 item A3 (assessment.md:248): freeze the 10.x layout and fix the obsolete citations in stratics-docs/AGENTS.md:20, DTEC-001, DTEC-002 (and the kit's docs/projects.md, owned by P1-01). P1-01 owns the freeze and the gate; this prompt owns the citations.
- Measured on stratics-docs main (2026-10-06): `grep -rnE "agents/skills/|agents/rules/|agents/knowledge/|rules/godot/|rules/java/|(^|[^/])kits/java-maven/|(^|[^/])kits/github/|platforms/install/|processes/sdd/|plugins/ai-kit/" --exclude-dir=legacy --exclude-dir=sessions --exclude-dir=.git .` returns exactly 4 lines in 3 files (listed under Current state). The `(^|[^/])` guard keeps the valid 10.x `platforms/kits/...` paths out of the hit list (plain `grep -E`, no `-P`, so it also works on macOS/BSD grep); without it the replacement paths written in steps 3 and 4 would match again. Two further files under `docs/sessions/` also match and are historical records (exempt, see Out of scope).
- Measured on kit main (commit `ddd3ad2`, VERSION `10.1.0`): all replacement paths below are tracked files (`git ls-files` lists each one). `platforms/kits/java-maven/pom-parent.xml:117` still carries `<requireJavaVersion><version>[25,26)</version>`, so the DTEC-001 fact stays true once the path is corrected.
- stratics-docs/AGENTS.md:17 says `Ask first: ... alter an \`approved\` DEC`; both DECs are `status: approved` (DTEC-001:4, DTEC-002:4). The edit is therefore limited to the path strings plus a History line, and the owner approves the PR.

## Current state

All paths below are relative to the stratics-docs repo.

```text
AGENTS.md:20:- Process: agent-rules-kit `agents/skills/process/README.md`
docs/spec/decisions/DTEC-001-java-25-lts.md:19:- [FACT] agent-rules-kit `kits/java-maven/pom-parent.xml` requires `[25,26)`; JDK 25.0.4.1 installed via Homebrew (keg-only) on 2026-09-29; JDK 27 (non-LTS) remains on PATH.
docs/spec/decisions/DTEC-001-java-25-lts.md:43:- agent-rules-kit `rules/java/build-and-dependencies.md`, `kits/java-maven/`.
docs/spec/decisions/DTEC-002-stack-cliente-servidor-banco.md:50:- agent-rules-kit `rules/godot/godot-2d.md`, `rules/java/*`, `postgresql` skill.
```

Structure facts that constrain the edit:

- DTEC-001 and DTEC-002 end with `## References` as their last section (DTEC-001:41, DTEC-002:48). No DEC in `docs/spec/decisions/` has a `## History` section today, and the kit template `plugins/architect-sdd/templates/spec-decision.md` has none either; `.github/spec-lint/check_spec.py` validates frontmatter and FEAT/REQ links only, so an extra trailing section is accepted by the gate.
- `changelog.d/README.md` names fragments `<id>.<type>.md`, where `<id>` is the task issue number or, for PRs without an issue, the branch slug; the content is Keep a Changelog bullets starting with `- ` and a claim tag.
- `changelog.d/p1-02-stale-kit-paths.fixed.md` (new file). `changelog.d/` has no index file; the fragment is picked up by name.

## Change

All edits are in the stratics-docs repo. Before step 1, confirm each replacement path on kit main: `git -C <kit clone> ls-files <path>` must print the path, or check the file on github.com/ChristianPrzybulinski/agent-rules-kit; verify against kit main before relying on it.

1. Create the branch `docs/p1-02-stale-kit-paths` from `main`.

2. Edit `AGENTS.md:20`. Replace the whole line with:

```markdown
- Process: agent-rules-kit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md`
```

3. Edit `docs/spec/decisions/DTEC-001-java-25-lts.md`. Change only the path strings; the `[FACT]` tag, the `[25,26)` claim and the JDK sentence stay as they are.
   - Line 19: `kits/java-maven/pom-parent.xml` -> `platforms/kits/java-maven/pom-parent.xml`.
   - Line 43 becomes:

```markdown
- agent-rules-kit `plugins/dev-java/skills/java-standards/references/build-and-dependencies.md`, `platforms/kits/java-maven/`.
```

   - Append after the References list, as the new last section of the file:

```markdown

## History

- 2026-10-06 editorial: kit path updated (kit 10.1.0).
```

   Use the date you make the edit in `YYYY-MM-DD`. Do not touch the frontmatter (`status: approved`, `date`, `features`), the Decision, Alternatives, Consequences or How to validate sections.

4. Edit `docs/spec/decisions/DTEC-002-stack-cliente-servidor-banco.md`. Line 50 becomes:

```markdown
- agent-rules-kit `plugins/dev-godot/skills/godot-standards/SKILL.md`, `plugins/dev-java/rules/java.md`, `postgresql` skill.
```

   Only the two stale path strings change (assessment §4.1 names `rules/godot/godot-2d.md`; `rules/java/*` maps to one file); `postgresql` skill is not a path and stays as written. Append the same `## History` section with the same editorial line as in step 3. Nothing else in the file changes.

5. Re-run the repo-wide grep from Why (same anchored pattern with the `(^|[^/])` guard, same exclusions). The expected result is zero lines and exit status 1; if a new hit appears (a file merged after 2026-10-06), map it with the table below and fix it in the same commit. Mapping, old -> new, all verified on kit main `ddd3ad2`:
   - `agents/skills/process/README.md` -> `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md`
   - `agents/skills/<type>/<name>` -> `plugins/<plugin>/skills/<name>/SKILL.md` (find the plugin with `git -C <kit clone> ls-files 'plugins/*/skills/<name>/SKILL.md'`)
   - `agents/rules/*`, `rules/java/*` -> `plugins/dev-java/rules/java.md`; `rules/godot/*` -> `plugins/dev-godot/rules/godot.md` or `plugins/dev-godot/skills/godot-standards/SKILL.md`
   - `agents/knowledge/java/*` -> `plugins/dev-java/skills/java-standards/references/*`
   - `kits/java-maven/` -> `platforms/kits/java-maven/`; `kits/github/` -> `platforms/kits/github/`
   - `platforms/install/`, `processes/sdd/`, `plugins/ai-kit/` -> no 10.x equivalent as a folder; cite the concrete 10.x file (`platforms/tools/*.sh`, `plugins/architect-sdd/skills/sdd-*/SKILL.md`, `plugins/<plugin>/`) and say so in the PR body.

6. Create `changelog.d/p1-02-stale-kit-paths.fixed.md` with exactly:

```markdown
- [FACT] `AGENTS.md`, DTEC-001 and DTEC-002 cite agent-rules-kit 10.1.0 paths (`plugins/`, `platforms/kits/`) instead of the pre-8.0 layout (old `agents/`, `rules/` and `kits/` roots); editorial only, DEC status and decision text unchanged (kit assessment §4.1, item A3).
```

7. Run the gates (Acceptance criteria), commit with Conventional Commits, open the PR with the repo template. Do not open a GitHub issue for this task; if the owner asks for one, run `python3 tools/project-sync/sync.py --issue <N> --repo ChristianPrzybulinski/stratics-docs` afterwards as AGENTS.md:15 requires.

Commit message:

```text
docs(spec): cite agent-rules-kit 10.1.0 paths in AGENTS.md, DTEC-001 and DTEC-002

Refs: agent-rules-kit docs/plans/2026-10-kit-assessment/assessment.md §4.1 (A3), prompt P1-02
```

PR body (template `.github/PULL_REQUEST_TEMPLATE.md`): What = the 3 files and the 4 lines; Why = assessment §4.1 / A3, paths no longer exist since kit 8.0; How I tested = literal output of the two gates and the grep; Proof block:

```proof
! grep -rnE "agents/skills/|agents/rules/|agents/knowledge/|rules/godot/|rules/java/|(^|[^/])kits/java-maven/|(^|[^/])kits/github/|platforms/install/|processes/sdd/|plugins/ai-kit/" --exclude-dir=legacy --exclude-dir=sessions --exclude-dir=.git .
python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas
python3 tools/spec-trace/spec_trace.py check
grep -c "editorial: kit path updated (kit 10.1.0)" docs/spec/decisions/DTEC-001-java-25-lts.md
grep -c "editorial: kit path updated (kit 10.1.0)" docs/spec/decisions/DTEC-002-stack-cliente-servidor-banco.md
```

Replace the template's `Closes ChristianPrzybulinski/stratics-docs#` line with `Refs: agent-rules-kit assessment §4.1 (A3), P1-02`. Tick only the changelog checkbox. Request review from the owner and state in the PR body that two approved DECs change (path strings and History only), so the "Ask first" rule of AGENTS.md:17 is satisfied by the PR approval.

## Out of scope

- The kit itself: freezing the 10.x layout, the `check_kit.py` stale-path gate and the stale `platforms/install/` and `knowledge/` mentions in the kit's `docs/projects.md` belong to P1-01. Do not add new kit paths or propose renames: the layout is frozen.
- `docs/sessions/2026-09-30-kit-v5-english.md` and `docs/sessions/2026-09-30-pendencias-reconciliacao.md` match the obsolete pattern (lines 12, 24, 39, 40 and 13, 42, 43 with the anchored pattern). They are dated session records: do not edit them; list them as exempt in the PR body. The same exemption applies to anything under `docs/collab/` (0 hits today) and `legacy/`.
- `AGENTS.md:6` (`~/.ai-kit/platforms/tools/check.sh --spec docs/spec`) is a valid 10.x path (`check.sh` accepts `--spec`); leave it. Replacing `~/.ai-kit` by a per-repo copy is P2-04 (CLAUDE.md/settings) and P2-06 (vendored skills).
- The machine-specific sentence in DTEC-001:19 ("installed via Homebrew ...") is a DEC fact; leave it. Removing machine facts from the kit is P2-01.
- Generating `CLAUDE.md`, `.claude/settings.json` or `.claude/rules` in stratics-docs: P2-04, P2-05.
- Deriving FEAT/task status from GitHub: P2-08.

## Acceptance criteria

- [ ] `git branch --show-current` prints `docs/p1-02-stale-kit-paths`; `git diff --stat main` lists exactly 4 files: `AGENTS.md`, the two DEC files and `changelog.d/p1-02-stale-kit-paths.fixed.md`.
- [ ] `grep -rnE "agents/skills/|agents/rules/|agents/knowledge/|rules/godot/|rules/java/|(^|[^/])kits/java-maven/|(^|[^/])kits/github/|platforms/install/|processes/sdd/|plugins/ai-kit/" --exclude-dir=legacy --exclude-dir=sessions --exclude-dir=.git .` prints nothing and exits 1.
- [ ] `grep -c "plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md" AGENTS.md` prints `1`.
- [ ] `grep -c "platforms/kits/java-maven/" docs/spec/decisions/DTEC-001-java-25-lts.md` prints `2`.
- [ ] `grep -c "plugins/dev-godot/skills/godot-standards/SKILL.md" docs/spec/decisions/DTEC-002-stack-cliente-servidor-banco.md` prints `1`.
- [ ] `grep -c "^## History" docs/spec/decisions/DTEC-001-java-25-lts.md docs/spec/decisions/DTEC-002-stack-cliente-servidor-banco.md` prints `1` for each file, and `grep -c "editorial: kit path updated (kit 10.1.0)"` prints `1` for each.
- [ ] `grep -n "^status: approved" docs/spec/decisions/DTEC-001-java-25-lts.md docs/spec/decisions/DTEC-002-stack-cliente-servidor-banco.md` prints both files at line 4 (status unchanged); `git diff main -- docs/spec/decisions | grep -E "^[-+]" | grep -vE "^(---|\+\+\+) " | grep -vE "agent-rules-kit|## History|editorial: kit path updated|^[-+]$"` prints nothing (only path lines and the History block changed).
- [ ] Each replacement path exists on kit main: `git -C <kit clone> ls-files plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md platforms/kits/java-maven/pom-parent.xml plugins/dev-java/skills/java-standards/references/build-and-dependencies.md plugins/dev-godot/skills/godot-standards/SKILL.md plugins/dev-java/rules/java.md | wc -l` prints `5`.
- [ ] Gate: `pip install pyyaml jsonschema` then `python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas` prints `spec: OK (130 artifacts)` (count may be higher if FEATs were added after 2026-10-06) and exits 0.
- [ ] Gate: `python3 tools/spec-trace/spec_trace.py check` prints `spec-trace: OK (...)` and exits 0.
- [ ] `ls changelog.d/p1-02-stale-kit-paths.fixed.md` succeeds and `head -c 9 changelog.d/p1-02-stale-kit-paths.fixed.md` prints `- [FACT] `.
- [ ] PR body follows `.github/PULL_REQUEST_TEMPLATE.md` with the `proof` block above; every proof line starts with a word from `proof_allowlist` in `ops/review-loop/config.json` (`!`, `python3`, `grep` are allowed) and exits 0 on a clean checkout.
- [ ] CI workflow `docs-checks` is green on the PR (it runs the same two gates plus the spec-trace self-test).

## Conventions

- Everything committed is in English (stratics-docs AGENTS.md: "docs and frontmatter values in English").
- No layout or path change in the kit: the 10.x layout is frozen; cite kit paths exactly as they exist on kit main and never invent a new one.
- Kit `VERSION` and kit `CHANGELOG.md` are untouched: this task does not edit the kit. stratics-docs records the change through a `changelog.d/` fragment (DPRO-011), never by editing its `CHANGELOG.md` directly.
- Approved DEC rule (AGENTS.md:17): only path strings in Context/References plus the History line change; status, date, deciders and decision text are untouched; the owner approves the PR.
- Conventional Commits with a `Refs:` trailer; PR body = What / Why / How I tested (literal output) / Proof / Refs.
- Gates for stratics-docs: `python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas`; `python3 tools/spec-trace/spec_trace.py check`; the PR template proof block and the changelog.d fragment.
- Never write an obsolete prefix literally anywhere in the stratics-docs repo, including `changelog.d/` fragments and PR-related files; describe it instead (for example "old `agents/` root"), otherwise the grep above and the P1-01 kit gate fire on the fix itself and the hit migrates into `CHANGELOG.md`.
- No Claude-only tooling is needed; the task runs the same on Devin or Claude Code.

## Report back

Final message, in this order:

1. done: the 4 file paths with the exact lines changed (`path:line` before -> after), the branch name, the PR URL, and the literal output of: the obsolete-path grep (expected empty, exit 1), `check_spec.py`, `spec_trace.py check`, and the kit `git ls-files ... | wc -l` check (expected `5`).
2. unverified: anything not run (for example the kit path check if no kit clone or network was available, or `docs-checks` CI if the PR was not opened), each with the command the owner should run.
3. next step: owner approves the PR (two approved DECs change editorially); then P1-01 lands the kit-side gate that would have caught these citations.
4. Proposed one-line CHANGELOG entry (goes into stratics-docs `CHANGELOG.md` under `## [Unreleased]` when the orchestrator moves the fragment): `- [FACT] AGENTS.md, DTEC-001 and DTEC-002 cite agent-rules-kit 10.1.0 paths (plugins/, platforms/kits/) instead of the pre-8.0 layout (old agents/, rules/ and kits/ roots); editorial only, DEC status and decision text unchanged (kit assessment §4.1, A3).`
