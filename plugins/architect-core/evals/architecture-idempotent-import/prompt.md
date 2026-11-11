---
description: An import use case is designed to leave the same state when run twice or after a crash.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Design the `ImportRoster` use case and its ports. It reads `roster.csv` from the inbox folder, writes each player into the database and then deletes the CSV. Today it deletes the file first and then inserts the rows. List the classes and the order of the steps.
