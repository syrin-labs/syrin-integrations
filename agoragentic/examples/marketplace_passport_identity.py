"""Inspect Agoragentic Passport identity surfaces from a Syrin integration.

This example stays safe-by-default:
- it always allows the public passport info surface
- it optionally verifies one wallet address
- it optionally looks up one public agent identity
- it only performs the authenticated passport check when explicitly requested

Requires for public info only:
  - no API key

Requires for wallet or identity lookup:
  - no API key, but you must pass the wallet address and/or agent ref

Requires for authenticated status check:
  - `AGORAGENTIC_API_KEY`

Run:
    python agoragentic/examples/marketplace_passport_identity.py
    python agoragentic/examples/marketplace_passport_identity.py --wallet-address 0x123...
    python agoragentic/examples/marketplace_passport_identity.py --agent-ref agent://demo
    python agoragentic/examples/marketplace_passport_identity.py --check-auth
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
    available = [getattr(tool, "__name__", type(tool).__name__) for tool in tools]
    raise KeyError(
        f"Tool {name!r} not found in AgoragenticTools. Available: {', '.join(available)}"
    )


def _print_json(title: str, payload: dict[str, Any]) -> None:
    """Print a labeled JSON block for easier terminal inspection."""
    print(f"\n=== {title} ===")
    print(json.dumps(payload, indent=2))


def main() -> None:
    """Inspect public and authenticated passport surfaces through the adapter."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wallet-address",
        default="",
        help="Optional wallet address to verify against the public passport surface.",
    )
    parser.add_argument(
        "--agent-ref",
        default="",
        help="Optional agent ID or agent:// reference for public identity lookup.",
    )
    parser.add_argument(
        "--check-auth",
        action="store_true",
        help="Run the authenticated passport status check when AGORAGENTIC_API_KEY is set.",
    )
    args = parser.parse_args()
    wallet_address = args.wallet_address.strip()
    agent_ref = args.agent_ref.strip()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    tools = AgoragenticTools(api_key=os.getenv("AGORAGENTIC_API_KEY", ""))
    passport = _get_tool(tools, "agoragentic_passport")

    _print_json("Passport Info", passport(action="info"))

    if wallet_address:
        _print_json(
            "Wallet Verification",
            passport(action="verify", wallet_address=wallet_address),
        )
    else:
        print(
            "\nSkip wallet verification. Pass --wallet-address to inspect one public wallet "
            "verification surface."
        )

    if agent_ref:
        _print_json(
            "Agent Identity",
            passport(action="identity", agent_ref=agent_ref),
        )
    else:
        print(
            "\nSkip identity lookup. Pass --agent-ref to inspect one public agent identity "
            "surface."
        )

    if not args.check_auth:
        print(
            "\nAuthenticated passport check skipped. Pass --check-auth to inspect the "
            "current agent's passport status when AGORAGENTIC_API_KEY is set."
        )
        return

    if not os.getenv("AGORAGENTIC_API_KEY", "").strip():
        raise RuntimeError(
            "Set AGORAGENTIC_API_KEY before using --check-auth for the authenticated "
            "passport status surface."
        )

    _print_json("Authenticated Passport Check", passport(action="check"))


if __name__ == "__main__":
    main()
