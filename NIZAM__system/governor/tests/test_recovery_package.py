"""test_recovery_package.py — proofs for the G8 off-VPS recovery package.

Contract: NIZAM__system/governor, same G8 recovery-layer phase as
recovery_package.py. Uses ONLY synthetic secrets and a throwaway age
keypair generated fresh inside each test's tmp_path; never touches a real
/etc/nizam/*.env value and never sees the owner's real private key. The
throwaway private key is written to tmp_path (auto-cleaned by pytest) and
never leaves this process.
"""

import subprocess
import json
import shutil
from pathlib import Path

import pytest

from NIZAM__system.governor import recovery_package as rp


AGE_AVAILABLE = shutil.which("age") is not None and shutil.which("age-keygen") is not None
pytestmark = pytest.mark.skipif(not AGE_AVAILABLE, reason="age/age-keygen not installed")


@pytest.fixture()
def test_keypair(tmp_path: Path):
    """Generate a throwaway synthetic age keypair, purely for this test run."""
    identity_file = tmp_path / "synthetic-test-identity.txt"
    subprocess.run(
        ["age-keygen", "-o", str(identity_file)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    text = identity_file.read_text()
    pub_line = [l for l in text.splitlines() if l.startswith("# public key:")][0]
    public_key = pub_line.split(":", 1)[1].strip()
    return public_key, identity_file


class TestEncryptDecryptRoundTrip:
    def test_round_trip_recovers_exact_plaintext(self, test_keypair):
        public_key, identity_file = test_keypair
        plaintext = b"# === finance.env ===\nSYNTHETIC_KEY=synthetic-value-not-real\n"
        ciphertext = rp.encrypt_bytes(plaintext, public_key)
        assert ciphertext != plaintext
        recovered = rp.decrypt_bytes(ciphertext, identity_file)
        assert recovered == plaintext

    def test_ciphertext_is_not_recognizable_plaintext(self, test_keypair):
        public_key, _ = test_keypair
        plaintext = b"SLACK_BOT_TOKEN=synthetic-not-a-real-token-value"
        ciphertext = rp.encrypt_bytes(plaintext, public_key)
        assert b"synthetic-not-a-real-token-value" not in ciphertext

    def test_rejects_non_age_recipient(self):
        with pytest.raises(rp.RecoveryPackageError):
            rp.encrypt_bytes(b"data", "not-a-real-age-key")


class TestTamperDetection:
    def test_bitflip_in_ciphertext_fails_decryption(self, test_keypair):
        public_key, identity_file = test_keypair
        plaintext = b"SYNTHETIC_SECRET=abc123"
        ciphertext = bytearray(rp.encrypt_bytes(plaintext, public_key))
        # Flip one bit roughly in the middle of the ciphertext body.
        mid = len(ciphertext) // 2
        ciphertext[mid] ^= 0x01
        with pytest.raises(rp.RecoveryPackageError):
            rp.decrypt_bytes(bytes(ciphertext), identity_file)

    def test_wrong_identity_cannot_decrypt(self, test_keypair, tmp_path):
        public_key, _identity_file = test_keypair
        plaintext = b"SYNTHETIC_SECRET=abc123"
        ciphertext = rp.encrypt_bytes(plaintext, public_key)

        other_identity = tmp_path / "other-identity.txt"
        subprocess.run(
            ["age-keygen", "-o", str(other_identity)],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        with pytest.raises(rp.RecoveryPackageError):
            rp.decrypt_bytes(ciphertext, other_identity)

    def test_hash_manifest_detects_tampered_file_on_disk(self, tmp_path, test_keypair):
        public_key, identity_file = test_keypair
        manifest = rp.build_manifest(
            env_file_names=["synthetic.env"],
            env_file_var_names={"synthetic.env": ["SYNTHETIC_KEY"]},
            governance_hashes={"kill_switch.py": "deadbeef" * 8},
            repo_commits={"nizamcore": "abc1234"},
            kill_switch_file_present=True,
            generated_at="2026-09-02T00:00:00+00:00",
        )
        secrets = rp.collect_secret_bundle({"synthetic.env": b"SYNTHETIC_KEY=synthetic-value"})
        encrypted = rp.encrypt_bytes(secrets, public_key)
        out_dir = tmp_path / "package"
        hashes = rp.write_package(out_dir, manifest, encrypted, "# restore\n")

        # Simulate corruption after the fact (e.g. a bad transfer to Drive).
        secrets_path = out_dir / "secrets.age"
        corrupted = bytearray(secrets_path.read_bytes())
        corrupted[10] ^= 0xFF
        secrets_path.write_bytes(bytes(corrupted))

        recomputed = rp.sha256_hex(secrets_path.read_bytes())
        assert recomputed != hashes["secrets.age"], "corruption must change the hash"


class TestManifestNeverLeaksSecrets:
    def test_manifest_contains_only_variable_names_not_values(self):
        manifest = rp.build_manifest(
            env_file_names=["finance.env"],
            env_file_var_names={"finance.env": ["OPENROUTER_API_KEY", "SLACK_BOT_TOKEN"]},
            governance_hashes={},
            repo_commits={},
            kill_switch_file_present=True,
        )
        dumped = json.dumps(manifest)
        assert "OPENROUTER_API_KEY" in dumped
        assert "SLACK_BOT_TOKEN" in dumped
        # A real-looking secret value must never appear, only the key names.
        assert "sk-" not in dumped
        assert "xoxb-" not in dumped

    def test_env_var_names_extraction_ignores_comments_and_blank_lines(self):
        content = "# comment\n\nOPENROUTER_API_KEY=sk-should-not-appear-in-manifest\nBUS_PORT=1234\n"
        names = rp.env_var_names(content)
        assert names == ["OPENROUTER_API_KEY", "BUS_PORT"]

    def test_get_age_recipient_rejects_missing_file(self, tmp_path):
        with pytest.raises(rp.RecoveryPackageError):
            rp.get_age_recipient(tmp_path / "does-not-exist.env")

    def test_get_age_recipient_rejects_missing_var(self, tmp_path):
        f = tmp_path / "backup.env"
        f.write_text("BACKUP_WORK_DIR=/some/path\n")
        with pytest.raises(rp.RecoveryPackageError):
            rp.get_age_recipient(f)

    def test_get_age_recipient_reads_configured_public_key(self, tmp_path):
        f = tmp_path / "backup.env"
        f.write_text("BACKUP_WORK_DIR=/some/path\nAGE_RECOVERY_PUBLIC_KEY=age1exampleexampleexample\n")
        assert rp.get_age_recipient(f) == "age1exampleexampleexample"


class TestPackageWriteAndHashes:
    def test_write_package_produces_four_files_with_matching_hashes(self, tmp_path, test_keypair):
        public_key, _ = test_keypair
        manifest = rp.build_manifest(
            env_file_names=["a.env", "b.env"],
            env_file_var_names={"a.env": ["FOO"], "b.env": ["BAR"]},
            governance_hashes={"classifier.py": "cafebabe" * 8},
            repo_commits={"nizamcore": "0000000"},
            kill_switch_file_present=False,
        )
        secrets = rp.collect_secret_bundle({
            "a.env": b"FOO=synthetic-foo",
            "b.env": b"BAR=synthetic-bar",
        })
        encrypted = rp.encrypt_bytes(secrets, public_key)
        out_dir = tmp_path / "pkg"
        hashes = rp.write_package(out_dir, manifest, encrypted, rp.RESTORE_INSTRUCTIONS_TEMPLATE.format(generated_at="now"))

        for fname in ("MANIFEST.json", "secrets.age", "RESTORE_INSTRUCTIONS.md", "HASHES.json"):
            assert (out_dir / fname).exists()

        for fname, expected_hash in hashes.items():
            actual = rp.sha256_hex((out_dir / fname).read_bytes())
            assert actual == expected_hash

    def test_collect_secret_bundle_labels_each_source_file(self):
        bundle = rp.collect_secret_bundle({
            "x.env": b"X=1",
            "y.env": b"Y=2",
        })
        text = bundle.decode("utf-8")
        assert "# === x.env ===" in text
        assert "# === y.env ===" in text
        assert "X=1" in text
        assert "Y=2" in text
