"""
Database initialization and connection management for hybrid architecture
"""
from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient, GEOSPHERE, TEXT
from pymongo.errors import ConnectionFailure, OperationFailure
import logging

# Initialize SQLAlchemy for PostgreSQL
db = SQLAlchemy()

# MongoDB client (will be initialized in init_db)
mongo_client = None
mongo_db = None

logger = logging.getLogger(__name__)


def init_db(app):
    """
    Initialize both PostgreSQL and MongoDB connections
    
    Args:
        app: Flask application instance
    """
    # Initialize PostgreSQL with SQLAlchemy
    db.init_app(app)
    
    # Initialize MongoDB
    global mongo_client, mongo_db
    
    try:
        mongo_uri = app.config.get('MONGO_URI')
        mongo_db_name = app.config.get('MONGO_DB', 'agbot_db')
        
        # Create MongoDB client with connection pooling
        mongo_client = MongoClient(
            mongo_uri,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=45000,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        mongo_client.admin.command('ping')
        mongo_db = mongo_client[mongo_db_name]
        
        logger.info(f"MongoDB connected successfully to database: {mongo_db_name}")
        
        # Initialize MongoDB collections and indexes
        _init_mongodb_collections(mongo_db)
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        logger.warning("Application will run with PostgreSQL only")
        mongo_client = None
        mongo_db = None
    except Exception as e:
        logger.error(f"Unexpected error initializing MongoDB: {e}")
        mongo_client = None
        mongo_db = None


def _init_mongodb_collections(db):
    """
    Initialize MongoDB collections with schema validation and indexes
    
    Args:
        db: MongoDB database instance
    """
    # Create detection_meta collection with schema validation
    try:
        db.create_collection(
            'detection_meta',
            validator={
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['_id', 'user_id', 'pest_label', 'confidence', 'timestamp'],
                    'properties': {
                        '_id': {
                            'bsonType': 'string',
                            'description': 'Must be a string in format scan_{id}'
                        },
                        'user_id': {
                            'bsonType': 'int',
                            'description': 'Must be an integer'
                        },
                        'pest_label': {
                            'bsonType': 'string',
                            'description': 'Must be a string'
                        },
                        'confidence': {
                            'bsonType': 'double',
                            'minimum': 0,
                            'maximum': 1,
                            'description': 'Must be a float between 0 and 1'
                        },
                        'alternatives': {
                            'bsonType': 'array',
                            'description': 'Array of alternative predictions'
                        },
                        'image_info': {
                            'bsonType': 'object',
                            'description': 'Image metadata'
                        },
                        'model_details': {
                            'bsonType': 'object',
                            'description': 'Model inference details'
                        },
                        'location': {
                            'bsonType': 'object',
                            'description': 'GeoJSON location data'
                        },
                        'timestamp': {
                            'bsonType': 'date',
                            'description': 'Must be a date'
                        }
                    }
                }
            }
        )
        logger.info("Created detection_meta collection with schema validation")
    except OperationFailure:
        logger.info("detection_meta collection already exists")
    
    # Create feedback collection
    try:
        db.create_collection(
            'feedback',
            validator={
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['_id', 'detection_id', 'user_id', 'is_correct', 'feedback_time'],
                    'properties': {
                        '_id': {
                            'bsonType': 'string',
                            'description': 'Must be a string in format feedback_{id}'
                        },
                        'detection_id': {
                            'bsonType': 'string',
                            'description': 'Must be a string referencing detection_meta._id'
                        },
                        'user_id': {
                            'bsonType': 'int',
                            'description': 'Must be an integer'
                        },
                        'is_correct': {
                            'bsonType': 'bool',
                            'description': 'Must be a boolean'
                        },
                        'corrected_label': {
                            'bsonType': 'string',
                            'description': 'Corrected pest label if is_correct is false'
                        },
                        'confidence_in_correction': {
                            'bsonType': 'string',
                            'description': 'User confidence in their correction'
                        },
                        'comments': {
                            'bsonType': 'string',
                            'description': 'User comments'
                        },
                        'image_flagged_for_retraining': {
                            'bsonType': 'bool',
                            'description': 'Whether image should be used for retraining'
                        },
                        'feedback_time': {
                            'bsonType': 'date',
                            'description': 'Must be a date'
                        }
                    }
                }
            }
        )
        logger.info("Created feedback collection with schema validation")
    except OperationFailure:
        logger.info("feedback collection already exists")
    
    # Create analytics collection
    try:
        db.create_collection('analytics')
        logger.info("Created analytics collection")
    except OperationFailure:
        logger.info("analytics collection already exists")
    
    # Create indexes
    _create_mongodb_indexes(db)


def _create_mongodb_indexes(db):
    """
    Create indexes for MongoDB collections
    
    Args:
        db: MongoDB database instance
    """
    # Indexes for detection_meta collection
    detection_meta = db['detection_meta']
    
    # Geospatial index for location-based queries
    try:
        detection_meta.create_index([('location', GEOSPHERE)])
        logger.info("Created geospatial index on detection_meta.location")
    except Exception as e:
        logger.warning(f"Could not create geospatial index: {e}")
    
    # Text index for pest_label search
    try:
        detection_meta.create_index([('pest_label', TEXT)])
        logger.info("Created text index on detection_meta.pest_label")
    except Exception as e:
        logger.warning(f"Could not create text index: {e}")
    
    # Index on user_id for user-specific queries
    detection_meta.create_index('user_id')
    
    # Index on timestamp for time-based queries
    detection_meta.create_index('timestamp')
    
    # Indexes for feedback collection
    feedback = db['feedback']
    feedback.create_index('detection_id')
    feedback.create_index('user_id')
    feedback.create_index('feedback_time')
    feedback.create_index('image_flagged_for_retraining')
    
    # Indexes for analytics collection
    analytics = db['analytics']
    analytics.create_index([('region', 1), ('month', 1)])
    analytics.create_index('last_updated')
    
    logger.info("Created all MongoDB indexes")


def get_mongo_db():
    """
    Get MongoDB database instance
    
    Returns:
        MongoDB database instance or None if not connected
    """
    return mongo_db


def close_db_connections():
    """
    Close database connections (called on app teardown)
    """
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")
