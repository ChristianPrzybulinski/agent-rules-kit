---
description: Always/never constraints for the client/server contract folder (protocol/ unless sdd.rule_paths names it); checks in the sdd-plan contract reference.
trigger: glob
globs:
  - "**/protocol/**"
paths:
  - "**/protocol/**"
---

Always/never for the client/server contract: messages, schemas, examples and what is generated from them. The folder is `protocol/` unless `docs/spec/spec.md` names another in `sdd.rule_paths` (`protocol: [game]` scopes this rule to `game/**/protocol/**`). Compatibility, the message file and the four contract checks: skill `sdd-plan`, reference `contract.md`.

- Always: read the protocol folder and the approved transport and serialization decision first; with none approved, stop and propose a decision record: a contract change never picks the transport.
- Always: classify the change before editing: an optional field or a new message keeps the protocol version; a required field, a changed type or meaning, or a removal raises it, with its coexistence window or cutover recorded before any consumer changes; a docs or example change changes no bytes.
- Always: one file per message, headed `<Name> — <command|event|response|error>` with the protocol version it appears in and its FEAT; it states purpose, direction, field types, requiredness, range, size and frequency limits, server-side validation and stable errors, the idempotency key of a state-changing command, and ordering and out-of-order handling.
- Always: every state-changing command names its success reply and its error replies; never a reserved future field or an unspecified limit.
- Always: one valid and at least one invalid example per message under the protocol's `examples/` folder.
- Never: copy a legacy handler's opaque names, framing or unexplained fields; link it only after reading it, and mark a divergence as a proposal.
- Never: rename or reuse a message, field or error id; add a new one and retire the old one.
- Never: hand-edit a file generated from the protocol (codec, bindings, tables, client fixtures); rerun its generator and the generator's `--check`.
- Always: before "done", the protocol changelog and the motivating FEAT are updated, every generated file is regenerated and the schema or contract validator runs on the examples for both sides, with the literal output.
