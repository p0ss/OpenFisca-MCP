# OpenFisca MCP Tools

This directory contains documentation for each MCP tool. These docs serve as both developer reference and LLM tool descriptions.

## Tool Index

| Tool | Priority | Description |
|------|----------|-------------|
| [list_entities](list_entities.md) | Core | List entity types and their roles |
| [list_variables](list_variables.md) | Core | List available variables |
| [describe_variable](describe_variable.md) | Core | Get variable details |
| [list_parameters](list_parameters.md) | Medium | List parameters |
| [get_parameter](get_parameter.md) | Core | Get parameter values |
| [search_variables](search_variables.md) | High | Search variables by keyword |
| [calculate](calculate.md) | Core | Compute variable values |
| [trace_calculation](trace_calculation.md) | High | Calculate with dependency tracing |
| [validate_situation](validate_situation.md) | Medium | Validate situation structure |

## Recommended Tool Flow

1. **Discovery Phase**
   - `list_entities` - Understand entity structure
   - `list_variables` or `search_variables` - Find relevant variables
   - `describe_variable` - Get period format and entity

2. **Calculation Phase**
   - Construct situation JSON with correct structure
   - `validate_situation` - Check for errors (optional)
   - `calculate` - Get results

3. **Explanation Phase**
   - `trace_calculation` - Explain how result was reached
   - `get_parameter` - Show relevant thresholds/rates
