---
name: sdd-to-card
version: "1.0"
description: SDD step 9 — syncs a FEAT with a GitHub card (Issue + Project) via gh - creates the issue if missing, updates title/body/labels/status from the frontmatter, writes the number into the FEAT's card field. Use after specify (open) and after validate/merge (close). Do not use for branches, commits or PRs (skill github-cli).
argument-hint: "FEAT-nnn [--project <number>]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - edit
  - exec
---

# SDD 9 — To Card (GitHub Issues + Projects)

Product decision: GitHub Issues + Projects (not Trello). `gh` already authenticated; never print a token.

## Mapping

| FEAT (frontmatter) | GitHub |
|---|---|
| `id` + `title` | issue title: `FEAT-nnn: <title>` |
| body (Problem, Scope, Criteria) | issue body (link to the file in the repo, not a full copy) |
| `status` | label `status:<value>` + Project column (Status) |
| `requirements` | list in the body with links |
| `card` | issue number (`#42`) |
| `flag` | label `flag` if not null |

## Steps

1. Read the FEAT. `card: null` → create:
   ```bash
   gh issue create --title "FEAT-nnn: <title>" --body-file <(generate body) --label "feature,status:<status>"
   ```
   Write `card: <n>` into the frontmatter and commit `docs(spec): link FEAT-nnn to issue #n`.
2. Existing `card` → `gh issue edit <n> --title ... --body-file ... --add-label status:<new> --remove-label status:<old>`.
3. Project (if `--project` or a `project` field in `spec.md`): `gh project item-add <num> --owner <owner> --url <issue-url>`; update the Status field via `gh project item-edit` (requires IDs — get with `gh project field-list`). If the Project does not exist → ask before creating.
4. `status: delivered` → `gh issue close <n> --comment "Delivered in <PR>"`.
5. Labels `status:*` and `feature` missing in the repo → create with `gh label create` (once).

## Completion criteria

- `gh issue view <n>` reflects the FEAT's title, status and links.
- The FEAT has `card` filled in and committed.

## Do not

- Copy the whole spec into the issue (the file is the source of truth).
- Create issues for REQ/DEC/DEBT — only a FEAT becomes a card. A DEBT may become an issue with the `debt` label **if the user asks**.
