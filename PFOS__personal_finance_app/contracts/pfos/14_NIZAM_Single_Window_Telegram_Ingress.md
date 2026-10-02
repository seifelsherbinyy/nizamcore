# NIZAM Single-Window Slack Ingress

> **PROVENANCE: NIZAM-DERIVED.** Originally authorised by the owner's 2026-08-24 Option B
> decision (one primary Telegram bot). Amended 2026-08-31 by owner decision: Telegram killed
> completely; Slack Socket Mode replaces it as the sole conversational window.
> Derived from PFOS Contracts 06, 12, and 13, UPOI design sections 5 and 6, historical
> `two-agent-vps.md` isolation rules, `money-rules.md`, and `drive-db.md`.
>
> **Status:** IN FORCE for the ingress surface only. It does **not** supersede Contract 12
> isolation, Contract 06 store topology, or money/Drive invariants. Contract 13's two-bot
> *Telegram identity* drawing is replaced entirely for live traffic; its internal
> dual-profile, dual-store, dual-cap drawing remains.
>
> **v2 change:** Telegram is revoked at all levels. All Telegram bot aliases are no longer
> live. Slack credentials replace them. The routing contract, store isolation, and money
> rules are unchanged.
>
> **Privacy:** architecture and aliases only. No secret values, hostnames, workspace IDs,
> Slack member IDs, channel IDs, Drive IDs, webhook paths, or ledger figures.

## 1. Purpose

Give the owner one Slack workspace window that can switch between NIZAMCORE life work and
PFOS/MAL financial work without merging repositories, stores, or financial authority.

## 2. Topology

```text
USER
 └─ Slack (Desktop / Mobile)
      └─ NIZAM Hermes App  (Socket Mode, agent view)
           → Hermes gateway (one process, one allowlist)
                → NIZAM ingress router (deterministic first)
                     ├─ nizam tools   TAFRIGH YAWMIYAT SHURA NAQD QARAR THABAT
                     └─ pfos tools    deterministic PFOS/MAL only
```

Slack is an interface. Hermes is an execution runtime. The router is governance, not
a second money engine. Profiles `nizam` and `pfos` remain internal tool/store/cap
boundaries. They are not separate live Slack identities.

## 3. What stays isolated (unchanged from v1)

- `life.db`, `finance.db`, and `signals.db` remain separate. No cross-database ATTACH.
- OpenRouter keys and weekly caps remain distinct (`OR_KEY_LIFE` / `OR_KEY_FINANCE`,
  `LIFE_WEEKLY_CAP` / `FINANCE_WEEKLY_CAP`) even when only one Slack app is live.
- PFOS remains the only writer and the only source of monetary magnitudes.
- Integer milliunits only. One EGP = 1000 milliunits. No floating-point money.
- Drive remains `drive.file` only and never stores keys.
- Strict-local material has no egress path.
- Human gates G1 through G8 stay human. This contract does not complete, test, or mark them.

## 4. What changes (v2)

- All Telegram bot aliases are revoked: the owner revokes through BotFather and confirms
  no live poller exists before the Slack gateway starts.
- Live Slack ingress uses exactly two Hermes credentials: `SLACK_BOT_TOKEN` (xoxb prefix)
  and `SLACK_APP_TOKEN` (xapp prefix, `connections:write` scope for Socket Mode).
- Allowlist migrates to `SLACK_ALLOWED_USERS` (Slack member IDs). The `ALLOWED_USER_IDS`
  alias maps to this entry.
- Channel restriction uses `SLACK_ALLOWED_CHANNELS` and `SLACK_HOME_CHANNEL` for scheduled
  delivery. All other channels are ignored by policy.
- A stolen bot token reaches the Slack window only. Internal grants still fail closed, so
  the token is not a second PFOS writer.
- Mention requirement is enforced in channel contexts (`require_mention: true`). DM to the
  Hermes app requires no mention. Thread continuation in an active Hermes session requires
  no repeat mention.
- Bot-to-bot triggering is disabled (`allow_bots: none`).

## 5. Routing rule (unchanged from v1)

Classification is deterministic first. An LLM may explain a routed result; it may not
choose a monetary figure or widen a grant.

| Message class | Target | Authority |
|---|---|---|
| dump / journal / yawmiyat | nizamcore journal tools | nizamcore |
| plan / debate / critique | SHURA / NAQD tools | nizamcore |
| decision / continuity | QARAR / THABAT | nizamcore |
| money / budget / debt / forecast / balance | `pfos.*` | PFOS engines |
| mixed narrative plus money | nizamcore narrative plus PFOS facts by reference | both; numbers from PFOS only |
| secret, host, credential, commit, unknown write | refuse / `BLOCKED_HUMAN` | nobody |

Weak classification produces one clarifying question and zero effect.

## 6. Secret aliases this contract names (v2)

Named only. Values never appear in this repository.

- Live ingress: `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`
- Allowlist: `SLACK_ALLOWED_USERS` / `ALLOWED_USER_IDS`
- Channel config: `SLACK_HOME_CHANNEL`, `SLACK_ALLOWED_CHANNELS` (not secrets; operator sets)
- Kill switch: `NIZAM_KILL_ALL`
- Model: `OR_KEY_LIFE` (ingress default), `OR_KEY_FINANCE` (PFOS tool path)
- Revoked: all Telegram bot aliases (see ALIAS_REGISTRY for the full revocation list)

The approved holding place on the host is a root-owned mode-600 environment file.
Chat, tickets, tracked docs, Drive, and Git are not approved secret homes.

## 7. Acceptance

Offline: ingress policy tests, router tests, gateway-template audit, secret-scan clean.
Live (human, later): Slack app created from Hermes manifest; credentials installed on VPS;
Telegram pollers stopped and tokens revoked; Hermes gateway started; DM round-trip succeeds;
PFOS route returns integer milliunits; journal route creates local record; unauthorized
channel ignored; unauthorized user DM ignored; slash commands work; bot-to-bot triggering
blocked. `NIZAM_UNIFIED_RUNTIME_READY` is printed only after those live observations.

## 8. Hermes Slack configuration policy

The Hermes gateway process for `nizam-ingress` uses Socket Mode. The Slack app is created
from the Hermes-generated manifest (`hermes slack manifest --agent-view --write`). No manual
scope or event invention. The app name in the owner's private Slack workspace is `NIZAM Hermes`.

Slack AI is a separate optional retrieval layer. It does not replace NIZAM persistence or
financial truth. Canonical state path: Slack to Hermes to HIMAYAH to NIZAM to approved
local/Drive/GitHub persistence. Never: Slack as memory, Slack as ledger, Slack as journal.

## 9. Owner-only offline composition

`src/server/process/singleWindowFlow.ts` remains the offline rehearsal of the routing
window: one namespace, one allowlisted sender, deterministic routing, PFOS-only money,
local journal append, secret-seeking refusal. Platform credential checks are bypassed in
the offline mode by design.


## 10. Telegram restoration preparation (2026-09-15, local-only authority)

**PROVENANCE: NIZAM-DERIVED.** The owner requested a Telegram window plan and then directed
execution on 2026-09-15. This section governs local preparation and synthetic work only.
It does not assert Telegram is live or a credential is valid.

**Precedence:** sections 1-9 and v2 Telegram revocation checks remain current live policy.
This section permits a separately versioned restoration design and offline rehearsal; it
never re-enables revoked aliases, switches a gateway, weakens acceptance checks or silently
replaces Slack. Live policy selection requires an explicit reviewed cutover.

Target: one owner-only private text conversation, exactly one update consumer, separate
life/finance stores/keys/caps/grants. NIZAM governs; Hermes executes bounded grants; PFOS alone
sources money and writes finance. One EGP = 1000 integer milliunits. Drive remains encrypted
data only under `drive.file`; strict-local material has no VPS/model/Drive egress. Telegram
is an interface, not canonical storage or end-to-end encryption. No unrestricted shell,
host, credential or deployment tool is reachable through chat.

Requirements TW01-TW15 and design/tasks are in `.kiro/specs/telegram-window/`. Initial scope
excludes financial writes, attachments, voice, reminders and Mini Apps. Capture/continue stays
unavailable until native writer/privacy/idempotency/read-back/recovery are reconciled.
Metadata-only events are not saved content. Retry preserves effect identity and reuses
recorded results; uncertain reply delivery cannot rerun a canonical effect or claim
exactly-once Telegram delivery.

A credential exposed in chat is not used by this workflow. Owner supplies a protected
replacement by reference, never in tracked documents or chat. No real secret/deployment
identifier enters source, test, fixture, log, argv or prompt. Private sender/chat identity
handoff and installed-runtime alias mapping remain dependencies, not assumed facts.

Never execute, test, populate, substitute values into or mark complete either
`ops/GATE_REGISTER.md` or `ops/DEPLOYMENT_CONTROL.md`. G1-G8 remain human. No credential
lifecycle, host mutation, production spend, external send, native-repository modification,
commit or push is authorized here. Preserve user edits and all acceptance checks. A new
policy/check conflict must stop for explicit review, never relaxed assertions.

M0-M5 distinguish preparation, offline integration, live conversation, PFOS reads, verified
capture and operational acceptance. Lower milestones do not certify higher ones. Current
native inspection and scoped live authority remain prerequisites. Handoff:
`docs/plans/nizam-telegram-window-installation-plan.md`.


## 11. Daily companion policy v3 (2026-09-15, Phase DC1)

**PROVENANCE: NIZAM-DERIVED.** **Scope decision D-7, owner answered Reading A on 2026-09-22:**
this section governs every approved conversational window, including Slack. This clarifies which window
the existing policy governs; it activates no transport and widens no permission. The owner's daily
operating companion request extends
section 10's offline scope to adaptive proactive cycles and controls. Version identifier:
`telegram-companion-v3`. This defines the target Telegram-active policy, NOT activation.
Sections 1-9 retain their existing live Slack-v2 behavior and acceptance checks. No alias
revocation is undone. Section 10's reminder deferral is superseded for offline DC1 only.

Governing specification: `.kiro/specs/telegram-daily-companion/{requirements,design,tasks}.md`.
Reuse Contract 12's storeless clock. A life-owner tick handler evaluates policy; the clock
never acquires a store, model, credential or domain authority. This repository may build
pure policy, injected orchestration and a SQLite synthetic reference adapter. It must NOT
install another life writer, open native life data, or add companion data to finance.db.
The native owner's approved persistence/retention adapter is a live prerequisite.

Priority is HIMAYAH, SUKOON, urgent obligations, authoritative PFOS risk, THABAT,
SHURA/QARAR, BADAN, reflection, then NAQD. Missing recovery is not high capacity.
Only fresh approved bounded state participates. No monetary amounts or arbitrary source
text cross this policy boundary. Financial alerts require PFOS provenance; unavailable
PFOS means unavailable, not zero. The adapter must validate source identity and freshness
before mapping state, not trust user-provided boolean claims. No journal writer is called;
reflection is conversation, never an acknowledgement of durable capture.

Proactive delivery is disabled without explicit enabled policy, configured timezone/windows,
owner/private-chat authorization, consent and kill-gate permission. Quiet hours, pause,
skip-today and bounded global/per-pillar snooze override every proactive priority. Each tick
selects at most one cycle and one bundled plan, with at most three items/questions (one in
low/unknown capacity). Weekly replaces a colliding cycle rather than doubling messages.
Missed windows are skipped; no backlog flood. Duplicate local-day/cycle identities and
already reserved pillar revisions are suppressed across restart; source revisions must be
monotonic per pillar. A repeated DST hour cannot produce another local-day/cycle message.

Settings and run reservation use atomic persisted compare-and-set. Persist the bounded plan
before dispatch. Reserve content revisions in the same transaction. Mark delivery uncertain
before invoking the outbound port; failed/ambiguous delivery is never automatically replayed.
This deliberately prefers a potentially missed prompt to duplicate delivery. An uncertain
receipt is not proof a message was sent. Settings changed before dispatch cancel the old
plan. Native dispatch must also check the current auth/consent/kill fence at the actual effect.
No scheduler permission confers a Hermes tool grant or financial/native write authority.

Synthetic reference retention: only closed policy/settings, date/cycle identity, bounded
pillar revisions and outcome metadata; no raw conversation, journal, money, IDs or secrets.
Keep receipts/tombstones until an explicitly reviewed retention/migration policy preserves
replay protection. No automatic purge, no Drive upload, no production retention claim.
Native configuration, privacy/freshness sources, consumer ownership, protected replacement
credential, approved retention and governed runtime remain mandatory live prerequisites.
No external send, host change, credential lifecycle, production spend, native-repository
write, human-gate action, commit or push is authorized by DC1.


## 12. Dual-channel memory preparation (2026-09-16, Phase 14.2)

**PROVENANCE: NIZAM-DERIVED.** Owner approved preparing Telegram alongside working Slack
and requested channel-aware responses and memory on VPS and Google Drive. Target policy:
`dual-channel-memory-v1`. This supersedes single-channel-only target design for this offline
preparation, not the current Slack-v2 live behavior, alias checks or activation gates.
No live switch, token transfer, service restart, provider spend or upload is authorized here.

Both transports map separately authenticated identities to the same protected owner reference.
Transport metadata, not message text or the LLM, selects the origin and reply destination.
Replies retain platform/account/conversation/thread; no automatic cross-post or fallback.
Slack approved channels/threads retain existing enrollment; Telegram remains owner-only private
chat. Bot messages and unrecognized configuration fail closed before memory/model execution.
One Telegram consumer only. No Slack shutdown is implied by dual-channel preparation.

One native canonical memory writer on VPS; Drive is the approved encrypted replica/archive
of that record/version, not a second competing brain writer. This server-memory rule does not
change the financial application's Drive-as-database steering. No new native DB or second
journal/finance writer is introduced. PFOS stays the only financial writer and money source.

Memory provenance includes origin platform, direction, owner/profile-scoped conversation
reference, event reference and time. Stable replay identity includes platform, ingress account,
conversation/thread, provider event, owner/profile and direction; different channels never
collide. Duplicate transport delivery is not another memory. Same key/different content is
refused by the canonical writer. Explicit cross-channel continuity may retrieve approved
owner/profile memory; it never joins raw sessions or changes reply destinations by default.
Raw provider IDs live only in the protected transport binding, not prompts/logs/Drive metadata.
Hashed references remain private pseudonyms, not anonymous or automatically cloud-safe data.

VPS saved requires independent canonical read-back for the expected record/version/hash;
metadata-only events are not saved content. Drive synced additionally requires approved
privacy, `drive.file` only, encryption attestation and matching ciphertext hash/version from
independent remote read-back bound to that same source version/hash. Provider send success
is neither memory success nor sync. No arbitrary boolean from an LLM is a valid receipt.
Receipt adapters must be trusted native ports, not user-submitted evidence.

No raw transcript retention policy is inferred from this request. Native HIMAYAH classification,
consent, approved retention and sole-writer wiring precede real-content recording. Secrets
and strict-local material cannot enter this VPS/Drive path. Drive failure retains verified
local state and a pending sync status; retry mirrors the same record/version without rerunning
conversation/domain effects. Keys/secrets never go to Drive. Actual encryption, remote upload,
native writer recovery and live end-to-end channel tests remain separate prerequisites.

Specification: `.kiro/specs/dual-channel-memory/{requirements,design,tasks}.md`.
