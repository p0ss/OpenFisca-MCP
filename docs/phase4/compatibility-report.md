# Phase 4: Compatibility Report

## Summary

| Package | Core Version | Entities | Variables | Parameters | MCP Compatible |
|---------|--------------|----------|-----------|------------|----------------|
| country-template | >=43 | 2 | 19 | ~20 | Yes (baseline) |
| openfisca-france | >=43, <45 | 4 | ~2,776 | ~3,958 | **Yes** |
| openfisca-aotearoa | >=41.4.5, <45 | 5 | ~326 | ~58 | **Yes** |

## openfisca-france

### Status: Compatible

All 14 compatibility tests pass. The MCP tools handle France's more complex model correctly.

### Entity Model

France uses 4 entities instead of country-template's 2:

| Entity | Plural | Roles |
|--------|--------|-------|
| individu | individus | (none - person entity) |
| famille | familles | parent (max 2), enfant |
| foyer_fiscal | foyers_fiscaux | declarant (max 2), personne_a_charge |
| menage | menages | personne_de_reference (max 1), conjoint (max 1), enfant, autre |

### Key Differences Handled

1. **4-entity model**: MCP tools correctly enumerate all entities and roles
2. **French naming**: `individu` instead of `person`, `salaire_de_base` instead of `salary`
3. **Multiple group entities**: famille, foyer_fiscal, and menage all work
4. **Complex role structure**: Subroles and max constraints respected
5. **Scale**: 2,776 variables and 3,958 parameters returned efficiently

### Situation Structure

France situations require all 4 entities:

```json
{
  "individus": {
    "personne1": {
      "date_naissance": {"ETERNITY": "1990-01-01"},
      "salaire_de_base": {"2024-01": 2500}
    }
  },
  "familles": {
    "famille1": {"parents": ["personne1"]}
  },
  "foyers_fiscaux": {
    "foyer1": {"declarants": ["personne1"]}
  },
  "menages": {
    "menage1": {"personne_de_reference": ["personne1"]}
  }
}
```

### Verified Calculations

- Age calculation from `date_naissance`
- Couple scenarios with two declarants
- Tracing with dependency information

## openfisca-aotearoa

### Status: Compatible

All 17 compatibility tests pass. The package works with openfisca-core 44.x after updating the dependency constraint.

**Fix applied**: Changed `openfisca-core <42` to `>=41.4.5, <45` in `pyproject.toml`.

### Entity Model

Aotearoa defines 5 entities:

| Entity | Plural | Roles |
|--------|--------|-------|
| person | persons | (none - person entity) |
| family | families | principal (max 1), partner, parent, child, other |
| tenancy | tenancies | principal (max 1), tenant, other |
| ownership | ownerships | principal (max 1), owner, other |
| titled_property | titled_properties | owner, other |

### Unique Characteristics

1. **Property entities**: Tenancy, Ownership, Titled_Property are unusual group entities for property modeling
2. **DAY periods**: Age variable uses DAY definition period (unlike France's MONTH)
3. **WEEK periods**: Many benefit variables use WEEK definition period
4. **NZ-specific rules**: ACC (Accident Compensation), immigration rules
5. **Minimal situations**: Only required entities need to be included (e.g., just persons + families)

### Key Differences from France

| Aspect | France | Aotearoa |
|--------|--------|----------|
| Age period | MONTH (`2024-01`) | DAY (`2024-06-15`) |
| Entity count | 4 (individu, famille, foyer_fiscal, menage) | 5 (person, family, tenancy, ownership, titled_property) |
| Required entities | All 4 must be present | Only needed entities |
| Role format | Singular key with list (`"declarants": ["p1"]`) | Singular for max=1 (`"principal": "p1"`) |

### Situation Structure

Aotearoa situations can be minimal:

```json
{
  "persons": {
    "person1": {
      "date_of_birth": {"ETERNITY": "1990-01-01"},
      "age": {"2024-06-15": null}
    }
  },
  "families": {
    "family1": {
      "principal": "person1"
    }
  }
}
```

### Verified Calculations

- Age calculation with DAY periods
- Family structures with principal and partners
- Tracing with dependency information

## MCP Tool Compatibility Notes

### Works Across Packages

| Tool | country-template | france |
|------|------------------|--------|
| list_entities | ✅ | ✅ (4 entities) |
| list_variables | ✅ | ✅ (2,776 vars) |
| describe_variable | ✅ | ✅ |
| list_parameters | ✅ | ✅ (3,958 params) |
| get_parameter | ✅ | ✅ |
| search_variables | ✅ | ✅ |
| calculate | ✅ | ✅ |
| trace_calculation | ✅ | ✅ |
| validate_situation | ✅ | ✅ |

### No Code Changes Required

The MCP tools generalize without modification because:

1. They use the API, not hardcoded entity/variable names
2. Entity and role discovery is dynamic via `/entities`
3. Variable metadata comes from `/variable/{id}`
4. No assumptions about specific variables or periods

### Recommendations

1. **Document entity differences**: Users need to know France has 4 entities
2. **Provide country-specific examples**: Situation templates differ significantly
3. **Test WEEK periods**: When Aotearoa is updated, verify WEEK period handling
4. **Consider version detection**: Tool could warn about incompatible core versions

## Test Results

### country-template
- 40 tests passing (21 baseline + 19 MCP)

### openfisca-france
- 14 compatibility tests passing
- Entities, variables, parameters, calculate, trace all verified
- Run with: `poetry run openfisca serve -c openfisca_france -p 5051 &`

### openfisca-aotearoa
- 17 compatibility tests passing
- 5-entity model fully supported
- DAY period handling verified
- Run with: `poetry run openfisca serve -c openfisca_aotearoa -p 5052 &`

## Files

- `tests/test_france_compatibility.py` - France test suite (14 tests)
- `tests/test_aotearoa_compatibility.py` - Aotearoa test suite (17 tests)
- `country-packages/openfisca-france/` - Cloned France package
- `country-packages/openfisca-aotearoa/` - Cloned Aotearoa package (patched for core 44.x)
