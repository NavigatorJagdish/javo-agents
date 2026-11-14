"""Atomic, non-secret local pause state. Missing/corrupt state starts held."""
import json
import os
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass(frozen=True)
class ControlState:
    paused: bool = True
    emergency_stopped: bool = False


class ControlStateStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.load_error: str | None = None

    def load(self) -> ControlState:
        self.load_error = None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("version") != 1 or type(data.get("paused")) is not bool or type(data.get("emergency_stopped")) is not bool:
                raise ValueError("Invalid control state")
            if data["emergency_stopped"] and not data["paused"]:
                raise ValueError("Inconsistent control state")
            return ControlState(data["paused"], data["emergency_stopped"])
        except FileNotFoundError:
            return ControlState()
        except (OSError, ValueError, TypeError, AttributeError):
            self.load_error = "Control state unreadable; explicit resume required"
            return ControlState(paused=True, emergency_stopped=True)

    def save(self, state: ControlState) -> None:
        if state.emergency_stopped and not state.paused:
            raise ValueError("Emergency stop must remain paused")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix=self.path.name + ".", suffix=".tmp", delete=False) as handle:
                temp_path = Path(handle.name)
                json.dump({"version": 1, **asdict(state)}, handle)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
            self.load_error = None
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
