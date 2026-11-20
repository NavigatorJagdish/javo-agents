import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Target, Trash2 } from 'lucide-react';
import { Card, Badge, Button, Modal } from '@javo/design-system';
import {
  apiClient,
  type GoalDto,
  type GoalObjective,
  type MilestoneDto,
} from '../api/client';
import { useCreateGoalMutation, useGoalsQuery } from '../api/hooks';
import { useAppStore } from '../store/useAppStore';

const inputClass =
  'w-full rounded-xl border border-slate-300 dark:border-white/20 bg-white dark:bg-[#0B1026] px-3 py-2 text-sm';
const istEndOfDay = (value: string) =>
  value ? `${value}T23:59:59+05:30` : null;
const istDate = (value: string | null) =>
  value
    ? new Date(value).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata' })
    : 'No deadline';
const dateInput = (value: string | null) =>
  value
    ? new Date(value).toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' })
    : '';

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-1">
      <span className="text-sm">{label}</span>
      {children}
    </label>
  );
}

function MilestoneRow({
  goalId,
  milestone,
  onSaved,
}: {
  goalId: string;
  milestone: MilestoneDto;
  onSaved: () => void;
}) {
  const [value, setValue] = useState(String(milestone.current_value));
  const [remove, setRemove] = useState(false);
  const save = useMutation({
    mutationFn: () =>
      apiClient.goals.updateMilestone(goalId, milestone.id, {
        current_value: Number(value),
      }),
    onSuccess: onSaved,
  });
  const deletion = useMutation({
    mutationFn: () => apiClient.goals.removeMilestone(goalId, milestone.id),
    onSuccess: onSaved,
  });
  return (
    <div className="rounded-xl border border-slate-200 dark:border-white/15 p-3 space-y-2">
      <p className="font-medium">
        {milestone.title} {milestone.is_completed ? '✓ Completed' : ''}
      </p>
      <p className="text-xs text-slate-500">
        Target {milestone.target_value} · {istDate(milestone.due_date)}
      </p>
      <form
        className="flex flex-wrap items-end gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <Field label={`Current value for ${milestone.title}`}>
          <input
            className={inputClass}
            type="number"
            step="any"
            min="0"
            required
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        </Field>
        <Button type="submit" disabled={save.isPending}>
          Save milestone
        </Button>
        <Button type="button" variant="ghost" onClick={() => setRemove(true)}>
          Remove milestone
        </Button>
      </form>
      {remove && (
        <div className="flex flex-wrap items-center gap-2">
          <span>Remove this milestone?</span>
          <Button
            disabled={deletion.isPending}
            onClick={() => deletion.mutate()}
          >
            Confirm milestone removal
          </Button>
          <Button variant="ghost" onClick={() => setRemove(false)}>
            Keep milestone
          </Button>
        </div>
      )}
      {(save.isError || deletion.isError) && (
        <p role="alert" className="text-red-500">
          Milestone change failed. Saved data has not been replaced.
        </p>
      )}
    </div>
  );
}

export const Goals: React.FC = () => {
  const [offset, setOffset] = useState(0);
  const query = useGoalsQuery(offset);
  const goals = query.data ?? [];
  const [selectedId, setSelectedId] = useState('');
  const selected =
    goals.find((goal) => goal.goal_id === selectedId) ?? goals[0];
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<GoalDto | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [metric, setMetric] = useState('');
  const [unit, setUnit] = useState('');
  const [baseline, setBaseline] = useState('0');
  const [baselineSource, setBaselineSource] = useState('');
  const [target, setTarget] = useState('100');
  const [deadline, setDeadline] = useState('');
  const [constraints, setConstraints] = useState('');
  const [stopping, setStopping] = useState('');
  const [formError, setFormError] = useState('');
  const [removeGoal, setRemoveGoal] = useState(false);
  const [reading, setReading] = useState('');
  const [readingSource, setReadingSource] = useState('');
  const [milestoneTitle, setMilestoneTitle] = useState('');
  const [milestoneTarget, setMilestoneTarget] = useState('1');
  const [milestoneDue, setMilestoneDue] = useState('');
  const qc = useQueryClient();
  const addToast = useAppStore((s) => s.addToast);
  const create = useCreateGoalMutation();
  const refresh = () => {
    void qc.invalidateQueries({ queryKey: ['goals'] });
  };
  const milestones = useQuery({
    queryKey: ['goals', 'milestones', selected?.goal_id],
    enabled: !!selected,
    queryFn: () => apiClient.goals.milestones(selected!.goal_id),
    retry: false,
  });
  const history = useQuery({
    queryKey: ['goals', 'measurements', selected?.goal_id],
    enabled: !!selected,
    queryFn: () => apiClient.goals.measurements(selected!.goal_id),
    retry: false,
  });
  const update = useMutation({
    mutationFn: ({
      id,
      values,
    }: {
      id: string;
      values: Parameters<typeof apiClient.goals.update>[1];
    }) => apiClient.goals.update(id, values),
    onSuccess: refresh,
  });
  const deletion = useMutation({
    mutationFn: apiClient.goals.remove,
    onSuccess: () => {
      setRemoveGoal(false);
      setSelectedId('');
      refresh();
    },
  });
  const measure = useMutation({
    mutationFn: ({
      id,
      value,
      source,
    }: {
      id: string;
      value: number;
      source: string;
    }) =>
      apiClient.goals.measure(id, {
        value,
        source,
        observed_at: new Date().toISOString(),
      }),
    onSuccess: () => {
      setReading('');
      setReadingSource('');
      refresh();
    },
  });
  const addMilestone = useMutation({
    mutationFn: ({
      id,
      title: name,
      target: amount,
      due,
    }: {
      id: string;
      title: string;
      target: number;
      due: string;
    }) =>
      apiClient.goals.addMilestone(id, {
        title: name,
        target_value: amount,
        due_date: istEndOfDay(due),
      }),
    onSuccess: () => {
      setMilestoneTitle('');
      setMilestoneDue('');
      refresh();
    },
  });

  function openForm(goal: GoalDto | null) {
    setEditing(goal);
    setTitle(goal?.title ?? '');
    setDescription(goal?.description ?? '');
    setMetric('');
    setUnit('');
    setBaseline('0');
    setTarget('100');
    setBaselineSource('');
    setConstraints('');
    setStopping('');
    setDeadline(dateInput(goal?.deadline ?? null));
    setFormError('');
    setModalOpen(true);
  }

  async function saveGoal(e: React.FormEvent) {
    e.preventDefault();
    setFormError('');
    try {
      const values = {
        title: title.trim(),
        description: description.trim() || null,
        deadline: istEndOfDay(deadline),
      };
      if (editing) {
        await update.mutateAsync({ id: editing.goal_id, values });
      } else {
        if (
          !Number.isFinite(Number(baseline)) ||
          !Number.isFinite(Number(target)) ||
          Number(baseline) === Number(target)
        ) {
          setFormError('Enter finite baseline and target values that differ.');
          return;
        }
        const objective: GoalObjective = {
          metric: metric.trim(),
          unit: unit.trim(),
          baseline: Number(baseline),
          baseline_source: baselineSource.trim(),
          target: Number(target),
          constraints: constraints.trim(),
          stopping_conditions: stopping.trim(),
          uncertainty: 'Manual measurements are not independently verified.',
        };
        const saved = await create.mutateAsync({ ...values, objective });
        setSelectedId(saved.goal_id);
        setOffset(0);
      }
      setModalOpen(false);
      addToast(
        'Goal saved',
        'Changes are saved in the local database.',
        'success',
      );
    } catch {
      setFormError(
        'Goal could not be saved. Check the fields and runtime connection.',
      );
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-start gap-3">
        <div>
          <h1 className="text-2xl font-bold">Goals</h1>
          <p className="text-sm text-slate-500 mt-1">
            Track objectives with saved measurements and milestones. Growth
            outcomes are not guaranteed.
          </p>
        </div>
        <Button
          leftIcon={<Plus className="h-4 w-4" />}
          onClick={() => openForm(null)}
        >
          New Goal
        </Button>
      </div>
      {query.isPending && <p role="status">Loading saved goals…</p>}
      {query.isError && (
        <div role="alert">
          Saved goals could not be loaded.{' '}
          <Button onClick={() => void query.refetch()}>Retry goals</Button>
        </div>
      )}
      {query.isSuccess && !goals.length && (
        <Card>
          <p>No saved goals on this page. Create a goal to begin tracking.</p>
        </Card>
      )}
      {query.isSuccess && (
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            disabled={!offset}
            onClick={() => {
              setOffset(Math.max(0, offset - 50));
              setSelectedId('');
            }}
          >
            Previous goals
          </Button>
          <span className="text-sm">Page {offset / 50 + 1}</span>
          <Button
            variant="ghost"
            disabled={goals.length < 50}
            onClick={() => {
              setOffset(offset + 50);
              setSelectedId('');
            }}
          >
            Next goals
          </Button>
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="space-y-3" aria-label="Saved goals">
          {goals.map((goal) => (
            <button
              type="button"
              key={goal.goal_id}
              aria-pressed={selected?.goal_id === goal.goal_id}
              onClick={() => {
                setSelectedId(goal.goal_id);
                setRemoveGoal(false);
                setReading('');
                setReadingSource('');
              }}
              className={`w-full text-left rounded-xl border p-4 ${selected?.goal_id === goal.goal_id ? 'border-cyan-500' : 'border-slate-300 dark:border-white/15'}`}
            >
              <p className="font-semibold">{goal.title}</p>
              <p className="text-xs mt-1">
                {goal.status} · {istDate(goal.deadline)}
              </p>
              <p className="mt-2 font-mono">{goal.progress}%</p>
              <progress
                aria-label={`Progress for ${goal.title}`}
                value={goal.progress}
                max="100"
                className="w-full accent-cyan-500"
              />
            </button>
          ))}
        </div>
        {selected && (
          <div className="lg:col-span-2 space-y-5" key={selected.goal_id}>
            <Card>
              <div className="flex flex-wrap justify-between gap-3">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  {selected.title}
                </h2>
                <Badge
                  status={selected.status === 'completed' ? 'active' : 'info'}
                >
                  {selected.status}
                </Badge>
              </div>
              <p className="mt-2 whitespace-pre-wrap">{selected.description}</p>
              <p className="mt-3">
                Progress: {selected.progress}% ·{' '}
                {selected.progress_basis.replace('_', ' ')} ·{' '}
                {selected.completed_milestones}/{selected.total_milestones}{' '}
                milestones complete
              </p>
              <p className="text-sm mt-1">
                Deadline: {istDate(selected.deadline)} (IST)
              </p>
              {selected.objective ? (
                <div className="space-y-2 mt-4 text-sm">
                  <p>
                    {selected.objective.metric}: baseline{' '}
                    {selected.objective.baseline} → target{' '}
                    {selected.objective.target} {selected.objective.unit}
                  </p>
                  <p>Baseline source: {selected.objective.baseline_source}</p>
                  <p>
                    {selected.measurement
                      ? `Latest manual value: ${selected.measurement.value} ${selected.objective.unit} · Source: ${selected.measurement.source} · ${new Date(selected.measurement.observed_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} IST`
                      : 'No measurement recorded yet.'}
                  </p>
                  {selected.objective.constraints && (
                    <p>Constraints: {selected.objective.constraints}</p>
                  )}
                  {selected.objective.stopping_conditions && (
                    <p>Stop when: {selected.objective.stopping_conditions}</p>
                  )}
                  <p className="text-slate-500">
                    {selected.objective.uncertainty}
                  </p>
                </div>
              ) : (
                <p className="mt-3 text-sm text-slate-500">
                  Legacy goal. Progress uses saved milestones or a legacy manual
                  percentage; no verified analytics are attached.
                </p>
              )}
              <div className="flex flex-wrap items-end gap-2 mt-4">
                <Field label="Goal status">
                  <select
                    aria-label="Goal status"
                    className={inputClass}
                    value={selected.status}
                    disabled={update.isPending}
                    onChange={(e) =>
                      update.mutate({
                        id: selected.goal_id,
                        values: { status: e.target.value as GoalDto['status'] },
                      })
                    }
                  >
                    {['active', 'paused', 'completed', 'cancelled'].map((s) => (
                      <option key={s}>{s}</option>
                    ))}
                  </select>
                </Field>
                <Button variant="ghost" onClick={() => openForm(selected)}>
                  Edit goal
                </Button>
                <Button
                  variant="ghost"
                  leftIcon={<Trash2 className="h-4 w-4" />}
                  onClick={() => setRemoveGoal(true)}
                >
                  Remove goal
                </Button>
              </div>
              {removeGoal && (
                <div className="mt-3 space-y-2">
                  <p>
                    Remove this goal and its milestones? Task execution history
                    will be retained.
                  </p>
                  <Button
                    disabled={deletion.isPending}
                    onClick={() => deletion.mutate(selected.goal_id)}
                  >
                    Confirm goal removal
                  </Button>
                  <Button variant="ghost" onClick={() => setRemoveGoal(false)}>
                    Keep goal
                  </Button>
                </div>
              )}
              {(update.isError || deletion.isError) && (
                <p role="alert" className="text-red-500 mt-2">
                  Goal change failed. Reload saved data before retrying.
                </p>
              )}
            </Card>
            {selected.objective && (
              <Card>
                <h3 className="font-semibold">Record a manual measurement</h3>
                <p className="text-xs text-slate-500 my-2">
                  Recorded at the current time. This is your reported
                  observation, not live platform analytics.
                </p>
                <form
                  className="space-y-3"
                  onSubmit={(e) => {
                    e.preventDefault();
                    measure.mutate({
                      id: selected.goal_id,
                      value: Number(reading),
                      source: readingSource.trim(),
                    });
                  }}
                >
                  <Field label="Measured value">
                    <input
                      className={inputClass}
                      type="number"
                      step="any"
                      required
                      value={reading}
                      onChange={(e) => setReading(e.target.value)}
                    />
                  </Field>
                  <Field label="Measurement source">
                    <input
                      className={inputClass}
                      required
                      maxLength={500}
                      value={readingSource}
                      onChange={(e) => setReadingSource(e.target.value)}
                      placeholder="For example, manually copied from today's account report"
                    />
                  </Field>
                  <Button type="submit" disabled={measure.isPending}>
                    Save measurement
                  </Button>
                  {measure.isError && (
                    <p role="alert" className="text-red-500">
                      Measurement could not be saved.
                    </p>
                  )}
                </form>
                <h4 className="font-semibold mt-5">
                  Recent measurement history
                </h4>
                {history.isPending && <p>Loading measurements…</p>}
                {history.isError && (
                  <p role="alert">Measurement history unavailable.</p>
                )}
                {history.isSuccess && !history.data.length && (
                  <p className="text-sm">No manual measurements saved.</p>
                )}
                <ul className="mt-2 space-y-2">
                  {history.data?.map((item) => (
                    <li
                      key={item.id}
                      className="text-sm border-t border-slate-200 dark:border-white/10 pt-2"
                    >
                      {item.value} {selected.objective!.unit} · {item.source} ·{' '}
                      {new Date(item.observed_at).toLocaleString('en-IN', {
                        timeZone: 'Asia/Kolkata',
                      })}{' '}
                      IST
                    </li>
                  ))}
                </ul>
              </Card>
            )}
            <Card>
              <h3 className="font-semibold mb-3">Milestones</h3>
              <p className="text-xs text-slate-500 mb-3">
                Milestone values are entered manually. For measured goals,
                overall progress follows the objective measurement.
              </p>
              {milestones.isPending && <p>Loading milestones…</p>}
              {milestones.isError && (
                <p role="alert">Milestones unavailable.</p>
              )}
              <div className="space-y-3">
                {milestones.data?.map((item) => (
                  <MilestoneRow
                    key={`${item.id}:${item.current_value}:${item.target_value}`}
                    goalId={selected.goal_id}
                    milestone={item}
                    onSaved={refresh}
                  />
                ))}
              </div>
              <form
                className="space-y-3 mt-4"
                onSubmit={(e) => {
                  e.preventDefault();
                  addMilestone.mutate({
                    id: selected.goal_id,
                    title: milestoneTitle.trim(),
                    target: Number(milestoneTarget),
                    due: milestoneDue,
                  });
                }}
              >
                <Field label="Milestone title">
                  <input
                    className={inputClass}
                    required
                    maxLength={256}
                    value={milestoneTitle}
                    onChange={(e) => setMilestoneTitle(e.target.value)}
                  />
                </Field>
                <div className="grid sm:grid-cols-2 gap-3">
                  <Field label="Milestone target">
                    <input
                      className={inputClass}
                      type="number"
                      step="any"
                      min="0.000001"
                      required
                      value={milestoneTarget}
                      onChange={(e) => setMilestoneTarget(e.target.value)}
                    />
                  </Field>
                  <Field label="Milestone due date (IST)">
                    <input
                      className={inputClass}
                      type="date"
                      value={milestoneDue}
                      onChange={(e) => setMilestoneDue(e.target.value)}
                    />
                  </Field>
                </div>
                <Button type="submit" disabled={addMilestone.isPending}>
                  Add milestone
                </Button>
                {addMilestone.isError && (
                  <p role="alert" className="text-red-500">
                    Milestone could not be saved.
                  </p>
                )}
              </form>
            </Card>
          </div>
        )}
      </div>
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? 'Edit saved goal' : 'Create goal'}
        description="Saved locally. Automatic planning and experiments are not enabled."
      >
        <form onSubmit={saveGoal} className="space-y-3">
          <Field label="Goal title">
            <input
              className={inputClass}
              required
              maxLength={256}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </Field>
          <Field label="Goal description">
            <textarea
              className={inputClass}
              rows={2}
              maxLength={8000}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Field>
          {!editing && (
            <>
              <Field label="Metric name">
                <input
                  className={inputClass}
                  required
                  maxLength={100}
                  value={metric}
                  onChange={(e) => setMetric(e.target.value)}
                />
              </Field>
              <Field label="Metric unit">
                <input
                  className={inputClass}
                  required
                  maxLength={80}
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Baseline">
                  <input
                    className={inputClass}
                    type="number"
                    step="any"
                    required
                    value={baseline}
                    onChange={(e) => setBaseline(e.target.value)}
                  />
                </Field>
                <Field label="Target">
                  <input
                    className={inputClass}
                    type="number"
                    step="any"
                    required
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                  />
                </Field>
              </div>
              <Field label="Baseline source">
                <input
                  className={inputClass}
                  required
                  maxLength={500}
                  value={baselineSource}
                  onChange={(e) => setBaselineSource(e.target.value)}
                />
              </Field>
              <Field label="Constraints">
                <textarea
                  className={inputClass}
                  maxLength={4000}
                  value={constraints}
                  onChange={(e) => setConstraints(e.target.value)}
                />
              </Field>
              <Field label="Stopping conditions">
                <textarea
                  className={inputClass}
                  maxLength={4000}
                  value={stopping}
                  onChange={(e) => setStopping(e.target.value)}
                />
              </Field>
            </>
          )}
          <Field label="Goal deadline (IST)">
            <input
              className={inputClass}
              type="date"
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
            />
          </Field>
          {formError && (
            <p role="alert" className="text-red-500">
              {formError}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={create.isPending || update.isPending}
            >
              Save goal
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
