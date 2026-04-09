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
    """Import the integration without requiring requests at test import time."""
    if "requests" in sys.modules:
        return importlib.import_module("agoragentic.agoragentic_syrin")

    requests_stub = types.ModuleType("requests")

    class Response:
        """Minimal requests.Response stand-in for type references."""

    def _not_patched(*args, **kwargs):
        raise AssertionError("requests stub should be patched in tests")

    requests_stub.Response = Response
    requests_stub.get = _not_patched
    requests_stub.post = _not_patched
    with patch.dict(sys.modules, {"requests": requests_stub}):
        return importlib.import_module("agoragentic.agoragentic_syrin")


integration = _import_integration()


class FakeResponse:
    """Small HTTP response double for adapter tests."""

    def __init__(self, status_code=200, json_data=None, text="", reason="OK"):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.text = text
        self.reason = reason

    def json(self):
        """Return the configured JSON payload."""
        return self._json_data


class AgoragenticRelayTests(unittest.TestCase):
    """Regression coverage for relay-hosting helpers and wrappers."""

    def test_normalize_tags_handles_lists_strings_and_other_inputs(self):
        """_normalize_tags should return only trimmed, non-empty string tags."""
        self.assertEqual(
            integration._normalize_tags([" alpha ", "", "beta", 3]),
            ["alpha", "beta", "3"],
        )
        self.assertEqual(integration._normalize_tags(" alpha, beta ,, gamma "), ["alpha", "beta", "gamma"])
        self.assertEqual(integration._normalize_tags(None), [])

    @patch.object(integration.requests, "post")
    def test_relay_deploy_normalizes_payload(self, mock_post):
        """agoragentic_relay_deploy should normalize tags and default schemas."""
        mock_post.return_value = FakeResponse(
            status_code=201,
            json_data={
                "status": "deployed",
                "id": "relay_123",
                "relay_url": "https://agoragentic.com/api/relay/relay_123/invoke",
                "capability_id": "cap_123",
                "source_hash": "sha256:abc",
                "hosting": {"model": "relay-hosted"},
                "platform_hosting": True,
                "listing": {"status": "draft"},
                "next_steps": ["test", "list"],
            },
        )

        result = integration.agoragentic_relay_deploy(
            name="Echo tool",
            description="Echo text back to the caller.",
            source_code="exports.handler = async ({ input }) => input;",
            tags="preview-first, seller-tools, relay ",
            _api_key="test-key",
        )

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["tags"], ["preview-first", "seller-tools", "relay"])
        self.assertEqual(payload["input_schema"], {})
        self.assertEqual(payload["output_schema"], {})
        self.assertEqual(result["relay_function_id"], "relay_123")
        self.assertEqual(result["hosting"]["model"], "relay-hosted")

    @patch.object(integration.requests, "get")
    def test_relay_list_shapes_stats(self, mock_get):
        """agoragentic_relay_list should return a normalized list of seller functions."""
        mock_get.return_value = FakeResponse(
            json_data={
                "count": 1,
                "limit": 20,
                "hosting": {"model": "relay-hosted"},
                "platform_hosting": True,
                "functions": [
                    {
                        "id": "relay_123",
                        "name": "Echo tool",
                        "status": "active",
                        "version": 3,
                        "relay_url": "https://agoragentic.com/api/relay/relay_123/invoke",
                        "capability_id": "cap_123",
                        "stats": {"total_executions": 12, "avg_execution_ms": 44},
                    }
                ],
            }
        )

        result = integration.agoragentic_relay_list(_api_key="test-key")

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["functions"][0]["name"], "Echo tool")
        self.assertEqual(result["functions"][0]["total_executions"], 12)
        self.assertEqual(result["functions"][0]["avg_execution_ms"], 44)

    @patch.object(integration.requests, "post")
    def test_relay_test_normalizes_input_and_output(self, mock_post):
        """agoragentic_relay_test should normalize input and shape the function metadata."""
        mock_post.return_value = FakeResponse(
            json_data={
                "success": True,
                "result": {"text": "hello"},
                "error": None,
                "execution_ms": 31,
                "function": {"id": "relay_123", "name": "Echo tool", "version": 2},
                "hosting": {"model": "relay-hosted"},
                "platform_hosting": True,
            }
        )

        result = integration.agoragentic_relay_test(
            "relay_123",
            input_data=None,
            _api_key="test-key",
        )

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["input"], {})
        self.assertTrue(result["success"])
        self.assertEqual(result["relay_function"]["name"], "Echo tool")
        self.assertEqual(result["execution_ms"], 31)

    def test_toolset_includes_relay_tools(self):
        """AgoragenticTools should expose the relay-hosting tool surface."""
        tools = integration.AgoragenticTools(api_key="bound-key")
        tool_names = [tool.__name__ for tool in tools]

        self.assertEqual(len(tools), 19)
        self.assertIn("agoragentic_relay_deploy", tool_names)
        self.assertIn("agoragentic_relay_list", tool_names)
        self.assertIn("agoragentic_relay_test", tool_names)


if __name__ == "__main__":
    unittest.main()
