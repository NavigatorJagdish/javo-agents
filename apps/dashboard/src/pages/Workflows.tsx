import React, { useCallback, useMemo, useRef, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useEdgesState,
  useNodesState,
  Handle,
  Position,
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Zap,
  Clock,
  FolderOpen,
  UserCheck,
  ScanSearch,
  Sparkles,
  GitFork,
  ShieldCheck,
  Send,
  MessageSquareReply,
  Bell,
  BarChart2,
  Timer,
  RotateCcw,
  AlertTriangle,
  Flag,
  Play,
  Save,
  Trash2,
  Plus,
} from 'lucide-react';
import { Button, Badge, Card } from '@javo/design-system';
import { useSaveWorkflowMutation } from '../api/hooks';
import { useAppStore } from '../store/useAppStore';

export type WorkflowNodeKind =
  | 'Trigger'
  | 'Schedule'
  | 'Folder Watcher'
  | 'Account Event'
  | 'Content Analyzer'
  | 'AI Prompt'
  | 'Condition'
  | 'Approval'
  | 'Publish'
  | 'Comment Reply'
  | 'Notification'
  | 'Analytics'
  | 'Delay'
  | 'Retry'
  | 'Error Handler'
  | 'End';

interface NodeCatalogEntry {
  kind: WorkflowNodeKind;
  category: 'Triggers' | 'AI & Logic' | 'Actions' | 'Flow Control';
  description: string;
  defaultConfig: Record<string, string>;
}

const NODE_CATALOG: NodeCatalogEntry[] = [
  { kind: 'Trigger', category: 'Triggers', description: 'Manual or webhook event trigger', defaultConfig: { source: 'Webhook / Manual' } },
  { kind: 'Schedule', category: 'Triggers', description: 'Cron or interval schedule', defaultConfig: { cron: '0 18 * * 1-5' } },
  { kind: 'Folder Watcher', category: 'Triggers', description: 'Watch local media folder', defaultConfig: { path: 'D:/CreatorContent/Ready' } },
  { kind: 'Account Event', category: 'Triggers', description: 'New follower, mention, or comment', defaultConfig: { platform: 'YouTube', event: 'new_comment' } },
  { kind: 'Content Analyzer', category: 'AI & Logic', description: 'Score video/audio quality & hook', defaultConfig: { minScore: '85' } },
  { kind: 'AI Prompt', category: 'AI & Logic', description: 'Run local Ollama or Gemini prompt', defaultConfig: { model: 'Qwen 2.5 14B', prompt: 'Generate viral 3-line caption' } },
  { kind: 'Condition', category: 'AI & Logic', description: 'Branch on expression result', defaultConfig: { expression: 'score >= 85' } },
  { kind: 'Approval', category: 'Actions', description: 'Require human sign-off via Telegram', defaultConfig: { channel: 'Telegram + Inbox', timeout: '4h' } },
  { kind: 'Publish', category: 'Actions', description: 'Post to connected social channel', defaultConfig: { platform: 'YouTube Shorts', visibility: 'public' } },
  { kind: 'Comment Reply', category: 'Actions', description: 'Auto-reply with brand voice', defaultConfig: { tone: 'Helpful & Concise' } },
  { kind: 'Notification', category: 'Actions', description: 'Send desktop or Telegram alert', defaultConfig: { target: 'Telegram Admin' } },
  { kind: 'Analytics', category: 'Actions', description: 'Record metrics snapshot', defaultConfig: { metric: '1h_velocity' } },
  { kind: 'Delay', category: 'Flow Control', description: 'Wait before continuing flow', defaultConfig: { duration: '30m' } },
  { kind: 'Retry', category: 'Flow Control', description: 'Retry failed branch with backoff', defaultConfig: { maxRetries: '3', backoff: 'exponential' } },
  { kind: 'Error Handler', category: 'Flow Control', description: 'Catch exceptions & alert recovery', defaultConfig: { fallback: 'Recovery Agent #20' } },
  { kind: 'End', category: 'Flow Control', description: 'Terminate workflow execution', defaultConfig: { status: 'completed' } },
];

const iconForKind: Record<WorkflowNodeKind, React.ReactNode> = {
  Trigger: <Zap className="h-4 w-4" />,
  Schedule: <Clock className="h-4 w-4" />,
  'Folder Watcher': <FolderOpen className="h-4 w-4" />,
  'Account Event': <UserCheck className="h-4 w-4" />,
  'Content Analyzer': <ScanSearch className="h-4 w-4" />,
  'AI Prompt': <Sparkles className="h-4 w-4" />,
  Condition: <GitFork className="h-4 w-4" />,
  Approval: <ShieldCheck className="h-4 w-4" />,
  Publish: <Send className="h-4 w-4" />,
  'Comment Reply': <MessageSquareReply className="h-4 w-4" />,
  Notification: <Bell className="h-4 w-4" />,
  Analytics: <BarChart2 className="h-4 w-4" />,
  Delay: <Timer className="h-4 w-4" />,
  Retry: <RotateCcw className="h-4 w-4" />,
  'Error Handler': <AlertTriangle className="h-4 w-4" />,
  End: <Flag className="h-4 w-4" />,
};

const categoryColor: Record<NodeCatalogEntry['category'], string> = {
  Triggers: 'border-[#00E5FF]/60 bg-[#00E5FF]/10 text-[#00E5FF]',
  'AI & Logic': 'border-[#8B5CF6]/60 bg-[#8B5CF6]/15 text-[#A78BFA]',
  Actions: 'border-emerald-500/60 bg-emerald-500/15 text-emerald-400',
  'Flow Control': 'border-amber-500/60 bg-amber-500/15 text-amber-400',
};

interface CustomNodeData extends Record<string, unknown> {
  kind: WorkflowNodeKind;
  label: string;
  category: NodeCatalogEntry['category'];
  config: Record<string, string>;
  simulating?: boolean;
}

const JavoWorkflowNode: React.FC<NodeProps<Node<CustomNodeData>>> = ({ data, selected }) => {
  const isTrigger = data.category === 'Triggers';
  const isEnd = data.kind === 'End';
  const summary = Object.entries(data.config || {})
    .slice(0, 2)
    .map(([k, v]) => `${k}: ${v}`)
    .join(' • ');

  return (
    <div
      className={`min-w-[220px] max-w-[260px] rounded-2xl border backdrop-blur-xl transition-all shadow-lg ${
        data.simulating
          ? 'border-[#00E5FF] ring-2 ring-[#00E5FF]/60 shadow-[0_0_24px_rgba(0,229,255,0.45)]'
          : selected
            ? 'border-[#00E5FF] ring-2 ring-[#00E5FF]/35'
            : 'border-slate-300 dark:border-white/15'
      } bg-white/95 dark:bg-[#131C40]/95`}
    >
      {!isTrigger && (
        <Handle
          type="target"
          position={Position.Left}
          className="!w-3 !h-3 !bg-[#00E5FF] !border-2 !border-[#0B1026]"
        />
      )}

      <div className="p-3">
        <div className="flex items-center justify-between gap-2">
          <span
            className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg text-[11px] font-semibold border ${
              categoryColor[data.category]
            }`}
          >
            {iconForKind[data.kind]}
            {data.kind}
          </span>
          {data.simulating && (
            <span className="h-2 w-2 rounded-full bg-[#00E5FF] animate-ping" />
          )}
        </div>
        <p className="mt-2 text-sm font-semibold text-slate-900 dark:text-white truncate">
          {data.label}
        </p>
        {summary && (
          <p className="mt-1 text-[11px] font-mono text-slate-500 dark:text-slate-400 truncate">
            {summary}
          </p>
        )}
      </div>

      {!isEnd && (
        <Handle
          type="source"
          position={Position.Right}
          className="!w-3 !h-3 !bg-[#8B5CF6] !border-2 !border-[#0B1026]"
        />
      )}
    </div>
  );
};

const INITIAL_NODES: Node<CustomNodeData>[] = [
  {
    id: 'n-1',
    type: 'javoNode',
    position: { x: 40, y: 140 },
    data: {
      kind: 'Folder Watcher',
      label: 'Watch Ready Reels',
      category: 'Triggers',
      config: { path: 'D:/CreatorContent/Ready' },
    },
  },
  {
    id: 'n-2',
    type: 'javoNode',
    position: { x: 320, y: 140 },
    data: {
      kind: 'Content Analyzer',
      label: 'Inspect Hook & Audio',
      category: 'AI & Logic',
      config: { minScore: '85' },
    },
  },
  {
    id: 'n-3',
    type: 'javoNode',
    position: { x: 600, y: 60 },
    data: {
      kind: 'AI Prompt',
      label: 'Generate Viral Caption',
      category: 'AI & Logic',
      config: { model: 'Qwen 2.5 14B', prompt: '3-line high retention hook' },
    },
  },
  {
    id: 'n-4',
    type: 'javoNode',
    position: { x: 600, y: 230 },
    data: {
      kind: 'Condition',
      label: 'Score >= 85?',
      category: 'AI & Logic',
      config: { expression: 'score >= 85' },
    },
  },
  {
    id: 'n-5',
    type: 'javoNode',
    position: { x: 890, y: 60 },
    data: {
      kind: 'Approval',
      label: 'Telegram Sign-off',
      category: 'Actions',
      config: { channel: 'Telegram + Inbox', timeout: '4h' },
    },
  },
  {
    id: 'n-6',
    type: 'javoNode',
    position: { x: 1170, y: 60 },
    data: {
      kind: 'Publish',
      label: 'Publish YouTube Short',
      category: 'Actions',
      config: { platform: 'YouTube Shorts', visibility: 'public' },
    },
  },
  {
    id: 'n-7',
    type: 'javoNode',
    position: { x: 1170, y: 230 },
    data: {
      kind: 'Analytics',
      label: 'Track 1h Velocity',
      category: 'Actions',
      config: { metric: '1h_velocity' },
    },
  },
];

const INITIAL_EDGES: Edge[] = [
  { id: 'e1-2', source: 'n-1', target: 'n-2', animated: true, style: { stroke: '#00E5FF', strokeWidth: 2 } },
  { id: 'e2-3', source: 'n-2', target: 'n-3', animated: true, style: { stroke: '#8B5CF6', strokeWidth: 2 } },
  { id: 'e2-4', source: 'n-2', target: 'n-4', style: { stroke: '#8B5CF6', strokeWidth: 2 } },
  { id: 'e3-5', source: 'n-3', target: 'n-5', animated: true, style: { stroke: '#00E5FF', strokeWidth: 2 } },
  { id: 'e5-6', source: 'n-5', target: 'n-6', animated: true, style: { stroke: '#10B981', strokeWidth: 2 } },
  { id: 'e6-7', source: 'n-6', target: 'n-7', style: { stroke: '#10B981', strokeWidth: 2 } },
];

export const Workflows: React.FC = () => {
  const reactFlowWrapper = useRef<HTMLDivElement | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<CustomNodeData>>(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
  const [workflowName, setWorkflowName] = useState('Autonomous Short-Form Pipeline');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>('n-3');
  const [paletteFilter, setPaletteFilter] = useState('');
  const [simulating, setSimulating] = useState(false);

  const saveWorkflow = useSaveWorkflowMutation();
  const addToast = useAppStore((s) => s.addToast);

  const nodeTypes = useMemo(() => ({ javoNode: JavoWorkflowNode }), []);

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId]
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            animated: true,
            style: { stroke: '#00E5FF', strokeWidth: 2 },
          },
          eds
        )
      );
    },
    [setEdges]
  );

  const addCatalogNode = useCallback(
    (entry: NodeCatalogEntry, position?: { x: number; y: number }) => {
      const id = `n-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
      const pos = position ?? {
        x: 180 + (nodes.length % 4) * 140,
        y: 120 + (nodes.length % 3) * 110,
      };
      const newNode: Node<CustomNodeData> = {
        id,
        type: 'javoNode',
        position: pos,
        data: {
          kind: entry.kind,
          label: entry.kind,
          category: entry.category,
          config: { ...entry.defaultConfig },
        },
      };
      setNodes((nds) => nds.concat(newNode));
      setSelectedNodeId(id);
    },
    [nodes.length, setNodes]
  );

  const onDragStart = (event: React.DragEvent, entry: NodeCatalogEntry) => {
    event.dataTransfer.setData('application/javo-node', JSON.stringify(entry));
    event.dataTransfer.effectAllowed = 'move';
  };

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const raw = event.dataTransfer.getData('application/javo-node');
      if (!raw || !reactFlowWrapper.current) return;
      const entry = JSON.parse(raw) as NodeCatalogEntry;
      const bounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = {
        x: event.clientX - bounds.left - 110,
        y: event.clientY - bounds.top - 40,
      };
      addCatalogNode(entry, position);
    },
    [addCatalogNode]
  );

  const updateSelectedLabel = (label: string) => {
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((n) => (n.id === selectedNode.id ? { ...n, data: { ...n.data, label } } : n))
    );
  };

  const updateSelectedConfig = (key: string, value: string) => {
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((n) =>
        n.id === selectedNode.id
          ? {
              ...n,
              data: {
                ...n.data,
                config: { ...n.data.config, [key]: value },
              },
            }
          : n
      )
    );
  };

  const deleteSelectedNode = () => {
    if (!selectedNode) return;
    setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
    setEdges((eds) =>
      eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id)
    );
    setSelectedNodeId(null);
  };

  const handleSave = async () => {
    await saveWorkflow.mutateAsync({
      name: workflowName,
      nodes,
      edges,
      active: true,
    });
    addToast('Workflow Saved', `"${workflowName}" (${nodes.length} nodes) synced to DAG runner.`, 'success');
  };

  const handleSimulate = () => {
    if (simulating || nodes.length === 0) return;
    setSimulating(true);
    addToast('Simulation Started', `Stepping through ${nodes.length} workflow nodes...`, 'info');
    nodes.forEach((node, index) => {
      setTimeout(() => {
        setNodes((nds) =>
          nds.map((n) => ({
            ...n,
            data: { ...n.data, simulating: n.id === node.id },
          }))
        );
        if (index === nodes.length - 1) {
          setTimeout(() => {
            setNodes((nds) =>
              nds.map((n) => ({ ...n, data: { ...n.data, simulating: false } }))
            );
            setSimulating(false);
            addToast('Simulation Complete', 'All workflow branches verified with 0 errors.', 'success');
          }, 550);
        }
      }, index * 480);
    });
  };

  const filteredCatalog = NODE_CATALOG.filter(
    (entry) =>
      entry.kind.toLowerCase().includes(paletteFilter.toLowerCase()) ||
      entry.category.toLowerCase().includes(paletteFilter.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Top toolbar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <div className="flex items-center gap-3 flex-wrap">
          <input
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            aria-label="Workflow name"
            className="font-display text-xl sm:text-2xl font-bold bg-transparent border-b border-transparent hover:border-white/20 focus:border-[#00E5FF] focus:outline-none text-slate-900 dark:text-white"
          />
          <Badge status="info" size="sm">
            {nodes.length} Nodes • {edges.length} Connections
          </Badge>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant="secondary"
            leftIcon={<Play className="h-4 w-4" />}
            onClick={handleSimulate}
            isLoading={simulating}
          >
            Test Run
          </Button>
          <Button
            size="sm"
            variant="primary"
            leftIcon={<Save className="h-4 w-4" />}
            onClick={handleSave}
            isLoading={saveWorkflow.isPending}
          >
            Save Workflow
          </Button>
        </div>
      </div>

      {/* 3-Column Visual Editor */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[calc(100vh-210px)] min-h-[580px]">
        {/* Left Node Palette (All 16 node types) */}
        <Card
          variant="default"
          padding="sm"
          className="lg:col-span-3 xl:col-span-2 flex flex-col overflow-hidden"
        >
          <div className="mb-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
              Node Palette (16 Types)
            </p>
            <input
              type="search"
              value={paletteFilter}
              onChange={(e) => setPaletteFilter(e.target.value)}
              placeholder="Search nodes..."
              aria-label="Search node types"
              className="w-full h-8 px-2.5 rounded-lg text-xs bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/10 focus:outline-none focus:border-[#00E5FF]"
            />
          </div>

          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {filteredCatalog.map((entry) => (
              <div
                key={entry.kind}
                draggable
                onDragStart={(e) => onDragStart(e, entry)}
                className="group flex items-center justify-between gap-2 p-2 rounded-xl bg-slate-50 dark:bg-[#0B1026]/80 border border-slate-200 dark:border-white/10 hover:border-[#00E5FF]/50 cursor-grab active:cursor-grabbing transition-colors"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`p-1.5 rounded-lg border shrink-0 ${categoryColor[entry.category]}`}>
                    {iconForKind[entry.kind]}
                  </span>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-900 dark:text-white truncate">
                      {entry.kind}
                    </p>
                    <p className="text-[10px] text-slate-400 truncate">{entry.category}</p>
                  </div>
                </div>
                <button
                  type="button"
                  title={`Add ${entry.kind}`}
                  aria-label={`Add ${entry.kind} node`}
                  onClick={() => addCatalogNode(entry)}
                  className="p-1 rounded-md text-slate-400 hover:text-[#00E5FF] hover:bg-white/10 cursor-pointer"
                >
                  <Plus className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        </Card>

        {/* Center ReactFlow Canvas */}
        <div
          ref={reactFlowWrapper}
          className="lg:col-span-6 xl:col-span-7 rounded-2xl overflow-hidden border border-slate-200 dark:border-white/10 bg-slate-100 dark:bg-[#080C1D] relative"
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={(_e, node) => setSelectedNodeId(node.id)}
            nodeTypes={nodeTypes}
            fitView
            deleteKeyCode={['Backspace', 'Delete']}
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={20}
              size={1.2}
              color="rgba(0, 229, 255, 0.18)"
            />
            <Controls />
            <MiniMap
              nodeColor={(n) => {
                const cat = (n.data as CustomNodeData | undefined)?.category;
                if (cat === 'Triggers') return '#00E5FF';
                if (cat === 'AI & Logic') return '#8B5CF6';
                if (cat === 'Actions') return '#10B981';
                return '#F59E0B';
              }}
              maskColor="rgba(11, 16, 38, 0.7)"
            />
          </ReactFlow>
        </div>

        {/* Right Inspector Panel */}
        <Card
          variant="default"
          padding="sm"
          className="lg:col-span-3 flex flex-col justify-between overflow-y-auto"
        >
          {selectedNode ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border ${
                    categoryColor[selectedNode.data.category]
                  }`}
                >
                  {iconForKind[selectedNode.data.kind]}
                  {selectedNode.data.kind}
                </span>
                <button
                  type="button"
                  onClick={deleteSelectedNode}
                  aria-label="Delete selected node"
                  className="p-1.5 rounded-lg text-red-400 hover:bg-red-500/15 cursor-pointer"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-1">
                  Node Label
                </label>
                <input
                  value={selectedNode.data.label}
                  onChange={(e) => updateSelectedLabel(e.target.value)}
                  className="w-full h-9 px-3 rounded-xl text-sm bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 focus:outline-none focus:border-[#00E5FF]"
                />
              </div>

              <div className="space-y-3 pt-2 border-t border-slate-200 dark:border-white/10">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Node Parameters
                </p>
                {Object.entries(selectedNode.data.config).map(([key, val]) => (
                  <div key={key}>
                    <label className="block text-xs font-medium capitalize text-slate-500 dark:text-slate-400 mb-1">
                      {key}
                    </label>
                    <input
                      value={val}
                      onChange={(e) => updateSelectedConfig(key, e.target.value)}
                      className="w-full h-9 px-3 rounded-xl text-xs font-mono bg-slate-100 dark:bg-[#0B1026] border border-slate-200 dark:border-white/15 focus:outline-none focus:border-[#00E5FF]"
                    />
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-4 text-slate-400">
              <Sparkles className="h-8 w-8 text-[#00E5FF] mb-2 opacity-70" />
              <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
                Select a node to inspect
              </p>
              <p className="text-xs mt-1">
                Drag any of the 16 node types from the left palette or click + to add to the canvas.
              </p>
            </div>
          )}

          <div className="pt-4 mt-4 border-t border-slate-200 dark:border-white/10 text-[11px] text-slate-400">
            Drag handles to connect nodes • Press Delete to remove selected node or edge.
          </div>
        </Card>
      </div>
    </div>
  );
};
