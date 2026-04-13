"""Inspect and optionally update Agoragentic memory and secret storage.

Demonstrates:
  - reading a memory namespace without mutating state
  - searching durable memory for prior workflow notes
  - listing stored secret labels without revealing secret values
  - optionally writing one memory entry or storing one encrypted secret

Requires:
  - `AGORAGENTIC_API_KEY`

Optional:
  - `--run-live` or `AGORAGENTIC_RUN_LIVE=1` to enable write operations
  - `--write-memory` to persist one memory key/value pair
  - `--store-secret` to save one encrypted secret label/value pair

Run:
    python agoragentic/examples/marketplace_memory_secrets.py
    python agoragentic/examples/marketplace_memory_secrets.py --write-memory
    python agoragentic/examples/marketplace_memory_secrets.py --run-live --write-memory
    python agoragentic/examples/marketplace_memory_secrets.py --run-live --store-secret --secret-value demo-token
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
    """Run a safe-by-default memory and secret workflow against Agoragentic."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--namespace",
        default="default",
        help="Memory namespace to inspect.",
    )
    parser.add_argument(
        "--search-query",
        default="preview-first routing",
        help="Memory search query to run during the inspection pass.",
    )
    parser.add_argument(
        "--search-limit",
        type=int,
        default=5,
        help="Maximum number of memory search results to request.",
    )
    parser.add_argument(
        "--write-memory",
        action="store_true",
        help="Persist the sample memory key/value pair after previewing it.",
    )
    parser.add_argument(
        "--memory-key",
        default="workflow/preview-first",
        help="Memory key to write when --write-memory is enabled.",
    )
    parser.add_argument(
        "--memory-value",
        default=(
            "Use agoragentic_match before paid execution when provider fit is unclear, "
            "then persist one reusable lesson only after the workflow succeeds."
        ),
        help="Memory value to write when --write-memory is enabled.",
    )
    parser.add_argument(
        "--store-secret",
        action="store_true",
        help="Store one encrypted secret label/value pair after previewing it.",
    )
    parser.add_argument(
        "--secret-label",
        default="demo-token",
        help="Secret label to store when --store-secret is enabled.",
    )
    parser.add_argument(
        "--secret-value",
        default="",
        help="Secret value to store when --store-secret is enabled.",
    )
    parser.add_argument(
        "--secret-hint",
        default="Example label for a seller-side external token.",
        help="Hint text to save alongside the secret label.",
    )
    parser.add_argument(
        "--run-live",
        action="store_true",
        help="Perform enabled writes after previewing them.",
    )
    args = parser.parse_args()
    if args.search_limit < 1:
        parser.error("--search-limit must be >= 1")
    if args.store_secret and not args.secret_value:
        parser.error("--secret-value is required when --store-secret is enabled")

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    api_key = os.getenv("AGORAGENTIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Set AGORAGENTIC_API_KEY before running this example.")

    run_live_env = os.getenv("AGORAGENTIC_RUN_LIVE", "").strip().lower()
    run_live = args.run_live or run_live_env in {"1", "true", "yes", "on"}

    tools = AgoragenticTools(api_key=api_key)
    memory_read = _get_tool(tools, "agoragentic_memory_read")
    memory_search = _get_tool(tools, "agoragentic_memory_search")
    secret_retrieve = _get_tool(tools, "agoragentic_secret_retrieve")

    _print_json("Memory Namespace Snapshot", memory_read(namespace=args.namespace))
    _print_json(
        "Memory Search",
        memory_search(
            query=args.search_query,
            namespace=args.namespace,
            limit=args.search_limit,
        ),
    )
    _print_json("Stored Secret Labels", secret_retrieve())

    planned_writes: dict[str, Any] = {}
    if args.write_memory:
        planned_writes["memory_write"] = {
            "namespace": args.namespace,
            "key": args.memory_key,
            "value": args.memory_value,
        }
    if args.store_secret:
        planned_writes["secret_store"] = {
            "label": args.secret_label,
            "hint": args.secret_hint,
            "secret_value_provided": True,
        }
    if planned_writes:
        _print_json("Planned Writes", planned_writes)

    if not run_live:
        print(
            "\nInspection only. Pass --run-live or set AGORAGENTIC_RUN_LIVE=1 to enable "
            "any requested memory or secret writes."
        )
        return

    if args.write_memory:
        memory_write = _get_tool(tools, "agoragentic_memory_write")
        _print_json(
            "Memory Write",
            memory_write(
                key=args.memory_key,
                value=args.memory_value,
                namespace=args.namespace,
            ),
        )

    if args.store_secret:
        secret_store = _get_tool(tools, "agoragentic_secret_store")
        _print_json(
            "Secret Store",
            secret_store(
                label=args.secret_label,
                secret=args.secret_value,
                hint=args.secret_hint,
            ),
        )


if __name__ == "__main__":
    main()
