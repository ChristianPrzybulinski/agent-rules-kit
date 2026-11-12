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
| Repeated behavior correction that no hook or check below can catch | rule change | the owning skill; `../../../AGENTS.md` only when no skill loads in time |
| A written rule broken again, or a mistake a command can detect | hook or check, shown firing on a deliberate repro | `../../../hooks/hooks.json` for a blocked command; the repo's gate script for a file check |
| Skill missed or mis-triggered | description change | that skill's frontmatter |
| Repeated artifact shape | template | `../../../templates/` |
| A rule or step cost time this session without changing the outcome: a re-run that found nothing new, two sources that repeat or contradict each other, a record nobody read, a line that steers nothing | simplification: remove, merge or narrow it | the file that owns the rule: kit skill, `../../../AGENTS.md`, or the repo's `AGENTS.md` |

Not a signal: a sandbox, permission or network error, the session's own shell slip, a one-time flake. Propose only what the next session on a fresh checkout would likely hit again; a new line must save more than it costs every session that loads it.

Before proposing, search `~/.ai-kit/plugins/*/skills`, `~/.ai-kit/plugins/*/rules`, `~/.ai-kit/plugins/guardrails/AGENTS.md` and the kit's closed issues (`gh issue list --state closed --search '<topic>'`). If the material exists, propose improving its reach instead of adding another file; a rejected proposal returns only with new evidence. For a simplification, the search lists every copy of the rule, so the proposal removes them all, keeps any control the step still provides, names what decides the case once the line is gone and checks why it exists (`git log -S '<text>'`). A newer model alone never removes a safety rule, permission boundary, gate or output contract.

## Proposal block

Use exactly:

```text
Kit [PROPOSAL] — <reference | skill | AGENTS.md line | hook or check | description | template | simplification>: <path>
Evidence: <turn, command or file from this session>
Shape: <one-line proposed change>
Cost: <files, VERSION and CHANGELOG impact>
```

Ask whether to do it now, defer it, adjust it or discard it.

## Close accepted work

An accepted proposal is a separate kit outcome and follows the kit's `CONTRIBUTING.md`, `platforms/tools/check.sh`, `CHANGELOG.md` and `VERSION`.
