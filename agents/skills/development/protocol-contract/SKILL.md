---
name: protocol-contract
version: "1.0"
description: Creates or evolves a client↔server contract message (command, event, response, error) with versioning, testable examples and compatibility rules. Use when adding/changing a field, creating a new message, or when client and server disagree about a payload. Do not use to decide transport/serialization (that is a DEC).
argument-hint: "[message-name | FEAT-xxx that needs a new message]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Protocol Contract

The contract lives in a single place (in the project, typically `protocol/`); client and server consume it by version. This skill changes the contract, never the consumers directly.

## 1. Locate the source of truth

- Read `protocol/README.md` (or whatever `AGENTS.md` indicates): transport, serialization, current `protocol_version`, naming convention, common envelope (id, correlation, sequence, timestamp).
- If there is no approved DEC for transport/serialization → stop; open a `DEC-xxx` as `proposta` and report. Do not choose on your own.

## 2. Classify the change

| Change | `protocol_version` | Compatibility |
|---|---|---|
| New optional field; new message | minor | old client ignores it |
| New required field; changed type/semantics; removal | major | breaking — requires a coexistence window or a planned cutover |
| Doc/example fix without changing bytes | none | — |

Major → needs a DEC (even a short one) before proceeding.

## 3. Specify the message

Template: `agents/templates/doc-contract-message.md`. Required per message:

- direction (C→S, S→C, both), type (command / event / response / error);
- fields with type, requiredness, limits (size, range, frequency);
- who validates what (server validates everything that changes state; client only pre-validates UX);
- idempotency: deduplication key for commands with an effect (inventory, economy, reward);
- ordering: per-session or per-entity sequence; what happens out of order;
- possible errors with a stable code (not text);
- **one valid and ≥1 invalid example**, in separate files under `protocol/examples/`, to become contract-test fixtures on both sides.

## 4. Legacy as reference, not as mold

If an old protocol exists: record in "Related legacy" the equivalent subject/handler with `[FACT]` only if read in the code. Do not copy delimiters, obscure names or fields of unknown purpose. Behavior divergence from legacy → explicit `[PROPOSAL]`, never silent.

## 5. Close

- `protocol/CHANGELOG.md` (or section) with the version and the change.
- FEAT that motivated the message: link the message under "Relations".
- Examples pass through a schema validator if the project has one (run it; output in the report).

## Rules

- No "reserved for the future" fields.
- Every message with a state effect has a defined response or error — no fire-and-forget for commands.
- Maximum size and maximum frequency are part of the contract, not a server detail.
