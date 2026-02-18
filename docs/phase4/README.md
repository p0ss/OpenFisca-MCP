# Phase 4: Cross-Package Verification

This directory contains the results of testing MCP tools against real country packages.

## Documents

| Document | Description |
|----------|-------------|
| [compatibility-report.md](compatibility-report.md) | Full compatibility analysis |

## Key Findings

### openfisca-france: Compatible

- 4-entity model (vs 2 in country-template)
- ~2,776 variables, ~3,958 parameters
- All MCP tools work without modification
- 14 compatibility tests passing

### openfisca-aotearoa: Compatible

- 5-entity model with property entities (tenancy, ownership, titled_property)
- ~326 variables, ~58 parameters
- DAY period for age (vs MONTH in France)
- 17 compatibility tests passing
- Required: patch `pyproject.toml` to allow core `>=41.4.5, <45`

## Conclusion

The MCP tools **generalize correctly** to complex country packages because they:
- Use dynamic entity/variable discovery
- Don't hardcode country-specific names
- Work through the standard OpenFisca API
- Handle different period types (DAY, WEEK, MONTH, YEAR)

Both France and Aotearoa work with core 44.x after dependency constraint updates.
