import React, { useCallback, useEffect, useId, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useBeforeUnload, useBlocker } from "react-router-dom";
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  addEdge,
  useEdgesState,
  useNodesState,
  type Node,
  type NodeProps,
  type Edge,
  type Connection,
  type ReactFlowInstance,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Button, Card, Modal } from "@javo/design-system";
import { apiRequest, ApiError } from "../api/client";

type NodeData = {
  label: string;
  kind: string;
  config: Record<string, unknown> | null;
  entry: boolean;
};
type GraphNode = Node<NodeData>;
type SavedNode = {
  id: string;
  node_type: string;
  label: string;
  config: Record<string, unknown> | null;
  position_x: number;
  position_y: number;
  is_entry_point: boolean;
};
type SavedEdge = {
  id: string;
  source_node_id: string;
  target_node_id: string;
  condition: string | null;
  label: string | null;
};
type Graph = {
  id: string;
  name: string;
  description: string | null;
  status: string;
  revision: number;
  fingerprint: string;
  execution_available: boolean;
  validation_errors: string[];
  nodes: SavedNode[];
  edges: SavedEdge[];
  trigger_config: Record<string, unknown> | null;
  viewport: Record<string, unknown> | null;
};
type Revision = { revision: number; name: string; created_at: string };
type Run = {
  id: string;
  status: string;
  revision: number | null;
  execution_verified: boolean;
  error: string | null;
  message: string;
  execution_log: {
    node_id: string;
    event: string;
    node_type: string;
    output?: { text?: string; actions_executed?: boolean; matched?: boolean; decision?: string };
  }[];
};
const supported = new Set(["trigger", "ai_prompt", "delay", "condition", "approval", "end"]);
const kinds = [
  "trigger",
  "ai_prompt",
  "delay",
  "end",
  "condition",
  "approval",
  "publish",
  "schedule",
  "folder_watcher",
  "account_event",
  "content_analyzer",
  "comment_reply",
  "notification",
  "analytics",
  "retry",
  "error_handler",
];
const inputClass =
  "w-full min-w-0 rounded-lg border border-slate-300 dark:border-white/20 bg-white dark:bg-slate-950 px-3 py-2 text-sm";
const title = (kind: string) => kind.replaceAll("_", " ");
function message(error: unknown) {
  const detail =
    error instanceof ApiError
      ? (error.detail as { detail?: unknown })?.detail
      : null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail
      .map((item) =>
        typeof item?.msg === "string" ? item.msg : "Invalid graph field",
      )
      .join("; ");
  return error instanceof Error
    ? error.message
    : "The runtime did not confirm this operation.";
}
function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactElement<{ id?: string }>;
}) {
  const id = useId();
  return (
    <div className="space-y-1 min-w-0">
      <label htmlFor={id} className="block text-sm">
        {label}
      </label>
      {React.cloneElement(children, { id })}
    </div>
  );
}
function FlowNode({ data, selected }: NodeProps<GraphNode>) {
  return (
    <div
      className={`w-52 rounded-xl border-2 ${selected ? "border-cyan-500" : "border-slate-400 dark:border-slate-600"} bg-white dark:bg-slate-900 p-3 text-slate-900 dark:text-white`}
    >
      {!data.entry && <Handle type="target" position={Position.Left} />}
      <p className="text-xs capitalize">
        {title(data.kind)}
        {data.entry ? " · Start" : ""}
      </p>
      <p className="font-semibold break-words">{data.label}</p>
      {!supported.has(data.kind) && (
        <p className="text-xs text-amber-600">
          Save only · execution unavailable
        </p>
      )}
      {data.kind !== "end" && (
        <Handle type="source" position={Position.Right} />
      )}
    </div>
  );
}
const nodeTypes = { workflow: FlowNode };

export const Workflows: React.FC = () => {
  const canvas = useRef<HTMLDivElement>(null);
  const flow = useRef<ReactFlowInstance<GraphNode, Edge> | null>(null);
  const [nodes, setNodes, changeNodes] = useNodesState<GraphNode>([]);
  const [edges, setEdges, changeEdges] = useEdgesState<Edge>([]);
  const [name, setName] = useState("Untitled workflow");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("draft");
  const [saved, setSaved] = useState<Graph | null>(null);
  const [dirty, setDirty] = useState(false);
  const [offset, setOffset] = useState(0);
  const [selectedSaved, setSelectedSaved] = useState("");
  const [selected, setSelected] = useState("");
  const [configs, setConfigs] = useState<Record<string, string>>({});
  const [source, setSource] = useState("");
  const [target, setTarget] = useState("");
  const [branch, setBranch] = useState('true');
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [review, setReview] = useState(false);
  const [trigger, setTrigger] = useState("{}");
  const [revision, setRevision] = useState("");
  const [confirm, setConfirm] = useState<{
    text: string;
    action: () => void;
  } | null>(null);
  const qc = useQueryClient();
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      dirty && currentLocation.pathname !== nextLocation.pathname,
  );
  useBeforeUnload(
    useCallback(
      (event) => {
        if (dirty) {
          event.preventDefault();
          event.returnValue = "";
        }
      },
      [dirty],
    ),
  );
  const list = useQuery({
    queryKey: ["workflow-definitions", offset],
    queryFn: () =>
      apiRequest<Graph[]>("/api/workflows/", { params: { limit: 50, offset } }),
    retry: false,
  });
  const revisions = useQuery({
    queryKey: ["workflow-revisions", saved?.id, saved?.revision],
    enabled: !!saved,
    queryFn: () =>
      apiRequest<Revision[]>(`/api/workflows/${saved!.id}/revisions`),
    retry: false,
  });
  const history = useQuery({
    queryKey: ["workflow-runs", saved?.id],
    enabled: !!saved,
    queryFn: () => apiRequest<Run[]>(`/api/workflows/${saved!.id}/executions`),
    retry: false,
    refetchInterval: 1000,
  });
  const control = useQuery({
    queryKey: ["workflow-control"],
    queryFn: () =>
      apiRequest<{ paused: boolean; emergency_stopped: boolean }>(
        "/api/security/autopilot-status",
      ),
    refetchInterval: 2000,
    retry: false,
  });
  const selectedNode = nodes.find((node) => node.id === selected);

  useEffect(() => {
    let frame = 0;
    const fit = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        void flow.current?.fitView({ padding: 0.2, maxZoom: 1 });
      });
    };
    const observer = new ResizeObserver(fit);
    if (canvas.current) observer.observe(canvas.current);
    fit();
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [nodes.length, saved?.id]);

  function load(graph: Graph) {
    save.reset();
    setSaved(graph);
    setName(graph.name);
    setDescription(graph.description ?? "");
    setStatus(graph.status);
    setSelectedSaved(graph.id);
    setNodes(
      graph.nodes.map((node) => ({
        id: node.id,
        type: "workflow",
        position: { x: node.position_x, y: node.position_y },
        data: {
          label: node.label,
          kind: node.node_type,
          config: node.config,
          entry: node.is_entry_point,
        },
      })),
    );
    setEdges(
      graph.edges.map((edge) => ({
        id: edge.id,
        source: edge.source_node_id,
        target: edge.target_node_id,
        data: { condition: edge.condition },
        label: edge.label ?? undefined,
      })),
    );
    setConfigs(
      Object.fromEntries(
        graph.nodes.map((node) => [
          node.id,
          JSON.stringify(node.config, null, 2),
        ]),
      ),
    );
    setSelected(graph.nodes[0]?.id ?? "");
    setDirty(false);
    setError("");
    setRevision("");
  }
  function guard(action: () => void, text = "Discard unsaved workflow edits?") {
    if (dirty) setConfirm({ text, action });
    else action();
  }
  function blank() {
    save.reset();
    setSaved(null);
    setName("Untitled workflow");
    setDescription("");
    setStatus("draft");
    setNodes([]);
    setEdges([]);
    setConfigs({});
    setSelected("");
    setSelectedSaved("");
    setDirty(false);
    setError("");
    setNotice("");
  }
  function add(kind: string) {
    if (nodes.length >= 64) {
      setError("A workflow supports up to64 nodes.");
      return;
    }
    const id = crypto.randomUUID();
    const config =
      kind === "ai_prompt"
        ? {
            prompt: "Draft a short caption for manual review.",
            provider: "ollama",
            max_tokens: 128,
          }
        : kind === "delay"
          ? { seconds: 1 }
          : kind === 'condition'
            ? {source:'input',field:'generate',operator:'equals',value:true}
          : kind === 'approval'
            ? {instructions:'Review the saved draft before continuing.'}
          : {};
    setNodes((previous) => [
      ...previous,
      {
        id,
        type: "workflow",
        position: { x: 70 + previous.length * 240, y: 100 },
        data: {
          kind,
          label: title(kind),
          config,
          entry: kind === "trigger" && !previous.some((n) => n.data.entry),
        },
      },
    ]);
    setConfigs((previous) => ({
      ...previous,
      [id]: JSON.stringify(config, null, 2),
    }));
    setSelected(id);
    setDirty(true);
  }
  function template(kind: 'caption' | 'hindi' | 'trends' = 'caption') {
    blank();
    const start = crypto.randomUUID(),
      ai = crypto.randomUUID(),
      end = crypto.randomUUID();
    const config = {
      prompt: kind === 'hindi' ? 'Write a short natural Hindi voiceover in Devanagari from the supplied brief. Keep below600 characters. Do not invent facts or claim actions.' : kind === 'trends' ? 'Suggest three original content ideas using only supplied trend titles, sources and timestamps. State missing context. Never claim live social analytics or guaranteed popularity.' : "Draft a short caption for manual review.",
      provider: "ollama",
      max_tokens: 128,
    };
    setName(kind === 'hindi' ? 'Hindi voice script' : kind === 'trends' ? 'Source-labelled trend ideas' : "Local caption draft");
    setDescription('Review this saved local-text workflow before running. Audio/media rendering and publication are separate explicit operations.');
    setNodes([
      {
        id: start,
        type: "workflow",
        position: { x: 30, y: 90 },
        data: {
          kind: "trigger",
          label: "Manual start",
          config: {},
          entry: true,
        },
      },
      {
        id: ai,
        type: "workflow",
        position: { x: 300, y: 90 },
        data: {
          kind: "ai_prompt",
          label: kind === 'hindi' ? 'Draft Hindi script' : kind === 'trends' ? 'Draft trend ideas' : "Draft caption",
          config,
          entry: false,
        },
      },
      {
        id: end,
        type: "workflow",
        position: { x: 570, y: 90 },
        data: { kind: "end", label: "End", config: {}, entry: false },
      },
    ]);
    setEdges([
      { id: crypto.randomUUID(), source: start, target: ai },
      { id: crypto.randomUUID(), source: ai, target: end },
    ]);
    setConfigs({
      [start]: "{}",
      [ai]: JSON.stringify(config, null, 2),
      [end]: "{}",
    });
    setSelected(ai);
    setDirty(true);
  }
  function conditionalTemplate() {
    const ids=Array.from({length:5},()=>crypto.randomUUID());
    const specs=[
      {kind:'trigger',label:'Manual start',config:{}},
      {kind:'condition',label:'Generate requested?',config:{source:'input',field:'generate',operator:'equals',value:true}},
      {kind:'ai_prompt',label:'Draft caption',config:{prompt:'Draft a short original caption from the supplied brief for owner review.',provider:'ollama',max_tokens:128}},
      {kind:'approval',label:'Review actual draft',config:{instructions:'Read the actual generated draft and supplied facts before approving continuation.'}},
      {kind:'end',label:'End',config:{}},
    ];
    setSaved(null);setSelectedSaved('');setName('Conditional draft with owner review');setDescription('Choose one path from explicit input, then review the actual draft.');setStatus('draft');
    setNodes(specs.map((spec,i)=>({id:ids[i],type:'workflow',position:{x:30+i*240,y:i===4?180:80},data:{...spec,entry:i===0}})));
    const connections:[[number,number,string|null],[number,number,string|null],[number,number,string|null],[number,number,string|null],[number,number,string|null]]=[[0,1,null],[1,2,'true'],[1,4,'false'],[2,3,null],[3,4,null]];
    setEdges(connections.map(([from,to,condition])=>({id:crypto.randomUUID(),source:ids[from],target:ids[to],label:condition??undefined,data:{condition}})));
    setConfigs(Object.fromEntries(specs.map((spec,i)=>[ids[i],JSON.stringify(spec.config,null,2)])));
    setTrigger(JSON.stringify({generate:true,brief:'Use only these supplied verified facts.'},null,2));setSelected(ids[1]);setDirty(true);setError('');setNotice('');
  }
  function connect(connection: Connection) {
    const from = connection.source,
      to = connection.target;
    if (!from || !to) return;
    const reachable = (key: string, visited = new Set<string>()): boolean => {
      if (key === from) return true;
      if (visited.has(key)) return false;
      visited.add(key);
      return edges
        .filter((e) => e.source === key)
        .some((e) => reachable(e.target, visited));
    };
    if (reachable(to)) {
      setError("That connection would create a cycle. Choose a later node.");
      return;
    }
    if (edges.some((e) => e.source === from && e.target === to)) {
      setError("These nodes are already connected.");
      return;
    }
    const condition = nodes.find(n=>n.id===from)?.data.kind==='condition' ? branch : null;
    if(condition&&edges.some(e=>e.source===from&&e.data?.condition===condition)) {setError('This condition already has a '+condition+' connection. Remove it before replacing it.');return;}
    setEdges((previous) =>
      addEdge({ ...connection, id: crypto.randomUUID(), data:{condition},label:condition??undefined }, previous),
    );
    setDirty(true);
    setError("");
  }
  function body() {
    return {
      name,
      description: description || null,
      status,
      trigger_config: saved?.trigger_config ?? null,
      viewport: saved?.viewport ?? null,
      nodes: nodes.map((node) => {
        let config: unknown;
        try {
          config = JSON.parse(configs[node.id] ?? "{}");
        } catch {
          throw new Error(
            "Node configuration must be valid JSON. Your edits are still on this page.",
          );
        }
        if (
          config !== null &&
          (typeof config !== "object" || Array.isArray(config))
        )
          throw new Error("Node configuration must be a JSON object or null.");
        return {
          id: node.id,
          node_type: node.data.kind,
          label: node.data.label,
          position_x: node.position.x,
          position_y: node.position.y,
          config,
          is_entry_point: node.data.entry,
        };
      }),
      edges: edges.map((edge) => ({
        id: edge.id,
        source_node_id: edge.source,
        target_node_id: edge.target,
        condition: edge.data?.condition ?? null,
        label: typeof edge.label === "string" ? edge.label : null,
      })),
      ...(saved ? { expected_revision: saved.revision } : {}),
    };
  }
  const save = useMutation({
    mutationFn: () =>
      apiRequest<Graph>(
        saved ? `/api/workflows/${saved.id}` : "/api/workflows/",
        { method: saved ? "PUT" : "POST", body: body() },
      ),
    onSuccess: (graph) => {
      load(graph);
      setNotice(
        `Saved revision ${graph.revision}. No automatic trigger was enabled.`,
      );
      void qc.invalidateQueries({ queryKey: ["workflow-definitions"] });
    },
  });
  const operation = useMutation({
    mutationFn: async (action: () => Promise<void>) => {
      setError("");
      await action();
    },
    onError: (failure) => setError(message(failure)),
  });
  const run = useMutation({
    mutationFn: () => {
      let data: unknown;
      try {
        data = JSON.parse(trigger);
      } catch {
        throw new Error("Trigger data must be valid JSON.");
      }
      if (!data || typeof data !== "object" || Array.isArray(data))
        throw new Error("Trigger data must be a JSON object.");
      return apiRequest<Run>(`/api/workflows/${saved!.id}/execute`, {
        method: "POST",
        body: {
          expected_revision: saved!.revision,
          fingerprint: saved!.fingerprint,
          trigger_data: data,
        },
      });
    },
    onSuccess: () => {
      setReview(false);
      setNotice(
        "The saved run is queued. Its receipt will show the actual outcome.",
      );
      void qc.invalidateQueries({ queryKey: ["workflow-runs"] });
    },
  });
  const busy = save.isPending || operation.isPending;
  const active = history.data?.some((item) =>
    ["queued", "running"].includes(item.status),
  );

  return (
    <section className="space-y-5 min-w-0">
      <h1 className="text-3xl font-bold">Workflows</h1>
      <p className="text-sm">
        Save and reopen real graphs with revision history. Manual runs support
        manual paths using Trigger, local AI Prompt, Delay, Condition, Approval and End. Other
        nodes can be saved for planning; they do not execute. Generated text
        never publishes or performs an action.
      </p>
      <div className="flex flex-wrap gap-3 items-end">
        <div className="flex-1 min-w-48">
          <Field label="Saved workflow">
            <select
              className={inputClass}
              value={selectedSaved}
              onChange={(event) => setSelectedSaved(event.target.value)}
            >
              <option value="">Choose a saved workflow</option>
              {saved && !list.data?.some((graph) => graph.id === saved.id) && (
                <option value={saved.id}>
                  {saved.name} · revision {saved.revision}
                </option>
              )}
              {list.data?.map((graph) => (
                <option key={graph.id} value={graph.id}>
                  {graph.name} · revision {graph.revision}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <Button
          disabled={!selectedSaved || busy}
          onClick={() =>
            guard(() =>
              operation.mutate(async () =>
                load(
                  await apiRequest<Graph>(`/api/workflows/${selectedSaved}`),
                ),
              ),
            )
          }
        >
          Open saved workflow
        </Button>
        <Button
          variant="secondary"
          onClick={() => guard(blank)}
          disabled={busy}
        >
          New workflow
        </Button>
        <Button
          variant="secondary"
          onClick={() => guard(template)}
          disabled={busy}
        >
          Use caption draft template
        </Button>
        <Button variant="secondary" disabled={busy} onClick={()=>guard(()=>template('hindi'))}>Use Hindi voice script template</Button>
        <Button variant="secondary" disabled={busy} onClick={()=>guard(()=>template('trends'))}>Use trend ideas template</Button>
        <Button variant="secondary" disabled={busy} onClick={()=>guard(conditionalTemplate)}>Use conditional review template</Button>
      </div>
      {list.isError && (
        <p role="alert">
          Saved workflows could not be loaded.{" "}
          <Button onClick={() => list.refetch()}>Retry workflows</Button>
        </p>
      )}
      <div className="flex gap-3 items-center">
        <Button
          size="sm"
          disabled={offset === 0}
          onClick={() => setOffset(Math.max(0, offset - 50))}
        >
          Previous workflows
        </Button>
        <span>Page {offset / 50 + 1}</span>
        <Button
          size="sm"
          disabled={list.data?.length !== 50}
          onClick={() => setOffset(offset + 50)}
        >
          Next workflows
        </Button>
      </div>
      {(error || save.isError) && (
        <p
          role="alert"
          className="border border-red-500 rounded p-3 break-words"
        >
          {error || message(save.error)}
        </p>
      )}
      {notice && (
        <p role="status" className="border border-cyan-500 rounded p-3">
          {notice}
        </p>
      )}
      <Card>
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="Workflow name">
            <input
              className={inputClass}
              maxLength={256}
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setDirty(true);
              }}
            />
          </Field>
          <Field label="Definition status">
            <select
              className={inputClass}
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setDirty(true);
              }}
            >
              <option value="draft">Draft · manual run</option>
              <option value="paused">Paused</option>
              <option value="archived">Archived</option>
              {status === "active" && (
                <option value="active" disabled>
                  Legacy active · choose a new status
                </option>
              )}
            </select>
          </Field>
          <Field label="Workflow description">
            <textarea
              className={inputClass}
              maxLength={4000}
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                setDirty(true);
              }}
            />
          </Field>
          <div className="space-y-2 text-sm">
            <p>
              {dirty
                ? "Unsaved edits"
                : saved
                  ? `Saved revision ${saved.revision}`
                  : "New empty graph"}
            </p>
            <div className="flex flex-wrap gap-2">
              <Button
                disabled={busy || !name.trim()}
                onClick={() => save.mutate()}
              >
                Save workflow
              </Button>
              <Button
                variant="secondary"
                disabled={busy || !name.trim()}
                onClick={() =>
                  operation.mutate(async () => {
                    const copy = body();
                    delete copy.expected_revision;
                    const ids = new Map(
                      copy.nodes.map((node) => [node.id, crypto.randomUUID()]),
                    );
                    copy.name = name.slice(0, 247) + " (copy)";
                    const graph = await apiRequest<Graph>("/api/workflows/", {
                      method: "POST",
                      body: {
                        ...copy,
                        nodes: copy.nodes.map((node) => ({
                          ...node,
                          id: ids.get(node.id),
                        })),
                        edges: copy.edges.map((edge) => ({
                          ...edge,
                          id: crypto.randomUUID(),
                          source_node_id: ids.get(edge.source_node_id),
                          target_node_id: ids.get(edge.target_node_id),
                        })),
                      },
                    });
                    load(graph);
                    setNotice(
                      "Saved your current edits as a separate copy. The original workflow was preserved.",
                    );
                    await qc.invalidateQueries({
                      queryKey: ["workflow-definitions"],
                    });
                  })
                }
              >
                Save as new copy
              </Button>
              <Button
                variant="secondary"
                disabled={
                  busy || dirty || !saved?.execution_available || active
                }
                onClick={() => {
                  run.reset();
                  setReview(true);
                }}
              >
                Review manual run
              </Button>
              {saved && (
                <Button
                  variant="ghost"
                  onClick={() =>
                    guard(() =>
                      operation.mutate(async () =>
                        load(
                          await apiRequest<Graph>(`/api/workflows/${saved.id}`),
                        ),
                      ),
                    )
                  }
                >
                  Reload saved version
                </Button>
              )}
            </div>
          </div>
        </div>
        {saved?.validation_errors.map((item) => (
          <p
            className="mt-3 text-sm text-amber-600 dark:text-amber-300"
            key={item}
          >
            {item}
          </p>
        ))}
      </Card>
      <div className="flex flex-wrap gap-2">
        {kinds
          .filter((kind) => supported.has(kind))
          .map((kind) => (
            <Button
              key={kind}
              size="sm"
              variant="secondary"
              disabled={busy || nodes.length >= 64}
              onClick={() => add(kind)}
            >{`Add ${title(kind)}${supported.has(kind) ? "" : " (save only)"}`}</Button>
          ))}
      </div>
      <details className="rounded-xl border border-slate-300 dark:border-white/20 p-3">
        <summary className="cursor-pointer text-sm">
          More planning nodes · execution unavailable
        </summary>
        <div className="mt-3 flex flex-wrap gap-2">
          {kinds
            .filter((kind) => !supported.has(kind))
            .map((kind) => (
              <Button
                key={kind}
                size="sm"
                variant="secondary"
                disabled={busy || nodes.length >= 64}
                onClick={() => add(kind)}
              >{`Add ${title(kind)} (save only)`}</Button>
            ))}
        </div>
      </details>
      <div
        ref={canvas}
        className="h-[430px] sm:h-[500px] border rounded-xl overflow-hidden bg-slate-100 dark:bg-slate-950"
      >
        <ReactFlow
          onInit={(instance) => {
            flow.current = instance;
            void instance.fitView({ padding: 0.2, maxZoom: 1 });
          }}
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={(changes) => {
            changeNodes(changes);
            if (
              changes.some(
                (change) => !["select", "dimensions"].includes(change.type),
              )
            )
              setDirty(true);
          }}
          onEdgesChange={(changes) => {
            changeEdges(changes);
            if (changes.some((change) => change.type !== "select"))
              setDirty(true);
          }}
          onConnect={connect}
          onNodeClick={(_, node) => setSelected(node.id)}
          fitView
          minZoom={0.1}
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>
      <Card>
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">Node inspector</h2>
            <Field label="Selected node">
              <select
                className={inputClass}
                value={selected}
                onChange={(e) => setSelected(e.target.value)}
              >
                <option value="">Choose a node</option>
                {nodes.map((node) => (
                  <option key={node.id} value={node.id}>
                    {node.data.label} · {title(node.data.kind)}
                  </option>
                ))}
              </select>
            </Field>
            {selectedNode && (
              <>
                <Field label="Node label">
                  <input
                    className={inputClass}
                    maxLength={128}
                    value={selectedNode.data.label}
                    onChange={(e) => {
                      setNodes((previous) =>
                        previous.map((node) =>
                          node.id === selected
                            ? {
                                ...node,
                                data: { ...node.data, label: e.target.value },
                              }
                            : node,
                        ),
                      );
                      setDirty(true);
                    }}
                  />
                </Field>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    disabled={selectedNode.data.kind !== "trigger"}
                    checked={selectedNode.data.entry}
                    onChange={(e) => {
                      setNodes((previous) =>
                        previous.map((node) => ({
                          ...node,
                          data: {
                            ...node.data,
                            entry: e.target.checked
                              ? node.id === selected
                              : node.id === selected
                                ? false
                                : node.data.entry,
                          },
                        })),
                      );
                      setDirty(true);
                    }}
                  />
                  Manual starting node
                </label>
                <Field label="Node configuration (JSON)">
                  <textarea
                    className={`${inputClass} font-mono`}
                    rows={7}
                    value={configs[selected] ?? "{}"}
                    onChange={(e) => {
                      setConfigs((previous) => ({
                        ...previous,
                        [selected]: e.target.value,
                      }));
                      setDirty(true);
                    }}
                  />
                </Field>
                <p className="text-xs text-slate-500">
                  AI Prompt: prompt, provider="ollama", max_tokens (1–1024).
                  Delay: seconds (0–30). Trigger/End: empty object. Do not put
                  credentials in graph configuration.
                  Conditions read bounded input fields or previous output using equals, not_equals, contains or exists. Approval requires review instructions.
                </p>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() =>
                    setConfirm({
                      text: "Remove this node and its connected edges?",
                      action: () => {
                        setNodes((previous) =>
                          previous.filter((node) => node.id !== selected),
                        );
                        setEdges((previous) =>
                          previous.filter(
                            (edge) =>
                              edge.source !== selected &&
                              edge.target !== selected,
                          ),
                        );
                        setSelected("");
                        setDirty(true);
                      },
                    })
                  }
                >
                  Remove selected node
                </Button>
              </>
            )}
          </div>
          <div className="space-y-3">
            <h2 className="text-lg font-semibold">Connections</h2>
            <Field label="Connect from">
              <select
                className={inputClass}
                value={source}
                onChange={(e) => setSource(e.target.value)}
              >
                <option value="">Choose source</option>
                {nodes.map((node) => (
                  <option key={node.id} value={node.id}>
                    {node.data.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Connect to">
              <select
                className={inputClass}
                value={target}
                onChange={(e) => setTarget(e.target.value)}
              >
                <option value="">Choose target</option>
                {nodes.map((node) => (
                  <option key={node.id} value={node.id}>
                    {node.data.label}
                  </option>
                ))}
              </select>
            </Field>
            {nodes.find(n=>n.id===source)?.data.kind==='condition'&&<Field label="Connection branch"><select className={inputClass} value={branch} onChange={e=>setBranch(e.target.value)}><option value="true">True</option><option value="false">False</option></select></Field>}
            <Button
              size="sm"
              disabled={!source || !target || edges.length >= 128}
              onClick={() =>
                connect({
                  source,
                  target,
                  sourceHandle: null,
                  targetHandle: null,
                })
              }
            >
              Connect nodes
            </Button>
            {edges.map((edge) => (
              <div
                key={edge.id}
                className="text-sm flex flex-wrap justify-between gap-2"
              >
                <span className="break-all">
                  {nodes.find((node) => node.id === edge.source)?.data.label} →{" "}
                  {nodes.find((node) => node.id === edge.target)?.data.label}
                  {typeof edge.data?.condition==='string'?' · '+edge.data.condition:''}
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setEdges((previous) =>
                      previous.filter((item) => item.id !== edge.id),
                    );
                    setDirty(true);
                  }}
                >
                  Remove connection
                </Button>
              </div>
            ))}
          </div>
        </div>
      </Card>
      {saved && (
        <Card>
          <h2 className="text-lg font-semibold mb-3">Saved revision history</h2>
          {revisions.isError && (
            <p role="alert">Revision history unavailable.</p>
          )}
          <div className="flex flex-wrap items-end gap-3">
            <Field label="Revision to restore">
              <select
                className={inputClass}
                value={revision}
                onChange={(e) => setRevision(e.target.value)}
              >
                <option value="">Choose revision</option>
                {revisions.data?.map((item) => (
                  <option key={item.revision} value={item.revision}>
                    Revision {item.revision} · {item.name}
                  </option>
                ))}
              </select>
            </Field>
            <Button
              disabled={!revision || busy}
              onClick={() =>
                setConfirm({
                  text: "Restore this earlier definition as a new revision? Unsaved edits will be discarded. Existing run receipts keep their original snapshot.",
                  action: () =>
                    operation.mutate(async () => {
                      const graph = await apiRequest<Graph>(
                        `/api/workflows/${saved.id}/restore`,
                        {
                          method: "POST",
                          body: {
                            expected_revision: saved.revision,
                            revision: Number(revision),
                          },
                        },
                      );
                      load(graph);
                      setNotice(`Restored as revision ${graph.revision}.`);
                      await qc.invalidateQueries({
                        queryKey: ["workflow-definitions"],
                      });
                    }),
                })
              }
            >
              Restore revision
            </Button>
            <Button
              variant="danger"
              disabled={busy}
              onClick={() =>
                setConfirm({
                  text: "Remove this unused workflow and its revisions? Workflows with execution history are retained; archive them instead.",
                  action: () =>
                    operation.mutate(async () => {
                      await apiRequest(`/api/workflows/${saved.id}`, {
                        method: "DELETE",
                        params: { expected_revision: saved.revision },
                      });
                      blank();
                      await qc.invalidateQueries({
                        queryKey: ["workflow-definitions"],
                      });
                    }),
                })
              }
            >
              Remove unused workflow
            </Button>
          </div>
        </Card>
      )}
      <Card>
        <h2 className="text-lg font-semibold">Execution receipts</h2>
        <p className="my-2 text-sm">
          {control.isError
            ? "Runtime controls unavailable."
            : control.data?.emergency_stopped
              ? "Emergency stop active."
              : control.data?.paused
                ? "Runtime paused. Queued runs wait until you explicitly resume."
                : "Runtime resumed."}{" "}
          Pausing holds work between nodes; cancelling or emergency stop
          interrupts supported running work.
        </p>
        {history.isError && <p role="alert">Saved receipts unavailable.</p>}
        {history.data?.map((item) => (
          <div
            className="border-t border-slate-300 dark:border-white/15 py-3 space-y-2"
            key={item.id}
          >
            <p className="font-semibold">
              Run: {item.status} · revision{" "}
              {item.revision ?? "legacy/unverified"}
            </p>
            <p className="text-xs break-all">{item.id}</p>
            <p className="text-sm">{item.message}</p>
            {item.error && <p className="text-sm text-red-500">{item.error}</p>}
            {["queued", "running", "waiting_approval"].includes(item.status) && (
              <Button
                size="sm"
                onClick={() =>
                  operation.mutate(async () => {
                    await apiRequest(
                      `/api/workflows/${saved!.id}/executions/${item.id}/cancel`,
                      { method: "POST" },
                    );
                    await history.refetch();
                  })
                }
              >
                Cancel run
              </Button>
            )}
            {item.status==='waiting_approval'&&<Link to="/approvals" className="underline text-sm">Open saved checkpoint in Review inbox</Link>}
            {item.execution_verified &&
              item.execution_log.map((event, index) => (
                <div className="text-sm" key={index}>
                  <p>
                    {title(event.node_type)} · {event.event}
                  </p>
                  {typeof event.output?.matched==='boolean'&&<p>Chosen branch: {event.output.matched?'true':'false'}</p>}
                  {event.output?.decision&&<p>Owner review: {event.output.decision}</p>}
                  {event.output?.text && (
                    <pre className="whitespace-pre-wrap break-words rounded bg-slate-100 dark:bg-slate-950 p-3">
                      {event.output.text}
                    </pre>
                  )}
                </div>
              ))}
          </div>
        ))}
        {saved && history.data?.length === 0 && (
          <p>No saved executions for this workflow.</p>
        )}
      </Card>
      <Modal
        open={review}
        onClose={() => {
          if (!run.isPending) setReview(false);
        }}
        title="Review manual local run"
      >
        <p className="mb-3 text-sm">
          Run saved revision {saved?.revision} of {saved?.name}? This uses its
          fixed graph snapshot, may generate local AI advice and has no
          publishing or other action tools. Earlier saved output may be passed
          to the next AI node. Results are saved in the local database.
        </p>
        <Field label="Trigger data (JSON)">
          <textarea
            className={`${inputClass} font-mono`}
            rows={4}
            value={trigger}
            onChange={(e) => setTrigger(e.target.value)}
          />
        </Field>
        {run.isError && (
          <p role="alert" className="text-red-500 my-3">
            {message(run.error)}
          </p>
        )}
        <Button disabled={run.isPending} onClick={() => run.mutate()}>
          Confirm manual run
        </Button>
      </Modal>
      <Modal
        open={!!confirm}
        onClose={() => setConfirm(null)}
        title="Confirm workflow change"
      >
        <p className="mb-4">{confirm?.text}</p>
        <div className="flex gap-3">
          <Button
            onClick={() => {
              const action = confirm?.action;
              setConfirm(null);
              action?.();
            }}
          >
            Confirm change
          </Button>
          <Button variant="secondary" onClick={() => setConfirm(null)}>
            Keep current edits
          </Button>
        </div>
      </Modal>
      <Modal
        open={blocker.state === "blocked"}
        onClose={() => {
          if (blocker.state === "blocked") blocker.reset();
        }}
        title="Unsaved workflow edits"
      >
        <p className="mb-4">
          Leave this page and discard unsaved workflow edits?
        </p>
        <div className="flex gap-3">
          <Button
            onClick={() => {
              if (blocker.state === "blocked") blocker.proceed();
            }}
          >
            Discard edits and leave
          </Button>
          <Button
            variant="secondary"
            onClick={() => {
              if (blocker.state === "blocked") blocker.reset();
            }}
          >
            Stay and keep editing
          </Button>
        </div>
      </Modal>
    </section>
  );
};
