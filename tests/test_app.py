from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)

# Keep a pristine snapshot of the in-memory activity state for test isolation.
ORIGINAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities() -> None:
    """Reset the global in-memory activities dict between tests."""

    # Restore the global state before each test.
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))
    yield

    # Ensure changes from a test cannot leak into subsequent tests.
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))


def test_root_redirects_to_static_index() -> None:
    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_expected_structure() -> None:
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "description" in data["Chess Club"]


def test_signup_for_activity_success() -> None:
    # Arrange
    email = "tester@example.com"
    activity = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in activities[activity]["participants"]


def test_signup_for_nonexistent_activity_returns_404() -> None:
    # Act
    response = client.post("/activities/NotAnActivity/signup", params={"email": "x@example.com"})

    # Assert
    assert response.status_code == 404


def test_signup_duplicate_email_returns_400() -> None:
    # Arrange
    activity = "Chess Club"
    existing_email = activities[activity]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": existing_email})

    # Assert
    assert response.status_code == 400


def test_remove_participant_success() -> None:
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]

    # Act
    response = client.delete(f"/activities/{activity}/participants", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity}"}
    assert email not in activities[activity]["participants"]


def test_remove_participant_not_found_returns_404() -> None:
    # Act
    response = client.delete(
        "/activities/Chess Club/participants", params={"email": "notfound@example.com"}
    )

    # Assert
    assert response.status_code == 404
