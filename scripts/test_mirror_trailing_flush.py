#!/usr/bin/env python3
"""Simulate MIRROR-1: last _capture then silence still triggers trailing flush."""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "NIZAM__system/hermes-plugins/nizam-governor/__init__.py"


def _load_gov(tmp: str):
    os.environ["HOME"] = tmp
    nc = Path(tmp) / "nizamcore"
    nc.mkdir(parents=True, exist_ok=True)
    (nc / "NIZAM__system/ledgers").mkdir(parents=True, exist_ok=True)
    (nc / "NIZAM__system/config").mkdir(parents=True, exist_ok=True)
    for name in ("router.config.yaml", "intent_exemplars.yaml"):
        src = REPO / "NIZAM__system/config" / name
        if src.exists():
            (nc / "NIZAM__system/config" / name).write_text(
                src.read_text(encoding="utf-8"), encoding="utf-8",
            )
    spec = importlib.util.spec_from_file_location("nizam_governor_test", PLUGIN)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["nizam_governor_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    throttle = 2.0
    with tempfile.TemporaryDirectory() as tmp:
        gov = _load_gov(tmp)
        gov.MIRROR_THROTTLE_SEC = throttle
        gov.RCLONE = str(Path(tmp) / "fake-rclone")
        Path(gov.RCLONE).write_text("", encoding="utf-8")
        flushes: list[str] = []

        def fake_execute():
            flushes.append(time.time())

        gov._mirror_execute = fake_execute  # type: ignore[method-assign]

        # Burst inside window: only trailing should flush (no immediate if last was recent)
        gov._ensure(gov.STATE_DIR)
        with open(gov.MIRROR_STATE, "w") as f:
            f.write(str(time.time()))  # last mirror "just now"
        gov._mirror_ledgers_async()
        time.sleep(throttle + 0.6)
        trailing_only = len(flushes)

        # Last message then silence
        flushes.clear()
        gov._ensure(gov.STATE_DIR)
        with open(gov.MIRROR_STATE, "w") as f:
            f.write(str(time.time()))  # block immediate
        gov._mirror_ledgers_async()
        assert len(flushes) == 0, "immediate must not fire inside throttle window"
        time.sleep(throttle + 0.6)
        after_silence = len(flushes)

    ok = after_silence >= 1
    print("MIRROR-1 trailing flush simulation")
    print(f"  throttle_sec={throttle}")
    print(f"  after_quiet_period_flushes={after_silence} (need >= 1)")
    print(f"  result={'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
