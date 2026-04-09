# Why Use Agoragentic With Syrin

Agoragentic is a good fit for Syrin when your agent should choose from a live
market of capabilities instead of being wired to one provider forever.

## What it gives you

- Execute-first routing instead of hard-coded provider IDs
- Preview-first matching so the agent can inspect options before it spends
- One adapter surface for marketplace browse, routed execution, memory, vault,
  learning notes, and identity checks
- Access to paid x402-style capabilities without building provider-specific
  integrations one by one
- A path to multimodal work where the task can include text, image URLs, and
  document URLs in one payload

## When it fits

Use Agoragentic with Syrin when:

- the best provider may change over time and you do not want to pin the agent to
  a single backend
- you want the agent to route work under a budget instead of blindly calling
  one expensive tool
- you need access to marketplace-native capabilities such as memory, learning
  notes, vault inventory, or passport checks
- you want to start with a safe preview and only run live execution when the
  provider match looks good
- you want the same agent to handle simple browse/match flows and live paid
  execution flows

## Why not just call a single provider directly?

Direct integrations are still valid when the workflow is fixed and you already
know the exact provider you want. Agoragentic is for the cases where selection,
budget, and evolving supply matter.

If the question is "which provider should handle this task right now?" then
Agoragentic gives Syrin a better operating model than a hard-coded integration.

## Recommended workflow

1. Start with `agoragentic_match` when fit is unclear.
2. Use `agoragentic_execute` when you want the marketplace to route the live
   call.
3. Search memory before repeating work the agent may have already done.
4. Save a learning note when the result produces a reusable lesson.

That keeps the workflow inspectable and cost-aware while still giving the agent
access to a broader capability market.

## When not to use it

Agoragentic is probably not the right layer when:

- you have one fixed provider and do not want marketplace routing
- the workflow must stay fully offline
- every call must use a single pre-approved backend with no routing choice
- the extra marketplace abstraction does not buy you better cost, coverage, or
  operational flexibility

## Where to start

- [README.md](README.md) for the adapter surface and install instructions
- [examples/marketplace_agent.py](examples/marketplace_agent.py) for the basic
  execute-first flow
- [examples/marketplace_agent_serve.py](examples/marketplace_agent_serve.py) for
  a served agent and playground flow
- [examples/marketplace_process_verification.py](examples/marketplace_process_verification.py)
  for hooks, checkpoints, and trace inspection
