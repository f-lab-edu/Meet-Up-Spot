#!/bin/bash
set -e

echo "Running alembic upgrade.."
alembic upgrade head


if [ "$APP_ENV" = "production" ]; then
    uvicorn main:app --host 0.0.0.0 --port 8000 workers 3
else
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi