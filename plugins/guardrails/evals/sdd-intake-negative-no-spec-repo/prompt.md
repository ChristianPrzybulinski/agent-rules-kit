---
description: "A defect found while coding in a repository with no docs/spec/ does not load skill sdd-intake."
tags: [negative]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Write, Edit, Skill]
append_system_prompt: "A request someone makes (an idea, need, improvement or problem) in a repository with `docs/spec/` → load skill `sdd-intake` to record it as a NEED; a defect or gap your work finds → route it by type where found (skill `sdd-intake` § 4), a NEED only for a missing capability or an owner decision too large for one question or left unanswered; a request on another topic → say so and offer a follow-up or a new session before starting it."
---

While adding the export button I noticed that export_rows in src/export.py crashes on an empty list. Please fix it.
