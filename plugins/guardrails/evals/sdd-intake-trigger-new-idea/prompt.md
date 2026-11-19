---
description: "A new feature idea in a repository with docs/spec/ loads skill sdd-intake."
tags: [trigger]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
append_system_prompt: "A request someone makes (an idea, need, improvement or problem) in a repository with `docs/spec/` → load skill `sdd-intake` to record it as a NEED; a defect or gap your work finds → route it by type where found (skill `sdd-intake` § 4), a NEED only for a missing capability or an owner decision too large for one question or left unanswered; a request on another topic → say so and offer a follow-up or a new session before starting it."
---

This repository keeps its spec in docs/spec/ (NEEDs, FEATs, REQs). New idea: players keep asking for a way to trade items with each other directly, without the auction house. Can we get that going?
