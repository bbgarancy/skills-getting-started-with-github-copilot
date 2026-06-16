from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)
initial_activities = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(deepcopy(initial_activities))
    yield


def test_get_activities_returns_all_activities():
    # Arrange
    expected_names = set(initial_activities.keys())

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == expected_names
    for activity in data.values():
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


def test_signup_adds_participant_to_activity():
    # Arrange
    email = "newstudent@mergington.edu"
    activity_name = "Chess Club"
    path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(path, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    activity_data = client.get("/activities").json()[activity_name]
    assert email in activity_data["participants"]


def test_unregister_removes_participant():
    # Arrange
    email = "removeme@mergington.edu"
    activity_name = "Chess Club"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"
    client.post(signup_path, params={"email": email})

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_unregister_nonexistent_participant_returns_404():
    # Arrange
    email = "missing@mergington.edu"
    activity_name = "Chess Club"
    path = f"/activities/{quote(activity_name, safe='')}/participants"

    # Act
    response = client.delete(path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_signup_invalid_activity_returns_404():
    # Arrange
    email = "student@mergington.edu"
    activity_name = "Nonexistent Club"
    path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
