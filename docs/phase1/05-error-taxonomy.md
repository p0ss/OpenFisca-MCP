# OpenFisca Error Taxonomy

## Overview

This document catalogs all error types in OpenFisca, their triggers, HTTP status codes, and response formats. This informs a consistent error schema for MCP tools.

## Error Categories

| Category | HTTP Code | Description |
|----------|-----------|-------------|
| Validation | 400 | Input validation failures |
| Not Found | 404 | Resource doesn't exist |
| Dependency | 500 | Circular/spiral dependencies |
| Configuration | 500 | System configuration errors |
| Internal | 500 | Unhandled exceptions |

## Core Error Classes

### Variable Errors

#### VariableNotFoundError

**Location:** `openfisca_core/errors/variable_not_found_error.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Variable not defined in TaxBenefitSystem |
| HTTP Status | 404 |
| Attributes | `message`, `variable_name` |

**Example:**
```
You tried to calculate or to set a value for variable 'unknown_var',
but it was not found in the loaded tax and benefit system (country_package@version).
```

#### VariableNameConflictError

**Location:** `openfisca_core/errors/variable_name_config_error.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Two variables with same name added to system |
| HTTP Status | 500 |
| When | System initialization |

### Period Errors

#### PeriodMismatchError

**Location:** `openfisca_core/errors/period_mismatch_error.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Variable value set for wrong period type |
| HTTP Status | 400 |
| Attributes | `variable_name`, `period`, `definition_period`, `message` |

**Example scenarios:**
- Setting monthly variable for annual period
- Setting annual variable with ETERNITY

#### PeriodError

**Location:** `openfisca_core/periods/_errors.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Invalid period format |
| HTTP Status | 400 |

**Example:**
```
Expected a period (eg. '2017', 'month:2017-01', 'week:2017-W01-1:3', ...);
got: 'invalid period'.
```

#### InstantError

**Location:** `openfisca_core/periods/_errors.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Invalid instant/date format |
| HTTP Status | 400 |
| Accepted Formats | `YYYY-MM-DD`, `YYYY-Www-D` |

### Situation Parsing Errors

#### SituationParsingError

**Location:** `openfisca_core/errors/situation_parsing_error.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Input data cannot be parsed |
| HTTP Status | 400 (or custom) |
| Attributes | `error` (dict), `code` |

**Common triggers:**

| Scenario | Path Pattern | Example Message |
|----------|--------------|-----------------|
| Invalid JSON | Root | `{"error": "Invalid JSON: ..."}` |
| Wrong root type | Root | `Invalid type: must be of type 'Object'` |
| No persons | `persons` | `At least one person must be defined` |
| Unknown entity | Entity name | `Some entities are not found: dogs` |
| Unknown variable | `entity/id/var` | `You tried to calculate or to set...` |
| Wrong entity for variable | `entity/id/var` | `You tried to compute 'X' for entity 'Y'...` |
| Missing period | `entity/id/var` | `Can't deal with type: expected object` |
| Invalid value type | `entity/id/var/period` | `expected type number, received 'abc'` |
| Invalid date | `entity/id/var/period` | `Can't deal with date: '2017-13-45'` |
| Unknown person in role | `entity/id/role` | `unknown_id has not been declared in persons` |
| Duplicate in role | `entity/id/role` | `has been declared more than once` |

### Circular Dependency Errors

#### CycleError

**Location:** `openfisca_core/errors/cycle_error.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Direct circular dependency in formula |
| HTTP Status | 500 |

**Example:**
```
Circular definition detected on formula variable_name@2017-12
```

#### SpiralError

**Location:** `openfisca_core/errors/spiral_error.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Quasi-circular dependency exceeds threshold |
| HTTP Status | 500 |
| Threshold | `max_spiral_loops` iterations |

**Example:**
```
Quasicircular definition detected on formula variable_name@2017-12
involving [variable_stack]
```

### Parameter Errors

#### ParameterNotFoundError

**Location:** `openfisca_core/errors/parameter_not_found_error.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Parameter not found at given instant |
| HTTP Status | 500 |
| Attributes | `name`, `instant_str`, `variable_name` |

**Example:**
```
The parameter 'income_tax.rate' requested by variable 'income_tax'
was not found in the 2017-12-31 tax and benefit system.
```

#### ParameterParsingError

**Location:** `openfisca_core/errors/parameter_parsing_error.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Error parsing parameter YAML/JSON files |
| HTTP Status | 500 |
| Attributes | `message`, `file`, `traceback` |

### Enum Errors

#### EnumEncodingError

**Location:** `openfisca_core/indexed_enums/_errors.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Enum value encoded with unsupported type |
| HTTP Status | 400 |

**Example:**
```
Failed to encode "[b'TENANT']" of type 'bytes', as it is not supported.
```

#### EnumMemberNotFoundError

**Location:** `openfisca_core/indexed_enums/_errors.py`

| Attribute | Value |
|-----------|-------|
| Trigger | Enum member not in definition |
| HTTP Status | 400 |

**Example:**
```
Some members were not found in enum 'HouseholderStatus'.
Possible values are: TENANT, OWNER, OTHER; or their indices: 0, 1, 2.
```

### Population Errors

#### IncompatibleOptionsError

| Trigger | Incompatible options (e.g., 'add' and 'divide') |
| HTTP Status | 400 |

#### InvalidOptionError

| Trigger | Invalid option for variable |
| HTTP Status | 400 |

#### InvalidArraySizeError

| Trigger | Array size doesn't match entity count |
| HTTP Status | 400 |

#### PeriodValidityError

| Trigger | Calculation without period |
| HTTP Status | 500 |

### Other Errors

#### EmptyArgumentError

| Trigger | Method called with empty argument |
| HTTP Status | 500 |

#### NaNCreationError

| Trigger | Calculation resulted in NaN |
| HTTP Status | 500 |

## Web API Error Handling

### Flask Error Handler

```python
@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        result = handlers.calculate(tax_benefit_system, input_data)
    except (SituationParsingError, PeriodMismatchError) as e:
        abort(make_response(jsonify(e.error), e.code or 400))
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        abort(make_response(
            jsonify({"error": "'" + e[1] + "' is not a valid ASCII value."}),
            400,
        ))
    return jsonify(result)
```

### Error Handling Pipeline

1. **Invalid JSON (400)** - Flask's JSON loading handler
2. **SituationParsingError (400/custom)** - Input validation
3. **PeriodMismatchError (400/custom)** - Period validation
4. **Unicode Errors (400)** - Encoding issues
5. **Unhandled (500)** - Generic error handler

## Response Formats

### Simple Error (Top-Level)

```json
{
  "error": "Invalid JSON: Expecting value: line 1 column 2 (char 1)"
}
```

**Used for:**
- Invalid JSON syntax
- Internal server errors
- Unicode encoding errors

### Nested Error (Field-Level)

```json
{
  "persons/bob/salary": "Can't deal with value: expected type number, received 'abc'",
  "households/household/adults": "has been declared more than once"
}
```

**Path structure:** `entity_plural/entity_id/variable_name[/period]`

**Used for:**
- SituationParsingError
- PeriodMismatchError
- Field-specific validation

## Error Summary Table

| Error | Class | Category | HTTP | Response |
|-------|-------|----------|------|----------|
| Variable not found | VariableNotFoundError | not_found | 404 | Nested |
| Period mismatch | PeriodMismatchError | validation | 400 | Nested |
| Invalid input | SituationParsingError | validation | 400 | Nested |
| Circular dependency | CycleError | dependency | 500 | Simple |
| Quasi-circular | SpiralError | dependency | 500 | Simple |
| Parameter not found | ParameterNotFoundError | not_found | 500 | Simple |
| Invalid period | PeriodError | validation | 400 | Simple |
| Invalid date | InstantError | validation | 400 | Simple |
| Enum error | EnumEncodingError | validation | 400 | Simple |

## Recommended MCP Error Schema

Based on this analysis, a consistent error schema for MCP tools:

```json
{
  "error": {
    "type": "validation_error|not_found_error|dependency_error|internal_error",
    "code": 400,
    "message": "Human-readable error message",
    "details": {
      "field_path": "persons/bob/salary/2017-01",
      "variable": "salary",
      "expected": "number",
      "received": "string"
    },
    "suggestions": [
      "Check the variable name spelling",
      "Ensure the period format is correct (YYYY-MM)"
    ]
  }
}
```

### Error Types

| Type | Description | HTTP |
|------|-------------|------|
| `validation_error` | Input validation failed | 400 |
| `not_found_error` | Resource not found | 404 |
| `dependency_error` | Circular formula dependency | 500 |
| `configuration_error` | System config issue | 500 |
| `internal_error` | Unhandled exception | 500 |
