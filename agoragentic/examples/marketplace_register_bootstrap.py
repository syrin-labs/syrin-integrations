"""Preview and optionally run Agoragentic agent registration from Syrin.

This example is safe-by-default:
- it prints the bootstrap payload first
- it only creates a new agent when live mode is explicitly enabled
- it surfaces the returned API key and wallet bootstrap fields for the next step

Requires for preview only:
  - no API key

Requires for live registration:
  - no API key, but you must pass --run-live or set AGORAGENTIC_RUN_LIVE=1

Run:
    python agoragentic/examples/marketplace_register_bootstrap.py
    python agoragentic/examples/marketplace_register_bootstrap.py --agent-name my-syrin-agent --agent-type buyer --run-live
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agoragentic.agoragentic_syrin import AgoragenticTools


def _get_tool(tools: AgoragenticTools, name: str) -> Callable[..., dict[str, Any]]:
    """Look up one wrapped adapter tool by function name."""
    for tool in tools:
        if getattr(tool, "__name__", "") == name:
            return tool
    raise KeyError(f"Tool {name!r} not found in AgoragenticTools.")


def _print_json(title: str, payload: dict[str, Any]) -> None:
    """Print a labeled JSON block for easier terminal inspection."""
    print(f"\n=== {title} ===")
    print(json.dumps(payload, indent=2))


def _build_preview_payload(args: argparse.Namespace) -> dict[str, Any]:
    """Build the quickstart bootstrap payload without sending it."""
    return {
        "name": args.agent_name,
        "type": args.agent_type,
        "endpoint": "POST /api/quickstart",
        "purpose": "create an Agoragentic buyer, seller, or dual-use agent",
    }


def _print_next_steps(result: dict[str, Any]) -> None:
    """Print follow-up steps after a successful live registration."""
    if result.get("api_key"):
        print("\nSet AGORAGENTIC_API_KEY to the returned api_key before running the other examples.")
    wallet = result.get("wallet") or {}
    if wallet:
        print(
            "Wallet bootstrap: "
            f"balance={wallet.get('balance')} {wallet.get('currency')}, "
            f"chain={wallet.get('chain')}, "
            f"setup_required={wallet.get('setup_required')}"
        )


def main() -> None:
    """Preview or run Agoragentic quickstart registration from the integration."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agent-name",
        default="my-syrin-agent",
        help="Agent display name to register with Agoragentic.",
    )
    parser.add_argument(
        "--agent-type",
        choices=("buyer", "seller", "both"),
        default="both",
        help="Registration mode for the new agent.",
    )
    parser.add_argument(
        "--run-live",
        action="store_true",
        help="Create the agent now. Can also be enabled with AGORAGENTIC_RUN_LIVE=1.",
    )
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    run_live_env = os.getenv("AGORAGENTIC_RUN_LIVE", "").strip().lower()
    run_live = args.run_live or run_live_env in {"1", "true", "yes", "on"}

    tools = AgoragenticTools()
    register = _get_tool(tools, "agoragentic_register")

    _print_json("Registration Preview", _build_preview_payload(args))

    if not run_live:
        print(
            "\nPreview only. Pass --run-live or set AGORAGENTIC_RUN_LIVE=1 to create the "
            "agent and receive the bootstrap credentials."
        )
        return

    result = register(agent_name=args.agent_name, agent_type=args.agent_type)
    _print_json("Registration Result", result)
    _print_next_steps(result)


if __name__ == "__main__":
    main()
