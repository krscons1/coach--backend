# Deployment Guide

This guide covers deployment options for the Habit Coach Backend.

## Deployment Options

### 1. Docker Compose (Recommended for Small Deployments)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Cloud Platforms

#### Render.com

1. Create a new Web Service
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT`
5. Add environment variables
6. Add PostgreSQL and Redis add-ons

#### Fly.io

1. Install flyctl: `curl -L https://fly.io/install.sh | sh`
2. Login: `flyctl auth login`
3. Launch: `flyctl launch`
4. Set secrets: `flyctl secrets set SECRET_KEY=... DATABASE_URL=...`

#### Railway

1. Create new project
2. Add PostgreSQL and Redis services
3. Deploy from GitHub
4. Set environment variables

### 3. Kubernetes

See `infra/k8s/` for example manifests (create these based on your cluster).

### 4. Traditional VPS

1. Install dependencies on server
2. Set up Nginx reverse proxy
3. Use systemd for service management
4. Run with Gunicorn + Uvicorn workers

## Environment Variables for Production

```bash
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://host:port/0
SECRET_KEY=<generate-strong-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ML_MODEL_PATH=app/ml/saved_models/latest_model.pkl
SENTRY_DSN=<your-sentry-dsn>
LOG_LEVEL=INFO
```

## Pre-Deployment Checklist

- [ ] Database migrations run
- [ ] ML model trained and saved
- [ ] Environment variables configured
- [ ] CORS origins set correctly
- [ ] HTTPS enabled (via reverse proxy or load balancer)
- [ ] Health checks configured
- [ ] Monitoring set up (Sentry, logs)
- [ ] Backup strategy for database
- [ ] Celery workers and beat scheduled
- [ ] Rate limiting configured (if needed)

## Post-Deployment

1. Verify health endpoint: `GET /health`
2. Check admin health: `GET /api/v1/admin/health`
3. Test authentication flow
4. Monitor logs and metrics
5. Set up alerts for errors

## Scaling

- **Horizontal**: Run multiple backend instances behind load balancer
- **Database**: Use connection pooling, read replicas for heavy reads
- **Redis**: Use Redis Cluster for high availability
- **Workers**: Scale Celery workers based on queue length

## Backup and Recovery

- Database: Daily automated backups
- ML Models: Version control in S3 or similar
- Redis: Persistence enabled for important data

