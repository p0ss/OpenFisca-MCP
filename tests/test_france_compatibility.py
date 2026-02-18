"""Compatibility tests for openfisca-france.

These tests verify MCP tools work correctly with France's more complex model.

Run with: poetry run openfisca serve -c openfisca_france -p 5051 &
"""

import pytest

from openfisca_mcp.client import OpenFiscaClient
from openfisca_mcp.errors import MCPError


def _france_server_available():
    """Check if France server is running."""
    import httpx
    try:
        resp = httpx.get("http://localhost:5051/", timeout=2.0)
        return resp.status_code in (200, 300)
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _france_server_available(),
    reason="France server not running on port 5051"
)


@pytest.fixture(scope="module")
def france_client():
    """Create client for France server on port 5051."""
    client = OpenFiscaClient(base_url="http://localhost:5051")
    yield client
    client.close()


class TestFranceEntities:
    """Test France's 4-entity model."""

    def test_has_four_entities(self, france_client):
        """France has 4 entities: individu, famille, foyer_fiscal, menage."""
        data = france_client.get_entities()

        assert len(data) == 4
        assert "individu" in data
        assert "famille" in data
        assert "foyer_fiscal" in data
        assert "menage" in data

    def test_famille_roles(self, france_client):
        """Famille has parent and enfant roles."""
        data = france_client.get_entities()

        famille = data["famille"]
        assert "roles" in famille
        assert "parent" in famille["roles"]
        assert "enfant" in famille["roles"]
        assert famille["roles"]["parent"]["max"] == 2

    def test_foyer_fiscal_roles(self, france_client):
        """Foyer fiscal has declarant and personne_a_charge roles."""
        data = france_client.get_entities()

        foyer = data["foyer_fiscal"]
        assert "declarant" in foyer["roles"]
        assert "personne_a_charge" in foyer["roles"]

    def test_menage_roles(self, france_client):
        """Menage has personne_de_reference, conjoint, enfant, autre roles."""
        data = france_client.get_entities()

        menage = data["menage"]
        assert "personne_de_reference" in menage["roles"]
        assert "conjoint" in menage["roles"]
        assert "enfant" in menage["roles"]
        assert "autre" in menage["roles"]


class TestFranceVariables:
    """Test France's variable set."""

    def test_has_many_variables(self, france_client):
        """France has thousands of variables."""
        data = france_client.get_variables()

        # Should have at least 1000 variables
        assert len(data) > 1000

    def test_has_salaire_base(self, france_client):
        """France has salaire_de_base variable."""
        data = france_client.get_variables()

        assert "salaire_de_base" in data

    def test_describe_salaire(self, france_client):
        """Can describe salaire_de_base."""
        data = france_client.get_variable("salaire_de_base")

        assert data["id"] == "salaire_de_base"
        assert data["entity"] == "individu"
        assert data["definitionPeriod"] == "MONTH"

    def test_has_rsa(self, france_client):
        """France has RSA (welfare) variables."""
        data = france_client.get_variables()

        # Look for RSA-related variables
        rsa_vars = [v for v in data.keys() if "rsa" in v.lower()]
        assert len(rsa_vars) > 0

    def test_has_income_tax(self, france_client):
        """France has income tax variables."""
        data = france_client.get_variables()

        # Look for impot (tax) variables
        impot_vars = [v for v in data.keys() if "impot" in v.lower()]
        assert len(impot_vars) > 0


class TestFranceParameters:
    """Test France's parameter set."""

    def test_has_many_parameters(self, france_client):
        """France has thousands of parameters."""
        data = france_client.get_parameters()

        # Should have many parameters
        assert len(data) > 100

    def test_has_smic(self, france_client):
        """France has SMIC (minimum wage) parameters."""
        data = france_client.get_parameters()

        # Look for SMIC-related parameters
        smic_params = [p for p in data.keys() if "smic" in p.lower()]
        assert len(smic_params) > 0


class TestFranceCalculation:
    """Test calculations with France's model."""

    def test_calculate_simple(self, france_client):
        """Calculate a simple variable."""
        situation = {
            "individus": {
                "personne1": {
                    "date_naissance": {"ETERNITY": "1990-01-01"},
                    "salaire_de_base": {"2024-01": 2500},
                }
            },
            "familles": {
                "famille1": {
                    "parents": ["personne1"],
                }
            },
            "foyers_fiscaux": {
                "foyer1": {
                    "declarants": ["personne1"],
                }
            },
            "menages": {
                "menage1": {
                    "personne_de_reference": ["personne1"],
                }
            },
        }

        # Request age calculation
        situation["individus"]["personne1"]["age"] = {"2024-01": None}

        data = france_client.calculate(situation)

        age = data["individus"]["personne1"]["age"]["2024-01"]
        assert age == 34  # Born 1990, calculated for 2024

    def test_calculate_with_couple(self, france_client):
        """Calculate with a couple."""
        situation = {
            "individus": {
                "personne1": {
                    "date_naissance": {"ETERNITY": "1985-03-15"},
                    "salaire_de_base": {"2024-01": 3000},
                },
                "personne2": {
                    "date_naissance": {"ETERNITY": "1987-07-20"},
                    "salaire_de_base": {"2024-01": 2000},
                },
            },
            "familles": {
                "famille1": {
                    "parents": ["personne1", "personne2"],
                }
            },
            "foyers_fiscaux": {
                "foyer1": {
                    "declarants": ["personne1", "personne2"],
                }
            },
            "menages": {
                "menage1": {
                    "personne_de_reference": ["personne1"],
                    "conjoint": ["personne2"],
                }
            },
        }

        # Calculate ages
        situation["individus"]["personne1"]["age"] = {"2024-01": None}
        situation["individus"]["personne2"]["age"] = {"2024-01": None}

        data = france_client.calculate(situation)

        assert data["individus"]["personne1"]["age"]["2024-01"] == 38
        assert data["individus"]["personne2"]["age"]["2024-01"] == 36


class TestFranceTrace:
    """Test tracing with France's model."""

    def test_trace_calculation(self, france_client):
        """Trace returns dependency information."""
        situation = {
            "individus": {
                "personne1": {
                    "date_naissance": {"ETERNITY": "1990-01-01"},
                    "salaire_de_base": {"2024-01": 2500},
                    "salaire_net": {"2024-01": None},
                }
            },
            "familles": {
                "famille1": {
                    "parents": ["personne1"],
                }
            },
            "foyers_fiscaux": {
                "foyer1": {
                    "declarants": ["personne1"],
                }
            },
            "menages": {
                "menage1": {
                    "personne_de_reference": ["personne1"],
                }
            },
        }

        data = france_client.trace(situation)

        assert "requestedCalculations" in data
        assert "trace" in data
        assert len(data["trace"]) > 0
