"""End-to-end flow placeholder."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import app
from backend.src.api.v1.middleware.auth import SecurityService

client = TestClient(app)


def test_manual_review_flow(monkeypatch):
    headers = {"X-API-KEY": "default-key"}

    def fake_validate(self, api_key: str):
        class Cred:
            scopes = ["read", "write"]

        return Cred()

    monkeypatch.setattr(SecurityService, "validate_api_key", fake_validate)

    response = client.post(
        "/detection/manual-review",
        headers=headers,
        json={"comment_id": "1", "platform": "youtube"},
    )
    assert response.status_code == 202
