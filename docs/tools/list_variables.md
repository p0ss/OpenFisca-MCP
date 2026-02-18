# list_variables

List all available variables in the tax-benefit system.

## Description

Returns variable names with descriptions. This is the entry point for discovering what the rule set can compute. Use `describe_variable` for full details.

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "entity": {
      "type": "string",
      "description": "Filter by entity type (e.g., 'person', 'household')"
    }
  },
  "required": []
}
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity` | string | No | Filter to variables belonging to this entity |

## Output

```json
{
  "salary": {
    "description": "Salary",
    "href": "http://localhost:5000/variable/salary"
  },
  "income_tax": {
    "description": "Income tax",
    "href": "http://localhost:5000/variable/income_tax"
  }
}
```

## Example Usage

**List all variables:**
```json
{}
```

**List only person variables:**
```json
{"entity": "person"}
```

**List only household variables:**
```json
{"entity": "household"}
```

## Notes

- Returns a summary; use `describe_variable` for full details
- The `href` field points to the API endpoint for details
- Filtering by entity requires fetching each variable's details, which may be slow for large rule sets

## Error Cases

| Error | Cause |
|-------|-------|
| `connection_error` | Cannot reach OpenFisca server |
