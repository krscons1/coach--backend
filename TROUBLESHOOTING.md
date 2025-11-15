# Troubleshooting Guide

Common issues and their solutions.

## Dependency Installation Issues

### Issue: Redis version conflict
**Error**: `ERROR: Cannot install celery[redis]==5.3.4 and redis==5.0.1`

**Solution**: The requirements.txt has been updated. Redis version is set to 4.6.0 to be compatible with Celery.

```bash
pip install -r requirements.txt
```

### Issue: Missing dependencies
**Error**: `ModuleNotFoundError: No module named 'psycopg2'`

**Solution**: Install all dependencies:
```bash
pip install -r requirements.txt
```

If you're using a virtual environment (recommended):
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

## Docker Issues

### Issue: `docker-compose` command not found

**Solution 1**: Use newer Docker Compose syntax (Docker Desktop):
```bash
docker compose up -d postgres redis
```

**Solution 2**: Install Docker Compose separately:
- Windows: Install Docker Desktop (includes docker-compose)
- Linux: `sudo apt-get install docker-compose`
- Mac: Install Docker Desktop

**Solution 3**: Use Docker without Compose:
- Install PostgreSQL and Redis manually
- Update `.env` with connection strings

## Database Connection Issues

### Issue: `ModuleNotFoundError: No module named 'psycopg2'`

**Solution**: Install psycopg2-binary:
```bash
pip install psycopg2-binary
```

### Issue: Database connection refused

**Check**:
1. PostgreSQL is running: `pg_isready` or check Docker containers
2. DATABASE_URL in `.env` is correct
3. Database exists: `createdb habit_coach` (if needed)

**Solution**: Start PostgreSQL:
```bash
# With Docker
docker compose up -d postgres

# Or manually start PostgreSQL service
```

## Migration Issues

### Issue: `alembic upgrade head` fails

**Check**:
1. Database is running and accessible
2. DATABASE_URL in `.env` is correct
3. Database exists

**Solution**:
```bash
# Create database first (if needed)
createdb habit_coach

# Then run migrations
alembic upgrade head
```

### Issue: "Target database is not up to date"

**Solution**:
```bash
# Check current revision
alembic current

# Upgrade to latest
alembic upgrade head
```

## Application Startup Issues

### Issue: `ModuleNotFoundError: No module named 'prometheus_client'`

**Solution**: Install missing dependencies:
```bash
pip install prometheus-client
# Or install all:
pip install -r requirements.txt
```

### Issue: Import errors

**Check**:
1. You're in the `backend` directory
2. Virtual environment is activated
3. All dependencies are installed

**Solution**:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Redis Connection Issues

### Issue: Redis connection refused

**Check**:
1. Redis is running: `redis-cli ping` (should return PONG)
2. REDIS_URL in `.env` is correct

**Solution**: Start Redis:
```bash
# With Docker
docker compose up -d redis

# Or manually start Redis service
```

## Windows-Specific Issues

### Issue: PowerShell command syntax

**Problem**: `&&` doesn't work in PowerShell

**Solution**: Use `;` instead or run commands separately:
```powershell
# Instead of: cmd1 && cmd2
# Use:
cmd1; cmd2

# Or run separately
```

### Issue: Path issues

**Solution**: Use forward slashes or raw strings in Python code. For terminal, use PowerShell-compatible commands.

## Environment Variables

### Issue: Configuration not loading

**Check**:
1. `.env` file exists in `backend/` directory
2. `.env` file has correct format (no spaces around `=`)
3. All required variables are set

**Solution**: Copy from template:
```bash
cp env.example.txt .env
# Then edit .env with your values
```

## ML Model Issues

### Issue: Model not found

**Solution**: This is expected initially. The app will use fallback predictions. Train a model after collecting data:
```bash
python -m app.ml.train
```

## Celery Worker Issues

### Issue: Celery tasks not running

**Check**:
1. Redis is running
2. Worker is started: `celery -A app.workers.celery_app worker --loglevel=info`
3. Beat is started (for scheduled tasks): `celery -A app.workers.celery_app beat --loglevel=info`

## Still Having Issues?

1. Check logs for detailed error messages
2. Verify all services are running (PostgreSQL, Redis)
3. Ensure virtual environment is activated
4. Verify `.env` file is configured correctly
5. Check Python version: `python --version` (should be 3.11+)

For more help, check:
- [README.md](README.md) - Main documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide

