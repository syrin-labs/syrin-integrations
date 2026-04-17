# Agoragentic starter kits

Starter kits package the Agoragentic x Syrin integration into deployment-shaped
folders instead of one-file examples.

Use a starter kit when you want:

- a served Syrin agent process
- explicit environment variables and fail-closed defaults
- Docker and smoke-test assets
- a clearer path from local development to self-hosted deployment

## Available starter kits

### `hosted_syrin_agent/`

A preview-first, self-hostable Syrin agent that exposes the standard Syrin HTTP
routes and uses Agoragentic as the capability router.

Includes:

- runtime config helpers with preview-first defaults
- served agent entrypoint
- `.env.example`
- Dockerfile and `docker-compose.yml`
- `/health`, `/ready`, and `/describe` smoke test
- self-hosted now / platform-hosted later deployment notes

Start with [hosted_syrin_agent/README.md](hosted_syrin_agent/README.md).
