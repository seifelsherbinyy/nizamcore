# Contract: NIZAM-DAILY-ORCHESTRATION-04 schedule | Phase: R2_SCHEDULER
"""The single clock read in the scheduler package.

Owning contract: NIZAM Contract 04, `schedule`
Phase:           R2_SCHEDULER

WHY A WHOLE MODULE FOR ONE LINE
Every decision this package makes is a pure function of an instant, which is
what lets the DST hazards be swept offline and the Cairo gate be tested at the
exact minutes that matter. That property survives only while there is ONE place
where the real instant enters the system.

R2 originally kept that line inside `preflight_cli.main()`. Adding the governor
entrypoint immediately produced a second reader, and the invariant test caught
it. Two readers is not twice as bad as one, it is categorically different: with
one reader the impure boundary is a line, with two it is a policy that every
future entrypoint has to remember. So the line moved here, where it is the only
thing the module does, and every entrypoint now calls it instead of repeating
it. A third entrypoint cannot reintroduce the problem without deleting this
module's reason to exist.

The tests assert this rather than trusting the paragraph: the package may
contain exactly one clock read and it must be in this file. Note that the check
is a deliberately dumb textual scan, so it cannot be fooled by an indirect
call -- which also means this docstring must not spell the scanned token out.
"""
from __future__ import annotations

import datetime as _dt

from .cairo_gate import UTC

__all__ = ["read_utc_now"]


def read_utc_now() -> _dt.datetime:
    """Return the current instant as a timezone-aware UTC datetime.

    Timezone-aware on purpose. A naive datetime would be silently reinterpreted
    by the Cairo conversion, and `cairo_gate.decide` refuses naive input for
    exactly that reason, so the boundary hands it an unambiguous instant.
    """
    # THE ONLY CLOCK READ IN THE PACKAGE.
    return _dt.datetime.now(UTC)
