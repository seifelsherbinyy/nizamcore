# Pulsation + Council test matrix

| Layer | Primary tests |
|-------|---------------|
| L1 | `test_pulsation_contracts` |
| L2 | `test_context_refresh_*` |
| L3 | `test_routing_*`, message builder |
| L4 | `test_himayah_*` |
| L5 | `test_collision_*`, waking hours, islamic disabled |
| L6 | `test_ledger_append` |
| L7 | `test_sukoon_tiny_mode`, candidate mapping |
| L8 | CLI dry-run via `run_pulsation_loops.py --dry-run` |
| K1–K7 | `test_council.py` |
| 4.x | `test_skills_registry.py` |
| Regression | `test_companion.py`, `test_production_modules.py` |

## Run command

```powershell
cd D:\NIZAM
D:\NIZAM\.venv\Scripts\python.exe -m unittest `
  NIZAM__system.companion.tests.test_pulsation `
  NIZAM__system.companion.tests.test_companion `
  NIZAM__system.companion.tests.test_production_modules `
  NIZAM__system.companion.council.tests.test_council `
  NIZAM__system.companion.tests.test_skills_registry -v
```
