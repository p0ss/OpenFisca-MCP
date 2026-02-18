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
