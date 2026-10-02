# Dual-channel memory design

Authority: Contract 14 section 12. Phase 14.2.

## Research and chosen boundary

`singleWindowFlow.ts` is an offline composition; `journalPersistenceAdapter.ts` already owns
local stable-key append/conflict/read-back and accepts sourceRef. `drive_archive.py` already
coordinates injected sanitization/encryption/upload/read-back; it is not a live Drive client.
`knowledgeBoundary.ts` separates profile/privacy retrieval. Do not replace these with another
brain DB, transcript logger, Drive uploader or ungoverned Hermes memory tool.

`channelMemory.ts` is a pure admission/provenance/receipt boundary, not a live bridge.
Adapter provides provider-authenticated metadata and protected enrollment. Boundary validates
all shapes and exact owner/account/conversation matching, then separates reply transport
binding from safe model channel context. Event and session references use SHA-256 over
unambiguous ordered JSON tuples. Hashes remain sensitive metadata; no anonymity claim.
Direction distinguishes inbound owner capture from outbound assistant capture for the same
provider event. Native caller supplies actual outbound event identity on receipt, never an
invented delivery success. Cross-channel continuity stays owner/profile governed.

Existing writer integration uses recordId/sourceRef from the prepared provenance. The content
still must pass native privacy/consent/retention checks. A sourceRef is NOT stored content.
No default transcript policy or real-content write is introduced. Native writer must also
persist structured provenance in its approved schema; this increment does not migrate it.

Receipt assessment is pure: expected identity/version/hash is supplied by the canonical
writer, not recomputed by an LLM. Canonical write and independent read-back must agree and
attest content, not metadata-only. Mirror write/read-back must bind identical remote reference,
destination version and ciphertext hash, as well as source record version/hash, privacy
approval and drive.file encryption. This validates attestations, not cryptographic encryption
or provider authenticity. Real adapter construction remains a live requirement.

## User-visible semantics

Channel: Telegram or Slack. Reply stays in the originating private chat/approved Slack thread.
Memory: not verified / VPS saved. Drive: unavailable / pending / synced by verified receipt.
A failed mirror never erases local evidence. Synchronization retries must not replay canonical
writes or channel sends. No automatic broadcast of a sensitive reply onto the other platform.

## Live prerequisites

Working Slack is owner-confirmed and must stay unchanged. Replacement Telegram credential is
owner-reported created, not installed/validated. Protected credential transfer and owner/chat
enrollment remain human. Reconcile Telegram non-destructive startup and actual pre-plugin auth,
unique consumer, native memory schema/writer/retention, encrypted Drive adapter and scopes.
No native repository changes, remote credential reads or external effects in this increment.
