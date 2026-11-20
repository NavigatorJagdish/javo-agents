"""Reject known incompatible speech payloads; preserve the project's own license."""
from __future__ import annotations

import argparse
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path)
    args = parser.parse_args()
    license_text = (ROOT/'LICENSE').read_text(encoding='utf-8')
    if not license_text.startswith('MIT License') or 'Copyright (c) 2026 Javo Agents Contributors' not in license_text:
        raise ValueError('The project license changed; review the owner requirement before distribution')
    if version('sherpa-onnx') != '2.0.1' or version('sherpa-onnx-core') != '2.0.1':
        raise ValueError('Use the reviewed sherpa2 speech release; legacy1.x bundles a GPL frontend')
    if args.bundle:
        root = args.bundle.resolve()
        if not root.is_dir():
            raise ValueError('Bundle directory is unavailable')
        blocked = ['espeak', 'piper_phonemize', 'piper-phonemize', 'comfyui', 'task-master-ai', 'n8n-core']
        for item in root.rglob('*'):
            name = item.relative_to(root).as_posix().casefold()
            if any(part in name for part in blocked):
                raise ValueError('External-only/restricted payload unexpectedly present in the runtime bundle')
            if item.suffix.casefold() in {'.onnx', '.safetensors', '.gguf'}:
                raise ValueError('Model weights must not be silently redistributed inside the app runtime')
    print('JAVO_LICENSE_BOUNDARY_OK: original MIT notice retained; reviewed speech engine; known restricted runtimes/models excluded. This is a technical gate, not a full legal audit.')


if __name__ == '__main__':
    main()
