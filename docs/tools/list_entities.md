# list_entities

List all entity types in the tax-benefit system.

## Description

Returns the entity types (person, household, etc.) and their roles. Use this before constructing a situation to understand the required structure.

## Input Schema

```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

No parameters required.

## Output

```json
{
  "person": {
    "plural": "persons",
    "description": "An individual...",
    "documentation": "..."
  },
  "household": {
    "plural": "households",
    "description": "A household...",
    "documentation": "...",
    "roles": {
      "adult": {
        "plural": "adults",
        "description": "Adult members",
        "max": null
      },
      "child": {
        "plural": "children",
        "description": "Child members",
        "max": null
      }
    }
  }
}
```

## Key Fields

| Field | Description |
|-------|-------------|
| `plural` | Plural form used in situation JSON keys |
| `roles` | For group entities, defines valid role assignments |
| `max` | Maximum persons allowed in a role (null = unlimited) |

## Example Usage

Before constructing a situation, call this to understand:
1. What entity types exist (e.g., person, household)
2. What roles are available (e.g., adult, child)
3. The plural form to use as JSON keys

## Error Cases

| Error | Cause |
|-------|-------|
| `connection_error` | Cannot reach OpenFisca server |
