# Phase 1: Analysis Outputs

This directory contains the outputs from Phase 1 of the OpenFisca MCP project — analysis of the OpenFisca codebase to inform tool design.

## Documents

| Document | Description |
|----------|-------------|
| [01-web-api-surface.md](01-web-api-surface.md) | Complete map of HTTP endpoints, methods, request/response schemas |
| [02-entity-model.md](02-entity-model.md) | Entity types, roles, relationships, and situation JSON structure |
| [03-variable-parameter-schemas.md](03-variable-parameter-schemas.md) | Variable attributes, parameter formats, period handling |
| [04-simulation-lifecycle.md](04-simulation-lifecycle.md) | Request flow from JSON to calculation with tracing |
| [05-error-taxonomy.md](05-error-taxonomy.md) | Error types, HTTP codes, response formats |

## Key Findings

### Candidate MCP Tools (Confirmed)

Based on the API surface analysis, the following tools map directly to existing endpoints:

| Tool | Endpoint | Priority |
|------|----------|----------|
| `list_variables` | GET /variables | Core |
| `describe_variable` | GET /variable/{id} | Core |
| `list_parameters` | GET /parameters | Medium |
| `get_parameter` | GET /parameter/{id} | Core |
| `list_entities` | GET /entities | Core |
| `calculate` | POST /calculate | Core |
| `trace_calculation` | POST /trace | High |

Additional tools to build:
- `search_variables` — fuzzy search (not in API, build on top)
- `validate_situation` — pre-validate without calculating
- `scaffold_situation` — generate empty situation template (later phase)
- `batch_calculate` — multi-variable/date-range (v2)

### Critical Design Considerations

1. **Period handling** — Variables have definition periods (MONTH/YEAR/DAY/ETERNITY). Tool descriptions must be explicit about expected formats.

2. **Error schema** — Use nested path format (`entity/id/variable/period`) for field-level errors, simple `{error: message}` for top-level.

3. **Entity relationships** — Situations require correct role assignments. `list_entities` output should clearly document role constraints.

4. **Tracing for explainability** — The `/trace` endpoint provides dependency trees. Essential for LLM explanations of results.

## Sources

Analysis based on:
- `openfisca-core` @ commit from clone
- `country-template` @ commit from clone
