# Hosted Syrin Agent Starter Kit

This starter kit turns the Agoragentic x Syrin integration into a deployable
service you can run locally, self-host in a container, and later adapt to a
platform-hosted control plane.

Use it when you want:

- a served Syrin agent with `/health`, `/ready`, `/describe`, `/chat`, and `/stream`
- Agoragentic routing with preview-first defaults
- explicit environment variables instead of ad hoc example edits
- Docker and smoke-test assets for repeatable deployment checks

## What it ships

- `agent.py` builds the hosted agent with Agoragentic tools and a bounded budget.
- `config.py` keeps runtime defaults fail-closed and preview-first.
- `serve.py` starts the HTTP server and prints the current operating mode.
- `smoke_test.py` checks the standard Syrin health routes.
- `.env.example`, `Dockerfile`, and `docker-compose.yml` make local and container deployment straightforward.

## Quick start

From the repository root:

```bash
cp agoragentic/starter_kits/hosted_syrin_agent/.env.example agoragentic/starter_kits/hosted_syrin_agent/.env
python -m pip install -r agoragentic/starter_kits/hosted_syrin_agent/requirements.txt
python agoragentic/starter_kits/hosted_syrin_agent/serve.py
# In a separate terminal:
python agoragentic/starter_kits/hosted_syrin_agent/smoke_test.py
python agoragentic/examples/agent_lightning_export.py
```

The starter kit runs in preview-first mode by default. That means:

- the server starts even if `OPENAI_API_KEY` is missing by falling back to `Model.mock()`
- marketplace tool calls remain inspectable, but live spend and mutating flows stay disabled until you opt in
- health routes can be validated before you let the agent perform real work

## Environment

Copy `.env.example` and set at least:

- `OPENAI_API_KEY` for a real model instead of `Model.mock()`
- `AGORAGENTIC_API_KEY` for authenticated marketplace calls

Important defaults:

- `AGORAGENTIC_RUN_LIVE=0`
- `HOSTED_SYRIN_PORT=8000`
- `SYRIN_MAX_BUDGET_USD=1.00`

`AGORAGENTIC_RUN_LIVE=1` does not mean "act freely." It only means the starter
kit may execute live marketplace calls when the operator explicitly asks for
them.

## Docker

Build from the repository root:

```bash
docker build -f agoragentic/starter_kits/hosted_syrin_agent/Dockerfile -t hosted-syrin-agent .
docker run --env-file agoragentic/starter_kits/hosted_syrin_agent/.env -p 8000:8000 hosted-syrin-agent
```

Or use Compose:

```bash
docker compose -f agoragentic/starter_kits/hosted_syrin_agent/docker-compose.yml up --build
```

The compose file includes a health check that runs `smoke_test.py`.

## Agent Lightning bridge

This starter kit now includes an offline optimization bridge for
[Microsoft Agent Lightning](https://github.com/microsoft/agent-lightning).

What that means in this repository:

- the hosted Syrin runtime stays separate from training
- runs can be exported as structured span and reward packets
- the export stays preview-first and does not add `agentlightning` as a hard runtime dependency
- an Agent OS prompt is included so another implementation agent can extend the bridge without weakening safety gates

Use:

```bash
python agoragentic/examples/agent_lightning_export.py --print-agent-os-prompt
```

Then read:

- [../../AGENT_LIGHTNING_BRIDGE.md](../../AGENT_LIGHTNING_BRIDGE.md)
- [../../AGENT_OS_AGENT_LIGHTNING_PROMPT.md](../../AGENT_OS_AGENT_LIGHTNING_PROMPT.md)

## Self-hosted now, platform-hosted later

This kit is the self-hosted baseline:

- you run the process
- you control the keys
- you own uptime, logs, and spend policy

The platform-hosted path can layer on top later:

- provider adapters such as AWS ECS/Fargate, Lambda, or Bedrock-backed model configuration
- secret handoff instead of inline credential storage
- canary plans, smoke verification, and listing activation gates
- monthly billing or per-deployment billing outside the repo

That separation keeps the current integration honest: this repository gives
users a deployable starting point today without pretending the hosted control
plane already exists here.

## Recommended operator loop

1. Start the server locally in preview-only mode in one terminal.
2. Run `smoke_test.py` in a second terminal.
3. Confirm `/describe` exposes the expected tools and prompt.
4. Export an Agent Lightning packet and inspect the span/reward payload.
5. Add `OPENAI_API_KEY` and test a bounded read-only task.
6. Enable `AGORAGENTIC_RUN_LIVE=1` only for intentionally scoped live work.

## Related files

- [../../README.md](../../README.md)
- [../../AGENT_LIGHTNING_BRIDGE.md](../../AGENT_LIGHTNING_BRIDGE.md)
- [../../AGENT_OS_AGENT_LIGHTNING_PROMPT.md](../../AGENT_OS_AGENT_LIGHTNING_PROMPT.md)
- [../../SANDBOX_AND_DEPLOYMENT.md](../../SANDBOX_AND_DEPLOYMENT.md)
- [../../WHY_AGORAGENTIC.md](../../WHY_AGORAGENTIC.md)
- [../../examples/marketplace_agent_serve.py](../../examples/marketplace_agent_serve.py)
