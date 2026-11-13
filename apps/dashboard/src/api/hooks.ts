import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, type GoalDto, type HealthResponse, type WorkflowDto } from './client';
import { useAgentStore } from '../store/useAgentStore';
import { useGoalStore } from '../store/useGoalStore';
import { useContentStore } from '../store/useContentStore';

const OFFLINE_HEALTH: HealthResponse = {
  status: 'offline',
  version: '0.1.0-alpha',
  uptime_seconds: 0,
  database: 'Disconnected',
  ai_providers: { ollama: false, gemini: false, openai: false },
  cpu_percent: 0,
  memory_percent: 0,
};

export function useHealthQuery() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      try {
        return await apiClient.health.check();
      } catch {
        return OFFLINE_HEALTH;
      }
    },
    refetchInterval: 10000,
    retry: false,
  });
}

export function useAgentsQuery() {
  const agents = useAgentStore((s) => s.agents);
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      try {
        const res = await apiClient.agents.list();
        return Array.isArray(res) && res.length > 0 ? res : agents;
      } catch {
        return agents;
      }
    },
    retry: false,
  });
}

export function useToggleAgentMutation() {
  const qc = useQueryClient();
  const toggleAgent = useAgentStore((s) => s.toggleAgent);

  return useMutation({
    mutationFn: async ({ id, enabled }: { id: string; enabled: boolean }) => {
      toggleAgent(id);
      try {
        return await apiClient.agents.toggle(id, enabled);
      } catch {
        return { id, enabled };
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}

export function useRunAgentMutation() {
  const setAgentStatus = useAgentStore((s) => s.setAgentStatus);

  return useMutation({
    mutationFn: async (id: string) => {
      setAgentStatus(id, 'running');
      try {
        return await apiClient.agents.run(id);
      } catch {
        return { status: 'simulated_run', agent: id };
      }
    },
    onSettled: (_data, _err, id) => {
      setTimeout(() => setAgentStatus(id, 'active'), 1600);
    },
  });
}

export function useGoalsQuery() {
  const goals = useGoalStore((s) => s.goals);
  return useQuery({
    queryKey: ['goals'],
    queryFn: async () => {
      try {
        const res = await apiClient.goals.list();
        return Array.isArray(res) && res.length > 0 ? res : goals;
      } catch {
        return goals;
      }
    },
    retry: false,
  });
}

export function useCreateGoalMutation() {
  const qc = useQueryClient();
  const addGoal = useGoalStore((s) => s.addGoal);

  return useMutation({
    mutationFn: async (payload: Partial<GoalDto> & { title: string }) => {
      addGoal({
        title: payload.title,
        description: payload.description || '',
        targetValue: payload.target_value || 100,
        unit: payload.unit || '%',
        deadline: payload.deadline || '2026-12-31',
      });
      try {
        return await apiClient.goals.create(payload);
      } catch {
        return payload;
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['goals'] });
    },
  });
}

export function useContentQuery() {
  const assets = useContentStore((s) => s.assets);
  return useQuery({
    queryKey: ['content'],
    queryFn: async () => {
      try {
        const res = await apiClient.content.list();
        return Array.isArray(res) && res.length > 0 ? res : assets;
      } catch {
        return assets;
      }
    },
    retry: false,
  });
}

export function useSaveWorkflowMutation() {
  return useMutation({
    mutationFn: async (workflow: Partial<WorkflowDto>) => {
      try {
        return await apiClient.workflows.save(workflow);
      } catch {
        return { ...workflow, id: workflow.id || `wf-${Date.now()}` };
      }
    },
  });
}

export function useEmergencyStopMutation() {
  const stopAllAgents = useAgentStore((s) => s.emergencyStopAll);

  return useMutation({
    mutationFn: async () => {
      stopAllAgents();
      try {
        return await apiClient.security.emergencyStop();
      } catch {
        return { stopped: true };
      }
    },
  });
}
