---
name: [folder-name]
version: "1.0"
description: "[What it does in 1 sentence]. Use when [concrete trigger]. Do not use for [neighbor case that confuses]."
argument-hint: "[expected argument | empty]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# [Name]

[One sentence: the result this skill produces and what it does NOT do.]

## 1. [Step — imperative verb]

- [observable action; command when there is one]

## 2. [Step]

## 3. Close

- [artifact produced: path/template]
- [verification: command + expected output]

## Rules

- [acting boundary: what the skill never does]

<!-- Limit: 80 lines. Normative detail that does not fit goes to `references/` and is linked, not copied. -->
