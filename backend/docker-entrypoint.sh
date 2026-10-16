#!/bin/sh
# Apply database migrations, then hand PID 1 over to Uvicorn.
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

exec "$@"
