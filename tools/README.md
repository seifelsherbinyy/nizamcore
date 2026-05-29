# tools/

Single-purpose, stdlib-only operational scripts that any fresh sandbox session
can run without installing dependencies.

| Script | Purpose | Contract reference |
|--------|---------|---------------------|
| [`nizam_startup.py`](nizam_startup.py) | §2 startup verifier; emits §7 STARTUP RECEIPT. | [`../NIZAM__system/docs/NIZAM_ORCHESTRATION_LAYER.md`](../NIZAM__system/docs/NIZAM_ORCHESTRATION_LAYER.md) §2 + §7 |

## Why a separate folder

`HIFZ__github_version_control/scripts/` holds the **runtime** governor scripts
(Drive mirror, dual-write, Notion preflight) — they have external deps
(`google-api-python-client`, `python-docx`, `requests`).

`tools/` is for scripts that must work **before** any deps are installed — the
"verify this sandbox can even run NIZAM" layer. Keep them stdlib-only.

## Conventions

- Stdlib only. No `pip install` requirements.
- Exit 0 on success, exit 2 on a §2 HALT condition (missing gate, unreadable
  `NIZAM_TEMPLE.json`, etc.). Per §1.1 / §9, we fail loud, not silent.
- Output goes to **stdout** as a fenced JSON block matching §7. Pipe-friendly.
- Never write to disk. The sandbox is COMPUTE, not storage.
