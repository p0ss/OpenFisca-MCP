# list_parameters

List all parameters in the tax-benefit system.

## Description

Parameters are the rates, thresholds, and amounts defined in legislation that change over time. Use `get_parameter` to see historical values.

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
  "taxes.income_tax_rate": {
    "description": "Income tax rate",
    "href": "http://localhost:5000/parameter/taxes.income_tax_rate"
  },
  "benefits.basic_income": {
    "description": "Basic income amount",
    "href": "http://localhost:5000/parameter/benefits.basic_income"
  }
}
```

## Notes

- Parameter IDs use dot notation (e.g., `taxes.income_tax_rate`)
- Use `get_parameter` to see actual values and history
- Parameters can be simple values or tax scales with brackets

## Error Cases

| Error | Cause |
|-------|-------|
| `connection_error` | Cannot reach OpenFisca server |
