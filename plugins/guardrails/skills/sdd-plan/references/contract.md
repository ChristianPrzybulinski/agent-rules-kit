---
description: Contract compatibility, the message file and the four checks a FEAT's Contract section passes. Load when a FEAT changes a contract.
kind: detail
---

# Contract checks

A contract is every artifact two parts of the product read the same way: a message or endpoint schema, a table, a content file, a generated codec. The FEAT that owns a contract change states it in its Plan's Contract section, and `sdd-plan` checks the items below before setting `planned`. `sdd-tasks` turns items 3 and 4 into rows and waves; its row check on cross-feature fields reads item 1. The always/never for the protocol folder itself is rule `protocol.md`.

## 0. Source of truth and compatibility

- Read the project's protocol folder and its approved transport and serialization decision; with none, stop with a proposed decision record: this check changes the contract, not that choice.
- Classify each change and record a breaking one with its migration window before any consumer row:

| Change | Version effect | Compatibility |
|---|---|---|
| optional field or new message | same protocol version | older consumers ignore it |
| required field, changed type or meaning, removal | increment the protocol version | coexistence window or cutover required |
| documentation or example only | none | bytes unchanged |

- One file per message, headed `<Name> — <command|event|response|error>` with its protocol version and FEAT: purpose, direction, field types and requiredness, range/size/frequency limits, server-side validation and stable errors, the idempotency key of a state-changing command, ordering and out-of-order handling, and one valid plus at least one invalid example. A legacy handler is linked only after reading it, and a divergence from it is a proposal.

## 1. A field another FEAT reads exists, with its value domain

- Every field, column or key another FEAT reads (or will read, by its REQs) exists in the contract artifact itself, written by the FEAT that owns the contract, never inside the reader's PR.
- Each one names its type and value domain: an enum's values, a number's range and unit, a string's format, and the public identifier of any entity it names (never a database key).
- A reader that needs a missing field sends the change back to the owning FEAT's Plan first.

## 2. Every command has its success reply

- Each command or request names the reply its sender receives on success, and each error reply with its code, so no sender waits on silence; a fire-and-forget message says so, with the reason.

## 3. One regeneration row per consumer

- When the change needs regenerated code or data (codec, client bindings, content pack, fixtures), the task table holds one row per consuming repository or folder that regenerates it, runs the generator's `--check` and the validator on both sides' examples; the command and output paths are in that row's Files and Proof.

## 4. A new message lands with its consumer's validator in the same batch

- The schema row goes first (wave 0). The row that starts producing the new message or field and the row that makes its consumer's validator accept it (and still reject an invalid shape) land in the same wave, so no consumer rejects what a producer already sends and no producer sends what nothing validates.

## Example

| Check | FEAT-021 Contract line |
|---|---|
| 0 | `turn-result.order` is optional: protocol version unchanged, older clients ignore it |
| 1 | `turn-result.order: [string]`, public creature ids, 1–2 items |
| 2 | `submit-move` replies `move-accepted`; errors `E_TURN_CLOSED`, `E_NOT_YOUR_TURN` |
| 3 | T3 regenerates the client codec (`client/net/codec/`), T4 the server one (`server/net/codec/`): one row per consumer |
| 4 | T1 adds `order` to the schema (wave 0); T2 makes the server send it, T5 makes the client validator accept it: both wave 1 |
