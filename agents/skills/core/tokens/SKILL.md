---
name: tokens
version: "1.0"
description: The two communication lenses — compressed technical register (code, debug, logs) and text for people (e-mail, report, narrative README) — plus what to never compress and what is a governed document. Use for long responses, when writing text for humans, or when asked for more/less compression. Do not use for governed artifacts (specs and CHANGELOG follow their templates).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
---

# Tokens and communication

Token cost has two sides: what the agent **reads** (bigger) and what it **writes**. This rule covers both. Before answering, silently classify: technical, text for people, or governed document.

## Before answering (reading side)

- Understand the minimum needed to solve; do not solve what was not asked.
- Read only the relevant files; broad search requires a hypothesis.
- Do not repeat back to the user what they said nor the general rules (already in context).

## Technical lens — code, debug, logs, refactor, scripts, CLI

Pattern: `[code/diff/command] → skipped: X; add when Y.` At most three lines of prose after the code.

| Do | Don't |
|---|---|
| Short sentences; cut superfluous articles and connectors; fragments are acceptable | Greeting, "let's go", summary of what you'll do, "feature tour" |
| Bullets/table for lists; one level of indentation | Paragraph where a table fits; table where one line fits |
| Code, paths, commands, error messages **byte-for-byte exact** | Abbreviate paths, "simplify" an error message, paraphrase command output |
| Minimal snippet/diff | Rewrite a whole file for a local change |
| Worst fact first (literal failure in sentence one) | Bury the error after three paragraphs of context |

Levels, if the user asks: `lite` (full sentences, no filler — default), `full` (fragments, no articles), `ultra` (code only + one line). The level holds for the session until changed.

**Return to full prose**, even in compressed mode: security warning; confirmation of irreversible action (delete, force-push, migration, payment); multi-step sequence where a fragment creates ambiguity; the user repeated the question (a sign they were not understood).

## People lens — e-mail, report, message to the team, narrative README, requested explanation

Goal: read as written by someone who understands, for someone who will read it once. Without changing the content.

- Varied rhythm: short and long sentences alternating; a paragraph may hold one sentence.
- One idea per paragraph; the conclusion comes before the justification.
- Cut AI cliches: "it is important to note", "worth highlighting", "in summary", "in today's landscape", "robust/scalable/seamless" without a metric, decorative triads ("fast, secure and efficient"), bold on half the words, a list where a paragraph suffices, closing with a rhetorical question or an offer of help.
- Active voice; concrete subject ("the server rejects", not "is rejected").
- **No fabrication to sound natural**: no example, number, name or anecdote that is not in the source. Uncertainty stays marked as uncertainty.
- Calibrate by reader: technical team → exact terms; product/business → effect before mechanism.

## Governed documents — neither lens

`docs/spec/**` (FEAT, REQ, DEC, DEBT, spec.md), `CHANGELOG.md`, commit message, code comment, `AGENTS.md`/skill files, contracts (`protocol/`): follow template, schema and the `[FACT] [DECISION] [PROPOSAL] [HYPOTHESIS] [BLOCKER]` classification. Structural repetition there is deliberate and tool-validated — do not "humanize", do not "compress". Compressing a rules file to save tokens destroys the rule: forbidden.

## Mixed response (diff + decision)

Technical lens on the code; the passage that will become a document (DEC, spec, CHANGELOG) already comes out in the document's format. Never fragments in content that will be pasted into a governed artifact.

## Planning

- Internal TODOs to structure; do not expose trivial steps.
- Before a large feature, validate the approach in a few sentences (or a question with 2-4 options).
- End with: done · unverified · concrete next step.
