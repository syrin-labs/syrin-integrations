# syrin-integrations

Third-party integrations with Syrin.

Each integration lives in its own top-level directory and should include:

- a focused README
- install and environment instructions
- copy-paste examples
- any adapter code needed to connect the third-party system to Syrin

## Available integrations

### `agoragentic/`

Agoragentic as an execute-first capability router for Syrin.

Includes:

- a 19-tool Syrin adapter surface
- starter agent example
- HTTP serving example
- multimodal preview-first example
- process-verification example using hooks and checkpoints
- relay-hosted seller deployment example
- a practical guide explaining when Agoragentic is the right fit

See [agoragentic/README.md](agoragentic/README.md) and
[agoragentic/WHY_AGORAGENTIC.md](agoragentic/WHY_AGORAGENTIC.md).

## Contributing

Add each integration in its own directory so the code, docs, and examples stay isolated and easy to evolve independently.
