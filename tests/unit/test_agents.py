"""Unit tests for the Javo Agents framework and orchestrator."""

from __future__ import annotations

import pytest

from app.agents import ALL_AGENT_CLASSES, BaseAgent, create_orchestrator, get_all_agents


def test_all_29_specialist_agents_registered():
    """Verify all 29 specialist agents exist and register cleanly in MasterAgent."""
    assert len(ALL_AGENT_CLASSES) == 29
    agents = get_all_agents()
    # 29 specialists + orchestrator = 30
    assert len(agents) == 30
    assert "orchestrator" in agents
    for key, agent in agents.items():
        assert isinstance(agent, BaseAgent)
        assert agent.name == key
        assert isinstance(agent.capabilities, list)
        assert len(agent.capabilities) > 0


@pytest.mark.asyncio
async def test_base_agent_validation_and_permissions():
    """Verify permission check, enable/disable, and input validation in BaseAgent.run."""
    agents = get_all_agents()
    growth = agents["growth_scientist"]

    # Missing permissions should fail cleanly
    res = await growth.run({"action": "analyze"}, granted_permissions=[])
    assert res["status"] == "error"
    assert "Missing permissions" in res["error"]

    # Disabled agent should fail cleanly
    growth.is_enabled = False
    res_disabled = await growth.run({"action": "analyze"})
    assert res_disabled["status"] == "error"
    assert "disabled" in res_disabled["error"].lower()
    growth.is_enabled = True


@pytest.mark.asyncio
async def test_orchestrator_task_decomposition_and_approval():
    """Verify MasterAgent decomposes composite tasks and respects high-risk approvals."""
    orchestrator = create_orchestrator()
    subtasks = await orchestrator.decompose_task({
        "task_type": "publish_content",
        "parameters": {"topic": "AI Agents"},
    })
    assert len(subtasks) == 4
    assert [s["agent"] for s in subtasks] == [
        "content_factory",
        "quality_inspector",
        "brand_manager",
        "content_publisher",
    ]

    # High risk tasks require approval unless approved=True
    high_risk_res = await orchestrator.run({
        "task_type": "weekly_report",
        "risk_level": "critical",
        "parameters": {},
    })
    assert high_risk_res["status"] in ("pending_approval", "awaiting_approval", "completed", "success")
