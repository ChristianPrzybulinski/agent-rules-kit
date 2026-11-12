---
id: KIT-041
title: "The dev and sdd eval cases load core, so skill-fired measures the skill"
status: done
confirmed: "2026-11-11 (owner's kit review, brief from the coordinating session \"Agents kit review e simplificação\")"
issue: "#156"
pr: "#158"
---

# KIT-041 — The dev and sdd eval cases load core, so skill-fired measures the skill

## Problem and evidence

[FACT] Since KIT-038 (#153, `02382ee`) the `dev` and `sdd` manifests declare `"dependencies": ["core"]`, and
`claude plugin eval plugins/<p>` loads only the plugin it targets. On 2026-11-11, Claude Code 2.1.287, case
`java-standards-no-field-injection` at `02382ee` (`git archive`), target `plugins/dev`, `--runs 1 --ablation none
--keep-temp`:

- The trace's init event lists no `dev:` or `core:` skill and reads
  `plugin_errors: [{"plugin": "dev@inline", "type": "dependency-unsatisfied", "message": "Dependency \"core\" is not
  installed — run `claude plugin install core`, or check that its marketplace is added"}]`.
- `skill-fired` reads "Skill called 0x (expected 1..∞)"; the two regex graders pass on the base model alone, so the
  case scores 0.67 and measures no skill. The same holds for every `dev` and `sdd` case: 5 of the 8 cases.

`check_kit.py` checks that the Claude `dependencies` and Devin `requiredPlugins` name the same set, so dropping the
dependency to make the eval load was not an option without the owner.

## Change

- The five cases under `plugins/dev/evals/` and `plugins/sdd/evals/` gain one frontmatter line in `prompt.md`:
  `plugins: [../.., ../../../core]`. Claude Code 2.1.287 reads a case's `plugins` list relative to the case folder;
  the list replaces the plugin it detects, so it names the case's own plugin (`../..`) and `core`. A plugin
  dependency given by bare name is satisfied by any loaded plugin of that name. The manifests do not change.
- The eval target becomes `plugins`. Each `plugins:` entry must lie under the target directory; with target
  `plugins/dev` the case fails to load with "plugins entry \"../../../core\" resolves to …/plugins/core, outside the
  containment root …/plugins/dev". The `core` cases keep no `plugins:` line and still resolve to `core` alone.
- `docs/maintenance.md` § Evals gains a bullet on the `plugins:` line and the local command becomes
  `claude plugin eval plugins --case '<name>' --runs 1 --ablation none --no-publish --trust-plugin --output-dir
  "${TMPDIR:-/tmp}/kit-evals"`. Without `--output-dir` the aggregate result lands in `plugins/evals/results/`, and
  `check_kit.py` exits 1 on it ("plugins/evals/INDEX.md: layout: required plugin path missing" and 4 more lines).
  § CI requirements names `claude plugin eval plugins`.
- `.github/workflows/evals.yml` drops the `core`/`dev`/`sdd` matrix for one job on `plugins`, states
  `--ablation with-without` (the default applies only when the target is a plugin), writes `--output-dir
  eval-results` and uploads one `evals` artifact (`results.json`, `report.html`). `--max-cost-usd 20` now caps the
  whole suite, not each of three jobs.
- `CHANGELOG.md` gains one line under `[Unreleased]`; `VERSION` does not change.

## Proof

- Eval runs on 2026-11-11, Claude Code 2.1.287, with this branch, target `plugins`, `--runs 1 --ablation none
  --no-publish --trust-plugin`:

  | Case | Plugins loaded | `skill-fired` | Score | Cost |
  |---|---|---|---|---|
  | `java-standards-no-field-injection` (`dev`), before at `02382ee`, target `plugins/dev` | none (`dependency-unsatisfied`) | 0x | 0.67 | $0.056 |
  | `java-standards-no-field-injection` (`dev`) | `dev`, `core` | 1x | 1 | $0.081 |
  | `protocol-contract-required-field-bumps-version` (`sdd`) | `sdd`, `core` | 1x | 1 | $0.089 |
  | `testing-empty-return-passes` (`dev`), two runs | `dev`, `core`; `plugin_errors` none | 0x | 0.5 | $0.098, $0.096 |

- `testing-empty-return-passes` now loads `dev:testing`; the kept trace shows the model calling
  `Skill {"skill": "dev:java-standards"}` for the JUnit review, so its grader, which matches only `testing`, counts
  0. That is a routing question between the two skill descriptions, not a loading failure, and stays out of this
  change.
- A free probe (`--max-cost-usd 0`, exit 2, `partialReason: "cost_ceiling"`, cost 0) with target `plugins`,
  `--tag ready --ablation with-without --scaffold` resolves `suite.plugins` to `core`, `dev` and `sdd`; with
  `--case session-closeout-no-rerun` it resolves to `core` alone.
- Not run: `review-claimed-proof-not-rerun` (`validate-implementation-claimed-proof-not-rerun` before KIT-039), which
  needs `--scaffold --allow-tools Bash Edit Write` and stops on this host because `~/.docker` holds a symbolic link
  (§ Evals). Unverified.
- Gates: see the PR body.

## History

- 2026-11-11: confirmed (owner's kit review, brief from the coordinating session); issue #156.
- 2026-11-11: done in #158.
