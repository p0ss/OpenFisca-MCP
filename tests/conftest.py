"""Pytest configuration and fixtures for OpenFisca MCP tests."""

import json
import subprocess
import time
from pathlib import Path

import httpx
import pytest

BASE_URL = "http://localhost:5050"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def openfisca_server():
    """Start OpenFisca server for the test session."""
    process = subprocess.Popen(
        [
            "poetry",
            "run",
            "openfisca",
            "serve",
            "-c",
            "openfisca_country_template",
            "-p",
            "5050",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready
    max_attempts = 30
    for _ in range(max_attempts):
        try:
            response = httpx.get(f"{BASE_URL}/", timeout=1.0)
            if response.status_code in (200, 300):
                break
        except httpx.ConnectError:
            time.sleep(0.5)
    else:
        process.terminate()
        raise RuntimeError("OpenFisca server failed to start")

    yield BASE_URL

    process.terminate()
    process.wait()


@pytest.fixture
def client(openfisca_server):
    """HTTP client configured for the test server."""
    with httpx.Client(base_url=openfisca_server, timeout=30.0) as client:
        yield client


@pytest.fixture
def single_person_situation():
    """Load single person test fixture."""
    return json.loads((FIXTURES_DIR / "single_person.json").read_text())


@pytest.fixture
def couple_situation():
    """Load couple test fixture."""
    return json.loads((FIXTURES_DIR / "couple.json").read_text())


@pytest.fixture
def family_situation():
    """Load family with children test fixture."""
    return json.loads((FIXTURES_DIR / "family_with_children.json").read_text())


@pytest.fixture
def multi_household_situation():
    """Load multi-household test fixture."""
    return json.loads((FIXTURES_DIR / "multi_household.json").read_text())
