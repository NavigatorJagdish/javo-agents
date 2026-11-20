"""Isolated real HTTP runtime for explicit acceptance scripts; no owner profile."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]


class AcceptanceRefused(RuntimeError):
    def __init__(self, detail, status, uninvoked=False):
        super().__init__('Isolated API refused request: '+detail)
        self.status = status
        self.uninvoked = uninvoked


def clean_environment():
    allowed = {'PATH', 'PATHEXT', 'COMSPEC', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'HOME',
               'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 'LANG'}
    return {key: value for key, value in os.environ.items() if key.upper() in allowed}


@contextmanager
def isolated_runtime():
    with tempfile.TemporaryDirectory(prefix='javo-acceptance-') as folder:
        data = Path(folder)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        base = 'http://127.0.0.1:'+str(port)
        token = secrets.token_urlsafe(32)
        env = clean_environment()
        values = {'OWNER_ACCESS_TOKEN': token, 'ENCRYPTION_KEY': secrets.token_urlsafe(48),
            'DATABASE_URL': 'sqlite+aiosqlite:///'+str(data/'runtime.db'),
            'SCHEDULER_DB_URL': 'sqlite:///'+str(data/'scheduler.db'),
            'PROVIDER_CONFIG_PATH': str(data/'providers.enc'), 'CONTROL_STATE_PATH': str(data/'control.json'),
            'USAGE_LEDGER_PATH': str(data/'usage.sqlite'), 'ACCOUNT_CREDENTIALS_DIR': str(data/'accounts')}
        values.update({key: str(data/key.lower()) for key in ['CONTENT_ROOT', 'UPLOAD_DIR', 'BACKUP_DIR', 'THUMBNAIL_DIR']})
        env.update({'JAVO_'+key: value for key, value in values.items()})
        runtime_exe = os.environ.get('JAVO_RUNTIME_EXE')
        command = [str(Path(runtime_exe).resolve()), '--port', str(port)] if runtime_exe else [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', str(port)]
        opener = build_opener(ProxyHandler({}))
        def request(route, body=None, method=None, raw=False, content_type='application/json'):
            payload = body if isinstance(body, bytes) else None if body is None else json.dumps(body).encode()
            message = Request(base+route, data=payload, method=method or ('GET' if body is None else 'POST'),
                headers={'Authorization': 'Bearer '+token, 'Content-Type': content_type})
            try:
                response = opener.open(message, timeout=100)
            except HTTPError as error:
                detail = json.loads(error.read(32768)).get('detail')
                raise AcceptanceRefused(detail if isinstance(detail, str) else str(error.code), error.code,
                    error.code == 503 and error.headers.get('X-Javo-Admission') == 'not-started') from None
            with response:
                content = response.read(64*1024*1024+1)
                if len(content) > 64*1024*1024:
                    raise ValueError('Acceptance response exceeded its bound')
                return content if raw else json.loads(content)
        with (data/'runtime.log').open('w', encoding='utf-8') as log:
            process = subprocess.Popen(command, cwd=ROOT/'services/local-runtime', env=env, stdout=log, stderr=log)
            try:
                deadline = time.monotonic()+60
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError('Isolated runtime exited during startup')
                    try:
                        with opener.open(base+'/auth/status', timeout=1) as response:
                            if json.load(response).get('configured'):
                                break
                    except Exception:
                        time.sleep(0.1)
                else:
                    raise TimeoutError('Isolated runtime startup deadline exceeded')
                yield base, request
            except BaseException:
                print((data/'runtime.log').read_text(encoding='utf-8', errors='replace')[-7000:].replace(token, '[redacted disposable owner token]'), file=sys.stderr)
                raise
            finally:
                if process.poll() is None:
                    if sys.platform == 'win32':
                        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=False)
                    else:
                        process.terminate()
                    process.wait(timeout=15)
