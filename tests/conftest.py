"""Pytest configuration ensuring services/local-runtime is on sys.path."""

import sys
import secrets
from pathlib import Path
import pytest

RUNTIME_DIR = Path(__file__).resolve().parent.parent / "services" / "local-runtime"
if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))


@pytest.fixture
def owner_runtime(tmp_path, monkeypatch):
    """Isolated real app/database; synthetic capacity is not a host benchmark."""
    import app.config as cfg
    import app.core.resource_manager as resources
    from app.main import create_app
    from fastapi.testclient import TestClient
    token = secrets.token_urlsafe(32)
    values = {
        'OWNER_ACCESS_TOKEN': token,
        'DATABASE_URL': f"sqlite+aiosqlite:///{tmp_path / 'runtime.db'}",
        'SCHEDULER_DB_URL': f"sqlite:///{tmp_path / 'schedule.db'}",
        'CONTROL_STATE_PATH': str(tmp_path/'control.json'),
        'PROVIDER_CONFIG_PATH': str(tmp_path/'providers.enc'),
        'USAGE_LEDGER_PATH': str(tmp_path/'usage.sqlite'),
        'ACCOUNT_CREDENTIALS_DIR': str(tmp_path/'account-credentials'),
        'ENCRYPTION_KEY': secrets.token_urlsafe(48),
    }
    for key in ('CONTENT_ROOT', 'UPLOAD_DIR', 'BACKUP_DIR', 'THUMBNAIL_DIR'):
        values[key] = str(tmp_path/key.lower())
    for key, value in values.items():
        monkeypatch.setenv('JAVO_'+key, value)
    monkeypatch.setattr(resources.ResourceManager, 'get_metrics', lambda self: resources.SystemMetrics(
        0, 25, 8192, 16384, 10, 100, len(self._active_tasks), 0))

    def client():
        cfg._settings = None
        resources._resource_manager = None
        return TestClient(create_app(), headers={'Authorization': f'Bearer {token}'})

    yield client, tmp_path/'runtime.db'
    cfg._settings = None
    resources._resource_manager = None
