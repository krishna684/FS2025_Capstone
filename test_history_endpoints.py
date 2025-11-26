"""
Test suite for scan history and export endpoints
Tests Requirements 6.1, 6.2, 6.3, 6.4
"""
import pytest
import json
import csv
import io
from datetime import datetime
from app import app
from database import db, init_db
from models import User, Scan, PestDatabase, Treatment, IPMRecommendation


@pytest.fixture(scope='function')
def client():
    """Create test client with in-memory database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            # Drop and recreate all tables for each test
            db.drop_all()
            db.create_all()
            
            # Create test user
            user = User(
                name='Test Farmer',
                email='test@example.com',
                phone='1234567890',
                location='Test Region',
                language='en'
            )
            user.set_password('testpass123')
            db.session.add(user)
            
            # Create test pest
            pest = PestDatabase(
                common_name='Test Beetle',
                scientific_name='Testus beetleus',
                category='insect',
                name_es='Escarabajo de Prueba',
                name_hi='परीक्षण बीटल',
                name_sw='Mdudu wa Majaribio'
            )
            db.session.add(pest)
            
            # Create test scans
            scan1 = Scan(
                user_id=1,
                image_path='static/uploads/test1.jpg',
                pest_identified='Test Beetle',
                pest_scientific='Testus beetleus',
                confidence=0.92,
                status='identified',
                severity='moderate',
                crop_type='corn',
                field_name='Field A',
                model_version='v2.1.0'
            )
            
            scan2 = Scan(
                user_id=1,
                image_path='static/uploads/test2.jpg',
                pest_identified='Aphids',
                pest_scientific='Aphidoidea',
                confidence=0.87,
                status='corrected',
                severity='mild',
                crop_type='tomato',
                field_name='Field B',
                model_version='v2.1.0'
            )
            
            scan3 = Scan(
                user_id=1,
                image_path='static/uploads/test3.jpg',
                pest_identified='Spider Mites',
                pest_scientific='Tetranychidae',
                confidence=0.95,
                status='identified',
                severity='severe',
                crop_type='beans',
                field_name='Field C',
                model_version='v2.1.0'
            )
            
            db.session.add_all([scan1, scan2, scan3])
            db.session.commit()
            
        yield client
        
        # Cleanup after test
        with app.app_context():
            db.session.remove()
            db.drop_all()


def login(client, email='test@example.com', password='testpass123'):
    """Helper function to log in"""
    return client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)


def test_get_history_endpoint(client):
    """
    Test GET /api/history endpoint
    Validates Requirements 6.1, 6.2
    """
    # Login first
    login(client)
    
    # Get history
    response = client.get('/api/history')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Should return list of scans
    assert isinstance(data, list)
    assert len(data) == 3
    
    # Check first scan has required fields
    scan = data[0]
    assert 'id' in scan
    assert 'date' in scan
    assert 'pest_identified' in scan
    assert 'confidence' in scan
    assert 'severity' in scan
    
    # Verify scans are ordered by created_at DESC (most recent first)
    # Since all created at same time, just verify they're all present
    pest_names = [s['pest_identified'] for s in data]
    assert 'Test Beetle' in pest_names
    assert 'Aphids' in pest_names
    assert 'Spider Mites' in pest_names


def test_get_history_empty(client):
    """Test history endpoint with no scans"""
    # Create new user with no scans
    with app.app_context():
        user = User(
            name='Empty User',
            email='empty@example.com',
            phone='9999999999',
            location='Test Region',
            language='en'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
    
    # Login as new user
    login(client, email='empty@example.com')
    
    response = client.get('/api/history')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_scan_detail_endpoint(client):
    """
    Test GET /api/history/<scan_id> endpoint
    Validates Requirements 6.3
    """
    # Login first
    login(client)
    
    # Get detail for scan ID 1
    response = client.get('/api/history/1')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Check all required fields are present
    assert data['id'] == 1
    assert data['pest_identified'] == 'Test Beetle'
    assert data['pest_scientific'] == 'Testus beetleus'
    assert data['confidence'] == 92.0  # Converted to percentage
    assert data['severity'] == 'moderate'
    assert data['status'] == 'identified'
    assert data['crop_type'] == 'corn'
    assert data['field_name'] == 'Field A'
    assert data['model_version'] == 'v2.1.0'
    assert data['image_path'] == 'static/uploads/test1.jpg'
    
    # Should include recommendations (may be empty if no IPM data)
    assert 'recommendations' in data
    assert isinstance(data['recommendations'], list)


def test_get_scan_detail_not_found(client):
    """Test scan detail endpoint with non-existent scan ID"""
    login(client)
    
    response = client.get('/api/history/9999')
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_get_scan_detail_unauthorized(client):
    """Test scan detail endpoint without authentication"""
    # Don't login
    response = client.get('/api/history/1')
    
    # Should redirect to login or return 401
    assert response.status_code in [302, 401]


def test_export_scans_json(client):
    """
    Test GET /api/export/scans?format=json endpoint
    Validates Requirements 6.4
    """
    login(client)
    
    response = client.get('/api/export/scans?format=json')
    
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/json'
    assert 'attachment' in response.headers['Content-Disposition']
    assert 'scan_history_' in response.headers['Content-Disposition']
    assert '.json' in response.headers['Content-Disposition']
    
    data = json.loads(response.data)
    
    # Should be valid JSON array
    assert isinstance(data, list)
    assert len(data) == 3
    
    # Check structure
    scan = data[0]
    assert 'id' in scan
    assert 'date' in scan
    assert 'pest_identified' in scan
    assert 'confidence' in scan


def test_export_scans_csv(client):
    """
    Test GET /api/export/scans?format=csv endpoint
    Validates Requirements 6.4
    """
    login(client)
    
    response = client.get('/api/export/scans?format=csv')
    
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv'
    assert 'attachment' in response.headers['Content-Disposition']
    assert 'scan_history_' in response.headers['Content-Disposition']
    assert '.csv' in response.headers['Content-Disposition']
    
    # Parse CSV
    csv_data = response.data.decode('utf-8')
    reader = csv.reader(io.StringIO(csv_data))
    rows = list(reader)
    
    # Should have header row + 3 data rows
    assert len(rows) == 4
    
    # Check headers
    headers = rows[0]
    assert 'ID' in headers
    assert 'Date' in headers
    assert 'Pest Identified' in headers
    assert 'Confidence (%)' in headers
    assert 'Severity' in headers
    
    # Check data rows
    data_row = rows[1]
    assert len(data_row) == len(headers)


def test_export_scans_invalid_format(client):
    """Test export endpoint with invalid format parameter"""
    login(client)
    
    response = client.get('/api/export/scans?format=xml')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Unsupported format' in data['error']


def test_export_scans_default_format(client):
    """Test export endpoint defaults to JSON when no format specified"""
    login(client)
    
    response = client.get('/api/export/scans')
    
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/json'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
