# Agent Notes for D:\NIZAM

## Canonical Paths

- Workspace root: `D:\NIZAM`
- NIZAM Core repo: `D:\NIZAM`
- Repo pointer: `D:\NIZAM\NIZAMCORE_PATH.txt`
- Architecture docs: `D:\NIZAM\docs\architecture`
- Local scripts: `D:\NIZAM\scripts`

## Verification

Use the non-destructive verification script:

```powershell
D:\NIZAM\scripts\verify-nizamcore.ps1
```

For the canonical startup receipt:

```powershell
D:\NIZAM\.venv\Scripts\python.exe D:\NIZAM\tools\nizam_startup.py
```

## NIZAM Version Rule

Do not use `import nizam`; this repo is not a pip package named `nizam`.

Use:

- `D:\NIZAM\NIZAM_TEMPLE.json` → `platform_version`
- `D:\NIZAM\tools\nizam_startup.py`

## Boundaries

- `D:\NIZAM` is the GitHub mirror and NIZAM system source.
- `D:\NIZAM\docs\architecture` holds supporting analysis and reports.
- `C:\doctorhealth` is a separate project and must not be used for NIZAM Core.
- Do not commit local `.env`, `.venv`, `install-audit`, caches, or personal data.
