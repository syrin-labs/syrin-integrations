"""Regression coverage for the unified Syrin Agent OS export kit."""

import importlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPORT_KIT = importlib.import_module("agoragentic.starter_kits.syrin_agent_os_export")
PLATFORM_PREVIEW_ROUTE = EXPORT_KIT.PLATFORM_PREVIEW_ROUTE
build_acceptance_checklist = EXPORT_KIT.build_acceptance_checklist
build_agent_os_export_prompt = EXPORT_KIT.build_agent_os_export_prompt
build_deployment_workflow = EXPORT_KIT.build_deployment_workflow
build_export_manifest = EXPORT_KIT.build_export_manifest
build_platform_preview_payload = EXPORT_KIT.build_platform_preview_payload
summarize_acceptance_status = EXPORT_KIT.summarize_acceptance_status


class SyrinAgentOSExportKitTests(unittest.TestCase):
    """Coverage for export manifests, deployment flows, and acceptance checks."""

    def test_export_manifest_composes_policy_sandbox_swarm_and_hosting(self):
        """Hybrid exports should include the core native Agent OS pieces."""
        export = build_export_manifest(
            "Deploy a bounded growth swarm.",
            mode="hybrid",
            agent_count=3,
            include_platform_hosting=True,
        )
        data = export.as_dict()
        component_names = {component["name"] for component in data["components"]}
        targets = {target["target"] for target in data["deployment_targets"]}

        self.assertEqual(data["schema"], "agoragentic.syrin.agent-os-export.v1")
        self.assertEqual(data["agent_count"], 3)
        self.assertIn("agoragentic_execute_router", component_names)
        self.assertIn("micro_ecf_policy_pack", component_names)
        self.assertIn("syrin_sandbox_execute_loop", component_names)
        self.assertIn("syrin_swarm_router_loop", component_names)
        self.assertIn("self_hosted", targets)
        self.assertIn("platform_hosted", targets)
        self.assertFalse(data["controls"]["run_live"])
        self.assertTrue(data["controls"]["require_receipt_reconciliation"])

    def test_export_manifest_preserves_zero_budget(self):
        """Explicit zero budgets should not be silently raised."""
        export = build_export_manifest("Preview only.", max_budget_usd=0.0)

        self.assertEqual(export.max_budget_usd, 0.0)
        self.assertEqual(export.as_dict()["max_budget_usd"], 0.0)

    def test_platform_preview_payload_is_no_spend(self):
        """Platform preview payloads should not allow live effects."""
        export = build_export_manifest(
            "Deploy a platform-hosted Syrin agent.",
            mode="platform_hosted",
            include_platform_hosting=True,
        )
        payload = build_platform_preview_payload(export, provider=" ")

        self.assertEqual(payload["method"], "POST")
        self.assertEqual(payload["route"], PLATFORM_PREVIEW_ROUTE)
        self.assertTrue(payload["preview_only"])
        self.assertTrue(payload["body"]["constraints"]["preview_only"])
        self.assertFalse(payload["body"]["constraints"]["live_effects_allowed"])
        self.assertEqual(payload["body"]["provider"], "simulated_runtime")

    def test_acceptance_checklist_covers_smoke_receipts_and_rollback(self):
        """Acceptance should force the operational checks that close the live gap."""
        export = build_export_manifest("Deploy safely.", mode="hybrid", include_platform_hosting=True)
        checklist = build_acceptance_checklist(export)
        check_ids = {check["id"] for check in checklist["checks"]}

        self.assertIn("static_compile", check_ids)
        self.assertIn("micro_ecf_review", check_ids)
        self.assertIn("syrin_sandbox_smoke", check_ids)
        self.assertIn("swarm_router_preview", check_ids)
        self.assertIn("receipt_reconciliation", check_ids)
        self.assertIn("rollback_plan", check_ids)
        self.assertIn("platform_hosted_preview", check_ids)
        self.assertFalse(summarize_acceptance_status(checklist)["ready_for_live"])

    def test_deployment_workflow_keeps_live_enablement_last(self):
        """The canonical workflow should keep live effects out until acceptance."""
        workflow = build_deployment_workflow("Deploy a bounded swarm.", mode="hybrid", agent_count=2)
        phases = workflow["phases"]

        self.assertEqual(phases[-1]["id"], "optional_live_enablement")
        self.assertTrue(phases[-1]["live_effects_allowed"])
        self.assertTrue(all(not phase["live_effects_allowed"] for phase in phases[:-1]))
        self.assertEqual(workflow["platform_preview_payload"]["route"], PLATFORM_PREVIEW_ROUTE)
        self.assertIn("Micro ECF", workflow["agent_os_prompt"])

    def test_export_builders_reject_invalid_budget_and_agent_count(self):
        """Invalid deployment parameters should fail before manifest construction."""
        with self.assertRaisesRegex(ValueError, "agent_count"):
            build_export_manifest("Bad count.", agent_count=0)

        with self.assertRaisesRegex(ValueError, "max_budget_usd"):
            build_deployment_workflow("Bad budget.", max_budget_usd=-0.01)

    def test_agent_os_prompt_keeps_core_cli_maintainer_gated(self):
        """The export prompt should not tell users core CLI integration exists."""
        prompt = build_agent_os_export_prompt("Export the router.", mode="platform_hosted", agent_count=5)

        self.assertIn("Syrin remains the control plane", prompt)
        self.assertIn("Agoragentic remains the execution/deployment/marketplace plane", prompt)
        self.assertIn("USDC on Base", prompt)
        self.assertIn("Do not implement or assume `syrin integrate agoragentic`", prompt)

    def test_future_core_integration_is_disabled_by_default(self):
        """Core Syrin integration must stay maintainer-gated for now."""
        data = build_export_manifest("Export safely.").as_dict()
        future = data["future_core_integration"]

        self.assertEqual(future["status"], "maintainer_gated")
        self.assertFalse(future["implemented_here"])
        self.assertEqual(future["candidate_command"], "syrin integrate agoragentic")


if __name__ == "__main__":
    unittest.main()
