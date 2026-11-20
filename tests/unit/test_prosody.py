"""Audio safety and actual signal effects, without pretending to test naturalness."""
import numpy as np
import pytest
from app.services.prosody import apply, pace, PROFILES


def signal():
    time=np.arange(24000,dtype=np.float32)/24000
    return 0.5*np.sin(2*np.pi*220*time)


def test_neutral_and_zero_intensity_retain_the_original_samples():
    original=signal()
    assert np.array_equal(apply(original,24000,'neutral',0.6),original)
    assert np.array_equal(apply(original,24000,'angry',0),original)
    assert pace('angry',0)==1


@pytest.mark.parametrize('tone', [key for key in PROFILES if key!='neutral'])
def test_each_tone_changes_audio_with_finite_bounded_peak_and_duration(tone):
    original=signal()
    out=apply(original,24000,tone,0.8)
    assert out.dtype==np.float32 and out.ndim==1 and np.isfinite(out).all()
    assert 0.7*len(original)<len(out)<1.4*len(original)
    assert abs(out).max()<=0.991
    assert len(out)!=len(original) or not np.array_equal(out,original)


def test_deep_bright_modify_samples_instead_of_changing_wav_sample_rate():
    original=signal()
    deep=apply(original,24000,'neutral',0,'deep')
    bright=apply(original,24000,'neutral',0,'bright')
    assert len(deep)>len(original)>len(bright)
    for bad in [np.array([np.nan]), np.array([[1,2]])]:
        with pytest.raises(ValueError):
            apply(bad,24000,'neutral',0.6)
