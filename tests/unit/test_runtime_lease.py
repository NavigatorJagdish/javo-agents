import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.core.runtime_lease import RuntimeLease


def test_second_dispatcher_cannot_acquire_same_database_lease(tmp_path):
    path = tmp_path / "runtime.agent-worker.lock"
    first = RuntimeLease(path)
    second = RuntimeLease(path)
    first.acquire()
    try:
        with pytest.raises(RuntimeError, match="Another dispatcher"):
            second.acquire()
    finally:
        first.release()
    second.acquire()
    second.release()


def test_os_releases_lease_when_process_exits(tmp_path):
    path = tmp_path / "runtime.agent-worker.lock"
    env = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "services/local-runtime"),
        "JAVO_TEST_LEASE": str(path),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os; from app.core.runtime_lease import RuntimeLease; lock=RuntimeLease(os.environ['JAVO_TEST_LEASE']); lock.acquire(); os._exit(0)",
        ],
        env=env,
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0
    reopened = RuntimeLease(path)
    reopened.acquire()
    reopened.release()
