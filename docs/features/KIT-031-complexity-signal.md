---
id: KIT-031
title: "An advisory script reports CRAP for changed Java methods and CC for changed GDScript functions"
status: done
confirmed: "2026-11-10 (owner, ub-mode evaluation decisions D2, D3 and D5 in the chat of the ub-mode evaluation session; implementation prompt launched 2026-11-11)"
issue: "#133"
pr: "#141"
---

# KIT-031 — An advisory script reports CRAP for changed Java methods and CC for changed GDScript functions

## Problem and evidence

The owner evaluated the ub-mode principles against the kit on 2026-11-10
(`/Users/christian/Developer/GitHub/PROPOSAL-UB-MODE-2026-11-10.md` § 3 row 26, § 4 and § 5 "KIT-030", which this
feature implements under its real id) and decided that the complexity signal is advisory on changed functions (D2),
that the kit builds its own script instead of installing `crapper` (D3), and that both languages get the same check (D5).
Facts re-checked at kit `49b2137`:

- [FACT] no complexity check exists in the kit: `git grep -n -i -E 'crap|cyclomatic|gdradon' 49b2137 -- plugins platforms`
  prints nothing. `plugins/dev-core/skills/code-standards/SKILL.md:31` limits only length: "Treat 20 lines as the
  target and 40 as the review threshold; split by behavior, not arbitrary chunks."
- [FACT] the completion report has no line for it: the template of
  `plugins/quality-core/skills/validate-implementation/SKILL.md` § 5 (lines 58–68) holds Target, Verdict, Gates,
  Reused, the criterion table, Unverified and Next step.
- [FACT] `gdradon` needs no new dependency: it ships with gdtoolkit, pinned at `gdtoolkit==4.5.0` in
  `platforms/kits/godot/requirements-gdtoolkit.txt:2` and in stratics-client's `requirements-gdtoolkit.txt`
  (`CHANGELOG.md:258` of stratics-client at `f98e0091`); `gdradon --version` prints `gdradon 4.5.0` on this machine.
- [FACT] `gdradon` line numbers do not match the source (report § 4: `_validate_message` reported at line 283, defined
  at line 619), and it numbers lines without the blank ones (a scratch file whose function sits at line 4 was reported
  at line 2), so the script joins its results to the source's own `func` spans by name.
- [FACT] stratics-server `pom.xml` at `5bce89c2` writes the JaCoCo XML in `verify` (execution `report`, lines
  225–230), and its `includes` (lines 211–215: `domain/**`, `features/*/domain/**`, `shared/**`) sit on the plugin
  configuration, so they apply to the report as well as to `check`; a changed method outside those packages is not in
  the report. This corrects report § 4, which places the includes only on the `check` execution.
- [FACT] the only JaCoCo XML on this machine (`stratics-server/target/site/jacoco/jacoco.xml`, written 2026-10-07)
  is stale; parsed by the new script from a copy, it holds 67 methods in 26 source files; 25 of the methods are below
  100 % instruction coverage and none is at CRAP ≥ 10. It proves the parser reads a real report, not anything about today's
  server.
- [FACT] the client today, measured by the new script in FILE mode on the 659 `.gd` files of `app/`, `features/`,
  `shared/`, `tests/` and `tools/` at `f98e0091` (read-only; 23.7 s wall clock by `/usr/bin/time`): "66 of 7367
  measured function(s) above target", the worst `app/network/network.gd _validate_message CC 212`,
  `features/world/editor/records/schema_values.gd _check_node CC 45` and `tests/support/fake_network.gd _answer CC
  33`. One file is not parsed: "gdradon: Cannot process file 'features/world/movement/remote_track.gd' due to
  exception: invalid syntax (<unknown>, line 9)". The count matches report § 4 (66 functions above 10 out of 7,367).

## Change

`platforms/tools/complexity.py` (new, stdlib only, Python 3.9+):

- Usage `complexity.py [--base REF] [--jacoco XML]... [--threshold N] [FILE...]`. Without FILE it measures the
  functions whose lines changed in `git diff -U0 <base>...HEAD` (default base `origin/main`); with FILE it measures
  every function in those files.
- Java: per method of a JaCoCo XML the build already wrote (default `target/site/*/jacoco.xml` up to two directories
  down), CC = `COMPLEXITY` missed + covered, coverage = `INSTRUCTION` covered / total, CRAP = CC² × (1 − coverage)³ +
  CC; it reports CRAP ≥ 10. A method's span runs to the line before the next method; a lambda shares the span of the
  method around it. Sources under `src/test/` are skipped.
- GDScript: it runs `gdradon cc` on the `.gd` files and reports CC > 10, joined by function name to spans found by
  indentation. A function whose coverage is known scores CRAP, so GDScript coverage (KIT-034) only has to fill it in.
- stdout holds one `path function CRAP 12.0` or `path function CC 12` line per finding, highest first; stderr holds
  the notices: "no JaCoCo report at …; CRAP not computed for N changed Java file(s); build the report first or pass
  --jacoco", "gdradon not available (pip install gdtoolkit); skipped for N .gd file(s)", a file not in the report, a
  file newer than the report, and the summary "N of M measured function(s) above target". A missing report never
  scores as 0 % coverage.
- Exit 0. With `--threshold N`: 1 when a reported value reaches N, 2 when a report or `gdradon` the change needs is
  missing. A bad ref exits 2.

`platforms/ci/validations/test_complexity.py` (new, 9 unittest cases): a fixture JaCoCo XML with six methods (CRAP at
100 %, 50 % and 0 % coverage, a lambda, one unchanged and one below target, plus a class without methods), a fixture
`.gd` pair and a stub `gdradon` that reports wrong line numbers, in a throwaway repo with the global Git config off.

`platforms/tools/INDEX.md` and `platforms/ci/validations/INDEX.md` gain one row each.

`plugins/dev-core/skills/code-standards/SKILL.md` (73 → 74 lines), § 3 gains: "- New or changed functions target
CRAP < 10 (Java) and CC ≤ 10 (GDScript); bring one above it down by splitting it, testing it or both (the one-call
`match` above is exempt). `python3 ~/.ai-kit/platforms/tools/complexity.py --base <base>` lists them; its output is
advisory."

`plugins/quality-core/skills/validate-implementation/SKILL.md` (75 → 77 lines), § 5: the template gains
"Advisory: <complexity.py lines, or its missing-input notice>" after `Reused:`, and the rules gain: "- When the change
touches `.java` or `.gd`, run `python3 ~/.ai-kit/platforms/tools/complexity.py --base <base>` on the clean checkout
after the gates (so a JaCoCo report is the one the gate just wrote) and copy its lines to `Advisory:`; they never
change the verdict."

Skill descriptions do not change, so the skill rows of the plugin `INDEX.md` files stay identical; each new eval case gains its line under `## evals/` there, because `check_kit.py` fails on an unlisted case (`platforms/ci/validations/check_kit.py:974`–`991`). New eval cases, none naming its skill:

- `plugins/dev-core/evals/code-standards-complexity-target` (a changed GDScript function of CC 12, measured with
  `gdradon cc`, is split or tested)
- `plugins/quality-core/evals/validate-implementation-complexity-advisory` (fixture: a Java change with no JaCoCo
  report; the report carries an `Advisory:` line and the verdict does not rest on it)

No CI or loop gate runs the script (D2); a gate waits for the false-positive rate of two loop batches.

## Proof

Run from the worktree root at `df7aa9e` on 2026-11-11 (the commits after it change only this document and
`docs/features/README.md`); every command exited 0:

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: "check: OK (14 plugins, 46 skills, 3 rules,
  22 templates, 23 indexes, 124 links, 25 hook cases)", then "✔ Validation passed" 15 times and no skip line.
- `bash platforms/tools/smoke.sh`: "smoke: OK (46 skills, app fallback, cleanup, symlink safety, manifests,
  sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
- `python3 platforms/ci/validations/check_kit.py --links`: "check: OK (14 plugins, 46 skills, 3 rules, 22 templates, 23
  indexes, 124 links, 25 hook cases)".
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: "4 commits scanned.", "scanned ~52221 bytes (52.22 KB) in
  54.2ms", "no leaks found".
- `python3 -B -m unittest platforms/ci/validations/test_complexity.py`: "Ran 9 tests in 3.186s", "OK".
- New eval cases, unverified: each ran as `claude plugin eval plugins/<plugin> --case '<name>' --runs 1 --ablation none
  --no-publish --trust-plugin` and stopped before any model turn with "exit 1: Not logged in · Please run /login";
  `claude auth status` prints `"loggedIn": false` on this host, inside and outside the Bash sandbox. Cases:
  `plugins/dev-core`: `code-standards-complexity-target`.
- New fixture eval cases, unverified: the same command with `--scaffold --allow-tools Bash Edit Write` stopped before
  any model turn with "the Docker (~/.docker, DOCKER_CONFIG) credential store on this machine holds a symbolic link
  inside it, so the Bash sandbox cannot reliably exclude it"; the links are Docker Desktop's own, in `~/.docker/bin`.
  Cases: `plugins/quality-core`: `validate-implementation-complexity-advisory`.

## History

- 2026-11-10: confirmed (owner, ub-mode evaluation decisions D2, D3 and D5).
- 2026-11-11: implementation prompt launched; issue #133.
- 2026-11-11: done in #141.
