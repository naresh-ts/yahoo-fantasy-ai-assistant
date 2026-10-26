# Yahoo Fantasy AI Assistant

A private, non-commercial integration designed to connect an authorized Yahoo Fantasy Sports account with an AI assistant for personalized fantasy football analysis.

## Project Status

Yahoo API read-only access has been approved and the connector now supports authenticated league, roster, and available-player reads. The integration is **not yet deployed or connected to ChatGPT**. Remote MCP authentication and durable secret storage remain deployment requirements.

## Planned Features

The application is intended to use authorized, read-only access to retrieve:

* League settings and scoring rules
* My fantasy team and roster
* Other teams and rosters in my league
* Available players and waiver options
* Weekly matchups and standings
* Recent league transactions
* Player information available through Yahoo Fantasy

The AI assistant will use this information to provide:

* Weekly waiver recommendations
* Suggested players to add or drop
* Start/sit analysis
* Roster-strength and positional-needs analysis
* Matchup analysis
* Potential trade opportunities

## Intended Use

This is a personal, single-user project for analyzing my own Yahoo Fantasy league. It is not currently intended for commercial use or public distribution.

The initial version will be read-only. It will not automatically submit waiver claims, add or drop players, accept trades, change lineups, or perform other Yahoo Fantasy transactions.

## Planned Architecture

1. Yahoo OAuth 2.0 authorization
2. Yahoo Fantasy Sports API
3. A small read-only connector service
4. Model Context Protocol (MCP) tools
5. AI-assisted league analysis through ChatGPT

## Privacy and Security

Yahoo passwords, OAuth tokens, client secrets, league identifiers, and other private information will not be stored in this public repository. Sensitive configuration will be managed using environment variables and secure hosting configuration.

## Local Development

Prerequisites:

- Python 3.11 or newer
- Yahoo OAuth credentials for live requests (not required for unit tests)

Create a virtual environment and install the project:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the tests:

```bash
pytest
```

Start the MCP server over **local-only** Streamable HTTP:

```bash
python start_server.py
```

The launcher refuses non-loopback binding. Do **not** expose the MCP endpoint publicly until remote client authentication, TLS, and durable private token storage are configured.

The local MCP endpoint will be available at `http://localhost:8000/mcp`.

## Test Approved Yahoo Access

To perform a private,
interactive access test from a local terminal or GitHub Codespace:

```bash
python oauth_access_test.py
```

When `YAHOO_CLIENT_ID` and `YAHOO_CLIENT_SECRET` are configured as GitHub
Codespaces secrets, the script reads them automatically. Otherwise, it requests
them using hidden terminal input. It then opens the Yahoo authorization flow and
checks whether league `560937` is visible. Credentials and OAuth tokens remain in
memory and are not saved to disk.

## Configuration

Copy `.env.example` to `.env` and enter the
issued credentials locally. The `.env` file is ignored by Git and must never be
committed.

## Current Repository Structure

```text
config.py             # Environment-based configuration
server.py             # Read-only MCP tools
start_server.py       # Local-only HTTP MCP launcher
yahoo_client.py       # Read-only Yahoo HTTP client
token_manager.py      # Refresh and access token lifecycle
token_store.py        # Private local refresh-token persistence
test_*.py             # Initial automated tests
.env.example          # Safe configuration template
pyproject.toml        # Python dependencies and tooling
```

## Disclaimer

This is an independent personal project and is not affiliated with, endorsed by, or sponsored by Yahoo or OpenAI.

## Automated checks

Pull requests run the Python test suite and check the MCP startup script's syntax through GitHub Actions. These tests use mock credentials and do not require Yahoo secrets. Passing CI does **not** establish that a remote deployment is authenticated or reachable.
