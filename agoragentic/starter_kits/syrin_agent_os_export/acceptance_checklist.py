"""Acceptance checklist helpers for exported Agoragentic x Syrin agents."""

from __future__ import annotations

from typing import Any, Mapping

from agoragentic.starter_kits.syrin_agent_os_export.export_manifest import (
    SyrinAgentOSExport,
)

CHECKLIST_SCHEMA = "agoragentic.syrin.agent-os-acceptance.v1"


def _plain_object(value: Any) -> dict[str, Any]:
    """Normalize plain dictionaries and ignore other values."""
    return dict(value) if isinstance(value, Mapping) else {}


def _export_dict(export: SyrinAgentOSExport | Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize an optional export manifest."""
    if isinstance(export, SyrinAgentOSExport):
        return export.as_dict()
    return _plain_object(export)


def _check(
    check_id: str,
    title: str,
    evidence: str,
    *,
    command: str | None = None,
    required: bool = True,
) -> dict[str, Any]:
    """Build one pending checklist item."""
    item = {
        "id": check_id,
        "title": title,
        "status": "pending",
        "required": required,
        "evidence_required": evidence,
    }
    if command:
        item["command"] = command
    return item


def build_acceptance_checklist(
    export: SyrinAgentOSExport | Mapping[str, Any] | None = None,
    *,
    include_platform: bool | None = None,
) -> dict[str, Any]:
    """Build the operator checklist that must pass before live enablement."""
    manifest = _export_dict(export)
    targets = manifest.get("deployment_targets") or []
    target_names = {str(target.get("target")) for target in targets if isinstance(target, Mapping)}
    platform_required = include_platform if include_platform is not None else "platform_hosted" in target_names
    checks = [
        _check(
            "static_compile",
            "Compile integration code",
            "Compile output is clean.",
            command="python -m compileall -q agoragentic tests",
        ),
        _check(
            "unit_regression",
            "Run local regression suite",
            "All tests pass.",
            command="python -m unittest discover -s tests -v",
        ),
        _check(
            "micro_ecf_review",
            "Review intent, spend, secrets, outreach, and deployment policy",
            "Micro ECF review allows preview actions and denies unapproved live effects.",
            command="python agoragentic/examples/micro_ecf_policy_pack.py",
        ),
        _check(
            "syrin_sandbox_smoke",
            "Run Syrin sandbox smoke plan",
            "Attempt and reflection artifacts are written under SANDBOX_WORKSPACE.",
            command="python agoragentic/examples/syrin_sandbox_execute_loop.py",
        ),
        _check(
            "swarm_router_preview",
            "Preview Syrin swarm router budget plan",
            "Per-agent budget caps, A2A evidence, and MemoryBus filters are visible.",
            command="python agoragentic/examples/syrin_swarm_router_loop.py",
        ),
        _check(
            "hosted_service_smoke",
            "Smoke test served Syrin agent endpoints",
            "Health, ready, and describe endpoints return expected preview state.",
            command="python agoragentic/starter_kits/hosted_syrin_agent/smoke_test.py",
        ),
        _check(
            "platform_hosted_preview",
            "Preview platform-hosted deployment contract",
            "Provider preview shows no live cloud, billing, listing, or secret-injection effects.",
            command="python agoragentic/starter_kits/platform_hosted_syrin_agent/launch_request.py",
            required=platform_required,
        ),
        _check(
            "receipt_reconciliation",
            "Verify receipt and outcome reconciliation plan",
            "Every live action has a receipt path and intent/outcome comparison.",
        ),
        _check(
            "rollback_plan",
            "Document rollback and live-mode disable path",
            "Operator can disable AGORAGENTIC_RUN_LIVE and remove hosted/listing resources.",
        ),
    ]
    return {
        "schema": CHECKLIST_SCHEMA,
        "goal": manifest.get("goal") or "Deploy a Syrin agent with Agoragentic Agent OS controls.",
        "mode": manifest.get("mode") or "self_hosted",
        "status": "pending",
        "checks": checks,
    }


def summarize_acceptance_status(checklist: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize checklist completion state."""
    checks = checklist.get("checks") if isinstance(checklist, Mapping) else []
    if not isinstance(checks, list):
        checks = []
    required = [check for check in checks if isinstance(check, Mapping) and check.get("required") is not False]
    passed = [check for check in required if check.get("status") == "pass"]
    blocked = [check for check in required if check.get("status") == "blocked"]
    return {
        "required": len(required),
        "passed": len(passed),
        "blocked": len(blocked),
        "ready_for_live": len(required) > 0 and len(required) == len(passed) and not blocked,
    }
