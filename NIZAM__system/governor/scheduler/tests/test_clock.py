# Contract: NIZAM-DAILY-ORCHESTRATION-04 schedule | Phase: R2_SCHEDULER
"""Acceptance tests for the single clock read.

Owning contract: NIZAM Contract 04 `schedule`
                 NIZAM-CONTRACT-05 regression_protection
Phase:           R2_SCHEDULER

The module is four lines of code, but those four lines are the entire impure
surface of the scheduler, so the properties that make the rest of the package
testable are pinned here.
"""
import datetime as dt
import inspect
import pathlib

from scheduler import clock
from scheduler.cairo_gate import UTC, decide


def test_R2_K01_the_reader_returns_an_aware_utc_instant():
    """A naive instant would be silently reinterpreted by the Cairo conversion."""
    now = clock.read_utc_now()
    assert now.tzinfo is not None
    assert now.utcoffset() == dt.timedelta(0)


def test_R2_K02_the_returned_instant_is_accepted_by_the_gate():
    """The boundary must hand the gate something the gate will not refuse."""
    now = clock.read_utc_now()
    decision = decide(now, now.astimezone(UTC).hour, now.astimezone(UTC).minute)
    assert decision.verdict is not None


def test_R2_K03_the_instant_advances():
    first = clock.read_utc_now()
    second = clock.read_utc_now()
    assert second >= first


def test_R2_K04_the_module_exports_only_the_reader():
    """A module whose whole purpose is one function must not grow a second."""
    assert clock.__all__ == ["read_utc_now"]
    public = [
        name for name in vars(clock)
        if not name.startswith("_") and callable(getattr(clock, name))
    ]
    assert public == ["read_utc_now"], public


def test_R2_K05_the_module_states_why_it_exists_at_all():
    """Deleting this rationale is how the second reader comes back."""
    source = inspect.getsource(clock)
    assert "ONLY CLOCK READ" in source.upper()
    assert "second reader" in source or "second clock read" in source


def test_R2_K06_the_module_declares_its_contract_in_the_first_20_lines():
    head = "\n".join(inspect.getsource(clock).splitlines()[:20])
    assert "NIZAM-DAILY-ORCHESTRATION-04" in head
    assert "R2_SCHEDULER" in head


def test_R2_K07_the_reader_touches_no_storage_and_no_network():
    """The impure line reads the clock; it must not acquire other impurities."""
    source = inspect.getsource(clock)
    for forbidden in ("open(", "socket", "requests", "subprocess", "Path("):
        assert forbidden not in source, forbidden


def test_R2_K08_only_this_file_holds_the_reads_in_the_package():
    package = pathlib.Path(inspect.getsourcefile(clock)).parent
    holders = set()
    for path in sorted(package.glob("*.py")):
        code = [
            line for line in path.read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        ]
        if any("datetime.now(" in line or "utcnow(" in line for line in code):
            holders.add(path.name)
    assert holders == {"clock.py"}, holders
