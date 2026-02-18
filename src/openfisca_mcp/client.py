"""HTTP client for OpenFisca API."""

import os
from typing import Any

import httpx

from .errors import ConnectionError, format_api_error


class OpenFiscaClient:
    """Client for interacting with OpenFisca Web API."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        """Initialize the client.

        Args:
            base_url: OpenFisca API base URL. Defaults to OPENFISCA_API_URL env var
                     or http://localhost:5000.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url or os.getenv(
            "OPENFISCA_API_URL", "http://localhost:5000"
        )
        self.timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        return self._client

    def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response, raising appropriate errors."""
        if response.status_code >= 400:
            try:
                data = response.json()
            except Exception:
                data = {"error": response.text}
            raise format_api_error(data, response.status_code)
        return response.json()

    def get_entities(self) -> dict[str, Any]:
        """Get all entity definitions."""
        try:
            response = self.client.get("/entities")
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(
                message=f"Cannot connect to OpenFisca API at {self.base_url}",
                details={"url": self.base_url, "error": str(e)},
            )

    def get_variables(self) -> dict[str, Any]:
        """Get all variable definitions (summary)."""
        try:
            response = self.client.get("/variables")
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(
                message=f"Cannot connect to OpenFisca API at {self.base_url}",
                details={"url": self.base_url, "error": str(e)},
            )

    def get_variable(self, variable_id: str) -> dict[str, Any]:
        """Get detailed variable definition."""
        try:
            response = self.client.get(f"/variable/{variable_id}")
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(
                message=f"Cannot connect to OpenFisca API at {self.base_url}",
                details={"url": self.base_url, "error": str(e)},
            )

    def get_parameters(self) -> dict[str, Any]:
        """Get all parameter definitions (summary)."""
        try:
            response = self.client.get("/parameters")
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(
                message=f"Cannot connect to OpenFisca API at {self.base_url}",
                details={"url": self.base_url, "error": str(e)},
            )

    def get_parameter(self, parameter_id: str) -> dict[str, Any]:
        """Get detailed parameter definition."""
        try:
            response = self.client.get(f"/parameter/{parameter_id}")
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(
                message=f"Cannot connect to OpenFisca API at {self.base_url}",
                details={"url": self.base_url, "error": str(e)},
            )

    def calculate(self, situation: dict[str, Any]) -> dict[str, Any]:
        """Run a calculation."""
        try:
            response = self.client.post("/calculate", json=situation)
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(
                message=f"Cannot connect to OpenFisca API at {self.base_url}",
                details={"url": self.base_url, "error": str(e)},
            )

    def trace(self, situation: dict[str, Any]) -> dict[str, Any]:
        """Run a calculation with tracing."""
        try:
            response = self.client.post("/trace", json=situation)
            return self._handle_response(response)
        except httpx.ConnectError as e:
            raise ConnectionError(
                message=f"Cannot connect to OpenFisca API at {self.base_url}",
                details={"url": self.base_url, "error": str(e)},
            )
