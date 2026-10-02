# Decision brief D-7 — which window does Contract 14 §11 govern?

**Status: ANSWERED 2026-09-22 by the owner — Reading A. Contract 14 §11 governs every approved
conversational window, including Slack. No permission is widened.**
**Task:** NIZAM-FINAL-009 item E. **Authority:** Contract 14, Contract 12, the four preserved window
specs, and the server/agent/bot steering hierarchy. **Phase:** governance decision record, no runtime act.

## OWNER DECISION — D-7 ANSWERED 2026-09-22

**Selected: Reading A.** Contract 14 §11 governs every approved conversational window, including Slack.
This is a scope ruling over the existing safety rules, not a transport activation and not a permission
widening. Monetary amounts and arbitrary source text remain forbidden; PFOS provenance, freshness,
silence, controls, durable reservation and no-blind-replay requirements remain unchanged. Telegram-
specific authentication terms remain adapter obligations only where Telegram is the approved transport.
Phase 1b approval remains separate and is not granted by this decision.

## 0. Why this question outranks the earlier A/B/C amendment choice

The reference-not-value design rests on Contract 14 §11. If §11 governs Slack, its text explicitly
forbids monetary amounts while requiring PFOS provenance for financial alerts, which supports a
reference-bearing response. If §11 governs Telegram only, that argument is being made from a section
that does not apply to the Slack surface. In that reading Slack is not thereby permitted; it is
**ungoverned**, and `two-agent-vps.md` §5 makes absent authority a reason not to build, not a licence.

This brief therefore asks the scope question before asking whether §11 needs a clarification or a
figure-bearing amendment. It does not decide either.

## 1. Contract 14 §11, in full with line numbers

Source: `contracts/pfos/14_NIZAM_Single_Window_Telegram_Ingress.md`, measured on disk in this session.

```text
169: ## 11. Daily companion policy v3 (2026-09-15, Phase DC1)
170:
171: **PROVENANCE: NIZAM-DERIVED.** The owner's daily operating companion request extends
172: section 10's offline scope to adaptive proactive cycles and controls. Version identifier:
173: `telegram-companion-v3`. This defines the target Telegram-active policy, NOT activation.
174: Sections 1-9 retain their existing live Slack-v2 behavior and acceptance checks. No alias
175: revocation is undone. Section 10's reminder deferral is superseded for offline DC1 only.
176:
177: Governing specification: `.kiro/specs/telegram-daily-companion/{requirements,design,tasks}.md`.
178: Reuse Contract 12's storeless clock. A life-owner tick handler evaluates policy; the clock
179: never acquires a store, model, credential or domain authority. This repository may build
180: pure policy, injected orchestration and a SQLite synthetic reference adapter. It must NOT
181: install another life writer, open native life data, or add companion data to finance.db.
182: The native owner's approved persistence/retention adapter is a live prerequisite.
183:
184: Priority is HIMAYAH, SUKOON, urgent obligations, authoritative PFOS risk, THABAT,
185: SHURA/QARAR, BADAN, reflection, then NAQD. Missing recovery is not high capacity.
186: Only fresh approved bounded state participates. No monetary amounts or arbitrary source
187: text cross this policy boundary. Financial alerts require PFOS provenance; unavailable
188: PFOS means unavailable, not zero. The adapter must validate source identity and freshness
189: before mapping state, not trust user-provided boolean claims. No journal writer is called;
190: reflection is conversation, never an acknowledgement of durable capture.
191:
192: Proactive delivery is disabled without explicit enabled policy, configured timezone/windows,
193: owner/private-chat authorization, consent and kill-gate permission. Quiet hours, pause,
194: skip-today and bounded global/per-pillar snooze override every proactive priority. Each tick
195: selects at most one cycle and one bundled plan, with at most three items/questions (one in
196: low/unknown capacity). Weekly replaces a colliding cycle rather than doubling messages.
197: Missed windows are skipped; no backlog flood. Duplicate local-day/cycle identities and
198: already reserved pillar revisions are suppressed across restart; source revisions must be
199: monotonic per pillar. A repeated DST hour cannot produce another local-day/cycle message.
200:
201: Settings and run reservation use atomic persisted compare-and-set. Persist the bounded plan
202: before dispatch. Reserve content revisions in the same transaction. Mark delivery uncertain
203: before invoking the outbound port; failed/ambiguous delivery is never automatically replayed.
204: This deliberately prefers a potentially missed prompt to duplicate delivery. An uncertain
205: receipt is not proof a message was sent. Settings changed before dispatch cancel the old
206: plan. Native dispatch must also check the current auth/consent/kill fence at the actual effect.
207: No scheduler permission confers a Hermes tool grant or financial/native write authority.
208:
209: Synthetic reference retention: only closed policy/settings, date/cycle identity, bounded
210: pillar revisions and outcome metadata; no raw conversation, journal, money, IDs or secrets.
211: Keep receipts/tombstones until an explicitly reviewed retention/migration policy preserves
212: replay protection. No automatic purge, no Drive upload, no production retention claim.
213: Native configuration, privacy/freshness sources, consumer ownership, protected replacement
214: credential, approved retention and governed runtime remain mandatory live prerequisites.
215: No external send, host change, credential lifecycle, production spend, native-repository
216: write, human-gate action, commit or push is authorized by DC1.
217:
218:
```

## 2. Measured transport distribution across the authority set

**Method:** case-insensitive, non-overlapping literal occurrence counts of `Slack` and `Telegram` over
the file bytes decoded as UTF-8. These are vocabulary counts, not votes and not a precedence rule.

**Inclusion rule:** every local file that is authority under the repository's own precedence model and
explicitly touches the conversational window: (a) each PFOS contract containing either term; (b) the
`requirements.md`, `design.md` and `tasks.md` authority triplets for `telegram-window`,
`telegram-daily-companion`, `dual-channel-memory` and `hermes-governed-workflows`; and (c) the applicable
server/agent/bot steering file `two-agent-vps.md`. Dated inspections, verification receipts, checklists,
build logs, contract indexes and plans are evidence, not authority, so they are excluded from this table.
The previously retrieved PFOS v1.3 FINAL snapshot is not present in this workspace, so no fresh count is
invented for it; its Telegram-first posture remains prior evidence, not a measurement in this table.

| Authority file | Slack | Telegram |
|---|---:|---:|
| `contracts/pfos/01_PFOS_Product_Constitution_and_Problem_Solution_Logic.md` | 0 | 3 |
| `contracts/pfos/02_PFOS_Data_Architecture_Integrations_and_Security.md` | 0 | 14 |
| `contracts/pfos/04_PFOS_UX_UI_User_Journeys_Research_and_Delivery_Roadmap.md` | 0 | 8 |
| `contracts/pfos/05_AGENTIC_PROFILE_BASELINE.md` | 2 | 0 |
| `contracts/pfos/05_PFOS_Agent_Orchestration_Skill_and_Knowledge_Integration.md` | 0 | 3 |
| `contracts/pfos/12_PFOS_Two_Agent_VPS_Deployment_and_Operations.md` | 0 | 4 |
| `contracts/pfos/13_NIZAM_v1.4_Production_Controller_Delta.md` | 0 | 5 |
| `contracts/pfos/14_NIZAM_Single_Window_Telegram_Ingress.md` | **39** | **22** |
| `contracts/pfos/15_NIZAM_Daily_Transaction_Capture_and_Candidate_Staging.md` | 0 | 2 |
| `.kiro/specs/telegram-window/requirements.md` | 2 | 3 |
| `.kiro/specs/telegram-window/design.md` | 3 | 13 |
| `.kiro/specs/telegram-window/tasks.md` | 1 | 3 |
| `.kiro/specs/telegram-daily-companion/requirements.md` | 0 | 1 |
| `.kiro/specs/telegram-daily-companion/design.md` | 2 | 1 |
| `.kiro/specs/telegram-daily-companion/tasks.md` | 0 | 0 |
| `.kiro/specs/dual-channel-memory/requirements.md` | 1 | 2 |
| `.kiro/specs/dual-channel-memory/design.md` | 3 | 3 |
| `.kiro/specs/dual-channel-memory/tasks.md` | 0 | 1 |
| `.kiro/specs/hermes-governed-workflows/requirements.md` | 4 | 20 |
| `.kiro/specs/hermes-governed-workflows/design.md` | 24 | 71 |
| `.kiro/specs/hermes-governed-workflows/tasks.md` | 7 | 14 |
| `.kiro/steering/two-agent-vps.md` | 0 | 3 |
| **Total across this defined set** | **88** | **196** |

The distribution exposes the residue rather than resolving it:

- Contract 14's provenance header says Telegram was killed completely and Slack Socket Mode replaced it
  as the sole window. Its §§1-9 are Slack-first, and its own count is 39/22.
- The older contracts and the future/cutover specs remain Telegram-heavy, so the total authority corpus is
  88/196. Historical naming and future preparation dominate raw vocabulary.
- `hermes-governed-workflows` is explicit: Slack Socket Mode is the sole transport, Telegram aliases are
  revoked, `telegram*` symbol names are historical, and the preserved window specs are not superseded.
- The `telegram-window` spec is equally explicit that Contract 14 v2 remains policy until a separately
  reviewed cutover and that there is no simultaneous activation or automatic Slack fallback.
- Section 11 itself says both `target Telegram-active policy, NOT activation` and `Sections 1-9 retain
  their existing live Slack-v2 behavior`. That is the conflict this brief asks the owner to resolve.

## 3. Three candidate readings

### Reading A — §11 governs every conversational window, including Slack

**Text supporting it:** §11 is inside Contract 14, whose document-level status says Slack is the sole
window. Its safety rules are phrased as policy boundaries, not as provider API details: fresh approved
state, no monetary amounts, PFOS provenance, quiet controls, durable reservation, uncertain-before-send,
no automatic replay and no financial/native write authority.

**If true:** the reference-not-value design is governed now. A Slack financial response may carry a
bounded qualitative code plus PFOS provenance, may carry no amount, and must refuse when PFOS or its
receipt is unavailable. Telegram-specific identity and activation language remains a future adapter
concern rather than the scope of the policy.

**Unsafe under this reading:** copying `owner/private-chat` literally into Slack and treating it as Slack
authorization would confuse provider identity models. Treating §11's policy permission as transport
activation would also be unsafe: lines 173 and 215-216 explicitly deny activation and external send.

### Reading B — §11 governs the Telegram window only; Slack's daily financial response is ungoverned

**Text supporting it:** the section calls itself `telegram-companion-v3`, defines a `target
Telegram-active policy`, extends section 10's Telegram restoration scope, requires owner/private-chat
authorization, and points to a spec titled Telegram daily companion. It separately says §§1-9 retain
Slack-v2 behavior, which can be read as excluding Slack from §11 rather than including it.

**If true:** §§1-9 still govern Slack ingress and routing, but no authority in §11 governs the proactive
Slack financial-pillar answer. The reference-not-value argument cannot use §11, and the offline response
assembler must remain unregistered while a Slack-specific policy amendment is authored and approved.

**Unsafe under this reading:** interpreting “ungoverned” as “permitted.” Under `two-agent-vps.md` §5,
missing authority blocks the area. It does not create discretion. Binding `financialPillarTick`, emitting
a reference, or importing Telegram private-chat assumptions into Slack would each act before authority
has spoken.

### Reading C — §11 governs by transport-neutral intent; its Telegram framing is vestigial

**Text supporting it:** nearly every consequential sentence in lines 184-216 is transport-neutral, while
the provider-specific words are concentrated in the version/status framing at lines 171-177 and the
authorization noun at line 193. Contract 14's document-level amendment and §§1-9 already moved to Slack,
and `hermes-governed-workflows` says `telegram*` names may be historical rather than bindings.

**If true:** the cadence, provenance, silence, retention and durable-intent rules govern Slack today, but
the filename, title, version identifier, governing-spec name and private-chat terminology are stale. A
clarifying amendment should rename those surfaces without widening any permission.

**Unsafe under this reading:** treating “vestigial” as a self-executing edit. Until the owner adopts this
reading, a future maintainer can reasonably read the same words as Reading B. Building or binding on an
unrecorded interpretation would make the safety case depend on preference rather than authority.

## 4. Decision surface and consequences

| Choice | Immediate engineering consequence | Contract/document consequence |
|---|---|---|
| **A** | Keep the built assembler behind injected ports; registration still withheld for the missing receipt. | Add a one-sentence scope clarification that §11 applies to every approved conversational transport; retain Telegram adapter prerequisites as conditional. |
| **B** | Keep the assembler and tick handler unregistered; do not rely on §11 for Slack output. | Author and approve a Slack financial-pillar policy before any registration. Do not delete §11; it remains Telegram-target preparation. |
| **C** | Same as A on policy behaviour; no transport act follows. | Rename/reframe §11 and its governing spec in a reviewed amendment, preserving every substantive safety rule byte-for-byte in meaning. |

**None offered.** The owner selects A, B or C. This brief marks nothing complete and changes no contract.

## 5. Independent precondition: Phase 1b

Whichever reading the owner chooses, Phase 1b design approval remains an independent precondition.
`.kiro/specs/financial-snapshot-interface/design.md` states: **“DESIGN ONLY. No `src/` code is
authorized.”** `stateUseReceipt.ts` therefore does not exist. A scope ruling does not create a canonical
state version, a state-use receipt, a freshness proof or permission to build that module. Without the
receipt, six of seven financial question classes still refuse.

## 6. Boundaries this brief does not move

- Slack Socket Mode remains the sole current transport under `hermes-governed-workflows`; Telegram
  cutover remains owned by `telegram-window` and `hermes-governed-workflows`.
- `financialPillarTick` remains unregistered. `scheduler.ts` and its two-member `SCHEDULER_TARGETS` tuple
  remain untouched.
- D-H, D-M and D-V remain `None offered`. G5 and G8 remain unmarked. G7 remains CLOSED WONT-DO under prior
  owner authority and is not re-raised.
- No credential, consent, host, provider, transport, Drive write, commit or push action follows from this
  brief.
