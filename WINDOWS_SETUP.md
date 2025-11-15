# Windows Setup Guide

This guide is specifically for Windows users.

## Prerequisites

1. **Python 3.11+** - Download from [python.org](https://www.python.org/downloads/)
2. **PostgreSQL** - Download from [postgresql.org](https://www.postgresql.org/download/windows/) OR use Docker
3. **Redis** - Download from [redis.io](https://redis.io/download) OR use Docker
4. **Docker Desktop** (Optional but recommended) - Download from [docker.com](https://www.docker.com/products/docker-desktop/)

## Step-by-Step Setup

### 1. Install Python

1. Download Python 3.11+ from python.org
2. During installation, check "Add Python to PATH"
3. Verify installation:
   ```powershell
   python --version
   ```

### 2. Install Dependencies

Open PowerShell in the `backend` directory:

```powershell
# Install all dependencies
pip install -r requirements.txt
```

### 3. Setup Database and Redis

#### Option A: Using Docker Desktop (Recommended)

1. Install Docker Desktop for Windows
2. Start Docker Desktop
3. Use the new Docker Compose syntax:
   ```powershell
   docker compose up -d postgres redis
   ```

#### Option B: Manual Installation

**PostgreSQL:**
1. Download and install PostgreSQL from postgresql.org
2. During installation, remember the password you set for the `postgres` user
3. Create database:
   ```powershell
   # Using psql (comes with PostgreSQL)
   psql -U postgres
   CREATE DATABASE habit_coach;
   \q
   ```

**Redis:**
1. Download Redis for Windows from [GitHub releases](https://github.com/microsoftarchive/redis/releases)
2. Or use WSL2 to run Redis
3. Or use a cloud Redis service

### 4. Configure Environment

1. Copy the example env file:
   ```powershell
   copy env.example.txt .env
   ```

2. Edit `.env` file with Notepad or any text editor:
   ```powershell
   notepad .env
   ```

3. Update these values:
   - `DATABASE_URL`: `postgresql://postgres:YOUR_PASSWORD@localhost:5432/habit_coach`
   - `SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - `REDIS_URL`: `redis://localhost:6379/0` (if using local Redis)

### 5. Run Migrations

```powershell
alembic upgrade head
```

If you get an error about database connection, make sure:
- PostgreSQL is running
- Database exists
- DATABASE_URL in `.env` is correct

### 6. (Optional) Seed Database

```powershell
python -m app.db.seed
```

This creates test users:
- Admin: `admin@example.com` / `admin123`
- Test: `test@example.com` / `test123`

### 7. Start the Server

```powershell
uvicorn app.main:app --reload
```

The API will be available at:
- http://localhost:8000
- Docs: http://localhost:8000/docs

## PowerShell Commands

In PowerShell, use `;` instead of `&&`:

```powershell
# Wrong (doesn't work in PowerShell):
cmd1 && cmd2

# Correct:
cmd1; cmd2

# Or run separately:
cmd1
cmd2
```

## Common Windows Issues

### Issue: "docker-compose" not found

**Solution**: Use `docker compose` (without hyphen) if you have Docker Desktop:
```powershell
docker compose up -d postgres redis
```

### Issue: Permission errors

**Solution**: Run PowerShell as Administrator if needed for:
- Installing system-wide packages
- Starting services
- Creating databases

### Issue: Path issues

**Solution**: Use forward slashes in Python code, but PowerShell handles both:
```powershell
# Both work:
cd backend\app
cd backend/app
```

### Issue: Virtual environment activation

**Solution**: Use backslashes for Windows:
```powershell
# Create venv
python -m venv venv

# Activate (PowerShell)
venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Testing the Setup

1. **Test database connection:**
   ```powershell
   python -c "from app.db.session import engine; print('DB OK')"
   ```

2. **Test imports:**
   ```powershell
   python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
   ```

3. **Run tests:**
   ```powershell
   pytest app/tests/ -v
   ```

## Next Steps

- Read [QUICKSTART.md](QUICKSTART.md) for more details
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you encounter issues
- See [README.md](README.md) for full documentation

