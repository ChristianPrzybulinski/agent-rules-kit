# Living documentation

An outdated document is worse than a missing one: the agent trusts it. Every behavior change updates the doc **in the same PR**.

## Closing checklist (documentation Definition of Done)

| Changed... | Update |
|---|---|
| build/run/test command | the module's `README.md` + the repo's `AGENTS.md` |
| public Java API | Javadoc on the public class/method (the what + invariants; do not repeat the signature) |
| exported GDScript/autoload script | `##` docstring above `class_name`, `@export`, signals |
| user-visible behavior | `CHANGELOG.md` `Unreleased` section |
| client↔server contract message | protocol doc + example + `protocol_version` if incompatible |
| decision with trade-off | `docs/spec/decisions/DEC-xxx.md` (state `proposta` until approved) |
| feature status | frontmatter of `docs/spec/features/FEAT-xxx.md` |
| consciously assumed debt | `docs/spec/debts/DEBT-xxx.md` with a payment trigger |

## Javadoc / docstring

- Only on public API and non-obvious invariants. Getter, `record`, trivial override → no Javadoc.
- Content: purpose, pre/post-conditions, thrown exceptions, thread-safety when relevant. No `@author`, no date.
- A short example beats a paragraph.

## Module/project README

Purpose (2 lines) → prerequisites with versions → commands (build, run, test) → structure (5-10 lines) → where the rest lives (`docs/`). No framework tutorial.

## CHANGELOG

Keep a Changelog. `## [Unreleased]` always present; a release moves it to `## [X.Y.Z] - date`. Write the impact for the user, not the diff.

## Condition → action

- PR ready → run the checklist above; an applicable item without an update → PR is not ready.
- Doc contradicts code → code wins; fix the doc in the current PR (or open a `DEBT` if it's large).
- Long chat explanation of how something works → candidate for `knowledge/` or `docs/`; do not leave it only in the conversation.
