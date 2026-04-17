"""Hosted Agoragentic x Syrin agent factory."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agoragentic.agoragentic_syrin import AgoragenticTools
from agoragentic.starter_kits.hosted_syrin_agent.config import HostedStarterProfile, build_system_prompt


def _build_model(profile: HostedStarterProfile):
    """Create a real tool-calling model when configured, otherwise a mock model."""
    from syrin import Model

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_key:
        return Model.OpenAI(profile.model_name, api_key=openai_key)
    return Model.mock(latency_min=0, latency_max=0)


def build_agent(profile: HostedStarterProfile):
    """Create the hosted starter agent using the current runtime profile."""
    from syrin import Agent, Budget
    from syrin.enums import ExceedPolicy

    return Agent(
        model=_build_model(profile),
        budget=Budget(max_cost=profile.max_budget_usd, exceed_policy=ExceedPolicy.STOP),
        system_prompt=build_system_prompt(profile.live_enabled),
        tools=AgoragenticTools(api_key=os.getenv("AGORAGENTIC_API_KEY", "")),
    )
