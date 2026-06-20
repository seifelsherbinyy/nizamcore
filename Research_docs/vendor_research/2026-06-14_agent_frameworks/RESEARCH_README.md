# NIZAM Vendor Research Sandbox

Read-only reference area for external agent-framework repositories.

## Rules

1. Cloned repos live under `repos/` for inspection only — **not** production dependencies.
2. Default clone: `git clone --depth 1 <url> repos/<slug>`
3. **Never** copy third-party code into `NIZAM__system/` without license review, dependency audit, and explicit operator approval.
4. **Never** run untrusted `install.sh`, `postinstall`, or Docker files until reviewed.
5. **Never** expose strict-local paths (journals, ledgers, `.env`, OAuth tokens) to cloned repos or external tools.
6. Findings must be summarized as NIZAM-native pattern cards under `patterns/`, not pasted code.

## Outputs

| File | Purpose |
|------|---------|
| `vendor_repo_inventory.json` | Scored repo metadata |
| `assessments/*.md` | One-page per repo |
| `patterns/*.md` | Adaptation cards |
| `top_20_capability_patterns.md` | Ranked NIZAM mappings |
| `rejected_patterns.md` | Explicit rejections |

## Privacy

This folder is `private_github` / architecture-only. Do not store operator journals or ledger exports here.
