# OpenFisca MCP

MCP (Model Context Protocol) tools for interacting with OpenFisca tax-benefit systems.

## Installation

```bash
poetry install
```

## Usage

### Start the OpenFisca server

```bash
./scripts/serve.sh
```

### Run the MCP server

```bash
poetry run openfisca-mcp
```

### Configure with Claude Desktop

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "openfisca": {
      "command": "poetry",
      "args": ["run", "openfisca-mcp"],
      "cwd": "/path/to/RaMCP"
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_entities` | List entity types (person, household) and their roles |
| `list_variables` | List all available variables, optionally filtered by entity |
| `describe_variable` | Get detailed variable info (type, period, formulas) |
| `list_parameters` | List all parameters (rates, thresholds, amounts) |
| `get_parameter` | Get parameter values and history |
| `search_variables` | Search variables by keyword |
| `calculate` | Compute variable values for a situation |
| `trace_calculation` | Calculate with dependency tracing for explainability |
| `validate_situation` | Validate situation structure without calculating |

## Container images

One Dockerfile builds two images. The MCP bridge only talks HTTP to an
OpenFisca Web API, so the two runtimes share no Python dependencies.

| Target | Contents | Default command |
|--------|----------|-----------------|
| `api` | OpenFisca Core, the web server stack and one country package | `api` (gunicorn on port 5000) |
| `mcp` (default) | The MCP bridge (`mcp`, `httpx`, `uvicorn`) | `mcp` (SSE on port 8080) |

```bash
docker build --target api -t openfisca-api .
docker build --target mcp -t openfisca-mcp .
docker compose up        # both, wired together
```

Build arguments for `api`: `COUNTRY_PACKAGE_DIR` (directory under
`country-packages/`, default `openfisca-aotearoa`) and `COUNTRY_PACKAGE`
(its Python module, default `openfisca_aotearoa`). Initialise the country
package submodule first: `git submodule update --init country-packages/openfisca-aotearoa`.

Both images build on a digest-pinned Wolfi base with Python 3.13, apply pending
OS updates on every build, install hash-locked dependencies from
`requirements/*.lock`, remove pip after `pip check`, and run as UID 65532.
Regenerate a lock after editing its `.txt` with the command in that file's header.

The country package's declared `openfisca-core[web-api]` range is rewritten at
build time to the locked Core and web versions by
`scripts/relock-country-package.py`, and the package version gains a local
suffix (for example `22.0.0+openfiscamcp1`). Calculation code is unchanged; the
script refuses to run if the upstream declaration changes shape.

## Usage events (optional)

The SSE server can post usage events to a Loom/Umami-style collector. It is off
unless both `LOOM_INGEST_URL` and `LOOM_TENANT` are set.

| Variable | Meaning |
|----------|---------|
| `LOOM_INGEST_URL` | Collector base URL; events are POSTed to `/collect` |
| `LOOM_TENANT` | Tenant id stamped as `X-Loom-Tenant` |
| `LOOM_SOURCE_ID` | Source id for external traffic (default: the tenant) |
| `LOOM_INGEST_SECRET` | Shared secret sent as `X-Loom-Auth` |
| `LOOM_INTERNAL_UA_PATTERN` | Regex of User-Agents to record as internal |

One event is sent per SSE session start (`agora.rules.mcpSessionStart`) and per
tool call (`agora.rules.mcpToolCall`, with tool name, outcome and latency).
Tool arguments and results are never sent. The client address is passed to the
collector only as `X-Forwarded-For`, for its daily-salted visitor hash. The MCP
session id is never sent; events in one session share a random `trace_id`.

Requests carrying a non-empty `X-Agora-Internal` header, or a User-Agent
matching `LOOM_INTERNAL_UA_PATTERN`, are recorded with source `internal` so
smoke tests and agents can be excluded from usage figures.

Delivery is best effort: a bounded queue and one background thread. A slow or
unavailable collector drops events; it never delays or fails a request.

## Development

### Run tests

```bash
poetry run pytest
```

### Generate golden fixtures

```bash
./scripts/serve.sh &
poetry run python tests/generate_golden.py
```
  ┌────────────────────┬───────┬───────────────────────────────────────────────────────────────────────────────────────────┐
  │      Package       │ Tests │                                       Key Findings                                        │
  ├────────────────────┼───────┼───────────────────────────────────────────────────────────────────────────────────────────┤
  │ openfisca-france   │ 14 ✅ │ 4 entities, MONTH periods for age, all 4 entities required in situations                   │
  ├────────────────────┼───────┼───────────────────────────────────────────────────────────────────────────────────────────┤
  │ openfisca-aotearoa │ 17 ✅ │ 5 entities (including property entities), DAY periods for age, minimal situations allowed │
  └────────────────────┴───────┴───────────────────────────────────────────────────────────────────────────────────────────┘