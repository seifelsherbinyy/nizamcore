# Spec 07 task A0 — owner authorization receipt

> Owning authority: `ops/INTEROP_CONTRACT.md` §0 ("the owner to authorise modifying the other
> repository, which is spec 07 task A0 and is the single open gate"); `ops/hermes/WORKSPACE_MOUNT.md`
> ("Status: specification only. This file authorizes no clone, install, start, or host write.").
> Status: A0 CLOSED, scoped to the workstream named below. Every other line in the two documents
> above stays true; this receipt narrows nothing about them except the one gate it names.

## What this closes

Spec 07 task A0 blocked any modification of the `nizamcore` repository or its VPS runtime from this
side. The owner authorized closing it, in plain language, in chat, on 2026-09-02, for one named
workstream: **Hermes journal persistence** — YAWMIYAT capture, atomic VPS write with read-back
verification, THABAT exactly-once ledger append, HIMAYAH classification, and permitted Google Drive
mirror with read-back.

## Scope of the closure

Authorized:
- modifying `nizamcore` code, configuration, schemas, persistence logic and tests
- modifying/configuring the authorized VPS runtime, Hermes integration, containers, mounts, services
  and filesystem permissions required for this workstream
- installing required free/open-source dependencies and restarting the affected services

Not authorized by this receipt (unchanged, still gated elsewhere):
- minting or rotating any credential
- any spend against a production key
- DNS, TLS, or host provisioning (G1-G8, `ops/DEPLOYMENT_CONTROL.md`)
- anything outside the named journal-persistence workstream

## Record, not narrative

This file exists so a later reader of `INTEROP_CONTRACT.md` or `WORKSPACE_MOUNT.md` sees why work
proceeded past a gate those documents still describe as open in their own prose — the prose is
correct about the state *before* this receipt, and this receipt is the fact that changed it, for this
one workstream, on this date. No identity detail beyond "the owner, in chat" is recorded here.
