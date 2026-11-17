---
name: sdd-release
description: "SDD step 9 — release validated FEATs: changelog, version, test deploy, acceptance, flag on. Use when FEATs are validated. Not for PRs (skill git)."
argument-hint: "[FEAT-nnn ... | version]"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - exec
---

# SDD 9 — Release

Process: `../sdd-constitution/references/sdd-process.md`. Takes FEATs that `sdd-review` validated to the product: one release, a test-environment deploy, the owner's acceptance and the flag turned on. Only this step sets a FEAT `delivered` under `release: manual`, and with it the NEEDs whose FEATs are all delivered. It does not review code (skill `review`) or close a FEAT (skill `sdd-review`).

Under `release: merge` (the default `sdd:` value) `sdd-review` already moved each FEAT and its NEED to `delivered`; this skill then runs only §§ 2–3 and § 7 when the project cuts a version, and changes no status.

## 1. Group the FEATs

- Resolve the project profile first (`../session/references/project-profile.md`): `spec_root` (every `docs/spec` here), `sdd` (`release`, `acceptance`), `changelog`, `release` and `ci`.
- List the candidates: `grep -l '^status: validated' docs/spec/features/*.md`. Group the ones the owner releases together; a FEAT behind a flag goes with its flag plan (§ 5).
- A FEAT whose `## Closure` is older than a later merge into the files it covers gets `sdd-review` again before it joins.

## 2. Write the changelog and version

- The release notes come from the grouped FEATs' CHANGELOG `Unreleased` lines; the version follows SemVer from what they change (skill `git` § 9).
- One release PR (`chore(release): publish X.Y.Z`), reviewed like any PR; the tag on the merge commit.

## 3. Deploy to the test environment and smoke

- Deploy the release commit with the project's deploy command (`AGENTS.md` § Commands or its release runbook) to the test environment, never to production first.
- Smoke: the main steps of every journey the group touches, expanded, on that environment, with literal output or a capture per step. A step that cites a process walks each step it cites: `TRACE checklist <spec_root> J-NN` lists them as `S<n> › PROC-nnn S<m>` rows (`A<k>` for an alternative on either side) with their rules and proofs.
- A touched process that no journey cites (`Cited by` is `—` in `traceability.md` § Processes: a server-only flow such as a scheduled job, or a tech process) is smoked by its postconditions: start it by its Trigger on that environment and record, per Postconditions bullet, the literal output or capture that shows it holds. A process is touched when a grouped FEAT's NEED lists it in `processes` or its steps cite a grouped FEAT's tasks (`traceability.md` § Tasks → processes).
- A failed smoke stops the release and files a class-A fix row (skill `review`, reference `coordination.md`).

## 4. Get the product acceptance

- The owner accepts on the test environment, as `sdd.acceptance` says: `captures` (the default) compares the captures with each UI REQ's mock (`evidence.visual_approval`); `playtest` is the owner playing the build, its dated line written as `../sdd-review/references/playtest.md` says. Record who, when and their words in the release PR or the FEAT's History. A greybox block's acceptance is its playtest line (`sdd.passes`), never captures.
- A refusal returns the FEAT: a task row for a defect, `sdd-clarify` for a wrong REQ. With the new row open, `TRACE status --write` moves the validated FEAT back to `in-progress` with a History line, and `sdd-review` closes it again once the row merges.

## 5. Turn the flag on, with a rollback plan

- Before the switch, write the rollback plan in the release PR: the flag off, plus any data step and its backup (`references/backup.md`).
- Turn each flag on in the test environment, smoke again, then in production. A flag on for more than 30 days creates a `DEBT-nnn` removal item (skill `sdd-implement` § 3).

## 6. Deliver

- `TRACE deliver <spec_root> FEAT-nnn --in X.Y.Z` per FEAT: `validated` to `delivered` with its History line, and each NEED whose listed FEATs are now all delivered and cover its REQs to `delivered`. In a FEAT with `## Versions` it moves the open block, whose heading names the version `release.versioning` gives (`0.3.0`, or `M5`); a later version of that use case is the FEAT's next block.
- Never set `status` by hand: `check_spec.py` requires the line `deliver` writes.

## 7. Route the feedback

- Each finding from acceptance, smoke or production goes to `sdd-intake` as a new NEED with `parent: NEED-nnn` (the delivered NEED) and the observation as Evidence; never as an edit to the frozen FEAT.

Done when: the release PR is merged and tagged, the smoke and acceptance are recorded, each flag is on with its rollback plan written, `deliver` moved every grouped FEAT (and its complete NEEDs), and every feedback item is a child NEED.
