#!/usr/bin/env python3
# Contract: NIZAM-DAILY-ORCHESTRATION-04 schedule | Phase: R2_SCHEDULER
"""
install_governor_cron.py -- register the four governor slots with the OS scheduler.

Owning contract: NIZAM-DAILY-ORCHESTRATION-04 schedule
Phase: R2_SCHEDULER

WHY OS CRON AND NOT THE AGENT RUNTIME'S OWN SCHEDULER
The agent runtime ships a cron subsystem, but it interprets expressions in UTC
with a null timezone, so every entry would drift by an hour at each Egyptian DST
transition. Its main-profile job is also demonstrably not ticking. OS cron plus a
tested Cairo gate removes the timezone question instead of answering it.

WHY EACH SLOT IS REGISTERED TWICE
This host's cron has no CRON_TZ support, and the live 2026-09-03 preflight
measured the scheduler's own zone as UTC with TZ unset. A single fixed UTC minute
therefore cannot hold a Cairo wall time across DST. Each Cairo target is
registered at BOTH its summer and winter UTC candidate and
`scheduler.cairo_gate` decides which firing is real. A full sweep of every Cairo
day from 2026 to 2030 confirms exactly one firing per Cairo date for all four
production targets.

SAFETY
  * the pre-existing crontab is snapshotted and byte-compared before anything is
    installed, and the installer refuses to run if the snapshot cannot be taken;
  * only lines between the two markers are ever added or removed;
  * every pre-existing line must survive byte-identically, which is asserted
    after installation, not assumed;
  * `--remove` restores exactly the snapshot taken at install time.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import subprocess
import sys

BEGIN = "# ===== NIZAM-GOVERNOR-BLOCK begin (managed by install_governor_cron.py) ====="
END = "# ===== NIZAM-GOVERNOR-BLOCK end ====="

HOME = pathlib.Path(os.path.expanduser("~"))
STATE = HOME / ".nizam-governor"
WRAPPER = (
    HOME / "nizamcore" / "NIZAM__system" / "governor" / "scripts"
    / "nizam-governor.sh"
)
CRON_LOG = STATE / "logs" / "cron.log"

#: (minute, hours, slot). Hours are the EEST and EET UTC candidates.
SLOTS = [
    ("0", "7,8", "refresh_1000"),
    ("40", "8,9", "volatile_1140"),
    ("0", "9,10", "primary_1200"),
    ("0", "10,11", "reconcile_1300"),
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def read_crontab() -> str:
    proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if proc.returncode != 0 and "no crontab" not in (proc.stderr or "").lower():
        raise SystemExit(f"cannot read crontab: {proc.stderr.strip()}")
    return proc.stdout


def write_crontab(text: str) -> None:
    proc = subprocess.run(["crontab", "-"], input=text, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"cannot install crontab: {proc.stderr.strip()}")


def build_block() -> str:
    lines = [
        BEGIN,
        "#   Owning contract: NIZAM-DAILY-ORCHESTRATION-04 schedule",
        "#   Cron here has no CRON_TZ support and this host's scheduler runs in UTC",
        "#   (measured by the 2026-09-03 Contract 04 preflight), so every",
        "#   Africa/Cairo target below is registered at BOTH its EEST (+3) and EET",
        "#   (+2) UTC candidate. scheduler.cairo_gate decides which firing is the",
        "#   real one and a run-once guard keyed on the CAIRO date refuses the",
        "#   second. Exactly one firing per Cairo day passes, in either regime.",
        "#   A slot that stands down exits 0 on purpose: it is not a failure.",
    ]
    for minute, hours, slot in SLOTS:
        lines.append(
            f"{minute} {hours} * * * {WRAPPER} {slot} >> {CRON_LOG} 2>&1"
        )
    lines.append(END)
    return "\n".join(lines) + "\n"


def strip_block(text: str) -> str:
    if BEGIN not in text:
        return text
    head, rest = text.split(BEGIN, 1)
    if END not in rest:
        raise SystemExit("found a begin marker with no end marker; refusing to guess")
    _block, tail = rest.split(END, 1)
    return head + tail.lstrip("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--remove", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if sum(bool(x) for x in (args.install, args.remove, args.dry_run)) != 1:
        parser.error("choose exactly one of --install, --remove, --dry-run")

    STATE.mkdir(parents=True, exist_ok=True)
    CRON_LOG.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path = STATE / "crontab.before-governor"

    current = read_crontab()
    print(f"current crontab: {len(current.encode())} bytes, "
          f"{len([l for l in current.splitlines() if l.strip()])} non-blank lines")
    print(f"sha256         : {sha(current)}")
    print(f"block present  : {BEGIN in current}")

    if not WRAPPER.exists():
        print(f"\nABORT: wrapper not found at {WRAPPER}")
        print("Deploy nizam-governor.sh before registering it with cron.")
        return 2
    if not os.access(WRAPPER, os.X_OK):
        print(f"\nABORT: wrapper is not executable: {WRAPPER}")
        return 2

    block = build_block()

    if args.dry_run:
        print("\n--- block that WOULD be installed ---")
        print(block, end="")
        print("--- end block ---")
        print("\nnothing was written")
        return 0

    if args.remove:
        if BEGIN not in current:
            print("\nnothing to remove: no governor block present")
            return 0
        if not snapshot_path.exists():
            print(f"\nABORT: no snapshot at {snapshot_path.name}; refusing to guess "
                  "what the crontab looked like before")
            return 2
        expected = snapshot_path.read_text(encoding="utf-8")
        stripped = strip_block(current)
        if sha(stripped) != sha(expected):
            print("\nABORT: removing the block does not reproduce the snapshot.")
            print(f"  stripped sha256: {sha(stripped)}")
            print(f"  snapshot sha256: {sha(expected)}")
            print("Something else changed the crontab; a human should look.")
            return 1
        write_crontab(expected)
        after = read_crontab()
        ok = sha(after) == sha(expected)
        print(f"\nremoved. restored byte-identically: {ok}")
        return 0 if ok else 1

    # --install
    base = strip_block(current) if BEGIN in current else current
    if BEGIN in current:
        print("\nan existing governor block was found; it will be replaced")
    if not snapshot_path.exists():
        snapshot_path.write_text(base, encoding="utf-8")
        print(f"snapshot taken : {snapshot_path.name} ({len(base.encode())} bytes)")
    else:
        recorded = snapshot_path.read_text(encoding="utf-8")
        if sha(recorded) != sha(base):
            print(f"\nABORT: {snapshot_path.name} does not match the current crontab "
                  "with the block removed. The crontab changed outside this tool; a "
                  "human should reconcile before reinstalling.")
            return 1
        print(f"snapshot matches: {snapshot_path.name}")

    proposed = base
    if proposed and not proposed.endswith("\n"):
        proposed += "\n"
    proposed += block
    write_crontab(proposed)

    after = read_crontab()
    print(f"\ninstalled. crontab now {len(after.encode())} bytes")
    print(f"sha256         : {sha(after)}")

    # Every pre-existing line must have survived, verbatim.
    survived = all(
        line in after for line in base.splitlines() if line.strip()
    )
    block_present = BEGIN in after and END in after
    slot_lines = [
        line for line in after.splitlines()
        if str(WRAPPER) in line and not line.startswith("#")
    ]
    checks = {
        "block installed": block_present,
        "every pre-existing line survived": survived,
        "exactly four slot lines": len(slot_lines) == 4,
        "stripping the block reproduces the snapshot":
            sha(strip_block(after)) == sha(base),
    }
    print("\npost-conditions:")
    for name, ok in checks.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    for line in slot_lines:
        print("  slot: " + line.replace(str(HOME), "$HOME"))
    if not all(checks.values()):
        print("\nRESULT: FAILED. Run with --remove to restore the snapshot.")
        return 1
    print("\nRESULT: four governor slots registered with OS cron")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
