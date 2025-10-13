#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python app/backend_pre_start.py

# Check if there are any Alembic versions
#alembic revision --autogenerate -m "init schema"

# Run migrations
alembic upgrade head

# Create initial data in DB
python app/create_models.py

python app/initial_data.py
