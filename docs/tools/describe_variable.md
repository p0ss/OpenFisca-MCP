# describe_variable

Get detailed information about a specific variable.

## Description

Returns the variable's type, period, entity, formulas, and references. Critical for understanding how to use the variable in calculations.

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "variable_name": {
      "type": "string",
      "description": "The variable name (e.g., 'salary', 'income_tax')"
    }
  },
  "required": ["variable_name"]
}
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `variable_name` | string | Yes | The exact variable name |

## Output

```json
{
  "id": "income_tax",
  "description": "Income tax",
  "valueType": "Float",
  "defaultValue": 0,
  "definitionPeriod": "MONTH",
  "entity": "person",
  "source": "https://github.com/.../variables/taxes.py#L10-L25",
  "documentation": "Optional detailed docs",
  "references": ["https://law.gov/..."],
  "formulas": {
    "2015-01-01": {
      "source": "https://github.com/...",
      "content": "def formula(person, period, parameters):\n    ..."
    }
  }
}
```

## Key Fields

| Field | Description |
|-------|-------------|
| `valueType` | Float, Int, Boolean, String, or Date |
| `definitionPeriod` | **CRITICAL** - determines period format |
| `entity` | Which entity this variable belongs to |
| `formulas` | Calculation logic with start dates |
| `defaultValue` | Value when not set or calculated |

## Definition Period Mapping

| definitionPeriod | Period Format | Example |
|------------------|---------------|---------|
| MONTH | YYYY-MM | "2024-01" |
| YEAR | YYYY | "2024" |
| DAY | YYYY-MM-DD | "2024-01-15" |
| ETERNITY | ETERNITY | "ETERNITY" |

## Example Usage

```json
{"variable_name": "income_tax"}
```

## Error Cases

| Error | Cause |
|-------|-------|
| `not_found_error` | Variable doesn't exist |
| `connection_error` | Cannot reach OpenFisca server |

## Notes

- Always check `definitionPeriod` before using in calculate
- The `formulas` field shows the calculation logic
- Multiple formulas indicate the calculation changed over time
