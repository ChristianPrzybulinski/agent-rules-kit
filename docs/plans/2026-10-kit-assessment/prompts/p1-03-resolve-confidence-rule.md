# P1-03 — Resolve the 98% confidence rule in the global AGENTS.md

Phase: 1 · Repos: kit · Branch to create: fix/p1-03-resolve-confidence-rule from main · Depends on: none · Effort: ~1.5 h

## Goal

Replace the unverifiable "Confidence < 98% -> do not proceed" gate in the kit's always-on rules (`plugins/core/AGENTS.md`, section Skepticism) with rules an agent can check on its own output (a tag on unsourced claims, a one-line stated assumption, a single question with options), remove every numeric confidence threshold from `plugins/core/AGENTS.md` and from the policy and description of the `skeptic` skill, and keep the two rule sets consistent. Measurable result: `grep -n '98' plugins/core/AGENTS.md plugins/quality-core/skills/skeptic/SKILL.md plugins/quality-core/INDEX.md` prints nothing, the global rules state exactly one behaviour for ambiguity (decide when unblocked, ask one question when blocked), `plugins/core/AGENTS.md` stays at 57 lines (limit 60) and all gates pass.

## Why

- assessment §4.4, bullet Confidence: `AGENTS.md` section Skepticism says "Confidence < 98% -> do not proceed" while section Work loop says "Ambiguous but unblocked -> decide, state the assumption, proceed". The two rules collide; in practice the agent picks one at random. Current Anthropic guidance for autonomous agents is the second.
- assessment §6 item B1: replace section Skepticism with three verifiable lines (claim without a source is a hypothesis and is tagged as such; ambiguity that does not block -> decide, state the premise in one line, proceed; real blocker -> one question with 2-4 options and a recommendation). The number 98% goes: it is not measurable, and Anthropic recommends instructions the model can verify. assessment §8 puts B1 in week 1.
- assessment §5, table row on instruction files: Claude Code `memory` and `best-practices` pages ask that every line of an instruction file pass the test "would removing it cause an error?"; a threshold the model cannot measure fails that test, and when two lines contradict each other the model follows one arbitrarily (verify the wording against code.claude.com/docs/en/best-practices before quoting it in the PR).
- The contradiction is in three places today, not one: kit `plugins/core/AGENTS.md:15` (the gate), `:29` (decide and proceed) and `:51` ("Ambiguity -> one focused question", with no blocked/unblocked distinction). Measured with `grep -n 'Ambigu\|98' plugins/core/AGENTS.md`: 4 lines (13 is the section heading `## Skepticism (>98%)`, which step 1 also replaces; 15, 29 and 51 are the three rules).
- The `skeptic` skill repeats the gate in its description (`plugins/quality-core/skills/skeptic/SKILL.md:3`, copied verbatim into `plugins/quality-core/INDEX.md:7`) and in its policy (`:20`), verdict template (`:60`) and done criterion (`:69`). Measured with `grep -rn '98' plugins/quality-core/`: 5 lines, all in these two files (`grep -rn '98' plugins/` adds `plugins/core/AGENTS.md:13` and `:15`, 7 lines in total; nothing else in `plugins/` contains '98').
- Budgets measured today: `plugins/core/AGENTS.md` is 57 lines (`check_kit.py` `AGENTS_MAX_LINES = 60`, `platforms/ci/validations/check_kit.py:22`; assessment §5 says 58 in its table and prose, but `wc -l` and `splitlines()` both give 57 on `main` today: trust the command, not the assessment); the `skeptic` description is 159 chars (max 160, `:24`); all 43 skill descriptions sum to 6,803 chars (budget 7,200, `:25`); `SKILL.md` is 69 lines (max 80, `:26`).

## Current state

- kit `plugins/core/AGENTS.md:1`: `# Global Rules — AI Kit` (keep this header byte for byte).
- kit `plugins/core/AGENTS.md:13-17`:
  `## Skepticism (>98%)`
  ``
  `- Claim from the user, a doc, or my own → hypothesis until there is evidence. Confidence < 98% → do not proceed; say what is missing and how to get it.`
  `- User suggests a solution → seek evidence it is the best, list 1-2 alternatives with trade-offs, recommend. Never accept for the sake of accepting.`
  `- Disagree with evidence and hold the position until shown wrong or told "do it anyway". Found you were wrong → say "I was wrong about X" and correct going forward.`
- kit `plugins/core/AGENTS.md:29` (section Work loop):
  `- Ambiguous but unblocked → decide, state the assumption, proceed. Blocked → ask with a recommendation attached.`
- kit `plugins/core/AGENTS.md:51` (section Communication):
  `- End with: done · unverified · concrete next step. Ambiguity → one focused question with 2-4 options, not a questionnaire.`
- kit `plugins/quality-core/skills/skeptic/SKILL.md:3`:
  `description: Adversarial check of a claim or proposed fix. Use when the user suggests a solution, a claim is unproven, or confidence <98%. Not for bugs (skill investigate).`
- kit `plugins/quality-core/skills/skeptic/SKILL.md:20`:
  `- Require more than 98% confidence to proceed without a caveat; below that, state what is missing and the next test.`
- kit `plugins/quality-core/skills/skeptic/SKILL.md:56` (verdict block, stays): `Confidence: NN%`
- kit `plugins/quality-core/skills/skeptic/SKILL.md:60`:
  `Recommendation: <action; below 98%, missing evidence and next test>`
- kit `plugins/quality-core/skills/skeptic/SKILL.md:69`:
  `Done when: contrary and favorable evidence are sourced, the verdict names confidence, and any sub-98% gap has a concrete next test.`
- kit `plugins/quality-core/INDEX.md:7`:
  `| `skeptic` | Adversarial check of a claim or proposed fix. Use when the user suggests a solution, a claim is unproven, or confidence <98%. Not for bugs (skill investigate). |`
- kit `CHANGELOG.md:5`: `## [Unreleased]` exists with `### Added` (`:7`) and `### Changed` (`:11` once the plan branch is merged; `:10` on `main` before that, so locate the section by heading, not by number); append to `### Changed`.
- kit `CHANGELOG.md:275` mentions "Skepticism (>98%)" inside the 1.0.0 release notes: historical record, do not edit.

## Change

1. kit `plugins/core/AGENTS.md`: replace lines 13-17 (the whole Skepticism section) with this block. The file uses the arrow character in every condition -> action line; keep it so the section reads like its neighbours. The result is four bullets, not the three that assessment §6 B1 names: the "User suggests a solution" bullet stays because it is already verifiable (1-2 alternatives listed, a recommendation given) and it is the trigger the `skeptic` description names; the "Disagree with evidence" bullet stays as B1 asks:

```markdown
## Skepticism

- A claim without a source (the user's, a doc's, memory's or my own) is tagged `[HYPOTHESIS]` in the answer and never stated as fact. A source is a file read this session, a test or command output, or the official doc for the installed version.
- Ambiguity that does not block → decide, state the assumption in one line, proceed. A real blocker → one question with 2-4 options and a recommendation, never a questionnaire.
- User suggests a solution → seek evidence it is the best, list 1-2 alternatives with trade-offs, recommend. Never accept for the sake of accepting.
- Disagree with evidence and hold the position until shown wrong or told "do it anyway". Found you were wrong → say "I was wrong about X" and correct going forward.
```

2. kit `plugins/core/AGENTS.md`: delete the bullet that begins `- Ambiguous but unblocked → decide, state the assumption, proceed.` (line 29 before step 1, line 30 after it; match by content, not by number). The Skepticism section now carries that rule; a second copy would be the duplicate the best-practices test rejects. Section Work loop keeps its other three bullets.

3. kit `plugins/core/AGENTS.md`: shorten the bullet that begins `- End with: done · unverified · concrete next step.` (line 51 before step 1; back at line 51 once step 2 is done) to exactly `- End with: done · unverified · concrete next step.` The question format ("one question with 2-4 options") now lives in Skepticism; the old sentence said "ask" for every ambiguity, which was the contradiction in miniature.

4. kit `plugins/quality-core/skills/skeptic/SKILL.md`: replace line 3 with exactly:

```yaml
description: Adversarial check of a claim or proposed fix. Use when the user suggests a solution or a claim has no source yet. Not for bugs (skill investigate).
```

   (147 chars; contains the literal `Use when` that `check_kit.py:619` requires and the `Not for` that `:621` warns about when missing; total budget becomes 6,791 chars.)

5. kit `plugins/quality-core/skills/skeptic/SKILL.md`: replace line 20 with the line below. Line 19 (`- Treat every claim, including the user's and your own, as a hypothesis until a source or observation supports it.`) stays and already states the hypothesis rule, so the new line 20 only adds the tag and the consequence of proceeding:

```markdown
- Proceeding on an unsourced claim requires the `[HYPOTHESIS]` tag plus what is missing and the next test.
```

6. kit `plugins/quality-core/skills/skeptic/SKILL.md`: keep line 56 `Confidence: NN%` unchanged; replace line 60 with `Recommendation: <action; for PARTIAL or UNDETERMINED, missing evidence and next test>` and line 69 with `Done when: contrary and favorable evidence are sourced, the verdict names confidence, and any verdict other than CONFIRMED or REFUTED has a concrete next test.` The file stays at 69 lines.

7. kit `plugins/quality-core/INDEX.md`: replace line 7 with the new description, verbatim (the validator compares the table cell with the frontmatter character by character):

```markdown
| `skeptic` | Adversarial check of a claim or proposed fix. Use when the user suggests a solution or a claim has no source yet. Not for bugs (skill investigate). |
```

8. kit `CHANGELOG.md`, under `## [Unreleased]` / `### Changed`: one bullet. What: Skepticism section rewritten as verifiable rules (hypothesis tag, decide-and-state when unblocked, one question with options when blocked), numeric threshold removed from `AGENTS.md` and from the `skeptic` policy and description, duplicate ambiguity lines in Work loop and Communication folded into Skepticism. Why: `AGENTS.md:15` and `:29` contradicted each other (assessment §4.4, B1). Proof: the `grep -n '98'` and `grep -c 'Ambigu'` results from Acceptance criteria and the line count.

Files edited (all in the kit): `plugins/core/AGENTS.md`, `plugins/quality-core/skills/skeptic/SKILL.md`, `plugins/quality-core/INDEX.md`, `CHANGELOG.md`. No file is created or deleted.

## Out of scope

- Reordering the sections of `plugins/core/AGENTS.md` (Boundaries and Session to the top) and adding the compaction and task-scope lines: P2-03. Keep the current section order here.
- Any other skill's description or policy, skill merges and the extras plugin: P2-09, P2-10, P2-11.
- `plugins/core/skills/find-skills/SKILL.md:71` ("treated with skepticism" about GitHub stars) is a vendored heuristic, not a confidence gate: leave it.
- `CHANGELOG.md:275` (1.0.0 release notes naming "Skepticism (>98%)"): historical, untouched.
- `VERSION`, manifests, layout, install destinations, `check_kit.py` constants: untouched (P1-01 owns the freeze gate).
- Stratics repositories: none cites the 98% rule (`grep -rn '98%' --include='*.md'` in stratics-docs, stratics-client and stratics-server prints nothing); nothing to change there.

## Acceptance criteria

- [ ] `grep -n '98' plugins/core/AGENTS.md plugins/quality-core/skills/skeptic/SKILL.md plugins/quality-core/INDEX.md` prints nothing (exit 1).
- [ ] `grep -rn 'Confidence <\|confidence <\|sub-98\|below 98' plugins/` prints nothing (exit 1).
- [ ] `grep -c 'HYPOTHESIS' plugins/core/AGENTS.md` prints `1`; `grep -c 'HYPOTHESIS' plugins/quality-core/skills/skeptic/SKILL.md` prints `1`.
- [ ] `grep -c 'Ambigu' plugins/core/AGENTS.md` prints `1` (only the Skepticism line); `grep -n 'questionnaire' plugins/core/AGENTS.md` prints exactly one line, inside the Skepticism section.
- [ ] `head -1 plugins/core/AGENTS.md` prints `# Global Rules — AI Kit`; `grep -c '^## Skepticism$' plugins/core/AGENTS.md` prints `1`.
- [ ] `python3 -c "print(len(open('plugins/core/AGENTS.md').read().splitlines()))"` prints `57` (the validator counts with `splitlines()`, `check_kit.py:398`); any value <= 60 passes the gate but a larger one means a line was added that this task does not ask for.
- [ ] `grep -c 'Confidence: NN%' plugins/quality-core/skills/skeptic/SKILL.md` prints `1`.
- [ ] `grep -n '^description:' plugins/quality-core/skills/skeptic/SKILL.md | wc -c` prints `163` (147 chars + the 15-char `3:description: ` prefix + newline; the validator's limit of 160 chars corresponds to 176 here); the same text appears once in `plugins/quality-core/INDEX.md`: `grep -c 'a claim has no source yet' plugins/quality-core/INDEX.md` prints `1`.
- [ ] `python3 -c "import re,glob;print(sum(len(re.search(r'^description:\s*(.*)$',open(f).read(),re.M).group(1).strip().strip('\"')) for f in glob.glob('plugins/*/skills/*/SKILL.md')))"` prints `6791` (<= 7200; 6803 today; `check_kit.py` enforces the same budget with `DESCRIPTIONS_BUDGET = 7200` at `:25`, summing `len(description)` of each frontmatter at `:572-577` and `:639`).
- [ ] `wc -l plugins/quality-core/skills/skeptic/SKILL.md` prints `69` (<= 80).
- [ ] `grep -c 'Skepticism' CHANGELOG.md` is at least `4` (3 historical lines plus the new Unreleased bullet), and the new bullet sits above `## [10.1.0]`.
- [ ] Gates: `platforms/tools/check.sh` exit 0; `platforms/tools/smoke.sh` exits 0 and its last line starts with `smoke: OK` (the full line is `smoke: OK (43 skills, app fallback, cleanup, symlink safety, manifests)`, `platforms/tools/smoke.sh:492`); `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` ends with `OK`; `python3 platforms/ci/validations/check_kit.py --links` exit 0. If `check.sh` or `check_kit.py --links` fails only on `broken link` lines inside `docs/plans/`, report those lines verbatim as pre-existing and out of scope (the plan prompts link to files that later tasks create; P1-03 does not edit `docs/plans/`); any other failure blocks.
- [ ] If `claude` is in PATH, `check.sh` also runs `claude plugin validate` on every plugin; it must print no error for `plugins/core` and `plugins/quality-core`.

## Conventions

- Everything committed is in English; new prompt-level text uses plain ASCII punctuation, while the arrow and middle-dot characters already used by `plugins/core/AGENTS.md` are kept in that file for consistency.
- No layout or path change: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths.
- `VERSION` untouched (no release in this task).
- `CHANGELOG.md` gets a `## [Unreleased]` entry written with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name (a folder never has both): `plugins/quality-core/INDEX.md` already lists `skeptic`; only its description cell changes. `plugins/core/` has no index entry for `AGENTS.md` to update.
- Skill description 40-160 chars in the form "<what>. Use when <trigger>. Not for <neighbor> (skill <x>)." and copied verbatim into the plugin `INDEX.md` table; all skill descriptions together <= 7,200 chars (6,803 today, 6,791 after this task); `SKILL.md` <= 80 lines.
- `plugins/core/AGENTS.md` <= 60 lines and it keeps the header line `# Global Rules — AI Kit`.
- Conventional Commits with Refs, for example `fix(core): replace the 98% confidence gate with verifiable skepticism rules` and `Refs: docs/plans/2026-10-kit-assessment/prompts/p1-03-resolve-confidence-rule.md`.
- PR body = What / Why / How I tested (literal output of the grep commands, the line count and the four gates) / Refs; also tick the kit's `.github/PULL_REQUEST_TEMPLATE.md` checklist.
- The executor may be Devin or Claude Code; nothing here needs Claude-specific tools. `plugins/core/AGENTS.md` reaches the agents through the bootstrap symlinks, so no install step is needed after the edit.

## Report back

Final message in three blocks: done (the four edited paths; each command from Acceptance criteria with its literal result, including the `grep -n '98'` output, the 57-line count, the description total and the four gate outputs) · unverified (anything not run, for example `claude plugin validate` when `claude` is not in PATH) · next step (P2-03 reorders the sections of `AGENTS.md` and adds the compaction and task-scope lines; P2-09 consolidates overlapping skills). Also include the proposed one-line CHANGELOG entry, for example: `AGENTS.md` section Skepticism rewritten as verifiable rules (unsourced claim tagged `[HYPOTHESIS]`; unblocked ambiguity -> decide and state the assumption; blocker -> one question with 2-4 options), the 98% threshold removed from the global rules and from the `skeptic` policy and description, and the duplicate ambiguity lines in Work loop and Communication folded into Skepticism; evidence: `AGENTS.md:15` and `:29` contradicted each other (assessment §4.4).
