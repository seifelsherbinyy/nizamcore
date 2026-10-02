# Dual-channel memory requirements

Authority: PFOS Contract 14 section 12; Contracts 06/12, money/Drive/server steering.
Phase 14.2: offline preparation, not native deployment.

- CM01: Explicit dual-channel version, separate owner/account/conversation enrollment,
  supported platform/profile, bot rejection, Telegram-private restriction. Unknown rejects.
- CM02: Reply route uses admitted metadata only; preserve Slack thread/Telegram private
  destination. Model context contains platform and pseudonymous conversation only, no raw IDs.
- CM03: Stable provenance/replay identity includes owner, profile, platform, ingress account,
  conversation/thread, provider event, direction. Cross-platform/account/profile keys differ.
  Use existing canonical writer's conflict refusal and independent read-back, no second writer.
- CM04: Separate VPS and Drive evidence. Require matching record/version/hash on canonical
  write and read-back; Drive additionally privacy approval, drive.file, encryption and matching
  source/ciphertext/version/remote-reference receipts. Malformed or mismatched evidence fails closed.
- CM05: Keep VPS saved if Drive fails, with pending/unavailable status. No fabricated saved/synced
  acknowledgement. Receipt provenance is a trusted injected native-port prerequisite.
- CM06: No new live transport, credentials, money, DB schema, uploads or native modifications.
  Synthetic tests, numeric phase headers, existing focused and full acceptance checks retained.
