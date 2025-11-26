"""
Database configuration for hybrid PostgreSQL + MongoDB architecture
"""
import os
from urllib.parse import quote_plus

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-jwt-secret-key')
    
    # PostgreSQL Configuration
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'agbot_user')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'agbot_password')
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'agbot_db')
    
    # Build PostgreSQL URI
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{quote_plus(POSTGRES_PASSWORD)}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # MongoDB Configuration
    MONGO_USER = os.environ.get('MONGO_USER', 'agbot_user')
    MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', 'agbot_password')
    MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
    MONGO_PORT = os.environ.get('MONGO_PORT', '27017')
    MONGO_DB = os.environ.get('MONGO_DB', 'agbot_db')
    
    # Build MongoDB URI
    MONGO_URI = (
        f"mongodb://{MONGO_USER}:{quote_plus(MONGO_PASSWORD)}"
        f"@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"
    )
    
    # Upload configuration
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size


class DevelopmentConfig(Config):
    """Development configuration - uses SQLite for easy setup"""
    DEBUG = True
    # Override with SQLite for development if PostgreSQL not available
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///agbot.db'
    )
    # Override with local MongoDB if not available
    MONGO_URI = os.environ.get(
        'MONGO_URI',
        'mongodb://localhost:27017/agbot_db'
    )


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Use environment variables for production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
