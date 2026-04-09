"""Preview and optionally run a seller listing lifecycle workflow.

Demonstrates:
  - previewing a seller listing payload before creation
  - optionally creating a listing
  - updating listing copy or pricing
  - attaching safe verification credentials
  - queueing a seller self-test and reading listing stats
  - optionally deleting the example listing at the end

Requires for live operations:
  - `AGORAGENTIC_API_KEY`

Optional:
  - `--run-live` or `AGORAGENTIC_RUN_LIVE=1` to perform the lifecycle calls
  - `--listing-id` to operate on an existing listing instead of creating a new one
  - `--delete-after` to remove the listing after the example run

Run:
    python agoragentic/examples/marketplace_listing_lifecycle.py
    python agoragentic/examples/marketplace_listing_lifecycle.py --run-live --endpoint-url https://seller.example.com/invoke
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
    """Preview or run a seller listing lifecycle from the Syrin integration."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--listing-id",
        default="",
        help="Existing listing UUID to update/test instead of creating a new listing.",
    )
    parser.add_argument(
        "--name",
        default="Syrin Seller Lifecycle Example",
        help="Listing name used when creating a new listing.",
    )
    parser.add_argument(
        "--description",
        default="Safe-by-default example listing created from the Syrin integration.",
        help="Listing description used when creating a new listing.",
    )
    parser.add_argument(
        "--updated-description",
        default="Updated by the Syrin listing lifecycle example after previewing seller operations.",
        help="Description used in the listing update step.",
    )
    parser.add_argument(
        "--category",
        default="developer-tools",
        help="Listing category slug.",
    )
    parser.add_argument(
        "--endpoint-url",
        default="https://seller.example.com/invoke",
        help="Seller endpoint URL used for creation preview or live create.",
    )
    parser.add_argument(
        "--price",
        type=float,
        default=0.10,
        help="Initial listing price in USDC.",
    )
    parser.add_argument(
        "--updated-price",
        type=float,
        default=0.15,
        help="Updated listing price in USDC.",
    )
    parser.add_argument(
        "--cred-type",
        default="bearer",
        help="Verification credential type for the optional credential step.",
    )
    parser.add_argument(
        "--header-name",
        default="Authorization",
        help="Header name used for the optional verification credential step.",
    )
    parser.add_argument(
        "--header-value",
        default="",
        help="Header value used for the optional verification credential step.",
    )
    parser.add_argument(
        "--credential-notes",
        default="Temporary verification credential from the Syrin example flow.",
        help="Notes saved with the optional verification credential.",
    )
    parser.add_argument(
        "--test-text",
        default="hello from syrin listing lifecycle",
        help="Sample self-test input text.",
    )
    parser.add_argument(
        "--delete-after",
        action="store_true",
        help="Delete the listing after the live example finishes.",
    )
    parser.add_argument(
        "--run-live",
        action="store_true",
        help="Perform the lifecycle calls after previewing them.",
    )
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    run_live_env = os.getenv("AGORAGENTIC_RUN_LIVE", "").strip().lower()
    run_live = args.run_live or run_live_env in {"1", "true", "yes", "on"}
    api_key = os.getenv("AGORAGENTIC_API_KEY", "").strip()

    create_payload = {
        "name": args.name,
        "description": args.description,
        "category": args.category,
        "endpoint_url": args.endpoint_url,
        "price_per_unit": args.price,
        "tags": "seller,syrin,lifecycle",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        "output_schema": {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
        },
    }
    update_payload = {
        "description": args.updated_description,
        "price_per_unit": args.updated_price,
    }
    self_test_payload = {
        "test_input": {"text": args.test_text},
        "timeout_ms": 15000,
    }

    _print_json("Planned Create Payload", create_payload)
    if args.listing_id:
        _print_json("Target Existing Listing", {"listing_id": args.listing_id})
    _print_json("Planned Update Payload", update_payload)
    _print_json("Planned Self-Test Payload", self_test_payload)
    if args.header_value:
        _print_json(
            "Planned Verification Credential",
            {
                "cred_type": args.cred_type,
                "header_name": args.header_name,
                "header_value_provided": True,
                "notes": args.credential_notes,
            },
        )

    if not run_live:
        print(
            "\nPreview only. Pass --run-live or set AGORAGENTIC_RUN_LIVE=1 to create or "
            "manage the listing for real."
        )
        return

    if not api_key:
        raise RuntimeError("Set AGORAGENTIC_API_KEY before using --run-live.")

    tools = AgoragenticTools(api_key=api_key)
    listing_create = _get_tool(tools, "agoragentic_listing_create")
    listing_update = _get_tool(tools, "agoragentic_listing_update")
    listing_stats = _get_tool(tools, "agoragentic_listing_stats")
    listing_self_test = _get_tool(tools, "agoragentic_listing_self_test")
    credentials_set = _get_tool(tools, "agoragentic_verification_credentials_set")
    credentials_get = _get_tool(tools, "agoragentic_verification_credentials_get")
    listing_delete = _get_tool(tools, "agoragentic_listing_delete")

    target_listing_id = args.listing_id.strip()
    if not target_listing_id:
        created = listing_create(**create_payload)
        _print_json("Listing Create", created)
        target_listing_id = created.get("listing_id") or ""
        if not target_listing_id:
            return

    _print_json(
        "Listing Update",
        listing_update(target_listing_id, changes=update_payload),
    )
    _print_json("Listing Stats", listing_stats(target_listing_id))

    if args.header_value:
        _print_json(
            "Verification Credential Set",
            credentials_set(
                target_listing_id,
                cred_type=args.cred_type,
                header_name=args.header_name,
                header_value=args.header_value,
                notes=args.credential_notes,
            ),
        )
        _print_json(
            "Verification Credential Summary",
            credentials_get(target_listing_id),
        )

    _print_json(
        "Listing Self-Test",
        listing_self_test(
            target_listing_id,
            test_input=self_test_payload["test_input"],
            timeout_ms=self_test_payload["timeout_ms"],
        ),
    )

    if args.delete_after:
        _print_json("Listing Delete", listing_delete(target_listing_id))


if __name__ == "__main__":
    main()
