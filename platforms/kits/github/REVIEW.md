# Review instructions

Review criteria for this repository, its quality definition of done. Read by Anthropic's hosted Claude Code Review (Team/Enterprise) and by any reviewer, human or agent. Each line ends with the agent-rules-kit skill section that holds its rule; `sdd-constitution` removes the lines a project gate enforces and lists that gate under "Do not report". Flag only gaps that affect correctness or the stated criteria; nits are optional. Report at most five nits; mention the rest as a count. Every finding cites `path:line` in the diff, not an inference from a name.

## Important means

A finding that breaks a criterion below, breaks behavior, leaks data or blocks a rollback. Style, naming and refactoring suggestions are nits at most.

## Scope
- The PR does one thing; Conventional Commit title; the body links the issue, FEAT, REQ or DEC it implements (`git` § 3, § 7).
- Changed paths stay inside the task's Files cell (or the issue's stated scope); anything else is a separate issue or DEBT (`review` § 2).

## Correctness
- Each acceptance criterion has a named test; the sad path (invalid input, failure, timeout) is covered (`testing` § 2).
- A proof must be able to fail: a gate that passes on zero tests or empty input is not proof (`review` § 2).
- A changed contract (schema, message, API) bumps its version and updates fixtures on every side (`protocol-contract` § 2).

## Architecture
- Dependencies point inward; domain code has no framework or engine import (`architecture` § 1).
- The server validates everything that changes state; the client only pre-validates UX (`security` § 4).
- No new pattern without a present problem; a trade-off is recorded as a decision (`architecture` § 5).

## Security
- No secret or personal data in code, logs or error messages; input validated at the boundary (`security` § 2, § 5).
- Authorization checked per action and per entity on every touched endpoint or handler (`security` § 4).
- SQL is parameterized; no string-built queries (`security` § 5).

## Docs
- CHANGELOG `Unreleased` entry; README when a command changed; doc comment on new public API (`code-standards` § 9).
- Spec status follows the repository's rule (derived by tooling where the repository has it, never typed by hand); incomplete work recorded as DEBT or behind a flag (`git` § 2; skill `sdd-constitution`, process reference § Regimes).

## Do not report
- Anything CI already enforces: formatting, lint, type errors, secret scanning.
- Generated files (`*.uid`, `*.import`, `.godot/`, lockfiles, `target/`).
