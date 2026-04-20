"""Agent Lightning-style trace and reward exports for the hosted Syrin starter kit."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from agoragentic.starter_kits.hosted_syrin_agent.config import HostedStarterProfile

DEFAULT_AGENT_IDENTITY = "hosted-syrin-agent"
DEFAULT_AGENT_LIGHTNING_OBJECTIVE = (
    "Improve hosted Syrin agent behavior through offline span and reward analysis "
    "without adding a training loop to the live request path."
)


def _now_ms() -> int:
    """Return current time in milliseconds."""
    return int(time.time() * 1000)


def _new_id(prefix: str) -> str:
    """Build a short identifier for exported spans and runs."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True)
class LightningSpan:
    """Serializable span record for offline optimization pipelines."""

    name: str
    kind: str
    status: str
    start_ms: int
    end_ms: int
    attributes: dict[str, Any] = field(default_factory=dict)
    span_id: str = field(default_factory=lambda: _new_id("span"))
    parent_span_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable span payload."""
        return {
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": self.kind,
            "status": self.status,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "attributes": self.attributes,
        }


@dataclass(frozen=True)
class RewardSignal:
    """Scalar reward emitted for offline analysis or training."""

    name: str
    value: float
    rationale: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable reward payload."""
        return {
            "name": self.name,
            "value": self.value,
            "rationale": self.rationale,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class LightningTraceExport:
    """Export packet shaped for Agent Lightning-style offline ingestion."""

    task: str
    objective: str
    preview_only: bool
    agent_identity: str
    spans: tuple[LightningSpan, ...]
    rewards: tuple[RewardSignal, ...]
    metadata: dict[str, Any]
    run_id: str = field(default_factory=lambda: _new_id("run"))

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable export packet."""
        reward_total = round(sum(reward.value for reward in self.rewards), 4)
        return {
            "version": 1,
            "run_id": self.run_id,
            "task": self.task,
            "objective": self.objective,
            "preview_only": self.preview_only,
            "agent_identity": self.agent_identity,
            "spans": [span.as_dict() for span in self.spans],
            "rewards": [reward.as_dict() for reward in self.rewards],
            "metadata": self.metadata,
            "summary": {
                "span_count": len(self.spans),
                "reward_count": len(self.rewards),
                "total_reward": reward_total,
            },
        }


def build_span(
    name: str,
    kind: str,
    *,
    status: str = "ok",
    attributes: Mapping[str, Any] | None = None,
    start_ms: int | None = None,
    end_ms: int | None = None,
    parent_span_id: str | None = None,
) -> LightningSpan:
    """Build one serializable span."""
    started = _now_ms() if start_ms is None else int(start_ms)
    ended = started if end_ms is None else int(end_ms)
    payload = dict(attributes or {})
    return LightningSpan(
        name=name,
        kind=kind,
        status=status,
        start_ms=started,
        end_ms=ended,
        attributes=payload,
        parent_span_id=parent_span_id,
    )


def build_default_spans(
    *,
    task: str,
    max_cost_usd: float,
    preview_only: bool,
    matched_providers: int = 0,
    approval_required: bool = False,
) -> tuple[LightningSpan, ...]:
    """Build a small default span tree for hosted Syrin preview and live runs."""
    base_ms = _now_ms()

    def _window(index: int) -> tuple[int, int]:
        start_ms = base_ms + (index * 10)
        return start_ms, start_ms + 5

    root_start_ms, root_end_ms = _window(0)
    root = build_span(
        "hosted_syrin_rollout",
        "rollout",
        status="preview" if preview_only else "ready",
        attributes={"task": task, "max_cost_usd": max_cost_usd},
        start_ms=root_start_ms,
        end_ms=root_end_ms,
    )
    profile_start_ms, profile_end_ms = _window(1)
    profile = build_span(
        "runtime.profile_loaded",
        "lifecycle",
        attributes={"preview_only": preview_only},
        start_ms=profile_start_ms,
        end_ms=profile_end_ms,
        parent_span_id=root.span_id,
    )
    routing_start_ms, routing_end_ms = _window(2)
    routing = build_span(
        "routing.match",
        "router",
        status="completed" if matched_providers > 0 else "planned",
        attributes={
            "matched_providers": matched_providers,
            "preview_only": preview_only,
            "max_cost_usd": max_cost_usd,
        },
        start_ms=routing_start_ms,
        end_ms=routing_end_ms,
        parent_span_id=root.span_id,
    )
    gate_start_ms, gate_end_ms = _window(3)
    gate = build_span(
        "execution.gate",
        "gate",
        status="blocked" if preview_only or approval_required else "ready",
        attributes={
            "approval_required": approval_required,
            "preview_only": preview_only,
        },
        start_ms=gate_start_ms,
        end_ms=gate_end_ms,
        parent_span_id=root.span_id,
    )
    artifact_start_ms, artifact_end_ms = _window(4)
    artifact = build_span(
        "artifact.export",
        "artifact",
        attributes={"format": "json", "consumer": "agent-lightning-style"},
        start_ms=artifact_start_ms,
        end_ms=artifact_end_ms,
        parent_span_id=root.span_id,
    )
    return (root, profile, routing, gate, artifact)


def build_reward_signals(
    *,
    preview_only: bool,
    max_cost_usd: float,
    actual_cost_usd: float = 0.0,
    matched_providers: int = 0,
    sandbox_passed: bool = True,
    approval_required: bool = False,
    task_completed: bool = False,
) -> tuple[RewardSignal, ...]:
    """Build a compact reward set for offline optimization and scoring."""
    planning_value = 1.0 if task_completed else (0.25 if preview_only and matched_providers > 0 else 0.0)
    budget_value = 1.0 if actual_cost_usd <= max_cost_usd else 0.0
    safety_value = 1.0 if preview_only or sandbox_passed else 0.0
    approval_value = 0.0 if approval_required else 1.0
    routing_value = round(min(1.0, matched_providers / 3.0), 4)
    return (
        RewardSignal(
            name="task_completion",
            value=planning_value,
            rationale="Reward completed work, or preview evidence when a routed plan was produced.",
            metadata={"task_completed": task_completed, "preview_only": preview_only},
        ),
        RewardSignal(
            name="budget_discipline",
            value=budget_value,
            rationale="Keep actual cost within the declared budget cap.",
            metadata={"actual_cost_usd": actual_cost_usd, "max_cost_usd": max_cost_usd},
        ),
        RewardSignal(
            name="sandbox_safety",
            value=safety_value,
            rationale="Prefer preview-first or sandbox-verified flows over unsafe live execution.",
            metadata={"sandbox_passed": sandbox_passed, "preview_only": preview_only},
        ),
        RewardSignal(
            name="approval_readiness",
            value=approval_value,
            rationale="Do not bypass operator approvals or gated live actions.",
            metadata={"approval_required": approval_required},
        ),
        RewardSignal(
            name="routing_evidence",
            value=routing_value,
            rationale="Reward plans that produced concrete provider-fit evidence.",
            metadata={"matched_providers": matched_providers},
        ),
    )


def build_agent_lightning_export(
    *,
    task: str,
    profile: HostedStarterProfile,
    spans: tuple[LightningSpan, ...],
    rewards: tuple[RewardSignal, ...],
    preview_only: bool,
    objective: str = DEFAULT_AGENT_LIGHTNING_OBJECTIVE,
    agent_identity: str = DEFAULT_AGENT_IDENTITY,
    metadata: Mapping[str, Any] | None = None,
) -> LightningTraceExport:
    """Build one Agent Lightning-compatible export packet."""
    combined_metadata = {
        "model_name": profile.model_name,
        "max_budget_usd": profile.max_budget_usd,
        "agoragentic_base_url": profile.agoragentic_base_url,
        "smoke_paths": list(profile.smoke_paths),
        "live_enabled": profile.live_enabled,
        "playground_enabled": profile.enable_playground,
        "debug": profile.debug,
    }
    if metadata:
        combined_metadata.update(dict(metadata))
    return LightningTraceExport(
        task=task,
        objective=objective,
        preview_only=preview_only,
        agent_identity=agent_identity,
        spans=spans,
        rewards=rewards,
        metadata=combined_metadata,
    )


def write_agent_lightning_export(export: LightningTraceExport, output_path: str | Path) -> Path:
    """Persist an export packet as pretty-printed JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(export.as_dict(), indent=2), encoding="utf-8")
    return path
