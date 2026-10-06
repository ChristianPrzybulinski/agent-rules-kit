# Devin snapshot checklist

Run it when you create or refresh the Devin snapshot of a repository that carries an `environment.yaml` copied from this folder.

1. Toolchain versions in the snapshot match CI: Godot `barichello/godot-ci:4.7.2`, JDK 25 (Temurin), Maven 3.10.0 through the wrapper, the Python pins of the docs checks workflow.
2. `initialize` runs on a fresh VM in one go, with no manual step and no prompt.
3. `maintenance` finishes in under 5 minutes, and the lint and test commands of `knowledge` each finish in under 5 minutes (limit from assessment §5; docs.devin.ai/onboard-devin/repo-setup does not state it, verify before relying on it).
4. `gh auth status` works with a token from the Devin secrets store; a token is never typed in a session or written to a file.
5. Docker answers `docker --version` when the project uses Testcontainers (`environment.java.yaml`).
6. Re-snapshot after any change to `initialize`; `maintenance` and `knowledge` changes do not need one.
7. Record the snapshot date in the PR that changed `environment.yaml`.
