"""Security module: encryption, credential storage, token management, auth middleware."""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)


class CredentialStore:
    """Encrypted credential storage using Fernet symmetric encryption."""

    def __init__(self, encryption_key: Optional[str] = None):
        if encryption_key:
            key = base64.urlsafe_b64encode(
                hashlib.sha256(encryption_key.encode()).digest()
            )
        else:
            key = Fernet.generate_key()
        self._fernet = Fernet(key)
        self._store: dict[str, bytes] = {}

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string."""
        return self._fernet.decrypt(ciphertext.encode()).decode()

    def store_credential(self, key: str, value: str) -> None:
        """Store an encrypted credential."""
        self._store[key] = self._fernet.encrypt(value.encode())
        logger.info(f"Credential stored: {key}")

    def retrieve_credential(self, key: str) -> Optional[str]:
        """Retrieve and decrypt a credential."""
        encrypted = self._store.get(key)
        if encrypted is None:
            return None
        return self._fernet.decrypt(encrypted).decode()

    def delete_credential(self, key: str) -> bool:
        """Delete a stored credential."""
        if key in self._store:
            del self._store[key]
            logger.info(f"Credential deleted: {key}")
            return True
        return False

    def list_keys(self) -> list[str]:
        """List all stored credential keys."""
        return list(self._store.keys())


class TokenManager:
    """JWT-like token management using HMAC-SHA256."""

    def __init__(self, secret_key: str, expiry_hours: int = 24):
        self._secret = secret_key.encode()
        self._expiry_hours = expiry_hours
        self._active_tokens: dict[str, dict] = {}

    def generate_token(self, user_id: str, device_id: Optional[str] = None) -> str:
        """Generate a new access token."""
        token_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self._expiry_hours)

        payload = {
            "token_id": token_id,
            "user_id": user_id,
            "device_id": device_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        # Create HMAC signature
        message = f"{token_id}:{user_id}:{expires_at.isoformat()}"
        signature = hmac.new(self._secret, message.encode(), hashlib.sha256).hexdigest()
        token = f"{token_id}.{signature}"

        self._active_tokens[token_id] = payload
        logger.info(f"Token generated for user {user_id}")
        return token

    def validate_token(self, token: str) -> Optional[dict]:
        """Validate a token and return its payload."""
        try:
            token_id, signature = token.split(".", 1)
        except ValueError:
            return None

        payload = self._active_tokens.get(token_id)
        if payload is None:
            return None

        # Check expiry
        expires_at = datetime.fromisoformat(payload["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            self.revoke_token(token_id)
            return None

        # Verify signature
        message = f"{token_id}:{payload['user_id']}:{payload['expires_at']}"
        expected = hmac.new(self._secret, message.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None

        return payload

    def revoke_token(self, token_id: str) -> bool:
        """Revoke an active token."""
        if token_id in self._active_tokens:
            del self._active_tokens[token_id]
            logger.info(f"Token revoked: {token_id}")
            return True
        return False

    def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user."""
        to_revoke = [
            tid for tid, p in self._active_tokens.items() if p["user_id"] == user_id
        ]
        for tid in to_revoke:
            del self._active_tokens[tid]
        logger.info(f"Revoked {len(to_revoke)} tokens for user {user_id}")
        return len(to_revoke)

    def get_active_sessions(self, user_id: str) -> list[dict]:
        """Get all active sessions for a user."""
        return [
            p for p in self._active_tokens.values() if p["user_id"] == user_id
        ]


# Singletons
_credential_store: Optional[CredentialStore] = None
_token_manager: Optional[TokenManager] = None


def get_credential_store() -> CredentialStore:
    """Get or create the credential store singleton."""
    global _credential_store
    if _credential_store is None:
        settings = get_settings()
        _credential_store = CredentialStore(settings.encryption_key)
    return _credential_store


def get_token_manager() -> TokenManager:
    """Get or create the token manager singleton."""
    global _token_manager
    if _token_manager is None:
        settings = get_settings()
        _token_manager = TokenManager(settings.secret_key, settings.token_expiry_hours)
    return _token_manager


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[dict]:
    """Auth middleware dependency - extracts and validates the current user.
    
    Returns None if no auth provided (for endpoints that allow anonymous access).
    Raises 401 if token is invalid.
    """
    if credentials is None:
        return None

    token_mgr = get_token_manager()
    payload = token_mgr.validate_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_auth(user: Optional[dict] = Depends(get_current_user)) -> dict:
    """Dependency that requires authentication."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def hash_password(password: str) -> str:
    """Hash a password with a random salt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, hashed = password_hash.split(":", 1)
        expected = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(expected.hex(), hashed)
    except (ValueError, AttributeError):
        return False
