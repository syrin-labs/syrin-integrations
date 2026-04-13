"""Preview and optionally deploy a relay-hosted seller function.

Demonstrates:
  - inspecting current relay-hosted functions
  - previewing a relay deployment payload before sending it
  - optionally deploying a JavaScript handler to Agoragentic native hosting
  - dry-running the deployed function without billing

Requires:
  - `AGORAGENTIC_API_KEY`

Optional:
  - `--run-live` or `AGORAGENTIC_RUN_LIVE=1` to perform the deploy
  - `--auto-list` to request a marketplace listing during deploy

Run:
    python agoragentic/examples/marketplace_relay_deploy.py
    python agoragentic/examples/marketplace_relay_deploy.py --run-live
    python agoragentic/examples/marketplace_relay_deploy.py --run-live --auto-list
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


SAMPLE_SOURCE = """function handler(input) {
  const text = typeof input.text === "string" ? input.text : "";
  return {
    processed: true,
    uppercase: text.toUpperCase(),
    length: text.length,
    note: "Handled by Agoragentic relay native hosting."
  };
}"""


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
    """Preview or deploy a relay-hosted seller function."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--name",
        default="Syrin Relay Example",
        help="Relay function name to deploy.",
    )
    parser.add_argument(
        "--description",
        default="Relay-hosted example function deployed from the Syrin integration.",
        help="Optional relay function description.",
    )
    parser.add_argument(
        "--price",
        type=float,
        default=0.10,
        help="Listing price in USDC when --auto-list is enabled.",
    )
    parser.add_argument(
        "--auto-list",
        action="store_true",
        help="Request marketplace listing creation during deploy.",
    )
    parser.add_argument(
        "--run-live",
        action="store_true",
        help="Perform the relay deploy after previewing the payload.",
    )
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    api_key = os.getenv("AGORAGENTIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Set AGORAGENTIC_API_KEY before running this example.")

    run_live_env = os.getenv("AGORAGENTIC_RUN_LIVE", "").strip().lower()
    run_live = args.run_live or run_live_env in {"1", "true", "yes", "on"}

    tools = AgoragenticTools(api_key=api_key)
    relay_list = _get_tool(tools, "agoragentic_relay_list")
    relay_deploy = _get_tool(tools, "agoragentic_relay_deploy")
    relay_test = _get_tool(tools, "agoragentic_relay_test")

    _print_json("Current Relay Functions", relay_list())
    _print_json(
        "Planned Deploy Payload",
        {
            "name": args.name,
            "description": args.description,
            "source_code": SAMPLE_SOURCE,
            "auto_list": args.auto_list,
            "price": args.price,
        },
    )

    if not run_live:
        print(
            "\nPreview only. Pass --run-live or set AGORAGENTIC_RUN_LIVE=1 to deploy the "
            "relay function and dry-run it."
        )
        return

    deployment = relay_deploy(
        name=args.name,
        description=args.description,
        source_code=SAMPLE_SOURCE,
        auto_list=args.auto_list,
        price=args.price,
        tags="relay,syrin,native-hosting",
        input_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "processed": {"type": "boolean"},
                "uppercase": {"type": "string"},
                "length": {"type": "integer"},
                "note": {"type": "string"},
            },
        },
    )
    _print_json("Relay Deployment", deployment)

    relay_function_id = deployment.get("relay_function_id")
    if not relay_function_id:
        return

    _print_json(
        "Relay Dry Run",
        relay_test(
            relay_function_id=relay_function_id,
            input_data={"text": "hello from syrin relay hosting"},
        ),
    )


if __name__ == "__main__":
    main()
