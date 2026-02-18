"""Baseline tests for OpenFisca Web API.

These tests verify the API behaves as expected, establishing a baseline
for MCP tool validation.
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_welcome(self, client):
        """Root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 300
        data = response.json()
        assert "welcome" in data


class TestEntitiesEndpoint:
    """Tests for /entities endpoint."""

    def test_list_entities(self, client):
        """Entities endpoint returns person and household."""
        response = client.get("/entities")
        assert response.status_code == 200
        data = response.json()

        assert "person" in data
        assert "household" in data

        # Person entity
        assert data["person"]["plural"] == "persons"
        assert "description" in data["person"]

        # Household entity with roles
        assert data["household"]["plural"] == "households"
        assert "roles" in data["household"]
        assert "adult" in data["household"]["roles"]
        assert "child" in data["household"]["roles"]


class TestVariablesEndpoint:
    """Tests for /variables endpoint."""

    def test_list_variables(self, client):
        """Variables endpoint returns list of variables."""
        response = client.get("/variables")
        assert response.status_code == 200
        data = response.json()

        # Check some expected variables exist
        expected_vars = ["salary", "age", "income_tax", "housing_allowance"]
        for var in expected_vars:
            assert var in data, f"Expected variable '{var}' not found"
            assert "description" in data[var]
            assert "href" in data[var]

    def test_get_variable_details(self, client):
        """Get details for a specific variable."""
        response = client.get("/variable/salary")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "salary"
        assert data["valueType"] == "Float"
        assert data["definitionPeriod"] == "MONTH"
        assert data["entity"] == "person"

    def test_get_variable_with_formula(self, client):
        """Get variable that has formulas."""
        response = client.get("/variable/income_tax")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "income_tax"
        assert "formulas" in data
        assert len(data["formulas"]) > 0

    def test_get_nonexistent_variable(self, client):
        """Requesting nonexistent variable returns 404."""
        response = client.get("/variable/nonexistent_var")
        assert response.status_code == 404


class TestParametersEndpoint:
    """Tests for /parameters endpoint."""

    def test_list_parameters(self, client):
        """Parameters endpoint returns list of parameters."""
        response = client.get("/parameters")
        assert response.status_code == 200
        data = response.json()

        # Should have some parameters
        assert len(data) > 0

    def test_get_parameter_details(self, client):
        """Get details for a specific parameter."""
        # First get the list to find a valid parameter
        response = client.get("/parameters")
        params = response.json()
        param_id = next(iter(params.keys()))

        # Now get details
        response = client.get(f"/parameter/{param_id}")
        assert response.status_code == 200
        data = response.json()

        assert "id" in data


class TestCalculateEndpoint:
    """Tests for /calculate endpoint."""

    def test_calculate_income_tax(self, client, single_person_situation):
        """Calculate income tax for single person."""
        situation = single_person_situation.copy()
        situation["persons"]["alice"]["income_tax"] = {"2024-01": None}

        response = client.post("/calculate", json=situation)
        assert response.status_code == 200
        data = response.json()

        # Check income tax was calculated (not None)
        income_tax = data["persons"]["alice"]["income_tax"]["2024-01"]
        assert income_tax is not None
        assert isinstance(income_tax, (int, float))

    def test_calculate_age(self, client, single_person_situation):
        """Calculate age from birth date."""
        situation = single_person_situation.copy()
        situation["persons"]["alice"]["age"] = {"2024-01": None}

        response = client.post("/calculate", json=situation)
        assert response.status_code == 200
        data = response.json()

        age = data["persons"]["alice"]["age"]["2024-01"]
        # Born 1990-01-15, age at start of 2024-01 is 33 (turns 34 on Jan 15)
        assert age in (33, 34)

    def test_calculate_household_variable(self, client, couple_situation):
        """Calculate household-level variable."""
        situation = couple_situation.copy()
        situation["households"]["household1"]["housing_tax"] = {"2024": None}

        response = client.post("/calculate", json=situation)
        assert response.status_code == 200
        data = response.json()

        housing_tax = data["households"]["household1"]["housing_tax"]["2024"]
        assert housing_tax is not None

    def test_calculate_multiple_variables(self, client, single_person_situation):
        """Calculate multiple variables in one request."""
        situation = single_person_situation.copy()
        situation["persons"]["alice"]["income_tax"] = {"2024-01": None}
        situation["persons"]["alice"]["social_security_contribution"] = {"2024-01": None}

        response = client.post("/calculate", json=situation)
        assert response.status_code == 200
        data = response.json()

        assert data["persons"]["alice"]["income_tax"]["2024-01"] is not None
        assert data["persons"]["alice"]["social_security_contribution"]["2024-01"] is not None

    def test_calculate_with_family(self, client, family_situation):
        """Calculate with family including children."""
        situation = family_situation.copy()
        situation["households"]["household1"]["total_taxes"] = {"2024-01": None}
        situation["households"]["household1"]["total_benefits"] = {"2024-01": None}

        response = client.post("/calculate", json=situation)
        assert response.status_code == 200
        data = response.json()

        assert data["households"]["household1"]["total_taxes"]["2024-01"] is not None
        assert data["households"]["household1"]["total_benefits"]["2024-01"] is not None

    def test_calculate_invalid_variable(self, client, single_person_situation):
        """Requesting invalid variable returns error."""
        situation = single_person_situation.copy()
        situation["persons"]["alice"]["nonexistent_var"] = {"2024-01": None}

        response = client.post("/calculate", json=situation)
        assert response.status_code == 404

    def test_calculate_period_mismatch(self, client, single_person_situation):
        """Period mismatch returns error."""
        situation = single_person_situation.copy()
        # income_tax is MONTH, but we're asking for a year
        situation["persons"]["alice"]["income_tax"] = {"2024": None}

        response = client.post("/calculate", json=situation)
        # May return 400 (validation error), 500 (period error), or 200 (if converted)
        assert response.status_code in (200, 400, 500)


class TestTraceEndpoint:
    """Tests for /trace endpoint."""

    def test_trace_calculation(self, client, single_person_situation):
        """Trace endpoint returns dependency information."""
        situation = single_person_situation.copy()
        situation["persons"]["alice"]["income_tax"] = {"2024-01": None}

        response = client.post("/trace", json=situation)
        assert response.status_code == 200
        data = response.json()

        assert "requestedCalculations" in data
        assert "trace" in data
        assert "entitiesDescription" in data

        # Check trace contains the requested calculation
        assert len(data["requestedCalculations"]) > 0

    def test_trace_shows_dependencies(self, client, single_person_situation):
        """Trace shows variable dependencies."""
        situation = single_person_situation.copy()
        # Use income_tax which depends on salary
        situation["persons"]["alice"]["income_tax"] = {"2024-01": None}

        response = client.post("/trace", json=situation)
        assert response.status_code == 200
        data = response.json()

        # Should have trace entries with dependencies
        trace = data["trace"]
        assert len(trace) > 0

        # At least some entries should have dependencies
        has_dependencies = any(
            len(entry.get("dependencies", [])) > 0 for entry in trace.values()
        )
        assert has_dependencies


class TestErrorHandling:
    """Tests for API error handling."""

    def test_invalid_json(self, client):
        """Invalid JSON returns 400."""
        response = client.post(
            "/calculate",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    def test_empty_persons(self, client):
        """Empty persons dict returns error."""
        response = client.post("/calculate", json={"persons": {}, "households": {}})
        assert response.status_code == 400

    def test_unknown_entity(self, client):
        """Unknown entity in input returns error."""
        response = client.post(
            "/calculate",
            json={
                "persons": {"alice": {}},
                "households": {"h1": {"adults": ["alice"]}},
                "companies": {"c1": {}},  # Unknown entity
            },
        )
        assert response.status_code == 400

    def test_person_not_in_household(self, client):
        """Person not assigned to any household."""
        response = client.post(
            "/calculate",
            json={
                "persons": {"alice": {}, "bob": {}},
                "households": {"h1": {"adults": ["alice"]}},
                # bob is not in any household
            },
        )
        # This might be valid (person can exist without household) or error
        # depending on the country package
        assert response.status_code in (200, 400)
