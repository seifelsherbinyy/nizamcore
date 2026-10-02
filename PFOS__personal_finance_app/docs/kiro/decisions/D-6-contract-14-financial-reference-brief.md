# Decision brief D-6 — does a receipt-backed financial response need a Contract 14 amendment?

**Contract:** PFOS Contract 14 §11. **Task:** NIZAM-SLACK-FINANCE-007, track_u.
**Register:** this brief presents options and answers nothing. No box is checked. No option is
recommended as decided. The owner decides; I do not.

## 1. The text as it stands

`contracts/pfos/14_NIZAM_Single_Window_Telegram_Ingress.md`, §11 "Daily companion policy v3
(2026-09-15, Phase DC1)", occupies **lines 169–218**. The two sentences this brief turns on are at
approximately **line 178**:

> No monetary amounts or arbitrary source text cross this policy boundary. Financial alerts require
> PFOS provenance; unavailable PFOS means unavailable, not zero.

Supporting sentences that bear on the question, quoted from the same section:

- line ~181: `The adapter must validate source identity and freshness before mapping state, not trust
  user-provided boolean claims.`
- line ~199: `Mark delivery uncertain before invoking the outbound port; failed/ambiguous delivery is
  never automatically replayed.` … `An uncertain receipt is not proof a message was sent.`
- line ~205: `No scheduler permission confers a Hermes tool grant or financial/native write authority.`
- line ~214: `Synthetic reference retention: only closed policy/settings, date/cycle identity, bounded
  pillar revisions and outcome metadata; no raw conversation, journal, money, IDs or secrets.`

And the owning file's own header rule, `src/server/hermes/dailyMessages.ts` line 1: *closed bilingual
companion questions, no interpolation of native text, IDs or money.*

## 2. Is an amendment needed at all?

**The evidence says: for a reference-bearing response, probably not — and that is the cheapest possible
outcome, which is why it is stated first.**

The argument, in three steps:

1. The prohibition is on **amounts**. "No monetary amounts … cross this policy boundary" is specific.
   It is not "no financial content" and it is not "no monetary reference".
2. The very next clause **presupposes that financial alerts cross the boundary** and imposes a
   condition on them rather than forbidding them: "Financial alerts require PFOS provenance". A rule
   that conditions a thing is a rule that contemplates the thing existing.
3. The condition is **provenance**, which is precisely what an anchor (`canonical_state_version` plus
   `receiptRef`) supplies. And the failure mode is already specified in the owner's preferred
   direction: "unavailable PFOS means unavailable, not zero" — refusal, not a best-effort zero.

So a response of the shape *closed qualitative code + provenance anchor + no figure* appears to sit
**inside** current authority. Under that reading the design needs no amendment, and §12's
"Synthetic reference retention" line is consistent with it: a *bounded reference* is exactly what that
sentence permits to be retained, while "money, IDs or secrets" is what it excludes.

**Three reasons not to treat that reading as settled**, because I am not the authority on it:

- (a) `dailyMessages.ts`'s own header says "no interpolation of … money" without the value/reference
  distinction. It is narrower than §11 on its face, and it is the file that would change. Whether the
  header is a restatement of §11 or an independent stricter rule is a question about intent, not text.
- (b) §11 declares itself the **target Telegram-active policy, NOT activation**, and says sections 1–9
  retain existing live Slack-v2 behaviour. So it is arguable that §11 does not govern the Slack surface
  at all today, which would leave the Slack financial response governed by §§1–9 plus the file header.
  **This is the single most consequential ambiguity in the whole task** and it is not mine to resolve.
- (c) A reference still implies a figure exists and is material. Whether that itself is "a monetary
  amount crossing the boundary" in spirit is a judgement about the rule's purpose.

## 3. If an amendment IS needed: two drafted options and the do-nothing option

### Option A — clarify, do not widen

Add one sentence to §11, changing no permission:

> A provenance reference is not a monetary amount. A financial alert may carry a canonical state
> version and a receipt reference together with a closed qualitative code, and may carry no figure. An
> alert without both anchor components is not a weaker alert; it is a refusal.

- **Cost:** near zero. Grants nothing new; removes ambiguity (a) and (c) above. Does not resolve (b).
- **Risk:** if the owner's intent was in fact stricter than §11's text, this ratifies a reading the
  owner did not hold. That is the reason it is a decision and not an edit.

### Option B — permit a bounded figure, fenced

Add to §11:

> A financial alert may carry at most one monetary figure, only when anchored by a canonical state
> version and a receipt reference, only as an integer minor-unit value rendered through locale currency
> data, only for a settled quantity and never for a staged candidate or a projection, and never for
> more than one figure per message. An unanchored or stale figure must be withheld, not rounded,
> qualified or defaulted.

- **Cost:** materially higher, and the evidence says so. It re-opens the bidi hazard the current rule
  makes impossible — right-to-left text "commonly include[s] numerals … [which] typically flow
  left-to-right within the overall" flow (evidence S039, W3C inline bidi markup, ASSESSED), requiring
  `U+2066`/`U+2067` isolation (S040, W3C bidi Unicode controls, ASSESSED). It makes staleness dangerous
  instead of self-revealing: a stale
  reference sends the owner to a record whose own version is visible, while a stale figure is believed.
  It puts a figure in a durable channel where minimisation says data must be "limited to what is
  necessary" (S085, GDPR Art. 5, ASSESSED). And it requires the currency's minor-unit exponent to be
  treated as data rather than a constant (S058, MDN `Intl.NumberFormat`, ASSESSED — "The Japanese yen
  doesn't use a minor unit").
- **Benefit, stated honestly because the brief must not stack the deck:** it is the only option that
  answers Q2 (spend-shaped) and improves Q6 (explain-this-change) without a redirect, and the
  accounting evidence does say a change should be reported with its composition rather than as a single
  delta (S007, IAS 7 Statement of Cash Flows, SCREENED as cited).

### Option C — do nothing

- **Cost, stated plainly:** the financial pillar stays a redirect. `MAL_PFOS` continues to read "A
  fresh PFOS alert needs review. Open the authoritative finance view for figures." One of seven
  question classes (Q7, meta) is answerable in-channel; six are not. The owner keeps opening the
  authoritative view to discover that nothing needed attention.
- **Not zero-benefit:** it is the only option with no new leakage surface, and it is the correct choice
  if ambiguity (b) resolves against §11 governing Slack.

## 4. The transport residue established in P1 and P2

Measured on disk today, and my counts govern per the probe instruction:

| | case-insensitive | case-sensitive |
|---|---|---|
| Slack | **39** | 28 |
| Telegram | **22** | 18 |

The supervisor's stated 32 / 19 is **not reproduced by either method** and the discrepancy is reported
rather than reconciled. The *direction* of the supervisor's claim holds: the body is substantially
amended toward Slack.

The residue is three-way and each part needs a different document changed:

1. **Body versus its own title.** The file is named `14_NIZAM_Single_Window_Telegram_Ingress.md` and
   titled for Telegram ingress, while §§1–9 describe live Slack-v2 behaviour and §11 describes a
   *target* Telegram policy. A reader cannot tell from the filename which transport governs.
   *Change needed:* the filename and title, plus a one-line scope statement per section saying which
   transport it governs.
2. **§10 versus §11 versus §12.** §10 is "Telegram restoration preparation", §11 is a Telegram-active
   *target* policy, §12 is "Dual-channel memory preparation". Three sections describe a future
   transport state at three different levels of commitment.
   *Change needed:* a single status line stating which of the three is in force.
3. **Contract 14 versus PFOS v1.3 FINAL on Drive**, which was authored Telegram-first.
   *Change needed:* an amendment to the PFOS master, on Drive, which is outside this repository.

**Ownership:** the cutover is owned by `telegram-window` and `hermes-governed-workflows`, **not** by
this task. Nothing here proposes performing it. The stored transport-policy position — Slack Socket
Mode as sole transport with Telegram aliases revoked — is consistent with §§1–9 being the live rule and
§§10–12 being preparation, which is a further reason to read (b) carefully rather than assume it.

## 5. What answering this brief does not do

- It does **not** substitute for **Phase 1b design approval**.
  `.kiro/specs/financial-snapshot-interface/design.md` line 9 reads: *Status: DESIGN ONLY. No `src/`
  code is authorized.* That is an independent precondition with its own gate. Granting Option A or B
  would still leave `stateUseReceipt.ts` unwritten and unauthorised, and therefore still leave every
  anchor-dependent question class refusing.
- It does not advance any of G1–G8, and **G7 stays CLOSED as WONT-DO**.
- It does not bind a transport. D-B stands at **(c) injected ports and mocks**.
- It answers no other open decision. D-H, D-M and D-V stay **None offered**. G-10, F6 and F12 stay
  open.

## 6. Decision requested

One selection from {A, B, C}, plus a ruling on ambiguity **(b)** — whether §11 governs the Slack
surface today or whether §§1–9 plus the `dailyMessages.ts` header do. **(b) is worth more than the
A/B/C choice**, because if §11 does not govern Slack then the reference argument in §2 rests on a
section that does not apply, and the analysis must be redone against §§1–9.

**None offered.**
