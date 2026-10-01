---
name: simplicity
version: "1.0"
description: Simplicity ladder (pragmatic YAGNI) — when not to write code, when a port/interface is justified, how to mark deliberate simplifications and how to report what was skipped. Use when designing a solution, reviewing an oversized PR, choosing a dependency or deciding whether a test is needed. Do not use for domain test gates (skill testing).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
---

# Simplicity

The best code is the code not written. Lazy = efficient, not careless. The ladder shortens the **solution**, never the **reading**: understand the whole flow (every file the change touches) before choosing a rung.

## The ladder — stop at the first rung that holds

1. **Does it need to exist?** Speculative need → don't do it; say so in one line.
2. **Already in the repository?** Helper, type, pattern three files away → reuse. Reimplementing the neighbor is the most common error.
3. **Does stdlib solve it?** Use it.
4. **Native platform feature?** Database constraint instead of code; native Godot signal instead of a custom bus; `record` instead of a builder.
5. **Does an already-installed dependency solve it?** Use it. Never add a new one for what fits in a few lines.
6. **Does it fit in one line?** One line.
7. **Only then:** the minimum that works.

Two rungs work → the higher one. Two options of the same size → the correct one in edge cases (less code, not the more fragile algorithm).

## Rules

- No unrequested abstraction: interface with one implementation, factory of a single product, config for a value that never changes, "for later" scaffolding.
- **Exception that justifies an interface (port)**: external I/O (database, network, clock, RNG, file), a real planned swap between implementations, or a domain boundary that must be tested without infrastructure. Outside that, concrete class.
- Fewer files wins. Deleting beats adding. Boring beats clever — clever is what someone deciphers at 3 a.m.
- Bug = root cause. Before editing, `grep` all callers; the fix at the common point is the smallest diff **and** the correct one.
- Complex request → deliver the simple version and question in the same turn: "I did X; Y covers it. Do you need the full X? Say so."
- Deliberate simplification with a known ceiling (global lock, O(n²) scan, heuristic) → comment `// simplified: <ceiling>; <when/how to evolve>`. Becomes a `DEBT-xxx` if the ceiling is on the roadmap's path.

## Never simplify

Validation at the trust boundary · error handling that prevents data loss · security and authorization · basic accessibility · what the user explicitly requested (insisted → build it, without re-litigating) · the **domain** (money, inventory, reward, battle): there the gates of the `testing` skill apply in full.

## Tests under the ladder

- Outside the domain: non-trivial logic leaves **one** executable check that fails if it breaks (one small `test_*`/`@Test`). No per-function suite, no ahead-of-time fixture. Trivial (getter, 1:1 mapping, one-liner) is not tested.
- Inside the domain: the ladder does not apply to tests.

## Output

Pattern: `[code] → skipped: X; add when Y.` If the explanation grew bigger than the code, delete the explanation. An explicitly requested explanation (report, walkthrough) is not debt — deliver it whole.
