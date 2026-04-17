"""Configuration helpers for the hosted Syrin starter kit."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

SMOKE_PATHS = ("/health", "/ready", "/describe")
_TRUE_VALUES = {"1", "true", "yes", "on"}
PREVIEW_PROMPT_TAG = "preview-only"
PREVIEW_PROMPT_INSTRUCTION = (
    "Do not make paid or mutating marketplace calls unless the operator explicitly "
    "enables AGORAGENTIC_RUN_LIVE=1."
)
LIVE_PROMPT_TAG = "live-enabled"
LIVE_PROMPT_INSTRUCTION = (
    "Paid or mutating marketplace calls are allowed only when the operator explicitly "
    "asks for them."
)


def _env_flag(value: str | None, default: bool = False) -> bool:
    """Parse a conventional truthy environment flag."""
    if value is None:
        return default
    return value.strip().lower() in _TRUE_VALUES


def _env_int(value: str | None, default: int) -> int:
    """Parse a positive integer environment variable with a safe default."""
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _env_float(value: str | None, default: float) -> float:
    """Parse a float environment variable with a safe default."""
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else 0.0


@dataclass(frozen=True)
class HostedStarterProfile:
    """Runtime profile for the hosted Syrin starter kit."""

    port: int
    live_enabled: bool
    enable_playground: bool
    debug: bool
    model_name: str
    max_budget_usd: float
    agoragentic_base_url: str
    smoke_paths: tuple[str, ...] = SMOKE_PATHS


def build_runtime_profile(env: Mapping[str, str] | None = None) -> HostedStarterProfile:
    """Build a runtime profile from environment variables."""
    source = os.environ if env is None else env
    return HostedStarterProfile(
        port=_env_int(source.get("HOSTED_SYRIN_PORT"), 8000),
        live_enabled=_env_flag(source.get("AGORAGENTIC_RUN_LIVE"), default=False),
        enable_playground=_env_flag(source.get("SYRIN_ENABLE_PLAYGROUND"), default=True),
        debug=_env_flag(source.get("SYRIN_DEBUG"), default=True),
        model_name=(source.get("SYRIN_MODEL_NAME") or "gpt-4o-mini").strip() or "gpt-4o-mini",
        max_budget_usd=_env_float(source.get("SYRIN_MAX_BUDGET_USD"), 1.0),
        agoragentic_base_url=(
            source.get("AGORAGENTIC_BASE_URL") or "https://agoragentic.com"
        ).rstrip("/"),
    )


def build_system_prompt(live_enabled: bool) -> str:
    """Return the system prompt used by the hosted agent."""
    mode_line = (
        f"Execution mode: {LIVE_PROMPT_TAG}. {LIVE_PROMPT_INSTRUCTION}"
        if live_enabled
        else f"Execution mode: {PREVIEW_PROMPT_TAG}. {PREVIEW_PROMPT_INSTRUCTION}"
    )
    return "\n".join(
        [
            "You are a hosted Agoragentic x Syrin agent.",
            mode_line,
            "Use agoragentic_match before agoragentic_execute when provider fit is unclear.",
            "Use agoragentic_execute for routed work instead of hard-coding provider IDs.",
            "Search memory before repeating prior work.",
            "Do not create listings, deploy relay functions, write secrets, or spend funds without an explicit operator request.",
            "When live mode is disabled, return a preview-oriented plan and explain what would be executed live later.",
        ]
    )


def build_startup_notes(
    profile: HostedStarterProfile,
    env: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Describe the current runtime state for operator visibility."""
    source = os.environ if env is None else env
    notes = [
        (
            "Mode: live-enabled. Keep requests scoped and explicit."
            if profile.live_enabled
            else "Mode: preview-only. Set AGORAGENTIC_RUN_LIVE=1 only after the smoke test passes."
        ),
        f"Agoragentic base URL: {profile.agoragentic_base_url}",
        f"Budget cap: ${profile.max_budget_usd:.2f}",
        "Health routes: " + ", ".join(profile.smoke_paths),
    ]
    if not (source.get("OPENAI_API_KEY") or "").strip():
        notes.append("OPENAI_API_KEY not set; the server will use Model.mock() for route inspection.")
    if not (source.get("AGORAGENTIC_API_KEY") or "").strip():
        notes.append("AGORAGENTIC_API_KEY not set; marketplace tool calls will fail until you provide one.")
    return tuple(notes)
