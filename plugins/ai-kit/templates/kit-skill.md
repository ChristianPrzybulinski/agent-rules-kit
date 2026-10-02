---
name: [folder-name]
description: "[≤160 chars: <what>. Use when <trigger>. Not for <neighbor> (skill <x>).]"
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

Done when: [observable completion condition].

<!-- Limit: 80 lines. Normative detail that does not fit goes to `references/` and is linked, not copied. -->
