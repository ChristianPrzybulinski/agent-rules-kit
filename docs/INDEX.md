# docs/ — documentation about the kit

Scope: architecture and maintenance information for humans changing the kit. Plugin behavior lives in `plugins/core/AGENTS.md`, `plugins/*/rules/` and `plugins/*/skills/`; executable lifecycle belongs in `platforms/`.

| File | Read when |
|---|---|
| [`design.md`](design.md) | understanding the plugin-first architecture, context costs and deliberate exclusions |
| [`projects.md`](projects.md) | deciding which artifacts belong in a project repository and where their templates originate |
| [`maintenance.md`](maintenance.md) | changing layout, content, vendors, CI or a release |
| [`features/`](features/README.md) | recording a confirmed big kit change (hook, core `AGENTS.md`, plugin structure, check or script behavior, skill added or removed): one `KIT-NNN` file and one `kit-feature` issue each, implemented by hand |
| `machine.local.md.example` | template for the git-ignored `machine.local.md` (this machine's versions/paths) |
