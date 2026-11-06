#!/bin/sh
set -e

COUNTRY_PACKAGE="${OPENFISCA_COUNTRY_PACKAGE:-openfisca_country_template}"
API_PORT="${OPENFISCA_API_PORT:-5000}"
API_WORKERS="${OPENFISCA_API_WORKERS:-3}"

case "$1" in
  api)
    # --bind is passed through to gunicorn (openfisca defaults to 127.0.0.1).
    # Gunicorn's local control socket is not needed in a container.
    exec openfisca serve \
      -c "$COUNTRY_PACKAGE" \
      -p "$API_PORT" \
      --workers "$API_WORKERS" \
      -b "0.0.0.0:$API_PORT" \
      --no-control-socket
    ;;
  mcp)
    export OPENFISCA_MCP_TRANSPORT=sse
    exec openfisca-mcp
    ;;
  *)
    exec "$@"
    ;;
esac
