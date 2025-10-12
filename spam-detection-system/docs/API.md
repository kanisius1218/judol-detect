# API Documentation

## Detection

- `POST /detection/predict` – run inference on comments.
- `POST /detection/auto-delete` – enqueue automatic deletion tasks.
- `POST /detection/manual-review` – flag a comment for manual review.
- `POST /detection/rollback` – rollback a deletion job.

All endpoints require the `X-API-KEY` header unless stated otherwise.
