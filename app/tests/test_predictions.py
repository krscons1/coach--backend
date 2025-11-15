"""Tests for predictions endpoints."""

import pytest


def test_get_prediction(client, auth_headers):
    """Test getting a prediction for a habit."""
    # Create a habit first
    create_response = client.post(
        "/api/v1/habits",
        headers=auth_headers,
        json={
            "name": "Test Habit",
            "type": "binary",
            "schedule": {"days": [0, 1, 2, 3, 4, 5, 6], "frequency": "daily"},
        },
    )
    habit_id = create_response.json()["id"]

    # Get prediction
    response = client.get(
        f"/api/v1/predictions/habits/{habit_id}/prediction",
        headers=auth_headers,
        params={"horizon": 7},
    )
    assert response.status_code == 200
    data = response.json()
    assert "prob_maintain" in data
    assert "risk_level" in data
    assert "explanation" in data
    assert 0.0 <= data["prob_maintain"] <= 1.0

