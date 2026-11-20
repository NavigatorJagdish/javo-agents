import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, Badge, Button, Modal } from '@javo/design-system';
import { apiClient, apiRequest, type GoalDto } from '../api/client';
import {
  useAgentsQuery,
  useGoalsQuery,
  useToggleAgentMutation,
} from '../api/hooks';

function SavedResult({ value }: { value: Record<string, unknown> }) {
  const goal = value.goal as GoalDto | undefined;
  const usage = value.usage as
    | {
        total_requests?: number;
        total_tokens?: number;
        requests_with_unknown_token_usage?: number;
      }
    | undefined;
  if (goal && typeof goal.title === 'string')
    return (
      <div className="space-y-2 mt-3 text-sm">
        <h4 className="font-semibold">{goal.title}</h4>
        <p>
          Saved progress: {goal.progress}% · Status: {goal.status}
        </p>
        <p>
          Milestones: {goal.completed_milestones} of {goal.total_milestones}{' '}
          completed
        </p>
        {goal.measurement && (
          <p>
            Manual measurement: {goal.measurement.value} {goal.objective?.unit}{' '}
            · Source: {goal.measurement.source}
          </p>
        )}
        <p className="text-slate-500">
          This is a saved snapshot of owner-reported evidence, not live account
          analytics.
        </p>
      </div>
    );
  if (usage)
    return (
      <div className="space-y-2 mt-3 text-sm">
        <p>Completed AI requests: {usage.total_requests ?? 'Unavailable'}</p>
        <p>Reported tokens: {usage.total_tokens ?? 'Unavailable'}</p>
        <p>
          Requests with unknown token counts:{' '}
          {usage.requests_with_unknown_token_usage ?? 'Unavailable'}
        </p>
        <p>
          Cloud execution is disabled. This summary does not activate a provider
          or spend money.
        </p>
      </div>
    );
  return (
    <p className="text-sm">
      A readable result is unavailable for this receipt.
    </p>
  );
}

export const AITeam: React.FC = () => {
  const agents = useAgentsQuery();
  const [search, setSearch] = useState('');
  const [selectedKey, setSelectedKey] = useState('');
  const [goalOffset, setGoalOffset] = useState(0);
  const [goalId, setGoalId] = useState('');
  const selected = agents.data?.find(
    (agent) => agent.agent_key === selectedKey,
  );
  const goals = useGoalsQuery(
    goalOffset,
    selected?.agent_key === 'goal_persistence',
  );
  const qc = useQueryClient();
  const toggle = useToggleAgentMutation();
  const control = useQuery({
    queryKey: ['agent-job-controls'],
    queryFn: () =>
      apiRequest<{ paused: boolean; emergency_stopped: boolean }>(
        '/api/security/autopilot-status',
      ),
    retry: false,
    refetchInterval: 2000,
  });
  const history = useQuery({
    queryKey: ['agent-executions', selectedKey],
    enabled: !!selected,
    queryFn: () => apiClient.agents.executions(selectedKey),
    retry: false,
    refetchInterval: 1000,
  });
  const run = useMutation({
    mutationFn: ({
      key,
      payload,
    }: {
      key: string;
      payload: Record<string, unknown>;
    }) => apiClient.agents.run(key, payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['agent-executions'] });
    },
  });
  const cancel = useMutation({
    mutationFn: ({ key, id }: { key: string; id: string }) =>
      apiClient.agents.cancelExecution(key, id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['agent-executions'] });
    },
  });
  const filtered =
    agents.data?.filter((agent) =>
      `${agent.name} ${agent.description ?? ''}`
        .toLowerCase()
        .includes(search.trim().toLowerCase()),
    ) ?? [];
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">AI Team</h1>
        <p className="mt-1 text-sm text-slate-500">
          {agents.data?.length ?? '—'} registered modules. Supported operations
          have real execution receipts; registration alone does not mean a
          feature is complete.
        </p>
      </div>
      <label className="block">
        <span className="text-sm">Filter AI agents</span>
        <input
          aria-label="Filter AI agents"
          className="block w-full rounded-xl border border-slate-300 dark:border-white/20 bg-white dark:bg-[#131C40] p-3 mt-1"
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </label>
      {agents.isPending && (
        <p role="status">Loading saved agent definitions…</p>
      )}
      {agents.isError && (
        <p role="alert">
          Agent definitions could not be loaded.{' '}
          <Button onClick={() => void agents.refetch()}>Retry agents</Button>
        </p>
      )}
      {toggle.isError && (
        <p role="alert">
          Agent enable/disable was not confirmed by the runtime.
        </p>
      )}
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((agent) => (
          <Card key={agent.agent_key}>
            <div className="flex items-start justify-between gap-3">
              <h2 className="font-semibold">{agent.name}</h2>
              <Badge
                status={
                  !agent.is_enabled
                    ? 'inactive'
                    : agent.status === 'running'
                      ? 'active'
                      : 'info'
                }
              >
                {agent.is_enabled ? agent.status : 'disabled'}
              </Badge>
            </div>
            <p className="text-sm mt-3">{agent.description}</p>
            <p className="text-xs mt-2 text-slate-500">
              Version {agent.version}
            </p>
            <p className="text-sm mt-3">
              {agent.supported_actions.length
                ? `Available: ${agent.supported_actions.join(', ').replaceAll('_', ' ')}`
                : 'Execution is not yet available for this module.'}
            </p>
            <div className="flex flex-wrap gap-2 mt-4">
              <Button
                variant="secondary"
                onClick={() => {
                  setSelectedKey(agent.agent_key);
                  setGoalId('');
                  run.reset();
                  cancel.reset();
                }}
              >
                Inspect {agent.name}
              </Button>
              <Button
                variant="ghost"
                disabled={toggle.isPending}
                onClick={() =>
                  toggle.mutate({
                    id: agent.agent_key,
                    enabled: !agent.is_enabled,
                  })
                }
              >
                {agent.is_enabled ? 'Disable' : 'Enable'} {agent.name}
              </Button>
            </div>
          </Card>
        ))}
      </div>
      {agents.isSuccess && !filtered.length && (
        <p>No modules match this filter.</p>
      )}
      <Modal
        open={!!selected}
        onClose={() => setSelectedKey('')}
        title={selected?.name}
        size="lg"
        description="Saved definitions and actual execution history."
      >
        {selected && (
          <div className="space-y-4">
            <p>{selected.description}</p>
            {!selected.supported_actions.length ? (
              <p>
                This module is still under development. No runnable operation or
                successful result is being claimed.
              </p>
            ) : (
              <>
                <p className="text-sm">
                  Available operations read local saved data. They do not call a
                  model, publish content, modify account settings or activate
                  spending.
                </p>
                {control.isError && (
                  <p role="alert">Runtime control state is unavailable.</p>
                )}
                {(control.data?.paused || control.data?.emergency_stopped) && (
                  <p role="status">
                    Runtime is paused or stopped. Queued operations wait for an
                    explicit resume from the main controls.
                  </p>
                )}
                {selected.agent_key === 'goal_persistence' && (
                  <div className="space-y-2">
                    <label className="block">
                      Saved goal
                      <select
                        aria-label="Saved goal"
                        className="block w-full rounded-lg p-2 border bg-white dark:bg-slate-900"
                        value={goalId}
                        onChange={(e) => setGoalId(e.target.value)}
                      >
                        <option value="">Choose a saved goal</option>
                        {goals.data?.map((goal) => (
                          <option key={goal.goal_id} value={goal.goal_id}>
                            {goal.title}
                          </option>
                        ))}
                      </select>
                    </label>
                    {goals.isError && <p role="alert">Goals unavailable.</p>}
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        disabled={!goalOffset}
                        onClick={() => {
                          setGoalOffset(Math.max(0, goalOffset - 50));
                          setGoalId('');
                        }}
                      >
                        Previous goals
                      </Button>
                      <Button
                        variant="ghost"
                        disabled={(goals.data?.length ?? 0) < 50}
                        onClick={() => {
                          setGoalOffset(goalOffset + 50);
                          setGoalId('');
                        }}
                      >
                        Next goals
                      </Button>
                    </div>
                  </div>
                )}
                <Button
                  disabled={
                    !selected.is_enabled ||
                    !control.data ||
                    run.isPending ||
                    control.data?.emergency_stopped ||
                    (selected.agent_key === 'goal_persistence' && !goalId)
                  }
                  onClick={() =>
                    run.mutate({
                      key: selected.agent_key,
                      payload:
                        selected.agent_key === 'goal_persistence'
                          ? { action: 'summary', goal_id: goalId }
                          : { action: 'summary' },
                    })
                  }
                >
                  Queue saved summary
                </Button>
                {run.isSuccess && (
                  <p role="status">
                    Operation queued. Completion is shown in its execution
                    receipt below.
                  </p>
                )}
                {run.isError && (
                  <p role="alert">
                    Operation was not queued. Check runtime controls and
                    selected data.
                  </p>
                )}
              </>
            )}
            <h3 className="font-semibold">Recent execution receipts</h3>
            {history.isPending && <p>Loading saved executions…</p>}
            {history.isError && (
              <p role="alert">Execution history unavailable.</p>
            )}
            {history.isSuccess && !history.data.length && (
              <p>No saved executions for this module.</p>
            )}
            <div className="space-y-3">
              {history.data?.map((item) => (
                <section
                  key={item.id}
                  aria-label={`Execution ${item.id}`}
                  className="border border-slate-300 dark:border-white/15 rounded-xl p-3 space-y-2"
                >
                  <p className="font-medium">Execution: {item.status}</p>
                  <p className="text-xs text-slate-500">
                    Requested{' '}
                    {new Date(item.created_at).toLocaleString('en-IN', {
                      timeZone: 'Asia/Kolkata',
                    })}{' '}
                    IST
                  </p>
                  {item.error && (
                    <p className="text-sm text-red-500">{item.error}</p>
                  )}
                  {(item.status === 'queued' || item.status === 'running') && (
                    <Button
                      variant="ghost"
                      disabled={cancel.isPending}
                      onClick={() =>
                        cancel.mutate({ key: selected.agent_key, id: item.id })
                      }
                    >
                      Cancel operation
                    </Button>
                  )}
                  {item.outputs && (
                    <details>
                      <summary className="cursor-pointer text-sm font-medium">
                        View saved result
                      </summary>
                      <SavedResult value={item.outputs} />
                    </details>
                  )}
                </section>
              ))}
            </div>
            {cancel.isError && (
              <p role="alert">
                Cancellation was not confirmed. Reload the execution receipt.
              </p>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};
