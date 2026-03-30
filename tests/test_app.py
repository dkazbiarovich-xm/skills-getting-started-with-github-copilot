from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activities_state():
    """Keep each test isolated because the API mutates in-memory state."""
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_expected_structure(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert "participants" in payload["Chess Club"]
    assert isinstance(payload["Chess Club"]["participants"], list)


def test_signup_adds_participant(client):
    email = "new.student@mergington.edu"

    signup_response = client.post(f"/activities/Chess%20Club/signup?email={email}")
    assert signup_response.status_code == 200
    assert email in activities["Chess Club"]["participants"]


def test_signup_duplicate_participant_returns_400(client):
    existing_email = activities["Chess Club"]["participants"][0]

    response = client.post(f"/activities/Chess%20Club/signup?email={existing_email}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_unknown_activity_returns_404(client):
    response = client.post("/activities/Unknown%20Club/signup?email=test@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    email = activities["Chess Club"]["participants"][0]

    response = client.delete(f"/activities/Chess%20Club/participants?email={email}")

    assert response.status_code == 200
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_unknown_activity_returns_404(client):
    response = client.delete("/activities/Unknown%20Club/participants?email=test@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_non_participant_returns_404(client):
    response = client.delete("/activities/Chess%20Club/participants?email=not.enrolled@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"
