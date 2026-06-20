#!/usr/bin/env python3

"""Thin wrapper — delegates to pulsation loop runner."""

from __future__ import annotations



import sys

from pathlib import Path



REPO = Path(__file__).resolve().parents[1]

if str(REPO) not in sys.path:

    sys.path.insert(0, str(REPO))



from tools.run_pulsation_loops import main  # noqa: E402





if __name__ == "__main__":

    raise SystemExit(main())

