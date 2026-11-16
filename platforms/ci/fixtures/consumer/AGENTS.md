# Consumer fixture

A small project that agent-rules-kit keeps for its functional test layer (KIT-077). The `ci-full` workflow copies it
to a throwaway folder, syncs the kit into it with `platforms/tools/sync-project.sh`, then runs the project's own
checks: its spec lint, `just verify` in each profile folder and `sync-project.sh --check`.

- The root holds the spec (`docs` profile); `tools/` holds Python code and its tests (`python:tools`).
- Nothing here is generated: the sync writes its files only into the throwaway copy.
