---
id: KIT-057
title: "The always-on rules are rewritten after the owner's section-by-section review"
status: confirmed
confirmed: "2026-11-12 (owner, chat of the kit always-on review session: \"Aceito todas\" per section, \"Tirar os dois\", \"Comparação visível\", \"Yes, Scope clause\")"
issue: "#202"
pr: ""
---

# KIT-057 — The always-on rules are rewritten after the owner's section-by-section review

## Problem and evidence

[FACT] On 2026-11-12 the owner reviewed `plugins/guardrails/AGENTS.md` (`origin/main` `c90aefd`, 57 lines) one section
at a time. The first reply was "estou lendo o boundaries primeiro e avaliando: mas nao entendi nenhum ponto deles, acho
que voce precisa me dar mais detalhes, pra eu conseguir entender se devemos manter ou nao." Each item was then shown with
what it does, an example, its origin, who enforces it, the risk without it and a recommendation, and the owner accepted
or changed it section by section.

[FACT] Lines that repeated another line, or that no longer worked:

- Boundaries `**Never**` held "rewrite public history without authorization", which is the force-push item of
  `**Ask first**` under another name, and "invent command output or an API", which Truth already covers ("claim only
  what you verified" and the installed-version check).
- Truth "Before claiming "done": test ran, app ran, diff read" repeated the Boundaries `**Always**` check and, read
  literally, asked for a running app on a docs-only change.
- Work loop "Same error twice" let a fix that changed the error escape the rule, and nothing stopped a fourth or fifth
  attempt.
- The browser preference (KIT-018, #108) is a personal choice, not discipline. The Claude desktop app defaults to its
  built-in browser and uses Chrome on request, so the kit and the app named two different defaults. The owner asked
  "nao faria sentido remover e usar apenas o padrao configurado no claude?".
- The "Context without an obvious skill" table sent the model to `sdd-specify`, which has
  `disable-model-invocation: true` (`plugins/guardrails/skills/sdd-specify/SKILL.md:7`). The vague-idea route already
  lives in `plugins/guardrails/skills/sdd-constitution/references/sdd-process.md:10` and
  `plugins/guardrails/skills/sdd-specify/SKILL.md:22`, and `grilling` is synced only to `docs` profiles
  (`platforms/tools/sync-profiles.txt:16`). The owner asked "precisamos ter isto no AGENTS?" and chose "Tirar os dois";
  for the legacy-code row: "ja coloque esse gatilho em testing e apague a linha do item 3."

[FACT] The owner proposed that the agent question its best solution three times before proposing it. An internal count
cannot be checked, the reason #31 (2026-10-06) replaced the ">98% confidence" gate with the `[HYPOTHESIS]` tag, and
Huang et al., "Large Language Models Cannot Self-Correct Reasoning Yet" (ICLR 2024, arXiv:2310.01798), report that
LLMs "struggle to self-correct their responses without external feedback". The owner chose the visible form instead:
the proposal shows the alternatives it beat. Example from the same review: the first recommendation for the SDD routing
row was to keep it with a changed action; removing it, the better answer, came only after the owner challenged it.

[FACT] The owner also proposed "Mudanças atômicas": change the minimum code needed and avoid unrequested refactors in
neighboring files. Boundaries `**Scope**` already stopped edits outside the task's files, and
`plugins/guardrails/skills/code-standards/SKILL.md:63` ("no drive-by refactor outside the flow the change touches",
adopted 2026-11-11) covered the same file, but only when that skill loads. Anthropic's prompting guide (section
"Overeagerness", `platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices`)
suggests "Only make changes that are directly requested or clearly necessary", and its next section asks for a
general solution instead of hard-coded values. Read literally, "minimum code" conflicts with `code-standards` § 8 (a
new requirement "is not bolted onto the old design"), so the owner chose a clause bounded by what the task needs.

## Change

`plugins/guardrails/AGENTS.md` (57 → 58 lines, 6,048 → 6,346 bytes):

- Intro: each line must hold before any skill could load.
- Boundaries: `**Ask first**` and `**Never**` become sublists. Rewriting pushed history (force-push, amend,
  `filter-repo`) moves to `**Ask first**`; each `**Never**` item names its safe path; the duplicate "invent command
  output or an API" goes. Scope says "the file list in its issue (the `Files` field)" instead of "cell" and ends with
  "Inside it, change what the task needs (a design change the fix needs included) and nothing more: no unrequested
  refactor, rename, reformat or "improvement"; offer a worthwhile cleanup as a follow-up."
- Session: start, other-topic and end become separate bullets; "kit proposal" reads "proposal to change the kit".
- Work loop: the browser line goes. The repeated-failure rule reads "Two fixes failed the same check → before a third,
  undo them and write in your reply the premise both shared, in one sentence; test it with the cheapest check that
  could prove it false. A third failure → stop and report the attempts and premises, or load skill `investigate`."
  The zsh line keeps its three traps as reasons for the positive rule. "Report the worst fact first" moves to
  Communication.
- Security: the secret warning does not repeat the value, and the agent gets the secret rotated (rotation is an
  external effect); "authz" and "leak internals" are spelled out.
- Truth: the API/flag/version check joins the code-is-truth line; "Report what you did not test, run or read in the
  diff as "unverified", never as done."; the `[HYPOTHESIS]` rule moves here from Skepticism.
- Decisions (was Skepticism): "A proposal, the user's or your own → open with a verdict backed by evidence. Before
  recommending, set it against the 2 strongest alternatives (doing less counts), each with its trade-off, and say what
  would prove the pick wrong; agree on evidence. Questions that hinge on the solution wait until the user accepts or
  rejects it." Admitting a mistake also fixes what the mistake already touched.
- Communication (was Craft): talk with the user in the language they write in; the short code-first format applies to
  an answer that delivers code, while paths, commands and errors stay byte-for-byte in every answer; text for people
  names explanations, proposals, reports and questions and, when the user must decide, adds a concrete example and what
  changes for them.
- The "Context without an obvious skill" table goes.

`plugins/guardrails/skills/testing/SKILL.md`: the description reads "Test policy. Use when choosing or reviewing tests,
setting coverage/mutation gates or before refactoring legacy or ported code. Not for verdicts (skill review)." (160
characters, the `check_kit.py` maximum). `plugins/guardrails/INDEX.md` is regenerated.

KIT-018's record keeps its text (records written before KIT-040 stay as they are); this record reverses its rule.

## Proof

`bash platforms/tools/check.sh`, `CI=1 bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, `python3 platforms/tools/gen_index.py --check` and
`gitleaks git --redact --log-opts=origin/main..HEAD`; results in the PR body. No eval covers the `testing` trigger for
legacy code; `claude plugin eval` is billed and was not run.

## History

- 2026-11-12: confirmed (owner, chat, section by section); Scope clause added on the owner's "Mudanças atômicas" proposal.
