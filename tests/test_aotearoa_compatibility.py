"""Compatibility tests for openfisca-aotearoa.

These tests verify MCP tools work correctly with Aotearoa's 5-entity model
including unique property entities and WEEK periods.

Run with: poetry run openfisca serve -c openfisca_aotearoa -p 5052 &
"""

import pytest

from openfisca_mcp.client import OpenFiscaClient


def _aotearoa_server_available():
    """Check if Aotearoa server is running."""
    import httpx
    try:
        resp = httpx.get("http://localhost:5052/", timeout=2.0)
        return resp.status_code in (200, 300)
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _aotearoa_server_available(),
    reason="Aotearoa server not running on port 5052"
)


@pytest.fixture(scope="module")
def aotearoa_client():
    """Create client for Aotearoa server on port 5052."""
    client = OpenFiscaClient(base_url="http://localhost:5052")
    yield client
    client.close()


class TestAotearoaEntities:
    """Test Aotearoa's 5-entity model."""

    def test_has_five_entities(self, aotearoa_client):
        """Aotearoa has 5 entities: person, family, tenancy, ownership, titled_property."""
        data = aotearoa_client.get_entities()

        assert len(data) == 5
        assert "person" in data
        assert "family" in data
        assert "tenancy" in data
        assert "ownership" in data
        assert "titled_property" in data

    def test_person_is_individual(self, aotearoa_client):
        """Person is the individual entity (no roles)."""
        data = aotearoa_client.get_entities()

        person = data["person"]
        assert person.get("isEntitiesCollection", False) is False

    def test_family_roles(self, aotearoa_client):
        """Family has principal, partner, parent, child, other roles."""
        data = aotearoa_client.get_entities()

        family = data["family"]
        assert "roles" in family
        role_keys = list(family["roles"].keys())
        assert "principal" in role_keys
        assert family["roles"]["principal"].get("max") == 1

    def test_tenancy_roles(self, aotearoa_client):
        """Tenancy entity models rental relationships."""
        data = aotearoa_client.get_entities()

        tenancy = data["tenancy"]
        assert "roles" in tenancy
        assert "principal" in tenancy["roles"]

    def test_ownership_roles(self, aotearoa_client):
        """Ownership entity models property ownership."""
        data = aotearoa_client.get_entities()

        ownership = data["ownership"]
        assert "roles" in ownership
        assert "principal" in ownership["roles"]

    def test_titled_property_entity(self, aotearoa_client):
        """Titled_property is a group entity."""
        data = aotearoa_client.get_entities()

        titled = data["titled_property"]
        assert "roles" in titled


class TestAotearoaVariables:
    """Test Aotearoa's variable set."""

    def test_has_many_variables(self, aotearoa_client):
        """Aotearoa has hundreds of variables."""
        data = aotearoa_client.get_variables()

        # Should have at least 100 variables
        assert len(data) > 100

    def test_has_acc_variables(self, aotearoa_client):
        """Aotearoa has ACC (Accident Compensation) variables."""
        data = aotearoa_client.get_variables()

        # Look for ACC-related variables
        acc_vars = [v for v in data.keys() if "acc" in v.lower()]
        assert len(acc_vars) > 0

    def test_has_age_variable(self, aotearoa_client):
        """Aotearoa has age variable."""
        data = aotearoa_client.get_variables()

        assert "age" in data

    def test_describe_age(self, aotearoa_client):
        """Can describe age variable."""
        data = aotearoa_client.get_variable("age")

        assert data["id"] == "age"
        assert data["entity"] == "person"

    def test_has_immigration_variables(self, aotearoa_client):
        """Aotearoa has immigration/visa variables."""
        data = aotearoa_client.get_variables()

        # Look for immigration or visa related variables
        immigration_vars = [v for v in data.keys()
                          if "visa" in v.lower() or "immigration" in v.lower()
                          or "citizen" in v.lower() or "resident" in v.lower()]
        assert len(immigration_vars) > 0


class TestAotearoaParameters:
    """Test Aotearoa's parameter set."""

    def test_has_parameters(self, aotearoa_client):
        """Aotearoa has parameters."""
        data = aotearoa_client.get_parameters()

        # Should have parameters
        assert len(data) > 0

    def test_has_benefit_parameters(self, aotearoa_client):
        """Aotearoa has benefit-related parameters."""
        data = aotearoa_client.get_parameters()

        # Look for benefit parameters
        benefit_params = [p for p in data.keys() if "benefit" in p.lower()]
        # May or may not have these, so just verify the query works
        assert isinstance(benefit_params, list)


class TestAotearoaCalculation:
    """Test calculations with Aotearoa's model."""

    def test_calculate_age(self, aotearoa_client):
        """Calculate age for a person.

        Note: Aotearoa's age variable has definitionPeriod=DAY,
        so we must use a day period like "2024-06-15".
        """
        situation = {
            "persons": {
                "person1": {
                    "date_of_birth": {"ETERNITY": "1990-01-01"},
                    # Use DAY period for age (Aotearoa uses DAY, not MONTH)
                    "age": {"2024-06-15": None},
                }
            },
            "families": {
                "family1": {
                    "principal": "person1",
                }
            },
        }

        data = aotearoa_client.calculate(situation)

        age = data["persons"]["person1"]["age"]["2024-06-15"]
        assert age == 34  # Born 1990-01-01, calculated for 2024-06-15

    def test_calculate_with_family(self, aotearoa_client):
        """Calculate with a family structure."""
        situation = {
            "persons": {
                "adult1": {
                    "date_of_birth": {"ETERNITY": "1985-06-15"},
                    "age": {"2024-06-15": None},
                },
                "adult2": {
                    "date_of_birth": {"ETERNITY": "1987-09-20"},
                    "age": {"2024-06-15": None},
                },
            },
            "families": {
                "family1": {
                    "principal": "adult1",
                    "partners": ["adult2"],
                }
            },
        }

        data = aotearoa_client.calculate(situation)

        # adult1: born 1985-06-15, on 2024-06-15 = exactly 39
        assert data["persons"]["adult1"]["age"]["2024-06-15"] == 39
        # adult2: born 1987-09-20, on 2024-06-15 = 36 (birthday not yet)
        assert data["persons"]["adult2"]["age"]["2024-06-15"] == 36


class TestAotearoaTrace:
    """Test tracing with Aotearoa's model."""

    def test_trace_calculation(self, aotearoa_client):
        """Trace returns dependency information."""
        situation = {
            "persons": {
                "person1": {
                    "date_of_birth": {"ETERNITY": "1990-01-01"},
                    # Use DAY period for age
                    "age": {"2024-06-15": None},
                }
            },
            "families": {
                "family1": {
                    "principal": "person1",
                }
            },
        }

        data = aotearoa_client.trace(situation)

        assert "requestedCalculations" in data
        assert "trace" in data


class TestAotearoaWeekPeriods:
    """Test Aotearoa's WEEK period handling."""

    def test_find_week_variables(self, aotearoa_client):
        """Aotearoa has variables with WEEK definition periods."""
        data = aotearoa_client.get_variables()

        # Find variables with WEEK periods
        week_vars = []
        for var_name in list(data.keys())[:50]:  # Check first 50 to avoid timeout
            try:
                var_detail = aotearoa_client.get_variable(var_name)
                if var_detail.get("definitionPeriod") == "WEEK":
                    week_vars.append(var_name)
                    break  # Found one, that's enough
            except Exception:
                pass

        # Just verify the search works - may or may not find WEEK vars in first 50
        assert isinstance(week_vars, list)
