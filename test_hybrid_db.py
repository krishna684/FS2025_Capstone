"""
Test script to verify hybrid database functionality
"""
import os
os.environ['FLASK_ENV'] = 'development'

from app import app
from database import db, get_mongo_db
from models import User, Scan, PestDatabase, Treatment, IPMRecommendation
from db_sync import sync_detection_metadata, get_detection_metadata
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_postgresql():
    """Test PostgreSQL functionality"""
    logger.info("=" * 60)
    logger.info("Testing PostgreSQL")
    logger.info("=" * 60)
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Test user query
        users = User.query.all()
        logger.info(f"✓ Users in database: {len(users)}")
        
        # Test pest query
        pests = PestDatabase.query.all()
        logger.info(f"✓ Pests in database: {len(pests)}")
        for pest in pests[:3]:
            logger.info(f"  - {pest.common_name} ({pest.scientific_name})")
        
        # Test treatment query
        treatments = Treatment.query.all()
        logger.info(f"✓ Treatments in database: {len(treatments)}")
        for treatment in treatments[:3]:
            logger.info(f"  - {treatment.name} ({treatment.type})")
        
        # Test IPM recommendations
        recommendations = IPMRecommendation.query.all()
        logger.info(f"✓ IPM Recommendations in database: {len(recommendations)}")
        
        # Test multilingual support
        if pests:
            pest = pests[0]
            logger.info(f"\n✓ Multilingual support test:")
            logger.info(f"  English: {pest.common_name}")
            logger.info(f"  Spanish: {pest.name_es}")
            logger.info(f"  Hindi: {pest.name_hi}")
            logger.info(f"  Swahili: {pest.name_sw}")
        
        # Test IPM recommendation query
        if pests and recommendations:
            pest = pests[0]
            pest_recs = IPMRecommendation.query.filter_by(pest_id=pest.id).all()
            logger.info(f"\n✓ IPM Recommendations for {pest.common_name}: {len(pest_recs)}")
            for rec in pest_recs:
                logger.info(f"  - {rec.treatment.name} (Priority: {rec.priority})")


def test_mongodb():
    """Test MongoDB functionality"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing MongoDB")
    logger.info("=" * 60)
    
    with app.app_context():
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            logger.warning("✗ MongoDB not available (this is OK for development)")
            logger.info("  Application will run with PostgreSQL only")
            return
        
        # Test collections
        collections = mongo_db.list_collection_names()
        logger.info(f"✓ MongoDB collections: {collections}")
        
        # Test detection_meta collection
        detection_meta = mongo_db['detection_meta']
        count = detection_meta.count_documents({})
        logger.info(f"✓ Detection metadata documents: {count}")
        
        # Test feedback collection
        feedback = mongo_db['feedback']
        count = feedback.count_documents({})
        logger.info(f"✓ Feedback documents: {count}")
        
        # Test analytics collection
        analytics = mongo_db['analytics']
        count = analytics.count_documents({})
        logger.info(f"✓ Analytics documents: {count}")


def test_id_synchronization():
    """Test ID synchronization between PostgreSQL and MongoDB"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing ID Synchronization")
    logger.info("=" * 60)
    
    with app.app_context():
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            logger.warning("✗ MongoDB not available - skipping sync test")
            return
        
        # Create a test scan
        user = User.query.first()
        if not user:
            logger.warning("✗ No users in database - skipping sync test")
            return
        
        scan = Scan(
            user_id=user.id,
            pest_identified='Test Pest',
            confidence=0.95,
            status='identified',
            model_version='test_v1.0'
        )
        db.session.add(scan)
        db.session.commit()
        
        scan_id = scan.id
        logger.info(f"✓ Created test scan with ID: {scan_id}")
        
        # Sync to MongoDB
        sync_detection_metadata(
            scan_id=scan_id,
            user_id=user.id,
            pest_label='Test Pest',
            confidence=0.95,
            alternatives=[
                {'label': 'Alternative 1', 'confidence': 0.03},
                {'label': 'Alternative 2', 'confidence': 0.02}
            ],
            model_details={
                'primary_model': 'EfficientNet-B0',
                'primary_version': 'test_v1.0',
                'inference_time_ms': 1500
            }
        )
        logger.info(f"✓ Queued metadata sync for scan_{scan_id}")
        
        # Wait a moment for background thread
        import time
        time.sleep(1)
        
        # Retrieve from MongoDB
        metadata = get_detection_metadata(scan_id)
        if metadata:
            logger.info(f"✓ Retrieved metadata from MongoDB:")
            logger.info(f"  - MongoDB ID: {metadata['_id']}")
            logger.info(f"  - Pest Label: {metadata['pest_label']}")
            logger.info(f"  - Confidence: {metadata['confidence']}")
            logger.info(f"  - Alternatives: {len(metadata.get('alternatives', []))}")
        else:
            logger.warning("✗ Could not retrieve metadata from MongoDB")
        
        # Clean up test scan
        db.session.delete(scan)
        db.session.commit()
        logger.info(f"✓ Cleaned up test scan")


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("HYBRID DATABASE FUNCTIONALITY TEST")
    logger.info("=" * 60)
    
    test_postgresql()
    test_mongodb()
    test_id_synchronization()
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
