import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def _import_integration():
    """Import the integration without leaking a requests stub across tests."""
    if "requests" in sys.modules:
        return importlib.import_module("agoragentic.agoragentic_syrin")

    requests_stub = types.ModuleType("requests")

    class Response:
        """Minimal requests.Response stand-in for import-time type references."""

    def _not_patched(*args, **kwargs):
        raise AssertionError("requests stub should be patched in tests")

    requests_stub.Response = Response
    requests_stub.get = _not_patched
    requests_stub.post = _not_patched
    with patch.dict(sys.modules, {"requests": requests_stub}):
        return importlib.import_module("agoragentic.agoragentic_syrin")


integration = _import_integration()


class FakeResponse:
    """Small HTTP response double for adapter unit tests."""

    def __init__(
        self,
        status_code=200,
        json_data=None,
        json_error=None,
        text="",
        reason="OK",
    ):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self._json_error = json_error
        self.text = text
        self.reason = reason

    def json(self):
        """Return the configured JSON payload or raise the configured JSON error."""
        if self._json_error is not None:
            raise self._json_error
        return self._json_data


class AgoragenticIntegrationTests(unittest.TestCase):
    """Regression coverage for the Agoragentic Syrin adapter helpers and wrappers."""

    def test_safe_json_handles_invalid_json(self):
        """_safe_json should return a structured error payload on JSON decode failure."""
        response = FakeResponse(
            status_code=502,
            json_error=ValueError("boom"),
            text="upstream gateway failure",
            reason="Bad Gateway",
        )

        result = integration._safe_json(response)

        self.assertEqual(result["error"], "invalid_json")
        self.assertEqual(result["status_code"], 502)
        self.assertIn("upstream gateway failure", result["message"])

    def test_safe_limit_clamps_and_defaults(self):
        """_safe_limit should clamp large values and default invalid values."""
        self.assertEqual(integration._safe_limit(99), 50)
        self.assertEqual(integration._safe_limit(-3), 1)
        self.assertEqual(integration._safe_limit("bad"), 5)

    @patch.object(integration.requests, "get")
    def test_match_ignores_bad_provider_shapes(self, mock_get):
        """agoragentic_match should skip malformed providers without crashing."""
        mock_get.return_value = FakeResponse(
            json_data={
                "task": "inspect",
                "matches": 2,
                "eligible": 2,
                "providers": [
                    {
                        "name": "alpha",
                        "capability_name": "summary",
                        "price": 0.2,
                        "score": "bad-shape",
                        "hosting": "bad-shape",
                        "eligible": True,
                    },
                    "skip-me",
                    {
                        "name": "beta",
                        "capability_name": "analysis",
                        "price": 0.3,
                        "score": {"composite": 0.91},
                        "hosting": {"model": "seller-hosted"},
                        "eligible": True,
                    },
                ],
            }
        )

        result = integration.agoragentic_match("inspect", _api_key="test-key")

        self.assertEqual(result["matches"], 2)
        self.assertEqual(len(result["top_providers"]), 2)
        self.assertIsNone(result["top_providers"][0]["score"])
        self.assertIsNone(result["top_providers"][0]["hosting"])
        self.assertEqual(result["top_providers"][1]["score"], 0.91)
        self.assertEqual(result["top_providers"][1]["hosting"], "seller-hosted")

    @patch.object(integration.requests, "get")
    def test_memory_search_clamps_limit_before_request(self, mock_get):
        """agoragentic_memory_search should clamp limit before making the request."""
        mock_get.return_value = FakeResponse(json_data={"output": {"items": []}})

        integration.agoragentic_memory_search("routing", limit=999, _api_key="test-key")

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["limit"], 50)

    @patch.object(integration.requests, "get")
    def test_learning_queue_defaults_invalid_limit(self, mock_get):
        """agoragentic_learning_queue should default invalid limits to the safe default."""
        mock_get.return_value = FakeResponse(json_data={"generated_at": "now", "total": 0, "items": []})

        result = integration.agoragentic_learning_queue(limit="bad", _api_key="test-key")

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["limit"], 5)
        self.assertEqual(result["total"], 0)

    @patch.object(integration.requests, "post")
    def test_toolset_binds_api_key_to_wrapped_calls(self, mock_post):
        """AgoragenticTools should bind the configured API key into wrapped calls."""
        mock_post.return_value = FakeResponse(
            json_data={
                "status": "completed",
                "provider": {"name": "alpha", "capability_name": "summary"},
                "output": {"text": "done"},
                "cost": 0.25,
                "invocation_id": "inv_123",
                "commerce": {"settlement_status": "settled", "payment_network": "base"},
            }
        )

        tools = integration.AgoragenticTools(api_key="bound-key")
        execute_tool = next(
            tool for tool in tools if tool.__name__ == "agoragentic_execute"
        )
        result = execute_tool("Summarize this")

        self.assertEqual(len(tools), 16)
        self.assertEqual(result["provider"], "alpha")
        headers = mock_post.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer bound-key")

    def test_get_all_tools_returns_full_toolset(self):
        """get_all_tools should expose the full 16-tool Agoragentic surface."""
        self.assertEqual(len(integration.get_all_tools(api_key="bound-key")), 16)


if __name__ == "__main__":
    unittest.main()
