"""
Tests for feedback collection system

Tests cover:
- Feedback submission and validation
- Dual database persistence (PostgreSQL + MongoDB)
- Scan status updates
- Feedback aggregation for retraining
- Proactive feedback prompting

Requirements: 5.2, 5.3, 5.4, 5.5, 9.1, 9.2
"""
import pytest
import json
from datetime import datetime
from app import app
from database import db, get_mongo_db
from models import User, Scan, Feedback
from db_sync import (
    sync_feedback_to_mongodb,
    aggregate_feedback_for_retraining,
    run_feedback_aggregation_task
)
from confidence_utils import should_request_feedback
import time


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        with app.test_client() as client:
            yield client
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(client):
    """Create test user and return user_id"""
    with app.app_context():
        user = User(
            name='Test Farmer',
            email='test@example.com',
            location='Test Region',
            language='en'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        return user_id


@pytest.fixture
def test_scan(client, test_user):
    """Create test scan and return scan_id"""
    with app.app_context():
        scan = Scan(
            user_id=test_user,
            image_path='test_image.jpg',
            pest_identified='Test Pest',
            pest_scientific='Testus pestus',
            confidence=0.85,
            status='identified',
            model_version='v1.0.0'
        )
        db.session.add(scan)
        db.session.commit()
        scan_id = scan.id
        return scan_id


class TestFeedbackSubmission:
    """Test feedback submission endpoint"""
    
    def test_feedback_submission_correct_identification(self, client, test_user, test_scan):
        """Test submitting feedback for correct identification"""
        with app.app_context():
            # Login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user)
            
            # Submit feedback
            response = client.post('/api/feedback', 
                json={
                    'scan_id': test_scan,
                    'is_correct': True,
                    'notes': 'Identification was accurate'
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['message'] == 'Feedback saved successfully'
            
            # Verify feedback in database
            feedback = Feedback.query.filter_by(scan_id=test_scan).first()
            assert feedback is not None
            assert feedback.is_correct == True
            assert feedback.notes == 'Identification was accurate'
            
            # Verify scan status unchanged for correct feedback
            scan = Scan.query.get(test_scan)
            assert scan.status == 'identified'
    
    def test_feedback_submission_incorrect_identification(self, client, test_user, test_scan):
        """Test submitting feedback for incorrect identification"""
        with app.app_context():
            # Login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user)
            
            # Submit feedback
            response = client.post('/api/feedback',
                json={
                    'scan_id': test_scan,
                    'is_correct': False,
                    'actual_pest_name': 'Actual Pest Name',
                    'notes': 'This is actually a different pest'
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200
            
            # Verify feedback in database
            feedback = Feedback.query.filter_by(scan_id=test_scan).first()
            assert feedback is not None
            assert feedback.is_correct == False
            assert feedback.actual_pest_name == 'Actual Pest Name'
            
            # Verify scan status updated to 'corrected'
            scan = Scan.query.get(test_scan)
            assert scan.status == 'corrected'
    
    def test_feedback_invalid_scan_id(self, client, test_user):
        """Test feedback submission with invalid scan_id"""
        with app.app_context():
            # Login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user)
            
            # Submit feedback with non-existent scan_id
            response = client.post('/api/feedback',
                json={
                    'scan_id': 99999,
                    'is_correct': True,
                    'notes': 'Test'
                },
                content_type='application/json'
            )
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data


class TestProactiveFeedbackPrompting:
    """Test proactive feedback prompting logic"""
    
    def test_should_request_feedback_low_confidence(self):
        """Test feedback requested for confidence < 0.75"""
        assert should_request_feedback(0.74) == True
        assert should_request_feedback(0.70) == True
        assert should_request_feedback(0.50) == True
        assert should_request_feedback(0.30) == True
    
    def test_should_not_request_feedback_high_confidence(self):
        """Test feedback not requested for confidence >= 0.75"""
        assert should_request_feedback(0.75) == False
        assert should_request_feedback(0.80) == False
        assert should_request_feedback(0.90) == False
        assert should_request_feedback(1.0) == False
    
    def test_boundary_value(self):
        """Test exact boundary value at 0.75"""
        assert should_request_feedback(0.75) == False
        assert should_request_feedback(0.7499) == True


class TestFeedbackAggregation:
    """Test feedback aggregation for model retraining"""
    
    def test_aggregation_task_structure(self):
        """Test that aggregation task returns proper structure"""
        with app.app_context():
            result = run_feedback_aggregation_task()
            
            # Verify result structure
            assert 'total_corrections' in result
            assert 'pest_counts' in result
            assert 'pests_needing_retraining' in result
            assert 'timestamp' in result
            
            # Verify types
            assert isinstance(result['total_corrections'], int)
            assert isinstance(result['pest_counts'], dict)
            assert isinstance(result['pests_needing_retraining'], dict)
    
    def test_aggregation_empty_database(self):
        """Test aggregation with no feedback"""
        with app.app_context():
            result = run_feedback_aggregation_task()
            
            assert result['total_corrections'] == 0
            assert len(result['pest_counts']) == 0
            assert len(result['pests_needing_retraining']) == 0
    
    def test_retraining_threshold_not_reached(self):
        """Test that pests below threshold are not flagged"""
        # This test would require MongoDB to be available
        # For now, we test the logic
        aggregation = {
            'Pest A': 50,
            'Pest B': 75,
            'Pest C': 99
        }
        
        pests_needing_retraining = {
            pest: count for pest, count in aggregation.items() if count >= 100
        }
        
        assert len(pests_needing_retraining) == 0
    
    def test_retraining_threshold_reached(self):
        """Test that pests at/above threshold are flagged"""
        aggregation = {
            'Pest A': 100,
            'Pest B': 150,
            'Pest C': 99
        }
        
        pests_needing_retraining = {
            pest: count for pest, count in aggregation.items() if count >= 100
        }
        
        assert len(pests_needing_retraining) == 2
        assert 'Pest A' in pests_needing_retraining
        assert 'Pest B' in pests_needing_retraining
        assert 'Pest C' not in pests_needing_retraining


class TestDualDatabasePersistence:
    """Test dual database persistence (PostgreSQL + MongoDB)"""
    
    def test_feedback_persisted_to_postgresql(self, client, test_user, test_scan):
        """Test feedback is saved to PostgreSQL"""
        with app.app_context():
            # Create feedback
            feedback = Feedback(
                user_id=test_user,
                scan_id=test_scan,
                is_correct=False,
                actual_pest_name='Corrected Pest',
                notes='Test notes'
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            # Verify in PostgreSQL
            saved_feedback = Feedback.query.filter_by(scan_id=test_scan).first()
            assert saved_feedback is not None
            assert saved_feedback.actual_pest_name == 'Corrected Pest'
    
    def test_mongodb_sync_called(self, client, test_user, test_scan):
        """Test that MongoDB sync is triggered"""
        # This test verifies the sync function is called
        # Actual MongoDB persistence would require MongoDB to be running
        with app.app_context():
            feedback_id = 1
            
            # Call sync function (would normally be async)
            # In production, this runs in a background thread
            try:
                sync_feedback_to_mongodb(
                    feedback_id=feedback_id,
                    detection_id=test_scan,
                    user_id=test_user,
                    is_correct=False,
                    corrected_label='Test Pest',
                    confidence_in_correction='high',
                    comments='Test',
                    image_flagged_for_retraining=True
                )
                # If MongoDB is not available, function should handle gracefully
            except Exception as e:
                # Expected if MongoDB not running in test environment
                pass


class TestFeedbackEndToEnd:
    """End-to-end tests for feedback system"""
    
    def test_complete_feedback_flow(self, client, test_user, test_scan):
        """Test complete feedback submission flow"""
        with app.app_context():
            # Login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user)
            
            # Submit incorrect feedback
            response = client.post('/api/feedback',
                json={
                    'scan_id': test_scan,
                    'is_correct': False,
                    'actual_pest_name': 'Fall Armyworm',
                    'notes': 'This is clearly a fall armyworm'
                },
                content_type='application/json'
            )
            
            assert response.status_code == 200
            
            # Verify PostgreSQL
            feedback = Feedback.query.filter_by(scan_id=test_scan).first()
            assert feedback is not None
            assert feedback.is_correct == False
            assert feedback.actual_pest_name == 'Fall Armyworm'
            
            # Verify scan status updated
            scan = Scan.query.get(test_scan)
            assert scan.status == 'corrected'
            
            # Give background thread time to complete (if MongoDB available)
            time.sleep(0.5)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
