---
id: KIT-035
title: "Advisory GDScript mutation testing of changed, covered functions, with PIT's default operators"
status: done
confirmed: "2026-11-10 (owner, ub-mode evaluation decisions D3 and D5 in the chat of the ub-mode evaluation session; implementation prompt launched 2026-11-11)"
issue: "#137"
pr: "#192, #195, #196, #200, #218"
---

# KIT-035 — Advisory GDScript mutation testing of changed, covered functions, with PIT's default operators

Compacted on 2026-11-16 (#291) to the problem, the decisions, the outcome and the numbers behind them. Every decision,
measurement table and proof run is in the full record at `cf087f4`
([KIT-035-gdscript-mutation.md](https://github.com/ChristianPrzybulinski/agent-rules-kit/blob/cf087f4a8017f1a00e9ac57f5f39b21a6c854c51/docs/features/KIT-035-gdscript-mutation.md); `git show cf087f4:docs/features/KIT-035-gdscript-mutation.md`).

## Problem and evidence

The owner's ub-mode evaluation (2026-11-10, `PROPOSAL-UB-MODE-2026-11-10.md` row 29 and § 5) set two rules: the kit
builds its own GDScript tools (D3) and gives GDScript every check Java has (D5). Facts at kit `49b2137`,
stratics-client `f98e0091` and stratics-server `5bce89c2`:

- [FACT] the same rule had a mutation gate in Java and none in GDScript: skill `testing` asked domain rules for
  "mutation score ≥80%" and `pitest-maven` gates ≥80 % in `domain`, while gdUnit4 has no mutation support.
- [FACT] the server pins PIT 1.30.0 and names no `<mutators>`, so the Java gate runs PIT's unnamed default set
  (`Mutator.newDefaults()`: six operators plus five typed returns), not the named group `DEFAULTS`.
- [FACT] the cost was unknown (one headless Godot run per mutant, a hypothesis until measured), and mutating only
  covered lines needs KIT-034's coverage.

## Change

`platforms/tools/gd_mutation.py`, advisory; its module docstring holds the operator mapping and the statuses, and its
row in `platforms/tools/README.md` every flag. One mutant per place a PIT default operator applies, one edit that keeps
every line number and parses again; `--base` narrows it to changed functions, and with `--coverage` (KIT-034's JSON) a
mutant on an uncovered line is "no coverage" without a run. It reuses `gd_coverage.py`'s copy and runner, with an APFS
clone per worker, the suites that name the file, an unmutated run per selection that must count, and a timeout of 10 ×
that run plus `--timeout-constant` (default 30 s). Invalid mutants stay out of the score; a mutant whose write or run
raises is "not run", exit 2.

- Cache (T5): killed, survived and invalid results are kept under a hash of the function's text and its selected test
  files, so a second run with nothing changed starts no Godot; `--no-cache` runs every mutant.
- Workers (T6): `--workers N` is an upper bound. Every Godot run starts only while fewer than 2 gate runs hold the host
  (the review loop's own admission records), and a run beside another of ours only while the load is below the core
  count; after an hour of gate runs at the cap the rest are "not run".

T7 names the tool, `--coverage` and `--no-cache` in skill `testing` § 1 and `testable-game-logic.md`, with eval case
`testing-gdscript-mutation-command`. No CI or loop gate runs it.

## Decisions

- T1–T3: PIT's unnamed default set, because the Java gate runs it; a mutant that does not load stays out of the score,
  and none the return type cannot hold is generated (T1's `return null` in `-> String` exited 105 before any test);
  a red or empty unmutated run marks every mutant for the wrong reason, so it must count.
- Review of #192: "not run" with exit 2 for a raise, the host's failure, not the mutant's; a timeout constant of 30 s
  (PIT's factor-plus-constant shape; 30 s is a judgement), so a run that host load (5–20 during gates) slows does not
  count as detected.
- T5 and the review of #195: the key holds the function and its selected test files, since a new test can kill a
  survivor; only killed, survived and invalid are kept, since host load also decides "timed out".
- T6 and the review of #200: the load bounds only a second run at once (this host runs at 5–20 during gates on 10
  cores); gate runs come from the loop's admission records, after command-name lists missed entry points twice.
- 2026-11-13: the owner chose "Advisory only, close": no gate and T8 cancelled. The cost: no measured time or count of
  equivalent mutants; false survivors such as T3's lines 90, 107, 109 and 124 stay in the output as survivors.

## Measurements

- T1, stratics-client `f98e0091`: ten hand-picked mutants of `PackChoice.check` took 0.81–1.31 s each (mean 0.966 s);
  8 of the 9 valid ones were killed (88.9 %); M4 (`< 1` → `<= 1`) survived, a real gap, since no test uses a
  `pck_size` of 1; M10 (`return null` in `-> String`) did not compile (exit 105).
- T3, monorepo `ac649c10c`, `app/update/pack_choice.gd`: 100 mutants in 157 s (22 s import, mean 1.22 s per mutant,
  about one unmutated run each): 92 killed, 7 survived, 1 invalid, score 92.9 %; every T1 status the generator still
  makes came back the same. Of the 7 survivors, 3 are test gaps and 4 equivalent or out of the tests' reach.
- T5: the first run made 103 Godot calls in 142 s, the second, with nothing changed, none in 5 s, with the same 100
  statuses; about 1.6 KB per cached function, so the 5000-function cap is about 8 MB.
- T6, with the review loop running one gate at a load of 5.9–11.6 on 10 cores: `--workers 1` took 224 s and
  `--workers 4` 105 s (mutants 168.7 → 47.0 s), with the same 100 statuses and no start held.

## Proof

Each PR's gates exited 0 on its head: `check.sh` (also with `CI=1`), `smoke.sh`, `check_kit.py --links`, the validation
suite with `test_gd_mutation.py` unskipped (gdtoolkit 4.5.0), `gen_index.py --check`, `vendor.sh --check` and
`gitleaks`; each review fix showed its new tests failing without it, and T7 added its eval case (score 1.00, one run).
Exception: in the T6 review-fix run `smoke.sh` failed once beside a loop gate and passed alone right after (cause not
found). Commands and output: the full record.

## History

- 2026-11-10: confirmed (owner, ub-mode evaluation decisions D3 and D5); 2026-11-11: issue #137, T1 spike in #145.
- 2026-11-12: the owner approved T2 onward of KIT-034 and KIT-035 in chat ("Sim, KIT-034 primeiro"), KIT-035 after
  KIT-034 T4 merged (`86a4564`, #191). T2–T4 and the T3 measurement in #192 (merged as `af9bb69`), T5 in #195, T7 in
  #196 with KIT-034 T6, T6 in #200; each refers to #137 and leaves it open.
- 2026-11-13: done: the owner kept the tool advisory with no gate ("Advisory only, close") and cancelled T8 (time and
  false survivors over two loop batches); skill `testing` § 1 now says so (#218).
- 2026-11-16: compacted to problem, decisions, outcome and numbers (#291); the full record stays at `cf087f4`.
