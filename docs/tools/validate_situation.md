# validate_situation

Validate a situation without calculating.

## Description

Checks that the situation JSON is structurally valid before running a calculation. Catches errors early without the overhead of actual computation.

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "situation": {
      "type": "object",
      "description": "The situation JSON to validate"
    }
  },
  "required": ["situation"]
}
```

## Output - Valid

```json
{
  "valid": true,
  "message": "Situation is valid",
  "warnings": []
}
```

## Output - Invalid

```json
{
  "valid": false,
  "errors": [
    "Unknown variable 'salry' for person 'alice'",
    "Person 'bob' in households/household1/adults is not defined in persons"
  ],
  "warnings": []
}
```

## Validation Checks

| Check | Error Message |
|-------|---------------|
| Unknown entity type | "Unknown entity type: 'companies'" |
| No persons defined | "At least one person must be defined" |
| Unknown variable | "Unknown variable 'xyz' for person 'alice'" |
| Person not declared | "Person 'bob' ... is not defined in persons" |

## Example Usage

```json
{
  "situation": {
    "persons": {
      "alice": {
        "salry": {"2024-01": 3000}
      }
    },
    "households": {
      "household1": {
        "adults": ["alice", "bob"]
      }
    }
  }
}
```

Response:
```json
{
  "valid": false,
  "errors": [
    "Unknown variable 'salry' for person 'alice'",
    "Person 'bob' in households/household1/adults is not defined in persons"
  ],
  "warnings": []
}
```

## When to Use

1. **Before calculate** - Catch typos and structural errors
2. **Building situations** - Validate as you construct
3. **User input** - Check user-provided situations

## Limitations

This tool checks:
- Entity types exist
- Variables exist
- Person IDs in roles are declared

This tool does NOT check:
- Period format correctness (use describe_variable)
- Value types (string vs number)
- Business logic constraints

## Error Cases

| Error | Cause |
|-------|-------|
| `validation_error` | Situation is empty or null |
| `connection_error` | Cannot reach OpenFisca server |
