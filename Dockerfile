FROM python:3.12-slim AS base

WORKDIR /app

# Country package to install (directory name under country-packages/, or empty to skip)
ARG COUNTRY_PACKAGE_DIR=""

# Install system deps for numpy/C extensions
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Install poetry and export plugin
RUN pip install --no-cache-dir poetry poetry-plugin-export

# Copy dependency files first for layer caching
COPY pyproject.toml poetry.lock ./

# Export and install dependencies (no poetry venv in container)
RUN poetry export -f requirements.txt --without-hashes -o requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and README (needed by pyproject.toml)
COPY README.md .
COPY src/ src/

# Install the project itself
RUN pip install --no-cache-dir .

# Install country package from local directory (for packages not on PyPI)
COPY country-packages/ country-packages/
RUN if [ -n "$COUNTRY_PACKAGE_DIR" ] && [ -d "country-packages/$COUNTRY_PACKAGE_DIR" ]; then \
      pip install --no-cache-dir --no-build-isolation "./country-packages/$COUNTRY_PACKAGE_DIR"; \
    fi

# Remove build toolchain to shrink image
RUN apt-get purge -y gcc g++ && apt-get autoremove -y

# --- OpenFisca API entrypoint ---
# Runs the OpenFisca Web API (gunicorn)
# Usage: docker run -p 5000:5000 openfisca-mcp api
#
# --- MCP SSE entrypoint ---
# Runs the MCP server with SSE transport
# Usage: docker run -p 8080:8080 openfisca-mcp mcp

COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["mcp"]
