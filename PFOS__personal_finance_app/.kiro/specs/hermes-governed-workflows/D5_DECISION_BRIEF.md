# D-5 decision brief — Drive encryption scheme and the candidate-egress fix

**Status: ANSWERED 2026-09-21 by the owner.** Authored 2026-09-20 under NIZAM-HYBRID-005 Track B (b3)
as a brief that answered nothing; the owner has since answered it.

> ## OWNER DECISION — D-5 ANSWERED 2026-09-21
>
> **Part 1 (Drive encryption scheme) = (a) WebCrypto, `crypto.subtle`, AES-GCM.**
> **Part 2 (candidate egress, F5) = (c) single serialisation-time projection.**
> **Part 3 = (e) CLOSED, `drive-db.md` as amended holds** (already settled by D-S(a)).
>
> Recorded with **four binding conditions**:
>
> 1. **(a) is a choice of MECHANISM, not an authorization to ship encryption.** It permits
>    `payloadEnvelope.ts` to be authored. It does NOT permit a key to be generated, named, held or
>    placed anywhere. **G8 (backup keypair) and G5 (storage consent) remain owner-only and unmarked.**
>    "D-5 answered" must never be read or reported as "encryption shipped".
> 2. **The two parts differ in gating and are sequenced accordingly.** (c) needs no key and no gate, so
>    it lands first. (a) unblocks module authorship immediately but its live rollout waits on G8.
> 3. **(c)'s refactor must be proven by the F17 fence tests that ALREADY EXIST**
>    (`src/lib/db/candidateFence.test.ts`, three Drive-payload assertions), not by new tests authored to
>    fit the refactor. If a test has to change shape to accommodate the projection, stop and report.
> 4. **D-G is answered-by-D-5 with an explicit scope limit.** It makes the I0 modules buildable and lets
>    the projection helper move out of `candidateFence.test.ts` into production. It does **NOT** authorize
>    increment 10's coherence-and-mirroring work, which still has **F6 (`If-Match`) and F12 (tombstones)**
>    as independent preconditions. **G-10** (readable financial context) stays separately OPEN; (e) does
>    not drift into permitting a readable mirror.
>
> **Evidence verified on disk before signing, 2026-09-21:** H.1 real at `driveDb.ts:76` (live db) and
> `:108-111` (snapshots) — two plaintext sites, not one. Zero `crypto.subtle` anywhere in `src`.
> `engines` pins `node >=24 <25`, so WebCrypto is native and (a) adds no dependency. F5 real at
> `src/lib/drive/sync.ts:194`.
>
> **One finding sharper than this brief's own:** the property does not merely live in a comment. At
> `sync.ts:192` the comment reads *"Candidates are device-local ... not synced to Drive"* and at line
> **194**, two lines below, sits `transactionCandidates: local.transactionCandidates` inside the object
> that is serialised to Drive. The comment is **contradicted by the line it annotates** — true about
> merge semantics, false about egress. That is the decisive argument against (d): per-call-site
> convention is exactly what produced a comment that lies about the code beneath it.
>
> **Task 1.2's box is NOT checked by this answer.** Checking it remains the owner's separate act.

---

## 0. What this document is, and the one tension it has to declare

`tasks.md` task **1.2** is "Write the D-5 brief". This is that brief.

**But this spec's own gate says no task below may begin without Stage-1 plan approval**, and `design.md`
§0.5 records that *"Every increment in §F and §G is a plan for work that has not been approved yet."*
Stage-1 approval is **not** recorded anywhere in this spec. So writing this document is, read strictly,
beginning task 1.2 before its precondition.

**Why it is nonetheless the right thing to write, stated so the owner can overrule it.** D-5 is a
*decision*, not an implementation. It cannot be answered without a brief, and until it is answered **I0
cannot be written** — and I0 is the only thing that clears **F7/RG-5**, which is what currently stands
between a promoted canonical row and a figure the daily brief could cite. Holding the brief behind
Stage-1 approval would make the brief wait on the approval that the brief exists to inform. That is a
deadlock, and it is the same shape as the benchmark deadlock `two-agent-vps.md` §0 had to relocate.

**What this document therefore does NOT do.** It does not check task 1.2's box — that is the owner's act,
once they decide the precondition is satisfied. It claims no Stage-1 approval, writes no code, names no
file as created, and answers no decision. It contains no secret and no deployment particular.

---

## 1. D-5 got smaller: part 3 is already closed

D-5 was opened with three parts. **One of them has since been settled elsewhere**, and carrying it as open
would invite the owner to re-decide something already decided.

| Part | Subject | State |
|---|---|---|
| **1** | Drive encryption scheme | **OPEN** — options in §2 |
| **2** | Candidate egress (finding F5) | **OPEN** — options in §3 |
| **3** | The `drive-db.md`-vs-O1-§2.2 conflict | **CLOSED** — see below |

### 1.1 Part 3 is closed by D-S(a), with the citation

**D-S was answered (a) on 2026-09-20:** `.kiro/steering/drive-db.md` was amended so that **Drive is the
durable evidence and recovery mirror, and the server tier is canonical**, matching `tech.md` D1's
statement that the Drive-JSON store *"is the Profile-A build, NOT the final database."* The amendment
preserved the `drive.file`-only scope and the no-keys rule verbatim.

Task 1.2 framed part 3 as **(e)** `drive-db.md` holds, versus **(f)** amend toward a readable mirror.
**The outcome is (e) — `drive-db.md` as amended holds.** Three independent sources agree: the amendment
itself, `tech.md` D1, and PFOS v1.3 FINAL §42.1 (*"Google Drive is a one-way reviewed mirror/archive, not
the canonical live store"*, with C-06 CLOSED).

**Two precision points, because conflating them would undo the closure.**

1. **(e) does not mean "Drive is unchanged".** It means the amended `drive-db.md` governs. The amendment
   *moved* Drive from canonical to mirror. Choosing (e) endorses that move; it does not revert it.
2. **(e) is not the same as refusing a readable mirror forever.** The *readable-financial-context
   expansion* — recorded separately as **G-10** — is its own sub-decision and remains open. What part 3
   settles is which document is **authority**, not what that authority will eventually permit.

**Constraint carried forward, unchanged:** **do not design to O1 §2.2.** It is PROPOSED / CONFLICTED and
is not authority. `drive-db.md` as amended holds. This brief designs to nothing else.

---

## 2. Part 1 — the Drive encryption scheme

### 2.1 What forces the choice

`drive-db.md` requires that anything leaving the device for Drive be encrypted before upload, and PFOS
v1.3 FINAL §42.2 places *"live databases"* and *"full append-only ledgers"* in its **encrypt-before-upload**
tier, with API keys, tokens and `.env` content **forbidden outright**. Today `driveDb.ts` uploads the whole
database as raw `JSON.stringify` via `createTextFile` — **no application-level encryption at all**. That is
finding **H.1**, and it is one of the two risks that get *worse with time* rather than staying constant:
every day of delay adds a plaintext artifact that a later fix cannot retract.

### 2.2 Options

| # | Option | For | Against |
|---|---|---|---|
| **(a)** | **WebCrypto-based** — `crypto.subtle`, AES-GCM, key derived per `drive-db.md`'s custody rules | Zero new dependency, so nothing new enters the bundle or the supply chain. Available in both the browser and Node 24. Authenticated encryption, so a single-byte ciphertext mutation refuses rather than decrypting to garbage. | Lower-level: the envelope format, version field, nonce discipline and key-absent refusal all have to be written and tested here rather than inherited. |
| **(b)** | **Library-based** — an established encryption library | Less code to author; format decisions already made and reviewed. | A new runtime dependency on the **money-adjacent** path, which widens the supply chain for the most sensitive artifact in the system. `AC08b` already fences what may enter the bundle, and this would be a new thing to fence. |

### 2.3 Recommendation: (a)

Grounds, in order of weight:

1. **No new dependency on the evidence path.** The repository's whole posture is that the sensitive tier
   carries as little third-party surface as possible. A crypto library is exactly where a supply-chain
   compromise would be most damaging and least visible.
2. **AES-GCM gives the refusal semantics the design already demands.** §G.0's acceptance requires that a
   mutated ciphertext **refuse** and that an undecryptable payload yield *"an explicit refusal, never a
   silent empty db."* Authenticated encryption makes that the default rather than something to remember.
3. **The format work is not the expensive part.** The version field, the key-absent refusal and the
   legacy-plaintext detection path have to exist under either option, because they are about *this
   repository's* migration from plaintext, not about the cipher.

**What (a) does not decide, and must not be read as deciding:** key generation, custody, rotation and the
backup keypair are **G8** and **owner-only**. This is a choice of *mechanism*, not a grant to mint or hold
a key. `two-agent-vps.md` is explicit — never invent a secret value, never place a key on Drive.

---

## 3. Part 2 — the candidate-egress fix (finding F5)

### 3.1 What is actually wrong

`sync.ts` keeps transaction candidates local on **merge**. But `driveDb.ts` serialises the **whole
database** for upload, and that serialisation **includes `transactionCandidates`** — so candidates leave
the device despite the merge-side intent. The property is asserted **nowhere**: it exists only as a comment.

This matters more under Contract 6 §5 than it did when F5 was opened. **I5.2** now states that a candidate
*"is not financial truth and MUST NOT be counted in any balance, budget, forecast or report."* A candidate
that has been mirrored to Drive is a candidate that has escaped the staging boundary I5.2 creates.

**And encryption does not fix it.** An encrypted payload still *contains* the candidates; the owner's key
decrypts them; and if the readable-mirror expansion (G-10) is ever taken, they become visible. The design
already records this — encryption and exclusion are two different fixes for two different problems, and
part 1 does not subsume part 2.

### 3.2 Options

| # | Option | For | Against |
|---|---|---|---|
| **(c)** | **Single serialisation-time projection** — one function builds the Drive-bound payload, and it omits candidates by construction | **One** place to get right and one place to test. A new caller cannot forget the exclusion, because there is no other way to build a payload. Matches the "single writer" doctrine the rest of the store already uses. | Requires that every existing upload path be routed through it — a small refactor, and the refactor is the risk. |
| **(d)** | **Per-call-site exclusion** — each upload path strips candidates itself | No refactor; each site changes independently. | The exclusion becomes a **convention**, and a convention is exactly what F5 already is. Every future upload path is a new chance to omit the omission. Cannot be asserted once. |

### 3.3 Recommendation: (c)

**(d) reproduces the defect it is meant to fix.** F5 exists *because* the property lived in a comment
rather than in a structure; per-call-site stripping moves it from one comment to several. (c) makes the
exclusion a property of the type that reaches Drive, which is the only form that survives a new caller
being added by someone who never read this brief.

**Note the coupling to increment 5.** The pipeline's increment 5 builds the **F17 fence** — the tests that
prove candidates leave every engine unchanged and appear in no Drive-bound payload. (c) is what makes the
Drive half of that fence assertable in one place. If D-5 resolves to (d), the fence needs N assertions
instead of one and grows every time an upload path is added.

---

## 4. Recommended default, and what each part blocks

**(a) + (c)**, with part 3 already closed as **(e)**.

This matches the default `tasks.md` task 1.2 itself recorded — **(a) + (c) + (e)** — reached here
independently from the evidence rather than adopted from that line.

| Part | Choice | Blocks until answered |
|---|---|---|
| 1 — scheme | **(a)** recommended | `payloadEnvelope.ts` — its content *is* the scheme, so the module cannot be written first. Therefore **all of I0**, and therefore any real-data Drive path. |
| 2 — egress | **(c)** recommended | `candidateExclusion.ts`, the candidate-egress property test, and the Drive half of the pipeline's **F17 fence** (increment 5). |
| 3 — conflict | **(e) CLOSED by D-S(a)** | Nothing further. Recorded so it is not re-opened. **G-10** (readable financial context) stays separate and open. |

### 4.1 Why answering this clears the brief-blocker

The chain, stated end to end so the owner can see what the decision buys:

```
D-5 answered  ->  I0 buildable (payloadEnvelope + candidateExclusion)
              ->  increment 10 (coherence + mirroring) unblocks
              ->  the two-canonical-stores split is closed
              ->  F7 / RG-5 clears
              ->  a figure in the daily brief becomes citeable
```

**F7 is currently release-blocking and non-waivable** — v1.3 FINAL §43 plus AC-48 place it in gate RG-5,
and §54.2 forbids weakening an acceptance criterion to pass. So D-5 is not a tidiness decision. It is the
first link in the only chain that makes the daily Slack brief legitimate.

---

## 5. What this brief does not do

Answers no decision. Grants no Stage-1 or Stage-2 approval. Writes no code and creates no module. Marks no
task complete, including task 1.2. Advances no gate — **G5** (storage consent) and **G8** (backup keypair)
remain owner-only and unmarked, and no key of any kind is generated, named or held. Designs to no
PROPOSED/CONFLICTED source: **O1 §2.2 is not authority here**, and `drive-db.md` as amended holds.
Contains no real amount, balance, account identifier, payee, hostname or Drive identifier.

**Two decisions this brief deliberately leaves alone even though they are adjacent:** **G-10**, the
readable-financial-context expansion, and **D-G**'s disposition in the pipeline plan, which defers to this
D-5 and should be recorded as answered only once D-5 itself is.
