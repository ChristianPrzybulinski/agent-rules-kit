---
name: tokens
description: Response register for code, e-mail, reports, README and governed docs. Use when writing long answers or text for humans. Not for doc policy (skill update-docs).
triggers:
  - user
  - model
allowed-tools:
  - read
---

# Tokens and Communication

## 1. Classify before writing

Choose one register: technical, human-facing, or governed. Read only the material needed for the requested outcome; broad reading needs a named hypothesis. Bulk output (long logs, wide searches, full test runs) goes to a subagent or a file; the main thread keeps the summary and the path. A register sets density, never language or format: the conversation stays in the language the repo's `AGENTS.md` sets, and governed passages keep their template (§4), so there is no session-wide compression mode to request or remember.

## 2. Use the technical register

For code, debugging, logs, refactors, scripts and CLI work:

- Lead with code, diff or command; follow with at most three prose lines.
- Put the worst literal failure first.
- Preserve paths, commands and error text byte-for-byte.
- Use the smallest useful snippet; do not repeat the request or narrate a feature tour.

Return to full prose for security warnings, irreversible actions, payments, migrations, force-pushes, or multi-step instructions that become ambiguous when compressed.

## 3. Use the human-facing register

For e-mail, reports, team messages, narrative README text and requested explanations:

- Put the conclusion before its justification and use concrete subjects.
- Preserve uncertainty; do not invent examples, names, numbers or anecdotes for fluency.
- Match terminology to the reader: exact mechanism for technical readers, effect before mechanism for product readers.
- Cut AI clichés: "it is important to note", "worth highlighting", "in summary", decorative triads ("fast, secure and efficient"), bold on half the words, a list where a paragraph suffices, closing with a rhetorical question or an offer of help.
- Remove filler and unmeasured claims such as “robust”, “scalable” or “seamless”.

## 4. Preserve governed documents

For `docs/spec/**`, `CHANGELOG.md`, commit messages, comments, `AGENTS.md`, skills and protocol contracts, follow their template and schema. Keep `[FACT]`, `[DECISION]`, `[PROPOSAL]`, `[HYPOTHESIS]` and `[BLOCKER]`; do not compress structural repetition.

## 5. Handle mixed output

Apply the technical register to the surrounding explanation, but emit any DEC, spec, CHANGELOG or other governed passage in its final governed format.

## 6. Close

End technical work with: done, unverified, concrete next step. Ask one focused question with two to four options when ambiguity blocks progress.

Done when: one register governs each passage, exact technical text is preserved, and governed content remains template-valid.
