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

## Later CI verification — 15 November 2026

At source commit 36e4a171727974c3c3c4344a1f156e26f6f07585, Windows
[run 43683631252](https://github.com/NavigatorJagdish/javo-agents/actions/runs/43683631252)
passed frozen backend/browser content flow, 17 desktop tests, packaged Electron
controls/restart/quit, NSIS and portable compilation, and NSIS install/uninstall/
reinstall with a separately retained QA profile. The app test excluded Python
from the child PATH. This supersedes earlier inability to test those paths.

The runner still has developer tooling installed, and QA profile preservation
does not prove all default-profile migrations or every clean-PC installation.
Portable wrapper execution, signing/SmartScreen, upgrade rollback and complete
feature/release acceptance remain pending. Build outputs are unsigned
development packages. This workflow does not publish or retain binaries.


Fresh-install regression: electron-builder is pinned to 26.9.0 rather than 25.1.8
to include the upstream Windows-version guard around legacy per-user path
detection (https://github.com/electron-userland/electron-builder/pull/9564).
A reproduced 0xC0000005 remains a failed check until the new installer passes.
The QA script uses `_?=` for synchronous uninstall, preserves encrypted provider
configuration and its wrapped key, and checks decryption after reinstall.

Desktop dependencies use `pnpm@11.25.0` and its frozen lockfile (Node >=22.13).
The Windows job installs this package manager explicitly: builder 26.9 detects
the pnpm lockfile and invokes pnpm while collecting packaged production modules.
Mixing an npm-only dependency install with an unavailable pnpm binary fails the
package build. Install the same pnpm version before running desktop packaging.
