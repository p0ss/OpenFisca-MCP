# OpenFisca Web API Surface

## Overview

The OpenFisca Web API is a Flask-based REST API that exposes the tax-benefit system for querying and calculation. All responses include headers `Country-Package` and `Country-Package-Version`.

## Endpoints

### 1. Root

**Path:** `/`
- **Method:** GET
- **Response Code:** 300 (Multiple Choices)
- **Response:**
  ```json
  {
    "welcome": "This is the root of an OpenFisca Web API..."
  }
  ```

### 2. Parameters

#### List Parameters

**Path:** `/parameters`
- **Method:** GET
- **Response Code:** 200
- **Response:**
  ```json
  {
    "taxes.income_tax_rate": {
      "description": "Income tax rate",
      "href": "http://localhost:5000/parameter/taxes.income_tax_rate"
    }
  }
  ```
- **Notes:** Lists only leaf parameters (excludes nodes with subparams)

#### Get Parameter Details

**Path:** `/parameter/{parameterID}`
- **Method:** GET
- **URL Parameters:** `parameterID` - Parameter ID (e.g., `taxes/income_tax_rate` or legacy `taxes.income_tax_rate`)
- **Response Codes:** 200 OK, 404 Not Found
- **Response:**
  ```json
  {
    "id": "taxes.income_tax_rate",
    "description": "Income tax rate",
    "metadata": {},
    "source": "https://github.com/.../blob/version/path#L1-L10",
    "documentation": "Optional multi-line docs",
    "values": {
      "2015-01-01": 0.15,
      "2016-01-01": 0.18
    },
    "brackets": {
      "2017-01-01": {
        "0.0": 0.03,
        "12000.0": 0.12
      }
    },
    "subparams": {
      "child_param": {
        "description": "Child parameter"
      }
    }
  }
  ```

### 3. Variables

#### List Variables

**Path:** `/variables`
- **Method:** GET
- **Response Code:** 200
- **Response:**
  ```json
  {
    "salary": {
      "description": "Salary",
      "href": "http://localhost:5000/variable/salary"
    }
  }
  ```

#### Get Variable Details

**Path:** `/variable/{variableID}`
- **Method:** GET
- **URL Parameters:** `variableID` - Variable name
- **Response Codes:** 200 OK, 404 Not Found
- **Response:**
  ```json
  {
    "id": "salary",
    "description": "Salary",
    "valueType": "Float",
    "defaultValue": 0,
    "definitionPeriod": "MONTH",
    "entity": "person",
    "source": "https://github.com/.../blob/version/path#L1-L10",
    "documentation": "Optional multi-line docs",
    "references": ["https://law.gov/..."],
    "formulas": {
      "2016-12-01": {
        "content": "def formula(person, period, parameters):\n    ...",
        "source": "https://github.com/..."
      }
    },
    "possibleValues": {
      "TENANT": "tenant",
      "OWNER": "owner"
    }
  }
  ```

### 4. Entities

**Path:** `/entities`
- **Method:** GET
- **Response Code:** 200
- **Response:**
  ```json
  {
    "person": {
      "plural": "persons",
      "description": "An individual",
      "documentation": "..."
    },
    "household": {
      "plural": "households",
      "description": "A household",
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

### 5. Calculate

**Path:** `/calculate`
- **Method:** POST
- **Content-Type:** application/json
- **Response Codes:** 200 OK, 400 Bad Request, 404 Not Found

**Request Body (SituationInput):**
```json
{
  "persons": {
    "person_id": {
      "salary": {
        "2017-01": 2000
      },
      "income_tax": {
        "2017-01": null
      }
    }
  },
  "households": {
    "household_id": {
      "adults": ["person_id"],
      "rent": {
        "2017-01": 800
      }
    }
  }
}
```

- Use `null` as value to request calculation
- Periods are ISO date strings (YYYY-MM or YYYY)

**Response Body:**
- Same structure as input with calculated values replacing nulls

### 6. Trace

**Path:** `/trace`
- **Method:** POST
- **Content-Type:** application/json
- **Response Codes:** 200 OK, 400 Bad Request, 404 Not Found

**Request Body:** Same as `/calculate`

**Response Body:**
```json
{
  "requestedCalculations": ["income_tax<2017-01>"],
  "entitiesDescription": {
    "persons": ["person_id"]
  },
  "trace": {
    "income_tax<2017-01>": {
      "value": [300],
      "dependencies": ["salary<2017-01>"],
      "parameters": {
        "taxes.income_tax_rate<2017-01-01>": 0.15
      }
    },
    "salary<2017-01>": {
      "value": [2000],
      "dependencies": [],
      "parameters": {}
    }
  }
}
```

### 7. Specification

**Path:** `/spec`
- **Method:** GET
- **Response Code:** 200
- **Response:** OpenAPI 3.0.0 specification (YAML structure)

## Error Response Format

**Simple errors (top-level):**
```json
{
  "error": "Invalid JSON: Expecting value..."
}
```

**Field-level errors:**
```json
{
  "persons/bob/salary/2017-01": "Can't deal with value: expected type number, received 'abc'"
}
```

## Response Headers

All responses include:
- `Country-Package`: Name of loaded country package
- `Country-Package-Version`: Version (semver format)

## Technical Details

- **Framework:** Flask
- **Server:** Gunicorn (production)
- **CORS:** Enabled for all origins
- **JSON:** UTF-8 encoding, non-ASCII preserved
- **URLs:** Strict slashes disabled
