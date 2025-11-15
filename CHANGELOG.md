# Changelog

All notable changes to the Habit Coach Backend will be documented in this file.

## [0.1.0] - Initial Release

### Added
- FastAPI application with OpenAPI documentation
- PostgreSQL database with SQLAlchemy ORM
- Alembic migrations
- JWT authentication with access and refresh tokens
- User management (signup, login, logout)
- Habit CRUD operations
- Daily check-in system
- Statistics computation (streaks, completion rates)
- ML predictions using LightGBM
- Feature engineering pipeline
- Model training script
- Background workers with Celery
- Scheduled tasks (predictions, reports, notifications)
- Weekly reports
- Notification system
- Admin endpoints
- Health checks
- Prometheus metrics
- Sentry integration
- Docker Compose setup
- Comprehensive test suite
- Documentation (README, DEPLOYMENT, QUICKSTART)

### Security
- Password hashing with bcrypt
- JWT token-based authentication
- Refresh tokens in HttpOnly cookies
- Token rotation
- CORS configuration
- Input validation with Pydantic

### Infrastructure
- Docker support
- CI/CD pipeline (GitHub Actions)
- Environment-based configuration
- Structured logging

