"""Canonical deployment workflow for Agoragentic x Syrin Agent OS exports."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_acceptance = importlib.import_module("agoragentic.starter_kits.syrin_agent_os_export.acceptance_checklist")
_prompt = importlib.import_module("agoragentic.starter_kits.syrin_agent_os_export.agent_os_prompt")
_manifest = importlib.import_module("agoragentic.starter_kits.syrin_agent_os_export.export_manifest")
build_acceptance_checklist = _acceptance.build_acceptance_checklist
build_agent_os_export_prompt = _prompt.build_agent_os_export_prompt
build_export_manifest = _manifest.build_export_manifest
build_platform_preview_payload = _manifest.build_platform_preview_payload
SyrinAgentOSExport = _manifest.SyrinAgentOSExport
_require_non_negative_finite_float = _manifest._require_non_negative_finite_float
_require_positive_int = _manifest._require_positive_int


def _plain_object(value: Any) -> dict[str, Any]:
    """Normalize plain dictionaries and ignore other values."""
    return dict(value) if isinstance(value, Mapping) else {}


def _export_dict(export: SyrinAgentOSExport | Mapping[str, Any]) -> dict[str, Any]:
    """Normalize export instances and serialized manifests."""
    if isinstance(export, SyrinAgentOSExport):
        return export.as_dict()
    return _plain_object(export)


def _phase(
    phase_id: str,
    title: str,
    action: str,
    evidence: str,
    *,
    route: str | None = None,
    command: str | None = None,
    live_effects_allowed: bool = False,
) -> dict[str, Any]:
    """Build one deployment phase."""
    phase = {
        "id": phase_id,
        "title": title,
        "action": action,
        "evidence_required": evidence,
        "live_effects_allowed": live_effects_allowed,
    }
    if route:
        phase["route"] = route
    if command:
        phase["command"] = command
    return phase


def build_deployment_workflow(
    goal: str = "Deploy a Syrin agent with Agoragentic Agent OS controls.",
    *,
    mode: str = "hybrid",
    agent_count: int = 1,
    max_budget_usd: float = 0.25,
    provider: str = "simulated_runtime",
) -> dict[str, Any]:
    """Build the canonical deployment workflow for exported agents."""
    normalized_mode = str(mode or "hybrid").strip().lower().replace("-", "_")
    validated_agent_count = _require_positive_int(agent_count, "agent_count")
    validated_max_budget = _require_non_negative_finite_float(max_budget_usd, "max_budget_usd")
    export = build_export_manifest(
        goal,
        mode=normalized_mode,
        agent_count=validated_agent_count,
        max_budget_usd=validated_max_budget,
        include_platform_hosting=normalized_mode in {"platform_hosted", "hybrid"},
    )
    manifest = export.as_dict()
    phases = [
        _phase(
            "configure_export",
            "Build export manifest",
            "Select self-hosted, platform-hosted, or hybrid deployment mode and freeze the component list.",
            "Manifest includes router, policy, sandbox, swarm, and hosting boundaries.",
        ),
        _phase(
            "micro_ecf_review",
            "Review intent and live-effect boundaries",
            "Classify requested actions before spend, deployment, secrets, outreach, or memory writes.",
            "Policy fingerprint and decision are recorded.",
            command="python agoragentic/examples/micro_ecf_policy_pack.py",
        ),
        _phase(
            "syrin_sandbox_smoke",
            "Run internal Syrin sandbox smoke plan",
            "Execute bash/Python sandbox steps through shared SANDBOX_WORKSPACE artifacts.",
            "Attempt and reflection artifacts exist before live enablement.",
            command="python agoragentic/examples/syrin_sandbox_execute_loop.py",
        ),
        _phase(
            "swarm_router_preview",
            "Preview multi-agent routing",
            "Plan budgeted Syrin swarm roles and Agoragentic execute constraints.",
            "Per-agent cap and MemoryBus filters are visible.",
            command="python agoragentic/examples/syrin_swarm_router_loop.py",
        ),
        _phase(
            "platform_hosted_preview",
            "Preview platform-hosted deployment",
            "Shape the hosted launch payload without starting cloud, billing, or listing effects.",
            "Provider preview has live_effects_allowed=false.",
            route="/api/hosting/agent-os/preview",
            command="python agoragentic/starter_kits/platform_hosted_syrin_agent/launch_request.py",
        ),
        _phase(
            "operator_acceptance",
            "Run acceptance checklist",
            "Collect smoke, policy, budget, receipt, reconciliation, and rollback evidence.",
            "All required checks are pass before live mode.",
        ),
        _phase(
            "optional_live_enablement",
            "Enable live mode only after acceptance",
            "Set AGORAGENTIC_RUN_LIVE=1 only for scoped work with budget and approval evidence.",
            "Receipt and outcome reconciliation are attached for each live action.",
            live_effects_allowed=True,
        ),
    ]
    return {
        "schema": "agoragentic.syrin.agent-os-deployment-flow.v1",
        "export_manifest": manifest,
        "platform_preview_payload": build_platform_preview_payload(export, provider=provider),
        "acceptance_checklist": build_acceptance_checklist(export),
        "agent_os_prompt": build_agent_os_export_prompt(
            goal,
            mode=manifest["mode"],
            agent_count=manifest["agent_count"],
        ),
        "phases": phases,
    }


def _build_parser() -> argparse.ArgumentParser:
    """Create CLI arguments for export workflow previews."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("goal", nargs="?", default="Deploy a Syrin agent with Agoragentic Agent OS controls.")
    parser.add_argument("--mode", default="hybrid", choices=("self_hosted", "platform_hosted", "hybrid"))
    parser.add_argument("--agent-count", type=int, default=1)
    parser.add_argument("--max-budget-usd", type=float, default=0.25)
    parser.add_argument("--provider", default="simulated_runtime")
    return parser


def main() -> None:
    """Print the deployment workflow as JSON."""
    args = _build_parser().parse_args()
    workflow = build_deployment_workflow(
        args.goal,
        mode=args.mode,
        agent_count=args.agent_count,
        max_budget_usd=args.max_budget_usd,
        provider=args.provider,
    )
    print(json.dumps(workflow, indent=2))


if __name__ == "__main__":
    main()
