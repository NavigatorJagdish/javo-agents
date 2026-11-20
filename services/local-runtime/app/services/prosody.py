"""Original bounded prosody effects; these are not trained emotion embeddings."""
from __future__ import annotations

PROFILES = {
    'neutral': (1.0, 1.0, 1.0, 0.0),
    'happy': (1.08, 1.055, 1.08, 0.0),
    'curious': (0.97, 1.025, 1.0, 0.0),
    'playful': (1.04, 1.07, 1.06, 0.06),
    'funny': (1.10, 1.10, 1.08, 0.09),
    'angry': (1.05, 0.98, 1.20, 0.0),
    'calm': (0.90, 0.98, 0.88, 0.0),
    'sad': (0.88, 0.95, 0.85, 0.0),
    'laugh': (1.08, 1.06, 1.05, 0.35),
}


def pace(emotion, strength):
    return 1+(PROFILES[emotion][0]-1)*strength


def apply(samples, rate, emotion, strength, effect='natural'):
    import numpy as np
    samples = np.asarray(samples, dtype=np.float32)
    if not np.isfinite(samples).all() or samples.ndim != 1 or len(samples) > rate*90:
        raise ValueError('Invalid or oversized speech waveform')
    _, pitch, energy, pulse = PROFILES[emotion]
    ratio = 1+(pitch-1)*strength
    if effect in {'deep', 'bright'}:
        ratio *= 0.88 if effect == 'deep' else 1.12
    # Change the samples, retaining a standard WAV sample rate that the
    # recognizer accepts. Pitch and duration still change together.
    if len(samples) and ratio != 1:
        positions = np.arange(0, len(samples), ratio)
        if emotion == 'curious' and strength:
            positions += strength*0.04*len(samples)*np.maximum(positions/len(samples)-0.7,0)**2
        samples = np.interp(positions, np.arange(len(samples)), samples).astype(np.float32)
    samples = samples*(1+(energy-1)*strength)
    if len(samples) and pulse and strength:
        time = np.arange(len(samples))/rate
        samples *= 1-pulse*strength*(0.5+0.5*np.sin(2*np.pi*5.2*time))
    peak = float(np.max(np.abs(samples))) if len(samples) else 0
    if peak > 0.99:
        samples *= 0.99/peak
    return np.clip(samples,-0.99,0.99).astype(np.float32)
