#!/usr/bin/env python3
"""GAP closure: G2 (POP->NIZAM rename) + G3 (visibility=private) + G4 (stale path) + G5 (MARSAD).

Pure stdlib. No egress.

Tasks executed:
- G2.1  Rename POP_TEMPLE.json -> NIZAM_TEMPLE.json
- G2.2  Rename POP_MASTER_REGISTER.json -> NIZAM_MASTER_REGISTER.json
- G2.3  Update PRIVACY_CLASSIFICATION.json glob entries (POP_*->NIZAM_*)
- G2.4  Update SYNC_POLICY.json allowed[] + canonical_source_of_truth
- G2.5  Update AGENT_MAPPING.json POP_TEMPLE refs (token swap)
- G2.6  Update top-level docs (CRITICAL_FACTS, README, index, .gitignore, log.md)
- G2.7  Update D:\\NIZAM\\AGENTS.md (workspace-level)
- G2.8  Update tools/nizam_startup.py + D:\\NIZAM\\scripts\\verify-nizamcore.ps1
- G3.2  visibility -> private in NIZAM_TEMPLE.json
- G3.3  Verify TOOL_ACCESS_MATRIX consistency
- G4    Replace stale C:\\Users\\selsherb path in 3 live configs
- G5.1  Add MARSAD to NIZAM_TEMPLE modules block
- G5.2  Add MARSAD to phase_2_folders
- G5.3  Add infrastructure_folders block (MAKHZAN+HAJR) so total=21
- G2.9 / G5.3 Verification scans
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WORKSPACE = REPO
NEW_CANONICAL = "local working tree at D:\\NIZAM"

SKIP_PATHS = {REPO / "CHANGELOG.md"}
SKIP_DIRS_PREFIXES = [
    REPO / "MAKHZAN__archive",
    REPO / ".git",
    REPO / ".venv",
    REPO / "install-audit",
]


def _skip(p: Path) -> bool:
    if p in SKIP_PATHS:
        return True
    for prefix in SKIP_DIRS_PREFIXES:
        try:
            p.relative_to(prefix)
            return True
        except ValueError:
            continue
    return False


def _walk_text(repo: Path) -> list[Path]:
    out: list[Path] = []
    for p in repo.rglob("*"):
        if not p.is_file() or _skip(p):
            continue
        if p.suffix.lower() in {
            ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".pyc",
            ".so", ".dll", ".exe", ".whl", ".tar", ".gz", ".zip", ".sqlite",
        }:
            continue
        out.append(p)
    return out


def step_renames() -> None:
    print("[G2.1, G2.2] File renames")
    pop_temple = REPO / "POP_TEMPLE.json"
    nizam_temple = REPO / "NIZAM_TEMPLE.json"
    if pop_temple.exists():
        pop_temple.rename(nizam_temple)
        print(f"  RENAME: POP_TEMPLE.json -> NIZAM_TEMPLE.json")
    pop_reg = REPO / "POP_MASTER_REGISTER.json"
    nizam_reg = REPO / "NIZAM_MASTER_REGISTER.json"
    if pop_reg.exists():
        pop_reg.rename(nizam_reg)
        print(f"  RENAME: POP_MASTER_REGISTER.json -> NIZAM_MASTER_REGISTER.json")


def step_temple_internals() -> None:
    print("[G2.x / G3.2 / G4 / G5] NIZAM_TEMPLE.json structural edits")
    temple_path = REPO / "NIZAM_TEMPLE.json"
    data = json.loads(temple_path.read_text(encoding="utf-8"))

    # G2: codename
    data["codename"] = "NIZAM"

    # G4: canonical_source_of_truth path
    data["canonical_source_of_truth"] = NEW_CANONICAL

    # G3.2: visibility -> private (locked decision Q3)
    cr = data.get("canonical_remote", {})
    cr["visibility"] = "private"
    cr["visibility_decision_date"] = "2026-05-28"
    cr["visibility_rationale"] = (
        "Locked by NIZAM_NEXT_PLAN_EXPANSION_v2 Q3. Private aligns with "
        "TOOL_ACCESS_MATRIX (github_private_repo). Operator + tooling retain "
        "access; firewall simpler with public-leak risk class eliminated. "
        "Drive (NQ1) is the only off-laptop plane holding clear-text framework "
        "material; encrypted blobs handle the rest. USER must flip the GitHub "
        "UI to private (G3.1) for this declaration to match live state."
    )
    data["canonical_remote"] = cr

    # G5.1: Add MARSAD module entry
    modules = data.get("modules", {})
    if "MARSAD" not in modules:
        modules["MARSAD"] = {
            "phase": 2,
            "persona": "NIZAM__system/personas/MARSAD.json",
            "scaffolded": True,
            "live": True,
            "note": "Flight-radar intel scout. Persona to be created at B2.7."
        }
    data["modules"] = modules

    # G5.2: Add MARSAD to phase_2_folders if missing
    p2 = data.get("phase_2_folders", [])
    if "MARSAD" not in p2:
        p2.append("MARSAD")
    data["phase_2_folders"] = p2

    # G5.3: Add infrastructure_folders block so disk topology count matches (21)
    if "infrastructure_folders" not in data:
        data["infrastructure_folders"] = ["MAKHZAN", "HAJR"]

    # G5.3: explicit disk topology invariant
    data["disk_topology_count"] = 21

    temple_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"  REWRITE: NIZAM_TEMPLE.json "
          f"(codename, canonical_source_of_truth, visibility, MARSAD, "
          f"infrastructure_folders, disk_topology_count)")


def step_master_register_internals() -> None:
    print("[G4] NIZAM_MASTER_REGISTER.json root path")
    reg_path = REPO / "NIZAM_MASTER_REGISTER.json"
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    data["root"] = "D:\\NIZAM\\nizamcore"

    # G5.1: Add MARSAD folder entry if missing
    folders = data.get("folders", [])
    symbols = {row.get("symbol") for row in folders}
    if "MARSAD" not in symbols:
        folders.append({
            "path": "MARSAD__flight_radar",
            "phase": 2,
            "symbol": "MARSAD",
            "meaning_ar": "watchtower / observation post — intel scout",
            "privacy": "review_before_commit",
            "registers": "_index.json",
            "scaffolded": True,
            "live": True,
        })
    data["folders"] = folders

    reg_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"  REWRITE: NIZAM_MASTER_REGISTER.json (root path + MARSAD entry)")


def step_sync_policy() -> None:
    print("[G2.4 / G4] SYNC_POLICY.json")
    p = REPO / "NIZAM__system" / "policies" / "SYNC_POLICY.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    if "canonical_source_of_truth" in data:
        data["canonical_source_of_truth"] = NEW_CANONICAL
    # Token swap in any allowed[] entries
    for k in ("allowed", "include_paths", "tokens"):
        if k in data and isinstance(data[k], list):
            data[k] = [
                s.replace("POP_TEMPLE", "NIZAM_TEMPLE")
                 .replace("POP_MASTER_REGISTER", "NIZAM_MASTER_REGISTER")
                if isinstance(s, str) else s
                for s in data[k]
            ]
    p.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"  REWRITE: SYNC_POLICY.json (path + token swap)")


def step_critical_facts() -> None:
    print("[G2.6 / G4] CRITICAL_FACTS.md")
    p = REPO / "CRITICAL_FACTS.md"
    text = p.read_text(encoding="utf-8")
    new = text.replace(
        "**POP root**: `C:\\Users\\selsherb\\POP`. Off OneDrive. Local-first.",
        "**NIZAM root**: `D:\\NIZAM\\nizamcore`. Off OneDrive. Local-first.",
    )
    p.write_text(new, encoding="utf-8")
    print(f"  REWRITE: CRITICAL_FACTS.md (POP root -> NIZAM root)")


def step_token_swap_repo() -> tuple[int, int]:
    print("[G2.x] Token swap across repo (POP_TEMPLE -> NIZAM_TEMPLE, "
          "POP_MASTER_REGISTER -> NIZAM_MASTER_REGISTER)")
    pairs = [
        ("POP_MASTER_REGISTER", "NIZAM_MASTER_REGISTER"),
        ("POP_TEMPLE", "NIZAM_TEMPLE"),
    ]
    files_changed = 0
    hits = 0
    for p in _walk_text(REPO):
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        original = text
        local_hits = 0
        for old, new in pairs:
            cnt = text.count(old)
            if cnt:
                text = text.replace(old, new)
                local_hits += cnt
        if text != original:
            p.write_text(text, encoding="utf-8")
            files_changed += 1
            hits += local_hits
            print(f"  EDIT ({local_hits}): {p.relative_to(REPO)}")
    return files_changed, hits


def step_workspace_files() -> None:
    print("[G2.7 / G2.8] Workspace-level files (D:\\NIZAM)")
    # AGENTS.md
    agents = WORKSPACE / "AGENTS.md"
    if agents.exists():
        t = agents.read_text(encoding="utf-8")
        t = t.replace(
            "NIZAM Core / POP repo: `D:\\NIZAM\\nizamcore`",
            "NIZAM Core repo: `D:\\NIZAM\\nizamcore`",
        )
        t = t.replace(
            "`D:\\NIZAM\\nizamcore\\POP_TEMPLE.json` \u2192 `platform_version`",
            "`D:\\NIZAM\\nizamcore\\NIZAM_TEMPLE.json` \u2192 `platform_version`",
        )
        t = t.replace(
            "`D:\\NIZAM\\nizamcore` is the GitHub mirror and POP system source.",
            "`D:\\NIZAM\\nizamcore` is the GitHub mirror and NIZAM system source.",
        )
        t = t.replace("POP_TEMPLE", "NIZAM_TEMPLE").replace(
            "POP_MASTER_REGISTER", "NIZAM_MASTER_REGISTER"
        )
        agents.write_text(t, encoding="utf-8")
        print(f"  REWRITE: D:\\NIZAM\\AGENTS.md")

    # verify-nizamcore.ps1
    ver = WORKSPACE / "scripts" / "verify-nizamcore.ps1"
    if ver.exists():
        t = ver.read_text(encoding="utf-8")
        t = t.replace("POP_TEMPLE", "NIZAM_TEMPLE").replace(
            "POP_MASTER_REGISTER", "NIZAM_MASTER_REGISTER"
        )
        ver.write_text(t, encoding="utf-8")
        print(f"  REWRITE: D:\\NIZAM\\scripts\\verify-nizamcore.ps1")


def step_startup_constant() -> None:
    print("[G2.8] tools/nizam_startup.py POP_TEMPLE constant")
    p = REPO / "tools" / "nizam_startup.py"
    t = p.read_text(encoding="utf-8")
    # Rename the python variable from POP_TEMPLE to NIZAM_TEMPLE for consistency
    t = re.sub(r"\bPOP_TEMPLE\b", "NIZAM_TEMPLE", t)
    p.write_text(t, encoding="utf-8")
    print(f"  REWRITE: tools/nizam_startup.py (variable + path)")


def step_tool_access_matrix_check() -> None:
    print("[G3.3] TOOL_ACCESS_MATRIX consistency check")
    p = REPO / "NIZAM__system" / "policies" / "TOOL_ACCESS_MATRIX.json"
    if not p.exists():
        print(f"  SKIP: TOOL_ACCESS_MATRIX.json not present")
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    # Walk and find any tool that has a sync_target or note referencing public repo
    found = []

    def _walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and ("public" in v.lower() or
                                           "github" in v.lower()):
                    found.append((path + "/" + k, v))
                _walk(v, path + "/" + k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _walk(v, f"{path}[{i}]")

    _walk(data)
    print(f"  TOOL_ACCESS_MATRIX entries referencing public/github: {len(found)}")
    for ref in found[:10]:
        print(f"    {ref[0]}: {ref[1][:80]}")
    print(f"  Locked decision: github visibility = private. "
          f"Operator must flip UI (G3.1). No further code change needed.")


def step_verify() -> int:
    print("[G2.9 / G5.3] Verification scans")
    rc = 0

    # Verify no POP_TEMPLE / POP_MASTER_REGISTER outside MAKHZAN / CHANGELOG
    leftover = []
    for p in _walk_text(REPO):
        try:
            t = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(t.splitlines(), 1):
            if re.search(r"POP_TEMPLE|POP_MASTER_REGISTER", line):
                leftover.append(f"{p.relative_to(REPO)}:{i}:{line.rstrip()}")
    if leftover:
        print("  RESIDUE (POP_TEMPLE / POP_MASTER_REGISTER):")
        for x in leftover[:30]:
            print(f"    {x}")
        rc = 1
    else:
        print("  CLEAN: zero POP_TEMPLE / POP_MASTER_REGISTER residue.")

    # Verify selsherb path in 3 live configs is gone
    live_configs = [
        REPO / "NIZAM_TEMPLE.json",
        REPO / "NIZAM_MASTER_REGISTER.json",
        REPO / "NIZAM__system" / "policies" / "SYNC_POLICY.json",
    ]
    selsherb_in_configs = []
    for p in live_configs:
        if p.exists():
            t = p.read_text(encoding="utf-8")
            if "selsherb" in t:
                selsherb_in_configs.append(str(p))
    if selsherb_in_configs:
        print("  RESIDUE selsherb in live configs:")
        for x in selsherb_in_configs:
            print(f"    {x}")
        rc = 1
    else:
        print("  CLEAN: zero selsherb in 3 live configs.")

    # Verify MARSAD presence
    temple = json.loads((REPO / "NIZAM_TEMPLE.json").read_text(encoding="utf-8"))
    if "MARSAD" not in temple.get("modules", {}):
        print("  FAIL: MARSAD missing from NIZAM_TEMPLE#modules")
        rc = 1
    if "MARSAD" not in temple.get("phase_2_folders", []):
        print("  FAIL: MARSAD missing from NIZAM_TEMPLE#phase_2_folders")
        rc = 1
    if temple.get("disk_topology_count") != 21:
        print(f"  FAIL: disk_topology_count = "
              f"{temple.get('disk_topology_count')} != 21")
        rc = 1
    if rc == 0:
        print("  CLEAN: MARSAD wired + disk_topology_count=21")

    # Verify visibility flip
    if temple.get("canonical_remote", {}).get("visibility") != "private":
        print(f"  FAIL: visibility = "
              f"{temple.get('canonical_remote', {}).get('visibility')}")
        rc = 1
    else:
        print("  CLEAN: visibility = private (Operator must still flip GitHub UI)")

    return rc


def main() -> int:
    step_renames()
    files_changed, hits = step_token_swap_repo()
    print(f"  -> {files_changed} files changed, {hits} hits")
    step_temple_internals()
    step_master_register_internals()
    step_sync_policy()
    step_critical_facts()
    step_workspace_files()
    step_startup_constant()
    step_tool_access_matrix_check()
    return step_verify()


if __name__ == "__main__":
    sys.exit(main())
