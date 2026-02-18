#!/bin/bash
# Start the OpenFisca Web API server

PORT=${1:-5000}

cd "$(dirname "$0")/.."
poetry run openfisca serve -c openfisca_country_template -p "$PORT"
