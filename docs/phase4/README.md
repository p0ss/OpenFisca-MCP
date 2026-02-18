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

### openfisca-aotearoa: Version Skew

- Requires openfisca-core <42 (we have 44.x)
- Cannot test until package is updated
- Unique features: WEEK periods, property entities, ACC rules

## Conclusion

The MCP tools **generalize correctly** to complex country packages because they:
- Use dynamic entity/variable discovery
- Don't hardcode country-specific names
- Work through the standard OpenFisca API

The only barrier is **core version compatibility**, which is a package maintainer responsibility.
