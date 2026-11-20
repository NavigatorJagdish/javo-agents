"""Explicit real Kokoro/Whisper smoke with normal admission and no owner data."""
import argparse
import io
import json
from pathlib import Path
import time
import wave
from uuid import uuid4

from verification_runtime import isolated_runtime, AcceptanceRefused


def admitted_request(request, *args, **kwargs):
    # The server explicitly proves no factory/model call began. Never retry a
    # model failure, unknown/network outcome, stopped runtime or invoked work.
    deadline = time.monotonic()+20
    while True:
        try:
            return request(*args, **kwargs)
        except AcceptanceRefused as error:
            if error.status != 503 or not error.uninvoked or time.monotonic() >= deadline:
                raise
            print('SPEECH_ACCEPTANCE_WAITING_FOR_UNINVOKED_CAPACITY', flush=True)
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-root', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--tones', action='store_true', help='Also verify real prosody-tone WAVs; this is not trained emotion or natural-laughter acceptance')
    args = parser.parse_args()
    with isolated_runtime() as (_, request):
        cfg = {'tts_model_dir': str((args.model_root/'kokoro-int8-multi-lang-v1_0').resolve()),
               'asr_model_dir': str((args.model_root/'sherpa-onnx-whisper-tiny').resolve())}
        request('/api/voice/configuration', cfg, method='PUT')
        capabilities = request('/api/voice/capabilities')
        assert capabilities['text_to_speech'] and capabilities['speech_to_text']
        request('/api/security/resume', {})
        args.output_dir.mkdir(parents=True, exist_ok=True)
        evidence = []
        samples = [('english', 'af_heart', 'Hello, welcome to Javo. Let us create something useful today.', 'natural'),
                                           ('hindi', 'hf_alpha', 'नमस्ते, जावो में आपका स्वागत है। आइए कुछ नया बनाते हैं।', 'natural'),
                                           ('radio', 'am_adam', 'This is Javo studio. Your creative work starts here.', 'radio')]
        if args.tones:
            samples += [(tone,'af_heart','Ha, ha! That is a funny idea.' if tone=='laugh' else 'Let us try a new creative idea today.','deep' if tone=='curious' else 'natural') for tone in ['happy','curious','angry','laugh']]
        for label, voice, text, effect in samples:
            started = time.monotonic()
            tone=label if label in {'happy','curious','angry','laugh'} else 'neutral'
            data = admitted_request(request, '/api/voice/tts', {'text': text, 'voice': voice, 'effect': effect,'emotion':tone,'emotion_strength':0.7}, raw=True)
            with wave.open(io.BytesIO(data)) as audio:
                assert audio.getnchannels() == 1 and audio.getnframes() > 1000
                assert audio.getframerate() in {16000,22050,24000,44100,48000}
                duration = audio.getnframes()/audio.getframerate()
            (args.output_dir/('javo-'+label+'.wav')).write_bytes(data)
            evidence.append({'sample': label, 'seconds': round(time.monotonic()-started, 3), 'audio_seconds': round(duration, 3), 'bytes': len(data)})
            print(json.dumps({'speech_sample_verified': evidence[-1]}), flush=True)
        # Use the saved synthetic-brief English waveform for a real recognizer
        # round trip; this is not a physical microphone or accent-quality test.
        recognition = []
        for label, language in [('english', 'en'), ('hindi', 'hi')]:
            boundary = 'javo-'+str(uuid4())
            form = ('--'+boundary+'\r\nContent-Disposition: form-data; name="language"\r\n\r\n'+language+
                '\r\n--'+boundary+'\r\nContent-Disposition: form-data; name="file"; filename="clip.wav"\r\nContent-Type: audio/wav\r\n\r\n').encode()
            form += (args.output_dir/('javo-'+label+'.wav')).read_bytes()+('\r\n--'+boundary+'--\r\n').encode()
            started = time.monotonic()
            result = admitted_request(request, '/api/voice/transcribe', form, content_type='multipart/form-data; boundary='+boundary)
            assert result['text'].strip() and result['requires_review'] is True and result['actions_executed'] is False
            recognition.append({'sample': label, 'seconds': round(time.monotonic()-started, 3), 'transcript': result['text']})
            print(json.dumps({'recognition_verified': recognition[-1]}, ensure_ascii=False), flush=True)
        print(json.dumps({'marker': 'REAL_LOCAL_NEURAL_TTS_HTTP_WAV_OK', 'samples': evidence,
            'recognition_marker': 'REAL_LOCAL_WHISPER_REVIEW_ROUNDTRIP_OK', 'recognition': recognition,
            'production_resource_admission': True, 'cloud_execution': False,
            'physical_microphone_verified': False, 'voice_training': False}))
        if args.tones:
            print('REAL_NEURAL_VOICE_PROSODY_TONE_WAVS_OK; original effects, not trained emotion/natural-laughter proof')


if __name__ == '__main__':
    main()
