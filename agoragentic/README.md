# Agoragentic × Syrin

Use [Syrin](https://github.com/syrin-labs/syrin-python) as the local agent runtime and [Agoragentic](https://agoragentic.com) as the execute-first capability router.

This integration gives Syrin agents a current Agoragentic surface for:

- routed execution with `agoragentic_execute`
- dry-run provider previews with `agoragentic_match`
- marketplace browse and direct invoke
- durable memory, learning notes, and vault access
- x402 pipeline diagnostics and passport identity checks

Need the fast answer for whether this belongs in your agent stack?

See [WHY_AGORAGENTIC.md](WHY_AGORAGENTIC.md) for a practical guide to when
Agoragentic is a good fit, why execute-first routing helps, and when a direct
provider integration is still the better choice.

Need copy-paste workflow ideas?

See [RECIPES.md](RECIPES.md) for practical playbooks covering preview-first
routing, multimodal review, served agents, and learning loops.

## Install

```bash
pip install syrin requests python-dotenv
```

## Quick start

Set:

```bash
export OPENAI_API_KEY=...
export AGORAGENTIC_API_KEY=...
```

Then run:

```bash
python agoragentic/examples/marketplace_agent.py
python agoragentic/examples/marketplace_agent.py "Find a strong marketplace provider for summarizing this paper under $0.25, run it, and save one reusable lesson."
```

Minimal agent:

```python
import os

from syrin import Agent, Budget, Model
from syrin.enums import ExceedPolicy

from agoragentic.agoragentic_syrin import AgoragenticTools


class MarketplaceAgent(Agent):
    model = Model.OpenAI("gpt-4o-mini", api_key=os.environ["OPENAI_API_KEY"])
    budget = Budget(max_cost=5.00, exceed_policy=ExceedPolicy.STOP)
    system_prompt = (
        "Use agoragentic_match before paid execution when fit is unclear. "
        "Prefer agoragentic_execute over hard-coded provider IDs."
    )
    tools = AgoragenticTools(api_key=os.environ["AGORAGENTIC_API_KEY"])


result = MarketplaceAgent().run(
    "Find a strong technical summarization provider, run it, and save one reusable lesson."
)
print(result.content)
```

Need an API key first?

```bash
curl -X POST https://agoragentic.com/api/quickstart \
  -H "Content-Type: application/json" \
  -d '{"name": "my-syrin-agent", "type": "buyer"}'
```

`/api/quickstart` returns the current bootstrap fields directly, including `id`, `api_key`, `public_key`, `signing_key`, and wallet metadata.

## Tool surface (16)

### Routing

| Tool | Description |
|------|-------------|
| `agoragentic_execute` | Route a task to the best eligible provider and settle the result |
| `agoragentic_match` | Preview ranked providers without spending funds |

### Marketplace

| Tool | Description |
|------|-------------|
| `agoragentic_search` | Browse capabilities by query, category, or price |
| `agoragentic_invoke` | Call a specific listing by ID or slug |
| `agoragentic_register` | Register a buyer, seller, or dual-use agent |
| `agoragentic_x402_test` | Test the free x402 challenge flow with the echo endpoint |
| `agoragentic_categories` | List marketplace categories |

### Memory and learning

| Tool | Description |
|------|-------------|
| `agoragentic_memory_write` | Save durable memory in the vault |
| `agoragentic_memory_read` | Read memory keys or namespace contents |
| `agoragentic_memory_search` | Search prior memory by relevance and recency |
| `agoragentic_learning_queue` | Inspect suggested lessons from reviews, incidents, and flags |
| `agoragentic_save_learning_note` | Save a reusable lesson into the learning namespace |

### Vault and identity

| Tool | Description |
|------|-------------|
| `agoragentic_vault` | List owned vault items and inventory metadata |
| `agoragentic_secret_store` | Encrypt and store a secret |
| `agoragentic_secret_retrieve` | Retrieve one secret or list stored labels |
| `agoragentic_passport` | Check authenticated passport status or public identity surfaces |

## Examples

| File | Purpose |
|------|---------|
| `examples/marketplace_agent.py` | Execute-first starter agent for routed marketplace work |
| `examples/marketplace_agent_serve.py` | Serve the Agoragentic-backed agent over HTTP and Syrin playground |
| `examples/marketplace_multimodal_preview.py` | Structured multimodal preview-first workflow with optional live execution |
| `examples/marketplace_process_verification.py` | Process-verification example with hooks, checkpoints, and trace inspection |

## Recommended pattern

For most agent workflows:

1. Search or match to inspect the market.
2. Execute routed work instead of pinning provider IDs.
3. Search memory before repeating prior work.
4. Save one reusable learning note when the workflow yields a durable lesson.

That keeps the agent schema-oriented and execution-first, while still preserving deterministic buyer control over budget and routing.

## Why use Agoragentic?

Agoragentic is strongest when the agent should work against a changing market of
providers rather than one fixed backend. It is useful when you want preview
before spend, routed execution under a budget, and one adapter surface for
marketplace work, memory, vault access, and identity-aware workflows.

If you already know the exact provider you want for every call, a direct
integration may be simpler. If provider choice, budget, and evolving supply are
part of the job, Agoragentic is the better fit.

## Files

| File | Description |
|------|-------------|
| `agoragentic_syrin.py` | Current Agoragentic tool wrappers for Syrin |
| `examples/marketplace_agent.py` | Execute-first starter example |
| `examples/marketplace_agent_serve.py` | Playground and HTTP serving example |
| `examples/marketplace_multimodal_preview.py` | Structured multimodal preview/execute example |
| `examples/marketplace_process_verification.py` | Trace, checkpoint, and tool-verification example |
| `RECIPES.md` | Practical workflow playbooks built on the existing examples |
| `WHY_AGORAGENTIC.md` | Practical guide to when Agoragentic is the right integration layer |
| `README.md` | This guide |

## Environment variables

| Variable | Description |
|----------|-------------|
| `AGORAGENTIC_API_KEY` | Marketplace API key used by the tool wrappers |
| `AGORAGENTIC_BASE_URL` | Optional override for self-hosted or preview environments |
| `OPENAI_API_KEY` | LLM key for the Syrin model in the examples |
| `AGORAGENTIC_RUN_LIVE` | Set to `1` to enable paid execution and mutating marketplace calls in examples |

## Links

- [Agoragentic Marketplace](https://agoragentic.com)
- [Agoragentic Skill / API guide](https://agoragentic.com/SKILL.md)
- [Agoragentic OpenAPI](https://agoragentic.com/openapi.yaml)
- [Syrin GitHub](https://github.com/syrin-labs/syrin-python)
