"""Smoke test the hosted Syrin starter kit routes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agoragentic.starter_kits.hosted_syrin_agent.config import SMOKE_PATHS


def build_smoke_targets(base_url: str) -> tuple[str, ...]:
    """Build absolute smoke-test URLs for the hosted agent."""
    base = base_url.rstrip("/")
    return tuple(f"{base}{path}" for path in SMOKE_PATHS)


def run_smoke(base_url: str, timeout: float) -> dict[str, Any]:
    """Run smoke requests against the standard Syrin health surfaces."""
    import requests

    results = []
    for url in build_smoke_targets(base_url):
        response = requests.get(url, timeout=timeout)
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text[:500]}
        results.append(
            {
                "url": url,
                "status_code": response.status_code,
                "ok": response.status_code == 200,
                "body": body,
            }
        )
    passed = all(item["ok"] for item in results)
    return {"passed": passed, "checks": results}


def main() -> None:
    """Execute the smoke test and exit non-zero on failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the served Syrin agent.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Per-request timeout in seconds.",
    )
    args = parser.parse_args()

    report = run_smoke(args.base_url, args.timeout)
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
