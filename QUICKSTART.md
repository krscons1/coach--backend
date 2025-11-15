# Quick Start Guide

Get the Habit Coach backend running in 5 minutes!

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)
- Docker & Docker Compose (recommended)

## Step 1: Clone and Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Configure Environment

```bash
# Copy the example env file
cp env.example.txt .env

# Edit .env and set:
# - DATABASE_URL (if not using Docker)
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - REDIS_URL (if not using Docker)
```

## Step 3: Start Services

### Option A: Using Docker Compose (Recommended)

**Note**: On newer Docker installations, use `docker compose` (without hyphen)

```bash
# Start PostgreSQL and Redis
docker compose up -d postgres redis

# Or start everything (backend + worker + beat)
docker compose up

# If you have older Docker, try:
docker-compose up -d postgres redis
```

### Option B: Manual Setup

```bash
# Start PostgreSQL and Redis manually
# Then update .env with your connection strings
```

## Step 4: Run Migrations

```bash
alembic upgrade head
```

## Step 5: Seed Database (Optional)

```bash
python -m app.db.seed
```

This creates:
- Admin user: `admin@example.com` / `admin123`
- Test user: `test@example.com` / `test123`
- Sample habits with entries

## Step 6: Start the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Step 7: Start Background Workers (Optional)

In separate terminals:

```bash
# Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Celery beat (scheduler)
celery -A app.workers.celery_app beat --loglevel=info
```

## Step 8: Train ML Model (After collecting data)

Once you have habits with at least 7 days of entries:

```bash
python -m app.ml.train
```

## Test the API

```bash
# Sign up
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "name": "Test User"
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

## Troubleshooting

### Database Connection Error
- Check PostgreSQL is running: `docker ps` or `pg_isready`
- Verify DATABASE_URL in .env

### Redis Connection Error
- Check Redis is running: `redis-cli ping`
- Verify REDIS_URL in .env

### Import Errors
- Make sure you're in the backend directory
- Activate virtual environment
- Install dependencies: `pip install -r requirements.txt`

### Migration Errors
- Make sure database exists
- Check DATABASE_URL is correct
- Try: `alembic downgrade -1` then `alembic upgrade head`

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Check [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
3. Explore the API at http://localhost:8000/docs

