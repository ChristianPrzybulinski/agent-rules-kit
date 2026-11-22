---
description: Kit-proposal signals, duplicate search, the proposal block and direct GitHub filing at session closeout.
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

Before proposing, search `~/.ai-kit/plugins/*/skills`, `~/.ai-kit/plugins/*/rules`, `~/.ai-kit/plugins/guardrails/AGENTS.md` and the kit's open and closed issues (`gh issue list --repo ChristianPrzybulinski/agent-rules-kit --state all --search '<topic>'`). Reuse and link a matching open issue instead of creating a duplicate. If the material exists, propose improving its reach instead of adding another file; a rejected proposal returns only with new evidence. For a simplification, the search lists every copy of the rule, so the proposal removes them all, keeps any control the step still provides, names what decides the case once the line is gone and checks why it exists (`git log -S '<text>'`). A newer model alone never removes a safety rule, permission boundary, gate or output contract.

## Proposal block

Use exactly:

```text
Kit [PROPOSAL] — <reference | skill | AGENTS.md line | hook or check | description | template | simplification>: <path>
Evidence: <turn, command or file from this session; for a bottleneck or a fix, the why chain: symptom → whys with evidence → root cause>
Shape: <one-line proposed change>
Cost: <files, VERSION and CHANGELOG impact>
```

## File at closeout

For review or handoff, the global Session rule authorizes filing the chosen proposal without another confirmation. With no observed kit signal, create no issue. This permission covers only recording the proposal in `ChristianPrzybulinski/agent-rules-kit`, never implementation, a release or unrelated external actions; audit mode keeps its own approval rule.

- Use the block above as the issue body, with a concise `proposal: <change>` title. Publish only the minimal evidence safe for the public kit repository: omit private project details, personal data, credentials and raw transcripts. If the proposal cannot be explained safely, report filing as blocked instead of publishing it.
- After the duplicate search, create with an explicit repository: `gh issue create --repo ChristianPrzybulinski/agent-rules-kit --title 'proposal: <change>' --body-file <proposal-file>`. Write literal Markdown to the file; never interpolate session text into a shell command. For a fork, use its verified kit repository and the owner's authorization, never the current consumer project's remote by default.
- Confirm the returned issue with `gh issue view <number> --repo ChristianPrzybulinski/agent-rules-kit --json url,title,state` and include its URL in the closeout. A matching open issue needs only its link; do not add a duplicate comment.
- If search or creation fails, report the unfiled proposal and the error as unverified. After an ambiguous creation result, search for the exact title before any retry; never claim success without a confirmed issue. Missing access waits for the user; do not change credentials or create elsewhere.

The issue records a proposal, not approval to implement it. Ask about implementation only when taking up that separate outcome; an approval already given for the same scope stands.

## Close accepted work

An accepted proposal is a separate kit outcome and follows the kit's `.github/CONTRIBUTING.md`, `platforms/tools/check.sh`, `CHANGELOG.md` and `VERSION`.
