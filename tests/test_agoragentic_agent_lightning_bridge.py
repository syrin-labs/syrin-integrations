"""Regression coverage for the Agent Lightning bridge helpers."""

import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class AgentLightningBridgeTests(unittest.TestCase):
    """Pure helper coverage for Agent Lightning bridge exports and prompts."""

    @classmethod
    def setUpClass(cls):
        """Load the bridge modules once for the test class."""
        cls.config = importlib.import_module("agoragentic.starter_kits.hosted_syrin_agent.config")
        cls.tracing = importlib.import_module("agoragentic.starter_kits.hosted_syrin_agent.tracing")
        cls.prompt = importlib.import_module("agoragentic.starter_kits.hosted_syrin_agent.agent_os_prompt")
        cls.smoke = importlib.import_module("agoragentic.starter_kits.hosted_syrin_agent.smoke_test")

    def test_default_spans_keep_preview_blocked(self):
        """Preview packets should keep the execution gate blocked."""
        spans = self.tracing.build_default_spans(
            task="Preview a route.",
            max_cost_usd=0.25,
            preview_only=True,
            matched_providers=2,
        )

        span_map = {span.name: span for span in spans}
        self.assertEqual(span_map["hosted_syrin_rollout"].status, "preview")
        self.assertEqual(span_map["execution.gate"].status, "blocked")
        self.assertEqual(span_map["routing.match"].attributes["matched_providers"], 2)
        self.assertTrue(all(span.end_ms > span.start_ms for span in spans))
        self.assertEqual(
            [span.start_ms for span in spans],
            sorted(span.start_ms for span in spans),
        )

    def test_reward_signals_respect_budget_and_safety_failures(self):
        """Reward shaping should penalize overspend, approval debt, and sandbox failure."""
        rewards = self.tracing.build_reward_signals(
            preview_only=False,
            max_cost_usd=1.0,
            actual_cost_usd=1.5,
            matched_providers=1,
            sandbox_passed=False,
            approval_required=True,
            task_completed=False,
        )

        reward_map = {reward.name: reward.value for reward in rewards}
        self.assertEqual(reward_map["budget_discipline"], 0.0)
        self.assertEqual(reward_map["sandbox_safety"], 0.0)
        self.assertEqual(reward_map["approval_readiness"], 0.0)

    def test_export_packet_includes_profile_metadata_and_summary(self):
        """Exports should include summary counts and starter-kit metadata."""
        profile = self.config.build_runtime_profile({"SYRIN_MAX_BUDGET_USD": "0.5"})
        spans = self.tracing.build_default_spans(
            task="Preview a route.",
            max_cost_usd=profile.max_budget_usd,
            preview_only=True,
        )
        rewards = self.tracing.build_reward_signals(
            preview_only=True,
            max_cost_usd=profile.max_budget_usd,
            matched_providers=2,
        )
        export = self.tracing.build_agent_lightning_export(
            task="Preview a route.",
            profile=profile,
            spans=spans,
            rewards=rewards,
            preview_only=True,
        )

        data = export.as_dict()
        self.assertEqual(data["metadata"]["max_budget_usd"], 0.5)
        self.assertEqual(data["summary"]["span_count"], len(data["spans"]))
        self.assertEqual(data["summary"]["reward_count"], len(data["rewards"]))

    def test_agent_os_prompt_preserves_runtime_training_boundary(self):
        """The prompt should keep training out of the live request path."""
        prompt = self.prompt.build_agent_os_implementation_prompt()

        self.assertIn("Agent Lightning-compatible", prompt)
        self.assertIn("preview-first", prompt)
        self.assertIn("do not add agentlightning as a hard runtime dependency", prompt)
        self.assertIn("agoragentic/starter_kits/hosted_syrin_agent/tracing.py", prompt)

    def test_smoke_report_captures_transport_failures(self):
        """Smoke tests should return a structured failed check on request errors."""
        requests_stub = types.ModuleType("requests")

        class RequestException(Exception):
            """Minimal requests exception stand-in."""

        def failing_get(*_args, **_kwargs):
            raise RequestException("connection refused")

        requests_stub.RequestException = RequestException
        requests_stub.get = failing_get

        with patch.dict(sys.modules, {"requests": requests_stub}):
            report = self.smoke.run_smoke("http://localhost:8000", 1.0)

        self.assertFalse(report["passed"])
        self.assertIsNone(report["checks"][0]["status_code"])
        self.assertIn("RequestException: connection refused", report["checks"][0]["body"]["error"])


if __name__ == "__main__":
    unittest.main()
