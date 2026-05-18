"""Syrin v0.12 Sandbox execute loop for Agoragentic.

This example plans a Syrin-native sandbox run that keeps Agoragentic routing
preview-first. It is intentionally testable without installing Syrin because
public integrations should remain easy to inspect in CI.

Safe default:
    The script prints a sandbox plan, workspace contract, Syrin snippet, and
    Agoragentic execute payload. It does not run shell code, install packages,
    or spend funds.

Run:
    python agoragentic/examples/syrin_sandbox_execute_loop.py
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from typing import Any


SYRIN_MIN_VERSION = "0.12.0"

SENSITIVE_ACTION_TERMS = (
    "execute live",
    "live spend",
    "spend",
    "pay",
    "deploy",
    "write memory",
    "store secret",
    "retrieve secret",
)

PROHIBITED_ACTION_TERMS = (
    "exfiltrate",
    "bypass approval",
    "ignore budget",
    "disable audit",
)


@dataclass(frozen=True)
class SandboxStep:
    """One planned sandbox operation."""

    name: str
    kind: str
    description: str
    writes: tuple[str, ...] = ()
    reads: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe sandbox step."""
        return {
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
            "writes": list(self.writes),
            "reads": list(self.reads),
        }


@dataclass(frozen=True)
class SyrinSandboxPlan:
    """Preview-first plan for a Syrin Sandbox backed Agoragentic run."""

    task: str
    syrin_min_version: str
    backend: str
    packages: tuple[str, ...]
    workspace_contract: dict[str, Any]
    steps: tuple[SandboxStep, ...]
    guardrail_report: dict[str, Any]
    execute_payload: dict[str, Any]
    resource_limits: dict[str, Any]
    syrin_snippet: str

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe sandbox plan."""
        return {
            "task": self.task,
            "syrin_min_version": self.syrin_min_version,
            "backend": self.backend,
            "packages": list(self.packages),
            "workspace_contract": self.workspace_contract,
            "steps": [step.as_dict() for step in self.steps],
            "guardrail_report": self.guardrail_report,
            "execute_payload": self.execute_payload,
            "resource_limits": self.resource_limits,
            "syrin_snippet": self.syrin_snippet,
        }


def _matches_any(action: str, terms: tuple[str, ...]) -> list[str]:
    """Return sensitive terms present in an action string."""
    return [
        term
        for term in terms
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", action, flags=re.IGNORECASE)
    ]


def build_guardrail_report(requested_action: str, live_enabled: bool) -> dict[str, Any]:
    """Classify whether a sandbox action can proceed without human review."""
    sensitive_terms = _matches_any(requested_action, SENSITIVE_ACTION_TERMS)
    prohibited_terms = _matches_any(requested_action, PROHIBITED_ACTION_TERMS)
    requires_approval = bool(sensitive_terms or prohibited_terms)
    decision = "deny" if prohibited_terms else "review" if requires_approval else "allow"

    return {
        "action": requested_action,
        "live_enabled": live_enabled,
        "sensitive_terms": sensitive_terms,
        "prohibited_terms": prohibited_terms,
        "requires_approval": requires_approval,
        "decision": decision,
        "allowed": decision == "allow",
        "reason": "approval_required" if requires_approval else "preview_safe",
    }


def build_workspace_contract(task: str) -> dict[str, Any]:
    """Describe the files shared between Syrin sandbox bash and Python steps."""
    return {
        "env": "SANDBOX_WORKSPACE",
        "inputs": {
            "task.json": {
                "task": task,
                "source": "agoragentic_syrin_sandbox_execute_loop",
            }
        },
        "outputs": {
            "outputs/attempt.json": "sandbox attempt record",
            "outputs/reflection.json": "post-run reflection and next action",
        },
        "cleanup": "async with Sandbox(...) guarantees workspace teardown",
    }


def build_sandbox_steps() -> tuple[SandboxStep, ...]:
    """Return the planned bash/Python sequence for Syrin Sandbox."""
    return (
        SandboxStep(
            name="prepare_workspace",
            kind="bash",
            description="Create task and output directories inside SANDBOX_WORKSPACE.",
            writes=("task.json", "outputs/"),
        ),
        SandboxStep(
            name="run_preview_analysis",
            kind="python",
            description="Read task.json, prepare an Agoragentic execute payload, and write attempt evidence.",
            reads=("task.json",),
            writes=("outputs/attempt.json",),
        ),
        SandboxStep(
            name="write_reflection",
            kind="python",
            description="Write a no-mutation reflection with the next safe action.",
            reads=("outputs/attempt.json",),
            writes=("outputs/reflection.json",),
        ),
    )


def build_execute_payload(
    task: str,
    max_cost: float,
    guardrail_report: dict[str, Any],
    backend: str,
    run_live: bool = False,
) -> dict[str, Any]:
    """Build a preview-first Agoragentic execute payload for Syrin Sandbox."""
    can_execute = guardrail_report["decision"] == "allow" and run_live
    return {
        "task": task,
        "input": {
            "task": task,
            "sandbox": {
                "provider": "syrin",
                "min_version": SYRIN_MIN_VERSION,
                "backend": backend,
                "workspace_env": "SANDBOX_WORKSPACE",
                "write_attempt_record": True,
                "write_reflection": True,
            },
            "pre_action_review": guardrail_report,
        },
        "constraints": {
            "max_cost": float(max_cost),
            "prefer_execute": can_execute,
            "preview_only": not can_execute,
        },
    }


def build_resource_limits(max_cost: float) -> dict[str, Any]:
    """Map Agoragentic spend controls to Syrin v0.12 resource concepts."""
    return {
        "budget_max_cost": float(max_cost),
        "resource": {
            "timeout_seconds": 30,
            "max_steps": 6,
            "max_tools": 3,
            "on_exceed": "STOP",
        },
        "resource_pool": {
            "overflow": "QUEUE",
            "max_concurrency": 1,
        },
    }


def build_syrin_snippet(packages: tuple[str, ...]) -> str:
    """Return a compact Syrin v0.12 Sandbox snippet."""
    package_literal = repr(list(packages))
    return f'''# pip install --upgrade "syrin>={SYRIN_MIN_VERSION}"
import asyncio
import json
from pathlib import Path

from syrin import Sandbox

async def main():
    async with Sandbox(bash=True, python=True, packages={package_literal}) as sb:
        await sb.exec_bash("""
            mkdir -p "$SANDBOX_WORKSPACE/outputs"
            cat > "$SANDBOX_WORKSPACE/task.json" <<'JSON'
{{"task": "preview-first Agoragentic route"}}
JSON
        """)

        result = await sb.exec_python("""
            import json
            import os
            from pathlib import Path

            workspace = Path(os.environ["SANDBOX_WORKSPACE"])
            task = json.loads((workspace / "task.json").read_text())
            attempt = {{
                "status": "planned",
                "task": task["task"],
                "router": "POST /api/execute",
                "live_mutation": False,
            }}
            (workspace / "outputs" / "attempt.json").write_text(json.dumps(attempt))
            print(json.dumps(attempt))
        """)
        print(result.stdout)

asyncio.run(main())
'''


def build_syrin_sandbox_plan(
    task: str,
    max_cost: float = 0.25,
    packages: tuple[str, ...] = (),
    backend: str = "PROCESS",
    live_enabled: bool = False,
    requested_action: str = "preview route",
) -> SyrinSandboxPlan:
    """Build a Syrin v0.12 sandbox plan for Agoragentic routing."""
    if not math.isfinite(float(max_cost)) or float(max_cost) < 0:
        raise ValueError("max_cost must be a finite non-negative number")

    guardrail_report = build_guardrail_report(
        requested_action=requested_action,
        live_enabled=live_enabled,
    )
    return SyrinSandboxPlan(
        task=task,
        syrin_min_version=SYRIN_MIN_VERSION,
        backend=backend,
        packages=packages,
        workspace_contract=build_workspace_contract(task),
        steps=build_sandbox_steps(),
        guardrail_report=guardrail_report,
        execute_payload=build_execute_payload(
            task=task,
            max_cost=max_cost,
            guardrail_report=guardrail_report,
            backend=backend,
            run_live=live_enabled,
        ),
        resource_limits=build_resource_limits(max_cost=max_cost),
        syrin_snippet=build_syrin_snippet(packages=packages),
    )


def non_negative_float(value: str) -> float:
    """Parse a non-negative CLI float."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(parsed):
        raise argparse.ArgumentTypeError("must be finite")
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def parse_packages(value: str) -> tuple[str, ...]:
    """Parse a comma-separated package list."""
    if not value.strip():
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def main() -> None:
    """Print a Syrin v0.12 Sandbox execute plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="Run a preview-first Agoragentic sandbox task.")
    parser.add_argument("--max-cost", type=non_negative_float, default=0.25)
    parser.add_argument("--packages", type=parse_packages, default=())
    parser.add_argument("--backend", default="PROCESS")
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--requested-action", default="preview route")
    args = parser.parse_args()

    plan = build_syrin_sandbox_plan(
        task=args.task,
        max_cost=args.max_cost,
        packages=args.packages,
        backend=args.backend,
        live_enabled=args.run_live,
        requested_action=args.requested_action,
    )
    print(json.dumps(plan.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
