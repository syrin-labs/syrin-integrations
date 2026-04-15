# Workflow Schemas

These schemas describe how Agoragentic workflows should be represented in Syrin
examples. They are integration contracts, not a replacement for the live
Agoragentic OpenAPI document.

The goal is to keep agent workflows predictable enough for humans, agents, and
CI to inspect.

## Common envelope

Use this envelope for new workflow examples:

```json
{
  "intent": "route_capability",
  "mode": "preview",
  "budget": {
    "max_usd": 0.25
  },
  "inputs": {},
  "controls": {
    "run_live": false,
    "prefer_execute": true
  },
  "expected_outputs": []
}
```

Recommended fields:

- `intent`: short workflow name such as `route_capability`, `direct_invoke`,
  `seller_listing_lifecycle`, `relay_deploy`, or `memory_or_identity`.
- `mode`: `public_read`, `preview`, `dry_run`, or `live`.
- `budget.max_usd`: buyer-side budget cap when the workflow can spend.
  Note: examples use `budget.max_usd` as the workflow contract and send it to
  the API as `constraints.max_cost` at request time.
- `inputs`: task, listing ID, payload, media URLs, or seller listing fields.
- `controls.run_live`: explicit live-mode gate.
- `controls.prefer_execute`: true for routed buyer work.
- `expected_outputs`: fields the example should print or verify.

## Buyer route schema

Use this for routed marketplace execution:

```json
{
  "intent": "route_capability",
  "mode": "preview",
  "budget": {
    "max_usd": 0.25
  },
  "inputs": {
    "task": "Summarize this paper and return three implementation risks.",
    "category": "research"
  },
  "controls": {
    "run_live": false,
    "prefer_execute": true
  },
  "expected_outputs": [
    "matched_provider",
    "estimated_price",
    "result"
  ]
}
```

Use `agoragentic_match` first when fit is unclear. Use
`agoragentic_execute` when the marketplace should choose the provider.

## Direct invoke schema

Use this only when the workflow intentionally pins a known listing:

```json
{
  "intent": "direct_invoke",
  "mode": "preview",
  "inputs": {
    "listing_id_or_slug": "known-listing",
    "payload": {
      "task": "Run the fixed provider workflow."
    }
  },
  "controls": {
    "run_live": false,
    "prefer_execute": false
  },
  "expected_outputs": [
    "listing",
    "invoke_payload",
    "result"
  ]
}
```

Prefer routed execution unless a fixed listing is part of the requirement.

## Multimodal schema

Use this when a task combines text with image or document URLs:

```json
{
  "intent": "multimodal_review",
  "mode": "preview",
  "budget": {
    "max_usd": 0.5
  },
  "inputs": {
    "task": "Review the image against the SOP and flag risks.",
    "image_url": "https://example.com/screenshot.png",
    "document_url": "https://example.com/sop.pdf"
  },
  "controls": {
    "run_live": false,
    "prefer_execute": true
  },
  "expected_outputs": [
    "matched_provider",
    "review_findings"
  ]
}
```

Keep binary data out of examples. Prefer URLs or metadata so the payload remains
readable and portable.

## Seller listing schema

Use this for listing create, update, stats, verification credentials, self-test,
and delete flows:

```json
{
  "intent": "seller_listing_lifecycle",
  "mode": "preview",
  "inputs": {
    "name": "Syrin demo capability",
    "description": "A capability exposed from a Syrin-backed seller workflow.",
    "endpoint_url": "https://example.com/invoke",
    "price_usd": 0.05
  },
  "controls": {
    "run_live": false,
    "delete_after_test": true
  },
  "expected_outputs": [
    "listing_id",
    "self_test_status",
    "stats"
  ]
}
```

Never imply a listing is verified unless the self-test or sandbox verification
actually ran.

## Relay deployment schema

Use this for preview-first relay-hosted JavaScript seller functions:

```json
{
  "intent": "relay_deploy",
  "mode": "preview",
  "inputs": {
    "function_name": "syrin-demo-seller",
    "source_kind": "inline_sample",
    "auto_list": false
  },
  "controls": {
    "run_live": false,
    "dry_run_after_deploy": true
  },
  "expected_outputs": [
    "function_id",
    "dry_run_result",
    "listing_id"
  ]
}
```

Deploy only after previewing the source and confirming live mode.

## Memory, secrets, and identity schema

Use this for durable memory, encrypted-secret, vault, and passport workflows:

```json
{
  "intent": "memory_or_identity",
  "mode": "preview",
  "inputs": {
    "namespace": "learning",
    "memory_key": "routing.lesson",
    "passport_subject": "current-agent"
  },
  "controls": {
    "run_live": false,
    "write_memory": false,
    "store_secret": false
  },
  "expected_outputs": [
    "memory_summary",
    "vault_inventory",
    "passport_status"
  ]
}
```

Read before writing. When writing, use labels and namespaces that make rollback
or cleanup straightforward.

## Process verification schema

Use this when the example verifies that the Syrin process followed expected
tool-use checkpoints:

```json
{
  "intent": "process_verification",
  "mode": "dry_run",
  "inputs": {
    "required_tools": [
      "agoragentic_match",
      "agoragentic_execute"
    ],
    "task": "Preview then route a marketplace task."
  },
  "controls": {
    "run_live": false,
    "inspect_trace": true
  },
  "expected_outputs": [
    "checkpoints",
    "trace_summary",
    "missing_steps"
  ]
}
```

Verification should describe what was observed. It should not claim runtime
trust that was not actually proven.

## Agent OS loop schema

Use this when a Syrin agent reads the Agoragentic control plane before choosing
work:

```json
{
  "intent": "agent_os_loop",
  "mode": "preview",
  "budget": {
    "max_usd": 0.25
  },
  "inputs": {
    "task": "Inspect operating state and identify one safe next action.",
    "control_plane": [
      "commerce.account",
      "jobs.summary",
      "procurement",
      "approvals",
      "learning",
      "reconciliation",
      "identity",
      "tumbler.graduation",
      "tasks"
    ]
  },
  "controls": {
    "run_live": false,
    "prefer_execute": true,
    "require_match_before_execute": true
  },
  "expected_outputs": [
    "survival_tier",
    "recommended_mode",
    "prompt",
    "match_preview"
  ]
}
```

The loop may borrow autonomy concepts such as heartbeat polling and survival
tiers, but live execution still stays behind explicit Agoragentic budget,
approval, Tumbler, and live-mode gates.

## Skill evolution schema

Use this when a Syrin agent plans a Read -> Execute -> Reflect -> Write cycle:

```json
{
  "intent": "skill_evolution",
  "mode": "preview",
  "budget": {
    "max_usd": 0.25
  },
  "inputs": {
    "task": "Route a research task and propose one reusable improvement.",
    "candidate_skills": [
      "preview-first-research-routing",
      "process-verified-marketplace-run"
    ]
  },
  "controls": {
    "run_live": false,
    "write_memory": false,
    "mutate_code": false
  },
  "expected_outputs": [
    "selected_skill",
    "execute_payload",
    "reflection",
    "learning_note_payload"
  ]
}
```

Write memory only after execution evidence passes a grader or review.

## Autonomous eval loop schema

Use this when an agent should measure whether an execution should be kept,
iterated, or discarded:

```json
{
  "intent": "autonomous_eval_loop",
  "mode": "preview",
  "budget": {
    "max_usd": 0.25
  },
  "inputs": {
    "task": "Run a budget-constrained route.",
    "grader": {
      "required_terms": [
        "agoragentic",
        "budget"
      ],
      "forbidden_terms": [
        "unbounded spend"
      ]
    }
  },
  "controls": {
    "run_live": false,
    "record_attempt": true,
    "redact_secrets": true
  },
  "expected_outputs": [
    "score",
    "attempt_record",
    "reflection"
  ]
}
```

Attempt records should preserve evidence without leaking API keys, tokens,
signing keys, authorization headers, or secrets.

## Trap-aware execute schema

Use this when untrusted web, email, document, memory, or approval content may
influence tool calls:

```json
{
  "intent": "trap_aware_execute",
  "mode": "preview",
  "budget": {
    "max_usd": 0.25
  },
  "inputs": {
    "task": "Summarize this web page safely.",
    "source_trust": "untrusted",
    "requested_action": "route_capability"
  },
  "controls": {
    "run_live": false,
    "require_approval_on_medium_or_high_risk": true
  },
  "expected_outputs": [
    "trap_report",
    "approval_evidence",
    "execute_payload"
  ]
}
```

High-risk trap signals should interrupt live spend, deployment, memory writes,
secret access, and approval flows.

## Multimodal process-eval schema

Use this when the workflow needs process evidence for image, document, or
search-heavy tasks:

```json
{
  "intent": "multimodal_process_eval",
  "mode": "preview",
  "budget": {
    "max_usd": 0.5
  },
  "inputs": {
    "task": "Inspect this image and cite decisive visual evidence.",
    "image_url": "https://example.com/screenshot.png",
    "document_url": "https://example.com/spec.pdf"
  },
  "controls": {
    "run_live": false,
    "log_visual_events": true,
    "log_search_events": true
  },
  "expected_outputs": [
    "process_events",
    "visual_artifacts",
    "strategy_score",
    "visual_tool_score",
    "visual_evidence_score",
    "overthinking_score"
  ]
}
```

This complements final-answer grading by checking whether the agent generated
evidence-bearing intermediate artifacts.

## Harness engineering schema

Use this when an agent proposes improvements to prompts, tools, routing, or
orchestration:

```json
{
  "intent": "harness_engineering",
  "mode": "preview",
  "budget": {
    "max_usd": 0.25
  },
  "inputs": {
    "task": "Suggest one simpler routing rule.",
    "fixed_boundary": [
      "adapter_boundary",
      "benchmark_runner",
      "settlement",
      "approval_gates"
    ]
  },
  "controls": {
    "run_live": false,
    "return_patch_plan_not_patch": true,
    "allow_git_mutation": false
  },
  "expected_outputs": [
    "iteration_payload",
    "boundary_violations",
    "decision"
  ]
}
```

Equal benchmark score with lower complexity can be a keep decision. Boundary
violations should always discard the change.

## Optional sandbox-agent schema

Use this when a user wants to run the workflow inside an OpenAI Agents SDK-style
sandbox or another hosted sandbox provider:

```json
{
  "intent": "sandbox_agent_loop",
  "mode": "preview",
  "budget": {
    "max_usd": 0.25
  },
  "inputs": {
    "task": "Run a preview-first sandboxed Agoragentic task.",
    "manifest_entries": [
      "instructions/AGENTS.md",
      "inputs/task.json",
      "outputs/attempt.json",
      "outputs/reflection.json"
    ]
  },
  "controls": {
    "run_live": false,
    "require_manifest": true,
    "require_guardrails": true
  },
  "expected_outputs": [
    "manifest_entries",
    "guardrail_report",
    "execute_payload"
  ]
}
```

Keep sandbox examples optional. They should not become a hard dependency for
using the Agoragentic Syrin integration.
