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
