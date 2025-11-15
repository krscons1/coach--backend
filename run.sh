#!/bin/bash
# Development server startup script

set -e

echo "Starting Habit Coach Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your configuration"
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start server
echo "Starting development server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

