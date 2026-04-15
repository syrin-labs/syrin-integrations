"""Syrin Agent OS loop example for Agoragentic control-plane workflows.

This example adapts public Conway Automaton patterns into the Agoragentic/Syrin
integration without copying Conway runtime code:

- heartbeat-style control-plane polling
- survival-tier classification from account and sandbox state
- think/act/observe prompts for a Syrin agent
- explicit spend, mutation, and deployment gates

Safe default:
    The script reads Agent OS control-plane endpoints and prints a plan. It does
    not spend, execute paid work, create jobs, or mutate marketplace state unless
    you pass --execute and enable live mode with --run-live or
    AGORAGENTIC_RUN_LIVE=1.

Environment:
    AGORAGENTIC_API_KEY=...
    OPENAI_API_KEY=...              # only required for --agent-run
    AGORAGENTIC_BASE_URL=...        # optional
    AGORAGENTIC_AGENT_OS_TASK=...   # optional default task

Run:
    python agoragentic/examples/marketplace_agent_os_loop.py
    python agoragentic/examples/marketplace_agent_os_loop.py --match
    python agoragentic/examples/marketplace_agent_os_loop.py --agent-run
    AGORAGENTIC_RUN_LIVE=1 python agoragentic/examples/marketplace_agent_os_loop.py \
      --execute --run-live
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args: Any, **_kwargs: Any) -> bool:
        """Allow offline tests to import this example without python-dotenv."""
        return False

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

DEFAULT_BASE_URL = "https://agoragentic.com"
DEFAULT_TASK = (
    "Inspect marketplace operating state, identify one safe revenue-positive "
    "next action, preview provider fit, and save a reusable lesson only if a "
    "real execution produced new evidence."
)

CONTROL_PLANE_ENDPOINTS = {
    "account": "/api/commerce/account",
    "jobs": "/api/jobs/summary",
    "procurement": "/api/commerce/procurement",
    "approvals": "/api/approvals",
    "learning": "/api/commerce/learning",
    "reconciliation": "/api/commerce/reconciliation",
    "identity": "/api/commerce/identity",
    "tumbler": "/api/tumbler/graduation",
    "tasks": "/api/agents/me/tasks",
}


@dataclass(frozen=True)
class ControlPlaneSnapshot:
    """Compact Agent OS state that can be injected into a Syrin prompt."""

    account: dict[str, Any]
    jobs: dict[str, Any]
    procurement: dict[str, Any]
    approvals: dict[str, Any]
    learning: dict[str, Any]
    reconciliation: dict[str, Any]
    identity: dict[str, Any]
    tumbler: dict[str, Any]
    tasks: dict[str, Any]
    survival_tier: str
    recommended_mode: str

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable view for prompt construction and tests."""
        return {
            "account": self.account,
            "jobs": self.jobs,
            "procurement": self.procurement,
            "approvals": self.approvals,
            "learning": self.learning,
            "reconciliation": self.reconciliation,
            "identity": self.identity,
            "tumbler": self.tumbler,
            "tasks": self.tasks,
            "survival_tier": self.survival_tier,
            "recommended_mode": self.recommended_mode,
        }


class AgentOSClient:
    """Small requests-based client for Agoragentic Agent OS examples."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 20.0,
    ):
        """Create a client with a bearer token and normalized base URL."""
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET one Agent OS endpoint and return structured JSON or an error payload."""
        import requests

        try:
            response = requests.get(
                f"{self.base_url}{path}",
                headers=self._headers(),
                params=params or {},
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as exc:
            return request_failed_payload(path, exc)
        return _safe_json(response)

    def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST one Agent OS endpoint and return structured JSON or an error payload."""
        import requests

        try:
            response = requests.post(
                f"{self.base_url}{path}",
                headers=self._headers(),
                json=payload,
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as exc:
            return request_failed_payload(path, exc)
        return _safe_json(response)

    def snapshot(self) -> ControlPlaneSnapshot:
        """Read the Agent OS control plane and derive a conservative operating mode."""
        raw = {
            label: self.get_json(path, {"limit": 10} if label in {"approvals", "tasks"} else None)
            for label, path in CONTROL_PLANE_ENDPOINTS.items()
        }
        survival_tier = classify_survival_tier(raw["account"], raw["tumbler"], raw["approvals"])
        recommended_mode = recommend_operating_mode(survival_tier, raw["procurement"], raw["tasks"])
        return ControlPlaneSnapshot(
            account=raw["account"],
            jobs=raw["jobs"],
            procurement=raw["procurement"],
            approvals=raw["approvals"],
            learning=raw["learning"],
            reconciliation=raw["reconciliation"],
            identity=raw["identity"],
            tumbler=raw["tumbler"],
            tasks=raw["tasks"],
            survival_tier=survival_tier,
            recommended_mode=recommended_mode,
        )

    def match(self, task: str, max_cost: float) -> dict[str, Any]:
        """Preview routed provider fit without spending funds."""
        return self.get_json(
            "/api/execute/match",
            {
                "task": task,
                "max_cost": max_cost,
            },
        )

    def execute(self, task: str, max_cost: float) -> dict[str, Any]:
        """Run a routed execute call. Callers must apply live-mode gates first."""
        return self.post_json(
            "/api/execute",
            build_execute_payload(task=task, max_cost=max_cost),
        )

    def _headers(self) -> dict[str, str]:
        """Build auth headers for JSON requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }


def _safe_json(response: Any) -> dict[str, Any]:
    """Return JSON when possible and preserve HTTP context on parse failures."""
    try:
        payload = response.json()
    except ValueError:
        return {
            "error": "invalid_json",
            "status_code": getattr(response, "status_code", None),
            "message": getattr(response, "text", "")[:1000],
        }

    if isinstance(payload, dict):
        if getattr(response, "status_code", 200) >= 400:
            payload.setdefault("status_code", getattr(response, "status_code", None))
        return payload
    return {"value": payload, "status_code": getattr(response, "status_code", None)}


def request_failed_payload(path: str, exc: Exception) -> dict[str, Any]:
    """Return a structured payload for transport-level request failures."""
    return {
        "ok": False,
        "error": "request_failed",
        "message": str(exc),
        "status_code": None,
        "path": path,
    }


def classify_survival_tier(
    account: dict[str, Any],
    tumbler: dict[str, Any],
    approvals: dict[str, Any],
) -> str:
    """Map Agent OS wallet/sandbox state into a Conway-style survival tier."""
    balance = extract_usdc_balance(account)
    lifecycle_stage = str(
        tumbler.get("lifecycle_stage")
        or tumbler.get("stage")
        or tumbler.get("status")
        or ""
    )
    pending_approvals = extract_count(approvals, "pending", "pending_count", "total_pending")

    if balance <= 0 and lifecycle_stage in {
        "sandbox_join_required",
        "building_sandbox_proof",
        "ready_to_graduate",
    }:
        return "sandbox_only"
    if balance <= 0.25 or pending_approvals >= 10:
        return "critical"
    if balance < 2.00:
        return "low_compute"
    return "normal"


def recommend_operating_mode(
    survival_tier: str,
    procurement: dict[str, Any],
    tasks: dict[str, Any],
) -> str:
    """Choose the safest next operating mode from state pressure signals."""
    open_tasks = extract_count(tasks, "total", "open", "count")
    procurement_status = str(procurement.get("status") or procurement.get("state") or "")

    if survival_tier == "sandbox_only":
        return "tumbler_first"
    if survival_tier == "critical":
        return "conserve_and_seek_revenue"
    if survival_tier == "low_compute":
        return "preview_only"
    if procurement_status in {"approval_required", "blocked"}:
        return "supervised"
    if open_tasks > 0:
        return "work_queue"
    return "autonomous_preview"


def extract_usdc_balance(account: dict[str, Any]) -> float:
    """Extract a best-effort USDC balance from several known Agent OS shapes."""
    candidates = [
        account.get("balance_usdc"),
        account.get("ledger_balance"),
        account.get("available_usdc"),
        _nested(account, "ledger", "balance"),
        _nested(account, "ledger", "available"),
        _nested(account, "wallet", "balance_usdc"),
        _nested(account, "wallet", "usdc"),
        _nested(account, "balances", "usdc"),
        _nested(account, "summary", "balance_usdc"),
    ]
    for candidate in candidates:
        value = parse_float(candidate)
        if value is not None:
            return value
    return 0.0


def extract_count(payload: dict[str, Any], *keys: str) -> int:
    """Extract the first integer-like count found at top level or under summary."""
    for key in keys:
        value = parse_int(payload.get(key))
        if value is not None:
            return value
        summary_value = parse_int(_nested(payload, "summary", key))
        if summary_value is not None:
            return summary_value
    items = payload.get("items")
    if isinstance(items, list):
        return len(items)
    tasks = payload.get("tasks")
    if isinstance(tasks, list):
        return len(tasks)
    approvals = payload.get("approvals")
    if isinstance(approvals, list):
        return len(approvals)
    return 0


def parse_float(value: Any) -> float | None:
    """Parse numeric strings and numbers into floats."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace("$", "").replace(",", "").strip())
        except ValueError:
            return None
    return None


def parse_int(value: Any) -> int | None:
    """Parse integer-like strings and numbers."""
    parsed = parse_float(value)
    if parsed is None:
        return None
    return max(0, int(parsed))


def non_negative_float(value: str) -> float:
    """Parse a non-negative CLI float."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def build_execute_payload(task: str, max_cost: float) -> dict[str, Any]:
    """Build the canonical router-first execute payload."""
    return {
        "task": task,
        "input": {
            "task": task,
        },
        "constraints": {
            "max_cost": max(0.01, float(max_cost)),
        },
    }


def build_agent_os_prompt(
    snapshot: ControlPlaneSnapshot,
    task: str,
    max_cost: float,
    live_enabled: bool,
) -> str:
    """Create a Syrin prompt that makes the Agent OS state actionable."""
    compact_state = compact_snapshot(snapshot)
    mode = "live-enabled" if live_enabled else "preview-only"
    return "\n".join(
        [
            "You are a Syrin agent operating through Agoragentic Agent OS.",
            "",
            "Operating contract:",
            "- Think in terms of Agent OS state, then act through Agoragentic tools.",
            "- Prefer agoragentic_match before any paid action.",
            "- Prefer agoragentic_execute over hard-coded provider IDs.",
            "- Use Tumbler/sandbox guidance before production spend when the state says so.",
            "- If approvals are pending or procurement is blocked, explain the gate "
            "instead of bypassing it.",
            "- Do not mutate listings, deploy code, or store secrets unless explicitly requested.",
            "- Save learning notes only after a real result produced reusable evidence.",
            "",
            f"Mode: {mode}",
            f"Max spend for this turn: ${max_cost:.2f}",
            f"Survival tier: {snapshot.survival_tier}",
            f"Recommended operating mode: {snapshot.recommended_mode}",
            "",
            "Control-plane snapshot:",
            json.dumps(compact_state, indent=2, sort_keys=True),
            "",
            "Task:",
            task,
        ]
    )


def compact_snapshot(snapshot: ControlPlaneSnapshot) -> dict[str, Any]:
    """Keep prompt state compact enough for practical Syrin runs."""
    data = snapshot.as_dict()
    return {
        "survival_tier": data["survival_tier"],
        "recommended_mode": data["recommended_mode"],
        "balance_usdc": extract_usdc_balance(snapshot.account),
        "jobs": compact_keys(
            snapshot.jobs,
            "active",
            "paused",
            "failing",
            "disabled",
            "next_run_at",
        ),
        "procurement": compact_keys(snapshot.procurement, "status", "state", "recommendations"),
        "approvals": compact_keys(snapshot.approvals, "pending", "pending_count", "total", "items"),
        "learning": compact_keys(snapshot.learning, "total", "items", "recommendations"),
        "reconciliation": compact_keys(
            snapshot.reconciliation,
            "total_spend",
            "success_rate",
            "receipts",
        ),
        "identity": compact_keys(
            snapshot.identity,
            "agent_id",
            "status",
            "primary_buying_identity",
        ),
        "tumbler": compact_keys(snapshot.tumbler, "lifecycle_stage", "status", "recommendations"),
        "tasks": compact_keys(snapshot.tasks, "total", "items", "tasks"),
    }


def compact_keys(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    """Copy selected keys and trim long lists for prompt use."""
    output: dict[str, Any] = {}
    for key in keys:
        if key not in payload:
            continue
        value = payload[key]
        if isinstance(value, list):
            output[key] = value[:5]
        else:
            output[key] = value
    if not output and "error" in payload:
        output["error"] = payload.get("error")
        output["message"] = payload.get("message")
    return output


def live_mode_enabled(args: argparse.Namespace) -> bool:
    """Return true only when CLI or environment explicitly enables live mode."""
    return bool(args.run_live or os.getenv("AGORAGENTIC_RUN_LIVE") == "1")


def run_syrin_agent(prompt: str, api_key: str, max_cost: float) -> str:
    """Run the constructed prompt through Syrin when OPENAI_API_KEY is configured."""
    from agoragentic.agoragentic_syrin import AgoragenticTools
    from syrin import Agent, Budget, Model
    from syrin.enums import ExceedPolicy

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_key:
        raise RuntimeError("Set OPENAI_API_KEY before using --agent-run.")

    agent = Agent(
        model=Model.OpenAI("gpt-4o-mini", api_key=openai_key),
        budget=Budget(max_cost=max_cost, exceed_policy=ExceedPolicy.STOP),
        system_prompt=(
            "Operate as an Agent OS control-plane agent with strict "
            "preview-first spending gates."
        ),
        tools=AgoragenticTools(api_key=api_key),
    )
    result = agent.run(prompt)
    return getattr(result, "content", str(result))


def _nested(payload: dict[str, Any], *path: str) -> Any:
    """Safely read a nested dictionary path."""
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI arguments for the example."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "task",
        nargs="?",
        default=os.getenv("AGORAGENTIC_AGENT_OS_TASK", DEFAULT_TASK),
        help="Agent OS task to plan or execute.",
    )
    parser.add_argument(
        "--max-cost",
        type=non_negative_float,
        default=0.25,
        help="Maximum routed spend for execute.",
    )
    parser.add_argument(
        "--match",
        action="store_true",
        help="Preview routed providers with /api/execute/match.",
    )
    parser.add_argument(
        "--agent-run",
        action="store_true",
        help="Run the Agent OS prompt through Syrin.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the task through /api/execute.",
    )
    parser.add_argument(
        "--run-live",
        action="store_true",
        help="Allow live paid execution for --execute.",
    )
    return parser


def main() -> None:
    """Run the Agent OS loop example."""
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    args = _build_parser().parse_args()

    api_key = os.getenv("AGORAGENTIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Set AGORAGENTIC_API_KEY before reading Agent OS control-plane endpoints."
        )

    client = AgentOSClient(
        api_key=api_key,
        base_url=os.getenv("AGORAGENTIC_BASE_URL", DEFAULT_BASE_URL),
    )
    live_enabled = live_mode_enabled(args)
    snapshot = client.snapshot()
    prompt = build_agent_os_prompt(
        snapshot=snapshot,
        task=args.task,
        max_cost=args.max_cost,
        live_enabled=live_enabled,
    )

    print("=== Agent OS Snapshot ===")
    print(json.dumps(compact_snapshot(snapshot), indent=2, sort_keys=True))

    print("\n=== Syrin Prompt ===")
    print(prompt)

    if args.match:
        print("\n=== Provider Match Preview ===")
        print(json.dumps(client.match(args.task, args.max_cost), indent=2, sort_keys=True))

    if args.agent_run:
        print("\n=== Syrin Agent Output ===")
        print(run_syrin_agent(prompt, api_key=api_key, max_cost=args.max_cost))

    if args.execute:
        if not live_enabled:
            print(
                "\n--execute was requested, but live mode is disabled. "
                "Rerun with --run-live or AGORAGENTIC_RUN_LIVE=1."
            )
            return
        print("\n=== Live Execute Result ===")
        print(json.dumps(client.execute(args.task, args.max_cost), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
