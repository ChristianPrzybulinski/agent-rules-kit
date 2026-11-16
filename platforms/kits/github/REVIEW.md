# Review instructions

Review criteria for this repository, its quality definition of done. Read by Anthropic's hosted Claude Code Review (Team/Enterprise) and by any reviewer, human or agent. Each line ends with the agent-rules-kit rule, or skill section or reference, that holds it; `sdd-constitution` removes the lines a project gate enforces and lists that gate under "Do not report". Flag only gaps that affect correctness or the stated criteria; nits are optional. Report at most five nits; mention the rest as a count. Every finding cites `path:line` in the diff, not an inference from a name.

## The review bar

One review round per PR. The reviewer reads the diff against the acceptance criteria, plus the required gates' result recorded for the exact head: the CI checks, or the project's gate record where it runs no CI on pull requests. Only when no such result exists for that head does the reviewer run the gates, once, on a clean checkout; beyond that it runs nothing, except a targeted probe at a security boundary where untrusted input enters (`review` § 2).

A finding blocks only for one of the four reasons of `review` § 4, the bar's single home, which it names; every other finding, even one under a line below, goes to one follow-up issue.

A line ending in `<!-- grep: REGEX -->` (or `grep tests:` for test files only) is checked by `review_checks.py dod` on the diff's added lines; keep the regex narrow enough that a hit is worth reading.

## Scope
- The PR does one thing; Conventional Commit title; the body links the issue, FEAT, REQ or DEC it implements (`git` § 3, § 7).
- Changed paths stay inside the task's Files cell (or the issue's stated scope); anything else is a separate issue or DEBT; `## Files widened` adds only existing tests (`review` § 1, step 4).
- A PR that changes skills or rules cites, in its body, the eval command run before it was opened and the score (`sdd-implement` § 2).

## Correctness
- Each acceptance criterion has a named test; the sad path (invalid input, failure, timeout) is covered (`sdd-implement` reference `tdd.md` § 1-2).
- The new test failed before the change, as the PR's `## Red` shows, or the PR names its exception (`review` § 1, step 3).
- No focused, skipped or disabled test, and no assertion loosened without a reason in the PR (`review` § 2). <!-- grep tests: \.only\(|\bfit\(|\bxit\(|@Disabled|@Ignore|pytest\.mark\.skip|unittest\.skip|skip_test\( -->
- A proof must be able to fail: a gate that passes on zero tests or empty input is not proof (`review` § 2).
- A changed contract (schema, message, API) bumps its version and updates fixtures on every side (rule `protocol.md`; `sdd-plan` reference `contract.md` § 0).

## Architecture
- Dependencies point inward; domain code has no framework or engine import (`sdd-plan` reference `architecture.md` § 1).
- The server validates everything that changes state; the client only pre-validates UX (`sdd-plan` reference `security-design.md` § 2).
- No new pattern without a present problem; a trade-off is recorded as a decision (`sdd-plan` reference `architecture.md` § 5).

## Security
- No secret or personal data in code, logs or error messages; input validated at the boundary (`security` § 2; `sdd-plan` reference `security-design.md` § 3).
- Authorization checked per action and per entity on every touched endpoint or handler (`sdd-plan` reference `security-design.md` § 2).
- SQL is parameterized; no string-built queries (`sdd-plan` reference `security-design.md` § 3).
- Each sensitive change (endpoint, dependency, network message, CI or container file, hidden text) passes the checklist (`security` § 3).

## Docs
- CHANGELOG `Unreleased` entry; README when a command changed; doc comment on new public API (`sdd-implement` reference `living-docs.md`).
- Spec status follows the repository's rule (derived by tooling where the repository has it, never typed by hand); incomplete work recorded as DEBT or behind a flag (`git` § 2; skill `sdd-constitution`, process reference § Regimes).

## Do not report
- Anything CI already enforces: formatting, lint, type errors, secret scanning.
- Generated files (`*.uid`, `*.import`, `.godot/`, lockfiles, `target/`).
