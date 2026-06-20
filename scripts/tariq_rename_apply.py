#!/usr/bin/env python3
"""Apply KABIR_SHERBO -> Tariq rename across the working tree.

Per D:/NIZAM/scripts/tariq_rename_plan.md (G1.0). Tasks G1.2 - G1.19.

Rules:
- MAKHZAN__archive/** is immutable history; never touched.
- CHANGELOG.md retains historical mentions; never touched.
- .git/** never touched.
- Renames use Path.rename (git detects rename via similarity).
- Token order matters; longer literals first.

Special-case rewrites (not pure token swap):
- TARIQ.json `meaning_ar` field
- KABIR_SHERBO__long_horizon_strategy/README.md etymology line (L3)
- BIG_SHERBO_LONG_WAR_DOCTRINE.md title + opening prose (L1, L3)
- POP_TEMPLE.json `hard_gates`: drop `no_naming_kabir` (G1.19)
- POP_MASTER_REGISTER.json `meaning_ar` field

Pure stdlib. No egress.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Order matters: longer literals first
TOKEN_PAIRS = [
    ("KABIR_SHERBO__long_horizon_strategy", "TARIQ__long_horizon_strategy"),
    ("kabir-sherbo-annual-review", "tariq-annual-review"),
    ("kabir-sherbo-vision", "tariq-vision"),
    ("BIG_SHERBO_LONG_WAR_DOCTRINE", "TARIQ_LONG_WAR_DOCTRINE"),
    ("KABIR_SHERBO", "TARIQ"),
    ("BIG_SHERBO", "TARIQ"),
    ("Big Sherbo", "Tariq"),
    ("Kabir Sherbo", "Tariq"),
]

# Files that retain history; do NOT modify
SKIP_PATHS = {
    REPO / "CHANGELOG.md",
}

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


def _rename(src: Path, dst: Path) -> None:
    if not src.exists():
        print(f"  SKIP (not found): {src}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    print(f"  RENAME: {src.relative_to(REPO)} -> {dst.relative_to(REPO)}")


def step_renames() -> None:
    print("[STEP 1] File/folder renames (G1.2 / G1.4 / G1.5 / G1.6)")
    # Folder rename — Path.rename also moves contents on same FS
    _rename(REPO / "KABIR_SHERBO__long_horizon_strategy",
            REPO / "TARIQ__long_horizon_strategy")
    # Persona JSON
    _rename(REPO / "NIZAM__system" / "personas" / "KABIR_SHERBO.json",
            REPO / "NIZAM__system" / "personas" / "TARIQ.json")
    # Skill MDs
    _rename(REPO / "NIZAM__system" / "skills" / "kabir-sherbo-vision.md",
            REPO / "NIZAM__system" / "skills" / "tariq-vision.md")
    _rename(REPO / "NIZAM__system" / "skills" / "kabir-sherbo-annual-review.md",
            REPO / "NIZAM__system" / "skills" / "tariq-annual-review.md")
    # Doctrine doc
    _rename(REPO / "NIZAM__system" / "docs" / "BIG_SHERBO_LONG_WAR_DOCTRINE.md",
            REPO / "NIZAM__system" / "docs" / "TARIQ_LONG_WAR_DOCTRINE.md")


def _walk_text_files() -> list[Path]:
    out: list[Path] = []
    for p in REPO.rglob("*"):
        if not p.is_file():
            continue
        if _skip(p):
            continue
        suffix = p.suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf",
                       ".pyc", ".pyo", ".so", ".dll", ".exe", ".whl",
                       ".tar", ".gz", ".zip", ".7z", ".sqlite", ".db"}:
            continue
        out.append(p)
    return out


def step_token_replace(files: list[Path]) -> tuple[int, int]:
    print("[STEP 2] Token replacement across tracked tree (G1.7 - G1.18)")
    files_changed = 0
    total_hits = 0
    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        original = text
        hits = 0
        for old, new in TOKEN_PAIRS:
            cnt = text.count(old)
            if cnt:
                text = text.replace(old, new)
                hits += cnt
        if text != original:
            p.write_text(text, encoding="utf-8")
            files_changed += 1
            total_hits += hits
            print(f"  EDIT ({hits} hits): {p.relative_to(REPO)}")
    return files_changed, total_hits


def step_special_rewrites() -> None:
    print("[STEP 3] Special-case rewrites (etymology + gate lift)")

    # 3.a TARIQ.json meaning_ar (G1.3)
    persona = REPO / "NIZAM__system" / "personas" / "TARIQ.json"
    if persona.exists():
        data = json.loads(persona.read_text(encoding="utf-8"))
        data["meaning_ar"] = (
            "knocker / morning star — long-horizon commander "
            "(after Tariq ibn Ziyad)"
        )
        # Refresh role wording to align with the locked role definition
        data["role"] = (
            "Long-horizon strategist — 2/3+ year campaign view. Watches "
            "tactical moves accumulate toward multi-year objectives. "
            "Pairs with Khalid (tactics) + MARSAD (intel) as the "
            "strategic-command triad."
        )
        persona.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"  REWRITE: {persona.relative_to(REPO)} (meaning_ar + role)")

    # 3.b folder README etymology line
    readme = REPO / "TARIQ__long_horizon_strategy" / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        lines = text.splitlines()
        if len(lines) > 2:
            lines[0] = "# TARIQ — Long-Horizon Strategy"
            lines[2] = (
                "Arabic: طارق — \"knocker / morning star.\" "
                "Named for Tariq ibn Ziyad, the long-horizon campaign commander."
            )
        readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  REWRITE: {readme.relative_to(REPO)} (etymology)")

    # 3.c folder _index.json meaning_ar
    idx = REPO / "TARIQ__long_horizon_strategy" / "_index.json"
    if idx.exists():
        data = json.loads(idx.read_text(encoding="utf-8"))
        data["meaning_ar"] = (
            "knocker / morning star — long-horizon commander "
            "(after Tariq ibn Ziyad)"
        )
        idx.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"  REWRITE: {idx.relative_to(REPO)} (meaning_ar)")

    # 3.d POP_MASTER_REGISTER.json meaning_ar entry
    reg = REPO / "POP_MASTER_REGISTER.json"
    if reg.exists():
        data = json.loads(reg.read_text(encoding="utf-8"))
        for row in data.get("folders", []):
            if row.get("symbol") == "TARIQ":
                row["meaning_ar"] = (
                    "knocker / morning star — long-horizon commander "
                    "(after Tariq ibn Ziyad)"
                )
        reg.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"  REWRITE: {reg.relative_to(REPO)} (meaning_ar)")

    # 3.e BIG_SHERBO_LONG_WAR_DOCTRINE.md (now TARIQ_LONG_WAR_DOCTRINE.md)
    doctrine = REPO / "NIZAM__system" / "docs" / "TARIQ_LONG_WAR_DOCTRINE.md"
    if doctrine.exists():
        text = doctrine.read_text(encoding="utf-8")
        lines = text.splitlines()
        if len(lines) > 2:
            lines[0] = "# TARIQ Long War Doctrine"
            lines[2] = (
                "> TARIQ is named after Tariq ibn Ziyad — long-horizon "
                "campaign commander. The doctrine is about playing the long "
                "game across decades."
            )
        doctrine.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  REWRITE: {doctrine.relative_to(REPO)} (title + framing)")

    # 3.f G1.19 lift no_naming_kabir gate from POP_TEMPLE.json
    temple = REPO / "POP_TEMPLE.json"
    if temple.exists():
        data = json.loads(temple.read_text(encoding="utf-8"))
        hard_gates = data.get("hard_gates", {})
        if "no_naming_kabir" in hard_gates:
            del hard_gates["no_naming_kabir"]
            temple.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"  REWRITE: {temple.relative_to(REPO)} "
                  f"(lifted no_naming_kabir gate)")


def step_verify() -> int:
    print("[STEP 4] G1.20 verification scan")
    import re
    pattern = re.compile(
        r"KABIR_SHERBO|kabir-sherbo|BIG_SHERBO|Big Sherbo|Kabir Sherbo",
        re.IGNORECASE,
    )
    leftover: list[str] = []
    for p in _walk_text_files():
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                leftover.append(f"{p.relative_to(REPO)}:{i}:{line.rstrip()}")
    if leftover:
        print("  RESIDUE (outside MAKHZAN/CHANGELOG):")
        for entry in leftover[:80]:
            print(f"    {entry}")
        return 1
    print("  CLEAN: zero residue outside MAKHZAN/CHANGELOG.")
    return 0


def main() -> int:
    step_renames()
    files = _walk_text_files()
    files_changed, hits = step_token_replace(files)
    print(f"  -> {files_changed} files changed, {hits} hits replaced")
    step_special_rewrites()
    return step_verify()


if __name__ == "__main__":
    sys.exit(main())
