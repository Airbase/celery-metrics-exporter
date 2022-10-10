#!/bin/bash

set -e
# Postgres migration
DATABASE_URL=$DATABASE_URL alembic --config exporters/postgres/alembic.ini upgrade head
