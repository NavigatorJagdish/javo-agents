"""Real SQLite/process/concurrency accounting; no provider or billing requests."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import httpx
import pytest

from app.config import Settings
from app.core.ai_router import AIRouter
from app.core.usage_ledger import BudgetDenied, LedgerUnavailable, UsageLedger
from app.services import provider_settings as providers


def test_persistent_idempotent_local_usage_and_unknown_tokens(tmp_path):
    path = tmp_path / 'ledger.sqlite'
    ledger = UsageLedger(path)
    request = str(uuid4())
    assert ledger.reserve(request, 'ollama', 'local-model')
    assert not UsageLedger(path).reserve(request, 'ollama', 'local-model')
    ledger.settle(request, prompt_tokens=3, completion_tokens=5, cost_microusd=0)
    UsageLedger(path).settle(request, prompt_tokens=3, completion_tokens=5, cost_microusd=0)
    unknown = str(uuid4())
    ledger.reserve(unknown, 'ollama', 'local-model')
    ledger.settle(unknown, prompt_tokens=None, completion_tokens=None, cost_microusd=0)
    summary = UsageLedger(path).summary()
    assert summary['total_requests'] == 2 and summary['total_attempts'] == 2
    assert summary['total_tokens'] == 8
    assert summary['requests_with_unknown_token_usage'] == 1
    assert summary['daily_spend_usd'] == 0
    with pytest.raises(ValueError, match='rewritten'):
        ledger.settle(request, prompt_tokens=99, completion_tokens=5, cost_microusd=0)
    with pytest.raises(ValueError, match='different reservation'):
        ledger.reserve(request, 'ollama', 'different-model')
    env = {**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[2] / 'services/local-runtime'), 'JAVO_TEST_LEDGER': str(path)}
    script = "import os; from app.core.usage_ledger import UsageLedger; s=UsageLedger(os.environ['JAVO_TEST_LEDGER']).summary(); assert s['total_requests']==2 and s['total_tokens']==8; print('PROCESS_LEDGER_OK')"
    result = subprocess.run([sys.executable, '-c', script], env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0 and 'PROCESS_LEDGER_OK' in result.stdout, result.stderr


def test_atomic_reservations_never_overcommit(tmp_path):
    path = tmp_path / 'ledger.sqlite'

    def reserve(_):
        try:
            return UsageLedger(path).reserve(str(uuid4()), 'openai', 'fixture-model',
                estimate_microusd=20, daily_budget_microusd=100, monthly_budget_microusd=100, price_verified=True)
        except BudgetDenied:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(reserve, range(24)))
    assert sum(results) == 5
    summary = UsageLedger(path).summary()
    assert summary['unresolved_requests'] == 5 and summary['unresolved_reserved_usd'] == 0.0001


def test_unknown_outcome_hold_survives_restart_and_period_rollover(tmp_path):
    now = datetime(2026, 11, 30, 23, 59, tzinfo=timezone.utc)
    path = tmp_path / 'ledger.sqlite'
    ledger = UsageLedger(path, lambda: now)
    request = str(uuid4())
    args = dict(estimate_microusd=80, daily_budget_microusd=100, monthly_budget_microusd=100, price_verified=True)
    ledger.reserve(request, 'gemini', 'fixture-model', **args)
    ledger.fail(request)
    now += timedelta(days=1)
    reopened = UsageLedger(path, lambda: now)
    with pytest.raises(BudgetDenied):
        reopened.reserve(str(uuid4()), 'gemini', 'fixture-model', **args)
    assert reopened.summary()['unresolved_reserved_usd'] == 0.00008
    # Reconciliation may settle a genuinely known amount. This core operation
    # is not exposed as a client-supplied charge/price override in production.
    reopened.settle(request, prompt_tokens=1, completion_tokens=2, cost_microusd=10)
    assert reopened.reserve(str(uuid4()), 'gemini', 'fixture-model', **args)


def test_unknown_prices_invalid_usage_and_corrupt_storage_fail_closed(tmp_path):
    ledger = UsageLedger(tmp_path / 'ledger.sqlite')
    for kwargs in ({}, {'estimate_microusd': 0}, {'estimate_microusd': 10, 'price_verified': True}):
        with pytest.raises(BudgetDenied):
            ledger.reserve(str(uuid4()), 'openai', 'fixture-model', **kwargs)
    request = str(uuid4())
    ledger.reserve(request, 'ollama', 'fixture-model')
    with pytest.raises(ValueError):
        ledger.settle(request, prompt_tokens=-1, completion_tokens=1, cost_microusd=0)
    with pytest.raises(ValueError):
        ledger.settle(request, prompt_tokens=True, completion_tokens=1, cost_microusd=0)
    corrupt = tmp_path / 'broken.sqlite'
    corrupt.write_bytes(b'not-a-database')
    with pytest.raises(LedgerUnavailable):
        UsageLedger(corrupt).reserve(str(uuid4()), 'ollama', 'fixture-model')


@pytest.fixture
def configured(tmp_path, monkeypatch):
    settings = Settings(provider_config_path=str(tmp_path/'providers.enc'), usage_ledger_path=str(tmp_path/'usage.sqlite'), encryption_key='synthetic-ledger-key-'*3)
    monkeypatch.setattr(providers, 'get_settings', lambda: settings)
    return settings


@pytest.mark.asyncio
async def test_router_records_actual_local_counters_across_instances(configured, monkeypatch):
    original_client = httpx.AsyncClient

    def handle(request):
        return httpx.Response(200, json={'message': {'content': 'Fixture'}, 'prompt_eval_count': 3, 'eval_count': 5})

    monkeypatch.setattr('app.core.ai_router.httpx.AsyncClient', lambda **kwargs: original_client(transport=httpx.MockTransport(handle)))
    await AIRouter().generate('Private prompt never retained', fallback_to_local=False)
    status = AIRouter().get_provider_status()['usage']
    assert status['total_requests'] == 1 and status['total_tokens'] == 8
    data = Path(configured.usage_ledger_path).read_bytes()
    assert b'Private prompt never retained' not in data and b'Fixture' not in data


@pytest.mark.asyncio
async def test_failure_and_cancellation_are_persisted(configured, monkeypatch):
    router = AIRouter()
    started = asyncio.Event()

    async def blocked(*args):
        started.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(router, '_call_ollama', blocked)
    task = asyncio.create_task(router.generate('Fixture', fallback_to_local=False))
    await asyncio.wait_for(started.wait(), 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    summary = AIRouter().get_provider_status()['usage']
    assert summary['failed_requests'] == 1 and summary['total_requests'] == 0


@pytest.mark.asyncio
async def test_cloud_environment_budget_cannot_enable_spending(configured, monkeypatch):
    configured.ai_daily_budget = configured.ai_monthly_budget = 100
    called = False

    async def network(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError('Must not send a cloud request')

    monkeypatch.setattr(httpx.AsyncClient, 'post', network)
    router = AIRouter()
    with pytest.raises(RuntimeError, match='budget'):
        await router.generate('Hello', provider='openai', fallback_to_local=False)
    with pytest.raises(RuntimeError, match='budget'):
        await router._call_gemini('Hello', None, None, 0.7, 10)
    assert not called


@pytest.mark.asyncio
async def test_broken_ledger_prevents_local_provider_dispatch(configured, monkeypatch, tmp_path):
    corrupt = tmp_path / 'broken.sqlite'
    corrupt.write_bytes(b'broken')
    configured.usage_ledger_path = str(corrupt)
    called = False

    async def provider(*args):
        nonlocal called
        called = True

    router = AIRouter()
    monkeypatch.setattr(router, '_call_ollama', provider)
    with pytest.raises(LedgerUnavailable):
        await router.generate('Hello', fallback_to_local=False)
    assert not called


@pytest.mark.asyncio
async def test_budget_agent_reads_same_ledger_and_cannot_fabricate_spend(configured):
    from app.agents.budget_guardian import BudgetGuardianAgent
    ledger = UsageLedger(configured.usage_ledger_path)
    request = str(uuid4())
    ledger.reserve(request, 'ollama', 'fixture-model')
    ledger.settle(request, prompt_tokens=1, completion_tokens=1, cost_microusd=0)
    agent = BudgetGuardianAgent()
    result = await agent.execute({'action': 'summary'})
    assert result['allowed'] and result['usage']['total_requests'] == 1
    assert not (await agent.execute({'action': 'check_budget', 'provider': 'openai'}))['allowed']
    with pytest.raises(ValueError):
        await agent.execute({'action': 'record_spend', 'estimated_cost_usd': 10})
    assert ledger.summary()['total_attempts'] == 1


def test_overrun_is_recorded_and_blocks_later_reservations(tmp_path):
    ledger = UsageLedger(tmp_path/'usage.sqlite')
    request = str(uuid4())
    args = dict(estimate_microusd=50, daily_budget_microusd=100, monthly_budget_microusd=100, price_verified=True)
    ledger.reserve(request, 'openai', 'fixture-model', **args)
    ledger.settle(request, prompt_tokens=1, completion_tokens=1, cost_microusd=120)
    assert ledger.summary()['daily_spend_usd'] == 0.00012
    with pytest.raises(BudgetDenied):
        ledger.reserve(str(uuid4()), 'openai', 'fixture-model', **args)


@pytest.mark.asyncio
async def test_repeated_request_id_cannot_repeat_provider_dispatch(configured, monkeypatch):
    from app.core.ai_router import AIResponse
    identifier = uuid4()
    monkeypatch.setattr('app.core.ai_router.uuid4', lambda: identifier)
    calls = 0

    async def local(*args):
        nonlocal calls
        calls += 1
        return AIResponse(content='Synthetic reply', provider='ollama', model='fixture-model')

    router = AIRouter()
    monkeypatch.setattr(router, '_call_ollama', local)
    await router.generate('Hello', fallback_to_local=False)
    with pytest.raises(RuntimeError, match='duplicate dispatch'):
        await router.generate('Hello', fallback_to_local=False)
    assert calls == 1
