# OpenFisca Entity Model

## Overview

OpenFisca defines two main entity types that form the foundation of all tax-benefit calculations.

## Entity Types

### Single Entity (Person)

The minimal legal entity on which legislation can be applied.

**Characteristics:**
- `is_person = True`
- Cannot contain other entities
- Represents individuals (persons, companies, organizations)

**Definition:**
```python
Person = build_entity(
    key="person",
    plural="persons",
    label="An individual. The minimal entity on which legislation can be applied.",
    doc="...",
    is_person=True,
)
```

### Group Entity

Contains multiple single entities with different roles.

**Characteristics:**
- `is_person = False`
- Collects individuals under different roles
- Variables apply to the group as a whole

**Definition:**
```python
Household = build_entity(
    key="household",
    plural="households",
    label="All the people in a family or group who live together.",
    doc="...",
    roles=[
        {
            "key": "adult",
            "plural": "adults",
            "label": "Adult",
            "doc": "The adults of the household.",
        },
        {
            "key": "child",
            "plural": "children",
            "label": "Child",
            "doc": "The non-adults of the household.",
        },
    ],
)
```

## Roles

Roles define how persons participate in group entities.

### Role Properties

| Property | Required | Description |
|----------|----------|-------------|
| `key` | Yes | Identifier (e.g., "adult", "parent") |
| `plural` | No | Plural form (e.g., "adults", "parents") |
| `label` | No | Summary description |
| `doc` | No | Full description |
| `max` | No | Maximum persons with this role |
| `subroles` | No | Sub-division for indexed access |

### Subroles

Subroles allow indexed access to specific positions within a role:

```python
{
    "key": "parent",
    "subroles": ["first_parent", "second_parent"]
}
```

**Behavior:**
- Parent role's `max` is set to number of subroles
- Each subrole has `max=1`
- Accessible as `household.FIRST_PARENT`, `household.SECOND_PARENT`

## Entity Relationships

### Person to Group Entity

- Multiple persons can belong to a single group entity
- Each person has exactly one role per group entity
- Persons can belong to multiple different group entities

### Projectors

Projectors handle data transformations between entity perspectives:

| Projector | Direction | Example |
|-----------|-----------|---------|
| EntityToPersonProjector | Group → Person | `person.household("rent")` |
| FirstPersonToEntityProjector | Person → Group | `household.first_person` |
| UniqueRoleToEntityProjector | Role → Group | When role has `max=1` |

**Usage in formulas:**
```python
# From group to person: project household.housing_tax to each member
housing_tax = household("housing_tax", YEAR)
projected = household.project(housing_tax)

# From person to group: aggregate person.salary to household
salary = household.members("salary", "2016-01")
total_salary = household.sum(salary)
```

## Situation JSON Structure

### Standard Format

```json
{
  "persons": {
    "<person_id>": {
      "<variable_name>": {
        "<period>": <value>
      }
    }
  },
  "households": {
    "<household_id>": {
      "<role_key>": ["<person_id>", ...],
      "<variable_name>": {
        "<period>": <value>
      }
    }
  }
}
```

### Single Person Example

```json
{
  "persons": {
    "Alicia": {
      "birth": {
        "2017-01": null
      }
    }
  },
  "households": {
    "_": {
      "adults": ["Alicia"],
      "disposable_income": {
        "2017-01": null
      }
    }
  }
}
```

### Couple Example

```json
{
  "persons": {
    "Alicia": {
      "birth": {"ETERNITY": "1980-01-01"},
      "salary": {"2017-01": 4000}
    },
    "Javier": {
      "birth": {"ETERNITY": "1984-01-01"},
      "salary": {"2017-01": 2500}
    }
  },
  "households": {
    "_": {
      "adults": ["Alicia", "Javier"],
      "disposable_income": {"2017-01": null}
    }
  }
}
```

### Multi-Household Example

```json
{
  "persons": {
    "ind0": {},
    "ind1": {},
    "ind2": {},
    "ind3": {},
    "ind4": {},
    "ind5": {}
  },
  "households": {
    "h1": {
      "adults": ["ind0", "ind1"],
      "children": ["ind2", "ind3"]
    },
    "h2": {
      "adults": ["ind4"],
      "children": ["ind5"]
    }
  }
}
```

## Period Specification

Periods in situations can be:

| Format | Example | Description |
|--------|---------|-------------|
| Year | `"2017"` | Full year |
| Month | `"2017-01"` | Specific month |
| Day | `"2017-01-15"` | Specific day |
| ETERNITY | `"ETERNITY"` | Values that never change |
| null | `null` | Request calculation |

## Internal Processing

When a simulation is built from a situation, the following structures are created:

```python
# Entity IDs
entity_ids = {"persons": ["ind0", "ind1"], "households": ["h1", "h2"]}

# Entity counts
entity_counts = {"persons": 6, "households": 2}

# Memberships - which group entity each person belongs to
memberships = {"households": [0, 0, 0, 0, 1, 1]}

# Roles - what role each person has
roles = {"households": [ADULT, ADULT, CHILD, CHILD, ADULT, CHILD]}
```

## Role Constraints

### Maximum Enforcement

```python
if role.max is not None and len(persons_with_role) > role.max:
    raise SituationParsingError(
        f"There can be at most {role.max} {role_plural} in a {entity.key}. "
        f"{len(persons_with_role)} were declared in '{instance_id}'."
    )
```

### Subrole Assignment

When processing subroles, persons are assigned in order:
- 1st person in list → `first_parent` subrole
- 2nd person in list → `second_parent` subrole

## Key Files

| File | Purpose |
|------|---------|
| `openfisca_core/entities/entity.py` | Single/Person Entity |
| `openfisca_core/entities/group_entity.py` | Group Entity |
| `openfisca_core/entities/role.py` | Role class |
| `openfisca_core/entities/helpers.py` | `build_entity()` helper |
| `openfisca_core/simulations/simulation_builder.py` | Situation parsing |
| `openfisca_core/projectors/helpers.py` | Entity projections |
