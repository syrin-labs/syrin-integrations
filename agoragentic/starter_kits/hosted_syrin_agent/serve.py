"""Serve the hosted Syrin starter kit over HTTP."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agoragentic.starter_kits.hosted_syrin_agent.agent import build_agent
from agoragentic.starter_kits.hosted_syrin_agent.config import build_runtime_profile, build_startup_notes


def _load_env() -> None:
    """Load the starter-kit env file first, then fall back to the integration env file."""
    starter_env = Path(__file__).with_name(".env")
    integration_env = Path(__file__).resolve().parents[2] / ".env"
    if starter_env.exists():
        load_dotenv(starter_env, override=False)
    if integration_env.exists():
        load_dotenv(integration_env, override=False)


def main() -> None:
    """Serve the hosted starter agent with explicit startup notes."""
    _load_env()
    profile = build_runtime_profile()
    if profile.port <= 0:
        raise RuntimeError("HOSTED_SYRIN_PORT must be a positive integer.")

    print(f"Serving hosted Syrin agent at http://localhost:{profile.port}")
    if profile.enable_playground:
        print(f"Open http://localhost:{profile.port}/playground to inspect the agent.")
    for note in build_startup_notes(profile):
        print(f"- {note}")

    agent = build_agent(profile)
    agent.serve(
        port=profile.port,
        enable_playground=profile.enable_playground,
        debug=profile.debug,
    )


if __name__ == "__main__":
    main()
