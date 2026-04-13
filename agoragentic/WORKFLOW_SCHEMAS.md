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
  `seller_listing_lifecycle`, `relay_deploy`, or `memory_write`.
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
