# Habit Coach Backend

Production-ready FastAPI backend for the Fitness/Health Habit Coach application.

## Features

- **FastAPI** with async support and automatic OpenAPI documentation
- **PostgreSQL** database with SQLAlchemy ORM and Alembic migrations
- **JWT Authentication** with access tokens and refresh tokens (HttpOnly cookies)
- **ML Predictions** using LightGBM for habit maintenance probability
- **Background Workers** with Celery for scheduled tasks (predictions, reports, notifications)
- **Redis** for Celery broker and result backend
- **Comprehensive API** for habits, entries, predictions, reports, and notifications
- **Docker Compose** setup for local development
- **Testing** with pytest
- **Monitoring** with Sentry and Prometheus metrics

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routers
│   ├── core/             # Core utilities (security, ML loader, background)
│   ├── db/               # Database models and migrations
│   ├── ml/               # ML training pipeline
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic layer
│   ├── workers/          # Celery tasks
│   ├── tests/            # Test suite
│   ├── config.py         # Configuration
│   ├── deps.py           # Dependency injection
│   ├── logger.py         # Logging setup
│   └── main.py           # FastAPI app
├── docker-compose.yml    # Local development setup
├── Dockerfile            # Production container
├── requirements.txt      # Python dependencies
├── alembic.ini           # Alembic configuration
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose (optional)

### Local Development

1. **Clone and setup:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your database and Redis URLs
```

3. **Start services with Docker Compose:**

```bash
docker-compose up -d postgres redis
```

4. **Run database migrations:**

```bash
alembic upgrade head
```

5. **Seed database (optional):**

```bash
python -m app.db.seed
```

6. **Start the development server:**

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Docker Compose (Full Stack)

Run everything with Docker Compose:

```bash
docker-compose up
```

This starts:
- PostgreSQL database
- Redis
- FastAPI backend
- Celery worker
- Celery beat (scheduler)

## Environment Variables

See `.env.example` for all required variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing secret (generate with `openssl rand -hex 32`)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiry (default: 15)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiry (default: 7)
- `ML_MODEL_PATH`: Path to saved ML model file
- `SENTRY_DSN`: Sentry DSN for error tracking (optional)
- `SMTP_*`: Email configuration for reports (optional)

## Database Migrations

### Create a new migration:

```bash
alembic revision --autogenerate -m "description"
```

### Apply migrations:

```bash
alembic upgrade head
```

### Rollback:

```bash
alembic downgrade -1
```

## ML Model Training

### Train a new model:

```bash
python -m app.ml.train
```

This will:
1. Export training data from the database
2. Train a LightGBM model
3. Save the model to `app/ml/saved_models/`
4. Register the model in the registry

### Model Requirements:

- At least 100 training samples (habits with 7+ days of entries)
- Model is saved as `latest_model.pkl` and timestamped version
- Fallback rule-based predictions are used if model is missing

## Background Workers

### Start Celery worker:

```bash
celery -A app.workers.celery_app worker --loglevel=info
```

### Start Celery beat (scheduler):

```bash
celery -A app.workers.celery_app beat --loglevel=info
```

### Scheduled Tasks:

- **Nightly predictions** (2 AM UTC): Batch predictions for all active habits
- **Weekly reports** (Monday 8 AM UTC): Generate and email weekly reports
- **Notifications** (Every 15 minutes): Send scheduled notifications

## API Endpoints

### Authentication

- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout

### Habits

- `POST /api/v1/habits` - Create habit
- `GET /api/v1/habits` - List habits
- `GET /api/v1/habits/{id}` - Get habit
- `PUT /api/v1/habits/{id}` - Update habit
- `DELETE /api/v1/habits/{id}` - Delete habit

### Entries

- `POST /api/v1/habits/{id}/checkin` - Create/update check-in
- `GET /api/v1/habits/{id}/entries` - Get entries
- `GET /api/v1/habits/{id}/stats` - Get statistics

### Predictions

- `GET /api/v1/predictions/habits/{id}/prediction` - Get prediction
- `GET /api/v1/predictions` - List predictions
- `POST /api/v1/predictions/batch` - Trigger batch predictions

### Reports

- `GET /api/v1/reports/weekly` - Get weekly report
- `POST /api/v1/reports/weekly/email` - Send weekly email

### Notifications

- `POST /api/v1/notifications` - Schedule notification
- `GET /api/v1/notifications` - List notifications
- `POST /api/v1/notifications/{id}/dismiss` - Dismiss notification

### Admin

- `POST /api/v1/admin/train-model` - Trigger model training
- `POST /api/v1/admin/reload-model` - Reload ML model
- `GET /api/v1/admin/health` - Detailed health check

See `/docs` for interactive API documentation.

## Testing

Run tests:

```bash
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=html
```

## Production Deployment

### Using Docker:

1. Build image:

```bash
docker build -t habit-coach-backend .
```

2. Run container:

```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  habit-coach-backend
```

### Using Gunicorn:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Environment Setup:

- Use managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
- Use managed Redis (AWS ElastiCache, Redis Cloud, etc.)
- Set `APP_ENV=production`
- Use strong `SECRET_KEY`
- Enable HTTPS (use reverse proxy like Nginx)
- Configure CORS for your frontend domain
- Set up monitoring (Sentry, Prometheus)

### Health Checks:

- Basic: `GET /health`
- Detailed: `GET /api/v1/admin/health`
- Metrics: `GET /metrics` (Prometheus format)

## CI/CD

Example GitHub Actions workflow:

```yaml
name: CI/CD

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Your deployment commands
```

## Troubleshooting

### Database Connection Issues:

- Verify `DATABASE_URL` format: `postgresql://user:pass@host:port/dbname`
- Check PostgreSQL is running and accessible
- Verify database exists

### Redis Connection Issues:

- Verify `REDIS_URL` format: `redis://host:port/db`
- Check Redis is running
- Test connection: `redis-cli ping`

### ML Model Not Loading:

- Check `ML_MODEL_PATH` points to valid file
- Train model first: `python -m app.ml.train`
- Fallback predictions will be used if model missing

### Celery Tasks Not Running:

- Verify Celery worker is running
- Check Redis connection
- Verify task imports in `celery_app.py`

## License

MIT

## Support

For issues and questions, please open an issue on GitHub.

