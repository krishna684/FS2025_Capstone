"""
Migration script to move from SQLite to hybrid PostgreSQL + MongoDB architecture
"""
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_from_sqlite():
    """
    Migrate data from existing SQLite database to PostgreSQL + MongoDB
    """
    try:
        # Import after setting up app context
        from app import app
        from database import db, get_mongo_db
        from models import User, Scan, Feedback, PestDatabase
        from db_sync import sync_detection_metadata, sync_feedback_to_mongodb
        
        with app.app_context():
            logger.info("Starting migration from SQLite to hybrid database...")
            
            # Check if SQLite database exists
            sqlite_path = 'instance/agbot.db'
            if not os.path.exists(sqlite_path):
                logger.warning(f"SQLite database not found at {sqlite_path}")
                logger.info("No migration needed - starting fresh")
                return
            
            # Create new database tables
            logger.info("Creating PostgreSQL tables...")
            db.create_all()
            
            # Note: This is a simplified migration script
            # In production, you would use a proper migration tool like Alembic
            # and handle data migration more carefully
            
            logger.info("Migration setup complete!")
            logger.info("Note: This script creates the new schema.")
            logger.info("For data migration from SQLite, please use a proper migration tool.")
            logger.info("Alternatively, users can start fresh with the new database.")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    migrate_from_sqlite()
