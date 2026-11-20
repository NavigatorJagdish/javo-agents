"""OS-backed exclusive lease for one dispatcher per persisted runtime database."""

from pathlib import Path
import sys


class RuntimeLease:
    def __init__(self, path):
        self.path = Path(path)
        self._handle = None

    def acquire(self):
        if self._handle is not None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        try:
            if handle.seek(0, 2) == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise RuntimeError("Another dispatcher owns this runtime database") from None
        self._handle = handle

    def release(self):
        if self._handle is not None:
            self._handle.close()  # OS releases the lock, including after a crash.
            self._handle = None
