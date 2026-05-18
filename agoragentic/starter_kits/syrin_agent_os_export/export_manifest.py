"""Export manifest helpers for deployable Agoragentic x Syrin agents."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

EXPORT_SCHEMA = "agoragentic.syrin.agent-os-export.v1"
PLATFORM_PREVIEW_ROUTE = "/api/hosting/agent-os/preview"
SUPPORTED_MODES = {"self_hosted", "platform_hosted", "hybrid"}


def _plain_object(value: Any) -> dict[str, Any]:
    """Normalize plain dictionaries and ignore other values."""
    return dict(value) if isinstance(value, Mapping) else {}


def _require_non_negative_finite_float(value: Any, field_name: str) -> float:
    """Parse a non-negative finite float or fail closed."""
    try:
        parsed = float(str(value).strip())
    except (AttributeError, TypeError, ValueError):
        raise ValueError(f"{field_name} must be a non-negative finite number.") from None
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"{field_name} must be a non-negative finite number.")
    return parsed


def _require_positive_int(value: Any, field_name: str) -> int:
    """Parse a positive integer or fail closed."""
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer greater than zero.")
    try:
        parsed = int(str(value).strip())
    except (AttributeError, TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer greater than zero.") from None
    if parsed < 1:
        raise ValueError(f"{field_name} must be an integer greater than zero.")
    return parsed


def _normalize_mode(mode: str | None) -> str:
    """Normalize supported export modes."""
    candidate = str(mode or "self_hosted").strip().lower().replace("-", "_")
    return candidate if candidate in SUPPORTED_MODES else "self_hosted"


@dataclass(frozen=True)
class ExportComponent:
    """One component shipped or referenced by the export kit."""

    name: str
    role: str
    path: str
    mode: str = "preview"
    required: bool = True
    live_effects: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable component contract."""
        return {
            "name": self.name,
            "role": self.role,
            "path": self.path,
            "mode": self.mode,
            "required": self.required,
            "live_effects": list(self.live_effects),
        }


@dataclass(frozen=True)
class SyrinAgentOSExport:
    """Manifest for exporting Agoragentic Agent OS controls into Syrin."""

    goal: str
    mode: str
    agent_count: int
    max_budget_usd: float
    components: tuple[ExportComponent, ...]
    controls: Mapping[str, Any]
    deployment_targets: tuple[Mapping[str, Any], ...]
    economics: Mapping[str, Any]
    future_core_integration: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable export manifest."""
        return {
            "schema": EXPORT_SCHEMA,
            "goal": self.goal,
            "mode": self.mode,
            "agent_count": self.agent_count,
            "max_budget_usd": self.max_budget_usd,
            "components": [component.as_dict() for component in self.components],
            "controls": _plain_object(self.controls),
            "deployment_targets": [dict(target) for target in self.deployment_targets],
            "economics": _plain_object(self.economics),
            "future_core_integration": _plain_object(self.future_core_integration),
        }


def _component_names(components: tuple[ExportComponent, ...]) -> set[str]:
    """Return the component names for quick membership checks."""
    return {component.name for component in components}


def build_future_core_integration_contract() -> dict[str, Any]:
    """Describe the maintainer-gated Syrin core integration boundary."""
    return {
        "status": "maintainer_gated",
        "implemented_here": False,
        "candidate_command": "syrin integrate agoragentic",
        "current_source": "syrin-integrations/agoragentic",
        "reason": "Keep usage proof in the integration repo before adding Syrin core UX.",
    }


def build_export_manifest(
    goal: str = "Deploy a Syrin agent with Agoragentic Agent OS controls.",
    *,
    mode: str = "self_hosted",
    agent_count: int = 1,
    max_budget_usd: float = 0.25,
    include_micro_ecf: bool = True,
    include_sandbox: bool = True,
    include_swarm: bool = True,
    include_self_hosting: bool = True,
    include_platform_hosting: bool = False,
    inference_provider: str = "bedrock",
) -> SyrinAgentOSExport:
    """Build the export manifest used by self-hosted or platform-hosted launches."""
    normalized_mode = _normalize_mode(mode)
    normalized_agents = _require_positive_int(agent_count, "agent_count")
    budget = _require_non_negative_finite_float(max_budget_usd, "max_budget_usd")
    platform_requested = include_platform_hosting or normalized_mode in {"platform_hosted", "hybrid"}
    self_hosted_requested = include_self_hosting and normalized_mode in {"self_hosted", "hybrid"}
    components = [
        ExportComponent(
            name="agoragentic_execute_router",
            role="execution_plane",
            path="agoragentic/agoragentic_syrin.py",
        ),
        ExportComponent(
            name="agent_os_control_loop",
            role="intent_and_execution_loop",
            path="agoragentic/examples/marketplace_agent_os_loop.py",
        ),
    ]
    if self_hosted_requested:
        components.append(
            ExportComponent(
                name="self_hosted_syrin_agent",
                role="self_hosted_runtime",
                path="agoragentic/starter_kits/hosted_syrin_agent",
            )
        )
    if platform_requested:
        components.append(
            ExportComponent(
                name="platform_hosted_syrin_agent",
                role="platform_hosted_runtime",
                path="agoragentic/starter_kits/platform_hosted_syrin_agent",
            )
        )
    if include_micro_ecf:
        components.append(
            ExportComponent(
                name="micro_ecf_policy_pack",
                role="policy_and_intent_boundary",
                path="agoragentic/examples/micro_ecf_policy_pack.py",
            )
        )
    if include_sandbox:
        components.append(
            ExportComponent(
                name="syrin_sandbox_execute_loop",
                role="internally_hosted_sandbox_testing",
                path="agoragentic/examples/syrin_sandbox_execute_loop.py",
            )
        )
    if include_swarm or normalized_agents > 1:
        components.append(
            ExportComponent(
                name="syrin_swarm_router_loop",
                role="multi_agent_budgeted_router",
                path="agoragentic/examples/syrin_swarm_router_loop.py",
            )
        )
    components.extend(
        [
            ExportComponent(
                name="agent_os_export_acceptance_checklist",
                role="operator_acceptance",
                path="agoragentic/starter_kits/syrin_agent_os_export/acceptance_checklist.py",
            ),
            ExportComponent(
                name="agent_os_export_prompt",
                role="implementation_prompt",
                path="agoragentic/starter_kits/syrin_agent_os_export/agent_os_prompt.py",
            ),
        ]
    )

    component_names = _component_names(tuple(components))
    controls = {
        "preview_first": True,
        "run_live": False,
        "prefer_execute": True,
        "require_match_before_execute": True,
        "require_micro_ecf_review": "micro_ecf_policy_pack" in component_names,
        "require_sandbox_smoke": "syrin_sandbox_execute_loop" in component_names,
        "require_swarm_budget_caps": "syrin_swarm_router_loop" in component_names,
        "require_receipt_reconciliation": True,
        "allow_self_deployment": False,
        "allow_core_cli_install": False,
    }
    deployment_targets = []
    if self_hosted_requested:
        deployment_targets.append(
            {
                "target": "self_hosted",
                "starter_kit": "agoragentic/starter_kits/hosted_syrin_agent",
                "hosting_boundary": "operator_managed",
                "live_enablement": "AGORAGENTIC_RUN_LIVE=1 after acceptance",
            }
        )
    if platform_requested:
        deployment_targets.append(
            {
                "target": "platform_hosted",
                "starter_kit": "agoragentic/starter_kits/platform_hosted_syrin_agent",
                "preview_route": PLATFORM_PREVIEW_ROUTE,
                "provider_options": ["simulated_runtime", "aws_apprunner", "vast_gpu_worker"],
                "inference_provider": str(inference_provider or "bedrock"),
            }
        )
    economics = {
        "settlement_rail": "USDC on Base through Agoragentic/x402 where live execution is enabled",
        "pricing_shapes": ["monthly_hosting_fee", "per_deployment_setup", "usage_budget_cap"],
        "default_monthly_billing_state": "not_started",
        "live_spend_requires": ["operator_approval", "budget_cap", "receipt_reconciliation"],
    }

    return SyrinAgentOSExport(
        goal=str(goal or "Deploy a Syrin agent with Agoragentic Agent OS controls.").strip(),
        mode=normalized_mode,
        agent_count=normalized_agents,
        max_budget_usd=budget,
        components=tuple(components),
        controls=controls,
        deployment_targets=tuple(deployment_targets),
        economics=economics,
        future_core_integration=build_future_core_integration_contract(),
    )


def _export_dict(export: SyrinAgentOSExport | Mapping[str, Any]) -> dict[str, Any]:
    """Normalize export instances and serialized manifests."""
    if isinstance(export, SyrinAgentOSExport):
        return export.as_dict()
    return _plain_object(export)


def build_platform_preview_payload(
    export: SyrinAgentOSExport | Mapping[str, Any],
    *,
    provider: str = "simulated_runtime",
) -> dict[str, Any]:
    """Build a no-spend payload for Agoragentic platform-hosting previews."""
    manifest = _export_dict(export)
    normalized_provider = str(provider or "").strip() or "simulated_runtime"
    return {
        "method": "POST",
        "route": PLATFORM_PREVIEW_ROUTE,
        "preview_only": True,
        "body": {
            "schema": "agoragentic.agent-os.hosting-preview.v1",
            "goal": manifest.get("goal"),
            "agent_count": manifest.get("agent_count"),
            "max_budget_usd": manifest.get("max_budget_usd"),
            "source_type": "runtime_bundle",
            "source_ref": "syrin_agent_os_export",
            "provider": normalized_provider,
            "components": manifest.get("components") or [],
            "controls": manifest.get("controls") or {},
            "constraints": {
                "preview_only": True,
                "max_cost": manifest.get("max_budget_usd", 0.0),
                "live_effects_allowed": False,
            },
        },
    }
