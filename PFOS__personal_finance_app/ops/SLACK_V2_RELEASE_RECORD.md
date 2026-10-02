# Slack-v2 release record — which human gates this release traverses

> **This file does not modify `ops/DEPLOYMENT_CONTROL.md`.** Every `G1`–`G8` status there is untouched and
> stays exactly as its operator left it. That register's own rule is that the only status an agent may ever
> write is `BLOCKED - awaiting human`, and that marking a gate satisfied is the most damaging possible act.
> This record therefore does something different: it states which gates a **Slack-first release** has to
> traverse at all, and why. A gate that a release does not traverse is not a gate that was passed.

**Owning authority:** PFOS Contract 12; `src/server/hermes/ingressPolicy.ts` v2; ADR-0004.
**Plan:** `NIZAM-SLACK-FINANCE-PRODUCTION-2026-09-22`, phase P1.
**Public-repository constraint (R24):** this file contains no deployment particular. No host, domain, port,
identifier, path on the host, or credential value appears here, and none may be added.

---

## The transport fact this record rests on

`src/server/hermes/ingressPolicy.ts` v2 names **Slack Socket Mode as the sole transport**, with exactly
three aliases — `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_ALLOWED_USERS` — and lists five
`REVOKED_TELEGRAM_ALIASES`: `BOT_NIZAM_TOKEN`, `BOT_A_TOKEN`, `BOT_B_TOKEN`, `TELEGRAM_BOT_TOKEN`,
`TELEGRAM_ALLOWED_CHATS`. `assertRevokedTelegramAliasesNotPresent` **refuses** any process presenting one of
them. This is enforced by refusal in code, not by documentation, and the
`hermes-governed-workflows` requirements, design and acceptance checklist all carry it.

**The consequence that reshapes the deployment.** Socket Mode connects **outbound** from the host. It needs
no inbound listener, so it needs no public port, no hostname, no DNS record, no TLS certificate and no
webhook registration. Those were never optional for a webhook transport; for this transport they are simply
not part of the path.

---

## Gate applicability for the Slack-first release

| Gate | Applies to this release? | Why |
|---|---|---|
| **G1** provision and harden the host | **YES** | Still the trust root. An outbound connection still runs on a host, and the environment files every service reads exist only because G1 created the root-owned configuration directory. |
| **G2** records for the two hostnames | **NOT TRAVERSED** | A hostname exists to be *reached*. Nothing reaches this deployment: Socket Mode dials out. G2 returns the moment an independently approved public HTTP endpoint is in scope. |
| **G3** create the two messaging bots | **SUPERSEDED IN FORM** | The obligation is unchanged — an owner-created application, its credentials, and a **non-empty** allowlist — but it is discharged against Slack with the three v2 aliases, not against the revoked Telegram aliases. Tracked as **H2** in the plan. |
| **G4** mint the runtime model keys and caps | **CONDITIONAL** | Required only if model-authored *explanations* are enabled. Not required for deterministic financial answers, which under **D-SLACK-2** and **D-8** never reach a model at all. |
| **G5** storage consent grant | **CONDITIONAL** | Required only if the mirror or backup path is selected as a production source or destination. |
| **G6** register both webhooks | **NOT APPLICABLE** | There is no webhook to register. This is the gate most at risk of being "completed" out of habit; it has no counterpart in a Socket Mode release. |
| **G7** | **CLOSED — WONT-DO** | Owner decision 2026-08-06. Not re-raised here. |
| **G8** backup keypair with the private half off the host | **YES** | Unchanged and independent of transport. |

**Nothing in this table marks a gate satisfied.** G1 and G8 remain owner-only work, and G3's obligation is
restated rather than relaxed: an **empty allowlist must refuse everyone**, and that is verified by observing
a refusal, never by reading a value back.

---

## What replaces the webhook verification block

The five negative cases the Telegram path verified — missing secret token, wrong secret token, sender absent
from the allowlist, the same update twice, two bots emitting the same update identifier — do not disappear.
They are re-expressed for Socket Mode, and every one of them is observable **without** a public endpoint:

1. A connection presenting an invalid application token is refused.
2. A sender absent from the allowlist is refused **before any parsing**.
3. The same envelope delivered twice produces exactly **one** effect.
4. A reconnect does not re-process work already acknowledged.
5. A missing credential alias fails **readiness**, rather than degrading quietly to an unauthenticated mode.

Cases 3 and 4 are the substance of **D-SLACK-1**: one consumer per envelope.

---

## Revoked aliases stay refused

The refusal tests for the five revoked Telegram aliases are **retained**, not removed as obsolete. An alias
that is merely unused comes back; an alias that is refused by an assertion does not. Removing those tests
because "Telegram is gone" is how it would return.

**A `telegram*` symbol name in the tree is historical naming, not a live binding.** `TELEGRAM_SEND_REFUSED`
is the name of a *refusal*, and it is load-bearing: `createBindableReplySender` throws it when no transport
is bound, which is what keeps an unbound deployment from silently dropping replies.
