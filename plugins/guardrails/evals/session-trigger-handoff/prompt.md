---
description: "A request to hand off unfinished work loads skill session."
tags: [trigger]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
append_system_prompt: "Before a handoff or closeout → load skill `session`. End with done · unverified · one concrete next step, plus at most **one** evidence-backed kit proposal, filed directly as a GitHub issue without asking first; link it in the closeout. Filing is authorized; implementing the proposal still needs approval."
---

I have to stop for today. Hand this off so a new session can pick it up tomorrow: we are adding rate limiting to the login endpoint (issue #48); the limiter class and its tests are done and green, wiring it into the route is not started, and the open question is whether the limit applies per IP or per account.
