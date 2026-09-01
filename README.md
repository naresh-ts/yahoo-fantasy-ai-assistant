# Yahoo Fantasy AI Assistant

A private, non-commercial integration designed to connect an authorized Yahoo Fantasy Sports account with an AI assistant for personalized fantasy football analysis.

## Project Status

This project is currently in initial development. Access to the Yahoo Fantasy Sports API is pending approval.

The safe project scaffold is now in place. Yahoo OAuth and league-data tools will
be implemented after Yahoo provisions read-only API access.

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
- Yahoo API approval for live Yahoo requests (not required for the current tests)

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

Start the MCP server over Streamable HTTP:

```bash
mcp run server.py --transport streamable-http
```

The local MCP endpoint will be available at `http://localhost:8000/mcp`.

## Configuration

After Yahoo approves the application, copy `.env.example` to `.env` and enter the
issued credentials locally. The `.env` file is ignored by Git and must never be
committed.

## Current Repository Structure

```text
config.py             # Environment-based configuration
server.py             # MCP server and safe status tool
yahoo_client.py       # Read-only Yahoo HTTP client foundation
test_*.py             # Initial automated tests
.env.example          # Safe configuration template
pyproject.toml        # Python dependencies and tooling
```

## Disclaimer

This is an independent personal project and is not affiliated with, endorsed by, or sponsored by Yahoo or OpenAI.
