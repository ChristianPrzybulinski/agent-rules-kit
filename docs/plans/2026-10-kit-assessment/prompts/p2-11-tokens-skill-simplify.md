# P2-11 — Simplify the tokens skill (drop compression levels)

Phase: 2 · Repos: kit (agent-rules-kit) · Branch to create: fix/p2-11-tokens-skill-simplify from main · Depends on: none · Effort: ~0.5 h

## Goal

Remove the per-session output compression levels (`lite`, `full`, `ultra`) from `plugins/core/skills/tokens/SKILL.md` and state in the same skill that a register changes density, never the conversation language. The three registers (technical, human-facing, governed), the mixed-output rule and the closing rule (§6) stay as they are. Measurable result: `grep -rnw 'ultra' plugins` and `grep -rnw 'lite' plugins` print nothing, `grep -c 'Compression levels' plugins/core/skills/tokens/SKILL.md` prints `0`, the skill stays at 50 lines (limit 80), the description budget stays at its current value, and all four kit gates stay green.

## Why

- assessment §4.7: "`tokens` defines 'ultra' compression levels that conflict with 'governed documents never compressed' and with the required pt-BR communication".
- assessment §6 F3 (the authoritative shape of this change): "Keep the three registers (technical, human, governed); remove `lite/full/ultra`. Output compression does not reduce input tokens (where the cost is) and conflicts with the pt-BR/governed rule."
- `plugins/core/skills/tokens/SKILL.md:25` makes a compression level sticky ("Keep the chosen level for the session") while `:41` says "do not compress structural repetition" for governed documents and `:45` requires governed passages "in their final governed format" even inside technical output. A session-wide `ultra` level has no defined behavior when the next passage is a spec or a CHANGELOG entry.
- `plugins/core/AGENTS.md:34`: "Only the conversation with the user is in pt-BR." A "fragments" or "code plus one line" level applied to the conversation produces pt-BR fragments or English-only code answers; nothing in the skill says which rule wins.
- `plugins/core/AGENTS.md:50` already summarizes the skill without any level ("code/diff first, then ≤3 lines ... Governed documents ...: template and schema, never compressed. Detail: skill `tokens`"); the levels exist only in the skill, so no other always-on text changes.
- Measured: `grep -rnw -e ultra -e lite plugins docs README.md CHANGELOG.md` finds the levels in exactly one kit file outside `docs/plans/` (`plugins/core/skills/tokens/SKILL.md:25`); `grep -rl 'Compression levels on request'` across the three Stratics checkouts finds no vendored copy. The whole change is one file plus the CHANGELOG.

## Current state

All paths are in the kit repo (v10.1.0). `wc -l plugins/core/skills/tokens/SKILL.md` prints `51`. The folder holds only `SKILL.md` (no `references/`, no `agents/openai.yaml`).

```
plugins/core/skills/tokens/SKILL.md:1:---
plugins/core/skills/tokens/SKILL.md:2:name: tokens
plugins/core/skills/tokens/SKILL.md:3:description: Response register for code, e-mail, reports, README and governed docs. Use when writing long answers or text for humans. Not for doc policy (skill update-docs).
plugins/core/skills/tokens/SKILL.md:4:triggers:
plugins/core/skills/tokens/SKILL.md:5:  - user
plugins/core/skills/tokens/SKILL.md:6:  - model
plugins/core/skills/tokens/SKILL.md:7:allowed-tools:
plugins/core/skills/tokens/SKILL.md:8:  - read
plugins/core/skills/tokens/SKILL.md:9:---
plugins/core/skills/tokens/SKILL.md:13:## 1. Classify before writing
plugins/core/skills/tokens/SKILL.md:15:Choose one register: technical, human-facing, or governed. Read only the material needed for the requested outcome; broad reading needs a named hypothesis.
plugins/core/skills/tokens/SKILL.md:17:## 2. Use the technical register
plugins/core/skills/tokens/SKILL.md:24:- Use the smallest useful snippet; do not repeat the request or narrate a feature tour.
plugins/core/skills/tokens/SKILL.md:25:- Compression levels on request: `lite` = concise sentences, `full` = fragments, `ultra` = code plus one line. Keep the chosen level for the session.
plugins/core/skills/tokens/SKILL.md:27:Return to full prose for security warnings, irreversible actions, payments, migrations, force-pushes, or multi-step instructions that become ambiguous when compressed.
plugins/core/skills/tokens/SKILL.md:39:## 4. Preserve governed documents
plugins/core/skills/tokens/SKILL.md:41:For `docs/spec/**`, `CHANGELOG.md`, commit messages, comments, `AGENTS.md`, skills and protocol contracts, follow their template and schema. Keep `[FACT]`, `[DECISION]`, `[PROPOSAL]`, `[HYPOTHESIS]` and `[BLOCKER]`; do not compress structural repetition.
plugins/core/skills/tokens/SKILL.md:47:## 6. Close
plugins/core/skills/tokens/SKILL.md:49:End technical work with: done, unverified, concrete next step. Ask one focused question with two to four options when ambiguity blocks progress.
plugins/core/skills/tokens/SKILL.md:51:Done when: one register governs each passage, exact technical text is preserved, and governed content remains template-valid.
```

The description (line 3) is 160 characters, exactly the validator limit (`platforms/ci/validations/check_kit.py:24: DESCRIPTION_MAX = 160`). It is repeated verbatim in the plugin index:

```
plugins/core/INDEX.md:13:| `tokens` | Response register for code, e-mail, reports, README and governed docs. Use when writing long answers or text for humans. Not for doc policy (skill update-docs). |
```

Always-on lines that constrain the skill (read-only; they do not change in this task):

```
plugins/core/AGENTS.md:34:- **Everything written is in English** — code, comments, commits, docs, folder names. Only the conversation with the user is in pt-BR.
plugins/core/AGENTS.md:50:- Technical answer: code/diff first, then ≤3 lines; paths, commands and errors byte-for-byte; full prose only for security warnings, irreversible actions and multi-step sequences. Text for people: fluid, no AI clichés, no fabricated facts. Governed documents (specs, CHANGELOG, commits, skills): template and schema, never compressed. Detail: skill `tokens`.
```

`CHANGELOG.md:5` is `## [Unreleased]` with `### Added` and `### Changed` subsections already present. `VERSION` is `10.1.0`.

## Change

1. Edit `plugins/core/skills/tokens/SKILL.md` (kit): delete line 25 in full (both sentences, "Compression levels on request: ..." and "Keep the chosen level for the session."). Do not renumber or retitle any section; do not touch lines 1-9 (frontmatter), 27 ("Return to full prose ..." stays verbatim: "full prose" is English, not the removed level), 39-51.
2. Same file, line 15 (§1): append one sentence at the end of the paragraph, on the same line, so the paragraph reads:
   ```markdown
   Choose one register: technical, human-facing, or governed. Read only the material needed for the requested outcome; broad reading needs a named hypothesis. A register sets density, never language or format: the conversation stays in the language the repo's `AGENTS.md` sets, and governed passages keep their template (§4), so there is no session-wide compression mode to request or remember.
   ```
   This is the only added text. Net effect on the file: 51 lines become 50.
3. Keep the description on line 3 verbatim (it is already at the 160 limit and matches `plugins/core/INDEX.md:13`). If you decide to shorten it, keep the form `<what>. Use when <trigger>. Not for <neighbor> (skill <x>).`, 40-160 characters, and replace `plugins/core/INDEX.md:13` with the identical string in the same cell; `check_kit.py:791-792` fails when the two differ. Shortening is optional and not required for acceptance.
4. Run `grep -rnw -e ultra -e lite plugins docs README.md CHANGELOG.md | grep -v '^docs/plans/'`. Expected: no output. If any line appears, remove the level mention there with the same minimal edit and list the file in the report; the only hit known today is the deleted line 25.
5. Edit `CHANGELOG.md` (kit): add one bullet under `## [Unreleased]` / `### Changed` using the proposed entry in Report back, with the grep result and the line count as proof.
6. Do not touch `VERSION`, `plugins/core/INDEX.md` (unless step 3 shortened the description), `plugins/core/AGENTS.md`, any other skill, any script in `platforms/`, or any path.

## Out of scope

- Merging `sessions` + `session-review` + `session-handoff` and the other skill consolidations: P2-09. `tokens` stays a separate skill in `plugins/core`.
- Moving `find-skills`, `skill-creator` and the other extras out of `plugins/core`: P2-10. Do not edit their rows in `plugins/core/INDEX.md`.
- Reordering or rewording `plugins/core/AGENTS.md`, including line 50 ("Detail: skill `tokens`") and line 34 (the pt-BR rule): P2-03 owns the order; the text of line 50 is already consistent with this change and stays.
- Vendoring the updated skill into the Stratics repos (`.claude/skills` with a manifest): P2-06; applying it to the three repos: P2-15. Do not edit stratics-docs, stratics-client or stratics-server.
- Skill evals that would measure whether `tokens` loads for the right requests: P3-09.
- Raising `DESCRIPTION_MAX`, `DESCRIPTIONS_BUDGET` or `SKILL_MAX_LINES` in `check_kit.py`: not allowed by any prompt (layout and validator freeze, P1-01).

## Acceptance criteria

- [ ] `grep -c 'Compression levels' plugins/core/skills/tokens/SKILL.md` prints `0`.
- [ ] `grep -c 'Keep the chosen level' plugins/core/skills/tokens/SKILL.md` prints `0`.
- [ ] `grep -rnw -e ultra -e lite plugins docs README.md CHANGELOG.md | grep -v '^docs/plans/' | grep -v '^CHANGELOG.md' | wc -l` prints `0` (the CHANGELOG bullet is allowed to name the removed levels).
- [ ] `grep -c 'A register sets density, never language or format' plugins/core/skills/tokens/SKILL.md` prints `1` and `awk '/^## 1\./{f=1} /^## 2\./{f=0} f && /never language/' plugins/core/skills/tokens/SKILL.md | wc -l` prints `1` (the sentence sits in §1).
- [ ] `grep -c '^## ' plugins/core/skills/tokens/SKILL.md` prints `6` and `grep '^## ' plugins/core/skills/tokens/SKILL.md | tr '\n' '|'` prints `## 1. Classify before writing|## 2. Use the technical register|## 3. Use the human-facing register|## 4. Preserve governed documents|## 5. Handle mixed output|## 6. Close|`.
- [ ] `grep -c 'Return to full prose for security warnings' plugins/core/skills/tokens/SKILL.md` prints `1` and `grep -c 'do not compress structural repetition' plugins/core/skills/tokens/SKILL.md` prints `1` (the governed rule and the prose fallback are untouched).
- [ ] `wc -l < plugins/core/skills/tokens/SKILL.md` prints `50` (at most 80).
- [ ] `diff <(git show main:plugins/core/skills/tokens/SKILL.md) plugins/core/skills/tokens/SKILL.md` prints exactly two hunks, `15c15` (one `<` line, one `>` line) and `25d24` (one `<` line: the old compression-levels bullet); no other hunk.
- [ ] `d="$(sed -n 3p plugins/core/skills/tokens/SKILL.md | sed 's/^description: //')"; grep -Fc "| \`tokens\` | $d |" plugins/core/INDEX.md; printf '%s' "$d" | wc -c` prints `1` and then a number between 40 and 160 (160 when the description is kept).
- [ ] `platforms/tools/check.sh` exits 0.
- [ ] `platforms/tools/smoke.sh` exits 0.
- [ ] `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` reports `OK`.
- [ ] `python3 platforms/ci/validations/check_kit.py --links` exits 0 and its output contains no `description budget` failure (the total stays at today's value when the description is kept; the kit limit is 7,200).
- [ ] `grep -n 'P2-11' CHANGELOG.md` finds the new bullet above `## [10.1.0]`.
- [ ] `git diff --stat main` lists exactly two files, `plugins/core/skills/tokens/SKILL.md` and `CHANGELOG.md` (three if step 3 shortened the description: plus `plugins/core/INDEX.md`).

## Conventions

- Everything committed is in English.
- No layout or path change: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths. The skill stays at `plugins/core/skills/tokens/SKILL.md`.
- `VERSION` untouched (no release in this task).
- `CHANGELOG.md` gets a `## [Unreleased]` entry written with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name: no file is added or removed, so `plugins/core/INDEX.md` changes only if the description is shortened, and then only the `tokens` row.
- Skill description 40-160 chars in the form `<what>. Use when <trigger>. Not for <neighbor> (skill <x>).` and copied verbatim into the plugin `INDEX.md` table; all skill descriptions together at most 7,200 chars (6,803 today).
- `SKILL.md` at most 80 lines (50 after this change).
- `plugins/core/AGENTS.md` is not edited; it stays at 60 lines or fewer with the header line `# Global Rules — AI Kit`.
- Gates when the kit is touched: `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`.
- Conventional Commits with Refs, for example `fix(core): drop lite/full/ultra compression levels from the tokens skill` with body `Refs: P2-11, assessment §4.7, §6 F3`.
- PR body = What / Why / How I tested (literal output of the four gates, the two greps and `wc -l`) / Refs.
- Nothing here needs Claude-only tools; Devin or Claude Code can execute it with read, grep, edit and shell.

## Report back

Final message format:

- done: `plugins/core/skills/tokens/SKILL.md` (deleted line, final text of line 15, final `wc -l`), `CHANGELOG.md` (line number of the new bullet), `plugins/core/INDEX.md` only if the description changed; then every command run (the four gates, the `grep -rnw` sweep, the `diff` against main, the section-heading `tr` check) with its literal output.
- unverified: anything not reproduced (for example `claude plugin validate` skipped because `claude` is not on PATH, which `check.sh` reports).
- next step: P2-06 (vendor the updated skill into the repos) and P2-15 (apply it to the three Stratics repos); P3-09 if an eval for `tokens` is wanted.
- Proposed CHANGELOG line (under `### Changed`):
  `- tokens skill: the lite/full/ultra compression levels and the "keep the chosen level for the session" rule are removed; §1 now states that a register sets density, never language or format. Output compression does not reduce input tokens, where the cost is, and a session-wide level contradicted the pt-BR conversation rule (AGENTS.md) and "do not compress" for governed documents in the same skill (assessment §4.7, §6 F3). Proof: grep -rnw -e ultra -e lite plugins prints nothing; SKILL.md 51 -> 50 lines; description and INDEX.md row unchanged; all four kit gates green (P2-11).`
