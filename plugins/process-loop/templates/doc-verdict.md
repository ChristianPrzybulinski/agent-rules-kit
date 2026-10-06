# Verdict - <project>#<pr>

JSON that validates against `platforms/kits/review-loop/verdict.schema.json`. Post it with the loop tool; `head_sha` is the reviewed head.

```json
{
  "schema": "<project>-verdict/v1",
  "pr": "<repo>#<number>",
  "issue": 0,
  "head_sha": "[40 hex characters]",
  "verdict": "approved | flagged | needs-product | needs-human",
  "risk": "light | standard | full",
  "round": 1,
  "summary": "[one or two sentences; in a mixed round name the reviewed SHA]",
  "findings": [
    {
      "id": "F1",
      "severity": "blocking | required | info",
      "owner": "spec | apply | judgment",
      "claim": "[what is wrong, with path:line]",
      "fix": "[what to change]",
      "patch": "[unified diff or exact replacement text, when mechanical]",
      "close_when": "[one allowlisted command that exits 0 when closed; empty only for info]",
      "resolved_in": "[commit or PR that fixed it, for findings the architect fixed]"
    }
  ],
  "unblocks_on_merge": [0],
  "cost": {"model": "[model]", "usd": 0, "duration_s": 0}
}
```

Required: `schema`, `pr`, `issue`, `head_sha`, `verdict`, `risk`, `round`, `findings`; per finding `id`, `severity`, `owner`, `claim`, `close_when`. Delete the optional keys you do not use.
