"""Tests for habits endpoints."""

import pytest


def test_create_habit(client, auth_headers):
    """Test creating a habit."""
    response = client.post(
        "/api/v1/habits",
        headers=auth_headers,
        json={
            "name": "Morning Run",
            "description": "Run 5km every morning",
            "type": "binary",
            "schedule": {"days": [0, 1, 2, 3, 4, 5, 6], "frequency": "daily"},
            "reminder_times": ["07:00"],
            "difficulty": "medium",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Morning Run"
    assert data["type"] == "binary"


def test_list_habits(client, auth_headers):
    """Test listing habits."""
    # Create a habit first
    client.post(
        "/api/v1/habits",
        headers=auth_headers,
        json={
            "name": "Test Habit",
            "type": "binary",
            "schedule": {"days": [0, 1, 2, 3, 4, 5, 6], "frequency": "daily"},
        },
    )

    response = client.get("/api/v1/habits", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "habits" in data
    assert "total" in data
    assert len(data["habits"]) > 0


def test_get_habit(client, auth_headers):
    """Test getting a specific habit."""
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

    response = client.get(f"/api/v1/habits/{habit_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == habit_id


def test_update_habit(client, auth_headers):
    """Test updating a habit."""
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

    response = client.put(
        f"/api/v1/habits/{habit_id}",
        headers=auth_headers,
        json={"name": "Updated Habit"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Habit"


def test_delete_habit(client, auth_headers):
    """Test deleting a habit."""
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

    response = client.delete(f"/api/v1/habits/{habit_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's deactivated
    get_response = client.get(f"/api/v1/habits/{habit_id}", headers=auth_headers)
    assert get_response.json()["active"] == False

