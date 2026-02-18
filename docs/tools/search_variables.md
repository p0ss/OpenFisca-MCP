# search_variables

Search for variables by keyword.

## Description

Searches variable names and descriptions for matching terms. Use this when you don't know the exact variable name.

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search term (e.g., 'tax', 'allowance', 'income')"
    },
    "entity": {
      "type": "string",
      "description": "Filter by entity type (optional)"
    }
  },
  "required": ["query"]
}
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search term |
| `entity` | string | No | Filter to this entity type |

## Output

```json
{
  "income_tax": {
    "description": "Income tax",
    "href": "http://localhost:5000/variable/income_tax"
  },
  "housing_tax": {
    "description": "Tax paid by each household...",
    "href": "http://localhost:5000/variable/housing_tax"
  }
}
```

## Example Usage

**Search for tax-related variables:**
```json
{"query": "tax"}
```

**Search for person-level income variables:**
```json
{"query": "income", "entity": "person"}
```

## No Results Response

```json
{
  "message": "No variables found matching 'xyz'",
  "suggestions": [
    "Try a different search term",
    "Use list_variables to see all available variables"
  ]
}
```

## Notes

- Search is case-insensitive
- Matches both variable names and descriptions
- Use `describe_variable` to get full details for a match

## Error Cases

| Error | Cause |
|-------|-------|
| `connection_error` | Cannot reach OpenFisca server |
