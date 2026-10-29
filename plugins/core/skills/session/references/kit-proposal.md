---
description: Kit-proposal signal table, the search-before-proposing step and the exact proposal block for the review mode.
kind: detail
---

# Kit proposal

## Signals

Use `read`, `glob`, `grep` and the session evidence to classify only observed signals:

| Signal | Candidate | Destination |
|---|---|---|
| External fact needed again | reference note | `../../<owner>/references/` |
| Procedure repeated twice, or once with three corrections | skill change | `../../<name>/` |
| Repeated behavior correction | rule change | `../../../AGENTS.md` or the owning skill |
| Skill missed or mis-triggered | description change | that skill's frontmatter |
| Repeated artifact shape | template | `../../../templates/` |
| A rule or step cost time this session without changing the outcome: a re-run that found nothing new, two sources that repeat or contradict each other, a record nobody read | simplification: remove, merge or narrow it | the file that owns the rule: kit skill, `../../../AGENTS.md`, or the repo's `AGENTS.md` |

Before proposing, search `~/.ai-kit/plugins/*/skills`, `~/.ai-kit/plugins/*/rules` and `~/.ai-kit/plugins/core/AGENTS.md`. If the material exists, propose improving its reach instead of adding another file. For a simplification, the search lists every copy of the rule, so the proposal removes them all and keeps any control the step still provides.

## Proposal block

Use exactly:

```text
Kit [PROPOSAL] — <reference | skill | AGENTS.md line | description | template | simplification>: <path>
Evidence: <turn, command or file from this session>
Shape: <one-line proposed change>
Cost: <files, VERSION and CHANGELOG impact>
```

Ask whether to do it now, defer it, adjust it or discard it.

## Close accepted work

An accepted proposal is a separate kit outcome and follows `docs/maintenance.md`, `platforms/tools/check.sh`, `CHANGELOG.md` and `VERSION`.
