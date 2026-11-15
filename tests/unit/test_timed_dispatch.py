"""Real synchronous SQLite policy checks; async worker/HTTP coverage is separate."""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.models.account import SocialAccount, Platform
from app.models.content import ContentAsset, ContentSchedule, AssetType
from app.models.publication import PublicationTimer, PublicationAttempt, PublicationApproval
from app.services import publishing, timed_dispatch as timed


def finish(coro):
    try:
        coro.send(None)
    except StopIteration as result:
        return result.value
    finally:
        coro.close()
    raise AssertionError("Unexpected IO in synchronous adapter")


class Adapter:
    def __init__(self, session):
        self.session = session

    def add(self, item):
        self.session.add(item)

    async def get(self, *args):
        return self.session.get(*args)

    async def execute(self, *args):
        return self.session.execute(*args)

    async def commit(self):
        self.session.commit()

    async def rollback(self):
        self.session.rollback()


@pytest.fixture
def setup(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        due = datetime(2030, 1, 1, 12)
        session.add_all(
            [
                SocialAccount(
                    id="account", user_id="owner", username="local", platform=Platform.OTHER
                ),
                ContentAsset(id="asset", user_id="owner", title="Test", asset_type=AssetType.TEXT),
                ContentSchedule(
                    id="schedule", asset_id="asset", account_id="account", scheduled_at=due
                ),
            ]
        )
        session.commit()
        adapter = Adapter(session)
        control = SimpleNamespace(_paused=False, _emergency_stopped=False)
        monkeypatch.setattr(timed, "get_resource_manager", lambda: control)
        monkeypatch.setattr(publishing, "get_resource_manager", lambda: control)
        approved = finish(publishing.approve_schedule(adapter, "schedule", "mock", "owner"))
        yield adapter, session, due, control, approved["fingerprint"]
    engine.dispose()


def arm(setup):
    adapter, _, due, _, fp = setup
    return finish(timed.arm_timer(adapter, "schedule", fp, now=due - timedelta(minutes=1)))


def test_future_timer_does_not_run_early(setup):
    adapter, session, due, _, _ = setup
    arm(setup)
    finish(timed.run_due(adapter, now=due - timedelta(seconds=1)))
    assert session.get(PublicationTimer, "schedule").state == "armed"
    assert session.scalars(select(PublicationAttempt)).all() == []


def test_due_timer_persists_one_simulation_receipt(setup):
    adapter, session, due, _, _ = setup
    arm(setup)
    finish(timed.run_due(adapter, now=due))
    session.expunge_all()
    assert session.get(PublicationTimer, "schedule").state == "simulated"
    finish(timed.run_due(adapter, now=due + timedelta(seconds=1)))
    attempts = session.scalars(select(PublicationAttempt)).all()
    assert len(attempts) == 1 and attempts[0].state == "simulated"


@pytest.mark.parametrize("reason", ["pause", "stop", "late", "changed", "revoked", "live"])
def test_unsafe_due_work_is_held_without_dispatch(setup, reason):
    adapter, session, due, control, _ = setup
    arm(setup)
    if reason == "pause":
        control._paused = True
    if reason == "stop":
        control._emergency_stopped = True
    if reason == "changed":
        session.get(ContentSchedule, "schedule").caption = "changed"
    if reason == "revoked":
        session.delete(session.get(PublicationApproval, "schedule"))
    if reason == "live":
        session.get(PublicationApproval, "schedule").mode = "live"
    session.commit()
    finish(timed.run_due(adapter, now=due + timedelta(seconds=31 if reason == "late" else 0)))
    assert session.get(PublicationTimer, "schedule").state == "held"
    assert session.scalars(select(PublicationAttempt)).all() == []
    control._paused = control._emergency_stopped = False
    finish(timed.run_due(adapter, now=due + timedelta(seconds=32)))
    assert session.scalars(select(PublicationAttempt)).all() == []


@pytest.mark.parametrize("state", ["armed", "executing"])
def test_restart_holds_due_or_inflight_work(setup, state):
    adapter, session, due, _, _ = setup
    arm(setup)
    session.get(PublicationTimer, "schedule").state = state
    session.commit()
    finish(timed.hold_after_restart(adapter, now=due))
    session.expunge_all()
    assert session.get(PublicationTimer, "schedule").state == "held"
    finish(timed.run_due(adapter, now=due))
    assert session.scalars(select(PublicationAttempt)).all() == []


def test_restart_preserves_future_armed_timer(setup):
    adapter, session, due, _, _ = setup
    arm(setup)
    finish(timed.hold_after_restart(adapter, now=due - timedelta(seconds=1)))
    assert session.get(PublicationTimer, "schedule").state == "armed"


def test_cancel_is_persistent_and_never_dispatches(setup):
    adapter, session, due, _, _ = setup
    arm(setup)
    assert finish(timed.cancel_timer(adapter, "schedule"))["state"] == "cancelled"
    session.expunge_all()
    finish(timed.run_due(adapter, now=due))
    assert session.get(PublicationTimer, "schedule").state == "cancelled"
    assert session.scalars(select(PublicationAttempt)).all() == []


@pytest.mark.parametrize("invalid", ["past", "fingerprint", "live", "attempted"])
def test_arm_rejects_invalid_authorization_or_past_schedule(setup, invalid):
    adapter, session, due, _, fp = setup
    now = due if invalid == "past" else due - timedelta(minutes=1)
    if invalid == "fingerprint":
        fp = "0" * 64
    if invalid == "live":
        session.get(PublicationApproval, "schedule").mode = "live"
    if invalid == "attempted":
        session.add(
            PublicationAttempt(
                id="attempt", schedule_id="schedule", dedupe_key="key", state="unknown", mode="mock"
            )
        )
    session.commit()
    with pytest.raises(HTTPException) as error:
        finish(timed.arm_timer(adapter, "schedule", fp, now=now))
    assert error.value.status_code == 409


def test_cancel_cannot_claim_executing_work_is_stopped(setup):
    adapter, session, _, _, _ = setup
    arm(setup)
    session.get(PublicationTimer, "schedule").state = "executing"
    session.commit()
    with pytest.raises(HTTPException) as error:
        finish(timed.cancel_timer(adapter, "schedule"))
    assert error.value.status_code == 409


def test_connector_failure_holds_timer_with_unknown_receipt(setup, monkeypatch):
    adapter, session, due, _, _ = setup
    arm(setup)

    class FailingConnector:
        def __init__(self, **kwargs):
            pass

        async def publish_post(self, payload):
            raise RuntimeError("Test connection failure")

    monkeypatch.setattr(publishing, "MockConnector", FailingConnector)
    finish(timed.run_due(adapter, now=due))
    assert session.get(PublicationTimer, "schedule").state == "held"
    attempt = session.scalars(select(PublicationAttempt)).one()
    assert attempt.state == "unknown"
    finish(timed.run_due(adapter, now=due + timedelta(seconds=1)))
    assert len(session.scalars(select(PublicationAttempt)).all()) == 1


def test_repeated_arm_reuses_timer_and_cancel_can_be_explicitly_rearmed(setup):
    adapter, session, _, _, _ = setup
    first = arm(setup)
    assert arm(setup) == first
    finish(timed.cancel_timer(adapter, "schedule"))
    assert arm(setup)["state"] == "armed"
    assert len(session.scalars(select(PublicationTimer)).all()) == 1
