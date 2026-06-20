"""sync_arbiter.py — VPS-authoritative sync arbitration.

Post-cutover (Phase 2 LIVE) the VPS holds the canonical working tree.
Pre-cutover (Phase 1) the laptop holds it. This module arbitrates writes
across the three planes — laptop, VPS, GitHub — and refuses operations
that violate the locked rules.

Rules (per locked Q4 + section_B locked decision):

  1. VPS is the canonical store post-cutover (C5). Laptop becomes
     a thin client.
  2. GitHub is the immutable framework mirror (`private_github` /
     `mirror_sanitized` only).
  3. Drive (rclone-crypt) is the only off-laptop plane that holds
     clear-text framework material; encrypted blobs handle strict_local.
  4. `strict_local_maximum` data is HARD-BLOCKED from all external planes.
  5. Every cross-plane write goes through the egress firewall (classifier).

This module produces ARBITRATION DECISIONS; actual transport (rsync, git,
rclone) is performed by separate scripts that call `decide()` first.

Pure stdlib.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Iterable

from . import classifier, kill_switch


class Plane(str, enum.Enum):
    # Names harmonized with classifier.EGRESS_MATRIX targets.
    LAPTOP = "laptop_disk"
    VPS_PLAINTEXT = "vps_plaintext"
    VPS_ENCRYPTED_VOLUME = "vps_encrypted_volume"
    GITHUB_PRIVATE = "github_private"
    DRIVE_CLEAR = "drive_clear"
    DRIVE_CRYPT = "drive_crypt"
    NOTION_SANITIZED = "notion_sanitized"
    TELEGRAM_OPERATOR = "telegram_operator"
    ZDR_INFERENCE = "zdr_inference"


# Allowed targets per classification (mirrors classifier.EGRESS_MATRIX
# but adds Drive-crypt and Telegram-operator targets the matrix doesn't know).
_ALLOWED = {
    "strict_local_maximum": set(),
    "strict_local": {Plane.LAPTOP, Plane.VPS_ENCRYPTED_VOLUME, Plane.DRIVE_CRYPT,
                     Plane.TELEGRAM_OPERATOR, Plane.ZDR_INFERENCE},
    "review_before_commit": {Plane.LAPTOP, Plane.VPS_PLAINTEXT, Plane.GITHUB_PRIVATE,
                              Plane.DRIVE_CLEAR, Plane.TELEGRAM_OPERATOR,
                              Plane.ZDR_INFERENCE},
    "private_github": {Plane.LAPTOP, Plane.VPS_PLAINTEXT, Plane.GITHUB_PRIVATE,
                       Plane.DRIVE_CLEAR, Plane.NOTION_SANITIZED,
                       Plane.TELEGRAM_OPERATOR, Plane.ZDR_INFERENCE},
    "mirror_sanitized": {Plane.LAPTOP, Plane.VPS_PLAINTEXT, Plane.GITHUB_PRIVATE,
                         Plane.DRIVE_CLEAR, Plane.NOTION_SANITIZED,
                         Plane.TELEGRAM_OPERATOR, Plane.ZDR_INFERENCE},
}


@dataclass
class Decision:
    allowed: bool
    reason: str
    classification: str
    rel_path: str
    target: Plane

    def __bool__(self) -> bool:
        return self.allowed


def decide(rel_path: str, target: Plane) -> Decision:
    """Single-path arbitration."""
    kill_switch.assert_alive("sync_arbiter.decide")
    cls = classifier.classify(rel_path)
    permitted = _ALLOWED.get(cls, set())
    if target in permitted:
        return Decision(True,
                        f"ok: {cls} -> {target.value}", cls, rel_path, target)
    return Decision(False,
                    f"HIMAYAH refuses: {cls} -> {target.value} not in "
                    f"{[p.value for p in permitted]}",
                    cls, rel_path, target)


def decide_many(paths: Iterable[str], target: Plane) -> list[Decision]:
    return [decide(p, target) for p in paths]


def pre_commit_check(paths: Iterable[str]) -> tuple[bool, list[Decision]]:
    """Used by the .git/hooks/pre-commit hook.

    Any path classified strict_local or strict_local_maximum -> BLOCK.
    """
    decisions = decide_many(paths, Plane.GITHUB_PRIVATE)
    blocked = [d for d in decisions if not d.allowed]
    return len(blocked) == 0, blocked


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("usage: sync_arbiter.py <rel_path> <target_plane>")
        sys.exit(2)
    path = sys.argv[1]
    plane = Plane(sys.argv[2])
    d = decide(path, plane)
    print(f"{path} -> {plane.value}: {'ALLOW' if d.allowed else 'BLOCK'} ({d.reason})")
    sys.exit(0 if d.allowed else 1)
