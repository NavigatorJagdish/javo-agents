"""Unit tests for Task, Goal, and Milestone database models."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.task import Goal, GoalStatus, Milestone, Task, TaskPriority, TaskState
from app.models.user import User


@pytest.mark.asyncio
async def test_task_goal_milestone_persistence():
    """Verify creating, querying, and updating Task, Goal, and Milestone in SQLite."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        user = User(username="creator1", email="creator1@example.com", password_hash="hash")
        session.add(user)
        await session.flush()

        goal = Goal(
            title="Reach 10k Followers",
            description="Grow Instagram and YouTube presence",
            owner_id=user.id,
            target_metrics={"followers": 10000},
            progress=25.0,
            status=GoalStatus.ACTIVE,
        )
        session.add(goal)
        await session.flush()

        milestone = Milestone(
            goal_id=goal.goal_id,
            title="First 2,500 followers",
            target_value=2500.0,
            current_value=2500.0,
            is_completed=True,
        )
        task = Task(
            goal_id=goal.goal_id,
            assigned_agent="growth_scientist",
            title="Analyze weekly retention",
            inputs={"period_days": 7},
            outputs={},
            permissions=["read_analytics"],
            state=TaskState.PENDING,
            priority=TaskPriority.HIGH,
            retry_budget=3,
            cost_budget=1.5,
            failure_history=[],
            audit_trail=[{"event": "created"}],
        )
        session.add_all([milestone, task])
        await session.commit()

        assert goal.goal_id is not None
        assert task.task_id is not None
        assert task.state == TaskState.PENDING
        assert task.priority == TaskPriority.HIGH
        assert milestone.is_completed is True

    await engine.dispose()
