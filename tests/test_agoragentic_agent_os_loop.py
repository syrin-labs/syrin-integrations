"""Regression coverage for the Agent OS loop example helpers."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATH = ROOT / "agoragentic" / "examples" / "marketplace_agent_os_loop.py"


def _load_example_module():
    """Import the example module directly from its file path."""
    spec = importlib.util.spec_from_file_location("marketplace_agent_os_loop", EXAMPLE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


example = _load_example_module()


class AgentOSLoopExampleTests(unittest.TestCase):
    """Pure helper coverage for Conway-inspired Agent OS loop logic."""

    def test_classifies_sandbox_only_when_unfunded_and_not_graduated(self):
        """Unfunded agents still building Tumbler proof should stay sandbox-first."""
        tier = example.classify_survival_tier(
            account={"ledger": {"balance": 0}},
            tumbler={"lifecycle_stage": "building_sandbox_proof"},
            approvals={},
        )

        self.assertEqual(tier, "sandbox_only")

    def test_classifies_low_compute_from_small_balance(self):
        """Small production balances should force preview-only behavior."""
        tier = example.classify_survival_tier(
            account={"ledger": {"balance": "1.25"}},
            tumbler={"lifecycle_stage": "ready_for_production"},
            approvals={"pending": 0},
        )

        self.assertEqual(tier, "low_compute")

    def test_recommends_supervised_when_procurement_blocks(self):
        """Procurement approval pressure should override autonomous preview mode."""
        mode = example.recommend_operating_mode(
            survival_tier="normal",
            procurement={"status": "approval_required"},
            tasks={},
        )

        self.assertEqual(mode, "supervised")

    def test_execute_payload_uses_router_constraints(self):
        """The example should map its workflow budget to constraints.max_cost."""
        payload = example.build_execute_payload("Summarize this", 0.25)

        self.assertEqual(payload["task"], "Summarize this")
        self.assertEqual(payload["constraints"]["max_cost"], 0.25)
        self.assertEqual(payload["input"]["task"], "Summarize this")

    def test_non_negative_float_rejects_non_finite_values(self):
        """CLI budget parsing should reject NaN and Infinity."""
        with self.assertRaises(Exception):
            example.non_negative_float("nan")
        with self.assertRaises(Exception):
            example.non_negative_float("inf")

    def test_safe_json_marks_http_error_payloads(self):
        """HTTP error JSON should be explicit enough for downstream classification."""
        class FakeResponse:
            status_code = 500
            text = "server error"

            def json(self):
                return {"message": "server error"}

        result = example._safe_json(FakeResponse())

        self.assertEqual(result["status_code"], 500)
        self.assertEqual(result["error"], "http_500")

    def test_prompt_preserves_preview_first_contract(self):
        """The prompt should keep spend and mutation gates explicit."""
        snapshot = example.ControlPlaneSnapshot(
            account={"ledger": {"balance": 3.0}},
            jobs={},
            procurement={},
            approvals={},
            learning={},
            reconciliation={},
            identity={},
            tumbler={},
            tasks={},
            survival_tier="normal",
            recommended_mode="autonomous_preview",
        )

        prompt = example.build_agent_os_prompt(
            snapshot=snapshot,
            task="Find revenue-positive work.",
            max_cost=0.25,
            live_enabled=False,
        )

        self.assertIn("Prefer agoragentic_match before any paid action.", prompt)
        self.assertIn("Mode: preview-only", prompt)
        self.assertIn("Max spend for this turn: $0.25", prompt)

    def test_prompt_reflects_live_mode_enabled(self):
        """Live-enabled prompts should make the execution mode explicit."""
        snapshot = example.ControlPlaneSnapshot(
            account={"ledger": {"balance": 3.0}},
            jobs={},
            procurement={},
            approvals={},
            learning={},
            reconciliation={},
            identity={},
            tumbler={},
            tasks={},
            survival_tier="normal",
            recommended_mode="autonomous_preview",
        )

        prompt = example.build_agent_os_prompt(
            snapshot=snapshot,
            task="Find revenue-positive work.",
            max_cost=0.25,
            live_enabled=True,
        )

        self.assertIn("Mode: live-enabled", prompt)

    def test_handles_transport_request_failed(self):
        """AgentOSClient should surface transport failures as structured errors."""
        requests_stub = types.ModuleType("requests")

        class RequestException(Exception):
            """Minimal requests exception stand-in."""

        def failing_get(*_args, **_kwargs):
            raise RequestException("network down")

        requests_stub.exceptions = types.SimpleNamespace(RequestException=RequestException)
        requests_stub.get = failing_get
        requests_stub.post = failing_get

        with patch.dict(sys.modules, {"requests": requests_stub}):
            result = example.AgentOSClient(api_key="test-key").get_json("/api/commerce/account")

        self.assertEqual(result["error"], "request_failed")
        self.assertEqual(result["path"], "/api/commerce/account")
        self.assertIn("network down", result["message"])


if __name__ == "__main__":
    unittest.main()
