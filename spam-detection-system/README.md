# Multi-Platform Spam Detection & Auto-Deletion System

This project provides a production-ready scaffold for detecting and removing spam across YouTube, Instagram, and TikTok.

## Features

- Automated spam detection powered by an extensible ML abstraction.
- Secure API with API key authentication, rate limiting, and error handling.
- Safe deletion queue with rollback and manual review workflows.
- React dashboard for real-time monitoring.
- Infrastructure templates for Docker, CI/CD, and observability.

## Getting Started

1. Install backend dependencies: `pip install -r backend/requirements-dev.txt`.
2. Run the API: `uvicorn backend.app:app --reload`.
3. Install frontend dependencies: `npm install` inside `frontend`.
4. Start the dashboard: `npm run dev`.

Run `pytest backend/tests` to execute the automated test suite.
