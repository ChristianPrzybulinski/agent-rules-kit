---
id: KIT-060
title: "check_kit.py parses every kit shell script with bash -n"
status: done
confirmed: "2026-11-12 (owner, chat of the KIT-010 300000 session: \"Aprovo\")"
issue: "#211"
pr: "#212"
---

# KIT-060 — check_kit.py parses every kit shell script with bash -n

## Problem and evidence

[FACT] The kit's scripts start with `#!/usr/bin/env bash`, so on macOS they run under `/bin/bash` 3.2.57, the only
bash on the owner's `PATH`. That bash cannot parse a heredoc inside `"$(...)"` that holds an odd number of
apostrophes. During #207 (2026-11-12), the comment `# Bounds of Claude Code 2.1.287's settings schema` in the Python
heredoc of `platforms/tools/doctor.sh` made `bash -n platforms/tools/doctor.sh` stop with
`line 836: unexpected EOF while looking for matching` and `line 841: syntax error: unexpected end of file`.

[FACT] No kit gate would have caught it:

- `shellcheck` 0.11.0 exits 0 on a minimal reproduction (`x="$(python3 - <<'PY'` / `# Claude Code's schema` /
  `print("hi")` / `PY` / `)"`);
- `check.sh` did not parse the shell scripts.

Only a manual `bash -n` caught it before the merge. launchd runs the doctor every six hours, so a merged parse error
would break every run on the owner's machine. `CONTRIBUTING.md` already required scripts to parse under bash 3.2,
but nothing checked it.

[HYPOTHESIS] The Ubuntu bash 5 in `ci.yml` parses this construct, so the bash 3.2 trap is caught only by a local run on
macOS; a plain syntax error is caught on both.

## Change

- `platforms/ci/validations/check_kit.py` § 13 (Shell syntax) runs `bash -n` on every `*.sh` file of the kit outside
  `.git`, with the bash `shutil.which("bash")` finds. It is the bash `#!/usr/bin/env bash` runs. A parse error fails as
  `<path>: bash -n failed under <bash>: <first error line>`; a timeout (10 s) fails, and a missing bash warns. The
  summary line ends with `<N> shell scripts`.
- `platforms/ci/validations/test_check_kit_readmes.py`, which runs on a throwaway copy of the kit:
  - the passing copy reports one shell script per `*.sh`;
  - an unclosed `if` appended to `doctor.sh` fails with exactly one `FAIL:`;
  - on bash 3.x, `# Claude Code's schema` inserted into the doctor's heredoc fails with
    `unexpected EOF while looking for matching`.
- `CONTRIBUTING.md` § CI requirements names the apostrophe trap and the check.

## Proof

`python3 -B -m unittest platforms/ci/validations/test_check_kit_readmes.py` (5 tests); the two new tests fail with
`origin/main`'s `check_kit.py` (`AssertionError: 0 != 1`); `bash platforms/tools/check.sh`; `CI=1 bash
platforms/tools/check.sh`; `bash platforms/tools/smoke.sh`; `python3 platforms/ci/validations/check_kit.py --links`.

## History

- 2026-11-12: proposed at the end of the #207 session and confirmed by the owner in chat ("Aprovo"); implemented.
