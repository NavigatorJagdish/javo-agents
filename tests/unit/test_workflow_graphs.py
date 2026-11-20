"""Invalid or unsupported graph configuration must fail before any dispatch."""

from copy import deepcopy
import pytest

from app.services.workflow_graphs import Definition, execution_plan
from app.services.workflow_graphs import Condition, condition_result


def graph():
    return {
        "name": "Local draft",
        "nodes": [
            {"id": "start", "node_type": "trigger", "label": "Start", "is_entry_point": True},
            {
                "id": "text",
                "node_type": "ai_prompt",
                "label": "Text",
                "config": {"prompt": "Draft text", "provider": "ollama", "max_tokens": 64},
            },
            {"id": "end", "node_type": "end", "label": "End"},
        ],
        "edges": [
            {"source_node_id": "start", "target_node_id": "text"},
            {"source_node_id": "text", "target_node_id": "end"},
        ],
    }


@pytest.mark.parametrize(
    "config",
    [
        {"prompt": "Text", "provider": "gemini"},
        {"prompt": "Text", "provider": "openai"},
        {"prompt": "Text", "max_tokens": True},
        {"prompt": "Text", "max_tokens": 1025},
        {"prompt": "Text", "tool": "publish"},
        {"prompt": ""},
        {"prompt": "x" * 8001},
    ],
)
def test_invalid_text_actions_cannot_enter_plan(config):
    value = graph()
    value["nodes"][1]["config"] = config
    with pytest.raises(ValueError):
        execution_plan(value)


def test_branch_disconnected_and_non_manual_entries_require_implementation():
    base = graph()
    disconnected = deepcopy(base)
    disconnected["nodes"].append({"id": "orphan", "node_type": "end", "label": "Disconnected"})
    branch = deepcopy(base)
    branch["edges"].append({"source_node_id": "start", "target_node_id": "end"})
    automatic = deepcopy(base)
    automatic["nodes"][0]["node_type"] = "schedule"
    for value in (disconnected, branch, automatic):
        # Planning a draft may be valid; executing unsupported work is not.
        Definition.model_validate(value)
        with pytest.raises(ValueError):
            execution_plan(value)


def test_delays_and_json_are_finite_bounded_and_not_code():
    for seconds in (-1, 31, True, "1"):
        value = graph()
        value["nodes"][1].update(node_type="delay", config={"seconds": seconds})
        with pytest.raises(ValueError):
            execution_plan(value)
    value = graph()
    value["nodes"][1]["config"] = {"prompt": "Text", "max_tokens": float("nan")}
    with pytest.raises(ValueError):
        Definition.model_validate(value)


def test_conditions_are_data_only_missing_fields_fail_closed_and_scalar_types_are_explicit():
    assert condition_result(
        {"field": "brand.language", "operator": "equals", "value": "hi"},
        {"brand": {"language": "hi"}},
        "",
    )
    assert not condition_result(
        {"field": "missing", "operator": "not_equals", "value": "approved"}, {}, ""
    )
    assert not condition_result(
        {"field": "ready", "operator": "equals", "value": True}, {"ready": 1}, ""
    )
    assert condition_result(
        {"source": "previous_output", "operator": "contains", "value": "literal(.*)"},
        {},
        "Only literal(.*) data",
    )
    for config in [
        {"field": "__class__", "operator": "equals"},
        {"field": "a", "operator": "exec", "value": "x"},
        {"field": "a", "operator": "contains", "value": 42},
        {"source": "previous_output", "field": "ignored", "operator": "exists"},
    ]:
        with pytest.raises(ValueError):
            Condition.model_validate(config)
