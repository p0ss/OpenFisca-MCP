# Phase 4: Compatibility Report

## Summary

| Package | Core Version | Entities | Variables | Parameters | MCP Compatible |
|---------|--------------|----------|-----------|------------|----------------|
| country-template | >=43 | 2 | 19 | ~20 | Yes (baseline) |
| openfisca-france | >=43, <45 | 4 | ~2,776 | ~3,958 | **Yes** |
| openfisca-aotearoa | <42 | 5 | ~326 | ~58 | **No** (version skew) |

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

### Status: Not Compatible (Version Skew)

**Critical Issue**: Package requires `openfisca-core <42` but we have version 44.x

### Entity Model

Aotearoa defines 5 entities:

| Entity | Roles |
|--------|-------|
| Person | (none - person entity) |
| Family | principal (max 1), partner, parent, child, other |
| Tenancy | principal, tenant, other |
| Ownership | principal, owner, other |
| Titled_Property | owner, other |

### Unique Characteristics

1. **Property entities**: Tenancy, Ownership, Titled_Property are unusual
2. **WEEK periods**: 226+ variables use WEEK definition period
3. **NZ-specific rules**: ACC (Accident Compensation), immigration rules
4. **Extensive discretionary rules**: Many "not coded" placeholders

### Required Migration

To make Aotearoa compatible:

1. **Update core dependency**: Migrate from `openfisca-core <42` to `>=43`
2. **Fix period imports**: Standardize `periods.DateUnit.WEEK` vs `periods.WEEK`
3. **Review API changes**: Check `set_input_dispatch_by_period` compatibility
4. **Test formula routing**: Verify date-versioned formulas work

### API Differences (41.x → 44.x)

| Area | Potential Change |
|------|------------------|
| Period enums | `periods.WEEK` → `periods.DateUnit.WEEK` |
| Holder methods | `set_input_dispatch_by_period` signature |
| Variable class | Formula registration |
| TaxBenefitSystem | Initialization |

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

### openfisca-aotearoa
- Not tested (incompatible core version)
- Would require package update before testing

## Files

- `tests/test_france_compatibility.py` - France test suite
- `country-packages/openfisca-france/` - Cloned France package
- `country-packages/openfisca-aotearoa/` - Cloned Aotearoa package (incompatible)
