"""Security module: encryption, credential storage, token management, auth middleware."""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
from pathlib import Path
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

    def generate_token(
        self,
        user_id: str,
        device_id: Optional[str] = None,
        role: str = "owner",
    ) -> str:
        """Generate a new access token."""
        token_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self._expiry_hours)

        payload = {
            "token_id": token_id,
            "user_id": user_id,
            "device_id": device_id,
            "role": role,
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


# ---------------------------------------------------------------------------
# OS-Backed Credential Storage & Windows DPAPI
# ---------------------------------------------------------------------------
def _get_credential_dir() -> Path:
    """Return platform-appropriate secure credential directory."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
        cred_dir = Path(base) / "JavoAgents" / "credentials"
    else:
        cred_dir = Path.home() / ".javo" / "credentials"
    cred_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(cred_dir, 0o700)
    except Exception:
        pass
    return cred_dir


def _dpapi_protect(plaintext: bytes) -> bytes:
    """Encrypt data using Windows DPAPI (CryptProtectData via ctypes)."""
    if os.name != "nt":
        return plaintext
    try:
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char)),
            ]

        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32

        in_blob = DATA_BLOB(
            len(plaintext),
            ctypes.cast(ctypes.c_char_p(plaintext), ctypes.POINTER(ctypes.c_char)),
        )
        out_blob = DATA_BLOB()
        if not crypt32.CryptProtectData(
            ctypes.byref(in_blob),
            "javo_credential",
            None,
            None,
            None,
            0,
            ctypes.byref(out_blob),
        ):
            return plaintext
        protected = ctypes.string_at(out_blob.pbData, out_blob.cbData)
        kernel32.LocalFree(out_blob.pbData)
        return protected
    except Exception as exc:
        logger.debug(f"DPAPI protect fallback: {exc}")
        return plaintext


def _dpapi_unprotect(ciphertext: bytes) -> bytes:
    """Decrypt data using Windows DPAPI (CryptUnprotectData via ctypes)."""
    if os.name != "nt":
        return ciphertext
    try:
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char)),
            ]

        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32

        in_blob = DATA_BLOB(
            len(ciphertext),
            ctypes.cast(ctypes.c_char_p(ciphertext), ctypes.POINTER(ctypes.c_char)),
        )
        out_blob = DATA_BLOB()
        if not crypt32.CryptUnprotectData(
            ctypes.byref(in_blob),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(out_blob),
        ):
            return ciphertext
        unprotected = ctypes.string_at(out_blob.pbData, out_blob.cbData)
        kernel32.LocalFree(out_blob.pbData)
        return unprotected
    except Exception as exc:
        logger.debug(f"DPAPI unprotect fallback: {exc}")
        return ciphertext


def _load_durable_secret(name: str) -> Optional[str]:
    """Load a persistent secret from DPAPI-encrypted or permission-restricted storage."""
    cred_dir = _get_credential_dir()
    dpapi_file = cred_dir / f"{name}.dpapi"
    raw_file = cred_dir / f"{name}.key"

    if dpapi_file.exists():
        try:
            raw_bytes = dpapi_file.read_bytes()
            decrypted = _dpapi_unprotect(raw_bytes).decode("utf-8").strip()
            if decrypted:
                return decrypted
        except Exception as exc:
            logger.warning(f"Failed to read DPAPI secret {name}: {exc}")

    if raw_file.exists():
        try:
            val = raw_file.read_text(encoding="utf-8").strip()
            if val:
                return val
        except Exception as exc:
            logger.warning(f"Failed to read raw secret {name}: {exc}")

    return None


def _save_durable_secret(name: str, secret: str) -> None:
    """Save a persistent secret using Windows DPAPI or 0o600 restricted file storage."""
    cred_dir = _get_credential_dir()
    val_bytes = secret.strip().encode("utf-8")

    if os.name == "nt":
        dpapi_file = cred_dir / f"{name}.dpapi"
        protected = _dpapi_protect(val_bytes)
        dpapi_file.write_bytes(protected)
    else:
        raw_file = cred_dir / f"{name}.key"
        raw_file.write_text(secret.strip(), encoding="utf-8")
        try:
            os.chmod(raw_file, 0o600)
        except Exception:
            pass


_cached_owner_token: Optional[str] = None
_cached_app_secret: Optional[str] = None


def get_durable_app_secret() -> str:
    """Return or provision a durable 256-bit per-installation application secret key."""
    global _cached_app_secret
    if _cached_app_secret is not None:
        return _cached_app_secret

    persisted = _load_durable_secret("app_secret")
    if persisted:
        _cached_app_secret = persisted
        return _cached_app_secret

    new_secret = secrets.token_urlsafe(32)
    try:
        _save_durable_secret("app_secret", new_secret)
    except Exception as exc:
        logger.warning(f"Could not persist application secret: {exc}")

    _cached_app_secret = new_secret
    return _cached_app_secret


def get_owner_token() -> str:
    """Return configured owner token or load/provision a persistent OS-backed owner secret."""
    global _cached_owner_token
    settings = get_settings()
    if settings.owner_token:
        return settings.owner_token

    if _cached_owner_token is not None:
        return _cached_owner_token

    persisted = _load_durable_secret("owner_token")
    if persisted:
        _cached_owner_token = persisted
        return _cached_owner_token

    new_token = secrets.token_urlsafe(32)
    try:
        _save_durable_secret("owner_token", new_token)
    except Exception as exc:
        logger.warning(f"Could not persist owner token: {exc}")

    _cached_owner_token = new_token
    return _cached_owner_token


def validate_auth_token(token: str) -> Optional[dict]:
    """Validate either a TokenManager HMAC token or the local owner secret token."""
    if not token:
        return None
    owner_tok = get_owner_token()
    if hmac.compare_digest(token, owner_tok):
        return {"user_id": "owner", "role": "owner", "is_owner": True}
    token_mgr = get_token_manager()
    return token_mgr.validate_token(token)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[dict]:
    """Auth middleware dependency - extracts and validates the current user.

    Supports Bearer token, X-API-Key, or X-Owner-Token headers.
    Returns None if no auth provided (for endpoints that allow anonymous access).
    Raises 401 if supplied credentials are invalid.
    """
    raw_token: Optional[str] = None
    if credentials is not None:
        raw_token = credentials.credentials
    elif request.headers.get("X-API-Key"):
        raw_token = request.headers.get("X-API-Key")
    elif request.headers.get("X-Owner-Token"):
        raw_token = request.headers.get("X-Owner-Token")

    if raw_token is None:
        return None

    payload = validate_auth_token(raw_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_auth(user: Optional[dict] = Depends(get_current_user)) -> dict:
    """Dependency that requires an authenticated user."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_owner(user: dict = Depends(require_auth)) -> dict:
    """Dependency that requires authenticated owner/admin privileges."""
    role = str(user.get("role", "")).lower()
    if not user.get("is_owner") and role not in {"owner", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner privileges required",
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
