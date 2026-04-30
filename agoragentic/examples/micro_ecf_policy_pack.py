"""Micro ECF policy pack for Syrin agents using Agoragentic.

Micro ECF is the lightweight governance layer for local or hosted agents that
need explicit intent, budget boundaries, tool limits, approval evidence, and
outcome reconciliation without adopting a full enterprise control plane.

Safe default:
    This example builds and evaluates a policy pack only. It does not spend
    funds, deploy code, write memory, or retrieve secrets.

Run:
    python agoragentic/examples/micro_ecf_policy_pack.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any


SENSITIVE_ACTION_TERMS = (
    "execute live",
    "spend",
    "pay",
    "settle",
    "deploy",
    "write memory",
    "store secret",
    "retrieve secret",
    "send email",
    "post outreach",
    "change budget",
)

PROHIBITED_ACTION_TERMS = (
    "disable approval",
    "bypass review",
    "unbounded spend",
    "export private key",
    "ignore budget",
)

SECRET_LIKE_TERMS = ("api_key", "secret", "token", "private_key", "seed phrase", "authorization")


@dataclass(frozen=True)
class IntentContract:
    """Bounded statement of what the agent is allowed to pursue."""

    goal: str
    allowed_outcomes: tuple[str, ...]
    forbidden_outcomes: tuple[str, ...]
    success_metrics: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe intent contract."""
        return {
            "goal": self.goal,
            "allowed_outcomes": list(self.allowed_outcomes),
            "forbidden_outcomes": list(self.forbidden_outcomes),
            "success_metrics": list(self.success_metrics),
        }


@dataclass(frozen=True)
class ExecutionBoundary:
    """Controls that constrain spend, tools, mutation, and external effects."""

    max_cost_usd: float
    live_spend_allowed: bool
    deployment_allowed: bool
    memory_write_allowed: bool
    secret_access_allowed: bool
    external_messaging_allowed: bool
    require_match_before_execute: bool = True

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe execution boundary."""
        return {
            "max_cost_usd": self.max_cost_usd,
            "live_spend_allowed": self.live_spend_allowed,
            "deployment_allowed": self.deployment_allowed,
            "memory_write_allowed": self.memory_write_allowed,
            "secret_access_allowed": self.secret_access_allowed,
            "external_messaging_allowed": self.external_messaging_allowed,
            "require_match_before_execute": self.require_match_before_execute,
        }


@dataclass(frozen=True)
class MicroECFPolicyPack:
    """Portable Micro ECF contract for a Syrin agent or swarm."""

    name: str
    version: str
    intent: IntentContract
    boundary: ExecutionBoundary
    review_gates: dict[str, list[str]]
    consequence_axes: tuple[str, ...]
    reconciliation_required: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe policy pack."""
        return {
            "name": self.name,
            "version": self.version,
            "intent": self.intent.as_dict(),
            "boundary": self.boundary.as_dict(),
            "review_gates": self.review_gates,
            "consequence_axes": list(self.consequence_axes),
            "reconciliation_required": list(self.reconciliation_required),
            "fingerprint": fingerprint_policy(self),
        }


def non_negative_float(value: str) -> float:
    """Parse a finite non-negative CLI float."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(parsed):
        raise argparse.ArgumentTypeError("must be finite")
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def default_intent_contract(goal: str) -> IntentContract:
    """Build the default Micro ECF intent contract for a marketplace agent."""
    return IntentContract(
        goal=goal,
        allowed_outcomes=(
            "preview_routes",
            "score_leads",
            "prepare_outreach_drafts",
            "record_receipts",
            "propose_learning_notes",
        ),
        forbidden_outcomes=(
            "unapproved_live_spend",
            "unapproved_deployment",
            "secret_exfiltration",
            "unreviewed_external_messaging",
            "memory_poisoning",
        ),
        success_metrics=(
            "cost_within_budget",
            "approval_evidence_present",
            "receipt_or_trace_recorded",
            "outcome_reconciled_to_intent",
        ),
    )


def default_boundary(max_cost_usd: float = 0.25, live_enabled: bool = False) -> ExecutionBoundary:
    """Build fail-closed execution boundaries for Micro ECF."""
    return ExecutionBoundary(
        max_cost_usd=max(0.0, float(max_cost_usd)),
        live_spend_allowed=live_enabled,
        deployment_allowed=False,
        memory_write_allowed=False,
        secret_access_allowed=False,
        external_messaging_allowed=False,
    )


def default_review_gates() -> dict[str, list[str]]:
    """Return evidence requirements for sensitive action classes."""
    return {
        "live_spend": ["match_preview", "budget_remaining", "human_approval", "receipt_required"],
        "deployment": ["sandbox_passed", "rollback_plan", "human_approval"],
        "memory_write": ["source_provenance", "reviewed_content", "rollback_key"],
        "secret_access": ["declared_secret_label", "least_privilege_reason", "human_approval"],
        "external_message": ["recipient_scope", "message_preview", "rate_limit", "human_approval"],
        "budget_change": ["current_allocation", "new_allocation", "reason", "audit_log"],
    }


def build_micro_ecf_policy_pack(
    goal: str,
    max_cost_usd: float = 0.25,
    live_enabled: bool = False,
    name: str = "agoragentic-syrin-micro-ecf",
) -> MicroECFPolicyPack:
    """Build a portable Micro ECF policy pack for Syrin examples."""
    return MicroECFPolicyPack(
        name=name,
        version="0.1.0",
        intent=default_intent_contract(goal),
        boundary=default_boundary(max_cost_usd=max_cost_usd, live_enabled=live_enabled),
        review_gates=default_review_gates(),
        consequence_axes=(
            "financial_cost",
            "trust_impact",
            "reputation_risk",
            "security_risk",
            "rollback_complexity",
        ),
        reconciliation_required=(
            "intent_vs_action",
            "expected_cost_vs_actual_cost",
            "approval_vs_effect",
            "receipt_vs_settlement",
        ),
    )


def fingerprint_policy(policy: MicroECFPolicyPack) -> str:
    """Create a deterministic fingerprint without including runtime secrets."""
    data = {
        "name": policy.name,
        "version": policy.version,
        "intent": policy.intent.as_dict(),
        "boundary": policy.boundary.as_dict(),
        "review_gates": policy.review_gates,
        "consequence_axes": list(policy.consequence_axes),
        "reconciliation_required": list(policy.reconciliation_required),
    }
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _contains_any(text: str, terms: tuple[str, ...]) -> list[str]:
    """Return matching terms from a case-insensitive text scan."""
    lowered = text.lower()
    return [term for term in terms if term in lowered]


def classify_action(action: str, policy: MicroECFPolicyPack) -> dict[str, Any]:
    """Evaluate an action against the policy pack before execution."""
    sensitive_terms = _contains_any(action, SENSITIVE_ACTION_TERMS)
    prohibited_terms = _contains_any(action, PROHIBITED_ACTION_TERMS)
    secret_terms = _contains_any(action, SECRET_LIKE_TERMS)

    requires_review = bool(sensitive_terms or secret_terms)
    blocked_reasons: list[str] = []
    if prohibited_terms:
        blocked_reasons.append("prohibited_action")
    if secret_terms and not policy.boundary.secret_access_allowed:
        blocked_reasons.append("secret_access_not_allowed")
    if "deploy" in sensitive_terms and not policy.boundary.deployment_allowed:
        blocked_reasons.append("deployment_not_allowed")
    if any(term in sensitive_terms for term in ("execute live", "spend", "pay", "settle")):
        if not policy.boundary.live_spend_allowed:
            blocked_reasons.append("live_spend_not_allowed")
    if "write memory" in sensitive_terms and not policy.boundary.memory_write_allowed:
        blocked_reasons.append("memory_write_not_allowed")
    if any(term in sensitive_terms for term in ("send email", "post outreach")):
        if not policy.boundary.external_messaging_allowed:
            blocked_reasons.append("external_messaging_not_allowed")

    decision = "deny" if blocked_reasons else "review" if requires_review else "allow"
    return {
        "action": action,
        "decision": decision,
        "requires_review": requires_review,
        "sensitive_terms": sensitive_terms,
        "prohibited_terms": prohibited_terms,
        "blocked_reasons": blocked_reasons,
        "required_evidence": required_evidence_for_terms(sensitive_terms),
        "policy_fingerprint": fingerprint_policy(policy),
    }


def required_evidence_for_terms(sensitive_terms: list[str]) -> list[str]:
    """Map sensitive action terms to Micro ECF evidence requirements."""
    evidence: list[str] = []
    if any(term in sensitive_terms for term in ("execute live", "spend", "pay", "settle")):
        evidence.extend(default_review_gates()["live_spend"])
    if "deploy" in sensitive_terms:
        evidence.extend(default_review_gates()["deployment"])
    if "write memory" in sensitive_terms:
        evidence.extend(default_review_gates()["memory_write"])
    if any(term in sensitive_terms for term in ("store secret", "retrieve secret")):
        evidence.extend(default_review_gates()["secret_access"])
    if any(term in sensitive_terms for term in ("send email", "post outreach")):
        evidence.extend(default_review_gates()["external_message"])
    if "change budget" in sensitive_terms:
        evidence.extend(default_review_gates()["budget_change"])
    return sorted(set(evidence))


def build_execute_payload(
    task: str,
    policy: MicroECFPolicyPack,
    action: str = "preview route",
) -> dict[str, Any]:
    """Build an Agoragentic execute payload carrying Micro ECF constraints."""
    decision = classify_action(action, policy)
    return {
        "task": task,
        "input": {
            "task": task,
            "micro_ecf": policy.as_dict(),
            "pre_action_review": decision,
        },
        "constraints": {
            "max_cost": policy.boundary.max_cost_usd,
            "prefer_execute": True,
            "require_match_before_execute": policy.boundary.require_match_before_execute,
            "preview_only": decision["decision"] != "allow" or not policy.boundary.live_spend_allowed,
        },
    }


def build_syrin_mount_instructions(policy: MicroECFPolicyPack) -> list[str]:
    """Describe how to mount Micro ECF into a Syrin agent or swarm."""
    return [
        "Mount the Micro ECF policy pack as read-only agent context.",
        "Run classify_action before paid tools, deployment, memory writes, secrets, or outreach.",
        "Use agoragentic_match before agoragentic_execute when provider fit is unclear.",
        "Record policy_fingerprint with receipts, traces, and learning notes.",
        "Reconcile intent, approval, cost, receipt, and settlement after each live action.",
        f"Policy fingerprint: {fingerprint_policy(policy)}",
    ]


def main() -> None:
    """Print a Micro ECF policy pack and preview execute payload."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--goal",
        default=(
            "Operate a Syrin agent that previews marketplace routes, scores leads, "
            "drafts growth actions, and never spends or mutates state without approval."
        ),
    )
    parser.add_argument("--task", default="Preview one safe revenue-supporting next action.")
    parser.add_argument("--action", default="preview route")
    parser.add_argument("--max-cost", type=non_negative_float, default=0.25)
    parser.add_argument("--run-live", action="store_true")
    args = parser.parse_args()

    policy = build_micro_ecf_policy_pack(
        goal=args.goal,
        max_cost_usd=args.max_cost,
        live_enabled=args.run_live,
    )
    output = {
        "policy_pack": policy.as_dict(),
        "action_review": classify_action(args.action, policy),
        "execute_payload": build_execute_payload(args.task, policy, action=args.action),
        "syrin_mount_instructions": build_syrin_mount_instructions(policy),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
