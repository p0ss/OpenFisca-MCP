# get_parameter

Get a parameter's value and history.

## Description

Returns the parameter's values at different dates, including simple values or tax brackets with thresholds and rates.

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "parameter_id": {
      "type": "string",
      "description": "The parameter ID (e.g., 'taxes.income_tax_rate')"
    }
  },
  "required": ["parameter_id"]
}
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `parameter_id` | string | Yes | The parameter ID from list_parameters |

## Output - Simple Value

```json
{
  "id": "benefits.basic_income",
  "description": "Basic income amount",
  "metadata": {"unit": "currency-EUR"},
  "values": {
    "2015-01-01": 500,
    "2016-01-01": 550,
    "2017-01-01": 600
  }
}
```

## Output - Tax Scale (Brackets)

```json
{
  "id": "taxes.social_security_contribution",
  "description": "Social security contribution scale",
  "metadata": {"threshold_unit": "currency-EUR"},
  "brackets": {
    "2017-01-01": {
      "0.0": 0.03,
      "12000.0": 0.10,
      "48000.0": 0.15
    }
  }
}
```

For scales, the format is `{threshold: rate}`.

## Output - Parameter Node

```json
{
  "id": "taxes",
  "description": "Tax parameters",
  "subparams": {
    "income_tax_rate": {"description": "..."},
    "social_security": {"description": "..."}
  }
}
```

Nodes have children; use their IDs to get specific parameters.

## Example Usage

```json
{"parameter_id": "taxes.income_tax_rate"}
```

## Error Cases

| Error | Cause |
|-------|-------|
| `not_found_error` | Parameter doesn't exist |
| `connection_error` | Cannot reach OpenFisca server |

## Notes

- Values are keyed by their effective date
- Find the applicable value by finding the latest date <= your calculation date
- Scales show bracket thresholds and corresponding rates
