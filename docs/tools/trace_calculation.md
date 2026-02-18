# trace_calculation

Calculate with full dependency tracing for explainability.

## Description

Like `calculate`, but returns a detailed trace showing which variables were computed, what they depended on, and what parameter values were used. Essential for explaining results.

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "situation": {
      "type": "object",
      "description": "The situation JSON with persons, households, and variables"
    }
  },
  "required": ["situation"]
}
```

## Output Structure

```json
{
  "requestedCalculations": ["income_tax<2024-01>"],
  "entitiesDescription": {
    "persons": ["alice"],
    "households": ["household1"]
  },
  "trace": {
    "income_tax<2024-01>": {
      "value": [300.0],
      "dependencies": ["salary<2024-01>"],
      "parameters": {
        "taxes.income_tax_rate<2024-01-01>": 0.1
      }
    },
    "salary<2024-01>": {
      "value": [3000],
      "dependencies": [],
      "parameters": {}
    }
  }
}
```

## Trace Entry Fields

| Field | Description |
|-------|-------------|
| `value` | Array of computed values (one per entity instance) |
| `dependencies` | Variables this calculation depends on |
| `parameters` | Parameter values used in the calculation |

## Example Usage

```json
{
  "situation": {
    "persons": {
      "alice": {
        "birth": {"ETERNITY": "1990-01-15"},
        "salary": {"2024-01": 3000},
        "income_tax": {"2024-01": null}
      }
    },
    "households": {
      "household1": {
        "adults": ["alice"]
      }
    }
  }
}
```

## Understanding the Trace

The trace shows the dependency graph:

```
income_tax<2024-01>
├── depends on: salary<2024-01>
└── uses parameter: taxes.income_tax_rate = 0.1

salary<2024-01>
└── (input value, no dependencies)
```

## Use Cases

1. **Explain results** - Show user why they got a specific amount
2. **Debug calculations** - Find which input affects the result
3. **Audit trail** - Document calculation logic
4. **Teaching** - Show how rules interact

## Error Cases

Same as `calculate`:

| Error | Cause |
|-------|-------|
| `not_found_error` | Variable doesn't exist |
| `validation_error` | Invalid situation structure |
| `connection_error` | Cannot reach OpenFisca server |

## Notes

- Trace includes ALL intermediate calculations
- Parameter keys include their effective date
- Values are arrays because each entity instance gets a value
- Useful for complex calculations with many dependencies
