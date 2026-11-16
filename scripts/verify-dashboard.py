"""Start an isolated real runtime and exercise the built dashboard in Chrome."""
from contextlib import contextmanager
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import threading
import urllib.request

repo = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--scenario', choices=['dashboard', 'goals', 'usage', 'agents', 'accounts'], default='dashboard')
args = parser.parse_args()


@contextmanager
def fixture_provider():
    """Synthetic model responses behind the real router; never contact a cloud API."""
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            if self.path != "/api/chat" or not 0 < length < 65536:
                self.send_error(400)
                return
            payload = json.loads(self.rfile.read(length))
            conversation = json.loads(payload["messages"][-1]["content"])
            reply = {"message": {"content": "Fixture assistant reply; previous turns: " + str(len(conversation["previous_turns"]))},
                     "prompt_eval_count": 10, "eval_count": 10}
            encoded = json.dumps(reply).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, *_):
            pass  # Never log conversation text or headers.

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join(timeout=5)


with fixture_provider() as endpoint, tempfile.TemporaryDirectory(prefix="javo-ui-") as folder:
    data = Path(folder)
    incoming = data / "incoming"
    incoming.mkdir()
    (incoming / "sample.txt").write_text("Original browser test media", encoding="utf-8")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(repo / "services/local-runtime"),
        "JAVO_OWNER_ACCESS_TOKEN": secrets.token_urlsafe(32),
        "JAVO_DASHBOARD_DIST": str(repo / "apps/dashboard/dist"),
        "JAVO_CONTROL_STATE_PATH": str(data / "control.json"),
        "JAVO_PROVIDER_CONFIG_PATH": str(data / "providers.enc"),
        "JAVO_USAGE_LEDGER_PATH": str(data / "usage.sqlite"),
        "JAVO_ACCOUNT_CREDENTIALS_DIR": str(data / 'account-credentials'),
        "JAVO_ENCRYPTION_KEY": secrets.token_urlsafe(48),
        "JAVO_OLLAMA_BASE_URL": endpoint,
        "JAVO_DATABASE_URL": "sqlite+aiosqlite:///" + str(data / "runtime.db"),
        "JAVO_SCHEDULER_DB_URL": "sqlite:///" + str(data / "scheduler.db"),
        "JAVO_SMOKE_CONTENT": str(incoming),
        "JAVO_SMOKE_URL": f"http://127.0.0.1:{port}/dashboard/?apiBase=http://127.0.0.1:{port}",
    })
    for key in ["CONTENT_ROOT", "UPLOAD_DIR", "BACKUP_DIR", "THUMBNAIL_DIR"]:
        env["JAVO_" + key] = str(data / key.lower())
    if args.scenario == 'accounts':
        # Seed only synthetic old-version rows before startup. The real source
        # or frozen runtime must protect them; no migration is mocked here.
        seed = '''
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import Base
import app.models  # Register the real schema before creating synthetic rows.
from app.models.account import SocialAccount, Platform, AccountStatus
from app.models.user import User, UserRole
import os
engine = create_engine(os.environ['JAVO_DATABASE_URL'].replace('sqlite+aiosqlite:', 'sqlite:'))
Base.metadata.create_all(engine)
with Session(engine) as session:
    session.add(User(id='default-user', username='synthetic-ui-owner', email='synthetic@localhost.invalid', password_hash='!disabled', role=UserRole.ADMIN))
    session.add(SocialAccount(id='synthetic-legacy-account', user_id='default-user', platform=Platform.YOUTUBE, username='@synthetic-legacy', display_name='Synthetic legacy migration', access_token='synthetic-ui-legacy-access', refresh_token='synthetic-ui-legacy-refresh', status=AccountStatus.CONNECTED, metadata_={'credentials': {'token': 'synthetic-ui-metadata-secret'}}))
    session.commit()
engine.dispose()
'''
        subprocess.run([sys.executable, '-c', seed], cwd=data, env=env, check=True, timeout=20)
    if args.scenario == 'usage':
        # This UI scenario checks persisted counters with labelled synthetic
        # records. Router/transport accounting is tested independently.
        sys.path.insert(0, str(repo / 'services/local-runtime'))
        from app.core.usage_ledger import UsageLedger
        from uuid import uuid4
        ledger = UsageLedger(data / 'usage.sqlite')
        request_id = str(uuid4())
        ledger.reserve(request_id, 'ollama', 'synthetic-ui-fixture')
        ledger.settle(request_id, prompt_tokens=3, completion_tokens=5, cost_microusd=0)
    with (data / "runtime.log").open("w", encoding="utf-8") as log:
        bundled = os.environ.get("JAVO_RUNTIME_EXE")
        module = 'app.main:app'
        if args.scenario in ('agents', 'dashboard') and not bundled:
            # Synthetic model/read operations exercise the real worker with
            # fixture capacity, independently of other apps using the host RAM.
            # This does not benchmark a real model or change production limits.
            (data / 'scenario_runtime.py').write_text(
                'from app.core.resource_manager import ResourceManager, SystemMetrics\n'
                'ResourceManager.get_metrics = lambda self: SystemMetrics(0,25,8192,16384,10,100,len(self._active_tasks),0)\n'
                'from app.main import app\n', encoding='utf-8')
            env['PYTHONPATH'] += os.pathsep + str(data)
            module = 'scenario_runtime:app'
        command = ([str(Path(bundled).resolve()), "--port", str(port)] if bundled else
                   [sys.executable, "-m", "uvicorn", module, "--host", "127.0.0.1", "--port", str(port)])
        backend = subprocess.Popen(command, cwd=data, env=env, stdout=log, stderr=log)
        failed = True
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/auth/status", timeout=1):
                        break
                except OSError:
                    if backend.poll() is not None:
                        raise RuntimeError("Temporary backend failed to start")
                    time.sleep(0.25)
            else:
                raise TimeoutError("Temporary backend readiness timed out")
            scenario = {'goals': 'goals-smoke.cjs', 'usage': 'usage-smoke.cjs', 'agents': 'agents-smoke.cjs', 'accounts': 'accounts-smoke.cjs', 'dashboard': 'dashboard-smoke.cjs'}[args.scenario]
            result = subprocess.run(["node", str(repo / 'scripts' / scenario)], env=env, timeout=120)
            if result.returncode:
                sys.exit(result.returncode)
            failed = False
        finally:
            if backend.poll() is None:
                if os.name == 'nt':
                    # A venv Python launcher can own the real interpreter as a
                    # child. Terminating only the launcher leaks the HTTP server
                    # and its SQLite handles on Windows. This exact PID belongs
                    # to the temporary process created by this harness.
                    stopped = subprocess.run(['taskkill', '/PID', str(backend.pid), '/T', '/F'],
                                             capture_output=True, text=True, timeout=15)
                    if stopped.returncode and backend.poll() is None:
                        raise RuntimeError('Could not stop the isolated runtime process tree')
                else:
                    backend.terminate()
            try:
                backend.wait(timeout=10)
            except subprocess.TimeoutExpired:
                backend.kill()
                backend.wait()
            if failed:
                log.flush()
                tail = (data / "runtime.log").read_text(encoding="utf-8", errors="replace")[-6000:]
                for key, value in env.items():
                    if any(marker in key.upper() for marker in ("TOKEN", "KEY", "SECRET")) and len(value) > 8:
                        tail = tail.replace(value, "[REDACTED]")
                print("ISOLATED_RUNTIME_FAILURE_LOG:\n" + tail, file=sys.stderr)
