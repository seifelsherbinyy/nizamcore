# NIZAMCORE_INTEGRATION

> **Status**: DEFERRED — pending Phase 1.5 (requires `gh auth login`).

## What this is

`nizamcore` is Seif's private GitHub repo at `https://github.com/seifelsherbinyy/nizamcore`. It is expected to contain prior foundational work that may strengthen POP's NIZAM__system module.

## Why integration is deferred

The repo returned **HTTP 404 on anonymous fetch** (confirmed 2026-05-15). This is expected for private repos. Access requires `gh` CLI authentication.

## Phase 1.5 plan

1. User runs `gh auth login` (interactive, browser or device flow).
2. POP Claude session resumes and runs:
   ```
   gh repo view seifelsherbinyy/nizamcore
   ```
   to confirm the slug is correct. If 404 persists, list the user's repos via `gh repo list` to find the correct name.
3. Clone read-only to `C:\Users\selsherb\POP\NIZAM__system\_imported\nizamcore\`:
   ```
   gh repo clone seifelsherbinyy/nizamcore C:\Users\selsherb\POP\NIZAM__system\_imported\nizamcore
   ```
4. Inspect structure. Identify patterns, schemas, or skill files that strengthen NIZAM.
5. Populate the **Findings** section below with what was discovered and what (if anything) was cherry-picked.
6. Cherry-pick compatible elements into `NIZAM__system/` with file-level attribution comments. NEVER write back to the `_imported/` mirror.
7. Commit with message: `2026-MM-DD | NIZAM | integrate compatible patterns from nizamcore`.

## Privacy note

The `_imported/` folder is `.gitignored`. We do not push nizamcore's content back through POP's repo. Cherry-picked elements are re-authored, not pasted, into NIZAM's canonical paths.

---

## Findings (populated in Phase 1.5)

_(empty — to be filled after clone)_

## Cherry-picked elements (populated in Phase 1.5)

_(empty — to be filled after integration)_
