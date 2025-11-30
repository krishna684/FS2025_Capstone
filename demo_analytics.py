"""
Demo script for analytics and outbreak detection functionality
Shows how to use the analytics API endpoints
"""
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models import User, Scan

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_analytics_endpoints():
    """
    Demonstrate the analytics and outbreak detection endpoints
    """
    logger.info("=" * 70)
    logger.info("AGBOT Analytics and Outbreak Detection Demo")
    logger.info("=" * 70)
    
    with app.test_client() as client:
        logger.info("\n1. Analytics Aggregation")
        logger.info("-" * 70)
        logger.info("Endpoint: POST /api/admin/analytics/aggregate")
        logger.info("Purpose: Aggregate detection data by region and pest type")
        logger.info("\nNote: This endpoint requires authentication in production")
        logger.info("It groups scans by region and pest, calculating monthly occurrences")
        
        logger.info("\n2. Pest Trend Queries")
        logger.info("-" * 70)
        logger.info("Endpoint: GET /api/analytics/trends")
        logger.info("Purpose: Query pest trends with optional filters")
        logger.info("\nExample queries:")
        logger.info("  - All trends: GET /api/analytics/trends")
        logger.info("  - By region: GET /api/analytics/trends?region=East_Africa")
        logger.info("  - By pest: GET /api/analytics/trends?pest=Fall%20Armyworm")
        logger.info("  - By period: GET /api/analytics/trends?period=3 (last 3 months)")
        logger.info("  - Combined: GET /api/analytics/trends?region=East_Africa&pest=Aphids")
        
        # Test the endpoint
        logger.info("\nTesting: GET /api/analytics/trends")
        response = client.get('/api/analytics/trends')
        logger.info(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            logger.info(f"Response: {data}")
        
        logger.info("\n3. Outbreak Detection")
        logger.info("-" * 70)
        logger.info("Endpoint: POST /api/admin/analytics/detect-outbreaks")
        logger.info("Purpose: Detect pest outbreaks by comparing current to historical data")
        logger.info("\nAlgorithm:")
        logger.info("  1. Calculate historical average (last 6 months)")
        logger.info("  2. Compare current month to historical average")
        logger.info("  3. If current > 1.5 × historical, generate outbreak alert")
        logger.info("  4. Store alert in MongoDB analytics collection")
        logger.info("  5. Emit WebSocket notification to affected region")
        
        logger.info("\n4. Active Outbreak Alerts")
        logger.info("-" * 70)
        logger.info("Endpoint: GET /api/analytics/outbreaks")
        logger.info("Purpose: Get active outbreak alerts for current month")
        logger.info("\nExample queries:")
        logger.info("  - All alerts: GET /api/analytics/outbreaks")
        logger.info("  - By region: GET /api/analytics/outbreaks?region=East_Africa")
        
        # Test the endpoint
        logger.info("\nTesting: GET /api/analytics/outbreaks")
        response = client.get('/api/analytics/outbreaks')
        logger.info(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            logger.info(f"Response: {data}")
        
        logger.info("\n5. WebSocket Notifications")
        logger.info("-" * 70)
        logger.info("Namespace: /alerts")
        logger.info("Purpose: Real-time outbreak alert notifications")
        logger.info("\nClient-side usage:")
        logger.info("  const socket = io('/alerts');")
        logger.info("  socket.on('connect', () => {")
        logger.info("    console.log('Connected to outbreak alerts');")
        logger.info("  });")
        logger.info("  socket.on('outbreak_alert', (alert) => {")
        logger.info("    console.log('Outbreak detected:', alert);")
        logger.info("    // Display alert to user")
        logger.info("  });")
        
        logger.info("\nFeatures:")
        logger.info("  - Automatic region-based room subscription")
        logger.info("  - Filters recipients by user.location")
        logger.info("  - Includes pest, region, severity, and threshold data")
        logger.info("  - Supports manual region subscription/unsubscription")
        
        logger.info("\n6. Data Flow")
        logger.info("-" * 70)
        logger.info("1. User submits scan → Stored in PostgreSQL")
        logger.info("2. Scan metadata → Synced to MongoDB")
        logger.info("3. Periodic aggregation → Groups by region/pest/month")
        logger.info("4. Outbreak detection → Compares current to historical")
        logger.info("5. Alert generation → Stored in MongoDB")
        logger.info("6. WebSocket emission → Notifies affected users")
        
        logger.info("\n7. MongoDB Collections")
        logger.info("-" * 70)
        logger.info("analytics collection structure:")
        logger.info("  {")
        logger.info("    '_id': 'analytics_East_Africa_2025-11',")
        logger.info("    'region': 'East_Africa',")
        logger.info("    'month': '2025-11',")
        logger.info("    'pest_occurrences': {")
        logger.info("      'Fall Armyworm': 25,")
        logger.info("      'Aphids': 12,")
        logger.info("      'Whitefly': 8")
        logger.info("    },")
        logger.info("    'total_scans': 45,")
        logger.info("    'outbreak_alerts': [")
        logger.info("      {")
        logger.info("        'pest': 'Fall Armyworm',")
        logger.info("        'region': 'East_Africa',")
        logger.info("        'current_count': 25,")
        logger.info("        'historical_average': 10.5,")
        logger.info("        'threshold_exceeded': 2.38,")
        logger.info("        'alert_issued': '2025-11-26T...'")
        logger.info("      }")
        logger.info("    ],")
        logger.info("    'last_updated': '2025-11-26T...'")
        logger.info("  }")
    
    logger.info("\n" + "=" * 70)
    logger.info("Demo complete!")
    logger.info("=" * 70)


def show_database_stats():
    """Show current database statistics"""
    logger.info("\nCurrent Database Statistics:")
    logger.info("-" * 70)
    
    with app.app_context():
        total_users = User.query.count()
        total_scans = Scan.query.count()
        
        logger.info(f"Total Users: {total_users}")
        logger.info(f"Total Scans: {total_scans}")
        
        if total_scans > 0:
            # Get scan distribution by region
            from sqlalchemy import func
            region_stats = db.session.query(
                User.location,
                func.count(Scan.id).label('scan_count')
            ).join(Scan, User.id == Scan.user_id).group_by(User.location).all()
            
            logger.info("\nScans by Region:")
            for region, count in region_stats:
                logger.info(f"  {region or 'Unknown'}: {count} scans")
            
            # Get scan distribution by pest
            pest_stats = db.session.query(
                Scan.pest_identified,
                func.count(Scan.id).label('scan_count')
            ).filter(Scan.pest_identified.isnot(None)).group_by(Scan.pest_identified).all()
            
            logger.info("\nScans by Pest:")
            for pest, count in pest_stats:
                logger.info(f"  {pest}: {count} scans")


if __name__ == '__main__':
    demo_analytics_endpoints()
    show_database_stats()
