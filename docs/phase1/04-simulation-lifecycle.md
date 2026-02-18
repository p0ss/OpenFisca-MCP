# OpenFisca Simulation Lifecycle

## Overview

This document traces how a calculation request flows through OpenFisca: from receiving situation JSON, through simulation creation, variable computation with dependency resolution, to returning results.

## Request Flow Diagram

```
HTTP POST /calculate
    │
    ▼
app.calculate()
    │
    ├── request.get_json() → input_data
    │
    ▼
handlers.calculate(tax_benefit_system, input_data)
    │
    ├── SimulationBuilder.build_from_entities()
    │       │
    │       ├── tax_benefit_system.instantiate_entities()
    │       ├── Simulation(tbs, populations)
    │       ├── parse persons & group entities
    │       └── finalize_variables_init() → set inputs in holders
    │
    ├── dpath.search() → find all null values (requested calculations)
    │
    ▼
    For each requested calculation:
    │
    └── simulation.calculate(variable_name, period)
            │
            ├── Check cache (FAST PATH)
            │   └── If cached: return cached_array
            │
            ├── Check for circular dependencies
            │
            ├── variable.get_formula(period)
            │   └── Search formulas by date
            │
            ├── formula(population, period, parameters_at)
            │   │
            │   └── RECURSION: formula may call
            │       ├── population.household.income → simulation.calculate()
            │       └── parameters.tax.rate → record parameter access
            │
            ├── Cast result to variable dtype
            ├── holder.put_in_cache(array, period)
            └── return array
    │
    ▼
dpath.merge(input_data, computation_results)
    │
    ▼
HTTP 200 OK + JSON response
```

## 1. Web API Layer

**File:** `openfisca_web_api/app.py`

### /calculate endpoint

```python
@app.route("/calculate", methods=["POST"])
def calculate():
    tax_benefit_system = data["tax_benefit_system"]
    input_data = request.get_json()
    try:
        result = handlers.calculate(tax_benefit_system, input_data)
    except (SituationParsingError, PeriodMismatchError) as e:
        abort(make_response(jsonify(e.error), e.code or 400))
    return jsonify(result)
```

### /trace endpoint

Same as `/calculate` but enables tracing for explainability.

## 2. Handler Layer

**File:** `openfisca_web_api/handlers.py`

```python
def calculate(tax_benefit_system, input_data: dict) -> dict:
    # Step 1: Build simulation from input JSON
    simulation = SimulationBuilder().build_from_entities(tax_benefit_system, input_data)

    # Step 2: Find all null values (requested calculations)
    requested_computations = dpath.search(
        input_data,
        "*/*/*/*",  # entity_plural/entity_id/variable_name/period
        afilter=lambda t: t is None,
        yielded=True,
    )

    # Step 3: Calculate each requested variable
    for computation in requested_computations:
        path = computation[0]
        entity_plural, entity_id, variable_name, period = path.split("/")
        result = simulation.calculate(variable_name, period)
        # Extract and format result...

    # Step 4: Merge computed values into input
    dpath.merge(input_data, computation_results)
    return input_data
```

## 3. SimulationBuilder

**File:** `openfisca_core/simulations/simulation_builder.py`

### build_from_entities()

```python
def build_from_entities(self, tax_benefit_system, input_dict):
    # 1. Instantiate populations for all entities
    populations = tax_benefit_system.instantiate_entities()

    # 2. Create Simulation object
    simulation = Simulation(tax_benefit_system, populations)

    # 3. Register variables
    self.register_variables(simulation)

    # 4. Parse person entity
    persons_json = params.get(person_entity.plural)
    persons_ids = self.add_person_entity(simulation.persons.entity, persons_json)

    # 5. Parse group entities (households, etc.)
    for entity_class in tax_benefit_system.group_entities:
        self.add_group_entity(...)

    # 6. Initialize variable values in holders
    self.finalize_variables_init(simulation.persons)
    for entity_class in tax_benefit_system.group_entities:
        self.finalize_variables_init(simulation.populations[entity_class.key])

    return simulation
```

### Key Data Structures

| Structure | Purpose |
|-----------|---------|
| `entity_ids` | Maps entity plural to instance IDs |
| `entity_counts` | Count of each entity type |
| `memberships` | Maps person indices to group entity indices |
| `roles` | Maps person indices to their roles |
| `input_buffer` | Buffers input values before setting |

## 4. Simulation

**File:** `openfisca_core/simulations/simulation.py`

### Constructor

```python
def __init__(self, tax_benefit_system, populations):
    self.tax_benefit_system = tax_benefit_system
    self.populations = populations
    self.persons = self.populations[tax_benefit_system.person_entity.key]

    # Tracer configuration
    self.debug = False
    self.trace = False
    self.tracer = SimpleTracer()  # Upgraded to FullTracer if trace=True

    self.invalidated_caches = set()
    self.max_spiral_loops = 1
```

### calculate() - Public Interface

```python
def calculate(self, variable_name: str, period):
    if period is not None and not isinstance(period, Period):
        period = periods.period(period)

    self.tracer.record_calculation_start(variable_name, period)

    try:
        result = self._calculate(variable_name, period)
        self.tracer.record_calculation_result(result)
        return result
    finally:
        self.tracer.record_calculation_end()
        self.purge_cache_of_invalid_values()
```

### _calculate() - Core Logic

```python
def _calculate(self, variable_name: str, period):
    # 1. Get variable definition
    variable = self.tax_benefit_system.get_variable(variable_name)

    # 2. Check period consistency
    self._check_period_consistency(period, variable)

    # 3. Check cache (FAST PATH)
    cached_array = holder.get_array(period)
    if cached_array is not None:
        return cached_array

    # 4. Check for circular dependencies
    self._check_for_cycle(variable.name, period)

    # 5. Run formula
    array = self._run_formula(variable, population, period)

    # 6. Use default if no formula
    if array is None:
        array = holder.default_array()

    # 7. Type casting
    array = self._cast_formula_result(array, variable)

    # 8. Cache result
    holder.put_in_cache(array, period)

    return array
```

### Circular Dependency Detection

```python
def _check_for_cycle(self, variable: str, period):
    # Check if variable@period already in calculation stack
    previous_periods = [
        frame["period"]
        for frame in self.tracer.stack[:-1]
        if frame["name"] == variable
    ]
    if period in previous_periods:
        raise CycleError(...)

    # Guard against quasi-circles
    spiral = len(previous_periods) >= self.max_spiral_loops
    if spiral:
        self.invalidate_spiral_variables(variable)
        raise SpiralError(...)
```

## 5. Variable

**File:** `openfisca_core/variables/variable.py`

### Formula Resolution

```python
def get_formula(self, period=None):
    if not self.formulas:
        return None

    if period is None:
        return self.formulas.peekitem(index=0)[1]

    instant = period.start

    # Check variable hasn't ended
    if self.end and instant.date > self.end:
        return None

    # Find most recent formula effective at instant
    for start_date in reversed(self.formulas):
        if start_date <= str(instant):
            return self.formulas[start_date]

    return None
```

## 6. Population & Holders

**Files:** `openfisca_core/populations/_core_population.py`, `openfisca_core/holders/holder.py`

### Population Structure

```python
class CorePopulation:
    entity: Entity              # Entity type definition
    count: int                  # Number of members
    ids: Sequence[str]          # Instance identifiers
    simulation: Simulation      # Parent simulation
    _holders: Dict[Variable, Holder]  # Variable data storage
```

### Holder: Variable Data Store

```python
class Holder:
    variable: Variable
    population: Population
    _memory_storage: InMemoryStorage   # Primary cache
    _disk_storage: OnDiskStorage       # Secondary storage

    def get_array(self, period):
        if self.variable.is_neutralized:
            return self.default_array()
        value = self._memory_storage.get(period)
        if value is not None:
            return value
        if self._disk_storage:
            return self._disk_storage.get(period)
        return None

    def put_in_cache(self, array, period):
        self._memory_storage.add(array, period)
```

## 7. Tracing & Explainability

**Files:** `openfisca_core/tracers/`

### Tracer Hierarchy

```
SimpleTracer (lightweight)
    ├─ Maintains calculation stack
    ├─ Tracks name & period
    └─ Used when trace=False

FullTracer (comprehensive)
    ├─ Builds tree of TraceNodes
    ├─ Records calculation timing
    ├─ Tracks parameter accesses
    └─ Used when trace=True
```

### TraceNode

```python
@dataclass
class TraceNode:
    name: str                      # Variable or parameter name
    period: Period                 # Computation period
    parent: TraceNode | None       # Parent calculation
    children: List[TraceNode]      # Dependent calculations
    parameters: List[TraceNode]    # Parameters accessed
    value: numpy.ndarray | None    # Result value
    start: float                   # Start time (ns)
    end: float                     # End time (ns)
```

### FlatTrace Output

```python
{
    "salary<2020>": {
        "dependencies": [],
        "parameters": {},
        "value": [2000, 3000],
        "calculation_time": 0.0001234,
        "formula_time": 0.0001234,
    },
    "tax<2020>": {
        "dependencies": ["salary<2020>"],
        "parameters": {"rate<2020>": 0.15},
        "value": [300, 450],
        "calculation_time": 0.0002,
        "formula_time": 0.0001,
    }
}
```

### TracingParameterNodeAtInstant

Proxy wrapper that intercepts parameter access:

```python
class TracingParameterNodeAtInstant:
    def __getattr__(self, key):
        child = getattr(self.parameter_node_at_instant, key)

        # Record parameter access in trace
        self.tracer.record_parameter_access(
            name=self.parameter_node_at_instant._name + "." + key,
            period=self.parameter_node_at_instant._instant_str,
            value=child
        )

        return child
```

## Key Classes Summary

| Class | File | Purpose |
|-------|------|---------|
| SimulationBuilder | simulations/simulation_builder.py | Constructs simulations from JSON |
| Simulation | simulations/simulation.py | Orchestrates calculations |
| Variable | variables/variable.py | Variable metadata and formulas |
| Holder | holders/holder.py | Stores and caches variable data |
| CorePopulation | populations/_core_population.py | Entity instances |
| SimpleTracer | tracers/simple_tracer.py | Lightweight tracing |
| FullTracer | tracers/full_tracer.py | Comprehensive tracing |
| TraceNode | tracers/trace_node.py | Calculation tree node |
| FlatTrace | tracers/flat_trace.py | Serialized trace output |

## Performance Characteristics

### Caching Strategy

- **L1 Cache (Memory):** Unlimited fast access, checked first
- **L2 Cache (Disk):** Activated when RAM exceeds threshold
- **Invalidation:** Spiral variables purged after calculation

### Circular Dependency Protection

- **Exact cycles:** Detected via stack inspection → `CycleError`
- **Quasi-cycles:** Detected via spiral heuristic → `SpiralError`
- **max_spiral_loops:** Configurable threshold (default=1)

### Tracing Overhead

- **SimpleTracer:** Minimal - just stack management
- **FullTracer:** Moderate - builds tree, times each node, records parameter accesses
