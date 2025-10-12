"""Integration tests for API endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_prediction_requires_api_key():
    response = client.post("/detection/predict", json={"comments": []})
    assert response.status_code == 401
