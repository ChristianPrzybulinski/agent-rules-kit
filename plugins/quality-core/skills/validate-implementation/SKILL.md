---
name: validate-implementation
description: Completion verdict against a request or FEAT. Use when asking “is it done?” or preparing a PR. Not for fixing failures (skill sdd-implement).
argument-hint: "[FEAT-xxx | spec path | description of what should be done]"
triggers:
  - user
  - model
agent: reviewer
context: fork
background: false
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Validate Implementation

## 1. Pin down the target

- For `FEAT-xxx`, read its acceptance criteria and linked `REQ-*` files.
- For a path or request, extract verifiable criteria; stop and ask for one to three criteria if none exist.
- Write the final criterion rows before inspecting the implementation.

## 2. Inspect what exists

- Run `git diff <base>...HEAD --stat` and inspect the changed files; report cited files absent from the diff.
- For each criterion, locate implementation, executable proof and required documentation.
- A criterion without an executable test or reproducible command is not met.
- Validate the pushed head on a clean checkout (`git worktree add --detach <tmp> <sha>`); local uncommitted state never counts. Re-run there every proof command the author's report or PR lists. A claimed result that no command reproduces there is unverified; one that fails there makes the verdict `NOT READY`.
- A proof must be able to fail. A gate that passes on empty input (zero tests, zero schemas) is not proof; show it failing on a broken case.

## 3. Run canonical gates

Read the repository's `AGENTS.md` and README for commands. Kit fallbacks:

| Stack | Gate |
|---|---|
| Java/Maven | `./mvnw -q spotless:check verify` |
| Godot | `godot --headless --path . --import`, then the boot-proof grep of the `--quit` log from skill `godot-standards` section 5 (`--quit` exits 0 after a `SCRIPT ERROR`), plus the project test runner |
| Docs/spec | `platforms/tools/check.sh` or project spec lint |

Capture the literal failing excerpt; never replace it with “some tests failed.”

## 4. Check closure records

Read the `living-docs` reference in skill `update-docs`. Check CHANGELOG, command-facing README changes, public API docs, FEAT status, DEC/DEBT, and an incomplete feature's flag.

## 5. Issue the verdict

```text
Target: <FEAT, path or request>
Verdict: READY | PARTIAL | NOT READY
Gates: <command> → OK | FAILED (<literal excerpt>)
| Criterion | Code | Test | Doc | Status |
|---|---|---|---|---|
| ... | path:line | path/command | path | met / missing / partial |
Unverified: <what and why>
Next step: <smallest action that changes the verdict>
```

- `READY`: every criterion is met and every gate passes.
- `PARTIAL`: at least one criterion is missing or partial while gates otherwise run.
- `NOT READY`: a gate fails or the target cannot be validated.
- An ambiguous criterion is a spec gap; route it to `sdd-clarify` rather than guessing.

Done when: every criterion has observed code, proof and documentation status, all gates have literal results, and the verdict follows the rules above.
