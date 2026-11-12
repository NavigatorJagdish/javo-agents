import { create } from 'zustand';

export interface Milestone {
  id: string;
  title: string;
  completed: boolean;
  dueDate: string;
}

export interface Experiment {
  id: string;
  hypothesis: string;
  variantA: string;
  variantB: string;
  winner?: 'A' | 'B';
  lift: string;
  status: 'running' | 'completed';
}

export interface GoalItem {
  id: string;
  title: string;
  description: string;
  category: 'Audience' | 'Publishing' | 'Engagement' | 'Revenue';
  progress: number;
  currentValue: number;
  targetValue: number;
  unit: string;
  status: 'on_track' | 'at_risk' | 'completed' | 'paused';
  deadline: string;
  assignedAgent: string;
  milestones: Milestone[];
  experiments: Experiment[];
}

const INITIAL_GOALS: GoalItem[] = [
  {
    id: 'goal-1',
    title: 'Grow YouTube Shorts to 50K Subscribers',
    description: 'Publish 5 high-retention Shorts weekly with automated hook A/B testing.',
    category: 'Audience',
    progress: 74,
    currentValue: 37000,
    targetValue: 50000,
    unit: 'subscribers',
    status: 'on_track',
    deadline: '2026-12-31',
    assignedAgent: 'Growth Scientist',
    milestones: [
      { id: 'm1', title: 'Hit 25K subscribers baseline', completed: true, dueDate: '2026-10-15' },
      { id: 'm2', title: 'Achieve >68% average 3-sec hook hold', completed: true, dueDate: '2026-11-01' },
      { id: 'm3', title: 'Reach 40K subscribers with recycled top clips', completed: false, dueDate: '2026-12-01' },
      { id: 'm4', title: 'Cross 50K milestone', completed: false, dueDate: '2026-12-31' },
    ],
    experiments: [
      {
        id: 'exp-1',
        hypothesis: 'Question-based first 2s captions outperform bold statement hooks.',
        variantA: 'Statement Hook',
        variantB: 'Question Hook',
        winner: 'B',
        lift: '+22.4% retention',
        status: 'completed',
      },
      {
        id: 'exp-2',
        hypothesis: 'Posting at 18:00 EST increases initial 1h velocity over 12:00 EST.',
        variantA: '12:00 EST',
        variantB: '18:00 EST',
        lift: '+14.1% views (ongoing)',
        status: 'running',
      },
    ],
  },
  {
    id: 'goal-2',
    title: 'Maintain 98% Autonomous Content Cadence',
    description: 'Ensure daily multi-platform queue remains filled 14 days ahead.',
    category: 'Publishing',
    progress: 92,
    currentValue: 26,
    targetValue: 28,
    unit: 'posts queued',
    status: 'on_track',
    deadline: '2026-11-30',
    assignedAgent: 'Content Factory',
    milestones: [
      { id: 'm5', title: 'Connect folder watcher to Ready/Reels', completed: true, dueDate: '2026-11-02' },
      { id: 'm6', title: 'Enable Quality Inspector auto-scoring', completed: true, dueDate: '2026-11-08' },
      { id: 'm7', title: 'Lock 14-day buffer across 3 channels', completed: false, dueDate: '2026-11-30' },
    ],
    experiments: [
      {
        id: 'exp-3',
        hypothesis: 'Auto-recycled carousels maintain >85% save rate of original videos.',
        variantA: 'Original Carousel',
        variantB: 'Recycled Video -> Carousel',
        lift: '91% parity',
        status: 'running',
      },
    ],
  },
  {
    id: 'goal-3',
    title: 'Reduce Community Comment Response Time < 15m',
    description: 'Use Community Manager + Approval queue for rapid authentic replies.',
    category: 'Engagement',
    progress: 64,
    currentValue: 19,
    targetValue: 15,
    unit: 'min avg',
    status: 'at_risk',
    deadline: '2026-12-15',
    assignedAgent: 'Community Manager',
    milestones: [
      { id: 'm8', title: 'Enable Instagram & YouTube comment webhooks', completed: true, dueDate: '2026-11-05' },
      { id: 'm9', title: 'Auto-approve low-risk FAQ replies', completed: false, dueDate: '2026-11-25' },
    ],
    experiments: [],
  },
];

interface GoalState {
  goals: GoalItem[];
  addGoal: (input: {
    title: string;
    description: string;
    targetValue: number;
    unit: string;
    deadline: string;
  }) => void;
  toggleMilestone: (goalId: string, milestoneId: string) => void;
}

export const useGoalStore = create<GoalState>((set) => ({
  goals: INITIAL_GOALS,
  addGoal: (input) =>
    set((state) => ({
      goals: [
        {
          id: `goal-${Date.now()}`,
          title: input.title,
          description: input.description,
          category: 'Audience',
          progress: 0,
          currentValue: 0,
          targetValue: input.targetValue,
          unit: input.unit,
          status: 'on_track',
          deadline: input.deadline,
          assignedAgent: 'Goal Persistence',
          milestones: [
            {
              id: `m-${Date.now()}`,
              title: 'Initial baseline & agent assignment',
              completed: false,
              dueDate: input.deadline,
            },
          ],
          experiments: [],
        },
        ...state.goals,
      ],
    })),
  toggleMilestone: (goalId, milestoneId) =>
    set((state) => ({
      goals: state.goals.map((g) => {
        if (g.id !== goalId) return g;
        const milestones = g.milestones.map((m) =>
          m.id === milestoneId ? { ...m, completed: !m.completed } : m
        );
        const doneCount = milestones.filter((m) => m.completed).length;
        const progress =
          milestones.length > 0 ? Math.round((doneCount / milestones.length) * 100) : g.progress;
        return { ...g, milestones, progress };
      }),
    })),
}));
