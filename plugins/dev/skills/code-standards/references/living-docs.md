---
description: Documentation closure checklist for README, CHANGELOG, public APIs, decisions, debt, feature status and prose for people.
kind: detail
---

# Living documentation

An outdated document is worse than a missing one: the agent trusts it. Written artifacts are English, and every behavior change updates the doc **in the same PR**.

## Closing checklist (documentation Definition of Done)

| Changed... | Update |
|---|---|
| build/run/test command | the module's `README.md` + the repo's `AGENTS.md` |
| public Java API | Javadoc on the public class/method (the what + invariants; do not repeat the signature) |
| exported GDScript/autoload script | `##` docstring above `class_name`, `@export`, signals |
| user-visible behavior | `CHANGELOG.md` `Unreleased` section |
| client↔server contract message | protocol doc + example + `protocol_version` if incompatible |
| decision with trade-off | a decision record in `docs/spec/decisions/` (`DEC`, `DTEC`, `DGME` or `DPRO-nnn`, as the project numbers them; state `proposed` until approved) |
| feature status | status, history and frontmatter of `docs/spec/features/FEAT-xxx.md` |
| consciously assumed debt | `docs/spec/debts/DEBT-xxx.md` with a payment trigger |

## Javadoc / docstring

- Only on public API and non-obvious invariants. Getter, `record`, trivial override → no Javadoc.
- Content: purpose, pre/post-conditions, thrown exceptions, thread-safety when relevant. No `@author`, no date.
- A short example beats a paragraph.

## Module/project README

Purpose (2 lines) → prerequisites with versions → exact commands (build, run, test) → structure (5-10 lines) → where the rest lives (`docs/`). No framework tutorial; remove a stale command rather than keeping historical alternatives.

## CHANGELOG and release notes

Keep a Changelog. `## [Unreleased]` always present, under Added/Changed/Deprecated/Removed/Fixed/Security; a release moves it to `## [X.Y.Z] - YYYY-MM-DD`. Write the impact for the user, not the diff. Release notes and tag match `VERSION` and the SemVer policy (skill `git` § 5).

## Prose for people

For README narrative, reports, release notes, e-mail and team messages:

- Put the conclusion before its justification and use concrete subjects; match terminology to the reader (exact mechanism for technical readers, effect before mechanism for product readers).
- Preserve uncertainty; never invent examples, names, numbers or anecdotes for fluency.
- Cut AI clichés and filler: "it is important to note", "worth highlighting", "in summary", decorative triads ("fast, secure and efficient"), bold on half the words, a list where a paragraph suffices, closing with a rhetorical question or an offer of help, unmeasured "robust", "scalable" or "seamless"; and the structural tells: a "not X but Y" whose X nobody claimed, a "no X, no Y, no Z" list, a run-up sentence before the point, a one-line closer that repeats the paragraph. After rewriting, check that no fact, number, name or quote changed.
- Governed text (specs, CHANGELOG, commits, comments, `AGENTS.md`, skills, protocol contracts) follows its template and schema, keeps `[FACT]`, `[DECISION]`, `[PROPOSAL]`, `[HYPOTHESIS]` and `[BLOCKER]`, and never compresses structural repetition; inside a technical answer, a governed passage is still emitted in its final format.

## Condition → action

- PR ready → run the checklist above; an applicable item without an update → PR is not ready.
- Before closing → search for the old command, name or version, resolve relative links and run the documentation/project checks; grep or run every command, flag, path and symbol the changed text names, and replace a count that will drift (tests, rows, files) with the command that derives it.
- Doc contradicts code → code wins; fix the doc in the current PR (or open a `DEBT` if it's large).
- Long chat explanation of how something works → candidate for `knowledge/` or `docs/`; do not leave it only in the conversation.
