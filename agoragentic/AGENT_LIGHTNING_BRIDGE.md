# Agent Lightning Bridge

This document explains how the Agoragentic x Syrin integration can participate
in an [Agent Lightning](https://github.com/microsoft/agent-lightning)-style
optimization loop without turning the live runtime into a training process.

Reference architecture:

- Agent Lightning repo: <https://github.com/microsoft/agent-lightning>
- Paper: <https://arxiv.org/abs/2508.03680>
- Trainer docs: <https://microsoft.github.io/agent-lightning/latest/reference/trainer/>
- Traces docs: <https://microsoft.github.io/agent-lightning/latest/tutorials/traces/>

## Why this bridge exists

The hosted Syrin starter kit already provides:

- a served runtime
- preview-first safety gates
- bounded budgets
- smoke tests and container assets

Agent Lightning contributes the next layer:

- traces as structured spans
- rewards as scalar signals
- offline optimization loops that learn from those traces
- separation between execution and training

That separation is the key design decision. Runtime execution stays in Syrin +
Agoragentic. Optimization happens after the fact.

## Component mapping

| Agent Lightning concept | Agoragentic x Syrin equivalent |
| --- | --- |
| Runner | hosted Syrin starter kit process |
| Tracer | `starter_kits/hosted_syrin_agent/tracing.py` |
| Span | routed action, gate, artifact, or control-plane event |
| Reward | task completion, budget discipline, sandbox safety, approval readiness, routing evidence |
| Store | JSON export now, LightningStore later |
| Trainer / Algorithm | external offline optimizer, not in the request path |

## What ships in this repo

- `agoragentic/starter_kits/hosted_syrin_agent/tracing.py`
  Builds serializable spans, rewards, and export packets.
- `agoragentic/examples/agent_lightning_export.py`
  Writes a preview-first export packet without requiring a live training stack.
- `agoragentic/starter_kits/hosted_syrin_agent/agent_os_prompt.py`
  Builds a copy-paste prompt for another Agent OS implementation agent.
- `agoragentic/AGENT_OS_AGENT_LIGHTNING_PROMPT.md`
  Human-readable prompt version for docs and review.

## Safe operating model

The bridge is intentionally limited:

- no `agentlightning` dependency is required to run the starter kit
- no trainer is started by `serve.py`
- no prompt or policy update is promoted automatically
- no live execution is enabled by the bridge itself

The expected loop is:

1. Run the hosted starter kit in preview-first mode.
2. Emit a span/reward packet from a task or planned task.
3. Feed that packet into an external optimizer or analysis job.
4. Review the resulting prompt/policy/resource change.
5. Promote only approved changes back into runtime configuration.

## Reward schema

The default bridge exports these rewards:

- `task_completion`
- `budget_discipline`
- `sandbox_safety`
- `approval_readiness`
- `routing_evidence`

These are not final RL rewards. They are a practical starter schema for offline
analysis, prompt optimization, and future Agent Lightning adapters.

## Run the example

From the repository root:

```bash
python agoragentic/examples/agent_lightning_export.py
python agoragentic/examples/agent_lightning_export.py --print-agent-os-prompt
```

The example writes a JSON artifact under `agoragentic/artifacts/` by default.

## What should happen next

Short term:

- keep exporting JSON packets
- evaluate them with internal analysis or grading jobs
- use the Agent OS prompt to extend the bridge safely

Later:

- add optional OpenTelemetry emission
- add a true LightningStore adapter
- add offline prompt/resource promotion workflows
- tie promotion to sandbox verification and human review
