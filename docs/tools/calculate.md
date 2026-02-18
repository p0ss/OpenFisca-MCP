# calculate

Calculate variable values for a given situation.

## Description

Takes a situation (people, households, and their known values) and computes requested variables. This is the main calculation tool.

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

## Situation Structure

```json
{
  "persons": {
    "<person_id>": {
      "<variable>": {"<period>": <value_or_null>}
    }
  },
  "households": {
    "<household_id>": {
      "<role>": ["<person_id>", ...],
      "<variable>": {"<period>": <value_or_null>}
    }
  }
}
```

## Period Formats

**CRITICAL:** Use the correct format based on variable's `definitionPeriod`:

| definitionPeriod | Format | Example |
|------------------|--------|---------|
| MONTH | YYYY-MM | "2024-01" |
| YEAR | YYYY | "2024" |
| DAY | YYYY-MM-DD | "2024-01-15" |
| ETERNITY | ETERNITY | "ETERNITY" |

## Requesting Calculations

Set a variable's value to `null` to request calculation:

```json
{
  "persons": {
    "alice": {
      "salary": {"2024-01": 3000},
      "income_tax": {"2024-01": null}
    }
  }
}
```

## Example - Single Person

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
        "adults": ["alice"],
        "rent": {"2024-01": 800}
      }
    }
  }
}
```

## Example - Family

```json
{
  "situation": {
    "persons": {
      "parent1": {
        "birth": {"ETERNITY": "1980-05-12"},
        "salary": {"2024-01": 5000}
      },
      "parent2": {
        "birth": {"ETERNITY": "1982-09-25"},
        "salary": {"2024-01": 3000}
      },
      "child1": {
        "birth": {"ETERNITY": "2015-03-10"},
        "salary": {"2024-01": 0}
      }
    },
    "households": {
      "family": {
        "adults": ["parent1", "parent2"],
        "children": ["child1"],
        "total_taxes": {"2024-01": null},
        "total_benefits": {"2024-01": null}
      }
    }
  }
}
```

## Output

Same structure as input with calculated values:

```json
{
  "persons": {
    "alice": {
      "salary": {"2024-01": 3000},
      "income_tax": {"2024-01": 300.0}
    }
  },
  "households": {...}
}
```

## Error Cases

| Error | Cause | Suggestion |
|-------|-------|------------|
| `not_found_error` | Variable doesn't exist | Check spelling, use search_variables |
| `validation_error` | Wrong period format | Check variable's definitionPeriod |
| `validation_error` | Unknown entity | Use list_entities |
| `validation_error` | Person not declared | Define all persons before using in roles |

## Common Mistakes

1. **Wrong period format** - Using "2024" for a MONTH variable
2. **Missing person in roles** - Using a person ID that wasn't declared
3. **Variable on wrong entity** - Putting household variable under persons
4. **Missing required inputs** - Some variables need other variables set

## Notes

- Multiple variables can be calculated in one call
- Input values are preserved in output
- The `birth` variable uses ETERNITY period
- Salary and most financial variables use MONTH
- Annual taxes (like housing_tax) use YEAR
