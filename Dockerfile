# OpenFisca MCP images: two runtimes from one source tree.
#
#   --target api   OpenFisca Web API + one country package (no MCP stack)
#   --target mcp   MCP bridge only (default; talks HTTP to an OpenFisca API)
#
# The bridge does not import OpenFisca, so the MCP image carries no numpy,
# pandas or Core, and the API image carries no MCP, Starlette or JWT stack.
#
# Base: Wolfi (glibc, rolling security updates) pinned by digest. Every build
# also applies pending package updates, so a rebuild picks up OS fixes without a
# base bump. Debian stable was dropped in Nov 2026 because its glibc and zlib
# fixes for current HIGH advisories were only in unstable.
# Update the digest with:
#   podman pull cgr.dev/chainguard/wolfi-base:latest
#   podman image inspect cgr.dev/chainguard/wolfi-base:latest --format '{{index .RepoDigests 0}}'
ARG WOLFI_BASE=cgr.dev/chainguard/wolfi-base@sha256:8acb3a7694eda954b3ad4256aec3291bdd92715d7a8c030abd1a21546337b4e4

FROM ${WOLFI_BASE} AS python
RUN apk upgrade --no-cache \
    && apk add --no-cache python-3.13 ca-certificates-bundle \
    && python3 -c 'import sys; assert sys.version_info[:2] == (3, 13), sys.version'

# ---- build stage: wheels for local projects, hash-verified build backends ----
FROM python AS builder
WORKDIR /src
COPY requirements/ requirements/
RUN python3 -m venv /opt/build \
    && /opt/build/bin/pip install --no-cache-dir --require-hashes --only-binary :all: -r requirements/build.lock
COPY pyproject.toml README.md ./
COPY src/ src/
RUN /opt/build/bin/pip wheel --no-cache-dir --no-deps --no-build-isolation -w /wheels/mcp .

# Country package to bundle in the API image (a directory under country-packages/).
ARG COUNTRY_PACKAGE_DIR=openfisca-aotearoa
# PEP 440 local version marking the repackaged dependency contract.
ARG COUNTRY_LOCAL_TAG=openfiscamcp1
COPY country-packages/ country-packages/
COPY scripts/relock-country-package.py scripts/
RUN test -d "country-packages/$COUNTRY_PACKAGE_DIR" \
    && /opt/build/bin/python scripts/relock-country-package.py \
       "country-packages/$COUNTRY_PACKAGE_DIR" requirements/api.lock "$COUNTRY_LOCAL_TAG" \
    && /opt/build/bin/pip wheel --no-cache-dir --no-deps --no-build-isolation \
       -w /wheels/country "country-packages/$COUNTRY_PACKAGE_DIR"

# ---- dependency stages: one virtualenv each, pip removed after checking ----
FROM python AS api-env
COPY requirements/api.lock /tmp/api.lock
COPY --from=builder /wheels/country /tmp/wheels
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --require-hashes --only-binary :all: -r /tmp/api.lock \
    && /opt/venv/bin/pip install --no-cache-dir --no-deps /tmp/wheels/*.whl \
    && /opt/venv/bin/pip check \
    && /opt/venv/bin/pip freeze --all --exclude pip --exclude setuptools > /opt/venv/requirements.runtime.txt \
    && /opt/venv/bin/pip uninstall -y pip

FROM python AS mcp-env
COPY requirements/mcp.lock /tmp/mcp.lock
COPY --from=builder /wheels/mcp /tmp/wheels
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --require-hashes --only-binary :all: -r /tmp/mcp.lock \
    && /opt/venv/bin/pip install --no-cache-dir --no-deps /tmp/wheels/*.whl \
    && /opt/venv/bin/pip check \
    && /opt/venv/bin/pip freeze --all --exclude pip --exclude setuptools > /opt/venv/requirements.runtime.txt \
    && /opt/venv/bin/pip uninstall -y pip

# ---- runtimes ----
FROM python AS runtime
COPY --chmod=0755 scripts/docker-entrypoint.sh /docker-entrypoint.sh
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1
USER 65532:65532
ENTRYPOINT ["/docker-entrypoint.sh"]

# OpenFisca Web API (gunicorn). Usage: docker run -p 5000:5000 IMAGE
FROM runtime AS api
COPY --from=api-env /opt/venv /opt/venv
ARG COUNTRY_PACKAGE=openfisca_aotearoa
ENV OPENFISCA_COUNTRY_PACKAGE=${COUNTRY_PACKAGE}
RUN python -c "import importlib, os; importlib.import_module(os.environ['OPENFISCA_COUNTRY_PACKAGE'])"
EXPOSE 5000
CMD ["api"]

# MCP server over SSE. Usage: docker run -p 8080:8080 -e OPENFISCA_API_URL=... IMAGE
FROM runtime AS mcp
COPY --from=mcp-env /opt/venv /opt/venv
RUN python -c "import openfisca_mcp.server"
EXPOSE 8080
CMD ["mcp"]
