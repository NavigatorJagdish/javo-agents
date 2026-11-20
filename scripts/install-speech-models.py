"""Explicit optional model setup outside the repo; verifies pinned archives.

Only model/lexicon/license files needed by the sherpa2 native frontend are
installed. espeak data, executables and unrelated sample files are excluded.
No service, owner setting or paid account is activated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tarfile
import tempfile
from urllib.request import build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]
ASSETS = [
    {'name': 'kokoro-int8-multi-lang-v1_0', 'tag': 'tts-models', 'size': 132353410,
     'sha256': '72c347230107ef8a31098ec4d468a605244beef5f1ed00db97efa13518800653', 'vendor_digest_available': True,
     'files': ['model.int8.onnx', 'voices.bin', 'tokens.txt', 'lexicon-us-en.txt', 'lexicon-gb-en.txt', 'LICENSE', 'README.md']},
    {'name': 'sherpa-onnx-whisper-tiny', 'tag': 'asr-models', 'size': 116204861,
     'sha256': 'c46116994e539aa165266d96b325252728429c12535eb9d8b6a2b10f129e66b1', 'vendor_digest_available': False,
     'files': ['tiny-encoder.int8.onnx', 'tiny-decoder.int8.onnx', 'tiny-tokens.txt']},
]


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def install(root, asset):
    archive = root/(asset['name']+'.tar.bz2')
    url = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/'+asset['tag']+'/'+archive.name
    if not archive.exists():
        partial = archive.with_suffix('.part')
        try:
            opener = build_opener(ProxyHandler({}))
            with opener.open(url, timeout=60) as response, partial.open('xb') as destination:
                count = 0
                while chunk := response.read(1024*1024):
                    count += len(chunk)
                    if count > asset['size']:
                        raise ValueError('Model archive exceeded its pinned size')
                    destination.write(chunk)
            if partial.stat().st_size != asset['size'] or digest(partial) != asset['sha256']:
                raise ValueError('Model archive checksum mismatch')
            os.link(partial, archive)  # Exclusive publication never replaces an owner's file.
        finally:
            partial.unlink(missing_ok=True)
    if archive.is_symlink() or archive.stat().st_size != asset['size'] or digest(archive) != asset['sha256']:
        raise ValueError('Existing model archive does not match the reviewed pin; original file retained')
    target = root/asset['name']
    if target.is_symlink():
        raise ValueError('Model directory is a symlink')
    target.mkdir(exist_ok=True)
    hashes = {}
    with tarfile.open(archive) as bundle:
        members = bundle.getmembers()
        if sum(member.size for member in members) > 1024**3:
            raise ValueError('Expanded archive exceeds its bound')
        for member in members:
            if not (root/member.name).resolve().is_relative_to(root) or not (member.isfile() or member.isdir()):
                raise ValueError('Unsafe model archive member')
        for name in asset['files']:
            member = bundle.getmember(asset['name']+'/'+name)
            if not member.isfile():
                raise ValueError('Required model member is not a file')
            destination = target/name
            if destination.is_symlink():
                raise ValueError('Existing model file is a symlink')
            handle, temporary = tempfile.mkstemp(prefix='speech-model-', suffix='.tmp', dir=target)
            temporary = Path(temporary)
            try:
                with os.fdopen(handle, 'wb') as output, bundle.extractfile(member) as source:
                    while chunk := source.read(1024*1024):
                        output.write(chunk)
                expected = digest(temporary)
                if destination.exists():
                    if digest(destination) != expected:
                        raise ValueError('Existing model differs; original owner file retained')
                else:
                    os.link(temporary, destination)
                hashes[name] = expected
            finally:
                temporary.unlink(missing_ok=True)
    return {'model': asset['name'], 'source': url, 'archive_sha256': asset['sha256'],
            'vendor_digest_available': asset['vendor_digest_available'], 'installed_files': hashes,
            'gpl_frontend_extracted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-root', required=True, type=Path)
    args = parser.parse_args()
    root = args.model_root.resolve()
    if root.is_relative_to(ROOT):
        raise ValueError('Choose a model directory outside the source repository/distributable')
    root.mkdir(parents=True, exist_ok=True)
    evidence = [install(root, item) for item in ASSETS]
    (root/'javo-speech-model-provenance.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print('VERIFIED_SPEECH_MODELS_READY_OUTSIDE_REPO; native lexicon only; no service or owner setting changed.')


if __name__ == '__main__':
    main()
