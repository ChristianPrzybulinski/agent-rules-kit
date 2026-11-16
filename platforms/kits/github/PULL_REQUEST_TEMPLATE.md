## What

<!-- 1-3 sentences: what changes and for whom. -->

## Why

<!-- Problem/value. Link to the FEAT/issue if any. -->

## Red

<!-- The new test and its failing line on the code before the change, as run; or the exception:
     `characterization: ...` or `manual: <check>, no honest test because ...`. -->

## How I tested

<!-- Commands run + relevant output (paste, don't describe). -->

```text
$ ./mvnw verify
...
```

## Proof

<!-- One allowlisted command per line; the reviewer reads each line's result recorded for the head (CI or the project's gate record) and re-runs, once on a clean checkout, only a line with none. -->

```proof
```

<!-- Only when they apply: `## Files widened` (existing tests outside Files, `path`: why),
     `## Secrets to register` (name, where it lives, what it opens; never the value), the capture of a visual change. -->

## Checklist

- [ ] `CHANGELOG.md` updated (Keep a Changelog)
- [ ] `README.md` updated if the change is user-visible
- [ ] Javadoc/docstrings on new public API
- [ ] FEAT status left to the tooling (never typed by hand)
- [ ] Feature flag registered (if any)

Executor: provider=<claude|codex|devin|human> tier=<model or tier> session=<real session id>

Refs: FEAT-
