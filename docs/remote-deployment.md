# Remote MCP deployment — security and readiness

**Status: not deployed.** The local MCP server is not yet a secure remote
ChatGPT connector. Do not expose a Codespace port or set `MCP_HOST=0.0.0.0`
to bypass the local-only launcher guard.

## Required before connecting ChatGPT

1. Select an HTTPS hosting service with an authenticated ingress.
2. Configure MCP client authentication supported by ChatGPT. The Yahoo OAuth
   credential is for Yahoo API calls; **it does not authenticate ChatGPT to
   our MCP server**.
3. Enforce authorization on every MCP request, including tool listing and
   calls; reject unauthenticated requests before invoking any Yahoo tools.
4. Store the Yahoo refresh token in a persistent, private secret store.
   The current local file works for a single durable host but must not be
   placed on ephemeral storage. Coordinate token rotation across workers.
5. Keep Yahoo client ID, client secret, refresh token and any MCP auth secrets
   out of GitHub source, CI logs, and client-visible responses.
6. Use a single trusted user or explicitly scoped access; rate-limit calls
   and avoid logging authorization headers.
7. Test remote authentication failure, authorized tool discovery, token
   refresh and live Yahoo read-only calls before connecting ChatGPT.

## What currently works

- Local read-only MCP tools: `project_status`, `get_my_roster`,
  `get_available_players`, `get_team_snapshot`.
- Local-only Streamable HTTP launcher: `python start_server.py`.
- Yahoo token renewal and restricted-permission local token persistence.
- Automated tests via GitHub Actions.

## Still to implement

- HTTPS hosting and authenticated remote MCP ingress.
- Durable managed Yahoo refresh-token persistence with multi-instance
  concurrency control if hosting multiple workers.
- End-to-end live deployment test.
- More Yahoo Fantasy data for complete Waiver Full analysis: scoring rules,
  matchups, player statistics, injury reports, league transactions and
  waiver availability.

## Local Codespace verification (no credentials printed)

```bash
git pull --ff-only
python -m pytest -q
python deployment_preflight.py
```

Do not run the live Yahoo API tests in GitHub Actions with production
credentials unless a separate, restricted secrets policy is in place.

## Selected hosting direction

Use a **single-instance Render paid web service** with HTTPS, a persistent
disk, and an established OAuth identity provider (for example Auth0) to
authenticate ChatGPT clients. The current local-only launcher is deliberately
not a Render web service yet. A public deployment must wait until OAuth
resource protection is implemented and tested.

Render's default filesystem is ephemeral. For a mounted persistent disk,
configure `YAHOO_TOKEN_DIR` to a private directory inside that mount and
limit access to the service process. Keep a single worker until rotating
refresh-token coordination is implemented. Do not store a refresh token
in the repository or bake it into a container image.

**Cost:** Render paid compute, persistent disk, and any identity provider
fees must be checked in the hosting dashboard before creating resources.

## Free-first hosting decision

**Budget: $0; do not provision a paid Render service or persistent disk.**

Evaluate an Oracle Cloud Always Free VM with its included persistent boot
volume as a possible single-instance host. Availability, signup requirements,
regional capacity, and free-tier eligibility must be checked before use.
HTTPS, an authenticated MCP OAuth integration, secure private token storage,
backups, and operating-system updates remain mandatory. A free VM is **not**
a shortcut around authentication or operations.

If a free VM cannot be provisioned, retain local-only access and reassess
other free providers. Do not switch to an ephemeral free web service without
a durable, private refresh-token store, and never expose an unauthenticated
Codespace port. No provider account has been created.

## OAuth verification implementation status

The `oauth_verifier.py` module verifies RS256-signed JWTs against an
explicit HTTPS JWKS endpoint, issuer, and resource audience. **It is not
yet wired into an ASGI HTTP middleware or MCP authorization flow.**
Remote access remains disabled by the local-only launcher. Before
deployment, implement an OAuth-protected resource server with bearer
token extraction, challenge and metadata endpoints, authorized-user
policy, and end-to-end unauthenticated-request rejection tests. Do not
treat the presence of a JWT verifier as proof that the endpoint is safe
to expose.

## HTTP authentication gate

The `OAuthASGIGate` class enforces Bearer JWT verification and an
explicit allowlisted OAuth subject before forwarding HTTP requests to an
ASGI app. It denies missing, duplicate, malformed, expired, and
wrong-user tokens (through the JWT verifier). This is a building block,
**not yet an installed remote MCP transport**.

A production-ready MCP OAuth integration still requires protected
resource metadata, discovery/authorization compatibility with ChatGPT,
the remote launcher, integration tests, and hardened HTTPS deployment.
The local-only `start_server.py` remains unchanged.
