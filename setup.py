#!/usr/bin/env python3
"""Setup script for initial project setup."""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode == 0


def main():
    """Main setup function."""
    print("=" * 60)
    print("Habit Coach Backend - Setup Script")
    print("=" * 60)

    # Check Python version
    if sys.version_info < (3, 11):
        print("ERROR: Python 3.11+ is required")
        sys.exit(1)

    # Check if .env exists
    env_file = Path(".env")
    env_example = Path("env.example.txt")
    
    if not env_file.exists() and env_example.exists():
        print("\nCreating .env file from example...")
        with open(env_example, "r") as f:
            content = f.read()
        with open(env_file, "w") as f:
            f.write(content)
        print("✓ Created .env file")
        print("⚠ Please edit .env and set your SECRET_KEY and database URLs")
    elif env_file.exists():
        print("✓ .env file already exists")

    # Create necessary directories
    directories = [
        "app/ml/saved_models",
        "app/db/migrations/versions",
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")

    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("\n⚠ Virtual environment not found.")
        print("  Create one with: python -m venv venv")
        print("  Then activate it and run: pip install -r requirements.txt")
    else:
        print("✓ Virtual environment found")

    # Check if dependencies are installed
    try:
        import fastapi
        print("✓ Dependencies appear to be installed")
    except ImportError:
        print("⚠ Dependencies not installed. Run: pip install -r requirements.txt")

    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start PostgreSQL and Redis (or use docker-compose)")
    print("3. Run migrations: alembic upgrade head")
    print("4. (Optional) Seed database: python -m app.db.seed")
    print("5. Start server: uvicorn app.main:app --reload")
    print("\nSee QUICKSTART.md for detailed instructions")


if __name__ == "__main__":
    main()

