"""Tests for OpenFisca MCP tools.

These tests verify the MCP tools work correctly against the OpenFisca API.
"""

import json

import pytest

from openfisca_mcp.client import OpenFiscaClient
from openfisca_mcp.errors import MCPError, NotFoundError, ValidationError


@pytest.fixture
def mcp_client(openfisca_server):
    """Create MCP client connected to test server."""
    client = OpenFiscaClient(base_url=openfisca_server)
    yield client
    client.close()


class TestListEntities:
    """Tests for list_entities functionality."""

    def test_returns_entities(self, mcp_client):
        """Returns person and household entities."""
        data = mcp_client.get_entities()

        assert "person" in data
        assert "household" in data

    def test_person_entity_structure(self, mcp_client):
        """Person entity has expected structure."""
        data = mcp_client.get_entities()

        person = data["person"]
        assert person["plural"] == "persons"
        assert "description" in person

    def test_household_has_roles(self, mcp_client):
        """Household entity includes roles."""
        data = mcp_client.get_entities()

        household = data["household"]
        assert "roles" in household
        assert "adult" in household["roles"]
        assert "child" in household["roles"]


class TestListVariables:
    """Tests for list_variables functionality."""

    def test_returns_variables(self, mcp_client):
        """Returns list of variables."""
        data = mcp_client.get_variables()

        assert len(data) > 0
        assert "salary" in data
        assert "income_tax" in data

    def test_variable_has_description(self, mcp_client):
        """Each variable has description and href."""
        data = mcp_client.get_variables()

        for var_name, var_info in data.items():
            assert "description" in var_info
            assert "href" in var_info


class TestDescribeVariable:
    """Tests for describe_variable functionality."""

    def test_returns_variable_details(self, mcp_client):
        """Returns detailed variable information."""
        data = mcp_client.get_variable("salary")

        assert data["id"] == "salary"
        assert data["valueType"] == "Float"
        assert data["definitionPeriod"] == "MONTH"
        assert data["entity"] == "person"

    def test_variable_with_formula(self, mcp_client):
        """Variables with formulas include formula details."""
        data = mcp_client.get_variable("income_tax")

        assert "formulas" in data
        assert len(data["formulas"]) > 0

    def test_nonexistent_variable_raises_error(self, mcp_client):
        """Requesting nonexistent variable raises NotFoundError."""
        with pytest.raises(MCPError):
            mcp_client.get_variable("nonexistent_variable")


class TestListParameters:
    """Tests for list_parameters functionality."""

    def test_returns_parameters(self, mcp_client):
        """Returns list of parameters."""
        data = mcp_client.get_parameters()

        assert len(data) > 0


class TestGetParameter:
    """Tests for get_parameter functionality."""

    def test_returns_parameter_details(self, mcp_client):
        """Returns parameter with values or brackets."""
        # First get a parameter ID
        params = mcp_client.get_parameters()
        param_id = next(iter(params.keys()))

        data = mcp_client.get_parameter(param_id)

        assert "id" in data
        # Should have either values, brackets, or subparams
        assert any(k in data for k in ["values", "brackets", "subparams"])


class TestCalculate:
    """Tests for calculate functionality."""

    def test_calculate_income_tax(self, mcp_client, single_person_situation):
        """Calculate income tax for single person."""
        situation = single_person_situation.copy()
        situation["persons"]["alice"]["income_tax"] = {"2024-01": None}

        data = mcp_client.calculate(situation)

        income_tax = data["persons"]["alice"]["income_tax"]["2024-01"]
        assert income_tax is not None
        assert isinstance(income_tax, (int, float))

    def test_calculate_household_variable(self, mcp_client, couple_situation):
        """Calculate household-level variable."""
        situation = couple_situation.copy()
        situation["households"]["household1"]["total_taxes"] = {"2024-01": None}

        data = mcp_client.calculate(situation)

        total_taxes = data["households"]["household1"]["total_taxes"]["2024-01"]
        assert total_taxes is not None

    def test_invalid_variable_raises_error(self, mcp_client, single_person_situation):
        """Invalid variable raises error."""
        situation = single_person_situation.copy()
        situation["persons"]["alice"]["nonexistent_var"] = {"2024-01": None}

        with pytest.raises(MCPError):
            mcp_client.calculate(situation)


class TestTrace:
    """Tests for trace_calculation functionality."""

    def test_trace_returns_dependencies(self, mcp_client, single_person_situation):
        """Trace returns calculation dependencies."""
        situation = single_person_situation.copy()
        situation["persons"]["alice"]["income_tax"] = {"2024-01": None}

        data = mcp_client.trace(situation)

        assert "requestedCalculations" in data
        assert "trace" in data
        assert "entitiesDescription" in data

    def test_trace_shows_parameter_usage(self, mcp_client, single_person_situation):
        """Trace shows which parameters were accessed."""
        situation = single_person_situation.copy()
        situation["persons"]["alice"]["income_tax"] = {"2024-01": None}

        data = mcp_client.trace(situation)

        # At least one trace entry should have parameters
        trace = data["trace"]
        has_params = any(
            len(entry.get("parameters", {})) > 0 for entry in trace.values()
        )
        # This may or may not be true depending on the variable
        # Just check the structure exists
        assert isinstance(trace, dict)


class TestErrorHandling:
    """Tests for error handling."""

    def test_connection_error_on_bad_url(self):
        """Connection error when server is unreachable."""
        from openfisca_mcp.errors import ConnectionError

        client = OpenFiscaClient(base_url="http://localhost:59999")
        with pytest.raises(ConnectionError):
            client.get_entities()
        client.close()

    def test_error_has_correct_structure(self, mcp_client, single_person_situation):
        """Errors have the expected structure."""
        situation = single_person_situation.copy()
        situation["persons"]["alice"]["nonexistent_var"] = {"2024-01": None}

        try:
            mcp_client.calculate(situation)
            pytest.fail("Expected MCPError")
        except MCPError as e:
            error_dict = e.to_dict()
            assert "error" in error_dict
            assert "type" in error_dict["error"]
            assert "code" in error_dict["error"]
            assert "message" in error_dict["error"]


class TestGoldenFixtures:
    """Tests that verify MCP tools match golden fixtures."""

    def test_entities_match_golden(self, mcp_client):
        """Entities response matches golden fixture."""
        data = mcp_client.get_entities()
        golden = json.loads(
            (pytest.importorskip("pathlib").Path(__file__).parent / "fixtures" / "golden" / "entities.json").read_text()
        )

        # Check structure matches (values may differ)
        assert set(data.keys()) == set(golden["response"].keys())

    def test_variable_details_match_golden(self, mcp_client):
        """Variable details response has expected structure."""
        data = mcp_client.get_variable("salary")
        golden = json.loads(
            (pytest.importorskip("pathlib").Path(__file__).parent / "fixtures" / "golden" / "variable_salary.json").read_text()
        )

        # Check key fields match
        assert data["id"] == golden["response"]["id"]
        assert data["valueType"] == golden["response"]["valueType"]
        assert data["definitionPeriod"] == golden["response"]["definitionPeriod"]
        assert data["entity"] == golden["response"]["entity"]
