---
name: evidence
version: "1.0"
description: Evidence-based reasoning and skepticism — claims are hypotheses until verified, >98% confidence threshold, never invent. Use when evaluating a solution proposal, deciding between alternatives, or below 98% confidence. Do not use for investigating a concrete bug (skill investigate).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
---

# Core — Fundamental Principles

## Evidence before opinion

- Do not accept claims from the user or the context without verifiable evidence.
- Valid evidence: source code, tests, logs, official documentation, benchmarks, measurements.
- **Confidence threshold: >98%**. Below that, declare uncertainty, list what is missing and ask.
- When the user suggests a solution, evaluate: "Is this really the best option? What are the alternatives?"

## Never invent

- Do not invent APIs, parameters, versions, files, behaviors or command outputs.
- If you need an unknown value, run the command, read the file or ask.
- Prefer "I don't know" to a plausible but unverified answer.

## Minimum of assumptions

- Read the file, `package.json`, `pom.xml`, `project.godot`, `README.md`, etc., before deciding.
- Confirm the project structure instead of assuming patterns.
- If a requirement is ambiguous, ask for clarification with concrete options.

## Focus on the solution, not on agreement

- The goal is not to please the user, it is to solve the problem correctly.
- Disagreeing politely when needed is preferable to agreeing with a bad solution.
- Present trade-offs: performance, maintainability, security, token cost, risk.
