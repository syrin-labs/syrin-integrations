"""Preview and optionally invoke one known marketplace listing.

Demonstrates:
  - browsing for a known listing by query
  - selecting one listing ID or slug for direct invocation
  - previewing the exact invoke payload before any paid call

Requires for live invoke:
  - `AGORAGENTIC_API_KEY`

Optional:
  - `--run-live` or `AGORAGENTIC_RUN_LIVE=1` to perform the direct invoke

Run:
    python agoragentic/examples/marketplace_direct_invoke.py
    python agoragentic/examples/marketplace_direct_invoke.py --listing-id <listing-id> --run-live
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
    """Print a compact JSON section for easier terminal inspection."""
    print(f"\n=== {title} ===")
    print(json.dumps(payload, indent=2))


def main() -> None:
    """Preview or directly invoke one chosen marketplace listing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--query",
        default="summarization",
        help="Search term used to find a candidate listing.",
    )
    parser.add_argument(
        "--category",
        default="",
        help="Optional category slug for the browse step.",
    )
    parser.add_argument(
        "--max-price",
        type=float,
        default=0.25,
        help="Maximum listing price in USDC for the browse step.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of browse results to inspect.",
    )
    parser.add_argument(
        "--listing-id",
        default="",
        help="Known listing UUID or slug. When omitted, the first browse result is selected.",
    )
    parser.add_argument(
        "--input-text",
        default="Summarize the main technical argument in three bullets.",
        help="Input text passed to the chosen listing in live mode.",
    )
    parser.add_argument(
        "--run-live",
        action="store_true",
        help="Perform the direct invoke after previewing the chosen listing.",
    )
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be >= 1")

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    run_live_env = os.getenv("AGORAGENTIC_RUN_LIVE", "").strip().lower()
    run_live = args.run_live or run_live_env in {"1", "true", "yes", "on"}
    api_key = os.getenv("AGORAGENTIC_API_KEY", "").strip()

    tools = AgoragenticTools(api_key=api_key)
    search = _get_tool(tools, "agoragentic_search")
    invoke = _get_tool(tools, "agoragentic_invoke")

    browse = search(
        query=args.query,
        category=args.category,
        max_price=args.max_price,
        limit=args.limit,
    )
    _print_json("Browse Results", browse)

    chosen_listing = args.listing_id
    if not chosen_listing:
        capabilities = browse.get("capabilities") or []
        if not capabilities:
            raise RuntimeError("No listing candidates found. Adjust --query, --category, or --max-price.")
        chosen_listing = capabilities[0].get("id") or ""
    if not chosen_listing:
        raise RuntimeError("Could not resolve a listing ID or slug for direct invoke.")

    planned_invoke = {
        "capability_id": chosen_listing,
        "input": {"text": args.input_text},
        "purpose": "direct invoke for a known listing instead of routed execute()",
    }
    _print_json("Chosen Listing Invoke Payload", planned_invoke)

    if not run_live:
        print(
            "\nPreview only. Pass --run-live or set AGORAGENTIC_RUN_LIVE=1 to perform "
            "the direct invoke once you have confirmed the target listing."
        )
        return

    if not api_key:
        raise RuntimeError("Set AGORAGENTIC_API_KEY before using --run-live.")

    _print_json(
        "Invoke Result",
        invoke(
            capability_id=chosen_listing,
            input_data={"text": args.input_text},
        ),
    )


if __name__ == "__main__":
    main()
