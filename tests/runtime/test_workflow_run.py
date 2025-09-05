import asyncio

from axiomflow.dsl.parser import WorkflowParser
from axiomflow.runtime.executor import WorkflowExecutor

WORKFLOW_YAML = """
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
      estimated_runtime: 1.0
      estimated_cost: 10.0
    - id: step2
      name: Step Two
      persona: dev
      action: run
      inputs:
        prev_result: step1.result
      outputs:
        final: string
      estimated_runtime: 2.0
      estimated_cost: 20.0
  edges:
    - from: step1
      to: step2
  gates: []
"""


async def _step1():
    return {"runtime": 1.1, "cost": 11.0}


async def _step2():
    return {"runtime": 2.4, "cost": 18.0}


def test_estimation_accuracy_within_20_percent():
    parser = WorkflowParser()
    workflow = parser.parse(WORKFLOW_YAML)
    executor = WorkflowExecutor()
    step_funcs = {"step1": _step1, "step2": _step2}
    actual = asyncio.run(executor.run_workflow(workflow, step_funcs))
    estimate = workflow["estimates"]
    for key in ("runtime", "cost"):
        diff = abs(actual[key] - estimate[key]) / estimate[key]
        assert diff <= 0.2


def test_dry_run_produces_no_calls():
    parser = WorkflowParser()
    workflow = parser.parse(WORKFLOW_YAML)
    calls: list[str] = []

    async def recorder():
        calls.append("called")
        return {"runtime": 0.0, "cost": 0.0}

    executor = WorkflowExecutor()
    step_funcs = {"step1": recorder, "step2": recorder}
    asyncio.run(executor.run_workflow(workflow, step_funcs, dry_run=True))
    assert not calls
