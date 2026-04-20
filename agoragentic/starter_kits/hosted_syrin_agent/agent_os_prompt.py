"""Agent OS prompt builder for the Agent Lightning bridge."""

from __future__ import annotations

from textwrap import dedent

DEFAULT_AGENT_OS_LIGHTNING_OBJECTIVE = (
    "Implement an Agent Lightning-compatible observability and offline optimization "
    "bridge for the hosted Agoragentic x Syrin starter kit."
)
DEFAULT_EXPORT_PATH = "artifacts/agent_lightning_export.json"


def build_agent_os_implementation_prompt(
    *,
    objective: str = DEFAULT_AGENT_OS_LIGHTNING_OBJECTIVE,
    export_path: str = DEFAULT_EXPORT_PATH,
) -> str:
    """Return a copy-paste Agent OS prompt for implementing the bridge safely."""
    return dedent(
        f"""
        You are extending the hosted Agoragentic x Syrin starter kit with an Agent Lightning-compatible bridge.

        Objective:
        {objective}

        Files in scope:
        - agoragentic/starter_kits/hosted_syrin_agent/tracing.py
        - agoragentic/starter_kits/hosted_syrin_agent/agent_os_prompt.py
        - agoragentic/examples/agent_lightning_export.py
        - agoragentic/AGENT_LIGHTNING_BRIDGE.md
        - agoragentic/AGENT_OS_AGENT_LIGHTNING_PROMPT.md
        - tests/test_agoragentic_agent_lightning_bridge.py

        Required outputs:
        - emit structured spans and scalar rewards to {export_path}
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
        """
    ).strip()
