"""One local neural operation per short-lived process; never downloads a model."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import wave


def main():
    import numpy as np
    import sherpa_onnx

    raw = sys.stdin.buffer.read(65537)
    if len(raw) > 65536:
        raise ValueError('Speech operation exceeds its supported input size')
    value = json.loads(raw)
    root = Path(value['model_dir'])
    if value['operation'] == 'tts':
        from app.services.hindi_frontend import pronounce
        from app.services.prosody import apply, pace
        emotion, strength = value.get('emotion','neutral'), value.get('emotion_strength',0.6)
        # Native sherpa2 lexicon frontend: no espeak/piper module or data loaded.
        lexicon = dict(value.get('pronunciations', {'javo': 'dʒɑːvoʊ'}))
        for word in re.findall(r'[\u0900-\u097f]+', value['text']):
            lexicon.setdefault(word, pronounce(word))
        symbols = {line.rsplit(' ', 1)[0] for line in (root/'tokens.txt').read_text(encoding='utf-8').splitlines()}
        custom = Path(value['output']).with_name('custom-lexicon.txt')
        custom.write_text('\n'.join(word+' '+' '.join(c for c in phones if c in symbols) for word, phones in lexicon.items()), encoding='utf-8')
        native = 'lexicon-gb-en.txt' if value.get('speaker') in range(20, 28) and (root/'lexicon-gb-en.txt').is_file() else 'lexicon-us-en.txt'
        config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                    model=str(root / 'model.int8.onnx'), voices=str(root / 'voices.bin'),
                    tokens=str(root / 'tokens.txt'),
                    lexicon=','.join([str(custom), str(root/native)]),
                ), num_threads=2, provider='cpu', debug=False,
            ), max_num_sentences=1,
        )
        if not config.validate():
            raise ValueError('Speech configuration unavailable')
        engine = sherpa_onnx.OfflineTts(config)
        audio = engine.generate(value['text'], sid=value['speaker'], speed=value['speed']*pace(emotion,strength))
        samples = np.asarray(audio.samples, dtype=np.float32)
        rate = audio.sample_rate
        # Original DSP effects, clearly distinct from model/voice training.
        effect = value.get('effect', 'natural')
        if effect == 'radio':
            samples = np.concatenate(([0], np.diff(samples)))
            samples = np.tanh(samples * 3) * 0.65
        elif effect == 'echo':
            delay = int(rate * 0.15)
            mixed = np.zeros(len(samples) + delay, dtype=np.float32)
            mixed[:len(samples)] += samples
            mixed[delay:] += samples * 0.25
            samples = mixed
        samples = apply(samples,rate,emotion,strength,effect)
        peak = float(np.max(np.abs(samples))) if len(samples) else 0
        if peak > 0.99:
            samples *= 0.99 / peak
        pcm = (np.clip(samples, -1, 1) * 32767).astype('<i2')
        with wave.open(value['output'], 'wb') as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(rate)
            out.writeframes(pcm.tobytes())
        print(json.dumps({'sample_rate': rate, 'seconds': len(samples) / rate}))
    else:
        with wave.open(value['input'], 'rb') as source:
            rate = source.getframerate()
            samples = np.frombuffer(source.readframes(source.getnframes()), dtype='<i2').astype(np.float32) / 32768
        # Avoid a recognizer inventing a transcript for actual silence.
        if not len(samples) or float(np.sqrt(np.mean(samples ** 2))) < 0.001:
            print(json.dumps({'text': '', 'language': value['language']}))
            return
        recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=str(root / 'tiny-encoder.int8.onnx'),
            decoder=str(root / 'tiny-decoder.int8.onnx'), tokens=str(root / 'tiny-tokens.txt'),
            language='' if value['language'] == 'auto' else value['language'],
            task='transcribe', num_threads=2, provider='cpu', debug=False,
        )
        stream = recognizer.create_stream()
        stream.accept_waveform(rate, samples)
        recognizer.decode_stream(stream)
        print(json.dumps({'text': stream.result.text.strip(), 'language': value['language']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
