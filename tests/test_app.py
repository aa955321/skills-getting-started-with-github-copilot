import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """Should return all available activities"""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert len(data) > 0
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_has_required_fields(self):
        """Each activity should have required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity in data.items():
            for field in required_fields:
                assert field in activity
            assert isinstance(activity["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_success(self):
        """Student should successfully sign up for an activity"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Tennis Club"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]
        assert activity in response.json()["message"]
    
    def test_signup_adds_participant_to_activity(self):
        """Participant should be added to the activity list"""
        # Arrange
        email = "newstudent@test.com"
        activity = "Tennis Club"
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity]["participants"].copy()
        
        # Act
        client.post(f"/activities/{activity}/signup?email={email}")
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity]["participants"]
        
        # Assert
        assert len(participants_after) == len(participants_before) + 1
        assert email in participants_after
    
    def test_signup_duplicate_email_returns_400(self):
        """Should not allow duplicate signup for same activity"""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_invalid_activity_returns_404(self):
        """Should return 404 for non-existent activity"""
        # Arrange
        email = "test@example.com"
        invalid_activity = "Nonexistent Club"
        
        # Act
        response = client.post(f"/activities/{invalid_activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_same_email_different_activities(self):
        """Student should be able to sign up for multiple activities"""
        # Arrange
        email = "multiactivity@test.com"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={email}")
        response2 = client.post(f"/activities/{activity2}/signup?email={email}")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity1]["participants"]
        assert email in data[activity2]["participants"]
    
    def test_signup_empty_email(self):
        """Should handle empty email parameter"""
        # Arrange
        empty_email = ""
        activity = "Chess Club"
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={empty_email}")
        
        # Assert
        # FastAPI will accept it but we might want to validate this behavior
        # For now, just verify it doesn't crash
        assert response.status_code in [200, 400]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self):
        """Student should successfully unregister from an activity"""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_unregister_removes_participant(self):
        """Participant should be removed from activity list"""
        # Arrange
        email = "daniel@mergington.edu"
        activity = "Chess Club"
        response_before = client.get("/activities")
        participants_before = len(response_before.json()[activity]["participants"])
        
        # Act
        client.delete(f"/activities/{activity}/unregister?email={email}")
        response_after = client.get("/activities")
        participants_after = len(response_after.json()[activity]["participants"])
        
        # Assert
        assert participants_after == participants_before - 1
        assert email not in response_after.json()[activity]["participants"]
    
    def test_unregister_invalid_activity_returns_404(self):
        """Should return 404 for non-existent activity"""
        # Arrange
        email = "test@example.com"
        invalid_activity = "Nonexistent Club"
        
        # Act
        response = client.delete(f"/activities/{invalid_activity}/unregister?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_student_not_in_activity_returns_404(self):
        """Should return 404 if student not in activity"""
        # Arrange
        email = "notinclass@example.com"
        activity = "Chess Club"
        
        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert
        assert response.status_code == 404
        assert "Student not found" in response.json()["detail"]
    
    def test_unregister_then_signup_again(self):
        """Student should be able to signup after unregistering"""
        # Arrange
        email = "reregister@test.com"
        activity = "Science Club"
        
        # Act - Sign up first time
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Act - Unregister
        response_unregister = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Act - Sign up again
        response_signup = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response_unregister.status_code == 200
        assert response_signup.status_code == 200
        
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_full_signup_unregister_workflow(self):
        """Test complete signup and unregister workflow"""
        # Arrange
        email = "workflow@test.com"
        activity = "Music Band"
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Act - Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        response_after_signup = client.get("/activities")
        count_after_signup = len(response_after_signup.json()[activity]["participants"])
        
        # Assert signup
        assert signup_response.status_code == 200
        assert count_after_signup == initial_count + 1
        assert email in response_after_signup.json()[activity]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        response_after_unregister = client.get("/activities")
        count_after_unregister = len(response_after_unregister.json()[activity]["participants"])
        
        # Assert unregister
        assert unregister_response.status_code == 200
        assert count_after_unregister == initial_count
        assert email not in response_after_unregister.json()[activity]["participants"]
    
    def test_multiple_students_same_activity(self):
        """Test multiple students signing up for same activity"""
        # Arrange
        students = [
            "student1@test.com",
            "student2@test.com",
            "student3@test.com"
        ]
        activity = "Debate Team"
        response_before = client.get("/activities")
        initial_count = len(response_before.json()[activity]["participants"])
        
        # Act
        for student in students:
            client.post(f"/activities/{activity}/signup?email={student}")
        
        response_after = client.get("/activities")
        final_count = len(response_after.json()[activity]["participants"])
        participants = response_after.json()[activity]["participants"]
        
        # Assert
        assert final_count == initial_count + len(students)
        for student in students:
            assert student in participants
    
    def test_student_multiple_activities_workflow(self):
        """Test student signing up for and unregistering from multiple activities"""
        # Arrange
        email = "multitest@test.com"
        activities_list = ["Chess Club", "Programming Class", "Art Studio"]
        
        # Act - Sign up for all
        for activity in activities_list:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Assert all signups
        response = client.get("/activities")
        for activity in activities_list:
            assert email in response.json()[activity]["participants"]
        
        # Act - Unregister from middle one
        client.delete(f"/activities/{activities_list[1]}/unregister?email={email}")
        
        # Assert partial unregister
        response = client.get("/activities")
        assert email in response.json()[activities_list[0]]["participants"]
        assert email not in response.json()[activities_list[1]]["participants"]
        assert email in response.json()[activities_list[2]]["participants"]
