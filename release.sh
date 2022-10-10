#!/bin/bash

set -e
# Postgres migration
DATABASE_URL=$DATABASE_URL python -m alembic --config exporters/postgres/alembic.ini upgrade head
