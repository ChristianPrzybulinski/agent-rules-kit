# Review checklist — PR #[n] — `FEAT-xxx`

Mark only what was **observed**. Non-applicable item: `n/a`. Unverified item: leave it empty and say why at the end.

## Scope
- [ ] PR does one thing; Conventional Commit title; body links FEAT/REQ/DEC.
- [ ] Nothing outside the FEAT's scope (tangents became an issue/DEBT).

## Correctness
- [ ] Each CA of the FEAT has a named test; sad path covered.
- [ ] Domain: JaCoCo 100% + PITest ≥80% green (output in the PR).
- [ ] Effect on inventory/economy/reward: idempotency and concurrency test.
- [ ] Contract changed → `protocol_version` and fixtures updated on both sides.

## Architecture
- [ ] Dependencies point inward; domain without framework.
- [ ] Server validates everything that changes state; client only pre-validates UX.
- [ ] No new pattern without a present problem; DEC if there was a trade-off.

## Security
- [ ] No secret/personal data; `vuln-scan` OK; input validated at the boundary; error doesn't leak internals.
- [ ] Log without password/token; per-action/entity authorization on touched endpoints.

## Docs
- [ ] CHANGELOG `Unreleased`; README if a command changed; Javadoc/docstring on new public API.
- [ ] FEAT status and `updated` updated; DEBT/flag recorded if incomplete.

## When receiving review comments (author)
- [ ] Each comment verified in the code before applying — reviewers err too; disagreement comes with evidence, not with "ok".
- [ ] A comment that reveals a gap in the FEAT/REQ → fix the spec, not just the code.
- [ ] No change outside the comment "while at it"; it goes to follow-up.

## Unverified
- [...]
