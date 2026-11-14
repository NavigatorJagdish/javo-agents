# Windows packaging status and build procedure

The desktop release must include its own Python backend. A copy of Python
source is insufficient on a clean PC. The package now expects a PyInstaller
one-directory bundle under `apps/windows/build/runtime/javo-runtime/` and
launches its `javo-runtime.exe` directly. Development still uses Python.
Packaged mode does not fall back to a machine-wide Python installation.

Use a clean Windows x64 build environment with Python 3.11 and Node.js:

```powershell
python -m venv .venv-packaging
.\.venv-packaging\Scripts\python -m pip install -r services/local-runtime/requirements.txt "apscheduler<4" "pyinstaller>=6.11,<7"
.\.venv-packaging\Scripts\python scripts/build-desktop-runtime.py
```

The script bundles runtime dependencies, runs a bounded import/agent-registry
self-test from a temporary writable folder and writes a SHA256 manifest only
after that check passes. This check does not prove HTTP startup or user flows.
Model weights, FFmpeg and optional local AI services are separate installations.
Dependency ranges are not a reproducible release lock; retain the actual build
environment inventory and establish locked dependencies before release.

Build the dashboard and shell with their installed dependencies, and generate
the existing brand icons with `python packages/brand-assets/icons/generate_icons.py`
(requires Pillow; these are the existing assets, not a new reference-fidelity claim). Then:

```powershell
cd apps/windows
npm run typecheck
npm run test
npm run dist:win
```

`verify:package` and the electron-builder `beforePack` hook reject missing
dashboard/icon/runtime payloads, missing Python DLLs, failed self-test markers
and checksum mismatches. These are build-integrity checks, not code signing or
proof that an executable is trustworthy. Publishing is disabled in this build.
The manifest also binds the bundle to the backend Python source and dependency
declarations. Added, removed or edited backend source requires a new bundle.
Extra files absent from the payload manifest are rejected before packaging.

Release acceptance still requires a clean Windows VM without Python: install,
authenticated healthy backend, import/review/approve/simulate/receipt flow,
tray pause/stop, quit with no orphan runtime, restart with stop state restored,
uninstall/reinstall preserving owner data, and signing/update verification.
Use isolated test data. Installer existence alone does not pass these checks.

Current environment cannot complete the frozen build: PyInstaller is unavailable
from its configured package index, Electron binary download previously failed
DNS, and the minimal asyncio diagnostic currently hangs before app import.
No tested installer is claimed.
