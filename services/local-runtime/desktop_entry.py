"""Entry point for the bundled desktop backend (no external Python required)."""
from __future__ import annotations

import argparse
import json
import multiprocessing
import os


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")

    if args.self_test:
        # Exercise dynamic imports used by the frozen build without opening a
        # socket, creating data, starting agents, or exposing configuration.
        from app.main import app
        from app.agents import get_all_agents
        from sqlalchemy.dialects.sqlite import aiosqlite, pysqlite  # noqa: F401
        import uvicorn

        print(json.dumps({"result": "RUNTIME_IMPORTS_OK", "version": app.version,
                          "agents": len(get_all_agents())}))
        return

    if len(os.environ.get("JAVO_OWNER_ACCESS_TOKEN", "")) < 32:
        parser.error("desktop owner authorization is required")

    import uvicorn

    # Explicit implementations avoid optional auto-detection imports and
    # multiple-worker spawning inside a frozen executable.
    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port,
                loop="asyncio", http="h11", ws="websockets", workers=1)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
