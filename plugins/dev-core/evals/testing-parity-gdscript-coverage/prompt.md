---
description: A missing GDScript coverage tool gets the same rule as Java, not an exemption.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our Java server gates 100% line and branch coverage and PIT mutation on the domain. The Godot client has no coverage tool for GDScript, so a reviewer proposes we write in the project rules that coverage and mutation simply do not apply to the client. Should we accept that wording?
