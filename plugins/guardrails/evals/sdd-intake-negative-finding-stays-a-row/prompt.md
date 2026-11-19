---
description: "A defect found while reviewing a FEAT is routed to a fix row and never recorded as a NEED."
tags: [negative]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Write, Edit, Skill]
append_system_prompt: "A request someone makes (an idea, need, improvement or problem) in a repository with `docs/spec/` → load skill `sdd-intake` to record it as a NEED; a defect or gap your work finds → route it by type where found (skill `sdd-intake` § 4), a NEED only for a missing capability or an owner decision too large for one question or left unanswered; a request on another topic → say so and offer a follow-up or a new session before starting it."
---

This repository keeps its spec in docs/spec/. While reviewing FEAT-001 I found that src/login.py accepts an empty password, although REQ-F-001 says a login with an empty password is refused. How do I record this finding?
