"""Hardware-derived operating limits. These are heuristics, not benchmark claims."""

from dataclasses import asdict, dataclass
from math import isfinite


@dataclass(frozen=True)
class ResourceProfile:
    name: str
    total_memory_mb: float
    cpu_count: int
    max_concurrent_agents: int
    memory_headroom_mb: int
    recommended_model_budget_mb: int
    baseline_met: bool
    basis: str = "detected hardware; workload benchmarking still required"

    def to_dict(self) -> dict:
        return asdict(self)


def select_resource_profile(
    total_memory_mb: float,
    cpu_count: int,
    requested: str = "auto",
    concurrency_override: int = 0,
    headroom_mb: int = 1536,
) -> ResourceProfile:
    if not isfinite(total_memory_mb) or total_memory_mb <= 0 or cpu_count < 1:
        raise ValueError("Hardware measurements must be positive and finite")
    if requested not in {"auto", "low", "balanced", "performance"}:
        raise ValueError("resource_profile must be auto, low, balanced or performance")
    if not 0 <= concurrency_override <= 256 or headroom_mb < 512:
        raise ValueError("Invalid concurrency or memory headroom")
    # OS-reported usable memory may be slightly below the installed RAM capacity.
    tier = "low" if total_memory_mb < 12 * 1024 else (
        "balanced" if total_memory_mb < 24 * 1024 else "performance"
    )
    chosen = tier if requested == "auto" else requested
    reserve = max(headroom_mb, int(total_memory_mb * 0.20))
    usable = max(0, int(total_memory_mb) - reserve)
    hardware_limit = max(1, min(cpu_count, usable // 4096))
    preset_limit = 1 if chosen == "low" else (4 if chosen == "balanced" else hardware_limit)
    concurrency = concurrency_override or min(hardware_limit, preset_limit)
    return ResourceProfile(
        chosen, total_memory_mb, cpu_count, concurrency, reserve,
        max(0, usable // max(1, concurrency)), total_memory_mb >= 7.5 * 1024,
    )
