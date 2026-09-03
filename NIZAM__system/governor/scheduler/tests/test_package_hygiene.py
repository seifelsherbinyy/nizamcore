# Contract: NIZAM-CONTRACT-05 regression_protection | Phase: R2_SCHEDULER
"""Package-wide hygiene invariants for the scheduler.

Owning contract: NIZAM-CONTRACT-05 regression_protection
                 NIZAM repository rule: owning contract and phase in every file
Phase:           R2_SCHEDULER

WHY THIS FILE EXISTS
2026-09-03: five files in this package were silently rewritten with CRLF line
endings by a patch script running on Windows, because `pathlib.write_text`
translates newlines by default. Nothing failed. The suite still passed, the
modules still imported, and the defect only surfaced because a tamper harness
could no longer find its multi-line anchors -- ten adversarial cases came back
INCONCLUSIVE, which proves nothing at all.

The deployer refuses CRLF, so those files were undeployable while looking
perfectly healthy locally. A property that the toolchain enforces at the last
possible moment is a property the suite should enforce at the first, so it is
asserted here for every file at once rather than remembered per edit.
"""
import pathlib

import pytest

PACKAGE = pathlib.Path(__file__).resolve().parents[1]
PY_FILES = sorted(PACKAGE.rglob("*.py"))
SOURCE_FILES = [p for p in PY_FILES if "__pycache__" not in p.parts]


def _rel(path: pathlib.Path) -> str:
    return str(path.relative_to(PACKAGE))


def test_R2_H01_the_package_has_files_to_check():
    """A glob that silently matches nothing would make every test below vacuous."""
    assert len(SOURCE_FILES) >= 8, [_rel(p) for p in SOURCE_FILES]


@pytest.mark.parametrize("path", SOURCE_FILES, ids=_rel)
def test_R2_H02_every_file_uses_unix_line_endings(path):
    """The deployer refuses CRLF; a CRLF file is undeployable but looks fine."""
    body = path.read_bytes()
    assert b"\r\n" not in body, f"{_rel(path)} contains CRLF"
    assert b"\r" not in body, f"{_rel(path)} contains a bare CR"


#: The exact marker the deploy tool greps for, transcribed. Two files declared
#: their contract only in prose ("Owning contract: ...") and the deployer's
#: case-sensitive `grep -c "Contract:"` scored them 0 while a looser version of
#: this test scored them PASS. One rule enforced two different ways is one rule
#: that will drift, so this test now checks the same literal the tool does.
CONTRACT_MARKER = "# Contract:"
PHASE_MARKER = "| Phase:"


@pytest.mark.parametrize("path", SOURCE_FILES, ids=_rel)
def test_R2_H03_every_file_declares_its_contract_and_phase(path):
    """NIZAM rule: provenance in the first 20 lines of every file under src/tests."""
    head = path.read_text(encoding="utf-8").splitlines()[:20]
    joined = "\n".join(head)
    assert CONTRACT_MARKER in joined, (
        f"{_rel(path)} has no '{CONTRACT_MARKER}' line in its first 20; the "
        "deploy tool greps for this literal and will score the file 0"
    )
    assert PHASE_MARKER in joined, f"{_rel(path)} names no phase on that line"
    assert "NIZAM" in joined, f"{_rel(path)} names no NIZAM contract"


@pytest.mark.parametrize("path", SOURCE_FILES, ids=_rel)
def test_R2_H04_no_file_indents_with_tabs(path):
    """Mixed indentation is how a guard clause quietly changes scope."""
    for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = line.lstrip(" ")
        assert not stripped.startswith("\t"), f"{_rel(path)}:{number} indents with a tab"


@pytest.mark.parametrize("path", SOURCE_FILES, ids=_rel)
def test_R2_H05_every_file_ends_with_exactly_one_newline(path):
    """A missing final newline makes every future diff of the last line noisy."""
    body = path.read_bytes()
    assert body.endswith(b"\n"), f"{_rel(path)} has no final newline"
    assert not body.endswith(b"\n\n"), f"{_rel(path)} ends with a blank line"


def test_R2_H06_no_source_file_carries_a_deployment_particular():
    """Both NIZAM repositories are public: no host, path or identifier may land.

    The tokens are assembled from fragments rather than written out, because the
    first version of this test failed on its OWN source file: a scanner that
    spells its needles literally becomes the thing it is scanning for. Keeping
    the fragments split means the check tests real tokens while this file stays
    clean enough to be committed to a public repository.
    """
    forbidden = tuple(
        left + right
        for left, right in (
            ("ovh", ".net"),
            ("vps", "-"),
            ("/ho", "me/"),
            ("/o", "pt/personal-health"),
            ("ssh", "-rsa"),
            ("BEGIN OPENSSH PRIVATE", " KEY"),
        )
    )
    offenders = []
    for path in SOURCE_FILES:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{_rel(path)}: {token}")
    assert not offenders, offenders
