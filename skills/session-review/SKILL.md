---
name: session-review
version: "1.1"
description: Session closeout with evidence and one kit proposal. Use when work is delivered or a session closes. Not for handoff records (skill session-handoff).
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

## 1. Summarize the delivered outcome

- Re-read the actual diff, commands and outputs; do not reconstruct them from memory.
- Report in at most six technical lines: done with paths and verification, unverified claims, and one concrete next step.
- If work is committed or pending, invoke `session-handoff` first and point the summary to that record.

## 2. Look for a demonstrated kit gap

Use `read`, `glob`, `grep` and the session evidence to classify only observed signals:

| Signal | Candidate | Destination |
|---|---|---|
| External fact needed again | reference note | `../<owner>/references/` |
| Procedure repeated twice, or once with three corrections | skill change | `../<name>/` |
| Repeated behavior correction | rule change | `../../AGENTS.md` or the owning skill |
| Skill missed or mis-triggered | description change | that skill's frontmatter |
| Repeated artifact shape | template | `../../templates/` |

Before proposing, search `~/.ai-kit/skills`, `~/.ai-kit/rules` and `~/.ai-kit/AGENTS.md`. If the material exists, propose improving its reach instead of adding another file.

## 3. Decide whether to propose

- No observed signal → stop after the summary. Project-only discovery (critical constant, fragile convention) → propose one line for that repo's `AGENTS.md` on the spot; it is not a kit proposal.
- Several signals → choose the strongest; put the rest in the handoff as follow-ups.
- Never propose kit growth because it merely sounds useful.

## 4. Ask before editing

Use exactly:

```text
Kit [PROPOSAL] — <reference | skill | AGENTS.md line | description | template>: <path>
Evidence: <turn, command or file from this session>
Shape: <one-line proposed change>
Cost: <files, VERSION and CHANGELOG impact>
```

Ask whether to do it now, defer it, adjust it or discard it. Do not edit the kit in the same turn as the proposal.

## 5. Close accepted work

An accepted proposal is a separate kit outcome and follows `../../docs/maintenance.md`, `../../platforms/tools/check.sh`, `../../CHANGELOG.md` and `../../VERSION`.

Done when: the evidence-based summary is delivered and either no proposal qualified or exactly one proposal received a user decision.
