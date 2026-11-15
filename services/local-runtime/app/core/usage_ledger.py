"""Durable API usage accounting with atomic reservations and conservative holds.

Amounts are integer micro-USD. This module does not authorize purchases, carry
price tables, make network calls, or expire unresolved reservations on restart.
Only identifiers, counters and accounting metadata are retained, never prompts,
responses, API keys or provider URLs.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3
from uuid import UUID


class LedgerUnavailable(RuntimeError):
    pass


class BudgetDenied(RuntimeError):
    pass


class UsageLedger:
    def __init__(self, path: str | Path, clock=None):
        self.path = Path(path)
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _now(self):
        now = self.clock()
        if now.tzinfo is None:
            raise ValueError('Ledger clock must include a timezone')
        return now.astimezone(timezone.utc)

    @contextmanager
    def _connection(self):
        connection = None
        try:
            if self.path.is_symlink():
                raise LedgerUnavailable('Usage ledger cannot be a symbolic link')
            self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
            connection.row_factory = sqlite3.Row
            connection.execute('PRAGMA synchronous=FULL')
            connection.execute('''CREATE TABLE IF NOT EXISTS ai_ledger_meta (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                version INTEGER NOT NULL, coverage_since TEXT NOT NULL)''')
            connection.execute('INSERT OR IGNORE INTO ai_ledger_meta VALUES(1,1,?)', (self._now().isoformat(),))
            if connection.execute('SELECT version FROM ai_ledger_meta WHERE singleton=1').fetchone()[0] != 1:
                raise LedgerUnavailable('Unsupported usage ledger version')
            connection.execute('''CREATE TABLE IF NOT EXISTS ai_usage (
                request_id TEXT PRIMARY KEY, provider TEXT NOT NULL, model TEXT NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('reserved','completed','failed','uncertain')),
                reserved_microusd INTEGER NOT NULL CHECK(reserved_microusd>=0),
                cost_microusd INTEGER CHECK(cost_microusd>=0),
                prompt_tokens INTEGER CHECK(prompt_tokens>=0),
                completion_tokens INTEGER CHECK(completion_tokens>=0),
                pricing_basis TEXT NOT NULL, created_at TEXT NOT NULL,
                period_day TEXT NOT NULL, period_month TEXT NOT NULL, settled_at TEXT)''')
            connection.execute('CREATE INDEX IF NOT EXISTS ai_usage_periods ON ai_usage(period_month,period_day)')
            yield connection
        except (sqlite3.Error, OSError):
            raise LedgerUnavailable('Usage ledger is unavailable; execution remains blocked') from None
        finally:
            if connection is not None:
                connection.close()  # SQLite rolls back an uncommitted transaction.

    @staticmethod
    def _integer(value, name, optional=False):
        if optional and value is None:
            return
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10**15:
            raise ValueError(f'{name} must be a nonnegative bounded integer')

    def reserve(self, request_id: str, provider: str, model: str, *,
                estimate_microusd: int | None = None, daily_budget_microusd: int = 0,
                monthly_budget_microusd: int = 0, price_verified: bool = False) -> bool:
        """Return True only for a newly reserved ID; False never authorizes replay.

        Cloud callers must supply an independently verified conservative maximum
        quote and configured budgets. Current AIRouter never enables that path.
        """
        UUID(request_id)
        if provider not in {'ollama', 'gemini', 'openai'}:
            raise ValueError('Unsupported provider')
        if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}', model):
            raise ValueError('Invalid model identifier')
        for value, name in ((daily_budget_microusd, 'Daily budget'), (monthly_budget_microusd, 'Monthly budget')):
            self._integer(value, name)
        if provider == 'ollama':
            if isinstance(estimate_microusd, bool) or estimate_microusd not in (None, 0):
                raise ValueError('Local API usage has zero provider charge')
            estimate_microusd, basis = 0, 'local_api_zero'
        else:
            self._integer(estimate_microusd, 'Cost estimate', optional=True)
            if estimate_microusd is None or price_verified is not True:
                raise BudgetDenied('Cloud budget requires a verified maximum price quote')
            if not daily_budget_microusd or not monthly_budget_microusd:
                raise BudgetDenied('Cloud budget is zero or disabled')
            basis = 'verified_maximum_quote'
        now = self._now()
        day, month = now.strftime('%Y-%m-%d'), now.strftime('%Y-%m')
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT * FROM ai_usage WHERE request_id=?', (request_id,)).fetchone()
            if existing:
                if (existing['provider'], existing['model'], existing['reserved_microusd'], existing['pricing_basis']) != (provider, model, estimate_microusd, basis):
                    raise ValueError('Request ID belongs to a different reservation')
                db.commit()
                return False
            if provider != 'ollama':
                row = db.execute('''SELECT
                    COALESCE(SUM(CASE WHEN cost_microusd IS NULL THEN reserved_microusd WHEN period_day=? THEN cost_microusd ELSE 0 END),0) AS day,
                    COALESCE(SUM(CASE WHEN cost_microusd IS NULL THEN reserved_microusd WHEN period_month=? THEN cost_microusd ELSE 0 END),0) AS month
                    FROM ai_usage''', (day, month)).fetchone()
                if row['day'] + estimate_microusd > daily_budget_microusd or row['month'] + estimate_microusd > monthly_budget_microusd:
                    raise BudgetDenied('Cloud budget would exceed a reserved or settled limit')
            db.execute('INSERT INTO ai_usage(request_id,provider,model,state,reserved_microusd,pricing_basis,created_at,period_day,period_month) VALUES(?,?,?,?,?,?,?,?,?)',
                       (request_id, provider, model, 'reserved', estimate_microusd, basis, now.isoformat(), day, month))
            db.commit()
            return True

    def settle(self, request_id: str, *, prompt_tokens: int | None,
               completion_tokens: int | None, cost_microusd: int):
        self._integer(prompt_tokens, 'Prompt tokens', optional=True)
        self._integer(completion_tokens, 'Completion tokens', optional=True)
        self._integer(cost_microusd, 'Actual cost')
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM ai_usage WHERE request_id=?', (request_id,)).fetchone()
            if row is None:
                raise ValueError('Unknown reservation')
            if row['provider'] == 'ollama' and cost_microusd != 0:
                raise ValueError('Local API usage cannot have a provider charge')
            if row['state'] == 'completed':
                if (row['prompt_tokens'], row['completion_tokens'], row['cost_microusd']) != (prompt_tokens, completion_tokens, cost_microusd):
                    raise ValueError('A settled request cannot be rewritten')
                db.commit()
                return
            if row['state'] == 'failed':
                raise ValueError('A failed request cannot be completed')
            # Even an unexpected overrun must be recorded truthfully; subsequent
            # admissions count it instead of silently capping the actual charge.
            db.execute('UPDATE ai_usage SET state=?,prompt_tokens=?,completion_tokens=?,cost_microusd=?,settled_at=? WHERE request_id=?',
                       ('completed', prompt_tokens, completion_tokens, cost_microusd, self._now().isoformat(), request_id))
            db.commit()

    def fail(self, request_id: str):
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT provider,state FROM ai_usage WHERE request_id=?', (request_id,)).fetchone()
            if row is None:
                raise ValueError('Unknown reservation')
            if row['state'] != 'completed':
                local = row['provider'] == 'ollama'
                # An error/disconnect does not prove an external charge did not
                # happen. Preserve its full hold until explicit reconciliation.
                db.execute('UPDATE ai_usage SET state=?,cost_microusd=?,settled_at=? WHERE request_id=?',
                           ('failed' if local else 'uncertain', 0 if local else None, self._now().isoformat(), request_id))
            db.commit()

    def summary(self) -> dict:
        now = self._now()
        day, month = now.strftime('%Y-%m-%d'), now.strftime('%Y-%m')
        with self._connection() as db:
            db.execute('BEGIN')
            row = db.execute('''SELECT COUNT(*) AS attempts,
                COALESCE(SUM(state='completed'),0) AS completed,
                COALESCE(SUM(state='failed'),0) AS failed,
                COALESCE(SUM(state IN ('reserved','uncertain')),0) AS pending,
                COALESCE(SUM(state='completed' AND (prompt_tokens IS NULL OR completion_tokens IS NULL)),0) AS unknown_tokens,
                COALESCE(SUM(CASE WHEN state='completed' THEN COALESCE(prompt_tokens,0)+COALESCE(completion_tokens,0) ELSE 0 END),0) AS tokens,
                COALESCE(SUM(CASE WHEN period_day=? THEN COALESCE(cost_microusd,0) ELSE 0 END),0) AS daily,
                COALESCE(SUM(CASE WHEN period_month=? THEN COALESCE(cost_microusd,0) ELSE 0 END),0) AS monthly,
                COALESCE(SUM(CASE WHEN cost_microusd IS NULL THEN reserved_microusd ELSE 0 END),0) AS held
                FROM ai_usage''', (day, month)).fetchone()
            counts = {r['provider']: r['count'] for r in db.execute("SELECT provider,COUNT(*) AS count FROM ai_usage WHERE state='completed' GROUP BY provider")}
            coverage = db.execute('SELECT coverage_since FROM ai_ledger_meta WHERE singleton=1').fetchone()[0]
            db.commit()
        return {'total_attempts': row['attempts'], 'total_requests': row['completed'],
                'failed_requests': row['failed'], 'unresolved_requests': row['pending'],
                'requests_with_unknown_token_usage': row['unknown_tokens'], 'total_tokens': row['tokens'],
                'daily_spend_usd': row['daily']/1_000_000, 'monthly_spend_usd': row['monthly']/1_000_000,
                'unresolved_reserved_usd': row['held']/1_000_000, 'provider_counts': counts,
                'persistent': True, 'period_timezone': 'UTC', 'coverage_since': coverage,
                'cloud_execution_enabled': False,
                'cost_basis': 'Local provider API charge only; hardware and electricity are not priced.'}
