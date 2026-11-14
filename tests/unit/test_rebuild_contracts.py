"""Rule/SQLite tests without socket-dependent event loops.

The adapter uses real SQLite transactions but not the production async driver;
async-driver, concurrent dispatch and HTTP lifecycle coverage remains separate.
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import secrets
import pytest
from fastapi import HTTPException
from pydantic import SecretStr, ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.database import Base
from app.models.account import SocialAccount, Platform
from app.models.content import ContentAsset, ContentSchedule, AssetType, ScheduleStatus
from app.models.publication import PublicationAttempt
from app.services import publishing
from app.core import local_auth
from app.core.resource_profiles import select_resource_profile
from app.api.routes.content import ScheduleCreate


def finish(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    finally:
        coroutine.close()
    raise AssertionError("Test adapter unexpectedly yielded IO")


class SQLiteAdapter:
    def __init__(self, session): self.session = session
    def add(self, item): self.session.add(item)
    async def get(self, *args): return self.session.get(*args)
    async def execute(self, *args): return self.session.execute(*args)
    async def commit(self): self.session.commit()
    async def rollback(self): self.session.rollback()


@pytest.fixture
def publication(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        session.add_all([
            SocialAccount(id="account", user_id="owner", username="test", platform=Platform.FACEBOOK),
            ContentAsset(id="asset", user_id="owner", title="Test", asset_type=AssetType.TEXT, content_text="Original"),
            ContentSchedule(id="schedule", asset_id="asset", account_id="account", scheduled_at=datetime(2030,1,1)),
        ])
        session.commit()
        manager = SimpleNamespace(_paused=False, _emergency_stopped=False)
        monkeypatch.setattr(publishing, "get_resource_manager", lambda: manager)
        yield SQLiteAdapter(session), session, manager
    engine.dispose()


def test_requires_explicit_approval(publication):
    adapter, _, _ = publication
    with pytest.raises(HTTPException) as error:
        finish(publishing.dispatch_schedule(adapter, "schedule"))
    assert error.value.status_code == 409


def test_receipt_survives_reload_and_is_never_published(publication):
    adapter, session, _ = publication
    finish(publishing.approve_schedule(adapter, "schedule", "mock", "owner"))
    first = finish(publishing.dispatch_schedule(adapter, "schedule"))
    session.expunge_all()
    second = finish(publishing.dispatch_schedule(adapter, "schedule"))
    assert first == second
    assert first["status"] == "simulated"
    assert session.get(ContentSchedule, "schedule").status == ScheduleStatus.APPROVED
    assert len(session.scalars(select(PublicationAttempt)).all()) == 1


@pytest.mark.parametrize("change", ["caption", "account", "media"])
def test_changed_approval_is_rejected(publication, tmp_path, change):
    adapter, session, _ = publication
    media = tmp_path / "media.txt"
    media.write_text("first")
    session.get(ContentAsset, "asset").file_path = str(media)
    session.commit()
    finish(publishing.approve_schedule(adapter, "schedule", "mock", "owner"))
    if change == "caption": session.get(ContentSchedule, "schedule").caption = "changed"
    elif change == "account": session.get(SocialAccount, "account").platform_user_id = "another-destination"
    else: media.write_text("second")
    session.commit()
    with pytest.raises(HTTPException, match="changed"):
        finish(publishing.dispatch_schedule(adapter, "schedule"))


def test_live_mode_does_not_simulate_success(publication):
    adapter, _, _ = publication
    finish(publishing.approve_schedule(adapter, "schedule", "live", "owner"))
    with pytest.raises(HTTPException) as error:
        finish(publishing.dispatch_schedule(adapter, "schedule"))
    assert error.value.status_code == 503


def test_pause_blocks_dispatch(publication):
    adapter, _, manager = publication
    finish(publishing.approve_schedule(adapter, "schedule", "mock", "owner"))
    manager._paused = True
    with pytest.raises(HTTPException, match="paused"):
        finish(publishing.dispatch_schedule(adapter, "schedule"))


def test_duplicate_payload_blocks_second_schedule(publication):
    adapter, session, _ = publication
    finish(publishing.approve_schedule(adapter, "schedule", "mock", "owner"))
    finish(publishing.dispatch_schedule(adapter, "schedule"))
    session.add(ContentSchedule(id="second", asset_id="asset", account_id="account", scheduled_at=datetime(2030,2,1)))
    session.commit()
    finish(publishing.approve_schedule(adapter, "second", "mock", "owner"))
    with pytest.raises(HTTPException, match="Duplicate"):
        finish(publishing.dispatch_schedule(adapter, "second"))


def test_unknown_connector_outcome_blocks_retry(publication, monkeypatch):
    adapter, session, _ = publication
    class FailingConnector:
        def __init__(self, **kwargs): pass
        async def publish_post(self, payload): raise TimeoutError()
    monkeypatch.setattr(publishing, "MockConnector", FailingConnector)
    finish(publishing.approve_schedule(adapter, "schedule", "mock", "owner"))
    with pytest.raises(HTTPException) as error:
        finish(publishing.dispatch_schedule(adapter, "schedule"))
    assert error.value.status_code == 502
    assert session.scalar(select(PublicationAttempt)).state == "unknown"
    with pytest.raises(HTTPException, match="unresolved"):
        finish(publishing.dispatch_schedule(adapter, "schedule"))


def test_owner_token_validation(monkeypatch):
    token = secrets.token_urlsafe(32)
    settings = SimpleNamespace(owner_access_token=SecretStr(token))
    monkeypatch.setattr(local_auth, "get_settings", lambda: settings)
    assert local_auth.is_valid_owner_token("Bearer " + token)
    for header in [None, "", "Basic " + token, "Bearer wrong", "Bearer \u2603"]:
        assert not local_auth.is_valid_owner_token(header)
    settings.owner_access_token = None
    assert not local_auth.is_valid_owner_token("Bearer " + token)


def test_resource_profiles_scale_beyond_8gb():
    low = select_resource_profile(8192, 8)
    large = select_resource_profile(65536, 16)
    assert low.baseline_met and low.max_concurrent_agents == 1
    assert large.max_concurrent_agents > low.max_concurrent_agents
    assert large.recommended_model_budget_mb > 0
    assert not select_resource_profile(4096, 4).baseline_met


@pytest.mark.parametrize("memory", [0, -1, float("nan"), float("inf")])
def test_invalid_hardware_is_rejected(memory):
    with pytest.raises(ValueError): select_resource_profile(memory, 4)


def test_schedule_requires_future_timezone():
    for when in [datetime(2030,1,1), datetime.now(timezone.utc)-timedelta(days=1)]:
        with pytest.raises(ValidationError):
            ScheduleCreate(asset_id="asset", account_id="account", scheduled_at=when)
    assert ScheduleCreate(asset_id="asset", account_id="account", scheduled_at=datetime.now(timezone.utc)+timedelta(days=1))


def test_high_risk_without_manager_is_not_approved():
    from app.agents.orchestrator import MasterAgent
    assert finish(MasterAgent().check_approval({"task_type": "publish", "risk_level": "high"})) is False


def test_caller_approved_flag_cannot_bypass_review():
    from app.agents.orchestrator import MasterAgent
    result = finish(MasterAgent().execute({"task_type": "publish", "risk_level": "high", "approved": True}))
    assert result["status"] == "pending_approval"
    assert result["remaining_subtasks"]


def test_control_routes_are_registered_under_both_prefixes():
    from app.main import create_app
    paths = create_app().openapi()["paths"]
    for path in ["/security/emergency-stop", "/api/security/emergency-stop", "/content/schedule/{schedule_id}/approve"]:
        assert path in paths


def test_missed_scheduler_job_is_held():
    from app.core.scheduler import SchedulerService
    scheduler = SchedulerService()
    held = []
    scheduler._scheduler = SimpleNamespace(
        get_jobs=lambda: [SimpleNamespace(id="missed", next_run_time=datetime.now(timezone.utc)-timedelta(minutes=5)),
                         SimpleNamespace(id="future", next_run_time=datetime.now(timezone.utc)+timedelta(minutes=5))],
        pause_job=held.append)
    scheduler._reconcile_jobs()
    assert held == ["missed"]



def test_stale_review_cannot_approve_changed_payload(publication):
    adapter, session, _ = publication
    _, snapshot = finish(publishing.load_snapshot(adapter, "schedule"))
    reviewed = publishing.fingerprint_payload(snapshot)
    session.get(ContentSchedule, "schedule").caption = "Changed after preview"
    session.commit()
    with pytest.raises(HTTPException, match="Preview changed"):
        finish(publishing.approve_schedule(adapter, "schedule", "mock", "owner", reviewed))
    assert session.get(ContentSchedule, "schedule").status == ScheduleStatus.PENDING


def test_preview_and_persisted_receipt_endpoints(publication):
    from app.api.routes.content import preview_schedule, publication_receipt
    adapter, session, _ = publication
    preview = finish(preview_schedule("schedule", adapter))
    assert preview["fingerprint"] == publishing.fingerprint_payload(preview["snapshot"])
    finish(publishing.approve_schedule(adapter, "schedule", "mock", "owner", preview["fingerprint"]))
    dispatched = finish(publishing.dispatch_schedule(adapter, "schedule"))
    session.expunge_all()
    assert finish(publication_receipt("schedule", adapter)) == dispatched


def test_receipt_endpoint_does_not_invent_success(publication):
    from app.api.routes.content import publication_receipt
    adapter, _, _ = publication
    with pytest.raises(HTTPException) as error:
        finish(publication_receipt("schedule", adapter))
    assert error.value.status_code == 404


def test_approval_request_requires_review_fingerprint():
    from app.api.routes.content import ApprovalRequest
    with pytest.raises(ValidationError): ApprovalRequest(mode="mock")
    with pytest.raises(ValidationError): ApprovalRequest(mode="mock", fingerprint="invalid")
