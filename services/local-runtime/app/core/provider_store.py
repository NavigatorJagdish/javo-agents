"""Authenticated provider configuration at rest, protected by an OS/user key."""

from __future__ import annotations

import base64
from contextlib import contextmanager
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

from cryptography.fernet import Fernet


class VaultUnavailable(RuntimeError):
    pass


def _dpapi(data: bytes, *, decrypt: bool = False) -> bytes:
    """Windows current-user protection. Never use LOCAL_MACHINE scope or UI."""
    if sys.platform != "win32":
        raise VaultUnavailable("Windows user protection is unavailable")
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    source = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    blob, output = Blob(len(data), source), Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [
        ctypes.POINTER(Blob),
        ctypes.c_void_p,
        ctypes.POINTER(Blob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(Blob),
    ]
    function.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not function(ctypes.byref(blob), None, None, None, None, 1, ctypes.byref(output)):
        raise VaultUnavailable("Windows user key protection failed")
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        kernel.LocalFree(output.data)


class ProviderVault:
    """One encrypted document; atomic writes and a cross-process mutation lock."""

    def __init__(self, path: str | Path, encryption_secret: str | None = None):
        self.path = Path(path)
        self.secret = encryption_secret
        self.key_path = self.path.with_suffix(".key.dpapi")

    @property
    def protection(self) -> str:
        if self.secret and len(self.secret) >= 32:
            return "configured-key"
        return "windows-user" if sys.platform == "win32" else "unavailable"

    def _key(self) -> bytes:
        if self.secret and len(self.secret) >= 32:
            digest = hashlib.sha256(b"javo-provider-v1\0" + self.secret.encode()).digest()
            return base64.urlsafe_b64encode(digest)
        if sys.platform != "win32":
            raise VaultUnavailable(
                "Configure a persistent encryption key to save provider settings"
            )
        if not self.key_path.exists():
            # Never silently create a replacement key for existing encrypted data.
            if self.path.exists():
                raise VaultUnavailable(
                    "Provider user key is missing; recover the original profile/key"
                )
            protected = _dpapi(Fernet.generate_key())
            try:
                fd = os.open(self.key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as handle:
                    handle.write(protected)
                    handle.flush()
                    os.fsync(handle.fileno())
            except FileExistsError:
                pass
        if self.key_path.is_symlink() or self.key_path.stat().st_size > 8192:
            raise VaultUnavailable("Provider user key cannot be read")
        return _dpapi(self.key_path.read_bytes(), decrypt=True)

    def read(self) -> dict:
        if not self.path.exists():
            return {"version": 1, "providers": {}, "settings": {}}
        try:
            if self.path.is_symlink() or self.path.stat().st_size > 1024 * 1024:
                raise ValueError("Invalid vault file")
            value = json.loads(Fernet(self._key()).decrypt(self.path.read_bytes()))
            if (
                value.get("version") != 1
                or not isinstance(value.get("providers"), dict)
                or not isinstance(value.get("settings"), dict)
            ):
                raise ValueError("Invalid vault schema")
            return value
        except Exception:
            raise VaultUnavailable(
                "Provider storage is locked or damaged; recover the original key and data"
            ) from None

    @contextmanager
    def _lock(self):
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        if lock_path.is_symlink():
            raise VaultUnavailable("Provider storage lock is unsafe")
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        with os.fdopen(fd, "r+b") as handle:
            if os.fstat(handle.fileno()).st_size == 0:
                handle.write(b"0")
                handle.flush()
            deadline = time.monotonic() + 5
            while True:
                try:
                    handle.seek(0)
                    if sys.platform == "win32":
                        import msvcrt

                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise VaultUnavailable(
                            "Provider settings are busy; retry after the current save"
                        ) from None
                    time.sleep(0.05)
            try:
                yield
            finally:
                handle.seek(0)
                if sys.platform == "win32":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def update(self, mutate) -> dict:
        temporary = None
        try:
            with self._lock():
                value = self.read()
                mutate(value)
                raw = json.dumps(value, allow_nan=False, separators=(",", ":")).encode()
                if len(raw) > 65536:
                    raise VaultUnavailable("Provider configuration exceeds its storage limit")
                encrypted = Fernet(self._key()).encrypt(raw)
                fd, temporary = tempfile.mkstemp(
                    prefix=self.path.name + ".", suffix=".tmp", dir=self.path.parent
                )
                with os.fdopen(fd, "wb") as handle:
                    handle.write(encrypted)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, self.path)
                temporary = None
                return value
        except VaultUnavailable:
            raise
        except Exception:
            raise VaultUnavailable(
                "Provider settings could not be saved; existing data was preserved"
            ) from None
        finally:
            if temporary:
                Path(temporary).unlink(missing_ok=True)
