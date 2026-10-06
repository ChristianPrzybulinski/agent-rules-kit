# P2-08 — Derive task and FEAT status from GitHub instead of editing it by hand

Phase: 2 · Repos: stratics-docs, stratics-client, stratics-server · Branch to create: feat/p2-08-derived-spec-status from main (stratics-docs; the two template follow-ups use chore/p2-08-pr-template-status in stratics-client and stratics-server) · Depends on: P1-08 (issue per task is the canonical flow) · Effort: ~8 h

## Goal

Make `tools/spec-trace/spec_trace.py sync-status` the only writer of the `Status` cell of every FEAT task row and of the FEAT frontmatter `status`, deriving both from GitHub (task issues titled `[FEAT-NNN Tn]` and the merged PRs that close them), regenerating `docs/spec/traceability.md`, refreshing the `spec.md` indexes, and opening a `chore(spec): sync status` PR from a scheduled workflow. Measurable result: the 128 `todo` / 3 `done` rows measured on 2026-10-06 become consistent with the 27 merged task PRs (FEAT-009 T2 and T3 at least move to `done`), `spec.md` no longer says that no development has started, and no PR template asks a human to edit a status by hand.

## Why

- assessment §4.6: 128 task rows `todo`, 3 `done`, while ~35 implementation PRs merged; FEAT-009 T2/T3 are `todo` with their PRs merged. Re-measured 2026-10-06: `grep -h '^| T[0-9]* |' docs/spec/features/*.md | awk -F' \| ' '{print $7}' | sort | uniq -c` gives `128 todo`, `3 done` (131 rows, 52 FEATs); `gh api "repos/ChristianPrzybulinski/<repo>/pulls?state=closed&per_page=100"` filtered on `merged_at` and a `^\[FEAT-` title gives 12 (client) + 15 (server) = 27 merged task PRs.
- stratics-docs `docs/spec/spec.md:13` still says "No development has started" and `:62` lists the in-progress FEAT as "none yet"; stratics-server#21 `[FEAT-009 T2] V3 characters migration` merged 2026-10-05 and stratics-client#21 `[FEAT-009 T3] Client CharacterCreate` closed docs issue #175 (`state_reason: completed`), yet `docs/spec/features/FEAT-009.md:92-93` hold `| todo |`.
- The rule contradicts itself: stratics-client and stratics-server `.github/PULL_REQUEST_TEMPLATE.md:35` ask for "FEAT status updated in `stratics-docs/docs/spec/features/`" while stratics-docs `CONTRIBUTING.md:168` forbids contributors to "edit `docs/spec/**`" (assessment §4.6).
- assessment §6 E1: derive status instead of typing it; merged PR -> task `done`; every task `done` -> FEAT `delivered`; generate `traceability.md` and the frontmatter in an automatic PR, with `spec_trace.py`, which already exists and already owns the generated matrix (DPRO-013 decision 3-4).
- assessment §7 N6: the executor's progress state must come from a machine-written source read next to `git log`, not from a hand-edited Markdown cell. P3-04 and P3-10 build on the derived status this task produces.
- Only 5 of 62 task issues are closed although 27 task PRs merged, so "issue closed" alone is not a reliable signal: the derivation must look at the linked PR's merge state (measured with `gh api "repos/ChristianPrzybulinski/stratics-docs/issues?state=closed&per_page=100"`, 2026-10-06).

## Current state

- stratics-docs `tools/spec-trace/spec_trace.py:1-13` (module docstring, the folder's only index; no README exists in `tools/spec-trace/` or `tools/`):
  `  spec_trace.py check             fail on a broken journey link, a FEAT<->REQ asymmetry or a stale matrix`
  `  spec_trace.py generate          rewrite docs/spec/traceability.md from the FEAT, REQ and journey files`
  `  spec_trace.py impact BASE HEAD  markdown: the journey steps and tests a BASE...HEAD diff touches`
- `tools/spec-trace/spec_trace.py:33` `TASK_ROW = re.compile(r"^\| (T\d+) \|")`; `:87-93` `task_rows(body)` keeps the whole row line per task id; `:402-411` `main()` registers the three sub-parsers; `:331-333` `git(root, *args)` is the only subprocess helper; `:268` `render_matrix(spec)` writes the matrix text.
- `tools/spec-trace/tests/test_trace.py:1` docstring, `:94` `class CheckTest`, `:185` `class ImpactTest`; 22 tests, run by `.github/workflows/docs-checks.yml:82` `run: python3 -m unittest discover -s tools/spec-trace/tests`.
- `docs/spec/features/FEAT-009.md:88` table header `| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Devin model | Wave |` (identical in all 52 FEATs); `:92` row `T2` and `:93` row `T3` end with `| todo | Low | swe | 1 |` and `| todo | Med | sonnet | 1 |`; `:106` `## History` is a dated bullet list ending `- 2026-10-05 tasks: T8 applies ...`; frontmatter `:4` `status: clarified`, `:15` `updated: "2026-10-05"`.
- `.github/spec-lint/schemas/feature.schema.json:11-14` status enum `["proposed", "clarified", "planned", "in-progress", "validated", "delivered", "cancelled"]`; the kit linter never reads task rows (no `todo`/`done` string in `.github/spec-lint/check_spec.py`).
- `docs/spec/spec.md:13` "... No development has started. Next step per FEAT: ..." (the sentence continues with the clarify flow); `:62` `5. The in-progress `FEAT` (status `in-progress`)` followed by "none yet"; `:68` "42 features `clarified` + 9 `proposed` candidates ..."; `:70-71` Features table header `| ID | Title | Milestone | Status | Scope |`, rows such as `:72` `| [FEAT-001](features/FEAT-001.md) | Preserve and complete the archive | M0 | clarified | docs |`; `:206` last decisions row `| [DPRO-013](decisions/DPRO-013-journey-layer.md) | Journey layer: ... | process | approved | 2026-10-05 |`.
- `.github/workflows/project-sync.yml:10-12` documents the secret: "Requires repo secret STRATICS_PROJECT_TOKEN" (a PAT with `project` + `repo` scopes, `:11`); `:15-21` fires on `issues: [opened, closed, reopened, labeled, unlabeled]` plus `workflow_dispatch`; `tools/project-sync/sync.py:36-37` `BLOCKED_LABELS = {"blocked", "needs-human", "needs-product", "gate:failed"}` and `PROGRESS_LABELS = {"review:pending", "status:in-progress"}`.
- `.github/workflows/docs-checks.yml:14-17` runs on `pull_request` and `workflow_dispatch` only; `:19-20` `permissions: contents: read`; `:10-11` comment "Project-owned spec checks (journeys, FEAT<->REQ symmetry, the traceability matrix, PR impact ...) live in tools/spec-trace/."
- `ops/review-loop/loop.py:47` `CLOSES_RE = r"Closes\s+" + re.escape(f"{OWNER}/{BACKLOG}") + r"#{n}\b"`; task PR bodies carry the line `Closes ChristianPrzybulinski/stratics-docs#<N>` (stratics-client#21 body line 16).
- `docs/spec/ARCHITECT.md:26-30` delta 1: one issue per task, title `[FEAT-NNN Tn] <first ~8 words of the Task cell>`, repo `stratics-docs` for every task issue.
- `.github/PULL_REQUEST_TEMPLATE.md:33` (stratics-docs), stratics-client `:35`, stratics-server `:35`: `- [ ] FEAT status updated in ...docs/spec/features/ (if any)`.
- `docs/spec/decisions/DPRO-014-derived-status.md` (new file); listed in `docs/spec/spec.md` § Decisions table after `:206`.
- `tools/spec-trace/tests/test_sync_status.py` (new file); discovered by the unittest command above, no index needed.
- `.github/workflows/spec-status-sync.yml` (new file); name it in the `docs-checks.yml:10-11` comment.
- `changelog.d/p2-08-sync-status.added.md` (new file); `changelog.d/README.md` names the fragment format, no index entry.

## Change

1. Read first, in this order: `tools/spec-trace/spec_trace.py` whole file, `tools/spec-trace/tests/test_trace.py`, `docs/spec/decisions/DPRO-013-journey-layer.md` § Decision 3-4, `docs/spec/ARCHITECT.md` deltas 1 and 7, `tools/project-sync/sync.py:1-37`, `docs/spec/decisions/DPRO-009-spec-governance.md` § Decision. Keep the kit copy `.github/spec-lint/**` untouched (DPRO-013).
2. In `tools/spec-trace/spec_trace.py` add the command `sync-status [--write] [--repo ChristianPrzybulinski/stratics-docs] [--date YYYY-MM-DD]` (default dry run prints the report and exits 0; `--write` edits files). Implementation, all in this file, under 220 added lines:
   - `gh_json(args, gh=run_gh)`: `subprocess.run(["gh", "api", *args], capture_output=True, text=True)`; the `gh` callable is injectable so tests never spawn a process. REST only: `gh api graphql` returns HTTP 403 inside Claude Code cloud sessions, so do not depend on GraphQL.
   - `task_issues(repo, gh)`: `gh api --paginate "repos/<repo>/issues?state=all&per_page=100"`, drop items with `pull_request`, keep titles matching `^\[(FEAT-\d{3,}) (T\d+)\]`; result `{ "FEAT-009 T3": {"number": 175, "state": "closed", "labels": [...]}}`. A second issue for the same task is an error that fails the run.
   - `linked_prs(repo, number, gh)`: `gh api "repos/<repo>/issues/<number>/timeline?per_page=100"`, keep events `event == "cross-referenced"` whose `source.issue.pull_request` is set, then `gh api "repos/<owner>/<pr-repo>/pulls/<n>"` and keep only PRs whose body matches `Closes\s+<repo>#<number>\b` (same regex family as `loop.py:47`); return `[{"ref": "stratics-client#21", "state": "closed", "merged": bool}]`. Verified 2026-10-06 that the timeline of docs#175 lists `stratics-client/pull/21`; verify against the GitHub REST docs for the issues timeline endpoint before relying on it in CI.
   - `derive_task_status(current, issue, prs)` with this order, first match wins:
     ```text
     no issue                                  -> keep current (report "no issue")
     any linked PR merged                      -> done
     issue has a label in BLOCKED_LABELS       -> blocked
     any linked PR open, or PROGRESS_LABELS    -> doing
     issue closed and nothing merged           -> keep current, WARN "closed without a merged PR"
     otherwise                                 -> todo
     ```
     Copy the two label sets from `tools/project-sync/sync.py:36-37` verbatim; do not import that module (a separate script with no `__init__.py`).
   - `derive_feat_status(current, rows)`: `cancelled` and `validated` are never changed by the sync (`validated` is the product sign-off of a stage exit: DPRO-013 decision 1 and DPRO-004 delivery by complete journey; a human sets it); every row `done` -> `delivered`; any row `done` or `doing` -> `in-progress`; else keep current. Document this in the DPRO (step 6).
   - `apply_status(path, text, changes, date)`: rewrite only the 7th cell of each changed row (`split("|")`, keep every other cell byte-identical), set frontmatter `status` and `updated: "<date>"` when a value changed, and append one History bullet `- <date> sync: status derived from GitHub (T2 todo -> done via stratics-server#21; T3 todo -> done via stratics-client#21).` listing every row changed in that FEAT. Running the command twice must produce no second diff.
   - After the FEAT files: write `traceability.md` with the existing `render_matrix`, and in `docs/spec/spec.md` rewrite the `Status` cell of the Features table rows (match `^\| \[(FEAT-\d{3,})\]\(features/`) and replace everything between `<!-- sync-status:begin -->` and `<!-- sync-status:end -->` with the list of `in-progress` FEATs (`- FEAT-009 Character and world entry (3/11 done)` or `- none`).
   - Report, one line per change, exit 0: `FEAT-009 T3: todo -> done (stratics-client#21)`, `FEAT-009: clarified -> in-progress`, `WARN docs#175 ...`; `--write` prints the number of files written.
   - Extend the module docstring with one line for the command and update the `argparse` help.
3. In `docs/spec/spec.md`: line 13 replace the two sentences starting "No development has started." and "Next step per FEAT:" with "Development runs by issue per task (ARCHITECT.md delta 1); task and FEAT status are derived from GitHub by `tools/spec-trace/spec_trace.py sync-status` (DPRO-014)."; replace line 62 with the marker block below; keep `:68` wording but let the counts be rewritten by the sync when they drift.
   ```markdown
   5. The in-progress `FEAT`s (status `in-progress`), derived by sync-status:
   <!-- sync-status:begin -->
   - none
   <!-- sync-status:end -->
   ```
4. Tests: `tools/spec-trace/tests/test_sync_status.py` (new), same fixture style as `test_trace.py`, fake `gh` returning canned JSON by URL prefix, at least these cases: merged PR -> done; open PR -> doing; `blocked` label beats open PR; closed issue without merged PR keeps `todo` and warns; task without issue keeps `done`; two issues for one task fails; FEAT with all rows done -> `delivered`; FEAT with one `doing` row -> `in-progress`; `validated` and `cancelled` FEATs untouched; History bullet appended once and the second run is a no-op; `spec.md` marker block and Features Status cell rewritten; row cells outside Status byte-identical.
5. New workflow `.github/workflows/spec-status-sync.yml` (daily schedule, issue events filtered like the `if:` of `project-sync.yml:36-40`, manual dispatch). Use `STRATICS_PROJECT_TOKEN`: a PR created with `GITHUB_TOKEN` does not trigger `docs-checks`, which the `protect-main` ruleset requires. Skeleton (fill the `if:` from project-sync and keep `timeout-minutes`):
   ```yaml
   name: spec-status-sync
   on:
     schedule: [{ cron: '17 6 * * *' }]   # daily; DPRO-011 CI economy
     issues: { types: [closed, reopened, labeled, unlabeled] }
     workflow_dispatch:
   permissions: { contents: read }
   concurrency: { group: spec-status-sync, cancel-in-progress: true }
   jobs:
     sync:
       runs-on: ubuntu-latest
       timeout-minutes: 10
       steps:
         - uses: actions/checkout@v7
           with: { token: '${{ secrets.STRATICS_PROJECT_TOKEN }}' }
         - uses: actions/setup-python@v7
           with: { python-version: '3.12' }
         - run: pip install pyyaml
         - env: { GH_TOKEN: '${{ secrets.STRATICS_PROJECT_TOKEN }}' }
           run: python3 tools/spec-trace/spec_trace.py sync-status --write
         - env: { GH_TOKEN: '${{ secrets.STRATICS_PROJECT_TOKEN }}' }
           run: |
             git diff --quiet -- docs/spec && { echo "nothing to sync"; exit 0; }
             git config user.name spec-status-sync && git config user.email spec-status-sync@users.noreply.github.com
             git checkout -B chore/spec-sync-status && git commit -am "chore(spec): sync status from GitHub" -m "Refs: DPRO-014"
             git push --force origin chore/spec-sync-status
             gh pr list --head chore/spec-sync-status --state open --json number --jq length | grep -q '^0$' \
               && gh pr create --title "chore(spec): sync status" --body-file .github/spec-sync-pr-body.md || true
   ```
   Never push to `main` (`protect-main`). Write `.github/spec-sync-pr-body.md` (new file, What / Why / How I tested / Refs: DPRO-014, with the proof block `python3 tools/spec-trace/spec_trace.py check`). Update the `docs-checks.yml:10-11` comment to name the new workflow; do not add jobs to docs-checks (it is PR + dispatch only by design, `:14-17`).
6. `docs/spec/decisions/DPRO-014-derived-status.md` (new, `status: proposed`, `kind: process`, `deciders: "product"`, `features: []`, `supersedes: null`, same sections as DPRO-013): Context (the numbers from Why), Decision (the mapping table of step 2, the untouched states, the History bullet, the bot PR as the only writer, the template checkbox removal), Alternatives (hand editing; `progress.json` only, P3-10; GraphQL `closedByPullRequestsReferences`, rejected because 403 in cloud sessions), Consequences, How to validate. Add its row after `spec.md:206`.
7. `changelog.d/p2-08-sync-status.added.md` (new): one `- [DECISION] ...` bullet per `changelog.d/README.md`; do not edit `CHANGELOG.md` (DPRO-011).
8. Same stratics-docs PR: delete `.github/PULL_REQUEST_TEMPLATE.md:33`. Separate PRs, after the docs PR merges: delete stratics-client `.github/PULL_REQUEST_TEMPLATE.md:35` and stratics-server `.github/PULL_REQUEST_TEMPLATE.md:35`, commit `chore(pr-template): drop the manual FEAT status checkbox` with `Refs: DPRO-014`.
9. Run `python3 tools/spec-trace/spec_trace.py sync-status --write` once locally with `GH_TOKEN` set, commit the resulting FEAT, `traceability.md` and `spec.md` changes in the same PR so reviewers see the first derived state; if the network is unavailable, commit without it and say so in the report.

## Out of scope

- Kit changes: promoting `spec_trace.py` to `platforms/ci/validations/` and the SDD status flow text in `sdd-implement` (P1-08, P3-04); `progress.json` for executors (P3-10); spec regimes (P3-04).
- `CONTRIBUTING.md:168` stays: humans still never edit `docs/spec/**`; the sync bot is the only writer.
- `tools/project-sync/sync.py` and the board mapping; `ops/review-loop/**`; closing issues (the sync reports, never closes).
- The kit linter copy `.github/spec-lint/**` (P1-02 handles stale kit paths in stratics-docs).

## Acceptance criteria

- [ ] `python3 -m unittest discover -s tools/spec-trace/tests` prints `OK` with at least 34 tests (22 existing + 12 new).
- [ ] `python3 tools/spec-trace/spec_trace.py check` prints `spec-trace: OK (...)` and exits 0 after the `--write` run.
- [ ] `CI=1 python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas` exits 0 (DPRO-014 frontmatter, FEAT `status`/`updated` values valid).
- [ ] `python3 tools/spec-trace/spec_trace.py sync-status` (dry run, `GH_TOKEN` set) lists `FEAT-009 T2: todo -> done (stratics-server#21)` and `FEAT-009 T3: todo -> done (stratics-client#21)`.
- [ ] After `--write`, `git status --porcelain docs/spec` is non-empty; a second `--write` leaves it unchanged (`git diff --stat` after the second run prints nothing new).
- [ ] `grep -c 'No development has started' docs/spec/spec.md` prints `0`; `grep -c 'sync-status:begin' docs/spec/spec.md` prints `1`.
- [ ] `grep -c 'FEAT status updated' .github/PULL_REQUEST_TEMPLATE.md` prints `0` in each of the three repos (after the two follow-up PRs).
- [ ] `grep -c 'sync: status derived from GitHub' docs/spec/features/FEAT-009.md` prints `1` after two `--write` runs (one History bullet, no duplicate).
- [ ] `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/spec-status-sync.yml'))"` exits 0; `grep -c 'STRATICS_PROJECT_TOKEN' .github/workflows/spec-status-sync.yml` prints at least `2`; `grep -c 'GITHUB_TOKEN' .github/workflows/spec-status-sync.yml` prints `0`.
- [ ] `ls changelog.d/p2-08-sync-status.added.md docs/spec/decisions/DPRO-014-derived-status.md .github/spec-sync-pr-body.md` lists the three files; `grep -c 'DPRO-014' docs/spec/spec.md` prints at least `2`.
- [ ] After merge, `Actions > spec-status-sync > Run workflow` opens or refreshes a PR titled `chore(spec): sync status` whose `docs-checks` run is green (needs the secret; mark unverified if you cannot dispatch).
- [ ] stratics-client / stratics-server follow-ups: diff limited to the one template line; their CI (`ci.yml`) is green or skipped for a docs-only diff.

## Conventions

- Everything committed is in English; Conventional Commits with `Refs: DPRO-014` (and `Refs: FEAT-009` where a FEAT file changes); PR body = What / Why / How I tested (literal output) / Refs, plus the stratics-docs `proof` block (first word from `ops/review-loop/config.json` `proof_allowlist`, e.g. `python3`).
- stratics-docs gates: `CI=1 python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas`; `python3 tools/spec-trace/spec_trace.py check`; `python3 -m unittest discover -s tools/spec-trace/tests`; a `changelog.d/` fragment instead of a `CHANGELOG.md` edit (DPRO-011). The kit is not touched, so the kit `CHANGELOG.md` and `VERSION` rules do not apply.
- Folder index: `tools/spec-trace/` has no README, so the module docstring lists every command; `docs/spec/spec.md` lists the new DPRO; the `docs-checks.yml` header comment names the new workflow.
- Claude Code cloud sessions cannot call GitHub GraphQL (HTTP 403): keep the implementation on `gh api` REST so it runs for Devin, Claude Code and Actions alike.
- stratics-client gate if `ci.yml` runs on the template PR: `godot --headless --path . --import` then the gdUnit4 run; stratics-server: `./mvnw spotless:check verify`.

## Report back

- done: files created/edited per repo (repo-relative paths) and every command above with its literal output (test count, `spec-trace: OK` line, the two FEAT-009 report lines, grep counts).
- unverified: anything that needed `GH_TOKEN`, the secret, or a workflow dispatch you could not run; say which acceptance item it is.
- next step: the two template follow-up PR links, and whether the owner has approved DPRO-014 (`proposed` -> `approved`).
- Proposed changelog fragment line: `- [DECISION] Task and FEAT status are derived from GitHub by spec_trace.py sync-status and written only by the spec-status-sync PR (DPRO-014); the manual "FEAT status updated" PR checkbox is removed.`
