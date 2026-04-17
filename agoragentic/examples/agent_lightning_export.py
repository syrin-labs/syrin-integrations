"""Build an Agent Lightning-compatible export packet for the hosted Syrin starter kit.

This example does not start a trainer and does not require the `agentlightning`
package. It emits spans, rewards, and metadata that can be consumed later by an
offline optimizer or adapter.

Run:
    python agoragentic/examples/agent_lightning_export.py
    python agoragentic/examples/agent_lightning_export.py --task-completed --actual-cost 0.12
    python agoragentic/examples/agent_lightning_export.py --print-agent-os-prompt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args: Any, **_kwargs: Any) -> bool:
        """Allow offline tests to import this example without python-dotenv."""
        return False

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agoragentic.starter_kits.hosted_syrin_agent.agent_os_prompt import (
    build_agent_os_implementation_prompt,
)
from agoragentic.starter_kits.hosted_syrin_agent.config import build_runtime_profile
from agoragentic.starter_kits.hosted_syrin_agent.tracing import (
    build_agent_lightning_export,
    build_default_spans,
    build_reward_signals,
    write_agent_lightning_export,
)

DEFAULT_TASK = (
    "Preview a routed Agoragentic workflow, preserve budget discipline, and export "
    "the resulting spans and rewards for offline optimization."
)


def _build_parser() -> argparse.ArgumentParser:
    """Create CLI arguments for the export example."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="?", default=DEFAULT_TASK, help="Task to describe in the export packet.")
    parser.add_argument(
        "--output",
        default="agoragentic/artifacts/agent_lightning_export.json",
        help="JSON output path for the export packet.",
    )
    parser.add_argument(
        "--objective",
        default="Improve hosted Syrin routing behavior without weakening preview-first safety gates.",
        help="Optimization objective to store with the packet.",
    )
    parser.add_argument(
        "--matched-providers",
        type=int,
        default=2,
        help="Number of provider candidates surfaced during preview.",
    )
    parser.add_argument(
        "--actual-cost",
        type=float,
        default=0.0,
        help="Actual cost used for reward shaping.",
    )
    parser.add_argument(
        "--task-completed",
        action="store_true",
        help="Mark the task as completed instead of preview-only planning evidence.",
    )
    parser.add_argument(
        "--approval-required",
        action="store_true",
        help="Mark the export as requiring an approval gate.",
    )
    parser.add_argument(
        "--sandbox-failed",
        action="store_true",
        help="Mark the sandbox safety signal as failed.",
    )
    parser.add_argument(
        "--print-agent-os-prompt",
        action="store_true",
        help="Print the Agent OS implementation prompt after writing the export.",
    )
    return parser


def main() -> None:
    """Write the export packet and optionally print the Agent OS prompt."""
    load_dotenv(ROOT / "agoragentic" / ".env", override=False)
    load_dotenv(ROOT / "agoragentic" / "starter_kits" / "hosted_syrin_agent" / ".env", override=False)

    args = _build_parser().parse_args()
    profile = build_runtime_profile()
    preview_only = not profile.live_enabled

    spans = build_default_spans(
        task=args.task,
        max_cost_usd=profile.max_budget_usd,
        preview_only=preview_only,
        matched_providers=max(0, args.matched_providers),
        approval_required=args.approval_required,
    )
    rewards = build_reward_signals(
        preview_only=preview_only,
        max_cost_usd=profile.max_budget_usd,
        actual_cost_usd=max(0.0, args.actual_cost),
        matched_providers=max(0, args.matched_providers),
        sandbox_passed=not args.sandbox_failed,
        approval_required=args.approval_required,
        task_completed=args.task_completed,
    )
    export = build_agent_lightning_export(
        task=args.task,
        objective=args.objective,
        profile=profile,
        spans=spans,
        rewards=rewards,
        preview_only=preview_only,
        metadata={"source": "agoragentic/examples/agent_lightning_export.py"},
    )
    path = write_agent_lightning_export(export, ROOT / args.output)

    print(f"Wrote Agent Lightning export to {path}", file=sys.stderr)
    print(json.dumps(export.as_dict(), indent=2))

    if args.print_agent_os_prompt:
        print("\n=== Agent OS Prompt ===")
        print(build_agent_os_implementation_prompt())


if __name__ == "__main__":
    main()
