"""Tests for Workflow DSL parser."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))
import pytest

from axiomflow.dsl.parser import WorkflowParser

VALID_WORKFLOW_YAML = """
workflow:
  name: sample-workflow
  version: "1.0.0"
  inputs:
    - name: input1
      type: string
      required: true
  personas:
    - id: dev
      name: Developer
      role: coder
      capabilities: [code]
  steps:
    - id: step1
      name: Step One
      persona: dev
      action: run
      inputs: {}
      outputs:
        result: string
      gates: [PF-01]
    - id: step2
      name: Step Two
      persona: dev
      action: run
      inputs:
        prev_result: step1.result
      outputs:
        final: string
  edges:
    - from: step1
      to: step2
  gates:
    - id: PF-01
      type: pre_flight
      conditions: []
"""

VALID_WORKFLOW_JSON = """
{
  "workflow": {
    "name": "json-workflow",
    "version": "1.0.0",
    "inputs": [
      {"name": "input1", "type": "string", "required": true}
    ],
    "personas": [
      {"id": "dev", "name": "Developer", "role": "coder", "capabilities": ["code"]}
    ],
    "steps": [
      {
        "id": "step1",
        "name": "Step One",
        "persona": "dev",
        "action": "run",
        "inputs": {},
        "outputs": {"result": "string"}
      }
    ],
    "edges": [],
    "gates": []
  }
}
"""


def test_parse_yaml_workflow():
    parser = WorkflowParser()
    result = parser.parse(VALID_WORKFLOW_YAML)
    assert result["name"] == "sample-workflow"


def test_parse_json_workflow():
    parser = WorkflowParser()
    result = parser.parse(VALID_WORKFLOW_JSON)
    assert result["name"] == "json-workflow"


def test_invalid_yaml_syntax():
    parser = WorkflowParser()
    with pytest.raises(ValueError):
        parser.parse("workflow: [")


def test_missing_persona_reference():
    yaml_text = VALID_WORKFLOW_YAML.replace("persona: dev", "persona: unknown")
    parser = WorkflowParser()
    with pytest.raises(ValueError):
        parser.parse(yaml_text)


def test_missing_gate_reference():
    yaml_text = VALID_WORKFLOW_YAML.replace("gates: [PF-01]", "gates: [PF-99]")
    parser = WorkflowParser()
    with pytest.raises(ValueError):
        parser.parse(yaml_text)


def test_circular_dependencies():
    yaml_text = VALID_WORKFLOW_YAML.replace(
        "edges:\n    - from: step1\n      to: step2",
        "edges:\n    - from: step1\n      to: step2\n    - from: step2\n      to: step1",
    )
    parser = WorkflowParser()
    with pytest.raises(ValueError):
        parser.parse(yaml_text)


def test_unsatisfied_input_reference():
    yaml_text = VALID_WORKFLOW_YAML.replace("result: string", "other: string")
    parser = WorkflowParser()
    with pytest.raises(ValueError):
        parser.parse(yaml_text)


def test_invalid_retry_config():
    yaml_text = VALID_WORKFLOW_YAML.replace(
        "outputs:\n        final: string",
        "outputs:\n        final: string\n      retry:\n        backoff_strategy: invalid",
    )
    parser = WorkflowParser()
    with pytest.raises(ValueError):
        parser.parse(yaml_text)
