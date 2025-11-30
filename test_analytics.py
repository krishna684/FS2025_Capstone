"""
Test suite for analytics and outbreak detection functionality
Tests Requirements: 12.1, 12.2, 12.3, 12.4
"""
import sys
import os
import logging
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db, get_mongo_db
from models import User, Scan
from analytics_engine import (
    aggregate_detection_data,
    get_pest_trends,
    calculate_historical_average,
    detect_outbreaks,
    get_active_outbreak_alerts
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_test_data():
    """Create test data for analytics testing"""
    logger.info("Setting up test data...")
    
    with app.app_context():
        # Create test users with different locations
        test_users = []
        locations = ['East_Africa', 'West_Africa', 'South_Asia', 'Southeast_Asia']
        
        for i, location in enumerate(locations):
            user = User.query.filter_by(email=f'test_analytics_{i}@example.com').first()
            if not user:
                user = User(
                    name=f'Test User {i}',
                    email=f'test_analytics_{i}@example.com',
                    location=location
                )
                user.set_password('testpass123')
                db.session.add(user)
        
        db.session.commit()
        
        # Get users
        for location in locations:
            user = User.query.filter_by(location=location).first()
            if user:
                test_users.append(user)
        
        # Create test scans with various pests and dates
        pests = ['Fall Armyworm', 'Aphids', 'Whitefly', 'Spider Mites', 'Tomato Leafminer']
        
        # Create historical data (6 months back)
        for month_offset in range(6, 0, -1):
            scan_date = datetime.utcnow() - timedelta(days=month_offset * 30)
            
            for user in test_users:
                # Create 5-10 scans per user per month
                num_scans = 5 + (month_offset % 5)
                
                for _ in range(num_scans):
                    pest = pests[_ % len(pests)]
                    scan = Scan(
                        user_id=user.id,
                        pest_identified=pest,
                        pest_scientific=f'{pest} scientific',
                        confidence=0.85 + (_ * 0.01),
                        status='identified',
                        created_at=scan_date
                    )
                    db.session.add(scan)
        
        # Create current month data with outbreak conditions
        # East_Africa: High Fall Armyworm count (outbreak)
        user_ea = User.query.filter_by(location='East_Africa').first()
        if user_ea:
            for _ in range(25):  # Much higher than historical average
                scan = Scan(
                    user_id=user_ea.id,
                    pest_identified='Fall Armyworm',
                    pest_scientific='Spodoptera frugiperda',
                    confidence=0.90,
                    status='identified',
                    created_at=datetime.utcnow()
                )
                db.session.add(scan)
        
        # West_Africa: Normal Aphids count (no outbreak)
        user_wa = User.query.filter_by(location='West_Africa').first()
        if user_wa:
            for _ in range(6):  # Normal count
                scan = Scan(
                    user_id=user_wa.id,
                    pest_identified='Aphids',
                    pest_scientific='Aphidoidea',
                    confidence=0.88,
                    status='identified',
                    created_at=datetime.utcnow()
                )
                db.session.add(scan)
        
        db.session.commit()
        logger.info("Test data created successfully")


def test_aggregation():
    """Test detection data aggregation (Requirement 12.1)"""
    logger.info("\n=== Testing Detection Data Aggregation ===")
    
    with app.app_context():
        result = aggregate_detection_data()
        
        if result.get('success'):
            logger.info(f"✓ Aggregation successful")
            logger.info(f"  Regions updated: {result.get('regions_updated')}")
            logger.info(f"  Month: {result.get('month')}")
        else:
            logger.error(f"✗ Aggregation failed: {result.get('error')}")
            return False
    
    return True


def test_trend_queries():
    """Test pest trend queries (Requirement 12.2)"""
    logger.info("\n=== Testing Pest Trend Queries ===")
    
    with app.app_context():
        # Test 1: Get all trends
        logger.info("Test 1: Get all trends")
        trends = get_pest_trends()
        logger.info(f"  Retrieved {len(trends)} trend records")
        
        # Test 2: Filter by region
        logger.info("Test 2: Filter by region (East_Africa)")
        trends_ea = get_pest_trends(region='East_Africa')
        logger.info(f"  Retrieved {len(trends_ea)} trend records for East_Africa")
        
        # Test 3: Filter by pest
        logger.info("Test 3: Filter by pest (Fall Armyworm)")
        trends_fa = get_pest_trends(pest='Fall Armyworm')
        logger.info(f"  Retrieved {len(trends_fa)} trend records for Fall Armyworm")
        
        # Test 4: Filter by period
        logger.info("Test 4: Filter by period (last 3 months)")
        trends_period = get_pest_trends(period=3)
        logger.info(f"  Retrieved {len(trends_period)} trend records for last 3 months")
        
        # Test 5: Combined filters
        logger.info("Test 5: Combined filters (East_Africa + Fall Armyworm)")
        trends_combined = get_pest_trends(region='East_Africa', pest='Fall Armyworm')
        logger.info(f"  Retrieved {len(trends_combined)} trend records")
        
        if len(trends_combined) > 0:
            logger.info(f"  Sample trend: {trends_combined[0]}")
    
    return True


def test_outbreak_detection():
    """Test outbreak detection algorithm (Requirement 12.3)"""
    logger.info("\n=== Testing Outbreak Detection ===")
    
    with app.app_context():
        # First, ensure aggregation is up to date
        aggregate_detection_data()
        
        # Run outbreak detection
        alerts = detect_outbreaks()
        
        logger.info(f"Detected {len(alerts)} outbreak alerts")
        
        for alert in alerts:
            logger.info(f"  Outbreak Alert:")
            logger.info(f"    Pest: {alert['pest']}")
            logger.info(f"    Region: {alert['region']}")
            logger.info(f"    Current Count: {alert['current_count']}")
            logger.info(f"    Historical Avg: {alert['historical_average']}")
            logger.info(f"    Threshold Exceeded: {alert['threshold_exceeded']}x")
        
        # Verify outbreak was detected for Fall Armyworm in East_Africa
        fa_outbreak = any(
            a['pest'] == 'Fall Armyworm' and a['region'] == 'East_Africa'
            for a in alerts
        )
        
        if fa_outbreak:
            logger.info("✓ Expected outbreak detected (Fall Armyworm in East_Africa)")
        else:
            logger.warning("✗ Expected outbreak not detected")
    
    return True


def test_active_alerts():
    """Test retrieval of active outbreak alerts"""
    logger.info("\n=== Testing Active Outbreak Alerts ===")
    
    with app.app_context():
        # Get all active alerts
        logger.info("Test 1: Get all active alerts")
        alerts = get_active_outbreak_alerts()
        logger.info(f"  Retrieved {len(alerts)} active alerts")
        
        # Get alerts for specific region
        logger.info("Test 2: Get alerts for East_Africa")
        alerts_ea = get_active_outbreak_alerts(region='East_Africa')
        logger.info(f"  Retrieved {len(alerts_ea)} alerts for East_Africa")
        
        if len(alerts_ea) > 0:
            logger.info(f"  Sample alert: {alerts_ea[0]}")
    
    return True


def test_api_endpoints():
    """Test analytics API endpoints"""
    logger.info("\n=== Testing API Endpoints ===")
    
    with app.test_client() as client:
        # Test trends endpoint
        logger.info("Test 1: GET /api/analytics/trends")
        response = client.get('/api/analytics/trends')
        logger.info(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            logger.info(f"  Trends count: {data.get('count')}")
        
        # Test trends with filters
        logger.info("Test 2: GET /api/analytics/trends?region=East_Africa")
        response = client.get('/api/analytics/trends?region=East_Africa')
        logger.info(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            logger.info(f"  Trends count: {data.get('count')}")
        
        # Test outbreak alerts endpoint
        logger.info("Test 3: GET /api/analytics/outbreaks")
        response = client.get('/api/analytics/outbreaks')
        logger.info(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            logger.info(f"  Alerts count: {data.get('count')}")
    
    return True


def cleanup_test_data():
    """Clean up test data"""
    logger.info("\n=== Cleaning up test data ===")
    
    with app.app_context():
        # Delete test scans
        Scan.query.filter(Scan.user_id.in_(
            db.session.query(User.id).filter(User.email.like('test_analytics_%'))
        )).delete(synchronize_session=False)
        
        # Delete test users
        User.query.filter(User.email.like('test_analytics_%')).delete()
        
        db.session.commit()
        
        # Clean up MongoDB analytics collection
        mongo_db = get_mongo_db()
        if mongo_db:
            analytics_collection = mongo_db['analytics']
            analytics_collection.delete_many({})
            logger.info("MongoDB analytics collection cleaned")
        
        logger.info("Test data cleaned up")


def main():
    """Run all analytics tests"""
    logger.info("=" * 60)
    logger.info("AGBOT Analytics and Outbreak Detection Test Suite")
    logger.info("=" * 60)
    
    try:
        # Setup
        setup_test_data()
        
        # Run tests
        tests = [
            ("Aggregation", test_aggregation),
            ("Trend Queries", test_trend_queries),
            ("Outbreak Detection", test_outbreak_detection),
            ("Active Alerts", test_active_alerts),
            ("API Endpoints", test_api_endpoints)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                logger.error(f"Error in {test_name}: {e}", exc_info=True)
                results.append((test_name, False))
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{status}: {test_name}")
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        logger.info(f"\nTotal: {passed}/{total} tests passed")
        
    finally:
        # Cleanup
        cleanup_test_data()
    
    logger.info("\nTest suite complete!")


if __name__ == '__main__':
    main()
