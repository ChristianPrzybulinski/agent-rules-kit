---
id: KIT-052
title: "check_kit.py fails a link that leaves its plugin and a skill description without 'Not for'"
status: confirmed
confirmed: "2026-11-12 (owner, kit review of 100 repositories, lane E brief relayed by the coordinating session)"
issue: ""
pr: ""
---

# KIT-052 — check_kit.py fails a link that leaves its plugin and a skill description without 'Not for'

## Problem and evidence

[FACT] The Codex and Claude marketplaces install from `./plugins/<name>` (`CONTRIBUTING.md` § Invariants), so a path
that leaves the plugin breaks once installed. At `1d1b55f`, `check_kit.py` failed such a path in backticks ("path
escapes plugin root") but checked a markdown link only for existence: a link to `../../../../docs/design.md` appended to
`plugins/core/skills/session/SKILL.md` passed. The new test fails against the `1d1b55f` script with
`AssertionError: 0 != 1`: the copy with both violations exits 0.

[FACT] At `1d1b55f` a description without `Use when` failed, but one without `Not for` only warned, and a warning does
not change the exit code. All 26 non-vendored skills carry both (`check: OK`, no `WARN` line). `Not for` names the
neighbor skill, the routing boundary that KIT-039 used to find duplicate skills.

Sources: lane E of the owner's kit review, items `JimLiu/baoyu-skills` and `earthtojake/text-to-cad` (a skill never
links outside its own package) and `mukul975/Anthropic-Cybersecurity-Skills` (`lint-descriptions.py`).

## Change

- `platforms/ci/validations/check_kit.py`: `escapes_plugin(owner, resolved)` serves the link loop and the backtick
  loop, so a markdown link in `plugins/<name>/` that resolves outside it fails with "path escapes plugin root". A
  non-vendored skill description without the literal `Not for` fails ("description lacks literal 'Not for'"); vendored
  skills stay exempt.
- `platforms/ci/validations/test_check_kit_readmes.py`: a copy of the kit with both violations fails with exactly
  those two lines.
- `CONTRIBUTING.md` § CI requirements names both checks.

## Proof

`CI=1 bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links` and
`python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`.

## History

- 2026-11-12: confirmed (owner, lane E of the kit review).
