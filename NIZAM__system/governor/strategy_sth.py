"""strategy_sth.py — RFC 6962 Merkle tree + Ed25519 Signed Tree Head (E4.3).

Hardens `STRATEGY_LEDGER.jsonl` with:

  * An RFC 6962-style Merkle hash tree over the row_hash sequence.
  * An Ed25519 Signed Tree Head published to
    `NIZAM__system/ledgers/sth/STRATEGY_LEDGER.sth.json` on every
    append and once every 10 minutes via the systemd timer (I6).

If the optional `arc-protocol` package is installed we use its Merkle
implementation; otherwise we fall back to a small RFC 6962-faithful
implementation here. Either way the leaf hashing rule is:

    leaf_hash = SHA256(0x00 || row_hash)
    node_hash = SHA256(0x01 || left || right)

(per RFC 6962 §2.1).

Ed25519 keypair is loaded from:

  * env `NIZAM_STRATEGY_STH_KEY_PATH` (if set), OR
  * `NIZAM__system/governor/.keys/strategy_sth.ed25519` (gitignored).

The PUBLIC key is published alongside the STH so verifiers can confirm
without trusting the local disk. The PRIVATE key never leaves disk.

Pure stdlib + optional `cryptography` for Ed25519 + optional
`arc-protocol`. If `cryptography` is not present, this module degrades
to publishing an UNSIGNED tree head with `signature: null`; Ammar emits
a periodic alert until the dependency is installed.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any

_DEFAULT_REPO = Path(__file__).resolve().parents[2]
_LEDGERS_DIR = _DEFAULT_REPO / "NIZAM__system" / "ledgers"
_STH_DIR = _LEDGERS_DIR / "sth"
_KEY_DIR = Path(__file__).resolve().parent / ".keys"
_DEFAULT_KEY = _KEY_DIR / "strategy_sth.ed25519"


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# -------------------- RFC 6962 Merkle (fallback) --------------------

def _leaf_hash(row_hash_hex: str) -> bytes:
    """RFC 6962 §2.1 leaf hashing."""
    return hashlib.sha256(b"\x00" + bytes.fromhex(row_hash_hex)).digest()


def _node_hash(left: bytes, right: bytes) -> bytes:
    """RFC 6962 §2.1 internal node hashing."""
    return hashlib.sha256(b"\x01" + left + right).digest()


def _merkle_root_local(row_hashes: list[str]) -> bytes:
    """Compute Merkle root over a sequence of row_hash hex strings.

    Uses RFC 6962-faithful (non-power-of-two-safe) rules: at each level,
    if odd count remains, the last element is carried up unhashed.
    """
    if not row_hashes:
        return b"\x00" * 32
    level = [_leaf_hash(h) for h in row_hashes]
    while len(level) > 1:
        nxt: list[bytes] = []
        for i in range(0, len(level), 2):
            if i + 1 < len(level):
                nxt.append(_node_hash(level[i], level[i + 1]))
            else:
                nxt.append(level[i])
        level = nxt
    return level[0]


def merkle_root(row_hashes: list[str]) -> bytes:
    """Compute the Merkle root. Tries `arc-protocol` first; falls back."""
    try:
        from arc_protocol.merkle import merkle_root as _ext_root  # type: ignore
        return _ext_root([bytes.fromhex(h) for h in row_hashes])
    except Exception:
        return _merkle_root_local(row_hashes)


# -------------------- Ed25519 STH signing --------------------

def _load_signing_key():
    """Return an Ed25519PrivateKey or None if cryptography is missing.

    On first call, generates a new keypair and persists it to disk if
    none exists.
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.hazmat.primitives import serialization
    except Exception:
        return None, None

    key_path = Path(os.environ.get("NIZAM_STRATEGY_STH_KEY_PATH",
                                   str(_DEFAULT_KEY)))
    key_path.parent.mkdir(parents=True, exist_ok=True)
    if key_path.exists() and key_path.stat().st_size > 0:
        sk_bytes = key_path.read_bytes()
        sk = serialization.load_pem_private_key(sk_bytes, password=None)
    else:
        sk = ed25519.Ed25519PrivateKey.generate()
        pem = sk.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        key_path.write_bytes(pem)
        try:
            os.chmod(key_path, 0o600)
        except OSError:
            pass
    pk_bytes = sk.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return sk, pk_bytes


def _sign_tree_head(sk, payload_bytes: bytes) -> bytes | None:
    if sk is None:
        return None
    return sk.sign(payload_bytes)


# -------------------- Public API --------------------

def collect_row_hashes() -> list[str]:
    """Read STRATEGY_LEDGER.jsonl and return row_hash sequence in order."""
    path = _LEDGERS_DIR / "STRATEGY_LEDGER.jsonl"
    if not path.exists():
        return []
    out: list[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rh = row.get("row_hash")
            if isinstance(rh, str) and len(rh) == 64:
                out.append(rh)
    return out


def publish_sth() -> dict[str, Any]:
    """Compute Merkle root over STRATEGY_LEDGER, sign, persist STH.

    Returns the STH dict that was written.
    """
    rows = collect_row_hashes()
    root = merkle_root(rows)
    payload = {
        "schema_version": "1.0",
        "ledger": "STRATEGY_LEDGER",
        "tree_size": len(rows),
        "root_hash_hex": root.hex(),
        "timestamp": _utc_now(),
    }
    payload_bytes = json.dumps(
        payload, sort_keys=True, ensure_ascii=False
    ).encode("utf-8")

    sk, pk_bytes = _load_signing_key()
    sig = _sign_tree_head(sk, payload_bytes)

    sth = dict(payload)
    sth["public_key_raw_hex"] = pk_bytes.hex() if pk_bytes else None
    sth["signature_hex"] = sig.hex() if sig else None
    sth["algorithm"] = "Ed25519" if sig else "unsigned"

    _STH_DIR.mkdir(parents=True, exist_ok=True)
    path = _STH_DIR / "STRATEGY_LEDGER.sth.json"
    path.write_text(
        json.dumps(sth, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    # Also archive a timestamped copy so verifiers can audit history.
    archive_path = _STH_DIR / f"STRATEGY_LEDGER.{sth['tree_size']:08d}.sth.json"
    archive_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    return sth


def verify_sth(sth: dict[str, Any]) -> tuple[bool, str]:
    """Verify a STH dict against the current STRATEGY_LEDGER on disk.

    Returns (ok, reason_or_root_hex).
    """
    rows = collect_row_hashes()
    if len(rows) != sth.get("tree_size"):
        return False, "tree_size mismatch"
    root = merkle_root(rows)
    if root.hex() != sth.get("root_hash_hex"):
        return False, "root_hash mismatch"
    sig_hex = sth.get("signature_hex")
    if not sig_hex:
        return True, "unsigned ok (root matches)"
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except Exception:
        return True, "signed but cryptography unavailable; root matches"
    pk_hex = sth.get("public_key_raw_hex")
    if not pk_hex:
        return False, "signature present but no public key"
    pk = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(pk_hex))
    # Re-serialize payload exactly as in publish_sth().
    payload = {k: sth[k] for k in (
        "schema_version", "ledger", "tree_size",
        "root_hash_hex", "timestamp",
    )}
    payload_bytes = json.dumps(
        payload, sort_keys=True, ensure_ascii=False
    ).encode("utf-8")
    try:
        pk.verify(bytes.fromhex(sig_hex), payload_bytes)
        return True, "signature ok"
    except Exception as exc:  # InvalidSignature
        return False, f"signature invalid: {exc}"


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "publish"
    if cmd == "publish":
        out = publish_sth()
        print(json.dumps(out, indent=2))
    elif cmd == "verify":
        path = _STH_DIR / "STRATEGY_LEDGER.sth.json"
        if not path.exists():
            print("no STH on disk; run publish first")
            sys.exit(2)
        sth = json.loads(path.read_text(encoding="utf-8"))
        ok, reason = verify_sth(sth)
        print(f"ok={ok} reason={reason}")
        sys.exit(0 if ok else 1)
    else:
        print("usage: strategy_sth.py [publish|verify]")
        sys.exit(2)
