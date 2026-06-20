#!/usr/bin/env python3
"""Run NIZAM pulsation Loops A/B with context refresh."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from NIZAM__system.companion import scheduler  # noqa: E402
from NIZAM__system.companion.pulsation.loops import evaluate_loops  # noqa: E402
from NIZAM__system.relay import env_loader  # noqa: E402


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run NIZAM pulsation loops")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate and build messages without sending or persisting loop state",
    )
    parser.add_argument(
        "--at",
        help="Evaluate at this ISO timestamp (UTC or offset)",
    )
    parser.add_argument(
        "--loop",
        choices=("a", "b", "all"),
        default="all",
        help="Force evaluation of Loop A, Loop B, or both",
    )
    args = parser.parse_args()

    env_loader.load_all(activate=True)
    now = datetime.now(timezone.utc)
    if args.at:
        now = datetime.fromisoformat(args.at.replace("Z", "+00:00"))

    loop_arg = None if args.loop == "all" else args.loop
    evaluation = evaluate_loops(now=now, loop=loop_arg, dry_run=args.dry_run)

    receipt: dict[str, object] = {
        "run_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dry_run": args.dry_run,
        "loop_evaluated": args.loop,
        "evaluation": {
            k: v
            for k, v in evaluation.items()
            if k != "message"
        },
    }

    message = evaluation.get("message")
    if message is not None and hasattr(message, "to_dict"):
        receipt["message"] = message.to_dict()
        from NIZAM__system.companion.council.triggers import (  # noqa: E402
            minimal_pulse_note,
            should_convene_council,
        )

        refresh = message.context_refresh
        receipt["council"] = {
            **minimal_pulse_note(refresh, message=message),
            "full_deliberation": should_convene_council(
                refresh, pulse_kind=message.message_type, message=message
            ),
        }
        if not evaluation.get("skipped"):
            send_result = scheduler.send_pulsation(
                message,
                loop=str(evaluation.get("loop_sent") or "a"),
                dry_run=args.dry_run,
            )
            receipt["send"] = send_result
    else:
        receipt["send_status"] = "skipped"
        receipt["skipped_reason"] = evaluation.get("reason")

    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
