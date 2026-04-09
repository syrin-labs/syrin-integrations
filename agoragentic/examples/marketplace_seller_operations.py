"""Inspect seller-side Agoragentic operations from a Syrin-friendly workflow.

Demonstrates:
  - reviewing the seller learning queue
  - checking passport status and vault inventory
  - verifying the public x402 challenge path
  - optionally saving one reusable seller learning note

Requires:
  - `AGORAGENTIC_API_KEY`

Optional:
  - `--save-note` or `AGORAGENTIC_RUN_LIVE=1` to persist the example note

Run:
    python agoragentic/examples/marketplace_seller_operations.py
    python agoragentic/examples/marketplace_seller_operations.py --save-note
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
    """Run a seller-operations inspection flow against the Agoragentic adapter."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of learning queue items to inspect.",
    )
    parser.add_argument(
        "--save-note",
        action="store_true",
        help="Persist the sample learning note after the inspection pass.",
    )
    parser.add_argument(
        "--note-title",
        default="Route preview before paid execution",
        help="Title for the optional saved learning note.",
    )
    parser.add_argument(
        "--note-body",
        default=(
            "Use agoragentic_match first when a buyer asks for a marketplace workflow with "
            "unclear provider fit. Only move to paid execution after the preview shows a "
            "clear capability and price match."
        ),
        help="Body for the optional saved learning note.",
    )
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be >= 1")

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    api_key = os.getenv("AGORAGENTIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Set AGORAGENTIC_API_KEY before running this example.")

    run_live_env = os.getenv("AGORAGENTIC_RUN_LIVE", "").strip().lower()
    save_note = args.save_note or run_live_env in {"1", "true", "yes", "on"}

    tools = AgoragenticTools(api_key=api_key)

    learning_queue = _get_tool(tools, "agoragentic_learning_queue")
    passport = _get_tool(tools, "agoragentic_passport")
    vault = _get_tool(tools, "agoragentic_vault")
    x402_test = _get_tool(tools, "agoragentic_x402_test")

    _print_json("Passport Check", passport(action="check"))
    _print_json("Seller Learning Queue", learning_queue(limit=args.limit))
    _print_json("Vault Inventory", vault())
    _print_json("x402 Echo Diagnostic", x402_test())

    if not save_note:
        print(
            "\nInspection only. Pass --save-note or set AGORAGENTIC_RUN_LIVE=1 to persist "
            "the example seller learning note."
        )
        return

    try:
        save_learning_note = _get_tool(tools, "agoragentic_save_learning_note")
    except KeyError as exc:
        raise RuntimeError(
            "agoragentic_save_learning_note is unavailable; rerun without --save-note or "
            "update the Agoragentic integration."
        ) from exc

    _print_json(
        "Saved Learning Note",
        save_learning_note(
            title=args.note_title,
            lesson=args.note_body,
            source_type="manual",
            tags="seller-ops,preview-first,syrin",
            confidence=0.8,
        ),
    )


if __name__ == "__main__":
    main()
