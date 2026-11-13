"""Repeatable 8GB RAM & local-runtime capability benchmark for Javo Agents."""

from __future__ import annotations

import asyncio
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = REPO_ROOT / "services" / "local-runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def _total_ram_gb() -> float:
    if sys.platform == "win32":
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return round(stat.ullTotalPhys / (1024**3), 2)
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return round((pages * page_size) / (1024**3), 2)
    except Exception:
        return 0.0


async def run_benchmark() -> dict:
    from app.agents import create_orchestrator, get_all_agents
    from app.core.ai_router import get_ai_router

    t0 = time.monotonic()
    agents = get_all_agents()
    orchestrator = create_orchestrator()
    orch_t0 = time.monotonic()
    sample_res = await orchestrator.run(
        {"task_type": "content_pipeline", "goal": "Draft 1 zero-cost Instagram tip", "topic": "local AI", "granted_permissions": ["content:draft", "analytics:read"]},
    )
    orch_ms = round((time.monotonic() - orch_t0) * 1000, 2)

    ram_gb = _total_ram_gb()
    free_disk_gb = round(shutil.disk_usage(REPO_ROOT).free / (1024**3), 2)
    recommended_mode = (
        "8gb_cpu_optimized" if ram_gb < 12 else ("16gb_hybrid" if ram_gb < 24 else "32gb_workstation")
    )

    router = get_ai_router()
    report = {
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "cpu_cores": os.cpu_count() or 1,
        "total_ram_gb": ram_gb,
        "free_disk_gb": free_disk_gb,
        "recommended_mode": recommended_mode,
        "recommended_ollama_model": "qwen2.5:3b" if ram_gb < 12 else "llama3.1:8b",
        "ollama_cli_found": shutil.which("ollama") is not None,
        "ffmpeg_cli_found": shutil.which("ffmpeg") is not None,
        "registered_agents": len(agents),
        "orchestrator_smoke_ms": orch_ms,
        "orchestrator_status": sample_res.get("status"),
        "orchestrator_detail": sample_res.get("error"),
        "ai_provider_count": len(router.get_provider_status()),
        "total_benchmark_ms": round((time.monotonic() - t0) * 1000, 2),
        "default_budget_usd": 0.0,
    }
    return report


if __name__ == "__main__":
    data = asyncio.run(run_benchmark())
    print(json.dumps(data, indent=2))
