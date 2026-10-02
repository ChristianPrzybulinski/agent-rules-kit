---
name: protocol-contract
version: "1.1"
description: Client↔server contracts. Use when adding a message or field, changing a payload or fixing a client/server mismatch. Not for transport choice (skill sdd-plan).
argument-hint: "[message-name | FEAT-xxx that needs a new message]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - edit
---

# Protocol Contract

## 1. Locate the source of truth

Read the project's protocol location and approved transport/serialization DEC. Stop with a proposed DEC if transport or serialization has no approved decision; this skill changes the contract, not that choice.

## 2. Classify compatibility

| Change | Version effect | Compatibility |
|---|---|---|
| optional field or new message | same protocol version | older consumers ignore it |
| required field, changed type/meaning, removal | increment protocol version | coexistence window or cutover required |
| documentation/example only | none | bytes unchanged |

Record any breaking change and migration window before editing consumers.

## 3. Specify the message

Use `../../templates/doc-contract-message.md` and define:

- direction and command/event/response/error kind;
- field types, requiredness, range/size/frequency limits;
- server-side validation and stable errors;
- idempotency key for state-changing commands;
- ordering/sequence behavior and out-of-order handling;
- one valid and at least one invalid example under `protocol/examples/`.

Every state-changing command has a response/error; no reserved future fields or unspecified limits.

## 4. Compare legacy behavior

Link an equivalent legacy handler only after reading it. Mark divergence as a proposal; do not copy opaque names, framing or unexplained fields.

## 5. Close

Update the protocol changelog and motivating FEAT, then run the schema/contract validator on examples for both sides. Capture literal output.

Done when: compatibility is explicit, examples prove valid and invalid payloads, state effects define idempotency/ordering/errors, and both consumers share one versioned source.
