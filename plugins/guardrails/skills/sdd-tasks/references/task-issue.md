---
description: Cut item contract, GitHub issue or TASK-nnn file — field map, states, FEAT card, close line. Load when cutting, resyncing or reviewing items.
kind: detail
---

# Cut item — field contract

One item carries one task row, or several when `bundle` bundles rows of one repository that share a Files path. Its body is the rows filled verbatim — no rewriting, no added scope — and the rows' `Item` cell names it.

| Tracker | Item | Title | Body |
|---|---|---|---|
| `github` | an issue in the backlog repository the project names | `[FEAT-nnn Tn] <first ~8 words of the Task cell>` (bundle: `[FEAT-nnn T1+T2] ...`) | the kit issue template `platforms/kits/github/ISSUE_TEMPLATE/task.md`, installed as `.github/ISSUE_TEMPLATE/task.md` |
| `none` | `docs/spec/tasks/TASK-nnn-slug.md`, the next unused `TASK-nnn` | frontmatter `title` | the template `spec-task.md`, the same fields; frontmatter `feat`, `rows`, `status`, `labels`, `pr` (schema `task.schema.json`) |

## Field map (task row → item field)

| Row cell | Item field |
|---|---|
| Task | `Task` |
| (FEAT path) | `Spec` |
| Files | `Files` |
| Proof of completion | `Proof of completion`, and with the gate commands `DoD` |
| Covers | `Covers` |
| Depends on | `Depends on`, each row written as its item (`#N`, `TASK-nnn`) once cut, else `FEAT-nnn Tn` |
| Complexity, Model, Wave | `Directive` |

## Mechanical fields

- `Spec` is the FEAT path; REQ and decision ids are read from the FEAT's Relations, never copied into the item.
- `DoD` is the rows' proofs plus the gate commands of `<Repository>/AGENTS.md` § Commands; it adds no scope.
- `Repository` is the repository or clone the code lives in; `Notes` names the project's proof-wording allowlist location, never a hard-coded list.

## States

- An item is cut only from an approved or merged table, so it starts ready: a GitHub issue carries `status:planned`, a TASK file `status: todo`. An implementation session takes only those whose `Depends on` items are merged.
- GitHub derives the row `Status` from the issue: open is `todo`, open with an open PR is `doing`, the project's blocked label (when it keeps one) is `blocked`, closed by its merged PR is `done`, closed as not planned is `cancelled`. A TASK file holds the same values in `status`, with `pr` set once its PR exists.
- Task issues reuse the FEAT status labels of `platforms/kits/github/labels.json` with their FEAT meaning; a project that wants task-level labels adds them in its own labels file.

## Optional FEAT card (`tracker: github`)

- A FEAT card `FEAT-nnn: <title>` mirrors FEAT status through its labels (`status:<status>`, and `flag` when `flag` is set) and the Project status field when the project configures one; ask before creating a Project, and create missing `feature` or `status:*` labels only when authorized.
- `card` in the FEAT frontmatter stores only the card number; task issue numbers live in the `Item` cells, never in frontmatter.

## Close

- A task issue closes through its PR, whose last line is `Closes <owner>/<backlog-repo>#N` — cross-repo when the code lives elsewhere. A TASK file turns `done` in the PR that delivers it.
- The FEAT card closes when every task item is done or cancelled, with the delivered PR references. No cards for REQs, decisions or debts unless the user asks for a debt issue.
- Check with `gh issue view <n>` (or the TASK files) that title, state, links and the FEAT `card` agree.
