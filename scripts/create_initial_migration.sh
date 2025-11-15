#!/bin/bash
# Script to create initial Alembic migration

echo "Creating initial database migration..."
alembic revision --autogenerate -m "Initial migration"

echo "Migration created. Review the file in app/db/migrations/versions/"
echo "Then run: alembic upgrade head"

