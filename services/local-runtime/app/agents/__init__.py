"""Agent registry and exports for the Javo Agents framework."""

from app.agents.base import BaseAgent
from app.agents.orchestrator import MasterAgent
from app.agents.growth_scientist import GrowthScientistAgent
from app.agents.content_factory import ContentFactoryAgent
from app.agents.smart_memory import SmartMemoryAgent
from app.agents.self_upgrading_engineer import SelfUpgradingEngineerAgent
from app.agents.telegram_agent import TelegramAgent
from app.agents.brand_manager import BrandManagerAgent
from app.agents.voice_agent import VoiceAgent
from app.agents.api_integration import APIIntegrationAgent
from app.agents.content_publisher import ContentPublisherAgent
from app.agents.community_manager import CommunityManagerAgent
from app.agents.account_guardian import AccountGuardianAgent
from app.agents.resource_optimizer import ResourceOptimizerAgent
from app.agents.quality_inspector import QualityInspectorAgent
from app.agents.niche_radar import NicheRadarAgent
from app.agents.approval_manager import ApprovalManagerAgent
from app.agents.budget_guardian import BudgetGuardianAgent
from app.agents.content_recycler import ContentRecyclerAgent
from app.agents.brand_studio import BrandStudioAgent
from app.agents.weekly_analyst import WeeklyAnalystAgent
from app.agents.recovery_agent import RecoveryAgent
from app.agents.plugin_trust import PluginTrustAgent
from app.agents.security_guardian import SecurityGuardianAgent
from app.agents.goal_persistence import GoalPersistenceAgent
from app.agents.workflow_automation import WorkflowAutomationAgent
from app.agents.reporting_agent import ReportingAgent
from app.agents.release_agent import ReleaseAgent
from app.agents.device_sync_agent import DeviceSyncAgent
from app.agents.ux_assistant import UXAssistantAgent
from app.agents.compliance_agent import ComplianceAgent

ALL_AGENT_CLASSES: list[type[BaseAgent]] = [
    GrowthScientistAgent,
    ContentFactoryAgent,
    SmartMemoryAgent,
    SelfUpgradingEngineerAgent,
    TelegramAgent,
    BrandManagerAgent,
    VoiceAgent,
    APIIntegrationAgent,
    ContentPublisherAgent,
    CommunityManagerAgent,
    AccountGuardianAgent,
    ResourceOptimizerAgent,
    QualityInspectorAgent,
    NicheRadarAgent,
    ApprovalManagerAgent,
    BudgetGuardianAgent,
    ContentRecyclerAgent,
    BrandStudioAgent,
    WeeklyAnalystAgent,
    RecoveryAgent,
    PluginTrustAgent,
    SecurityGuardianAgent,
    GoalPersistenceAgent,
    WorkflowAutomationAgent,
    ReportingAgent,
    ReleaseAgent,
    DeviceSyncAgent,
    UXAssistantAgent,
    ComplianceAgent,
]


def create_orchestrator() -> MasterAgent:
    """Instantiate MasterAgent and register all 29 specialist agents."""
    orchestrator = MasterAgent()
    for agent_cls in ALL_AGENT_CLASSES:
        orchestrator.register_agent(agent_cls())
    return orchestrator


def get_all_agents() -> dict[str, BaseAgent]:
    """Return a dict mapping agent name -> agent instance for all specialists + orchestrator."""
    orchestrator = create_orchestrator()
    agents: dict[str, BaseAgent] = {orchestrator.name: orchestrator}
    for agent_cls in ALL_AGENT_CLASSES:
        instance = orchestrator.get_agent(agent_cls.name)
        if instance is not None:
            agents[instance.name] = instance
    return agents


__all__ = [
    "BaseAgent",
    "MasterAgent",
    "ALL_AGENT_CLASSES",
    "create_orchestrator",
    "get_all_agents",
    "GrowthScientistAgent",
    "ContentFactoryAgent",
    "SmartMemoryAgent",
    "SelfUpgradingEngineerAgent",
    "TelegramAgent",
    "BrandManagerAgent",
    "VoiceAgent",
    "APIIntegrationAgent",
    "ContentPublisherAgent",
    "CommunityManagerAgent",
    "AccountGuardianAgent",
    "ResourceOptimizerAgent",
    "QualityInspectorAgent",
    "NicheRadarAgent",
    "ApprovalManagerAgent",
    "BudgetGuardianAgent",
    "ContentRecyclerAgent",
    "BrandStudioAgent",
    "WeeklyAnalystAgent",
    "RecoveryAgent",
    "PluginTrustAgent",
    "SecurityGuardianAgent",
    "GoalPersistenceAgent",
    "WorkflowAutomationAgent",
    "ReportingAgent",
    "ReleaseAgent",
    "DeviceSyncAgent",
    "UXAssistantAgent",
    "ComplianceAgent",
]
