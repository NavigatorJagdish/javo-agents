"""AI-assisted goal decomposition, milestone tracking, and analytics evaluation service."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import get_all_agents
from app.models.analytics import Metric
from app.models.task import Goal, Milestone, Task, TaskPriority, TaskState


def _infer_numeric_target(goal: Goal) -> tuple[str, float, int]:
    """Infer metric name, numeric target, and horizon days from goal metadata or title."""
    tm = dict(goal.target_metrics or {})
    metric_name = "views"
    target_val = 0.0
    days = int(tm.get("days", 30) or 30)

    for key in ("views", "reach", "impressions", "followers", "subscribers", "target"):
        if key in tm and isinstance(tm[key], (int, float)) and float(tm[key]) > 0:
            metric_name = "views" if key == "target" else key
            target_val = float(tm[key])
            break

    if target_val <= 0:
        title_lower = f"{goal.title} {goal.description or ''}".lower()
        m_mil = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|million)\s*(views|impressions|reach|followers)?", title_lower)
        m_k = re.search(r"(\d+(?:\.\d+)?)\s*(?:k|thousand)\s*(views|impressions|reach|followers)?", title_lower)
        m_num = re.search(r"(\d{3,})\s*(views|impressions|reach|followers)", title_lower)
        if m_mil:
            target_val = float(m_mil.group(1)) * 1_000_000.0
            metric_name = m_mil.group(2) or "views"
        elif m_k:
            target_val = float(m_k.group(1)) * 1_000.0
            metric_name = m_k.group(2) or "views"
        elif m_num:
            target_val = float(m_num.group(1))
            metric_name = m_num.group(2) or "views"
        else:
            target_val = 100.0

        m_days = re.search(r"(\d+)\s*days?", title_lower)
        if m_days:
            days = max(1, int(m_days.group(1)))

    return metric_name, target_val, days


async def plan_goal_for_id(
    goal_id: str,
    session: AsyncSession,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Decompose a goal into persisted milestones and zero-cost permitted tasks."""
    result = await session.execute(select(Goal).where(Goal.goal_id == goal_id))
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Goal '{goal_id}' not found")

    extra = extra or {}
    regenerate = bool(extra.get("regenerate", False))
    metric_name, target_val, days = _infer_numeric_target(goal)

    agents = get_all_agents()
    gp_agent = agents.get("goal_persistence")
    agent_plan: dict[str, Any] = {}
    if gp_agent is not None:
        agent_plan = await gp_agent.run(
            {
                "goal": goal.title,
                "description": goal.description or "",
                "target_metrics": {metric_name: target_val, "days": days, **(goal.target_metrics or {})},
                "zero_cost_only": True,
                "approved_content_only": True,
            }
        )

    existing_ms_res = await session.execute(select(Milestone).where(Milestone.goal_id == goal_id))
    existing_milestones = list(existing_ms_res.scalars().all())

    created_milestones: list[Milestone] = []
    if regenerate or not existing_milestones:
        now = datetime.now(timezone.utc)
        fractions = [
            (0.10, max(1, days // 4), f"Phase 1: Content batch & baseline ({int(target_val * 0.10):,} {metric_name})"),
            (0.35, max(2, days // 2), f"Phase 2: Hook A/B experiments ({int(target_val * 0.35):,} {metric_name})"),
            (0.70, max(3, (days * 3) // 4), f"Phase 3: Scale winning formats ({int(target_val * 0.70):,} {metric_name})"),
            (1.00, days, f"Phase 4: Target review ({int(target_val):,} {metric_name})"),
        ]
        for frac, due_days, title in fractions:
            ms = Milestone(
                id=str(uuid4()),
                goal_id=goal_id,
                title=title,
                target_value=round(target_val * frac, 2),
                current_value=0.0,
                is_completed=False,
                due_date=now + timedelta(days=due_days),
            )
            session.add(ms)
            created_milestones.append(ms)
    else:
        created_milestones = existing_milestones

    existing_tasks_res = await session.execute(select(Task).where(Task.goal_id == goal_id))
    existing_tasks = list(existing_tasks_res.scalars().all())

    created_tasks: list[Task] = []
    if regenerate or not existing_tasks:
        task_specs = [
            (
                "Scan & draft approved content variants",
                "content_creator",
                TaskPriority.HIGH,
                {"topic": goal.title, "approved_only": True, "zero_cost_only": True},
            ),
            (
                "Inspect draft quality & compliance before approval",
                "quality_inspector",
                TaskPriority.HIGH,
                {"goal_id": goal_id, "requires_human_approval": True},
            ),
            (
                "Design growth A/B hook experiment",
                "growth_scientist",
                TaskPriority.NORMAL,
                {"metric": metric_name, "target": target_val, "days": days},
            ),
            (
                "Collect baseline engagement metrics",
                "analytics_interpreter",
                TaskPriority.NORMAL,
                {"goal_id": goal_id, "metric": metric_name},
            ),
        ]
        for title, assigned_agent, prio, inputs in task_specs:
            task = Task(
                task_id=str(uuid4()),
                goal_id=goal_id,
                assigned_agent=assigned_agent,
                title=title,
                description=f"Auto-planned for goal '{goal.title}' (zero-cost AI budget).",
                inputs=inputs,
                permissions={"granted": ["content:draft", "analytics:read"], "requires_approval": ["publish"]},
                state=TaskState.PENDING,
                priority=prio,
                cost_budget=0.0,
            )
            session.add(task)
            created_tasks.append(task)
    else:
        created_tasks = existing_tasks

    await session.commit()

    return {
        "goal_id": goal_id,
        "metric": metric_name,
        "target_value": target_val,
        "horizon_days": days,
        "ai_budget_usd": 0.0,
        "guarantee_disclaimer": (
            "Milestones are planning targets generated on a $0 AI budget; external reach and views "
            "depend on platform distribution and human-approved publishing."
        ),
        "agent_plan": agent_plan,
        "milestones": [
            {
                "id": m.id,
                "title": m.title,
                "target_value": m.target_value,
                "current_value": m.current_value,
                "is_completed": m.is_completed,
            }
            for m in created_milestones
        ],
        "tasks": [
            {
                "task_id": t.task_id,
                "title": t.title,
                "assigned_agent": t.assigned_agent,
                "state": t.state.value if isinstance(t.state, TaskState) else str(t.state),
                "cost_budget": t.cost_budget,
            }
            for t in created_tasks
        ],
    }


async def evaluate_goal_for_id(goal_id: str, session: AsyncSession) -> dict[str, Any]:
    """Evaluate a goal against recorded analytics metrics and revise strategy on underperformance."""
    result = await session.execute(select(Goal).where(Goal.goal_id == goal_id))
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Goal '{goal_id}' not found")

    metric_name, target_val, days = _infer_numeric_target(goal)

    ms_res = await session.execute(select(Milestone).where(Milestone.goal_id == goal_id))
    milestones = list(ms_res.scalars().all())

    tasks_res = await session.execute(select(Task).where(Task.goal_id == goal_id))
    tasks = list(tasks_res.scalars().all())

    metrics_res = await session.execute(select(Metric).order_by(Metric.recorded_at.desc()).limit(200))
    metrics = list(metrics_res.scalars().all())

    matching = [m for m in metrics if m.name.lower() in {metric_name.lower(), "views", "impressions", "reach"}]
    observed_total = round(sum(float(m.value) for m in matching), 2) if matching else 0.0

    for ms in milestones:
        if matching:
            ms.current_value = observed_total
            if ms.target_value > 0 and observed_total >= ms.target_value:
                ms.is_completed = True

    if milestones:
        completed_ms = sum(1 for m in milestones if m.is_completed)
        ms_ratio = completed_ms / len(milestones)
    else:
        completed_ms = 0
        ms_ratio = 0.0

    metric_ratio = min(1.0, observed_total / target_val) if target_val > 0 else 0.0
    task_done = sum(1 for t in tasks if t.state == TaskState.COMPLETED)
    task_ratio = (task_done / len(tasks)) if tasks else 0.0

    if matching:
        progress = round(min(100.0, (metric_ratio * 0.7 + ms_ratio * 0.2 + task_ratio * 0.1) * 100.0), 2)
    else:
        progress = round(min(100.0, (ms_ratio * 0.5 + task_ratio * 0.5) * 100.0), 2)

    goal.progress = progress

    # Detect underperformance if elapsed ratio exceeds achieved ratio, or 0 metrics with completed tasks
    elapsed_days = max(1.0, (datetime.now(timezone.utc) - goal.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 86400.0) if goal.created_at else 1.0
    expected_ratio = min(1.0, elapsed_days / max(1, days))
    underperforming = (metric_ratio < expected_ratio * 0.5) or (len(matching) > 0 and observed_total < target_val * 0.25)

    agents = get_all_agents()
    growth_agent = agents.get("growth_scientist")
    growth_analysis: dict[str, Any] = {}
    if growth_agent is not None:
        growth_analysis = await growth_agent.run(
            {
                "action": "evaluate_goal",
                "metric": metric_name,
                "observed_value": observed_total,
                "target_value": target_val,
                "underperforming": underperforming,
                "sample_count": len(matching),
            }
        )

    recommendations: list[str] = []
    if not matching:
        recommendations.append(
            "No live platform metrics recorded yet; ingest analytics metrics or publish approved posts to measure reach."
        )
    elif underperforming:
        recommendations.extend(
            [
                f"Observed {observed_total:,.0f} {metric_name} vs {target_val:,.0f} target: test 2 new opening hooks in short-form format.",
                "Shift posting schedule toward top-performing engagement windows found in Analytics snapshots.",
            ]
        )
    else:
        recommendations.append(
            f"Pace is on track ({observed_total:,.0f}/{target_val:,.0f} {metric_name}); replicate top-performing variant."
        )

    await session.commit()

    return {
        "goal_id": goal_id,
        "metric": metric_name,
        "target_value": target_val,
        "observed_value": observed_total,
        "data_source": "recorded_metrics" if matching else "no_metrics_recorded",
        "progress": goal.progress,
        "milestones_completed": completed_ms,
        "milestones_total": len(milestones),
        "tasks_completed": task_done,
        "tasks_total": len(tasks),
        "underperforming": underperforming,
        "recommendations": recommendations,
        "growth_analysis": growth_analysis,
    }
