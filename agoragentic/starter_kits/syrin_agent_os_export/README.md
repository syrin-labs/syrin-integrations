# Syrin Agent OS export kit

This kit packages the current Agoragentic x Syrin work into one deployable
contract for users who want provisioned Syrin agents with Agent OS controls.

It does not add a Syrin core CLI command. The future `syrin integrate
agoragentic` path is documented as maintainer-gated until usage patterns prove
stable.

## What it exports

- A manifest that composes the Agoragentic execute router, Agent OS loop,
  Micro ECF policy pack, Syrin sandbox loop, swarm router, and hosted starter
  kits.
- A canonical deployment workflow for self-hosted, platform-hosted, or hybrid
  launches.
- A no-spend platform preview payload for `POST /api/hosting/agent-os/preview`.
- An acceptance checklist covering compile, tests, Micro ECF review, sandbox
  smoke, swarm preview, hosted smoke, receipts, reconciliation, and rollback.
- A copy-paste Agent OS prompt for implementing the export in the platform.

## Quick start

Print a hybrid deployment workflow:

```bash
python agoragentic/starter_kits/syrin_agent_os_export/deployment_flow.py \
  "Deploy a lead-scoring Syrin swarm with Agoragentic execution" \
  --mode hybrid \
  --agent-count 3 \
  --max-budget-usd 0.25
```

Build the manifest from Python:

```python
from agoragentic.starter_kits.syrin_agent_os_export import (
    build_deployment_workflow,
    build_export_manifest,
    build_platform_preview_payload,
)

export = build_export_manifest(
    "Deploy a bounded growth agent.",
    mode="platform_hosted",
    agent_count=2,
    max_budget_usd=0.25,
    include_platform_hosting=True,
)

preview = build_platform_preview_payload(export)
workflow = build_deployment_workflow("Deploy a bounded growth agent.", mode="hybrid")
```

## Safety defaults

- Live spend is disabled by default.
- Platform hosting starts with `simulated_runtime`.
- Micro ECF review is required before live spend, deployment, secrets,
  outreach, memory writes, or budget changes.
- Syrin sandbox smoke should produce attempt and reflection artifacts before
  live mode.
- Swarms require per-agent budget caps and filtered memory sharing.
- Every live action needs receipt and intent/outcome reconciliation.

## Commercialization model

The manifest supports the product shapes discussed for deployed Syrin agents:

- self-hosted agents where the operator runs the service and pays for its own
  infrastructure
- platform-hosted agents where Agoragentic can charge a monthly hosting fee or
  per-deployment setup fee
- usage-capped execution where live work settles through Agoragentic/x402 and
  USDC on Base after approval
- optional Bedrock or other hosted inference lanes at the platform boundary

The export intentionally models these as contracts and previews, not as claims
that live cloud billing or marketplace activation already happened.
