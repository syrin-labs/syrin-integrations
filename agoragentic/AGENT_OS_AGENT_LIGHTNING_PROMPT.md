# Agent OS Prompt: Agent Lightning Bridge

Use this prompt when you want another implementation agent to extend the hosted
Agoragentic x Syrin starter kit with an Agent Lightning-style optimization
bridge.

```text
You are extending the hosted Agoragentic x Syrin starter kit with an Agent Lightning-compatible bridge.

Objective:
Implement an Agent Lightning-compatible observability and offline optimization bridge for the hosted Agoragentic x Syrin starter kit.

Files in scope:
- agoragentic/starter_kits/hosted_syrin_agent/tracing.py
- agoragentic/starter_kits/hosted_syrin_agent/agent_os_prompt.py
- agoragentic/examples/agent_lightning_export.py
- agoragentic/AGENT_LIGHTNING_BRIDGE.md
- agoragentic/AGENT_OS_AGENT_LIGHTNING_PROMPT.md
- tests/test_agoragentic_agent_lightning_bridge.py

Required outputs:
- emit structured spans and scalar rewards to artifacts/agent_lightning_export.json
- preserve preview-first defaults and explicit live-mode gates
- keep training and optimization out of the live request path
- update docs so users understand runtime vs offline optimization
- add tests for span export, reward shaping, and prompt generation

Constraints:
- do not add agentlightning as a hard runtime dependency
- do not enable self-mutation, automatic deployment, or live spend by default
- do not bypass approvals, sandbox checks, or budget caps
- do not replace Syrin runtime logic with the training loop

Success criteria:
- one hosted run can be exported as spans, rewards, and metadata
- the export is understandable to Agent Lightning-style adapters
- another Agent OS agent can pick up this prompt and continue implementation safely
```

Programmatic version:

- `agoragentic/starter_kits/hosted_syrin_agent/agent_os_prompt.py`
