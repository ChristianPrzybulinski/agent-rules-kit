---
name: skeptic
version: "1.0"
description: Adversarial verification of a claim (mine, the user's or a doc's). Seeks contrary evidence first, then favorable, and issues a verdict with confidence. Use when something "seems right" but was not proven, or when the user suggests a solution. Do not use to investigate a concrete bug (skill investigate) or for the general evidence policy (skill evidence).
argument-hint: "[claim to verify — default: last relevant claim]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - web_search
  - webfetch
---

# Skeptic — adversarial verification

Goal: replace "seems right" with evidence. Never conclude "true" without a verifiable source; never conclude "false" without trying to sustain the claim.

## 1. Pin down the claim

- Use `$ARGUMENTS` if provided; otherwise, the last factual claim or proposed solution in the conversation.
- Rewrite it as one falsifiable sentence ("X does Y in Z"). If it is not falsifiable, say so and stop.

## 2. Classify and choose sources

| Claim type | Primary source | Secondary source |
|---|---|---|
| Repo code behavior | read the file + run test/command | git log/blame |
| API, flag, lib/framework version | official doc of the installed version (`pom.xml`, `project.godot`, lockfile) | changelog/release notes |
| Best approach / architecture | 2+ concrete alternatives with trade-offs measured in the repo's context | recognized reference (book, official doc) |
| External fact | primary source (official site, RFC, spec) | 2 independent sources |

## 3. Seek CONTRARY evidence first

- Actively look for what would refute the claim: a failing test, a doc saying the opposite, an edge case, a different version.
- If the claim is a proposed solution, list 1-2 alternatives and what they do better.
- Record each finding with a source (path:line, URL, command output).

## 4. Seek FAVORABLE evidence

- Only after step 3. Same source requirement.

## 5. Verdict

Mandatory format (short):

```
Claim: <falsifiable sentence>
Verdict: CONFIRMED | REFUTED | PARTIAL | UNDETERMINED
Confidence: NN%  (≥98% required to proceed without caveats)
Against: - <evidence + source>
For: - <evidence + source>
Alternatives (if a solution): - <option> — <trade-off>
Recommendation: <what to do now; if <98%, what is missing to get there>
```

## Rules

- Do not count "the doc says" without citing the version and the passage.
- Do not count training memory as evidence.
- If verification requires running something destructive, stop and ask for authorization.
- If after reasonable effort nothing decides it, UNDETERMINED with the next concrete test that would.
