"""Unit tests for CredentialStore, TokenManager, password hashing, and PrivacyFirewall."""

from __future__ import annotations

from app.core.privacy_firewall import DataClassification, PrivacyFirewall
from app.core.security import CredentialStore, TokenManager, hash_password, verify_password


def test_credential_store_encryption_roundtrip():
    store = CredentialStore("super-secret-master-key")
    store.store_credential("ig_token", "EAAG-test-token-12345")
    assert store.retrieve_credential("ig_token") == "EAAG-test-token-12345"
    assert "ig_token" in store.list_keys()
    assert store.delete_credential("ig_token") is True
    assert store.retrieve_credential("ig_token") is None


def test_token_manager_and_password_hashing():
    mgr = TokenManager(secret_key="jwt-hmac-secret", expiry_hours=1)
    token = mgr.generate_token("user-42", device_id="dev-1")
    payload = mgr.validate_token(token)
    assert payload is not None
    assert payload["user_id"] == "user-42"

    # Tampered token must fail
    assert mgr.validate_token(token + "tamper") is None

    # Revoke all user tokens
    revoked = mgr.revoke_user_tokens("user-42")
    assert revoked == 1
    assert mgr.validate_token(token) is None

    pw_hash = hash_password("MyStrongPass!99")
    assert verify_password("MyStrongPass!99", pw_hash) is True
    assert verify_password("wrong", pw_hash) is False


def test_privacy_firewall_blocks_secrets_and_redacts_pii():
    fw = PrivacyFirewall()

    sample_key = "sk-" + "1234567890abcdefghijklmno"
    # API key must be blocked from cloud providers
    secret_decision = fw.evaluate_egress(f"Here is my key {sample_key}", provider="gemini")
    assert secret_decision.allowed is False

    # Same data is permitted locally on ollama
    local_decision = fw.evaluate_egress(f"Here is my key {sample_key}", provider="ollama")
    assert local_decision.allowed is True

    # PII gets flagged for redaction on cloud providers
    pii_decision = fw.evaluate_egress(
        "Contact alice@example.com for details",
        provider="openai",
        classification=DataClassification.INTERNAL,
    )
    assert pii_decision.allowed is True
    assert pii_decision.should_redact is True
    assert "[REDACTED_EMAIL]" in fw.redact_pii("Contact alice@example.com for details")
