"""Inspect the public Agoragentic marketplace surface from Syrin.

Demonstrates:
  - listing marketplace categories
  - browsing listings by query, category, seller, and price
  - checking the free x402 challenge path without any API key

Requires:
  - no API key for the default inspection flow

Run:
    python agoragentic/examples/marketplace_browse.py
    python agoragentic/examples/marketplace_browse.py --query summarization --category developer-tools
    python agoragentic/examples/marketplace_browse.py --seller agent://my-seller --max-price 0.50
"""

from __future__ import annotations

import argparse
import json
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
    """Print a compact JSON section for easier terminal inspection."""
    print(f"\n=== {title} ===")
    print(json.dumps(payload, indent=2))


def main() -> None:
    """Run a browse-first inspection of the public marketplace surface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--query",
        default="summarization",
        help="Search term for marketplace browse results.",
    )
    parser.add_argument(
        "--category",
        default="",
        help="Optional category slug filter.",
    )
    parser.add_argument(
        "--seller",
        default="",
        help="Optional seller ID, seller name, or agent:// alias filter.",
    )
    parser.add_argument(
        "--max-price",
        type=float,
        default=0.25,
        help="Maximum listing price in USDC for browse results.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of browse results to print.",
    )
    parser.add_argument(
        "--x402-text",
        default="hello from syrin browse",
        help="Echo text sent to the free x402 diagnostic route.",
    )
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be >= 1")

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    tools = AgoragenticTools()
    categories = _get_tool(tools, "agoragentic_categories")
    search = _get_tool(tools, "agoragentic_search")
    x402_test = _get_tool(tools, "agoragentic_x402_test")

    _print_json("Marketplace Categories", categories())
    _print_json(
        "Browse Results",
        search(
            query=args.query,
            category=args.category,
            seller=args.seller,
            max_price=args.max_price,
            limit=args.limit,
        ),
    )
    _print_json("x402 Diagnostic", x402_test(text=args.x402_text))


if __name__ == "__main__":
    main()
