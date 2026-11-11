# docs/templates/ — skeletons for kit content

Scope: templates that shape the kit's own files. Templates a project uses (specs, project `AGENTS.md`, session handoff) stay in their plugin's `templates/`.

| File | Scope | When to use |
|---|---|---|
| [`kit-skill.md`](kit-skill.md) | `SKILL.md` frontmatter and section shape | adding a skill |
| [`kit-reference.md`](kit-reference.md) | `references/<topic>.md` with `kind`, date and sources | adding a reference to a skill |
| [`kit-index.md`](kit-index.md) | directory `INDEX.md` listing | a folder needs only a listing |
| [`kit-readme.md`](kit-readme.md) | directory `README.md` with steps and limits | a folder needs explanation |
