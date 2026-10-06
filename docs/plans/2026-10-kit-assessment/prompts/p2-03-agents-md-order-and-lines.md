# P2-03 — Reorder the global AGENTS.md and add two lines

Phase: 2 · Repos: kit (agent-rules-kit) · Branch to create: docs/p2-03-agents-md-order-and-lines from main · Depends on: P1-03 · Effort: ~1 h

## Goal

Reorder the sections of `plugins/core/AGENTS.md` so the concrete, incident-preventing sections (Boundaries, Session, Work loop, Craft, Security, Communication) come before the abstract ones (Truth, Skepticism as rewritten by P1-03), and add two always-on lines: a compaction rule under Session and a task-scope rule under Boundaries. No existing line is reworded or dropped. Measurable result: the file stays at 60 lines or fewer (59 expected), keeps the exact header `# Global Rules — AI Kit`, and a sorted diff against `main` shows exactly two added lines and zero removed ones; every kit gate stays green.

## Why

- assessment §5.1 (IFScale row): IFScale (arXiv:2507.11538) measures that instruction adherence drops with instruction density and that instructions at the top of a file are followed more (primacy bias); the kit file is 57 lines "but the abstract Truth/Skepticism section comes before the concrete Boundaries"; verdict: adjust the order, Boundaries and commands first.
- assessment §6 item B3: put Boundaries (Always/Ask/Never) and Session at the top and Truth/Skepticism after; the concrete sections are the ones that prevent incidents. Add the compaction line and the Files-cell scope line.
- `plugins/core/AGENTS.md:5` to `:17` (Truth and Skepticism, 13 lines) sit above `plugins/core/AGENTS.md:42` (Boundaries) today; the Ask-first and Never lists are lines 45 and 46 of a 57-line file.
- The scope rule lives only in the project today: `stratics-docs/CONTRIBUTING.md:60` defines `Files` as "the only paths the PR may change", `:129` and `:144-145` tell the agent to stop and name the exact path, `:165` makes it the first Always rule. It is the rule that saved the most review rounds in the DPRO-011 loop (20 of 33 first-pass rejections in the ledger were scope or spec findings, assessment §4); a kit that is used by three repositories should carry it once.
- The compaction line follows the official Claude Code guidance: the costs page says to "customize compaction behavior in your CLAUDE.md file" with a "Compact instructions" section telling the model what to preserve (verified 2026-10-06 at https://code.claude.com/docs/en/costs; re-read it before relying on exact wording). Devin reads the same file (`README.md:19`, "Devin Cloud | required plugin `plugins/core/AGENTS.md`") and the line is harmless there.
- `docs/design.md:14`: "A line stays in `AGENTS.md` only if the behavior must hold before any skill could trigger". Both new lines pass that test: compaction happens between turns, and the scope check must hold before any skill loads.

## Current state

All paths are in the kit repo (v10.1.0, before P1-03). Line numbers below shift after P1-03 merges; re-derive them with `grep -n '^## ' plugins/core/AGENTS.md` before editing.

```
plugins/core/AGENTS.md:1:# Global Rules — AI Kit
plugins/core/AGENTS.md:3:Always-on discipline only. Procedures, standards and facts live in skills (loaded by description or by a `rules/` glob); each line here exists because no skill can enforce it. Project rules (the repo's `AGENTS.md`) override this file.
plugins/core/AGENTS.md:5:## Truth
plugins/core/AGENTS.md:13:## Skepticism (>98%)
plugins/core/AGENTS.md:19:## Session
plugins/core/AGENTS.md:21:- Start: read the repo's `AGENTS.md`; name **the** outcome of this session in one sentence.
plugins/core/AGENTS.md:22:- One session, one outcome; one PR, one concern. Request on another topic → warn and stop: follow-up or new session; never mix silently.
plugins/core/AGENTS.md:23:- End: summary (done · unverified · next step) + at most **one** kit proposal with evidence from this session, asked before written. Detail: skills `sessions`, `session-review`, `session-handoff`.
plugins/core/AGENTS.md:25:## Work loop
plugins/core/AGENTS.md:32:## Craft
plugins/core/AGENTS.md:35:- Standards are skills: `clean-code`, `clean-architecture`, `simplicity`, `ddd-and-patterns`, `testing`, `branching-and-versioning`, `update-docs`, `git-lfs`. Load the one the task touches; `rules/` loads the Java and Godot sets by file glob.
plugins/core/AGENTS.md:37:## Security
plugins/core/AGENTS.md:42:## Boundaries
plugins/core/AGENTS.md:44:- **Always**: run project tests/lint before saying "done"; read the repo's `AGENTS.md`/README before changing.
plugins/core/AGENTS.md:45:- **Ask first**: add/remove a dependency; change an applied migration; force-push; delete files you did not create; any operation with external effect (deploy, e-mail, payment).
plugins/core/AGENTS.md:46:- **Never**: commit `.env`/secrets; disable a failing test to go green; rewrite public history without authorization; invent command output or an API.
plugins/core/AGENTS.md:48:## Communication
plugins/core/AGENTS.md:53:| Context without an obvious skill | Load |
```

Section order today (`grep '^## ' plugins/core/AGENTS.md`): Truth, Skepticism (>98%), Session, Work loop, Craft, Security, Boundaries, Communication; then the routing table at lines 53-57. `wc -l` prints 57.

Gates and scripts that read this file (do not edit them; they define the constraints):

```
platforms/ci/validations/check_kit.py:22:AGENTS_MAX_LINES = 60
platforms/ci/validations/check_kit.py:399:    if agents_lines > AGENTS_MAX_LINES:
platforms/ci/validations/check_kit.py:400:        fail(rel(agents_md), f"{agents_lines} lines (>{AGENTS_MAX_LINES})")
platforms/tools/bootstrap.sh:8:HEADER="# Global Rules — AI Kit"
platforms/tools/bootstrap.sh:88:    if ! grep -Fxq "$HEADER" "$destination"; then
platforms/tools/doctor.sh:6:HEADER="# Global Rules — AI Kit"
platforms/tools/doctor.sh:105:    if grep -Fxq "$HEADER" "$destination"; then
platforms/tools/doctor.sh:581:    agents_lines="$(wc -l < "$KIT/plugins/core/AGENTS.md" | tr -d ' ')"
platforms/tools/smoke.sh:94:printf '# Global Rules — AI Kit\n' > "$TEST_HOME/.config/devin/AGENTS.md"
```

Project rule being lifted into the kit (stratics-docs, read-only here):

```
stratics-docs/CONTRIBUTING.md:60:| Files | the only paths the PR may change |
stratics-docs/CONTRIBUTING.md:144:4. If the proof needs a path outside the Files cell (a test file, a generated *.import or *.uid, pom.xml,
stratics-docs/CONTRIBUTING.md:145:   application.yml), stop and name the exact path.
stratics-docs/CONTRIBUTING.md:165:- **Always:** stay within the Files cell; follow the target repository's `AGENTS.md`; write everything
```

`plugins/core/INDEX.md` does not list `AGENTS.md` today and no file is added or removed, so no index changes. `CHANGELOG.md:5` is `## [Unreleased]` with `### Added` and `### Changed` subsections already present.

## Change

1. Confirm P1-03 is merged: `git log --oneline main -- plugins/core/AGENTS.md` shows its commit and `grep -c '98%' plugins/core/AGENTS.md` prints `0`. If not, stop and report; this prompt moves the Truth/Skepticism blocks exactly as P1-03 left them and must not re-edit their text.
2. Edit `plugins/core/AGENTS.md` (kit). Keep line 1 byte-for-byte (the header contains U+2014; the greps above use `grep -Fx`), keep the blank line 2 and the intro paragraph (line 3) in place. Move whole sections (heading, blank line, bullets) so the order becomes:
   1. `## Boundaries`
   2. `## Session`
   3. `## Work loop`
   4. `## Craft`
   5. `## Security`
   6. `## Communication`
   7. `## Truth`
   8. the Skepticism section under whatever heading P1-03 gave it
   9. the routing table (`| Context without an obvious skill | Load |` and its rows), unchanged and still last
   Every existing bullet keeps its text, including line 35 (`Standards are skills: ...`), which P2-09 owns.
3. In `## Boundaries`, append one bullet after the `**Never**` bullet:
   ```markdown
   - **Scope**: the task scope is the issue's `Files` cell (or the request when there is no issue). A change needed outside it → stop and name the exact path; never widen the scope silently.
   ```
4. In `## Session`, append one bullet after the `End:` bullet:
   ```markdown
   - When compacting or summarizing context, preserve the list of modified files and the test commands verbatim, so the next turn can re-run the proof. Detail: skill `session-handoff`.
   ```
   The two new bullets use the arrow and bold markers the file already uses; keep each on one line.
5. Run `wc -l plugins/core/AGENTS.md`: expected 59 (57 + 2) if P1-03 kept Skepticism at three bullets. If the count exceeds 60, do not trim any existing line: stop and report which line P1-03 added, so the owner decides.
6. Edit `CHANGELOG.md` (kit): add one bullet under `## [Unreleased]` / `### Changed` using the proposed entry in Report back, with the `grep '^## '` order and the sorted-diff result as proof.
7. Do not touch `VERSION`, any script in `platforms/tools/`, `check_kit.py`, `plugins/core/INDEX.md`, any skill, or any path.

## Out of scope

- The wording of Truth and Skepticism, and the removal of "98%": P1-03. This prompt only moves those blocks.
- The `Standards are skills:` line (consolidation of `clean-code`, `clean-architecture`, `simplicity` into fewer skills): P2-09.
- Generating per-repo `CLAUDE.md` / `.claude/settings.json` from this file: P2-04; `.claude/rules`: P2-05; vendored skills: P2-06.
- Applying the result to the three Stratics repos and reconciling `stratics-docs/CONTRIBUTING.md` §6 with the new kit line: P2-15. Do not edit the stratics repos.
- Deriving the `Files` cell from GitHub issues: P2-08. The sdd-tasks task template that produces the cell: P1-08.
- Raising `AGENTS_MAX_LINES` or changing the header string: not allowed by any prompt (layout freeze, P1-01).

## Acceptance criteria

- [ ] `head -n 1 plugins/core/AGENTS.md` prints `# Global Rules — AI Kit` and `grep -Fxq '# Global Rules — AI Kit' plugins/core/AGENTS.md; echo $?` prints `0`.
- [ ] `wc -l < plugins/core/AGENTS.md` prints a number of at most 60 (59 expected).
- [ ] `grep '^## ' plugins/core/AGENTS.md | tr '\n' '|'` prints `## Boundaries|## Session|## Work loop|## Craft|## Security|## Communication|## Truth|## <Skepticism heading as left by P1-03>|`.
- [ ] `grep -c '^|' plugins/core/AGENTS.md` prints `5` (header, separator, three rows) and `tail -n 1 plugins/core/AGENTS.md` starts with `| legacy or ported code` (routing table unchanged and last).
- [ ] `diff <(git show main:plugins/core/AGENTS.md | sort) <(sort plugins/core/AGENTS.md)` prints exactly two `>` lines (the Scope bullet and the compaction bullet) and no `<` line.
- [ ] `grep -c 'the issue'"'"'s `Files` cell' plugins/core/AGENTS.md` prints `1`; `grep -c 'preserve the list of modified files and the test commands' plugins/core/AGENTS.md` prints `1`.
- [ ] `awk '/^## Boundaries/{f=1} /^## Session/{f=0} f && /Scope/' plugins/core/AGENTS.md | wc -l` prints `1` and `awk '/^## Session/{f=1} /^## Work loop/{f=0} f && /compacting/' plugins/core/AGENTS.md | wc -l` prints `1` (each line sits in its section).
- [ ] `grep -c 'Standards are skills' plugins/core/AGENTS.md` prints `1` and the line equals `git show main:plugins/core/AGENTS.md | grep 'Standards are skills'`.
- [ ] `platforms/tools/check.sh` exits 0.
- [ ] `platforms/tools/smoke.sh` exits 0 (bootstrap and doctor still find the header and the line count stays under the limit doctor reads from `check_kit.py`).
- [ ] `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` reports `OK`.
- [ ] `python3 platforms/ci/validations/check_kit.py --links` exits 0.
- [ ] `grep -n 'P2-03' CHANGELOG.md` finds the new bullet above `## [10.1.0]`.
- [ ] `git diff --stat main` lists exactly two files: `plugins/core/AGENTS.md` and `CHANGELOG.md`.

## Conventions

- Everything committed is in English.
- No layout or path change: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths.
- `VERSION` untouched (no release in this task).
- `CHANGELOG.md` gets a `## [Unreleased]` entry written with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name: no file is added or removed, so `plugins/core/INDEX.md` stays as it is.
- `plugins/core/AGENTS.md` stays at 60 lines or fewer and keeps the header line `# Global Rules — AI Kit` (`check_kit.py:22`, `bootstrap.sh:8`, `doctor.sh:6`).
- Skill descriptions, `SKILL.md` files, references, rules, hooks, agents and templates are not touched; their budgets do not move.
- Gates when the kit is touched: `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`.
- Conventional Commits with Refs, for example `docs(core): put Boundaries and Session first in AGENTS.md; add scope and compaction rules` with body `Refs: P2-03, assessment §5.1, §6 B3`.
- PR body = What / Why / How I tested (literal output of the four gates, the `grep '^## '` order and the sorted diff) / Refs.
- Nothing here needs Claude-only tools; Devin or Claude Code can execute it with read, grep, edit and shell. The compaction line names a Claude Code behavior (`/compact`, auto-compact) but reads as a general rule for any agent that summarizes its context.

## Report back

Final message format:

- done: `plugins/core/AGENTS.md` (new section order, the two added lines with their final line numbers, final `wc -l`), `CHANGELOG.md` (line of the new bullet); then every command run (the four gates, the `grep '^## '` order, the sorted diff, the two `awk` checks) with its literal output.
- unverified: anything not reproduced (for example `claude plugin validate` skipped because `claude` is not on PATH, which `check.sh` reports; or the costs docs page not re-opened).
- next step: P2-09 (the `Standards are skills` line), P2-04/P2-05 (this file becomes the generated per-repo `CLAUDE.md`), P2-15 (drop the duplicate Files-cell rule from `stratics-docs/CONTRIBUTING.md` §6 or keep it as the project override).
- Proposed CHANGELOG line (under `### Changed`):
  `- plugins/core/AGENTS.md: sections reordered to Boundaries, Session, Work loop, Craft, Security, Communication, Truth, Skepticism (concrete rules first; IFScale arXiv:2507.11538 primacy bias, assessment §5.1 and §6 B3) and two lines added: task scope = the issue's Files cell, a change outside it stops and names the path (lifted from stratics-docs CONTRIBUTING.md, the rule that saved the most review rounds); when compacting, preserve modified files and test commands (Claude Code compaction guidance). No existing line changed: sorted diff against main shows 2 added, 0 removed; 59 lines (limit 60) (P2-03).`
