"""Real auth/storage/control/audio contracts; model text/waves explicitly synthetic."""
import io
import wave

import pytest


def model_files(path, operation):
    from app.services.speech import ready
    path.mkdir()
    names = ['model.int8.onnx', 'voices.bin', 'tokens.txt', 'espeak-ng-data', 'lexicon-us-en.txt', 'lexicon-zh.txt'] if operation == 'tts' else ['tiny-encoder.int8.onnx', 'tiny-decoder.int8.onnx', 'tiny-tokens.txt']
    for name in names:
        (path / name).write_bytes(b'synthetic model placeholder')
    assert ready(str(path), operation)


def wav(seconds=0.2):
    result = io.BytesIO()
    with wave.open(result, 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(16000)
        out.writeframes(b'\x10\x00' * int(16000 * seconds))
    return result.getvalue()


def test_voice_configuration_auth_encryption_restart_and_validation(owner_runtime, tmp_path):
    create, _ = owner_runtime
    tts, asr = tmp_path/'tts', tmp_path/'asr'
    model_files(tts, 'tts')
    model_files(asr, 'asr')
    with create() as client:
        assert not client.get('/api/voice/capabilities').json()['text_to_speech']
        assert client.get('/api/voice/configuration', headers={'Authorization': ''}).status_code == 401
        assert client.put('/api/voice/configuration', json={'tts_model_dir': '//remote/model'}).status_code == 422
        assert client.put('/api/voice/configuration', json={'tts_model_dir': str(tmp_path/'missing')}).status_code == 422
        result = client.put('/api/voice/configuration', json={'tts_model_dir': str(tts), 'asr_model_dir': str(asr)})
        assert result.status_code == 200
        from app.services.speech import vault
        assert str(tts).encode() not in vault().path.read_bytes()
    with create() as client:
        assert client.get('/api/voice/capabilities').json()['speech_to_text']
        assert client.get('/api/voice/configuration').json()['tts_model_dir'] == str(tts)


def test_binary_speech_transcript_review_and_runtime_guards(owner_runtime, tmp_path, monkeypatch):
    from pathlib import Path
    from app.services import speech
    create, _ = owner_runtime
    tts, asr = tmp_path/'tts', tmp_path/'asr'
    model_files(tts, 'tts')
    model_files(asr, 'asr')
    calls = []

    async def synthetic_worker(value):
        calls.append(value)
        if value['operation'] == 'tts':
            Path(value['output']).write_bytes(wav())
            return {'seconds': 0.2}
        return {'text': 'Synthetic reviewed transcript.'}

    monkeypatch.setattr(speech, 'run_worker', synthetic_worker)
    with create() as client:
        client.put('/api/voice/configuration', json={'tts_model_dir': str(tts), 'asr_model_dir': str(asr)})
        assert client.post('/api/voice/tts', json={'text': 'Hello'}).status_code == 409
        assert client.post('/api/security/resume').status_code == 200
        output = client.post('/api/voice/tts', json={'text': 'Hello', 'voice': 'hf_alpha', 'effect': 'echo'})
        assert output.status_code == 200, output.text
        assert output.content.startswith(b'RIFF') and output.headers['cache-control'] == 'no-store'
        assert calls[-1]['speaker'] == 31 and calls[-1]['effect'] == 'echo'
        assert not Path(calls[-1]['output']).exists()
        for data in [{'text': ' '}, {'text': 'x', 'voice': 'unknown'}, {'text': 'x', 'effect': 'shell'}, {'text': 'x', 'speed': 4}, {'text': 'x'*801}]:
            assert client.post('/api/voice/tts', json=data).status_code == 422
        assert client.post('/api/voice/transcribe', files={'file': ('bad.wav', b'not audio')}).status_code == 422
        result = client.post('/api/voice/transcribe', files={'file': ('clip.wav', wav())}, data={'language': 'hi'})
        assert result.status_code == 200, result.text
        assert result.json()['requires_review'] and not result.json()['actions_executed']
        assert calls[-1]['language'] == 'hi' and not Path(calls[-1]['input']).exists()
        before = len(calls)
        assert client.post('/api/voice/transcribe', files={'file': ('clip.wav', b'0'*(3*1024*1024+1))}).status_code == 413
        assert len(calls) == before
        client.post('/api/security/emergency-stop')
        assert client.post('/api/voice/tts', json={'text': 'Hello'}).status_code == 409


@pytest.mark.asyncio
async def test_neural_process_cancel_kills_child_and_scrubs_environment(monkeypatch):
    import asyncio
    from app.services import speech
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-private-key')
    monkeypatch.setenv('HTTP_PROXY', 'http://synthetic-private-proxy')
    began = asyncio.Event()
    class Process:
        returncode = None
        killed = False
        async def communicate(self, data):
            began.set()
            await asyncio.Future()
        def kill(self):
            self.killed = True
            self.returncode = -1
        async def wait(self):
            return self.returncode
    child = Process()
    async def spawn(*args, **kwargs):
        assert 'OPENAI_API_KEY' not in kwargs['env'] and 'HTTP_PROXY' not in kwargs['env']
        assert not any(k.startswith('JAVO_') for k in kwargs['env'])
        return child
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', spawn)
    task = asyncio.create_task(speech.run_worker({'operation': 'tts'}))
    await asyncio.wait_for(began.wait(), 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert child.killed


@pytest.mark.asyncio
async def test_actual_speech_process_tree_is_killed_on_cancel(monkeypatch, tmp_path):
    import asyncio
    import json
    import sys
    import time
    import psutil
    from app.services import speech
    signal_file = tmp_path/'owned-processes.json'
    source = ('import subprocess,sys,time,json,os;from pathlib import Path;'
        'child=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"]);'
        f'Path({str(signal_file)!r}).write_text(json.dumps([os.getpid(),child.pid]));time.sleep(60)')
    original = asyncio.create_subprocess_exec
    async def controlled_spawn(*args, **kwargs):
        if len(args) > 2 and args[1:3] == ('-m', 'app.services.speech_worker'):
            return await original(sys.executable, '-c', source, **kwargs)
        return await original(*args, **kwargs)
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', controlled_spawn)
    task = asyncio.create_task(speech.run_worker({'operation': 'tts'}))
    owned = []
    try:
        deadline = time.monotonic()+10
        while not signal_file.exists() and time.monotonic() < deadline:
            await asyncio.sleep(0.05)
        assert signal_file.exists()
        owned = [psutil.Process(pid) for pid in json.loads(signal_file.read_text())]
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, 12)
        for process in owned:
            try:
                assert not process.is_running() or process.status() == psutil.STATUS_ZOMBIE
            except psutil.NoSuchProcess:
                pass
    finally:
        task.cancel()
        for process in owned:
            try:
                if process.is_running():
                    process.kill()
            except psutil.NoSuchProcess:
                pass
