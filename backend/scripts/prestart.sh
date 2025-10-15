#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python app/backend_pre_start.py

# Check if there are any Alembic versions
#alembic revision --autogenerate -m "revision schema"

# Run migrations
alembic upgrade head

python app/create_models.py

# Create initial data in DB
python app/initial_data.py
