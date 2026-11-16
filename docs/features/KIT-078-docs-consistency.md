---
id: KIT-078
title: "13.0.0 docs consistency: one review-bar home, boot proof, Migration heading, record statuses"
status: done
confirmed: "2026-11-16 (coordinator session \"Revisão de regras e skills\", under the owner's overnight autonomy: \"seja autônomo com toda liberdade e finalize o que falta\")"
issue: "#290"
pr: ""
---

# KIT-078 — 13.0.0 docs consistency: one review-bar home, boot proof, Migration heading, record statuses

## Problem and evidence

[FACT] The final read-only docs review of kit `main` `6c168c5`, before the 13.0.0 tag, found ten contradictions or
stale lines in text that consumers read or copy at their resync (#290 lists each with `path:line`):
- the review bar restated in four places, with blocker (c) differing between them;
- `review_rounds` with no stated purpose;
- three versus five trigger cases;
- a boot-proof grep narrower than `just boot` and CI;
- a stale KIT-069 sentence;
- removed skills cited in `[Unreleased]`;
- journeys named as a skill;
- merged records still `confirmed`;
- a consumer PR template that invited a full local verify;
- migrations stated inline instead of under `### Migration`.

## Change

1. Skill `review` § 4 is the single home of the bar. Reason (c) includes a secret or personal data exposed in code
   or logs. `review_rounds` (default 3, unchanged) is the escalation cap for a PR whose fix delta adds a new mechanism,
   here and in `sdd-constitution/references/sdd-parameters.md`.
2. Agent `reviewer` and `platforms/kits/github/REVIEW.md` point to § 4 with one sentence each.
3. `.github/CONTRIBUTING.md` states eight cases: five `trigger` cases and three `ready` behavior cases.
4. Rule `godot.md` states the boot proof once: `just boot`, or the import then a `--quit` log grep for
   `SCRIPT ERROR|Parse Error|Parser Error|Can't load script`. The `sdd-implement` godot reference and agent `reviewer`
   point to it.
5. `sdd-parameters.md` drops the "A step marked KIT-069 reads its key once that change lands" sentence and the
   "(KIT-069)" tags.
6. `CHANGELOG.md` `[Unreleased]`: the KIT-069, KIT-071 and KIT-068 lines that cited removed skills now name the final
   homes (`test-gates.md` § 3, no `guardrails:testing` preload, `godot/scenes-and-generated-files.md`).
7. `README.md`: "the `sdd-*` pipeline" no longer names journeys as a skill.
8. `docs/features/`: KIT-065 to KIT-076 are `done` in the frontmatter and the index. KIT-077 stays `confirmed`, with
   its status note in the body, since items 1–4 are open.
9. The consumer PR template (`platforms/kits/github/PULL_REQUEST_TEMPLATE.md`) drops "How I tested" for one line:
   "TDD loop run locally …; CI runs the rest". It also gains an optional `Evals:` line.
10. `CHANGELOG.md` `### Migration` gathers the inline migrations of KIT-066, 067, 068, 069, 070 and 072. Each entry
    keeps a one-line pointer.

## Proof

`python3 platforms/ci/validations/check_kit.py --links`; results in the PR.

## History

- 2026-11-16: confirmed (coordinator); issue #290. Done when its PR merges.
