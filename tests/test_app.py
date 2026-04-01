"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy
from src.app import app, activities


client = TestClient(app)

# Store the original activities state for reset between tests
ORIGINAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test"""
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))
    yield
    # Cleanup after test
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))


class TestGetActivities:
    """Test suite for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """Should return all activities with their details"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_returns_correct_structure(self):
        """Should return activities with correct data structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self):
        """Should successfully sign up a student for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        assert "newstudent@mergington.edu" in activities_response.json()["Chess Club"]["participants"]
    
    def test_signup_duplicate_returns_400(self):
        """Should reject duplicate signup with 400 status"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_for_nonexistent_activity_returns_404(self):
        """Should return 404 when activity does not exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_with_existing_participant(self):
        """Should allow existing participant to appear in activity"""
        response = client.get("/activities")
        initial_participants = response.json()["Chess Club"]["participants"]
        assert len(initial_participants) > 0


class TestWithdrawFromActivity:
    """Test suite for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_withdraw_from_activity_success(self):
        """Should successfully remove a participant from an activity"""
        email = "removetest@mergington.edu"
        
        # First, sign up
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Then, withdraw
        response = client.delete(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Chess Club"]["participants"]
    
    def test_withdraw_nonexistent_email_returns_404(self):
        """Should return 404 when email not signed up"""
        response = client.delete(
            "/activities/Chess Club/signup?email=notregistered@mergington.edu"
        )
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]
    
    def test_withdraw_from_nonexistent_activity_returns_404(self):
        """Should return 404 when activity does not exist"""
        response = client.delete(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_withdraw_from_existing_participant(self):
        """Should successfully remove an existing participant"""
        # Get initial state
        response = client.get("/activities")
        initial_participants = response.json()["Programming Class"]["participants"]
        initial_count = len(initial_participants)
        
        if initial_count > 0:
            email_to_remove = initial_participants[0]
            
            # Withdraw the participant
            delete_response = client.delete(
                f"/activities/Programming Class/signup?email={email_to_remove}"
            )
            assert delete_response.status_code == 200
            
            # Verify participant count decreased
            updated_response = client.get("/activities")
            updated_participants = updated_response.json()["Programming Class"]["participants"]
            assert len(updated_participants) == initial_count - 1


class TestRedirect:
    """Test suite for root redirect"""
    
    def test_root_redirects_to_static(self):
        """Should redirect root path to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
