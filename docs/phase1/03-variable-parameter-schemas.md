# OpenFisca Variable and Parameter Schemas

## Variables

### Variable Attributes

#### Required Attributes

| Attribute | Description |
|-----------|-------------|
| `value_type` | Data type (see Value Types below) |
| `entity` | Entity this variable belongs to (Person, Household, etc.) |
| `definition_period` | Period granularity (MONTH, YEAR, DAY, ETERNITY) |

#### Value Types

| Type | NumPy Type | JSON Type | Default | Period-Size Independent |
|------|------------|-----------|---------|------------------------|
| `bool` | bool_ | boolean | False | Yes |
| `int` | int32 | integer | 0 | No |
| `float` | float32 | number | 0 | No |
| `str` | object | string | "" | Yes |
| `Enum` | ENUM_ARRAY_DTYPE | string | Required | Yes |
| `date` | datetime64[D] | string | 1970-01-01 | Yes |

#### Definition Periods

| Period | Description | Example |
|--------|-------------|---------|
| `DAY` | Granular daily calculations | Daily allowance |
| `MONTH` | Monthly (most common) | Salary, benefits |
| `YEAR` | Annual calculations | Tax liability |
| `ETERNITY` | Never changes | Birth date |

#### Optional Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `label` | str | Human-readable description |
| `reference` | str/list | Legislative references (URLs) |
| `default_value` | varies | Value when not explicitly set |
| `documentation` | str | Multi-line usage description |
| `unit` | str | Unit metadata (e.g., "currency-EUR") |
| `end` | str | Date variable is removed (YYYY-MM-DD) |
| `possible_values` | Enum | For Enum types, allowed values |
| `max_length` | int | For string types, max characters |
| `set_input` | function | Period conversion for inputs |
| `is_neutralized` | bool | If True, always returns default |

### Variable Definition Examples

**Input Variable (no formula):**
```python
class salary(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    set_input = set_input_divide_by_period
    label = "Salary"
```

**Computed Variable with Formulas:**
```python
class basic_income(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = "Basic income"

    def formula_2016_12(person, period, parameters):
        age_condition = person("age", period) >= 18
        return age_condition * parameters(period).benefits.basic_income

    def formula_2015_12(person, period, parameters):
        age_condition = person("age", period) >= 18
        salary_condition = person("salary", period) == 0
        return age_condition * salary_condition * parameters(period).benefits.basic_income
```

**Date Variable (ETERNITY):**
```python
class birth(Variable):
    value_type = date
    default_value = date(1970, 1, 1)
    entity = Person
    definition_period = ETERNITY
    label = "Birth date"
```

**Enum Variable:**
```python
class housing_occupancy_status(Variable):
    value_type = Enum
    possible_values = HousingOccupancyStatus
    default_value = HousingOccupancyStatus.TENANT
    entity = Household
    definition_period = MONTH
    label = "Housing occupancy status"
```

### Formula Naming Convention

Formula methods are named to indicate their start date:

| Method Name | Start Date |
|-------------|------------|
| `formula` | 0001-01-01 (earliest) |
| `formula_2020` | 2020-01-01 |
| `formula_2020_03` | 2020-03-01 |
| `formula_2020_03_15` | 2020-03-15 |

### Variable JSON Serialization

API response format from `/variable/{id}`:

```json
{
  "id": "basic_income",
  "description": "Basic income provided to adults",
  "valueType": "Float",
  "defaultValue": 0,
  "definitionPeriod": "MONTH",
  "entity": "person",
  "source": "https://github.com/.../blob/v1.0.0/variables/benefits.py#L25-L30",
  "documentation": "Optional multi-line docs",
  "references": ["https://law.gov/basic-income"],
  "formulas": {
    "2016-12-01": {
      "source": "https://github.com/...",
      "content": "def formula_2016_12(person, period, parameters):\n    ..."
    },
    "2015-12-01": {
      "source": "...",
      "content": "..."
    }
  },
  "possibleValues": {
    "TENANT": "tenant",
    "OWNER": "owner"
  }
}
```

## Parameters

### Parameter Types

1. **Parameter** - Single value with time history
2. **ParameterNode** - Tree structure containing other parameters
3. **ParameterScale** - Tax scales with brackets

### Parameter Definition (YAML)

**Simple parameter with metadata:**
```yaml
description: Amount of the basic income
metadata:
  reference: https://law.gov/basic-income
  unit: currency-EUR
documentation: |
  Multi-line explanation
values:
  2015-12-01:
    value: 600.0
    metadata:
      reference: https://law.gov/basic-income/2015
  2016-01-01:
    value: 620.0
```

**Simplified format:**
```yaml
2015-01-01: 550
2016-01-01: 600
```

### Parameter Tree Structure

Parameters are organized hierarchically via directories:

```
parameters/
  benefits/
    index.yaml          # Node metadata
    basic_income.yaml   # Leaf parameter
    housing_allowance.yaml
    parenting_allowance/
      amount.yaml
      income_threshold.yaml
  taxes/
    income_tax_rate.yaml
```

### Parameter Scales (Tax Brackets)

```yaml
description: Social security contribution tax scale
metadata:
  threshold_unit: currency-EUR
  rate_unit: /1
brackets:
  - rate:
      2013-01-01:
        value: 0.03
      2015-01-01:
        value: 0.04
    threshold:
      2013-01-01:
        value: 0.0
  - rate:
      2013-01-01:
        value: 0.1
      2015-01-01:
        value: 0.12
    threshold:
      2013-01-01:
        value: 12000.0
```

### Parameter JSON Serialization

API response format from `/parameter/{id}`:

```json
{
  "id": "benefits/basic_income",
  "description": "Amount of the basic income",
  "metadata": {"unit": "currency-EUR"},
  "source": "https://github.com/...",
  "documentation": "Multi-line docs",
  "values": {
    "2015-12-01": 600.0,
    "2016-01-01": 620.0
  }
}
```

**For scales:**
```json
{
  "id": "taxes/social_security",
  "description": "Social security contribution",
  "brackets": {
    "2017-01-01": {
      "0.0": 0.04,
      "12400.0": 0.12
    },
    "2015-01-01": {
      "0.0": 0.03,
      "12000.0": 0.1
    }
  }
}
```

**For nodes:**
```json
{
  "id": "benefits",
  "description": "All benefit programs",
  "subparams": {
    "basic_income": {"description": "..."},
    "housing_allowance": {"description": "..."}
  }
}
```

## Period Handling

### Period Representation

Periods are 3-tuples: `(unit, start, size)`

```python
# String formats
"2021"           # year:2021-01-01:1 (full year)
"2021-10"        # month:2021-10-01:1 (one month)
"month:2021-10:3" # 3 months starting Oct 2021
```

### Period-Size Independence

Controls whether results change based on period length:

| Independent (True) | Dependent (False) |
|--------------------|-------------------|
| bool, str, date, Enum | int, float |
| Age is same all year | $1000/month * 12 = $12000/year |

### Input Period Conversion

When input period doesn't match definition_period:

```python
set_input = set_input_divide_by_period  # Spread annual over months
# 12000 annual → 1000/month
```

## Key Files

| File | Purpose |
|------|---------|
| `openfisca_core/variables/variable.py` | Variable class |
| `openfisca_core/variables/config.py` | VALUE_TYPES config |
| `openfisca_core/parameters/parameter.py` | Parameter class |
| `openfisca_core/parameters/parameter_node.py` | ParameterNode class |
| `openfisca_core/parameters/parameter_scale.py` | ParameterScale class |
| `openfisca_core/periods/period_.py` | Period class |
| `openfisca_web_api/loader/variables.py` | Variable JSON builder |
| `openfisca_web_api/loader/parameters.py` | Parameter JSON builder |
