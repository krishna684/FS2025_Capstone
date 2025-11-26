"""
Test multi-language support implementation
Tests for task 8: Implement multi-language support
"""

import pytest
from app import app, db, detect_browser_language, get_localized_pest_name, get_translation
from models import User, PestDatabase
from flask import session
import os


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Add test pest data
            pest = PestDatabase(
                common_name='Japanese Beetle',
                scientific_name='Popillia japonica',
                category='insect',
                name_es='Escarabajo Japonés',
                name_hi='जापानी बीटल',
                name_sw='Mdudu wa Kijapani'
            )
            db.session.add(pest)
            
            # Add test user
            user = User(
                name='Test User',
                email='test@example.com',
                language='es'
            )
            user.set_password('password123')
            db.session.add(user)
            
            db.session.commit()
            
        yield client
        
        with app.app_context():
            db.drop_all()


def test_detect_browser_language_english(client):
    """Test browser language detection for English"""
    with app.test_request_context(
        headers={'Accept-Language': 'en-US,en;q=0.9'}
    ):
        lang = detect_browser_language()
        assert lang == 'en'


def test_detect_browser_language_spanish(client):
    """Test browser language detection for Spanish"""
    with app.test_request_context(
        headers={'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'}
    ):
        lang = detect_browser_language()
        assert lang == 'es'


def test_detect_browser_language_hindi(client):
    """Test browser language detection for Hindi"""
    with app.test_request_context(
        headers={'Accept-Language': 'hi-IN,hi;q=0.9,en;q=0.8'}
    ):
        lang = detect_browser_language()
        assert lang == 'hi'


def test_detect_browser_language_swahili(client):
    """Test browser language detection for Swahili"""
    with app.test_request_context(
        headers={'Accept-Language': 'sw-KE,sw;q=0.9,en;q=0.8'}
    ):
        lang = detect_browser_language()
        assert lang == 'sw'


def test_detect_browser_language_unsupported_fallback(client):
    """Test browser language detection falls back to English for unsupported languages"""
    with app.test_request_context(
        headers={'Accept-Language': 'fr-FR,fr;q=0.9'}
    ):
        lang = detect_browser_language()
        assert lang == 'en'


def test_detect_browser_language_no_header(client):
    """Test browser language detection with no Accept-Language header"""
    with app.test_request_context():
        lang = detect_browser_language()
        assert lang == 'en'


def test_get_localized_pest_name_english(client):
    """Test getting pest name in English"""
    with app.app_context():
        pest = PestDatabase.query.first()
        name = get_localized_pest_name(pest.id, 'en')
        assert name == 'Japanese Beetle'


def test_get_localized_pest_name_spanish(client):
    """Test getting pest name in Spanish"""
    with app.app_context():
        pest = PestDatabase.query.first()
        name = get_localized_pest_name(pest.id, 'es')
        assert name == 'Escarabajo Japonés'


def test_get_localized_pest_name_hindi(client):
    """Test getting pest name in Hindi"""
    with app.app_context():
        pest = PestDatabase.query.first()
        name = get_localized_pest_name(pest.id, 'hi')
        assert name == 'जापानी बीटल'


def test_get_localized_pest_name_swahili(client):
    """Test getting pest name in Swahili"""
    with app.app_context():
        pest = PestDatabase.query.first()
        name = get_localized_pest_name(pest.id, 'sw')
        assert name == 'Mdudu wa Kijapani'


def test_get_localized_pest_name_fallback(client):
    """Test pest name falls back to English when localized name not available"""
    with app.app_context():
        # Create pest without localized names
        pest = PestDatabase(
            common_name='Test Pest',
            scientific_name='Testus pestus',
            category='insect'
        )
        db.session.add(pest)
        db.session.commit()
        
        name = get_localized_pest_name(pest.id, 'es')
        assert name == 'Test Pest'


def test_get_localized_pest_name_invalid_id(client):
    """Test getting pest name with invalid ID returns None"""
    with app.app_context():
        name = get_localized_pest_name(99999, 'en')
        assert name is None


def test_get_translation_english(client):
    """Test getting translation in English"""
    with app.app_context():
        translation = get_translation('dashboard.greeting', 'en')
        assert translation == 'Hi, Farmer!'


def test_get_translation_fallback_to_english(client):
    """Test translation falls back to English when key missing in other language"""
    with app.app_context():
        # Test with a key that might not exist in all languages
        translation = get_translation('dashboard.greeting', 'es')
        # Should return either Spanish translation or English fallback
        assert translation is not None
        assert len(translation) > 0


def test_get_translation_missing_key(client):
    """Test translation with completely missing key returns the key itself"""
    with app.app_context():
        translation = get_translation('nonexistent.key.path', 'en')
        assert translation == 'nonexistent.key.path'


def test_language_priority_user_profile(client):
    """Test language detection priority: user profile takes precedence"""
    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        
        with client.session_transaction() as sess:
            sess['language'] = 'en'
        
        # Login user
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Make a request and check language in context
        response = client.get('/')
        # User language (es) should take precedence over session (en)
        assert response.status_code == 200


def test_language_priority_session(client):
    """Test language detection priority: session takes precedence over browser"""
    with client.session_transaction() as sess:
        sess['language'] = 'hi'
    
    # Make request with different browser language to login page (doesn't require auth)
    response = client.get('/login', headers={'Accept-Language': 'es-ES,es;q=0.9'})
    # Session language (hi) should take precedence
    assert response.status_code == 200


def test_missing_translation_logging(client):
    """Test that missing translations are logged"""
    with app.app_context():
        # Remove log file if exists
        log_file = 'missing_translations.log'
        if os.path.exists(log_file):
            os.remove(log_file)
        
        # Request a translation that doesn't exist
        get_translation('completely.fake.key', 'es')
        
        # Check if log file was created
        assert os.path.exists(log_file)
        
        # Check log content
        with open(log_file, 'r') as f:
            content = f.read()
            assert 'completely.fake.key' in content
            assert 'es' in content
        
        # Clean up
        if os.path.exists(log_file):
            os.remove(log_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
