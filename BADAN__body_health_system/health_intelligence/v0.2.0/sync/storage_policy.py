#!/usr/bin/env python3
"""
storage_policy.py — Storage-class policy for the health knowledge plane.

Owning contract: NIZAM-HEALTH-INTELLIGENCE v0.2.0
Phase: cloud-first reconciliation

Contains policy only. Deliberately holds NO folder IDs, hostnames, paths or any
other deployment particular, so this file is safe to version in Git. The live
identifiers live in drive_layout.py, which stays on the VPS.

Storage classes (spec 02 §2):
  vps_secret    encrypted VPS secret store            Drive: never
  vps_private   VPS DB/files                          Drive: no by default
  cloud_private VPS + private Drive when permitted    Drive: yes
  drive_knowledge private 47_NIZAM                    Drive: yes
  github_versioned private repo                       not a data store

`strict_local` is legacy and means VPS-only (spec 02 §36). It is never broadened.
"""
from __future__ import annotations

CONTRACT = "NIZAM-HEALTH-INTELLIGENCE v0.2.0"
SCHEMA_VERSION = "0.2.0"
TIMEZONE = "Africa/Cairo"

DRIVE_ALLOWED_CLASSES = frozenset({"cloud_private", "drive_knowledge"})
DRIVE_FORBIDDEN_CLASSES = frozenset({"vps_secret", "vps_private", "strict_local"})
ALL_CLASSES = frozenset(
    DRIVE_ALLOWED_CLASSES | DRIVE_FORBIDDEN_CLASSES | {"github_versioned"}
)
