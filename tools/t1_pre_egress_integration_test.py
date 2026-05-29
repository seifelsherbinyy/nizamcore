"""T1 — Pre-egress local integration test (Plan v2 §T1).

Runs every locally-runnable verification end-to-end. This is the gate
that must pass BEFORE any first egress (G3). It exercises:

  GAP layer:
    * nizam_startup receipt
    * persona validator (B2.9)
    * ledger chain integrity (G13.x)

  BUILD layer:
    * classifier + sync_arbiter fixtures (B1.2)
    * pre-commit hook logic (B1.8)
    * router dry-run on 10-input fixture (B3.1)
    * extraction dry-run on 10-extraction fixture (B3.2)
    * intent priority cascade (B3.3)
    * Phase-1 boot loop, 22 tests (B4.1–B4.10)
    * agent_message schema + trace.py (E1.1, E1.5)
    * MARSAD generic intel base (E4.2)
    * STRATEGY_LEDGER STH publish/verify + tamper (E4.3)

Exit code is 0 only when every check is GREEN.

Usage (from D:\\NIZAM\\nizamcore):

    .venv\\Scripts\\python.exe tools\\t1_pre_egress_integration_test.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

PYTHON = sys.executable
RESULTS: list[dict] = []
START = time.time()

GREEN = "[OK]"
RED = "[FAIL]"


def _print(*args) -> None:
    print(*args, flush=True)


def _record(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append({"name": name, "ok": ok, "detail": detail})
    tag = GREEN if ok else RED
    _print(f"{tag}  {name}  {detail}".rstrip())


def _run_unittest(module: str) -> tuple[bool, str]:
    proc = subprocess.run(
        [PYTHON, "-m", "unittest", module],
        capture_output=True, text=True, cwd=REPO,
    )
    last = (proc.stderr or proc.stdout).strip().splitlines()[-3:]
    summary = " | ".join(last)
    ok = proc.returncode == 0
    return ok, summary


def _run_script(args: list[str], *, cwd: Path | None = None) -> tuple[bool, str]:
    proc = subprocess.run(
        [PYTHON, *args],
        capture_output=True, text=True, cwd=cwd or REPO,
    )
    out = (proc.stdout + proc.stderr).strip().splitlines()
    tail = " | ".join(out[-2:]) if out else ""
    return proc.returncode == 0, tail


def check_nizam_startup() -> None:
    ok, detail = _run_script(["tools/nizam_startup.py"])
    _record("GAP nizam_startup receipt", ok, detail)


def check_persona_validator() -> None:
    script = REPO.parent / "scripts" / "validate_personas.py"
    if not script.exists():
        _record("B2.9 persona validator", False, "script missing")
        return
    ok, detail = _run_script([str(script)])
    _record("B2.9 persona validator", ok, detail)


def check_router_dry_run() -> None:
    ok, detail = _run_script([
        "NIZAM__system/config/fixtures/router_dry_run.py"
    ])
    _record("B3.1 router dry-run (10 inputs)", ok, detail)


def check_extraction_dry_run() -> None:
    ok, detail = _run_script([
        "NIZAM__system/config/fixtures/extraction_dry_run.py"
    ])
    _record("B3.2 extraction dry-run (10 extractions)", ok, detail)


def check_intent_priority() -> None:
    ok, detail = _run_script([
        "NIZAM__system/config/fixtures/intent_priority_test.py"
    ])
    _record("B3.3 intent priority cascade", ok, detail)


def check_classifier_fixtures() -> None:
    ok, detail = _run_unittest(
        "NIZAM__system.governor.tests.test_classifier_fixture"
    )
    _record("B1.2 classifier+sync_arbiter fixtures", ok, detail)


def check_pre_commit_hook() -> None:
    ok, detail = _run_unittest(
        "NIZAM__system.governor.tests.test_pre_commit_hook"
    )
    _record("B1.8 pre-commit hook block", ok, detail)


def check_phase1_boot_loop() -> None:
    env = dict(os.environ)
    env.setdefault("TELEGRAM_WEBHOOK_SECRET", "test-secret-XYZ")
    env.setdefault("NIZAM_TELEGRAM_ALLOWED_IDS", "111222333")
    proc = subprocess.run(
        [PYTHON, "-m", "unittest",
         "NIZAM__system.relay.tests.test_phase1_boot_loop"],
        capture_output=True, text=True, cwd=REPO, env=env,
    )
    last = (proc.stderr or proc.stdout).strip().splitlines()[-3:]
    _record("B4.1-B4.10 Phase-1 boot loop (22 tests)",
            proc.returncode == 0, " | ".join(last))


def check_agent_message_schema() -> None:
    ok, detail = _run_unittest(
        "NIZAM__system.governor.tests.test_agent_message_schema"
    )
    _record("E1.1+E1.5 agent_message + trace", ok, detail)


def check_strategy_sth() -> None:
    ok, detail = _run_unittest(
        "NIZAM__system.governor.tests.test_strategy_sth"
    )
    _record("E4.3 STRATEGY_LEDGER RFC 6962 + STH", ok, detail)


def check_marsad_generic_intel() -> None:
    proc = subprocess.run(
        [PYTHON, "-m", "unittest", "tests.test_generic_base"],
        capture_output=True, text=True,
        cwd=REPO / "MARSAD__flight_radar",
    )
    last = (proc.stderr or proc.stdout).strip().splitlines()[-3:]
    _record("E4.2 MARSAD generic intel base",
            proc.returncode == 0, " | ".join(last))


def check_ledger_chains() -> None:
    from NIZAM__system.governor import ledger_writer
    all_ok = True
    detail_parts: list[str] = []
    for ledger in [
        "EVENT_LEDGER", "LEARNING_LEDGER",
        "STRATEGY_LEDGER", "DEAD_LETTER",
    ]:
        ok, n, broken = ledger_writer.verify_chain(ledger)
        detail_parts.append(f"{ledger}={n}")
        if not ok:
            all_ok = False
            detail_parts.append(f"BROKEN@{broken}")
    _record("G13.x ledger hash-chain integrity",
            all_ok, " ".join(detail_parts))


def check_kill_switch_assertion() -> None:
    """Smoke test: temporarily arm the kill switch and ensure writers refuse."""
    from NIZAM__system.governor import ledger_writer
    os.environ["NIZAM_KILL_ALL"] = "1"
    try:
        try:
            ledger_writer.append(
                "EVENT_LEDGER",
                payload={"t1": "kill_switch_drill"},
                actor="Ammar", action="kill_switch_drill",
                module="tools.t1",
            )
            _record("B1.5 NIZAM_KILL_ALL halts writers", False,
                    "append did NOT raise")
            return
        except RuntimeError as exc:
            _record("B1.5 NIZAM_KILL_ALL halts writers", True, str(exc))
    finally:
        del os.environ["NIZAM_KILL_ALL"]


def main() -> int:
    _print(f"T1 — Pre-egress local integration test  ·  repo={REPO}")
    _print("-" * 64)

    check_nizam_startup()
    check_persona_validator()
    check_classifier_fixtures()
    check_pre_commit_hook()
    check_router_dry_run()
    check_extraction_dry_run()
    check_intent_priority()
    check_phase1_boot_loop()
    check_agent_message_schema()
    check_marsad_generic_intel()
    check_strategy_sth()
    check_kill_switch_assertion()
    check_ledger_chains()

    elapsed = time.time() - START
    failed = [r for r in RESULTS if not r["ok"]]
    _print("-" * 64)
    _print(
        f"checks: {len(RESULTS)}  ·  passed: {len(RESULTS) - len(failed)}"
        f"  ·  failed: {len(failed)}  ·  elapsed: {elapsed:.2f}s"
    )

    receipt_path = REPO / "NIZAM__system" / "ledgers" / "T1_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "checks": RESULTS,
            "elapsed_sec": elapsed,
            "ok": not failed,
        }, indent=2),
        encoding="utf-8",
    )

    if failed:
        _print(RED, "T1 NOT READY for first egress (G3).")
        return 1
    _print(GREEN, "T1 READY. All locally-verifiable gates GREEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
