import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient, type GoalDto, type WorkflowDto } from './client';

// Errors must reach callers; a failed command is never replaced with demo success.
export function useHealthQuery() {
  return useQuery({ queryKey: ['health'], queryFn: apiClient.health.check, refetchInterval: 15000, retry: false });
}
export function useAgentsQuery() {
  return useQuery({ queryKey: ['agents'], queryFn: apiClient.agents.list, retry: false });
}
export function useToggleAgentMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) => apiClient.agents.toggle(id, enabled),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['agents'] }); },
  });
}
export function useRunAgentMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => apiClient.agents.run(id),
    onSettled: () => { qc.invalidateQueries({ queryKey: ['agents'] }); } });
}
export function useGoalsQuery() {
  return useQuery({ queryKey: ['goals'], queryFn: apiClient.goals.list, retry: false });
}
export function useCreateGoalMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (payload: Partial<GoalDto> & { title: string }) => apiClient.goals.create(payload),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['goals'] }); } });
}
export function useContentQuery() {
  return useQuery({ queryKey: ['content'], queryFn: apiClient.content.list, retry: false });
}
export function useSaveWorkflowMutation() {
  return useMutation({ mutationFn: (workflow: Partial<WorkflowDto>) => apiClient.workflows.save(workflow) });
}
export function useEmergencyStopMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: apiClient.security.emergencyStop,
    onSuccess: () => { qc.invalidateQueries(); } });
}
