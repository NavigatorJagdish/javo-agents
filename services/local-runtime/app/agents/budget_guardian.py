"""Read durable router accounting; callers cannot manufacture a spend receipt."""
from app.agents.base import BaseAgent
from app.core.ai_router import get_ai_router


class BudgetGuardianAgent(BaseAgent):
    name = 'budget_guardian'
    display_name = 'Budget Guardian'
    description = 'Reports persisted API usage and the current zero-cost execution policy.'
    version = '1.1.0'
    capabilities = ['budget_tracking', 'cost_enforcement']
    required_permissions = ['read_usage', 'enforce_budget']
    input_schema = {'required': ['action'], 'properties': {'action': {'type': 'string'}, 'provider': {'type': 'string'}}}
    output_schema = {'required': ['status', 'allowed']}

    async def execute(self, task_data: dict) -> dict:
        if task_data.get('action') not in {'summary', 'check_budget'}:
            raise ValueError('Only summary/check_budget are supported; actual provider execution records usage')
        if {'spent_usd', 'budget_usd', 'estimated_cost_usd'} & task_data.keys():
            raise ValueError('Caller-provided costs cannot replace persisted accounting or spending policy')
        provider = task_data.get('provider', 'ollama')
        if provider not in {'ollama', 'gemini', 'openai'}:
            raise ValueError('Unsupported provider')
        router = get_ai_router()
        usage = router.get_provider_status()['usage']
        try:
            router._check_budget(provider)
            allowed = True
        except RuntimeError:
            allowed = False
        return {'status': 'success', 'allowed': allowed, 'provider': provider,
                'usage': usage, 'cloud_execution_enabled': False,
                'recommendation': 'local_api_has_no_provider_charge' if allowed else 'cloud_execution_disabled',
                'message': 'This is a budget check only; provider availability and resource admission are separate.'}
