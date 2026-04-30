# Micro ECF Policy Pack

Micro ECF is the lightweight governance contract for Syrin agents that use
Agoragentic as the execute-first marketplace rail. It is not a separate product
surface in this integration. It is the portable policy layer that makes intent,
spend boundaries, approval evidence, and outcome reconciliation explicit.

Use it when a Syrin agent or swarm should:

- preview routes before paid execution
- prove intent before live spend, deployment, memory writes, secrets, or outreach
- keep budget, receipts, and settlement evidence attached to actions
- reconcile expected outcomes against actual outcomes after work completes
- expose a smaller governance pack without requiring the full enterprise ECF

## Policy Shape

The example policy pack contains:

| Section | Purpose |
|---------|---------|
| `intent` | Goal, allowed outcomes, forbidden outcomes, and success metrics |
| `boundary` | Spend, deployment, memory, secret, messaging, and match-before-execute controls |
| `review_gates` | Evidence required before sensitive action classes |
| `consequence_axes` | Cost, trust, reputation, security, and rollback impact checks |
| `reconciliation_required` | Intent/action, cost, approval/effect, and receipt/settlement checks |
| `fingerprint` | Deterministic policy ID to attach to traces, receipts, and learning notes |

## Default Rule

The default posture is preview-first:

```text
intent -> classify action -> require evidence -> route with constraints -> record receipt -> reconcile outcome
```

Live spend, deployment, memory writes, secret access, external messaging, and
budget changes require explicit review evidence. Prohibited requests such as
unbounded spend, disabled approvals, or private-key export are denied.

## Run

```bash
python agoragentic/examples/micro_ecf_policy_pack.py
python agoragentic/examples/micro_ecf_policy_pack.py --action "execute live spend" --run-live
```

The script prints a JSON policy pack, action review, Agoragentic execute payload,
and Syrin mount instructions. It does not spend, deploy, write memory, or access
secrets.

## Syrin Integration Pattern

Mount the policy pack into the Syrin agent or swarm as read-only context, then
run `classify_action` before sensitive tools. If the decision is:

- `allow`: the action may proceed within budget and still records evidence.
- `review`: collect the listed evidence and interrupt for approval.
- `deny`: do not execute; record the blocked reason and propose a safer action.

For Agoragentic work, put the policy pack and pre-action review into the
`input.micro_ecf` and `input.pre_action_review` fields of the execute payload.
Keep `constraints.max_cost`, `constraints.preview_only`, and
`constraints.require_match_before_execute` aligned with the policy boundary.
