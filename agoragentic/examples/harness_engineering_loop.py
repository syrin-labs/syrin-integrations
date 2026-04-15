"""Preview-first harness engineering loop for Syrin plus Agoragentic.

This example adapts the fixed-adapter-boundary pattern used by autonomous
harness optimizers. Agents may propose prompt, orchestration, or tool-routing
changes, but benchmark plumbing and safety rails remain fixed.

Safe default:
    The script evaluates a proposed harness change locally. It does not edit
    files, run git, call paid APIs, or deploy code.

Run:
    python agoragentic/examples/harness_engineering_loop.py
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HarnessBoundary:
    """Files and actions the harness optimizer may or may not touch."""

    editable_files: tuple[str, ...]
    fixed_files: tuple[str, ...]
    prohibited_actions: tuple[str, ...]


@dataclass(frozen=True)
class HarnessChange:
    """Proposed harness change to evaluate."""

    summary: str
    changed_files: tuple[str, ...]
    before_score: float
    after_score: float
    complexity_delta: int
    requested_actions: tuple[str, ...]


def default_boundary() -> HarnessBoundary:
    """Return the recommended Syrin/Agoragentic harness boundary."""
    return HarnessBoundary(
        editable_files=(
            "prompts/",
            "agoragentic/examples/",
            "tests/",
            "workflow_schemas/",
        ),
        fixed_files=(
            "adapter_boundary/",
            "benchmark_runner/",
            "settlement/",
            "approval_gates/",
        ),
        prohibited_actions=(
            "git add -A",
            "disable approvals",
            "raise budget without approval",
            "deploy live",
            "read secrets",
        ),
    )


def _matches_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    """Return true when the path is inside one configured prefix."""
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in prefixes)


def boundary_violations(change: HarnessChange, boundary: HarnessBoundary) -> tuple[str, ...]:
    """Find fixed-boundary file or action violations."""
    violations: list[str] = []
    for path in change.changed_files:
        if _matches_prefix(path, boundary.fixed_files):
            violations.append(f"fixed_file:{path}")
        if not _matches_prefix(path, boundary.editable_files) and not _matches_prefix(
            path, boundary.fixed_files
        ):
            violations.append(f"outside_edit_scope:{path}")
    for action in change.requested_actions:
        lowered = action.strip().lower()
        if any(prohibited.strip().lower() in lowered for prohibited in boundary.prohibited_actions):
            violations.append(f"prohibited_action:{action}")
    return tuple(violations)


def evaluate_harness_change(
    change: HarnessChange,
    boundary: HarnessBoundary | None = None,
) -> dict[str, Any]:
    """Keep, iterate, or discard a harness change using score and safety gates."""
    active_boundary = boundary or default_boundary()
    violations = boundary_violations(change, active_boundary)
    score_delta = round(change.after_score - change.before_score, 4)

    if violations:
        decision = "discard"
        reason = "boundary_violation"
    elif score_delta > 0:
        decision = "keep"
        reason = "score_improved"
    elif score_delta == 0 and change.complexity_delta < 0:
        decision = "keep"
        reason = "same_score_simpler"
    elif score_delta >= 0:
        decision = "iterate"
        reason = "no_clear_gain"
    else:
        decision = "discard"
        reason = "score_regressed"

    return {
        "decision": decision,
        "reason": reason,
        "score_delta": score_delta,
        "complexity_delta": change.complexity_delta,
        "violations": list(violations),
        "next_step": next_step_for_decision(decision),
    }


def next_step_for_decision(decision: str) -> str:
    """Map a decision to the next safe operator action."""
    if decision == "keep":
        return "record_attempt_and_prepare_scoped_pr"
    if decision == "iterate":
        return "revise_one_general_harness_rule_then_rerun"
    return "drop_change_and_capture_failure_reason"


def build_agoragentic_iteration_payload(task: str, max_cost: float) -> dict[str, Any]:
    """Build a routed request for a harness-improvement suggestion."""
    return {
        "task": task,
        "input": {
            "task": task,
            "harness_contract": {
                "fixed_adapter_boundary": True,
                "preview_only": True,
                "return_patch_plan_not_patch": True,
            },
        },
        "constraints": {
            "max_cost": max(0.01, float(max_cost)),
            "prefer_execute": True,
        },
    }


def non_negative_float(value: str) -> float:
    """Parse a non-negative CLI float."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def main() -> None:
    """Print one harness engineering evaluation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task",
        default="Suggest one simpler routing rule for preview-first research tasks.",
    )
    parser.add_argument("--max-cost", type=non_negative_float, default=0.25)
    args = parser.parse_args()

    change = HarnessChange(
        summary="Simplify preview-first routing instructions.",
        changed_files=("prompts/research-routing.md", "tests/test_research_routing.py"),
        before_score=0.82,
        after_score=0.84,
        complexity_delta=-1,
        requested_actions=("prepare scoped PR",),
    )
    output = {
        "iteration_payload": build_agoragentic_iteration_payload(args.task, args.max_cost),
        "change": {
            "summary": change.summary,
            "changed_files": list(change.changed_files),
            "before_score": change.before_score,
            "after_score": change.after_score,
            "complexity_delta": change.complexity_delta,
            "requested_actions": list(change.requested_actions),
        },
        "evaluation": evaluate_harness_change(change),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
