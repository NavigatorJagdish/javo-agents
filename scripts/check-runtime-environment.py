"""Bounded, app-independent asyncio startup diagnostic. No external requests."""
import subprocess
import sys

probe = "import faulthandler; faulthandler.dump_traceback_later(5); import asyncio; asyncio.run(asyncio.sleep(0)); faulthandler.cancel_dump_traceback_later(); print('ASYNCIO_OK')"
try:
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=10)
except subprocess.TimeoutExpired as exc:
    print("ENVIRONMENT_BLOCKED: minimal asyncio startup exceeded 10 seconds, before importing Javo.")
    output = exc.stderr or b""
    print(output.decode(errors="replace") if isinstance(output, bytes) else output)
    sys.exit(2)
print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)
