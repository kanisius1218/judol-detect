# Architecture Overview

The system follows a clean architecture approach with clear separation between API, services, repositories, and models.

- **API Layer** – FastAPI routers with strict dependency injection and middleware for authentication, rate limiting, and error handling.
- **Service Layer** – Orchestrates business logic, integrates with ML models, and coordinates queues and notifications.
- **Model Layer** – Provides wrappers for ML inference and ORM models for persistence.
- **Workers** – Celery based asynchronous processing for safe deletion queues and scheduled tasks.
- **Frontend** – React dashboard for monitoring and manual review flows.
- **Infrastructure** – Docker and Kubernetes templates, monitoring stack, and CI/CD pipelines.
