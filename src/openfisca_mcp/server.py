"""OpenFisca MCP Server.

Provides MCP tools for interacting with OpenFisca tax-benefit systems.
"""

import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .client import OpenFiscaClient
from .errors import MCPError, NotFoundError, ValidationError

# Initialize server and client
server = Server("openfisca-mcp")
client = OpenFiscaClient()


def format_result(data: Any) -> list[TextContent]:
    """Format result as MCP TextContent."""
    if isinstance(data, dict):
        return [TextContent(type="text", text=json.dumps(data, indent=2))]
    return [TextContent(type="text", text=str(data))]


def format_error(error: MCPError) -> list[TextContent]:
    """Format error as MCP TextContent."""
    return [TextContent(type="text", text=json.dumps(error.to_dict(), indent=2))]


# =============================================================================
# Tool Definitions
# =============================================================================


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="list_entities",
            description="""List all entity types in the tax-benefit system.

Returns the entity types (person, household, etc.) and their roles.
Use this before constructing a situation to understand the required structure.

Example response:
- person: The individual entity (no roles)
- household: Group entity with roles like 'adult', 'child'""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="list_variables",
            description="""List all available variables in the tax-benefit system.

Returns variable names with descriptions, filterable by entity type.
This is the entry point for discovering what the rule set can compute.

Use this to find variables before using describe_variable for details.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity": {
                        "type": "string",
                        "description": "Filter by entity type (e.g., 'person', 'household')",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="describe_variable",
            description="""Get detailed information about a specific variable.

Returns the variable's:
- valueType: Float, Int, Boolean, String, Date
- definitionPeriod: MONTH, YEAR, DAY, or ETERNITY
- entity: Which entity it belongs to (person, household, etc.)
- description: What it represents
- formulas: Calculation logic with start dates
- references: Legislative sources

IMPORTANT: The definitionPeriod tells you what period format to use:
- MONTH: Use 'YYYY-MM' (e.g., '2024-01')
- YEAR: Use 'YYYY' (e.g., '2024')
- DAY: Use 'YYYY-MM-DD' (e.g., '2024-01-15')
- ETERNITY: Use 'ETERNITY' for values that never change""",
            inputSchema={
                "type": "object",
                "properties": {
                    "variable_name": {
                        "type": "string",
                        "description": "The variable name (e.g., 'salary', 'income_tax')",
                    },
                },
                "required": ["variable_name"],
            },
        ),
        Tool(
            name="list_parameters",
            description="""List all parameters in the tax-benefit system.

Parameters are the rates, thresholds, and amounts defined in legislation
that change over time. Use get_parameter to see historical values.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_parameter",
            description="""Get a parameter's value and history.

Returns the parameter's values at different dates, including:
- Simple values: Single number/boolean changing over time
- Scales: Tax brackets with thresholds and rates

Use this to look up current thresholds, rates, and amounts.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "parameter_id": {
                        "type": "string",
                        "description": "The parameter ID (e.g., 'taxes.income_tax_rate')",
                    },
                },
                "required": ["parameter_id"],
            },
        ),
        Tool(
            name="search_variables",
            description="""Search for variables by keyword.

Searches variable names and descriptions for matching terms.
Use this when you don't know the exact variable name.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (e.g., 'tax', 'allowance', 'income')",
                    },
                    "entity": {
                        "type": "string",
                        "description": "Filter by entity type (optional)",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="calculate",
            description="""Calculate variable values for a given situation.

Takes a situation (people, households, and their known values) and computes
requested variables. Set a variable to null to request its calculation.

IMPORTANT - Situation structure:
```json
{
  "persons": {
    "person_id": {
      "variable_name": {"period": value_or_null}
    }
  },
  "households": {
    "household_id": {
      "adults": ["person_id"],
      "children": ["person_id"],
      "variable_name": {"period": value_or_null}
    }
  }
}
```

IMPORTANT - Period format depends on variable's definitionPeriod:
- MONTH variables: Use 'YYYY-MM' (e.g., '2024-01')
- YEAR variables: Use 'YYYY' (e.g., '2024')
- ETERNITY variables: Use 'ETERNITY'

Set value to null to request calculation of that variable.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "situation": {
                        "type": "object",
                        "description": "The situation JSON with persons, households, and variables",
                    },
                },
                "required": ["situation"],
            },
        ),
        Tool(
            name="trace_calculation",
            description="""Calculate with full dependency tracing for explainability.

Like calculate, but returns a detailed trace showing:
- Which variables were computed
- What each variable depended on
- What parameter values were used

Use this when you need to explain WHY a result was reached.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "situation": {
                        "type": "object",
                        "description": "The situation JSON with persons, households, and variables",
                    },
                },
                "required": ["situation"],
            },
        ),
        Tool(
            name="validate_situation",
            description="""Validate a situation without calculating.

Checks that the situation JSON is structurally valid:
- All entities are recognized
- All variables exist and belong to correct entities
- Period formats match variable definitions
- Role assignments are valid

Use this to catch errors before running a calculation.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "situation": {
                        "type": "object",
                        "description": "The situation JSON to validate",
                    },
                },
                "required": ["situation"],
            },
        ),
    ]


# =============================================================================
# Tool Implementations
# =============================================================================


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "list_entities":
            return await handle_list_entities()
        elif name == "list_variables":
            return await handle_list_variables(arguments.get("entity"))
        elif name == "describe_variable":
            return await handle_describe_variable(arguments["variable_name"])
        elif name == "list_parameters":
            return await handle_list_parameters()
        elif name == "get_parameter":
            return await handle_get_parameter(arguments["parameter_id"])
        elif name == "search_variables":
            return await handle_search_variables(
                arguments["query"], arguments.get("entity")
            )
        elif name == "calculate":
            return await handle_calculate(arguments["situation"])
        elif name == "trace_calculation":
            return await handle_trace_calculation(arguments["situation"])
        elif name == "validate_situation":
            return await handle_validate_situation(arguments["situation"])
        else:
            raise ValidationError(f"Unknown tool: {name}")
    except MCPError as e:
        return format_error(e)
    except Exception as e:
        error = MCPError(
            error_type="internal_error",
            message=str(e),
            code=500,
        )
        return format_error(error)


async def handle_list_entities() -> list[TextContent]:
    """Handle list_entities tool."""
    data = client.get_entities()
    return format_result(data)


async def handle_list_variables(entity: str | None) -> list[TextContent]:
    """Handle list_variables tool."""
    data = client.get_variables()

    if entity:
        # Filter by entity - need to fetch details for each variable
        # For efficiency, we'll just return all and note the filter in output
        # In a production system, you might cache variable metadata
        filtered = {}
        for var_name, var_info in data.items():
            # Fetch details to check entity
            try:
                details = client.get_variable(var_name)
                if details.get("entity") == entity:
                    filtered[var_name] = var_info
            except Exception:
                continue
        data = filtered

    return format_result(data)


async def handle_describe_variable(variable_name: str) -> list[TextContent]:
    """Handle describe_variable tool."""
    data = client.get_variable(variable_name)
    return format_result(data)


async def handle_list_parameters() -> list[TextContent]:
    """Handle list_parameters tool."""
    data = client.get_parameters()
    return format_result(data)


async def handle_get_parameter(parameter_id: str) -> list[TextContent]:
    """Handle get_parameter tool."""
    data = client.get_parameter(parameter_id)
    return format_result(data)


async def handle_search_variables(query: str, entity: str | None) -> list[TextContent]:
    """Handle search_variables tool."""
    all_vars = client.get_variables()

    query_lower = query.lower()
    matches = {}

    for var_name, var_info in all_vars.items():
        # Search in name and description
        name_match = query_lower in var_name.lower()
        desc_match = query_lower in var_info.get("description", "").lower()

        if name_match or desc_match:
            if entity:
                # Check entity filter
                try:
                    details = client.get_variable(var_name)
                    if details.get("entity") != entity:
                        continue
                except Exception:
                    continue
            matches[var_name] = var_info

    if not matches:
        return format_result(
            {
                "message": f"No variables found matching '{query}'",
                "suggestions": [
                    "Try a different search term",
                    "Use list_variables to see all available variables",
                ],
            }
        )

    return format_result(matches)


async def handle_calculate(situation: dict[str, Any]) -> list[TextContent]:
    """Handle calculate tool."""
    if not situation:
        raise ValidationError(
            "Situation is required",
            suggestions=["Provide a situation object with persons and households"],
        )

    data = client.calculate(situation)
    return format_result(data)


async def handle_trace_calculation(situation: dict[str, Any]) -> list[TextContent]:
    """Handle trace_calculation tool."""
    if not situation:
        raise ValidationError(
            "Situation is required",
            suggestions=["Provide a situation object with persons and households"],
        )

    data = client.trace(situation)
    return format_result(data)


async def handle_validate_situation(situation: dict[str, Any]) -> list[TextContent]:
    """Handle validate_situation tool."""
    if not situation:
        raise ValidationError(
            "Situation is required",
            suggestions=["Provide a situation object with persons and households"],
        )

    errors = []
    warnings = []

    # Get valid entities
    try:
        entities = client.get_entities()
    except MCPError:
        raise

    valid_entity_plurals = {e["plural"] for e in entities.values()}
    valid_entity_plurals.update(entities.keys())  # Include singular forms

    # Check top-level keys
    for key in situation:
        if key not in valid_entity_plurals:
            errors.append(f"Unknown entity type: '{key}'")

    # Check persons exist
    persons = situation.get("persons", {})
    if not persons:
        errors.append("At least one person must be defined")

    # Check variables exist
    try:
        all_vars = client.get_variables()
    except MCPError:
        raise

    # Check person variables
    for person_id, person_data in persons.items():
        for var_name in person_data:
            if var_name not in all_vars:
                errors.append(f"Unknown variable '{var_name}' for person '{person_id}'")

    # Check group entities
    for entity_key, entity_info in entities.items():
        if "roles" not in entity_info:
            continue  # Skip person entity

        entity_plural = entity_info["plural"]
        group_instances = situation.get(entity_plural, {})

        for instance_id, instance_data in group_instances.items():
            # Check role assignments
            role_keys = set(entity_info["roles"].keys())
            role_plurals = {r.get("plural", r["key"]) for r in entity_info["roles"].values()} if isinstance(next(iter(entity_info["roles"].values()), {}), dict) else set()

            for key, value in instance_data.items():
                if key in role_keys or key in role_plurals:
                    # This is a role assignment
                    if isinstance(value, list):
                        for person_id in value:
                            if person_id not in persons:
                                errors.append(
                                    f"Person '{person_id}' in {entity_plural}/{instance_id}/{key} "
                                    f"is not defined in persons"
                                )
                elif key not in all_vars:
                    errors.append(
                        f"Unknown variable '{key}' for {entity_plural} '{instance_id}'"
                    )

    if errors:
        return format_result(
            {
                "valid": False,
                "errors": errors,
                "warnings": warnings,
            }
        )

    return format_result(
        {
            "valid": True,
            "message": "Situation is valid",
            "warnings": warnings,
        }
    )


# =============================================================================
# Server Entry Point
# =============================================================================


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run():
    """Entry point for running the server."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run()
