# rules/ — triggered guidance

Rules load focused skills only when matching files enter the session.

| File | Trigger | Globs | What it loads |
|---|---|---|---|
| [`java.md`](java.md) | `glob` | `**/*.java,**/pom.xml` | `java-standards`, `clean-code`, `testing` |
| [`godot.md`](godot.md) | `glob` | `**/*.gd,**/*.tscn,**/project.godot` | `godot-standards`, `clean-code`, `testing` |
| [`spec.md`](spec.md) | `glob` | `docs/spec/**/*.md` | `sdd-*` skills and `templates/spec-*.md` |
