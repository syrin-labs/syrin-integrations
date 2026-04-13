"""Regression coverage for seller listing management and browse helpers."""

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
    """Import the integration with a complete requests stub for management tests."""
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
    requests_stub.patch = _not_patched
    requests_stub.put = _not_patched
    requests_stub.delete = _not_patched
    with patch.dict(sys.modules, {"requests": requests_stub}):
        return importlib.import_module("agoragentic.agoragentic_syrin")


integration = _import_integration()


class FakeResponse:
    """Small HTTP response double for management wrapper tests."""

    def __init__(self, status_code=200, json_data=None, text="", reason="OK"):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.text = text
        self.reason = reason

    def json(self):
        """Return the configured JSON payload."""
        return self._json_data


class AgoragenticMarketplaceManagementTests(unittest.TestCase):
    """Regression coverage for listing management, browse, and seller verification wrappers."""

    @patch.object(integration.requests, "get")
    def test_search_supports_seller_filter_and_clamped_limit(self, mock_get):
        """agoragentic_search should pass seller and a clamped limit to browse."""
        mock_get.return_value = FakeResponse(json_data={"capabilities": [], "has_more": False})

        integration.agoragentic_search(
            query="summarize",
            seller="agent://demo-seller",
            limit=999,
        )

        params = mock_get.call_args.kwargs["params"]
        self.assertEqual(params["search"], "summarize")
        self.assertEqual(params["seller"], "agent://demo-seller")
        self.assertEqual(params["limit"], 50)

    @patch.object(integration.requests, "post")
    def test_listing_create_shapes_payload_and_result(self, mock_post):
        """agoragentic_listing_create should normalize tags and key response fields."""
        mock_post.return_value = FakeResponse(
            status_code=201,
            json_data={
                "id": "cap_123",
                "slug": "seller-listing",
                "review_status": "pending",
                "message": "Capability published. Review in progress.",
                "_links": {"detail": "/api/capabilities/cap_123"},
            },
        )

        result = integration.agoragentic_listing_create(
            name="Seller Listing",
            description="Example listing",
            category="developer-tools",
            endpoint_url="https://seller.example.com/invoke",
            tags="seller, lifecycle ",
            _api_key="test-key",
        )

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["tags"], ["seller", "lifecycle"])
        self.assertEqual(payload["price_per_unit"], 0.10)
        self.assertEqual(result["status"], "created")
        self.assertEqual(result["listing_id"], "cap_123")
        self.assertEqual(result["links"]["detail"], "/api/capabilities/cap_123")

    @patch.object(integration.requests, "patch")
    def test_listing_update_sends_changes_and_shapes_result(self, mock_patch):
        """agoragentic_listing_update should forward changes and preserve review metadata."""
        mock_patch.return_value = FakeResponse(
            json_data={
                "message": "Capability updated successfully.",
                "review_status": "pending",
                "re_review_required": True,
                "changed_fields": ["description", "price_per_unit"],
            }
        )

        result = integration.agoragentic_listing_update(
            "cap_123",
            changes={"description": "Updated", "price_per_unit": 0.2},
            _api_key="test-key",
        )

        self.assertEqual(
            mock_patch.call_args.kwargs["json"],
            {"description": "Updated", "price_per_unit": 0.2},
        )
        self.assertEqual(result["status"], "updated")
        self.assertTrue(result["re_review_required"])

    @patch.object(integration.requests, "delete")
    def test_listing_delete_returns_deleted_status(self, mock_delete):
        """agoragentic_listing_delete should normalize a successful delist response."""
        mock_delete.return_value = FakeResponse(
            json_data={"message": "Capability delisted successfully."}
        )

        result = integration.agoragentic_listing_delete("cap_123", _api_key="test-key")

        self.assertEqual(result["status"], "deleted")
        self.assertIn("delisted", result["message"])

    @patch.object(integration.requests, "get")
    def test_listing_stats_surfaces_pricing_guidance(self, mock_get):
        """agoragentic_listing_stats should expose recent performance and pricing hints."""
        mock_get.return_value = FakeResponse(
            json_data={
                "total_invocations": 25,
                "successes": 23,
                "failures": 1,
                "timeouts": 1,
                "avg_latency_ms": 122,
                "total_revenue": 5.75,
                "total_platform_fees": 0.17,
                "recent_30d": {"invocations": 12, "success_rate": "91.7%"},
                "pricing_suggestion": {"action": "consider_raising"},
            }
        )

        result = integration.agoragentic_listing_stats("cap_123", _api_key="test-key")

        self.assertEqual(result["total_invocations"], 25)
        self.assertEqual(result["pricing_suggestion"]["action"], "consider_raising")

    @patch.object(integration.requests, "post")
    def test_listing_self_test_queues_run(self, mock_post):
        """agoragentic_listing_self_test should normalize the queued self-test response."""
        mock_post.return_value = FakeResponse(
            status_code=202,
            json_data={
                "run_id": "run_123",
                "listing_id": "cap_123",
                "trigger_type": "seller_self_test",
                "message": "Sandbox self-test queued.",
            },
        )

        result = integration.agoragentic_listing_self_test(
            "cap_123",
            test_input={"text": "hello"},
            timeout_ms=9000,
            _api_key="test-key",
        )

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["test_input"], {"text": "hello"})
        self.assertEqual(payload["timeout_ms"], 9000)
        self.assertEqual(result["status"], "queued")
        self.assertEqual(result["run_id"], "run_123")

    @patch.object(integration.requests, "put")
    def test_verification_credentials_set_shapes_safe_result(self, mock_put):
        """agoragentic_verification_credentials_set should normalize the safe response."""
        mock_put.return_value = FakeResponse(
            json_data={
                "success": True,
                "credential": {"cred_type": "bearer", "header_name": "Authorization"},
                "message": "Verification credentials set.",
            }
        )

        result = integration.agoragentic_verification_credentials_set(
            "cap_123",
            cred_type="bearer",
            header_value="Bearer demo",
            notes="temporary",
            _api_key="test-key",
        )

        payload = mock_put.call_args.kwargs["json"]
        self.assertEqual(payload["cred_type"], "bearer")
        self.assertEqual(payload["header_name"], "Authorization")
        self.assertTrue(result["success"])

    @patch.object(integration.requests, "get")
    def test_verification_credentials_get_returns_safe_summary(self, mock_get):
        """agoragentic_verification_credentials_get should return the safe summary as-is."""
        mock_get.return_value = FakeResponse(
            json_data={"has_verification_credentials": True, "cred_type": "bearer"}
        )

        result = integration.agoragentic_verification_credentials_get(
            "cap_123",
            _api_key="test-key",
        )

        self.assertTrue(result["has_verification_credentials"])
        self.assertEqual(result["cred_type"], "bearer")

    @patch.object(integration.requests, "delete")
    def test_verification_credentials_delete_normalizes_result(self, mock_delete):
        """agoragentic_verification_credentials_delete should surface delete metadata."""
        mock_delete.return_value = FakeResponse(
            json_data={"success": True, "deleted": True, "message": "Verification credentials deleted."}
        )

        result = integration.agoragentic_verification_credentials_delete(
            "cap_123",
            _api_key="test-key",
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["deleted"])

    def test_toolset_includes_listing_management_tools(self):
        """AgoragenticTools should expose the seller listing management surface."""
        tools = integration.AgoragenticTools(api_key="bound-key")
        tool_names = [tool.__name__ for tool in tools]

        self.assertEqual(len(tools), 27)
        self.assertIn("agoragentic_listing_create", tool_names)
        self.assertIn("agoragentic_listing_update", tool_names)
        self.assertIn("agoragentic_listing_delete", tool_names)
        self.assertIn("agoragentic_listing_stats", tool_names)
        self.assertIn("agoragentic_listing_self_test", tool_names)
        self.assertIn("agoragentic_verification_credentials_set", tool_names)
        self.assertIn("agoragentic_verification_credentials_get", tool_names)
        self.assertIn("agoragentic_verification_credentials_delete", tool_names)


if __name__ == "__main__":
    unittest.main()
