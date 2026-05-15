# GITHUB_PRIVACY

## Visibility
**PRIVATE ONLY.** Never public. Verified before every push via `gh repo view --json visibility`.

## Repo
- Name: `pop-private` (default; user may override).
- Remote: SSH preferred (`git@github.com:<user>/pop-private.git`); HTTPS+PAT acceptable fallback.
- Branch: `main` only initially.

## .gitignore
See `C:\Users\selsherb\POP\.gitignore`. Excludes all strict-local paths by default.

## Pre-commit checklist (HIMAYAH gate)
1. `git status` — surface every staged file.
2. For each, look up `NIZAM__system/policies/PRIVACY_CLASSIFICATION.json`.
3. If any path is `strict_local` → ABORT. Surface offending file. Do not commit.
4. Verify `gh repo view --json visibility` returns `"PRIVATE"`.
5. Commit with message format: `YYYY-MM-DD | module | short summary`.

## What CAN be committed
- README.md, POP_TEMPLE.json, POP_MASTER_REGISTER.json, index.md, CRITICAL_FACTS.md, CHANGELOG.md, .gitignore.
- NIZAM__system/schemas/**, templates/**, skills/**, policies/**, docs/**, personas/**.
- Each folder's _index.json and README.md.

## What's NEVER committed
- raw/, triaged/, sessions/, signals/, overload_flags.jsonl, HAJR/, SOUL.md, log.md (after first init), MAL/**, BADAN/**, AHEL/**, KABIR_SHERBO/{10,15,20}_year/, MUNAWARA raw battle logs.
- All `*_LEDGER.jsonl` files (review-before-commit for Phase 1 ledgers; strict-local for Phase 2/3).
- Secrets: `.env`, `*token*`, `*secret*`, `*credentials*`, `*.pem`, `*.key`.

## SSH key setup (one-time)
1. `ssh-keygen -t ed25519 -C "seif.elsherbiny13@gmail.com"` — keys in `~\.ssh\`.
2. Add public key to GitHub: `Settings → SSH and GPG keys`.
3. Test: `ssh -T git@github.com` → should return "Hi <username>!".

## Force-push policy
Never force-push to `main`. If history rewrite needed, create new branch and PR.
