# Honcho-Pattern Integration Spike (E2.6)

**Status:** PLAN. Self-hosted, behind a strict_local boundary. Requires USER tasks U11 (VPS) and
I7 (Docker FastAPI).
**Owner:** Khaldun (HIKMAH) consumes the Dialectic API; Ammar gates writes.

## Goal

Stand up a self-hosted Honcho-pattern service that gives NIZAM a separate, peer-centric memory of
the operator. We use Honcho's open-source layout (FastAPI + Postgres + LangGraph) but run the whole
thing on the operator's own VPS, behind Tailscale, with **zero outbound calls to honcho.dev or any
hosted analogue.**

## Why a separate memory layer

The native NIZAM ledgers are *append-only event chains*. They answer "what happened?" extremely
well. They answer "what does the operator believe right now?" poorly. Honcho's Dialectic API is
designed for the latter: ask the model a question about the user, get a current snapshot, grounded
in prior turns but updated continuously.

For NIZAM, Honcho's role is narrow:

- Maintain a *peer profile* of the operator (operator-as-collaborator, not user-as-target).
- Answer "what does the operator believe about X?" when an agent (Khaldun, Tariq) asks before a
  big decision.
- Feed proposed updates to `user.md` / `user_deep.md` through the `/feedback` and GEPA paths.

The peer profile is **not** authoritative. `user.md`/`user_deep.md` remain the source of truth.
Honcho is a richer "current best guess" cache.

## Architecture (self-hosted, strict_local-adjacent)

```
+----------------- Laptop (operator) -----------------+
|                                                     |
|   nizam coordinator -- Tailscale -->   VPS (CX23)   |
|                                       +-----------+ |
|                                       | nizam     | |
|                                       | relay     | |
|                                       +-----------+ |
|                                       | honcho    | |
|                                       | FastAPI   | |
|                                       +-----------+ |
|                                       | postgres  | |
|                                       | (LUKS vol)| |
|                                       +-----------+ |
+-----------------------------------------------------+
```

- Honcho's FastAPI + Postgres run on the same VPS as the relay, but **on the LUKS-encrypted volume
  reserved for strict_local data**. They share the volume with no other service.
- Honcho's outbound LLM calls go through the same ZDR-routed gateway as everything else (Vercel AI
  Gateway / OpenRouter ZDR endpoints), never to a hosted Honcho cloud.
- The Honcho service is reachable only over Tailscale; no public port.

## Data flow on a Dialectic query

1. Khaldun (or any agent that wants context) emits an `agent_message` with `kind=request`,
   `to_agent=Honcho`, `purpose="what does operator believe about X?"`.
2. Coordinator forwards the request to the Honcho FastAPI on the VPS.
3. Honcho returns a JSON `dialectic_response`:
   ```jsonc
   {
     "summary": "Operator is currently prioritizing recovery over throughput.",
     "inferred_facts": [
       {"fact": "...", "confidence": 0.82, "support_refs": ["msg:abc", "msg:def"]}
     ],
     "model_used": "deepseek-flash",
     "ts": "..."
   }
   ```
4. Coordinator MAY persist a snippet into `user_deep.md#dialectic`, but only under operator approval
   (C2 checkpoint).

## Schema interaction

- `schemas/user_deep.schema.json#dialectic` already accepts the response shape (see E2.3).
- `schemas/agent_message.schema.json` carries the request/response with `from_agent=Khaldun`,
  `to_agent=Honcho`, `kind=request|response`.

## Tasks (in order)

1. **U11/U12/U13.** Provision VPS + Tailscale + endpoint (already on operator list).
2. **I3.** LUKS volume mounted at `/srv/nizam/strict_local`.
3. **I7.** Docker compose with: `nizam-relay`, `honcho-api`, `postgres` (all on the LUKS volume).
4. **First Dialectic call.** Stub a tiny request from the laptop, assert it returns a non-null
   summary; tear it down.
5. **Wire into Khaldun.** Khaldun gains a new tool `dialectic.query(question, k=5)`.
6. **Operator review.** First two weeks: every Dialectic-grounded recommendation gets C2.

## Failure modes

- **Honcho service unreachable.** Coordinator falls back to using only `user.md`/`user_deep.md`
  literally; no hidden silent degradation.
- **Honcho disagrees with `user.md`.** The static file always wins. Honcho's output is logged as
  a *proposal* in LEARNING_LEDGER for Khaldun review, never auto-applied.
- **Tailscale outage.** Relay degrades to read-only; no Honcho calls.

## Acceptance

Spike is complete when:

- One Dialectic call returns a non-null result.
- The call is logged in EVENT_LEDGER with `actor=Khaldun`, `module=NIZAM__system.honcho_spike`.
- Operator has reviewed and approved one round of Honcho's output landing in `user_deep.md`.

The spike is DELIBERATELY MINIMAL. Production usage (writing back inferred_facts, weekly digests)
lands later under E2.7 GEPA loop only after the spike has run for at least 4 weeks.
