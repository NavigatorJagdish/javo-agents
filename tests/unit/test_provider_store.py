"""Provider persistence, redaction and cross-process loss-prevention contracts."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys

from cryptography.fernet import Fernet
import pytest

from app.config import Settings
from app.core.provider_store import ProviderVault, VaultUnavailable
from app.services import provider_settings as providers

SECRET = "synthetic-master-key-for-tests-" * 2


@pytest.fixture
def configured(tmp_path, monkeypatch):
    settings = Settings(provider_config_path=str(tmp_path / "providers.enc"), encryption_key=SECRET)
    monkeypatch.setattr(providers, "get_settings", lambda: settings)
    return settings


def test_ciphertext_survives_new_object_and_excludes_plaintext(tmp_path):
    path = tmp_path / "provider.enc"
    vault = ProviderVault(path, SECRET)
    vault.update(
        lambda data: data["providers"].update({"gemini": {"api_key": "synthetic-private-value"}})
    )
    assert b"synthetic-private-value" not in path.read_bytes()
    assert (
        ProviderVault(path, SECRET).read()["providers"]["gemini"]["api_key"]
        == "synthetic-private-value"
    )
    if sys.platform != "win32":
        assert path.stat().st_mode & 0o777 == 0o600


def test_wrong_key_or_tampering_never_reinitializes_storage(tmp_path):
    path = tmp_path / "provider.enc"
    ProviderVault(path, SECRET).update(lambda data: data["settings"].update({"value": 1}))
    before = path.read_bytes()
    with pytest.raises(VaultUnavailable):
        ProviderVault(path, "different-master-key-" * 3).update(lambda data: data.clear())
    assert path.read_bytes() == before
    path.write_bytes(b"damaged ciphertext")
    with pytest.raises(VaultUnavailable):
        ProviderVault(path, SECRET).read()
    assert path.read_bytes() == b"damaged ciphertext"


def test_save_failure_preserves_previous_ciphertext(tmp_path, monkeypatch):
    vault = ProviderVault(tmp_path / "provider.enc", SECRET)
    vault.update(lambda data: data["settings"].update({"value": 1}))
    before = vault.path.read_bytes()

    def fail(*args):
        raise OSError("Simulated disk failure")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(VaultUnavailable):
        vault.update(lambda data: data["settings"].update({"value": 2}))
    assert vault.path.read_bytes() == before
    assert list(tmp_path.glob("*.tmp")) == []


def test_concurrent_writers_merge_without_lost_fields(tmp_path):
    path = tmp_path / "provider.enc"

    def save(index):
        ProviderVault(path, SECRET).update(
            lambda data: data["settings"].update({str(index): index})
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(save, range(20)))
    assert ProviderVault(path, SECRET).read()["settings"] == {str(i): i for i in range(20)}


@pytest.mark.skipif(sys.platform != "win32", reason="Windows mandatory byte locking")
def test_empty_lock_is_acquired_before_its_first_write(tmp_path, monkeypatch):
    import msvcrt

    original = msvcrt.locking
    sizes = []

    def observe(fd, mode, count):
        if mode == msvcrt.LK_NBLCK:
            sizes.append(os.fstat(fd).st_size)
        return original(fd, mode, count)

    monkeypatch.setattr(msvcrt, "locking", observe)
    ProviderVault(tmp_path / "new-vault.enc", SECRET).update(
        lambda document: document["settings"].update({"verified": True})
    )
    assert sizes == [0]
    assert (tmp_path / "new-vault.enc.lock").read_bytes() == b"0"


def test_fresh_concurrent_vault_initialization_stress(tmp_path):
    for attempt in range(10):
        path = tmp_path / f"fresh-{attempt}.enc"

        def save(index):
            ProviderVault(path, SECRET).update(
                lambda document: document["settings"].update({str(index): index})
            )

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(save, range(20)))
        assert ProviderVault(path, SECRET).read()["settings"] == {
            str(index): index for index in range(20)
        }


def test_independent_process_reads_ciphertext(tmp_path):
    path = tmp_path / "provider.enc"
    ProviderVault(path, SECRET).update(lambda data: data["settings"].update({"value": 42}))
    env = {
        **os.environ,
        "JAVO_TEST_PROVIDER_PATH": str(path),
        "JAVO_TEST_MASTER": SECRET,
        "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "services/local-runtime"),
    }
    script = "import os; from app.core.provider_store import ProviderVault; assert ProviderVault(os.environ['JAVO_TEST_PROVIDER_PATH'], os.environ['JAVO_TEST_MASTER']).read()['settings']['value']==42; print('PROCESS_VAULT_OK')"
    result = subprocess.run(
        [sys.executable, "-c", script], env=env, capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
    assert "PROCESS_VAULT_OK" in result.stdout


def test_metadata_redacts_key_and_explicit_removal_overrides_environment(configured):
    configured.gemini_api_key = "synthetic-environment-key"
    providers.update_provider(
        "gemini", {"api_key": "synthetic-saved-key", "enabled": True, "model": "configured-model"}
    )
    assert "synthetic-saved-key" not in json.dumps(providers.metadata())
    assert providers.effective()["providers"]["gemini"]["api_key"] == "synthetic-saved-key"
    providers.remove_credentials("gemini")
    cfg = providers.effective()["providers"]["gemini"]
    assert cfg["api_key"] is None and cfg["enabled"] is False


@pytest.mark.parametrize(
    "name,patch",
    [
        ("ollama", {"base_url": "http://example.com"}),
        ("openai", {"base_url": "http://example.com"}),
        ("openai", {"base_url": "https://user:pass@example.com"}),
        ("openai", {"base_url": "https://example.com?key=secret"}),
        ("gemini", {"base_url": "https://example.com"}),
        ("ollama", {"api_key": "not-a-local-setting"}),
        ("gemini", {"model": "invalid model with spaces"}),
    ],
)
def test_invalid_provider_fields_cannot_modify_vault(configured, name, patch):
    with pytest.raises(ValueError):
        providers.update_provider(name, patch)
    assert not Path(configured.provider_config_path).exists()


def test_default_model_and_zero_budget_persist(configured):
    providers.update_provider(
        "ollama", {"base_url": "http://127.0.0.1:11434", "model": "local-model:small"}
    )
    providers.update_ai_settings(
        {"default_ai_provider": "ollama", "max_tokens_per_request": 512, "ai_daily_budget": 0}
    )
    assert providers.effective()["providers"]["ollama"]["model"] == "local-model:small"
    assert providers.effective()["settings"]["max_tokens_per_request"] == 512
    before = Path(configured.provider_config_path).read_bytes()
    with pytest.raises(ValueError, match="Paid budget"):
        providers.update_ai_settings({"ai_daily_budget": 5})
    assert Path(configured.provider_config_path).read_bytes() == before


@pytest.mark.skipif(sys.platform == "win32", reason="Windows uses its OS-backed current-user key")
def test_unconfigured_non_windows_never_writes_plaintext_fallback(tmp_path):
    with pytest.raises(VaultUnavailable, match="persistent encryption"):
        ProviderVault(tmp_path / "provider.enc").update(lambda data: None)
    assert not (tmp_path / "provider.enc").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Exercises real Windows current-user DPAPI")
def test_windows_dpapi_reopen_and_missing_key_fail_closed(tmp_path):
    path = tmp_path / "provider.enc"
    vault = ProviderVault(path)
    vault.update(lambda data: data["settings"].update({"value": "protected"}))
    assert ProviderVault(path).read()["settings"]["value"] == "protected"
    wrapped = vault.key_path.read_bytes()
    assert wrapped and not wrapped.startswith(b"gAAAA")
    vault.key_path.unlink()
    with pytest.raises(VaultUnavailable):
        ProviderVault(path).read()
    assert not vault.key_path.exists()


def test_backup_key_and_provider_key_use_separate_domains(tmp_path):
    import base64
    import hashlib

    vault = ProviderVault(tmp_path / "provider.enc", SECRET)
    assert vault._key() != base64.urlsafe_b64encode(hashlib.sha256(SECRET.encode()).digest())
    assert Fernet(vault._key())
