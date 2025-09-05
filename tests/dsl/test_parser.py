"""Tests for workflow DSL parser."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from axiomflow.dsl.parser import parse_workflow

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
      estimated_cpu: 1.0
      estimated_memory: 256
    - id: step2
      name: Step Two
      persona: dev
      action: run
      inputs:
        prev_result: step1.result
      outputs:
        final: string
      estimated_cpu: 2.0
      estimated_memory: 512
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
        "outputs": {"result": "string"},
        "estimated_cpu": 1.0,
        "estimated_memory": 256
      }
    ],
    "edges": [],
    "gates": []
  }
}
"""

ESTIMATE_WORKFLOW_YAML = """
workflow:
  name: estimate-workflow
  version: "1.0.0"
  inputs: []
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
      estimated_cpu: 0.5
      estimated_memory: 128
    - id: step2
      name: Step Two
      persona: dev
      action: run
      inputs:
        prev_result: step1.result
      outputs:
        final: string
      estimated_cpu: 1.5
      estimated_memory: 256
  edges:
    - from: step1
      to: step2
  gates: []
"""


def _write_temp(path: Path, content: str) -> Path:
    file_path = path / "workflow.yaml"
    file_path.write_text(content)
    return file_path


def test_parse_yaml_workflow(tmp_path: Path) -> None:
    workflow_path = _write_temp(tmp_path, VALID_WORKFLOW_YAML)
    result = parse_workflow(str(workflow_path))
    assert result["name"] == "sample-workflow"


def test_parse_json_workflow(tmp_path: Path) -> None:
    file_path = tmp_path / "workflow.json"
    file_path.write_text(VALID_WORKFLOW_JSON)
    result = parse_workflow(str(file_path))
    assert result["name"] == "json-workflow"


def test_invalid_yaml_syntax(tmp_path: Path) -> None:
    workflow_path = _write_temp(tmp_path, "workflow: [")
    with pytest.raises(SyntaxError):
        parse_workflow(str(workflow_path))


def test_missing_persona_reference(tmp_path: Path) -> None:
    yaml_text = VALID_WORKFLOW_YAML.replace("persona: dev", "persona: unknown")
    workflow_path = _write_temp(tmp_path, yaml_text)
    with pytest.raises(ValueError):
        parse_workflow(str(workflow_path))


def test_circular_dependencies(tmp_path: Path) -> None:
    yaml_text = VALID_WORKFLOW_YAML.replace(
        "edges:\n    - from: step1\n      to: step2",
        "edges:\n    - from: step1\n      to: step2\n    - from: step2\n      to: step1",
    )
    workflow_path = _write_temp(tmp_path, yaml_text)
    with pytest.raises(ValueError):
        parse_workflow(str(workflow_path))


def test_unsatisfied_input_reference(tmp_path: Path) -> None:
    yaml_text = VALID_WORKFLOW_YAML.replace("result: string", "other: string")
    workflow_path = _write_temp(tmp_path, yaml_text)
    with pytest.raises(ValueError):
        parse_workflow(str(workflow_path))


def test_parse_estimates(tmp_path: Path) -> None:
    workflow_path = _write_temp(tmp_path, ESTIMATE_WORKFLOW_YAML)
    result = parse_workflow(str(workflow_path))
    estimates = result["resource_estimates"]
    assert estimates["step1"] == {"cpu": 0.5, "memory": 128.0}
    assert estimates["step2"] == {"cpu": 1.5, "memory": 256.0}


def test_dry_run_execution_order(tmp_path: Path) -> None:
    workflow_path = _write_temp(tmp_path, VALID_WORKFLOW_YAML)
    result = parse_workflow(str(workflow_path), dry_run=True)
    assert result["execution_order"] == ["step1", "step2"]
