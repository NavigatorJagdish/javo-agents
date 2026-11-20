"""Acceptance may wait for proven uninvoked capacity, never replay unknown work."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def driver(monkeypatch):
    scripts=Path(__file__).resolve().parents[2]/'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    spec=importlib.util.spec_from_file_location('speech_acceptance_driver',scripts/'verify-local-speech.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    clock=[0]
    def sleep(seconds):
        clock[0]+=seconds
    monkeypatch.setattr(module,'time',SimpleNamespace(monotonic=lambda:clock[0],sleep=sleep))
    return module,clock


def test_confirmed_uninvoked_refusal_can_wait_before_first_model_call(driver):
    module,clock=driver
    calls=[]
    def request(*args,**kwargs):
        calls.append((args,kwargs))
        if len(calls)==1:
            raise module.AcceptanceRefused('Synthetic CPU busy',503,True)
        return b'actual response sentinel'
    assert module.admitted_request(request,'/api/voice/tts',{'text':'synthetic'})==b'actual response sentinel'
    assert len(calls)==2 and calls[0]==calls[1] and clock[0]==1


@pytest.mark.parametrize('failure',['invoked','network','stopped'])
def test_invoked_unknown_and_stopped_requests_are_never_replayed(driver,failure):
    module,clock=driver
    error=TimeoutError('Unknown outcome') if failure=='network' else module.AcceptanceRefused('No retry',409 if failure=='stopped' else 503,failure=='stopped')
    calls=[]
    def request(*args,**kwargs):
        calls.append(1)
        raise error
    with pytest.raises(type(error)):
        module.admitted_request(request,'/api/voice/transcribe',b'synthetic')
    assert len(calls)==1 and clock[0]==0


def test_persistent_refusal_has_a_fixed_deadline(driver):
    module,clock=driver
    def request(*args,**kwargs):
        raise module.AcceptanceRefused('Synthetic persistent low RAM',503,True)
    with pytest.raises(module.AcceptanceRefused):
        module.admitted_request(request,'/api/voice/tts',{})
    assert clock[0]==20
