---
id: KIT-027
title: "A handoff names the owner of a shared device and what no other session may run on it"
status: done
confirmed: "2026-11-03 (owner, chat of the Stratics Time Machine session: \"Sim, gravar\")"
issue: "#128"
pr: ""
---

# KIT-027 — A handoff names the owner of a shared device and what no other session may run on it

## Problem and evidence

[FACT] The record of the mini PC's new 10 TB HD (`~/.claude/projects/-Users-christian-Developer-GitHub/memory/time-machine-pending-hdd.md`,
entry "2026-11-03 17:43–17:54 BRT") says a SMART pass-through (`smartctl -d sat`, ATA opcodes 0xec/0xa1) made the
JMicron 152d:0586 bridge abort and reset under `uas`; `usb-storage`, a `kworker` and the host's own `vgs` went into D
state, and Proxmox status, vzdump and `pct start` froze until the USB device was deauthorized.

[FACT] Two sessions used that disk and the host: a media-server session and a Time Machine session. The same record
shows the hand-over was a queued chat message ("the Time Machine session was told by message to leave `/dev/sda`
alone"), and at 20:30 it notes that "no reply to my heads-up arrived". No file said who owned the device or which
commands were off limits. Which session sent the SMART call is not recorded.

[FACT] `plugins/core/skills/session/references/handoff-record.md` and skill `parallelize` § 5 ("Keep unsafe work
sequential") name shared files and ports, not shared hardware: a search of `plugins/*/skills`, `plugins/*/rules` and
`plugins/core/AGENTS.md` for shared device, device owner and ownership found no rule for it.

## Change

`plugins/core/skills/session/references/handoff-record.md` § Collect observed state gains one bullet:

> For a device or host that another session also uses (disk, USB bridge, VM, port), name the owner session of each
> device and the commands no other session may run on it (SMART, partitioning, authorize or unbind) before the first
> probe. A peer message that got no reply is not a release.

`CHANGELOG.md` `[Unreleased]` records it. No new file in `plugins/`, no change to `VERSION` (the next release bump
covers it).

## Proof

`bash platforms/tools/check.sh`; `bash platforms/tools/smoke.sh`; `python3 platforms/ci/validations/check_kit.py --links`;
`gitleaks git --redact --log-opts="origin/main..HEAD"`.

## History

- 2026-11-03: confirmed (owner, chat).
- 2026-11-04: done; issue #128 opened on the owner's "Sim, abrir PR".
