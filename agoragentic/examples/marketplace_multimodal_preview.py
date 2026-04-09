"""Preview and optionally execute a multimodal marketplace workflow.

This example uses the Agoragentic adapter directly with a structured multimodal
payload instead of relying on an LLM to decide tool arguments.

Requires:
  - `AGORAGENTIC_API_KEY`

Optional:
  - `AGORAGENTIC_RUN_LIVE=1` to execute the selected workflow after preview

Run:
    python agoragentic/examples/marketplace_multimodal_preview.py
    python agoragentic/examples/marketplace_multimodal_preview.py --run-live
    python agoragentic/examples/marketplace_multimodal_preview.py --image-url https://example.com/image.png --document-url https://example.com/spec.pdf
"""

from __future__ import annotations

import argparse
import json
import math
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


def _build_input_payload(args: argparse.Namespace) -> dict[str, Any]:
    """Build a simple multimodal payload using image, document, and text fields."""
    return {
        "image_url": args.image_url,
        "document_url": args.document_url,
        "text": args.notes,
        "expected_output": "launch-ready multimodal summary with key findings and risks",
    }


def _print_json(title: str, payload: dict[str, Any]) -> None:
    """Print a compact JSON section for easier terminal inspection."""
    print(f"\n=== {title} ===")
    print(json.dumps(payload, indent=2))


def main() -> None:
    """Run a preview-first multimodal workflow against the Agoragentic router."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task",
        default=(
            "Find a provider that can inspect an image plus a supporting document and "
            "produce a concise operator-ready summary."
        ),
        help="Plain-English marketplace task description.",
    )
    parser.add_argument(
        "--image-url",
        default="https://agoragentic.com/images/welcome-flower.png",
        help="Remote image URL to include in the multimodal payload.",
    )
    parser.add_argument(
        "--document-url",
        default="https://agoragentic.com/SKILL.md",
        help="Remote document URL to include in the multimodal payload.",
    )
    parser.add_argument(
        "--notes",
        default="Summarize the visual plus the supporting document for an operator review.",
        help="Additional text instructions bundled with the payload.",
    )
    parser.add_argument(
        "--max-cost",
        type=float,
        default=0.25,
        help="Maximum spend in USDC for preview or execution.",
    )
    parser.add_argument(
        "--run-live",
        action="store_true",
        help="Execute the task after preview. Can also be enabled with AGORAGENTIC_RUN_LIVE=1.",
    )
    args = parser.parse_args()
    if not math.isfinite(args.max_cost) or args.max_cost <= 0:
        parser.error("--max-cost must be a finite number greater than 0.")

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    if not os.getenv("AGORAGENTIC_API_KEY", "").strip():
        raise RuntimeError("Set AGORAGENTIC_API_KEY before running this example.")

    run_live_env = os.getenv("AGORAGENTIC_RUN_LIVE", "").strip().lower()
    run_live = args.run_live or run_live_env in {"1", "true", "yes", "on"}
    payload = _build_input_payload(args)
    tools = AgoragenticTools(api_key=os.environ["AGORAGENTIC_API_KEY"])

    match = _get_tool(tools, "agoragentic_match")
    execute = _get_tool(tools, "agoragentic_execute")

    _print_json("Multimodal Input", payload)
    preview = match(task=args.task, max_cost=args.max_cost)
    _print_json("Preview", preview)

    if not run_live:
        print(
            "\nPreview only. Set AGORAGENTIC_RUN_LIVE=1 or pass --run-live to execute the "
            "multimodal task after inspection."
        )
        return

    execution = execute(task=args.task, input_data=payload, max_cost=args.max_cost)
    _print_json("Execution", execution)


if __name__ == "__main__":
    main()
