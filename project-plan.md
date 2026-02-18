openfisca-mcp
Build plan: wrapping OpenFisca as MCP tools using Claude Code agents

Approach
Use Claude Code agents to do the heavy lifting at each phase. The agents analyse the OpenFisca codebase, generate tool wrappers, write tests, and produce documentation as we go. Each tool is built, tested, and documented before moving on. The whole thing runs against real OpenFisca instances with real country packages, not mocks.

Phases
Phase 1 — Clone + analyse. Clone openfisca-core and a country package (country-template or openfisca-aotearoa). Run analysis agents across the codebase to map the Web API surface, entity model, variable/parameter schemas, and simulation lifecycle. Include analysis of error types returned by the API (missing variable, circular dependency, invalid period, malformed input) to inform a consistent error schema across all tools. Outputs: API surface map, entity model docs, error taxonomy, list of candidate MCP tools.
Phase 2 — Test instance. Spin up a local OpenFisca Web API instance against the country template. Populate with test situations and verify baseline API behaviour. Build a test harness that validates tool outputs against known-good API responses. Outputs: running instance, test fixtures, validation harness.
Phase 3 — Build tools. Run agents to generate MCP tool wrappers one at a time. Each tool gets built, tested against the harness, and documented before moving to the next. Start with read-only tools (list variables, get parameter, describe entity) then move to calculate. All tools should use the error schema defined in Phase 1, returning structured errors that let the LLM understand what went wrong and how to fix it (e.g., "variable not found" with suggestions, "invalid period format" with expected format). Outputs: MCP server with tested, documented tools.
Phase 4 — Verify on real rules. Swap in existing RaC country packages (Aotearoa NZ, France, etc.) and run the tool suite against them. Identify edge cases, missing capabilities, or assumptions baked into the country template that don't generalise. Watch for openfisca-core version skew between packages — different packages may pin different core versions with subtly different API behaviour. Outputs: compatibility report, version compatibility notes, fixes, updated docs.
Phase 5 — End-to-end demo. Connect an MCP client (Claude, or a local agent) and run through conversational eligibility scenarios against a real rule set. Record and document. Outputs: working demo, architecture docs.

Candidate tools (to be confirmed by Phase 1 analysis)
These are the likely tools based on the existing OpenFisca Web API surface. Phase 1 analysis may reveal others or suggest different groupings.
list_variables — Returns available variables, filterable by entity type. The LLM's entry point for discovering what the rule set can compute. Core, build first.
describe_variable — Returns a variable's definition period, value type, default, description, and formula source if available. Core, build first.
get_parameter — Retrieves a parameter's value at a given date, including its history. Lets the LLM look up thresholds and rates. Core, build first.
list_entities — Returns the entity types (person, household, etc.) and their roles. Needed before the LLM can construct a valid situation. Core, build first.
calculate — Accepts a situation JSON and one or more variables to compute. The main tool. Needs solid input validation and clear error messages. Tool description must be precise about period handling (monthly vs yearly variables, instant vs period values) as this is a common source of confusion. Error responses should use the consistent error schema from Phase 1 analysis. Core, after read tools.
trace_calculation — Runs a calculation with tracing enabled, returning the dependency tree. Lets the LLM explain why a result was reached. High priority, enables explainability.
search_variables — Fuzzy or keyword search across variable names and descriptions. Helps the LLM find the right variable when the user's language doesn't match the model's naming. High priority, usability.
list_parameters — Browse the parameter tree. Useful for exploring rate tables and thresholds. Medium.
validate_situation — Checks a situation JSON for structural validity before calculating. Saves round trips on malformed inputs. Medium.
scaffold_situation — Returns an empty situation template for given entity types and roles, with the required structure pre-filled. Reduces malformed input errors by giving the LLM a valid starting point. Lower priority — agents can likely construct situations from list_entities output early on, but this may help with complex multi-entity scenarios. Later phase.
batch_calculate — Compute multiple variables across a date range or multiple scenarios in a single call. Useful for "what-if" comparisons and time-series analysis. V2, once core tools are stable.

Documentation as we go
Each tool gets a doc page written at build time, not after the fact. The doc for each tool should cover: what it does, its input schema, its output schema, example calls and responses, error cases, and any assumptions about the underlying country package. These docs serve double duty — they're reference material for developers, and they become the tool descriptions that the MCP server exposes to LLM clients.

Period handling deserves special attention in the docs. OpenFisca's period logic (monthly vs yearly variables, instant vs period values, period syntax like "2024-01" vs "2024") is a common source of errors. Tool descriptions should be explicit about expected period formats and how the tool behaves when a variable's definition period doesn't match the requested period.

Verification against existing RaC bases
The country template is fine for building and unit testing, but the real proof is running against established rule sets. Candidate packages to verify against:
openfisca-aotearoa — NZ benefits, originated from the Service Innovation Lab Better Rules work.
openfisca-france — The most complete package, thousands of variables, good stress test for scale.
openfisca-nsw — NSW government rules, closest to the Services Australia context.
The goal is to confirm the tools generalise across different entity models, variable types, and parameter structures without country-specific assumptions leaking in.
