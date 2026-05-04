"""
FastAPI endpoint tests using the AAA (Arrange-Act-Assert) pattern.

This test suite covers all endpoints with both happy paths and error cases,
ensuring the API behaves correctly under various conditions.
"""

import pytest


class TestRootEndpoint:
    """Test suite for GET / endpoint."""

    def test_get_root_redirects_to_index_html(self, client):
        """
        Verify that GET / redirects to the static index.html page.
        
        AAA Pattern:
        - Arrange: TestClient is ready to make requests
        - Act: Make GET request to /
        - Assert: Verify 307 redirect status and correct Location header
        """
        # Arrange
        expected_redirect_url = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect_url


class TestGetActivitiesEndpoint:
    """Test suite for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """
        Verify that GET /activities returns all available activities.
        
        AAA Pattern:
        - Arrange: Know the expected number of activities in the app
        - Act: Make GET request to /activities
        - Assert: Verify response status and that activities dict is returned
        """
        # Arrange
        expected_min_activities = 3  # Chess Club, Programming Class, Gym Class (at minimum)
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(activities, dict)
        assert len(activities) >= expected_min_activities
        
    def test_get_activities_includes_activity_details(self, client):
        """
        Verify that each activity contains required fields.
        
        AAA Pattern:
        - Arrange: Know the required activity fields
        - Act: Get activities and inspect the first one
        - Assert: Verify all required fields are present
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        first_activity = next(iter(activities.values()))
        
        # Assert
        assert all(field in first_activity for field in required_fields)
        assert isinstance(first_activity["participants"], list)
        assert isinstance(first_activity["max_participants"], int)


class TestSignupEndpoint:
    """Test suite for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_valid_student_succeeds(self, client):
        """
        Verify that a valid student can sign up for an activity.
        
        AAA Pattern:
        - Arrange: Prepare valid activity name and email
        - Act: Make POST request to signup endpoint
        - Assert: Verify 200 status and success message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        assert activity_name in result["message"]
        
    def test_signup_multiple_students_succeeds(self, client):
        """
        Verify that multiple different students can sign up for the same activity.
        
        AAA Pattern:
        - Arrange: Prepare list of different emails for same activity
        - Act: Make multiple POST requests for same activity
        - Assert: All requests succeed
        """
        # Arrange
        activity_name = "Programming Class"
        students = ["alice@mergington.edu", "bob@mergington.edu", "charlie@mergington.edu"]
        
        # Act & Assert (for each student)
        for email in students:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Verify that signup for a non-existent activity returns 404.
        
        AAA Pattern:
        - Arrange: Prepare invalid activity name and valid email
        - Act: Make POST request to signup endpoint
        - Assert: Verify 404 status and error detail
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()
    
    def test_signup_duplicate_student_returns_400(self, client):
        """
        Verify that a student already signed up cannot sign up again.
        
        AAA Pattern:
        - Arrange: Get an existing participant from an activity
        - Act: Try to signup that same student again
        - Assert: Verify 400 status and appropriate error message
        """
        # Arrange
        activity_name = "Chess Club"
        # Michael is already in Chess Club (from initial data)
        email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "already signed up" in result["detail"].lower()


class TestRemoveEndpoint:
    """Test suite for DELETE /activities/{activity_name}/remove endpoint."""

    def test_remove_existing_participant_succeeds(self, client):
        """
        Verify that an existing participant can be removed from an activity.
        
        AAA Pattern:
        - Arrange: Identify an existing participant in an activity
        - Act: Make DELETE request to remove endpoint
        - Assert: Verify 200 status and success message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Existing participant
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        assert "Removed" in result["message"]
    
    def test_remove_nonexistent_activity_returns_404(self, client):
        """
        Verify that removing a participant from a non-existent activity returns 404.
        
        AAA Pattern:
        - Arrange: Prepare invalid activity name
        - Act: Make DELETE request to remove endpoint
        - Assert: Verify 404 status and error detail
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()
    
    def test_remove_non_participant_returns_400(self, client):
        """
        Verify that removing a non-participant returns 400 error.
        
        AAA Pattern:
        - Arrange: Prepare an email that is NOT in the activity
        - Act: Make DELETE request to remove endpoint
        - Assert: Verify 400 status and appropriate error message
        """
        # Arrange
        activity_name = "Gym Class"
        email = "notstudent@mergington.edu"  # Not a participant
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "not signed up" in result["detail"].lower()
    
    def test_signup_then_remove_works_correctly(self, client):
        """
        Verify the complete workflow: signup a new student, then remove them.
        
        AAA Pattern:
        - Arrange: Prepare new student email and target activity
        - Act: First signup the student, then remove them
        - Assert: Both operations succeed with correct messages
        """
        # Arrange
        activity_name = "Programming Class"
        email = "newstudent@mergington.edu"
        
        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert - Signup succeeded
        assert signup_response.status_code == 200
        
        # Act - Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        
        # Assert - Remove succeeded
        assert remove_response.status_code == 200
        
        # Act - Try to signup again (should succeed now)
        second_signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert - Second signup succeeds
        assert second_signup_response.status_code == 200
