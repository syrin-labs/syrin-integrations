"""Optional OpenAI Agents SDK sandbox loop for Agoragentic/Syrin.

This example mirrors the new Agents SDK sandbox pattern while keeping the
Agoragentic integration framework-optional. It can be read and tested without
installing `openai-agents`.

Safe default:
    The script prints a manifest plan, instructions, guardrail report, and
    SDK snippet. It does not launch a sandbox or spend funds unless a caller
    implements an explicit live runner.

Run:
    python agoragentic/examples/openai_agents_sandbox_loop.py
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from typing import Any


SENSITIVE_ACTION_TERMS = (
    "execute live",
    "spend",
    "pay",
    "deploy",
    "write memory",
    "store secret",
    "retrieve secret",
)


@dataclass(frozen=True)
class SandboxPlan:
    """Framework-neutral plan for a sandboxed Agoragentic run."""

    task: str
    manifest_entries: dict[str, str]
    instructions: str
    guardrail_report: dict[str, Any]
    execute_payload: dict[str, Any]
    sdk_snippet: str

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-safe sandbox plan."""
        return {
            "task": self.task,
            "manifest_entries": self.manifest_entries,
            "instructions": self.instructions,
            "guardrail_report": self.guardrail_report,
            "execute_payload": self.execute_payload,
            "sdk_snippet": self.sdk_snippet,
        }


def build_manifest_entries() -> dict[str, str]:
    """Describe the files that should be mounted into the sandbox."""
    return {
        "instructions/AGENTS.md": "Agoragentic/Syrin operating instructions",
        "inputs/task.json": "Task, budget, and workflow contract",
        "outputs/attempt.json": "Attempt record written by the sandbox run",
        "outputs/reflection.json": "Reflection note written after grading",
    }


def build_sandbox_instructions(max_cost: float, live_enabled: bool) -> str:
    """Build instructions for a sandbox agent."""
    mode = "live-enabled" if live_enabled else "preview-only"
    return "\n".join(
        [
            "You are a sandboxed Syrin agent using Agoragentic as the capability router.",
            f"Mode: {mode}",
            f"Maximum spend: ${max_cost:.2f}",
            "Prefer /api/execute routing over hard-coded provider IDs.",
            "Write process evidence to outputs/attempt.json.",
            "Write reflection and next action to outputs/reflection.json.",
            "Do not access secrets, deploy, or execute live spend without approval.",
        ]
    )


def guard_sensitive_action(action: str, live_enabled: bool) -> dict[str, Any]:
    """Gate live spend, deployment, memory writes, and secret access."""
    lowered = action.lower()
    sensitive_terms = [term for term in SENSITIVE_ACTION_TERMS if term in lowered]
    requires_approval = bool(sensitive_terms)
    return {
        "action": action,
        "live_enabled": live_enabled,
        "sensitive_terms": sensitive_terms,
        "requires_approval": requires_approval,
        "allowed": not requires_approval,
    }


def build_execute_payload(task: str, max_cost: float) -> dict[str, Any]:
    """Build a preview-first Agoragentic execute payload for the sandbox."""
    return {
        "task": task,
        "input": {
            "task": task,
            "sandbox": {
                "provider": "openai-agents-sdk",
                "manifest_required": True,
                "write_attempt_record": True,
            },
        },
        "constraints": {
            "max_cost": float(max_cost),
            "prefer_execute": True,
        },
    }


def build_sdk_snippet() -> str:
    """Return a compact optional Agents SDK snippet for users who install it."""
    return '''# pip install "openai-agents>=0.14.0"
from agents import Runner
from agents.run import RunConfig
from agents.sandbox import Manifest, SandboxAgent, SandboxRunConfig
from agents.sandbox.entries import LocalDir
from agents.sandbox.sandboxes import UnixLocalSandboxClient

agent = SandboxAgent(
    name="Agoragentic Syrin Sandbox",
    model="gpt-5.4",
    instructions=instructions,
    default_manifest=Manifest(entries={"workspace": LocalDir(src=workspace_path)}),
)

result = await Runner.run(
    agent,
    task,
    run_config=RunConfig(sandbox=SandboxRunConfig(client=UnixLocalSandboxClient())),
)'''


def build_sandbox_plan(
    task: str,
    max_cost: float = 0.25,
    live_enabled: bool = False,
    requested_action: str = "preview route",
) -> SandboxPlan:
    """Build a framework-neutral plan for optional Agents SDK execution."""
    return SandboxPlan(
        task=task,
        manifest_entries=build_manifest_entries(),
        instructions=build_sandbox_instructions(max_cost=max_cost, live_enabled=live_enabled),
        guardrail_report=guard_sensitive_action(requested_action, live_enabled=live_enabled),
        execute_payload=build_execute_payload(task, max_cost=max_cost),
        sdk_snippet=build_sdk_snippet(),
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


def main() -> None:
    """Print an optional OpenAI Agents SDK sandbox plan."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="Run a preview-first Agoragentic sandbox task.")
    parser.add_argument("--max-cost", type=non_negative_float, default=0.25)
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--requested-action", default="preview route")
    args = parser.parse_args()

    plan = build_sandbox_plan(
        task=args.task,
        max_cost=args.max_cost,
        live_enabled=args.run_live,
        requested_action=args.requested_action,
    )
    print(json.dumps(plan.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
