"""
Test model versioning and tracking functionality
Tests for Requirements 9.4, 9.5
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from database import db
from models import User, Scan


class TestModelVersioning:
    """Test model version logging and tracking"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                
                # Create test user
                user = User(
                    email='test@example.com',
                    name='Test User',
                    location='Test Region'
                )
                user.set_password('password123')
                db.session.add(user)
                db.session.commit()
                
                yield client
                
                db.session.remove()
                db.drop_all()
    
    def test_scan_stores_model_version(self, client):
        """Test that scans store model version in database"""
        with app.app_context():
            # Create a scan with model version
            user = User.query.filter_by(email='test@example.com').first()
            
            scan = Scan(
                user_id=user.id,
                image_path='test_image.jpg',
                pest_identified='Test Pest',
                pest_scientific='Testus pestus',
                confidence=0.92,
                status='identified',
                model_version='v2.1.0'
            )
            
            db.session.add(scan)
            db.session.commit()
            
            # Verify model version is stored
            saved_scan = Scan.query.filter_by(user_id=user.id).first()
            assert saved_scan is not None
            assert saved_scan.model_version == 'v2.1.0'
    
    def test_scan_to_dict_includes_model_version(self, client):
        """Test that scan.to_dict() includes model_version"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            scan = Scan(
                user_id=user.id,
                image_path='test_image.jpg',
                pest_identified='Test Pest',
                confidence=0.85,
                model_version='v2.1.0'
            )
            
            db.session.add(scan)
            db.session.commit()
            
            # Convert to dict
            scan_dict = scan.to_dict()
            
            # Verify model_version is included
            assert 'model_version' in scan_dict
            assert scan_dict['model_version'] == 'v2.1.0'
    
    def test_model_performance_endpoint_requires_auth(self, client):
        """Test that model performance endpoint requires authentication"""
        response = client.get('/api/admin/model-performance')
        
        # Should redirect to login or return 401
        assert response.status_code in [302, 401]
    
    def test_model_performance_endpoint_with_auth(self, client):
        """Test model performance endpoint returns data when authenticated"""
        with app.app_context():
            # Create test scans with different model versions
            user = User.query.filter_by(email='test@example.com').first()
            
            # Version v2.0.0 - 10 scans, 2 corrections
            for i in range(10):
                status = 'corrected' if i < 2 else 'identified'
                scan = Scan(
                    user_id=user.id,
                    image_path=f'test_{i}.jpg',
                    pest_identified='Fall Armyworm',
                    confidence=0.88,
                    status=status,
                    model_version='v2.0.0'
                )
                db.session.add(scan)
            
            # Version v2.1.0 - 15 scans, 1 correction (better performance)
            for i in range(15):
                status = 'corrected' if i < 1 else 'identified'
                scan = Scan(
                    user_id=user.id,
                    image_path=f'test_v21_{i}.jpg',
                    pest_identified='Aphids',
                    confidence=0.92,
                    status=status,
                    model_version='v2.1.0'
                )
                db.session.add(scan)
            
            db.session.commit()
            
            # Login
            client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            
            # Get model performance
            response = client.get('/api/admin/model-performance')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['success'] is True
            assert 'performance' in data
            assert len(data['performance']) == 2
            
            # Check v2.1.0 performance (should be first - sorted by version desc)
            v21_perf = next((p for p in data['performance'] if p['model_version'] == 'v2.1.0'), None)
            assert v21_perf is not None
            assert v21_perf['total_detections'] == 15
            assert v21_perf['corrections'] == 1
            assert v21_perf['correction_rate'] < 10  # Less than 10% correction rate
            assert v21_perf['estimated_accuracy'] > 90  # Greater than 90% accuracy
            
            # Check v2.0.0 performance
            v20_perf = next((p for p in data['performance'] if p['model_version'] == 'v2.0.0'), None)
            assert v20_perf is not None
            assert v20_perf['total_detections'] == 10
            assert v20_perf['corrections'] == 2
            assert v20_perf['correction_rate'] == 20  # 20% correction rate
            assert v20_perf['estimated_accuracy'] == 80  # 80% accuracy
    
    def test_model_performance_with_version_filter(self, client):
        """Test filtering model performance by specific version"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            # Create scans with different versions
            for version in ['v2.0.0', 'v2.1.0', 'v2.2.0']:
                scan = Scan(
                    user_id=user.id,
                    image_path=f'test_{version}.jpg',
                    pest_identified='Test Pest',
                    confidence=0.90,
                    model_version=version
                )
                db.session.add(scan)
            
            db.session.commit()
            
            # Login
            client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            
            # Filter by specific version
            response = client.get('/api/admin/model-performance?version=v2.1.0')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['success'] is True
            assert len(data['performance']) == 1
            assert data['performance'][0]['model_version'] == 'v2.1.0'
            assert data['filters']['version'] == 'v2.1.0'
    
    def test_model_performance_with_date_filter(self, client):
        """Test filtering model performance by date range"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            # Create scans with different dates
            old_date = datetime.now() - timedelta(days=30)
            recent_date = datetime.now() - timedelta(days=5)
            
            # Old scan
            old_scan = Scan(
                user_id=user.id,
                image_path='old_scan.jpg',
                pest_identified='Old Pest',
                confidence=0.85,
                model_version='v2.0.0',
                created_at=old_date
            )
            db.session.add(old_scan)
            
            # Recent scan
            recent_scan = Scan(
                user_id=user.id,
                image_path='recent_scan.jpg',
                pest_identified='Recent Pest',
                confidence=0.90,
                model_version='v2.1.0',
                created_at=recent_date
            )
            db.session.add(recent_scan)
            
            db.session.commit()
            
            # Login
            client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            
            # Filter by recent date range (last 7 days)
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            response = client.get(f'/api/admin/model-performance?start_date={start_date}')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['success'] is True
            # Should only include recent scan
            assert len(data['performance']) == 1
            assert data['performance'][0]['model_version'] == 'v2.1.0'


class TestAIServiceModelVersion:
    """Test AI service includes model version in response"""
    
    def test_ai_service_model_versions_function(self):
        """Test get_model_versions function returns version info"""
        # Import here to avoid loading TensorFlow in all tests
        try:
            from ai_service.models import get_model_versions
            
            versions = get_model_versions()
            
            assert 'primary_model_version' in versions
            assert 'fallback_model_version' in versions
            assert isinstance(versions['primary_model_version'], str)
            assert isinstance(versions['fallback_model_version'], str)
            
        except ImportError:
            pytest.skip("AI service modules not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
