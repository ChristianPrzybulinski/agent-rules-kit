---
description: Inputs, steps, expiry and promotion rules, check step, report, privacy and schedule of the session skill's audit mode (KIT-056).
kind: detail
---

# Cross-session audit

The `audit` mode turns many sessions into a short list of memory and rule actions. It reads the extract that `platforms/tools/session_audit.py` writes and the memory files, never a raw transcript.

## Inputs

- The newest `extract-*.json` in `${XDG_STATE_HOME:-~/.local/state}/ai-kit/session-audit/`. `refresh.sh` refreshes it when its stamp is 7 or more days old (`AI_KIT_SESSION_AUDIT=0` turns that off); when it is missing or older, run `python3 ~/.ai-kit/platforms/tools/session_audit.py --if-older-days 7`.
- Extract fields: `owner` (correction excerpts), `kit` (`Kit [PROPOSAL]` blocks), `errors` (normalized tool errors in 2 or more sessions), `memory` (entries cited, read and written, by session count) and `guard` (blocked destructive commands; `rm -rf` and `find -delete` split into `temp` and `other` targets).
- Each Claude memory folder (`~/.claude/projects/*/memory/` with its `MEMORY.md` index) and the `AGENTS.md` of every repository the excerpts name.
- To skip a session, add its id prefix (8 or more characters) or a substring of its Claude title or Codex thread name to `exclude.txt` in the state folder. `keywords.txt` there adds personal-topic words: `word`, or `word: confirm, confirm` for a word that also has a work meaning; a change re-checks the sessions of the kept extracts from their first line, and drops a kept session whose transcript is gone. Both files also reach kept sessions whose transcript is gone; Codex files wait for a later run while their titles cannot be read (`codex_deferred`).

## Steps

1. Classify each memory entry as active, expired, stale (a dated snapshot, or a fact the code now contradicts), duplicate (the rule already lives in a skill or an `AGENTS.md`) or contradicting another entry.
2. Find recurring failures: an owner correction, an error or a guard block in 3 or more sessions. Read the cited excerpts, not whole transcripts.
3. Check: re-verify every claim the report relies on with a command or a file read before the user sees it; the code wins over memory. A claim nobody checked is tagged `[HYPOTHESIS]`.
4. Write the report, then act within the rules below.

## Rules

| Case | Action |
|---|---|
| Entry limited to one night, batch or session, dated 7 or more days ago | expired: move it to `memory/archive/` and drop its `MEMORY.md` line, without asking |
| "until further notice", "standing" or no end date | active, whatever its age |
| Dated snapshot next to a durable how-to | rewrite list: propose keeping the durable part |
| Same lesson in memory and in a skill or an `AGENTS.md` | propose deleting the memory copy or shrinking it to a pointer |
| Rule for a whole repository, cited in 5 or more sessions in one week | promotion: a PR to that repository's `AGENTS.md`, after the user's yes |
| Lesson that holds in 2 or more repositories, or that an `AGENTS.md` line failed to prevent | a `Kit [PROPOSAL]` block (`kit-proposal.md`), after the user's yes |

Anything else (merge, rewrite, archive of a non-expired entry) waits for the user's yes. Once a lesson is promoted, its memory entry shrinks to a pointer or is deleted.

## Report

- One line per action: claim · evidence (extract field and session count, or file and line) · checked by (command or file) or `[HYPOTHESIS]`. Sort by citing sessions, highest first.
- Sections: archived (done, restorable), rewrite list (waiting for the yes), promotions, kit proposals.
- Save it as `report-YYYY-MM-DD.md` with mode 0600 in the state folder, and give the user the summary in chat.

## Errors the checks caught in the first runs

A "leaked secret" that a command disproved, an active authorization labeled stale, a pattern with 1 real instance, an overcount of sessions, and a bare personal keyword that skipped work sessions. Step 3 exists for these.

## Privacy

- Nothing from a transcript enters a repository. A promoted rule is written fresh, in the target file's words.
- The report quotes at most one excerpt of 12 words or fewer per theme, and names no amounts, names, account data or home paths. Never print a secret value, redacted or not.

## Schedule

A weekly Claude desktop scheduled task, the owner's local setup that the kit does not install, with the prompt `Run the session skill in audit mode on the newest cross-session extract.` On demand: `session audit`.
