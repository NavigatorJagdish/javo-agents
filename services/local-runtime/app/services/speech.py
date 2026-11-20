"""Authenticated offline speech, with bounded input and killable model processes."""
from __future__ import annotations

import asyncio
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import wave
import re
import signal
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import get_settings
from app.core.provider_store import ProviderVault, VaultUnavailable
from app.core.resource_manager import get_resource_manager
from app.services.prosody import PROFILES

VOICES = [
    {'id': 'af_heart', 'speaker': 3, 'language': 'en', 'name': 'Heart · English'},
    {'id': 'af_bella', 'speaker': 2, 'language': 'en', 'name': 'Bella · English'},
    {'id': 'am_adam', 'speaker': 11, 'language': 'en', 'name': 'Adam · English'},
    {'id': 'bf_emma', 'speaker': 21, 'language': 'en', 'name': 'Emma · British English'},
    {'id': 'hf_alpha', 'speaker': 31, 'language': 'hi', 'name': 'Alpha · Hindi'},
    {'id': 'hf_beta', 'speaker': 32, 'language': 'hi', 'name': 'Beta · Hindi'},
    {'id': 'hm_omega', 'speaker': 33, 'language': 'hi', 'name': 'Omega · Hindi'},
    {'id': 'hm_psi', 'speaker': 34, 'language': 'hi', 'name': 'Psi · Hindi'},
]


class SpeechConfiguration(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    tts_model_dir: str = Field(default='', max_length=1024)
    asr_model_dir: str = Field(default='', max_length=1024)
    pronunciations: dict[str, str] = Field(default_factory=lambda: {'javo': 'dʒɑːvoʊ'})

    @field_validator('pronunciations')
    @classmethod
    def word_pronunciations(cls, value):
        if len(json.dumps(value, ensure_ascii=False).encode()) > 32768 or len(value) > 100 or any(not re.fullmatch(r'[\w\-]{1,40}', word) or not 1 <= len(phones) <= 160 or
            any(ord(c) < 32 or c in '|\\' for c in phones) for word, phones in value.items()):
            raise ValueError('Use up to100 single words with bounded IPA pronunciations and no control characters')
        return value

    @field_validator('tts_model_dir', 'asr_model_dir')
    @classmethod
    def local_path(cls, value):
        if value and (not Path(value).is_absolute() or value.startswith(('\\\\', '//'))):
            raise ValueError('Choose an absolute local model directory')
        return value


def vault():
    s = get_settings()
    return ProviderVault(Path(s.provider_config_path).with_name('voice-config.enc'), s.encryption_key,
                         key_domain=b'javo-voice-v1\0')


def configuration():
    try:
        return SpeechConfiguration.model_validate(vault().read()['settings']).model_dump()
    except (ValueError, VaultUnavailable):
        raise HTTPException(503, 'Voice configuration is locked or damaged. Recover its original settings and key.') from None


def ready(root, operation):
    if not root:
        return False
    names = ['model.int8.onnx', 'voices.bin', 'tokens.txt', 'lexicon-us-en.txt'] if operation == 'tts' else ['tiny-encoder.int8.onnx', 'tiny-decoder.int8.onnx', 'tiny-tokens.txt']
    base = Path(root)
    return base.is_dir() and not base.is_symlink() and all((base / n).is_file() and not (base / n).is_symlink() for n in names)


def engine_compatible():
    from importlib.metadata import PackageNotFoundError, version
    try:
        return version('sherpa-onnx') == '2.0.1' and version('sherpa-onnx-core') == '2.0.1'
    except PackageNotFoundError:
        return False


def capabilities():
    cfg = configuration()
    installed = engine_compatible()
    return {'text_assistant': True, 'text_to_speech': installed and ready(cfg['tts_model_dir'], 'tts'),
            'speech_to_text': installed and ready(cfg['asr_model_dir'], 'asr'), 'wake_word': False,
            'history_storage': 'tab-memory-only', 'engine': 'Kokoro int8 / Whisper tiny · local CPU',
            'generation_verified': False, 'voices': VOICES,
            'effects': ['natural', 'radio', 'echo', 'deep', 'bright'],
            'emotions': list(PROFILES),
            'emotion_mode': 'Original prosody effects; not a trained emotion model or natural laughter',
            'message': 'Model files indicate readiness only. Speech is AI-generated. Review transcripts before sending. Hindi pronunciation uses an approximate original frontend; voice-model training is not enabled.'}


def require_capacity():
    manager = get_resource_manager()
    if manager._paused or manager._emergency_stopped:
        raise HTTPException(409, 'Runtime is paused or stopped. Explicitly resume before generating or transcribing speech.')
    if not manager.can_accept_work()[0]:
        raise HTTPException(503, 'Speech needs free memory and a queue slot. Close unused applications or wait, then retry.')
    return manager


def validate_wave(data):
    try:
        with wave.open(io.BytesIO(data), 'rb') as source:
            if (source.getnchannels() != 1 or source.getsampwidth() != 2 or source.getcomptype() != 'NONE'
                    or source.getframerate() not in {16000, 22050, 24000, 44100, 48000}
                    or not 0 < source.getnframes() <= source.getframerate() * 30):
                raise ValueError('Invalid WAV')
            if len(source.readframes(source.getnframes())) != source.getnframes() * 2:
                raise ValueError('Truncated WAV')
    except (ValueError, wave.Error, EOFError):
        raise HTTPException(422, 'Upload a complete mono 16-bit PCM WAV, at most30 seconds, at a supported sample rate.') from None


async def run_worker(value):
    args = [sys.executable, '--speech-worker'] if getattr(sys, 'frozen', False) else [sys.executable, '-m', 'app.services.speech_worker']
    # Neural processes need OS paths, not provider credentials or proxy settings.
    allowed = {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH', 'LANG', 'PYTHONUTF8', 'PYTHONIOENCODING'}
    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    env.update(OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    process = await asyncio.create_subprocess_exec(*args, stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, env=env,
            cwd=str(Path(__file__).resolve().parents[2]),
            **({'creationflags': 0x08000000} if sys.platform == 'win32' else {'start_new_session': True}))
    try:
        encoded = json.dumps(value, ensure_ascii=False).encode()
        if len(encoded) > 65536:
            raise ValueError('Speech operation exceeds its supported input size')
        output, _ = await asyncio.wait_for(process.communicate(encoded), timeout=90)
        if process.returncode != 0 or len(output) > 16384:
            raise RuntimeError('Local speech model failed')
        return json.loads(output)
    finally:
        cleanup = asyncio.create_task(_stop_worker(process))
        await asyncio.shield(cleanup)


async def _stop_worker(process):
    if process.returncode is None:
        pid = getattr(process, 'pid', None)
        if sys.platform == 'win32' and pid:
            # A Windows venv launcher can have an interpreter child. Killing
            # only its wrapper leaves inference running with open pipe handles.
            executable = str(Path(os.environ.get('SystemRoot', 'C:/Windows'))/'System32/taskkill.exe')
            killer = await asyncio.create_subprocess_exec(executable, '/PID', str(pid), '/T', '/F',
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL, creationflags=0x08000000)
            await asyncio.wait_for(killer.wait(), 5)
        elif pid and sys.platform != 'win32':
            try:
                if os.getpgid(pid) == pid:
                    os.killpg(pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
        else:
            process.kill()
    await asyncio.wait_for(process.wait(), 5)


async def synthesize(text, voice, speed, effect, emotion='neutral', emotion_strength=0.6):
    if not engine_compatible():
        raise HTTPException(501, 'Install the reviewed sherpa2 speech engine first. Legacy GPL frontend packages are not used by Javo.')
    cfg = configuration()
    if not ready(cfg['tts_model_dir'], 'tts'):
        raise HTTPException(501, 'Install and select the local Kokoro model directory in Voice setup first.')
    selected = next((v for v in VOICES if v['id'] == voice), None)
    if selected is None:
        raise HTTPException(422, 'Choose an available voice')
    manager = require_capacity()
    async def operation():
        with tempfile.TemporaryDirectory(prefix='javo-speech-') as folder:
            output = Path(folder) / 'speech.wav'
            result = await run_worker({'operation': 'tts', 'model_dir': cfg['tts_model_dir'],
                'text': text, 'speaker': selected['speaker'], 'language': selected['language'],
                'speed': speed, 'effect': effect, 'emotion': emotion, 'emotion_strength': emotion_strength,
                'output': str(output), 'pronunciations': cfg['pronunciations']})
            if not output.is_file() or output.stat().st_size > 8 * 1024 * 1024 or not 0 < result['seconds'] <= 90:
                raise RuntimeError('Speech output exceeded its bound')
            return output.read_bytes()
    return await manager.submit_task('speech-' + str(uuid4()), operation)


async def transcribe(data, language):
    if not engine_compatible():
        raise HTTPException(501, 'Install the reviewed sherpa2 speech engine first.')
    validate_wave(data)
    cfg = configuration()
    if not ready(cfg['asr_model_dir'], 'asr'):
        raise HTTPException(501, 'Install and select the local Whisper model directory in Voice setup first.')
    manager = require_capacity()
    async def operation():
        with tempfile.TemporaryDirectory(prefix='javo-transcribe-') as folder:
            source = Path(folder) / 'recording.wav'
            source.write_bytes(data)
            result = await run_worker({'operation': 'asr', 'model_dir': cfg['asr_model_dir'],
                'input': str(source), 'language': language})
            if not isinstance(result.get('text'), str) or len(result['text']) > 8000:
                raise RuntimeError('Transcript exceeded its bound')
            return {'text': result['text'], 'language': language, 'source': 'Whisper tiny · local',
                    'requires_review': True, 'actions_executed': False}
    return await manager.submit_task('transcribe-' + str(uuid4()), operation)
