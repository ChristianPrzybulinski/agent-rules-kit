---
name: session
description: Session start, closeout and handoff. Use when starting, switching topic, closing, handing off or a second human joins. Not for parallelism (skill parallelize).
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

# Session

One skill, three modes: `start` opens and scopes the session, `review` closes it with evidence, `handoff <topic>` writes the continuation record.

## start

- Read the repository's `AGENTS.md` and README before broad exploration. Name one outcome for the session in a single sentence; if it cannot be named, ask before proceeding.
- For work spanning three or more files, crossing a layer, or containing ambiguity, propose planning mode before editing; for a one- or two-file mechanical change, proceed directly. Once a plan is approved, execute it without repeatedly reopening the plan.
- Before the first edit in a worktree or folder that a state or handoff file describes, read that file's top line `Writer: <session id> since <YYYY-MM-DD HH:MM>`. A line naming another session that is still running means stop and ask the user; never write beside it. Otherwise add the line before the first edit and remove it at close or handoff.
- A new topic mid-session is not silently added: ask whether to record it as a follow-up or close and start another session. Keep follow-ups, and each decision or correction with its reason when it settles, in the issue, PR or handoff record, not conversational memory.
- Exhausted-session signals: rereading already-read files, compressed context, an outcome already delivered, new unrelated requests, or roughly two hours of work. Suggest the handoff mode and a new session; continue only if the user chooses to.
- A second human joins the backlog: apply the condition → action rules in `references/two-humans.md`.
- Match the agent tier: suggest a smaller tier for a mechanical one- or two-file task with no decision or investigation; keep the current tier for architecture, investigation or risk.
- Close explicitly: run the review mode for the evidence summary and optional kit proposal; when work is pending or transferring to another agent, point to the issue or PR that records its state, and run the handoff mode only when none does.

## review

- Re-read the actual diff, commands and outputs; do not reconstruct them from memory. Report in at most six technical lines: done with paths and verification, unverified claims, and one concrete next step.
- If work is committed or pending, point the summary to the issue or PR that records its state; run the handoff mode first only when no such record exists. Cite the proof already recorded; re-run nothing just to restate it.
- List the worktrees this session created (`git worktree list`): remove only those whose branch is merged and whose tree is clean; report each one with uncommitted work and its dirty paths, and never remove it.
- In Devin Cloud, open Session insights for ACU size, issues and the improved prompt; treat "misleading guidance" as a skill-description defect.
- Look for a demonstrated kit gap, or a rule or step that cost time without changing the outcome, using the signal table in `references/kit-proposal.md`, then decide: no observed signal → stop after the summary; project-only discovery (critical constant, fragile convention) → propose one line for that repo's `AGENTS.md` on the spot, shaped `when <trigger>, do <action>, because <why>`; several signals → choose the strongest and put the rest in the handoff as follow-ups. Never propose kit growth because it merely sounds useful.
- Propose with the exact block in `references/kit-proposal.md`, which also holds what to ask and how accepted work closes.

## handoff

- Use `../../templates/doc-session-handoff.md`; the record must let a new session continue without this conversation.
- Save to the project-defined location or `docs/sessions/YYYY-MM-DD-topic.md`. Link specs, decisions, commits and reports instead of copying them.
- Before writing, run `references/handoff-record.md`: collect the observed state, name exactly one executable first task, and confirm completeness before closing.

## Rules

- The handoff record is written only when invoked as session handoff <topic>, or when the user asks for a handoff in words; a model-triggered load runs start or review and may only suggest handoff.
- Do not edit the kit in the same turn as the proposal.
- A dirty tree is a blocker: list every path.

Done when: one outcome stayed in scope, the review delivered verified status with unverified items and one next step, and any requested handoff record names one unambiguous first action.
