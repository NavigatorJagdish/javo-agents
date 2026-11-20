"""Bounded saved graph contracts, snapshots and deterministic validation."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.local_identity import OWNER_IDS
from app.models.workflow import NodeType, Workflow, WorkflowRevision


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class Node(Input):
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=36)
    node_type: NodeType
    label: str = Field(min_length=1, max_length=128)
    position_x: float = Field(default=0.0, ge=-100000, le=100000)
    position_y: float = Field(default=0.0, ge=-100000, le=100000)
    config: dict[str, Any] | None = None
    is_entry_point: bool = Field(default=False, strict=True)


class Edge(Input):
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=36)
    source_node_id: str = Field(min_length=1, max_length=36)
    target_node_id: str = Field(min_length=1, max_length=36)
    condition: str | None = Field(default=None, max_length=256)
    label: str | None = Field(default=None, max_length=128)


class Definition(Input):
    name: str = Field(min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=4000)
    status: Literal["draft", "paused", "archived"] = "draft"
    trigger_config: dict[str, Any] | None = None
    viewport: dict[str, Any] | None = None
    nodes: list[Node] = Field(default_factory=list, max_length=64)
    edges: list[Edge] = Field(default_factory=list, max_length=128)

    @model_validator(mode="after")
    def validate_graph(self):
        # JSON-mode serialization can normalize NaN inside Any-valued config to
        # null. Validate the original Python values before that conversion.
        bounded_json(self.model_dump(mode="python"), 131072)
        node_ids, edge_ids = [n.id for n in self.nodes], [e.id for e in self.edges]
        if len(set(node_ids)) != len(node_ids) or len(set(edge_ids)) != len(edge_ids):
            raise ValueError("Node and edge identifiers must be unique")
        adjacency = {key: [] for key in node_ids}
        degrees = dict.fromkeys(node_ids, 0)
        pairs = set()
        for edge in self.edges:
            pair = edge.source_node_id, edge.target_node_id
            if any(key not in adjacency for key in pair):
                raise ValueError("Every edge must connect nodes in this graph")
            if pair in pairs:
                raise ValueError("Duplicate node connections are not allowed")
            pairs.add(pair)
            adjacency[pair[0]].append(pair[1])
            degrees[pair[1]] += 1
        queue = [key for key, degree in degrees.items() if degree == 0]
        visited = 0
        while queue:
            key = queue.pop()
            visited += 1
            for target in adjacency[key]:
                degrees[target] -= 1
                if degrees[target] == 0:
                    queue.append(target)
        if visited != len(node_ids):
            raise ValueError("Workflow contains a cycle; remove the circular connection")
        return self


def bounded_json(value, limit=16384):
    def depth(item, level):
        if level > 16:
            raise ValueError("JSON nesting exceeds its supported limit")
        if isinstance(item, dict):
            for child in item.values():
                depth(child, level + 1)
        elif isinstance(item, list):
            for child in item:
                depth(child, level + 1)

    depth(value, 0)
    try:
        size = len(json.dumps(value, allow_nan=False).encode("utf-8"))
    except (ValueError, TypeError):
        raise ValueError("Workflow data must be finite supported JSON") from None
    if size > limit:
        raise ValueError("Workflow data exceeds its storage limit")


def fingerprint(definition):
    return hashlib.sha256(
        json.dumps(definition, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


async def owned_workflow(session, workflow_id):
    workflow = (
        await session.execute(
            select(Workflow)
            .where(Workflow.id == workflow_id, Workflow.user_id.in_(OWNER_IDS))
            .options(selectinload(Workflow.nodes), selectinload(Workflow.edges))
        )
    ).scalar_one_or_none()
    if workflow is None:
        raise HTTPException(404, "Workflow not found")
    return workflow


async def revision_number(session, workflow_id):
    return (
        await session.scalar(
            select(func.max(WorkflowRevision.revision)).where(
                WorkflowRevision.workflow_id == workflow_id
            )
        )
    ) or 0


def snapshot(workflow):
    return {
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status.value,
        "trigger_config": workflow.trigger_config,
        "viewport": workflow.viewport,
        "nodes": [
            {
                "id": n.id,
                "node_type": n.node_type.value,
                "label": n.label,
                "position_x": float(n.position_x),
                "position_y": float(n.position_y),
                "config": n.config,
                "is_entry_point": n.is_entry_point,
            }
            for n in sorted(workflow.nodes, key=lambda n: n.id)
        ],
        "edges": [
            {
                "id": e.id,
                "source_node_id": e.source_node_id,
                "target_node_id": e.target_node_id,
                "condition": e.condition,
                "label": e.label,
            }
            for e in sorted(workflow.edges, key=lambda e: e.id)
        ],
    }


SUPPORTED_NODES = {"trigger", "ai_prompt", "delay", "condition", "approval", "end"}


class Condition(Input):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)
    source: Literal['input', 'previous_output'] = 'input'
    field: str = Field(default='', max_length=320)
    operator: Literal['equals', 'not_equals', 'contains', 'exists']
    value: str | bool | int | float | None = None

    @model_validator(mode='after')
    def check_field(self):
        if self.source == 'input' and (not self.field or len(self.field.split('.')) > 8 or
                any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,39}', key) for key in self.field.split('.'))):
            raise ValueError('Condition needs a bounded dotted JSON field')
        if self.source == 'previous_output' and self.field:
            raise ValueError('Previous-output conditions do not use a field path')
        if isinstance(self.value, str) and len(self.value) > 1024:
            raise ValueError('Condition value is too long')
        if self.operator == 'contains' and not isinstance(self.value, str):
            raise ValueError('Contains needs a text value')
        return self


def condition_result(config, input_data, previous):
    """Data-only predicate. A branch never grants permission or executes code."""
    rule = Condition.model_validate(config)
    found, actual = True, previous
    if rule.source == 'input':
        actual = input_data
        for key in rule.field.split('.'):
            if not isinstance(actual, dict) or key not in actual:
                found = False
                break
            actual = actual[key]
    if rule.operator == 'exists':
        return found
    if not found:
        return False
    if rule.operator == 'contains':
        return isinstance(actual, str) and rule.value in actual
    equal = type(actual) is type(rule.value) and actual == rule.value
    return equal if rule.operator == 'equals' else not equal


def conditional_review_template():
    ids = [str(uuid4()) for _ in range(5)]
    kinds = [('trigger', 'Manual start', {}),
        ('condition', 'Generate requested?', {'source':'input','field':'generate','operator':'equals','value':True}),
        ('ai_prompt', 'Draft caption', {'prompt':'Draft a short original caption from the supplied brief for owner review.','provider':'ollama','max_tokens':128}),
        ('approval', 'Review actual draft', {'instructions':'Read the actual generated draft and supplied facts before approving continuation.'}),
        ('end', 'End', {})]
    return Definition(name='Conditional draft with owner review', description='Provide generate=true and a verified brief. False skips drafting; true waits for owner review.',
        nodes=[Node(id=ids[i],node_type=kind,label=label,config=config,is_entry_point=i==0,
            position_x=30+i*240,position_y=180 if i==4 else 80) for i,(kind,label,config) in enumerate(kinds)],
        edges=[Edge(source_node_id=ids[a],target_node_id=ids[b],condition=condition)
            for a,b,condition in [(0,1,None),(1,2,'true'),(1,4,'false'),(2,3,None),(3,4,None)]]).model_dump(mode='json')


def execution_plan(definition):
    """Bounded manual DAG; conditions select one path, with no parallel fan-out."""
    graph = Definition.model_validate(definition)
    if graph.status != "draft":
        raise ValueError("Only a saved draft can be manually run in this build")
    if not graph.nodes:
        raise ValueError("Add a manual Trigger and End before running")
    if any(n.node_type.value not in SUPPORTED_NODES for n in graph.nodes):
        raise ValueError("This graph contains nodes whose execution is not available")
    entries = [n for n in graph.nodes if n.is_entry_point]
    if len(entries) != 1 or entries[0].node_type != NodeType.TRIGGER:
        raise ValueError("Choose exactly one manual Trigger as the starting node")
    successors = {node.id: [] for node in graph.nodes}
    incoming = dict.fromkeys((n.id for n in graph.nodes), 0)
    for edge in graph.edges:
        successors[edge.source_node_id].append(edge)
        incoming[edge.target_node_id] += 1
    if incoming[entries[0].id]:
        raise ValueError("Manual Trigger cannot have incoming connections")
    node_map = {n.id: n for n in graph.nodes}
    order, visited = [], set()
    def walk(key):
        if key in visited:
            return
        visited.add(key)
        order.append(node_map[key])
        for edge in successors[key]:
            walk(edge.target_node_id)
    walk(entries[0].id)
    if len(visited) != len(graph.nodes):
        raise ValueError("Connect every node to the manual Trigger")
    if sum(n.node_type == NodeType.TRIGGER for n in order) != 1:
        raise ValueError("Only one manual Trigger is supported")
    total_wait, ai_count, approvals = 0, 0, 0
    for node in order:
        outgoing = successors[node.id]
        if node.node_type == NodeType.END:
            if outgoing:
                raise ValueError('End cannot have outgoing connections')
        elif node.node_type == NodeType.CONDITION:
            if len(outgoing) != 2 or {e.condition for e in outgoing} != {'true', 'false'}:
                raise ValueError('Condition needs exactly one true and one false connection')
        elif len(outgoing) != 1 or outgoing[0].condition:
            raise ValueError('Each ordinary node needs one unconditional connection')
        config = node.config or {}
        if node.node_type in {NodeType.TRIGGER, NodeType.END}:
            if config:
                raise ValueError("Manual Trigger and End need an empty configuration")
        elif node.node_type == NodeType.DELAY:
            if (
                set(config) != {"seconds"}
                or type(config["seconds"]) not in (int, float)
                or not 0 <= config["seconds"] <= 30
            ):
                raise ValueError("Delay requires seconds between0 and30")
            total_wait += config["seconds"]
        elif node.node_type == NodeType.AI_PROMPT:
            ai_count += 1
            if (
                set(config) - {"prompt", "provider", "max_tokens"}
                or not isinstance(config.get("prompt"), str)
                or not 1 <= len(config["prompt"].strip()) <= 8000
            ):
                raise ValueError("AI Prompt needs nonempty prompt text up to8000 characters")
            if config.get("provider", "ollama") != "ollama":
                raise ValueError("Only the explicitly configured local provider is supported")
            tokens = config.get("max_tokens", 256)
            if type(tokens) is not int or not 1 <= tokens <= 1024:
                raise ValueError("AI Prompt token limit must be between1 and1024")
        elif node.node_type == NodeType.CONDITION:
            Condition.model_validate(config)
        elif node.node_type == NodeType.APPROVAL:
            approvals += 1
            if set(config) != {'instructions'} or not isinstance(config['instructions'], str) or not 1 <= len(config['instructions'].strip()) <= 2000:
                raise ValueError('Approval needs review instructions up to2000 characters')
    if total_wait > 30 or ai_count > 3 or approvals > 3:
        raise ValueError("A run supports at most30seconds of delay, three AI prompts and three review gates")
    return order
