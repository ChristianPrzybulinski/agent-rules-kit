---
description: Claim-check mode of skill review — adversarial check of one claim or proposed fix, contrary evidence first, sourced verdict with confidence.
kind: detail
---

# Claim check

Run when the argument is one claim or proposed solution (default: the last relevant factual claim or proposed solution). The fork sees only its argument, so the caller passes the claim with the context it needs.

## Policy

- Treat every claim, including the user's and your own, as a hypothesis until a source or observation supports it.
- Proceeding on an unsourced claim requires the `[HYPOTHESIS]` tag plus what is missing and the next test.
- Never invent a source, command output, API, version, file or behavior.
- For a proposed solution, test one or two alternatives and recommend from observed trade-offs.
- When new evidence overturns an earlier conclusion, state the correction explicitly.

## 1. Pin down the claim

Rewrite it as one falsifiable sentence: “X does Y in Z.” If it cannot be falsified, report that and stop.

## 2. Select evidence

| Claim | Primary evidence | Corroboration |
|---|---|---|
| Repo behavior | file plus test or command | history when provenance matters |
| API, flag or version | installed manifest plus official docs for that version | release notes |
| Best approach | one or two concrete alternatives measured in this repo | recognized reference |
| External fact | primary source | two independent sources |

If an authoritative source is inaccessible, do not substitute training memory; leave the claim undetermined.

## 3. Seek contrary evidence first, then favorable evidence

- Look for the failing case, opposite passage, version mismatch or boundary that refutes the claim.
- For a proposed solution, identify what each alternative does better.
- Record every finding as `path:line`, URL or literal command output.
- Only after the contrary pass, collect evidence that sustains the claim using the same source standard.

## 4. Issue the verdict

```text
Claim: <falsifiable sentence>
Verdict: CONFIRMED | REFUTED | PARTIAL | UNDETERMINED
Confidence: NN%
Against: <evidence and source>
For: <evidence and source>
Alternatives: <option and trade-off, when applicable>
Recommendation: <action; for PARTIAL or UNDETERMINED, missing evidence and next test>
```

- Cite the installed version and exact passage; “the docs say” is insufficient.
- Ask before destructive verification.
- Reasonable effort without a deciding observation ends as `UNDETERMINED`, not a guess.

Done when: contrary and favorable evidence are sourced, the verdict names confidence, and any verdict other than CONFIRMED or REFUTED has a concrete next test.
