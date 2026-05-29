"""NIZAM__system.relay — Telegram gateway + Coordinator scaffold.

Phase-1 boot loop (B4.1–B4.10):

    Telegram POST
      └── webhook.handle_update()           [auth + dedup]
            └── coordinator.process()        [SUKOON pre-gate + router]
                  └── agents.shura.respond() [Salman synthesis]
                        └── egress.check()   [HIMAYAH classification]
                              └── ledger.append() [Ammar / THABAT]
                                    └── reply()  [send back to Telegram]

This package is stdlib-only and runnable locally (no pip deps). For VPS
deployment, swap the stdlib `http.server` for FastAPI + uvicorn (I7) and
keep all other modules unchanged.
"""

__version__ = "0.1.0"
