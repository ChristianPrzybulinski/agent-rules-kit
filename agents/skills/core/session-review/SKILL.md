---
name: session-review
version: "1.0"
description: "Closes a session — brief summary of what was done (done · unverified · next step) and a review of whether this session exposed a gap in the AI kit: a fact looked up externally, a procedure repeated, a behavior the user had to correct, a skill that misfired. Proposes at most one knowledge note, skill, AGENTS.md line, description fix or template, only with evidence from the session, and asks before anything is written. Use at the end of every session, once the requested work is delivered or the user closes it. Do not use for the handoff record (skill session-handoff) or for project-only discoveries (they go to the repo's AGENTS.md on the spot)."
argument-hint: "[empty | session topic]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Session Review

Closes the session with a short summary and, only when the session produced evidence for it, one proposal to improve the kit. It never edits the kit: a proposal is a question to the user.

## 1. Summarize (≤6 lines, technical register)

- Done: what changed, where (paths/commits), verified by which command.
- Unverified: claims left without command + output.
- Next step: one concrete action, or "none".
- Committed work or pending items → `session-handoff` first; the summary then links the record.

## 2. Review the session against the kit

Re-read what actually happened (turns, `git diff`, commands run) — not memory. A gap exists only when one of these was observed:

| Signal observed this session | Candidate | Where it would live |
|---|---|---|
| A fact (version, quota, flag, API) looked up externally, needed again | knowledge note | `agents/knowledge/<domain>/` |
| Same multi-step procedure run ≥2 times, or once with ≥3 user corrections | skill | `agents/skills/<type>/<name>/` |
| User corrected the same behavior more than once; a rule followed gave a worse result | AGENTS.md line or skill rule | `agents/AGENTS.md` (≤110 lines — name the line that gives way) or the skill's `references/` |
| A skill did not trigger when it should have, or triggered wrongly | description fix | the skill's frontmatter |
| A kit doc contradicted the code or the installed tool | record fix | the file that lied |
| An artifact written by hand that has a repeatable shape | template | `agents/templates/` |

Before proposing: `grep -ril "<keyword>" ~/.ai-kit/agents`. Found → the proposal is "existing X did not reach me; adjust its description/trigger", not a new file.

## 3. Decide

- No signal → the review ends at step 1. No "kit: nothing to propose" line; silence is the correct output.
- One-off signal (this project, this incident) → not the kit. Project-specific → the repo's `AGENTS.md`, proposed on the spot.
- Signal with evidence → at most **one** proposal per session (the strongest). Others become follow-ups in the handoff record.

## 4. Propose and ask

Exact shape, after the summary:

```
Kit [PROPOSAL] — <knowledge | skill | AGENTS.md line | description fix | template>: `<name or path>`
Evidence: <what happened this session — turn, command or file>
Shape: <one line — what the file/line would say; for AGENTS.md, which line gives way>
Cost: <files touched, VERSION bump, CHANGELOG entry>
```

Then one question with 2-4 options: do it now (only if the original outcome is closed; the kit becomes the outcome) · follow-up session · adjust the proposal · discard. Wait for the answer; write nothing in `~/.ai-kit` before it.

## Done when

- Summary delivered; and either no proposal (no signal) or exactly one proposal with evidence and the user's answer recorded (handoff record or follow-up).

## Rules

- Evidence from this session only; "it would be useful" without an observed signal is not a proposal.
- One proposal per session; the kit grows by need, not by ideas.
- Never edit `~/.ai-kit` in the same turn as the proposal — the user decides.
- An accepted proposal is a normal kit change: `docs/maintenance.md`, `check.sh`, CHANGELOG, VERSION.
