"""Copy-paste Agent OS prompt for implementing exported Syrin deployments."""

from __future__ import annotations

DEFAULT_GOAL = "Deploy a Syrin agent that can route work, earn through approved execution, and self-improve safely."


def build_agent_os_export_prompt(
    goal: str = DEFAULT_GOAL,
    *,
    mode: str = "hybrid",
    agent_count: int = 1,
) -> str:
    """Return the implementation prompt for an exported Agent OS deployment."""
    normalized_goal = str(goal or DEFAULT_GOAL).strip() or DEFAULT_GOAL
    normalized_mode = str(mode or "hybrid").strip() or "hybrid"
    return "\n".join(
        [
            "You are implementing an Agoragentic x Syrin Agent OS export.",
            f"Goal: {normalized_goal}",
            f"Deployment mode: {normalized_mode}",
            f"Planned agent count: {agent_count}",
            "",
            "Architecture boundary:",
            "- Syrin remains the control plane: agents, swarms, budget visibility, tracing, replay, sandbox, and recovery.",
            "- Agoragentic remains the execution/deployment/marketplace plane: execute(), provider previews, receipts, x402, and USDC on Base settlement.",
            "- Micro ECF is the portable policy boundary for intent, spend, secrets, deployment, outreach, and reconciliation.",
            "",
            "Implementation rules:",
            "- Start preview-first. Do not enable live spend, cloud provisioning, listing activation, or external outreach by default.",
            "- Use agoragentic_execute only after Micro ECF review, budget caps, and approval evidence are attached.",
            "- Use Syrin Sandbox for internal smoke tests and write attempt/reflection artifacts under SANDBOX_WORKSPACE.",
            "- Use Syrin Swarm only with hard per-agent budget caps and filtered MemoryBus sharing.",
            "- For platform hosting, generate a no-spend POST /api/hosting/agent-os/preview payload before any provider action.",
            "- For self-hosting, run the hosted_syrin_agent smoke test before live mode.",
            "- Require receipts and intent/outcome reconciliation for every live action.",
            "- Keep rollback explicit: disabling AGORAGENTIC_RUN_LIVE must stop spend and mutation paths.",
            "- Do not implement or assume `syrin integrate agoragentic` unless the Syrin maintainer explicitly requests core CLI support.",
            "",
            "Deliverables:",
            "- Export manifest",
            "- Deployment workflow",
            "- Micro ECF policy review",
            "- Sandbox smoke evidence",
            "- Swarm budget preview when agent_count > 1",
            "- Acceptance checklist",
            "- Maintainer-gated future core integration note",
        ]
    )
