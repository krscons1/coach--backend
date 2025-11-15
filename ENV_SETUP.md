# Environment Variables Setup

Copy `.env.example` to `.env` and configure the following variables:

## Required Variables

```bash
# Application
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000

# Database (PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/habit_coach

# Redis
REDIS_URL=redis://localhost:6379/0

# Security (IMPORTANT: Generate a strong secret key!)
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# ML Model
ML_MODEL_PATH=app/ml/saved_models/latest_model.pkl

# Monitoring (Optional)
SENTRY_DSN=
LOG_LEVEL=INFO

# Email (Optional - for weekly reports)
SMTP_URL=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@habitcoach.com

# Push Notifications (Optional - FCM)
FCM_SERVER_KEY=

# Celery (Optional - defaults to REDIS_URL if not set)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Generating SECRET_KEY

```bash
# Using OpenSSL
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Production Considerations

- Never commit `.env` to version control
- Use environment variable management (AWS Secrets Manager, HashiCorp Vault, etc.)
- Rotate secrets regularly
- Use different secrets for each environment (dev, staging, prod)

