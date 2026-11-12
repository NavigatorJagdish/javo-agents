import React, { useState } from 'react';
import { Target, Plus, CheckCircle2, Circle, FlaskConical, Calendar } from 'lucide-react';
import { Card, Badge, Button, Modal, Chip } from '@javo/design-system';
import { useGoalStore } from '../store/useGoalStore';
import { useCreateGoalMutation } from '../api/hooks';
import { useAppStore } from '../store/useAppStore';

export const Goals: React.FC = () => {
  const goals = useGoalStore((s) => s.goals);
  const toggleMilestone = useGoalStore((s) => s.toggleMilestone);
  const createGoalMutation = useCreateGoalMutation();
  const addToast = useAppStore((s) => s.addToast);

  const [selectedGoalId, setSelectedGoalId] = useState<string>(goals[0]?.id ?? '');
  const [modalOpen, setModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [targetValue, setTargetValue] = useState('10000');
  const [unit, setUnit] = useState('followers');
  const [deadline, setDeadline] = useState('2026-12-31');

  const selectedGoal = goals.find((g) => g.id === selectedGoalId) ?? goals[0];

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    await createGoalMutation.mutateAsync({
      title,
      description,
      target_value: Number(targetValue) || 100,
      unit,
      deadline,
    });
    addToast('Goal Created', `Goal Persistence (#23) is now tracking "${title}".`, 'success');
    setTitle('');
    setDescription('');
    setModalOpen(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            Autonomous Goals & Experiments
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Goal Persistence (#23) and Growth Scientist (#01) continuously decompose KPIs into daily tasks.
          </p>
        </div>
        <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setModalOpen(true)}>
          New Goal
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Goal list */}
        <div className="space-y-3">
          {goals.map((goal) => {
            const active = selectedGoal?.id === goal.id;
            return (
              <Card
                key={goal.id}
                variant={active ? 'status' : 'default'}
                glow={active ? 'cyan' : 'none'}
                interactive
                onClick={() => setSelectedGoalId(goal.id)}
                className={active ? 'border-[#00E5FF]' : ''}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#008CA8] dark:text-[#00E5FF]">
                    {goal.category}
                  </span>
                  <Badge
                    status={
                      goal.status === 'on_track'
                        ? 'active'
                        : goal.status === 'at_risk'
                          ? 'warning'
                          : 'info'
                    }
                    size="sm"
                  >
                    {goal.status.replace('_', ' ')}
                  </Badge>
                </div>
                <h3 className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">
                  {goal.title}
                </h3>
                <div className="mt-3">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-500 dark:text-slate-400">
                      {goal.currentValue.toLocaleString()} / {goal.targetValue.toLocaleString()} {goal.unit}
                    </span>
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      {goal.progress}%
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-200 dark:bg-white/10 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-[#00E5FF] to-[#8B5CF6]"
                      style={{ width: `${goal.progress}%` }}
                    />
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        {/* Selected Goal Detail */}
        {selectedGoal && (
          <div className="lg:col-span-2 space-y-6">
            <Card variant="feature" glow="cyan">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Target className="h-5 w-5 text-[#00E5FF]" />
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                      {selectedGoal.title}
                    </h2>
                  </div>
                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                    {selectedGoal.description}
                  </p>
                </div>
                <div className="flex flex-col items-end shrink-0">
                  <span className="text-3xl font-bold font-mono text-[#008CA8] dark:text-[#00E5FF]">
                    {selectedGoal.progress}%
                  </span>
                  <span className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                    <Calendar className="h-3.5 w-3.5" /> Due {selectedGoal.deadline}
                  </span>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <Chip label={`Owner: ${selectedGoal.assignedAgent}`} selected variant="cyan" />
                <Chip
                  label={`Target: ${selectedGoal.targetValue.toLocaleString()} ${selectedGoal.unit}`}
                  variant="violet"
                  selected
                />
              </div>
            </Card>

            {/* Milestones */}
            <Card variant="default">
              <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-4">
                Milestones
              </h3>
              <div className="space-y-2.5">
                {selectedGoal.milestones.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => toggleMilestone(selectedGoal.id, m.id)}
                    className="w-full flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-50 dark:bg-[#0B1026]/65 border border-slate-200 dark:border-white/10 hover:border-[#00E5FF]/40 transition-colors text-left cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      {m.completed ? (
                        <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
                      ) : (
                        <Circle className="h-5 w-5 text-slate-400 shrink-0" />
                      )}
                      <span
                        className={`text-sm ${
                          m.completed
                            ? 'line-through text-slate-400'
                            : 'font-medium text-slate-900 dark:text-white'
                        }`}
                      >
                        {m.title}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-slate-400">{m.dueDate}</span>
                  </button>
                ))}
              </div>
            </Card>

            {/* Experiments */}
            <Card variant="default">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <FlaskConical className="h-4 w-4 text-[#8B5CF6]" /> Active & Completed Experiments
                </h3>
                <Badge status="violet" size="sm">
                  Growth Scientist #01
                </Badge>
              </div>
              {selectedGoal.experiments.length === 0 ? (
                <p className="text-sm text-slate-500">No experiments attached to this goal yet.</p>
              ) : (
                <div className="space-y-3">
                  {selectedGoal.experiments.map((exp) => (
                    <div
                      key={exp.id}
                      className="p-4 rounded-xl bg-slate-50 dark:bg-[#0B1026]/70 border border-slate-200 dark:border-white/10"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium text-slate-900 dark:text-white">
                          {exp.hypothesis}
                        </p>
                        <Badge status={exp.status === 'completed' ? 'active' : 'info'} size="sm">
                          {exp.status}
                        </Badge>
                      </div>
                      <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                        <div className="p-2 rounded-lg bg-white dark:bg-[#131C40] border border-slate-200 dark:border-white/10">
                          <span className="text-slate-400">Variant A:</span>{' '}
                          <span className="font-semibold">{exp.variantA}</span>
                        </div>
                        <div className="p-2 rounded-lg bg-white dark:bg-[#131C40] border border-slate-200 dark:border-white/10">
                          <span className="text-slate-400">Variant B:</span>{' '}
                          <span className="font-semibold">{exp.variantB}</span>
                        </div>
                        <div className="p-2 rounded-lg bg-[#00E5FF]/10 border border-[#00E5FF]/30 text-[#008CA8] dark:text-[#00E5FF] font-semibold">
                          Result: {exp.lift}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}
      </div>

      {/* Create Goal Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Create Autonomous Goal"
        description="Agents will automatically plan milestones and schedule weekly experiments."
      >
        <form onSubmit={handleCreateGoal} className="space-y-4">
          <div>
            <label className="block text-xs font-medium mb-1">Goal Title</label>
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Reach 25K Instagram Followers"
              className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Description</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Strategy, platforms, and constraints..."
              className="w-full p-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
            />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1">Target</label>
              <input
                type="number"
                value={targetValue}
                onChange={(e) => setTargetValue(e.target.value)}
                className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Unit</label>
              <input
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Deadline</label>
              <input
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 text-sm"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Create Goal
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
