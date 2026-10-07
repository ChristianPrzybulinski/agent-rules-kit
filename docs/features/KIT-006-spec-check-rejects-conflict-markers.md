---
id: KIT-006
title: "check_spec fails on a merge-conflict marker left in a spec file"
status: done
confirmed: "2026-10-07 (owner, chat of the Stratics owner-decisions session)"
issue: "#79"
pr: "#80"
---

# KIT-006 — check_spec fails on a merge-conflict marker left in a spec file

## Problem and evidence

[FACT] On 2026-10-07 the Stratics architect session merged `origin/main` into its PR branch (stratics-docs#663). The
merge stopped on a conflict in `docs/spec/features/FEAT-053.md`, and the next command, `git add -A && git commit`,
committed the file with its markers (`<<<<<<< HEAD` on line 160, `>>>>>>> origin/main` on line 165, commit
`29b51732b`), and the branch was pushed. The spec gates then ran on that head and all passed: `check_spec.py`,
`spec_trace.py check` and `status`, and `row_lint.py check --changed`. The markers sat in the `## History` section,
which no check parses. The architect saw them only in the next `git log` and fixed them in a follow-up commit.

[FACT] With this change, `check_spec.py` run on that file reports `FEAT-053.md:160: merge-conflict marker '<<<<<<<'`
and `:165: … '>>>>>>>'` and exits 1. On stratics-docs `main` (201 artifacts, journeys included) it still prints
`spec: OK`, so the check gives no false positive there.

## Change

- `platforms/ci/validations/check_spec.py`: every Markdown file under the spec dir (journeys and guides included) is
  scanned for the start, base (diff3) and end markers git writes, `<<<<<<<`, `|||||||` and `>>>>>>>` at the start
  of a line, each followed by a space or the line end. A bare `=======` is not matched: it is also a Markdown setext
  heading underline, and a conflict always carries the start and end markers. A match fails the run with the file
  and line.
- `platforms/ci/validations/test_check_spec.py`: a conflict in a feature fails with its line; a base marker in a file
  without frontmatter fails; a setext underline, a nested quote and a marker inside inline code pass.

## Proof

`python3 -m unittest platforms/ci/validations/test_check_spec.py`; `bash platforms/tools/check.sh`.

## History

- 2026-10-07: confirmed and done (owner, chat of the Stratics owner-decisions session).
