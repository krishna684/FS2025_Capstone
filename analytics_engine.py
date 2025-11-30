"""
Analytics and outbreak detection engine for AGBOT system
Handles aggregation of detection data, trend analysis, and outbreak alerts
Requirements: 12.1, 12.2, 12.3, 12.4
"""
import logging
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from database import get_mongo_db
from models import Scan, User
from database import db

logger = logging.getLogger(__name__)


def aggregate_detection_data():
    """
    Background task to aggregate detection data by region and pest type
    Groups by region and pest type, calculates occurrence counts per month
    Stores results in MongoDB analytics collection
    
    Requirements: 12.1
    
    Returns:
        Dictionary with aggregation results
    """
    logger.info("Starting detection data aggregation task")
    
    try:
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            logger.warning("MongoDB not available, skipping aggregation")
            return {'error': 'MongoDB not available'}
        
        # Get current month for aggregation
        now = datetime.utcnow()
        current_month = now.strftime('%Y-%m')
        
        # Query all scans from PostgreSQL with user location data
        # Join with users table to get location information
        scans_query = db.session.query(
            Scan.pest_identified,
            User.location,
            Scan.created_at
        ).join(User, Scan.user_id == User.id).filter(
            Scan.pest_identified.isnot(None),
            User.location.isnot(None)
        ).all()
        
        # Aggregate by region and pest type for current month
        monthly_aggregation = defaultdict(lambda: defaultdict(int))
        
        for pest, region, created_at in scans_query:
            if created_at:
                scan_month = created_at.strftime('%Y-%m')
                # Aggregate for current month
                if scan_month == current_month:
                    monthly_aggregation[region][pest] += 1
        
        # Store aggregated data in MongoDB analytics collection
        analytics_collection = mongo_db['analytics']
        
        total_regions_updated = 0
        for region, pest_counts in monthly_aggregation.items():
            # Create analytics document
            analytics_doc = {
                '_id': f"analytics_{region}_{current_month}",
                'region': region,
                'month': current_month,
                'pest_occurrences': dict(pest_counts),
                'total_scans': sum(pest_counts.values()),
                'last_updated': datetime.utcnow()
            }
            
            # Upsert to MongoDB
            analytics_collection.replace_one(
                {'_id': analytics_doc['_id']},
                analytics_doc,
                upsert=True
            )
            
            total_regions_updated += 1
            logger.info(f"Updated analytics for region={region}, month={current_month}, total_scans={analytics_doc['total_scans']}")
        
        logger.info(f"Detection data aggregation complete: {total_regions_updated} regions updated")
        
        return {
            'success': True,
            'regions_updated': total_regions_updated,
            'month': current_month,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in detection data aggregation: {e}", exc_info=True)
        return {
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


def run_aggregation_task_async():
    """
    Run aggregation task asynchronously in background thread
    """
    thread = threading.Thread(target=aggregate_detection_data)
    thread.daemon = True
    thread.start()
    logger.info("Queued detection data aggregation task")


def get_pest_trends(region=None, pest=None, period=None):
    """
    Query pest trends from MongoDB analytics collection
    Groups by pest_type, region, and time_period
    
    Requirements: 12.2
    
    Args:
        region: Optional region filter
        pest: Optional pest type filter
        period: Optional time period (format: YYYY-MM or number of months)
    
    Returns:
        List of aggregated trend data
    """
    try:
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            logger.warning("MongoDB not available")
            return []
        
        analytics_collection = mongo_db['analytics']
        
        # Build query filter
        query_filter = {}
        
        if region:
            query_filter['region'] = region
        
        # Handle period filter
        if period:
            # If period is a month string (YYYY-MM), filter for that month
            if isinstance(period, str) and len(period) == 7:
                query_filter['month'] = period
            # If period is a number, get last N months
            elif isinstance(period, int) or (isinstance(period, str) and period.isdigit()):
                months_back = int(period)
                now = datetime.utcnow()
                start_date = now - timedelta(days=months_back * 30)
                start_month = start_date.strftime('%Y-%m')
                query_filter['month'] = {'$gte': start_month}
        
        # Query MongoDB
        cursor = analytics_collection.find(query_filter).sort('month', -1)
        
        # Process results
        trends = []
        for doc in cursor:
            # If pest filter specified, filter pest_occurrences
            if pest:
                pest_count = doc.get('pest_occurrences', {}).get(pest, 0)
                trend_entry = {
                    'region': doc['region'],
                    'month': doc['month'],
                    'pest_type': pest,
                    'count': pest_count,
                    'last_updated': doc['last_updated'].isoformat() if isinstance(doc.get('last_updated'), datetime) else doc.get('last_updated')
                }
                if pest_count > 0:  # Only include if pest was detected
                    trends.append(trend_entry)
            else:
                # Return all pests for this region/month
                for pest_type, count in doc.get('pest_occurrences', {}).items():
                    trend_entry = {
                        'region': doc['region'],
                        'month': doc['month'],
                        'pest_type': pest_type,
                        'count': count,
                        'last_updated': doc['last_updated'].isoformat() if isinstance(doc.get('last_updated'), datetime) else doc.get('last_updated')
                    }
                    trends.append(trend_entry)
        
        logger.info(f"Retrieved {len(trends)} trend records (region={region}, pest={pest}, period={period})")
        return trends
        
    except Exception as e:
        logger.error(f"Error retrieving pest trends: {e}", exc_info=True)
        return []


def calculate_historical_average(region, pest_type, months_back=6):
    """
    Calculate historical average occurrences for a pest in a region
    
    Args:
        region: Region name
        pest_type: Pest type name
        months_back: Number of months to look back for average (default 6)
    
    Returns:
        Float representing average occurrences per month
    """
    try:
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            return 0.0
        
        analytics_collection = mongo_db['analytics']
        
        # Calculate date range
        now = datetime.utcnow()
        start_date = now - timedelta(days=months_back * 30)
        start_month = start_date.strftime('%Y-%m')
        current_month = now.strftime('%Y-%m')
        
        # Query historical data (excluding current month)
        query_filter = {
            'region': region,
            'month': {'$gte': start_month, '$lt': current_month}
        }
        
        cursor = analytics_collection.find(query_filter)
        
        # Calculate average
        total_occurrences = 0
        month_count = 0
        
        for doc in cursor:
            pest_count = doc.get('pest_occurrences', {}).get(pest_type, 0)
            total_occurrences += pest_count
            month_count += 1
        
        if month_count == 0:
            return 0.0
        
        average = total_occurrences / month_count
        logger.debug(f"Historical average for {pest_type} in {region}: {average:.2f} (over {month_count} months)")
        
        return average
        
    except Exception as e:
        logger.error(f"Error calculating historical average: {e}")
        return 0.0


def detect_outbreaks():
    """
    Detect pest outbreaks by comparing current occurrences to historical averages
    If current > 1.5 × historical, generate outbreak alert
    Store alerts in MongoDB analytics collection
    Emit WebSocket notifications to affected regions
    
    Requirements: 12.3, 12.4
    
    Returns:
        List of outbreak alerts generated
    """
    logger.info("Starting outbreak detection")
    
    try:
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            logger.warning("MongoDB not available")
            return []
        
        analytics_collection = mongo_db['analytics']
        
        # Get current month data
        now = datetime.utcnow()
        current_month = now.strftime('%Y-%m')
        
        query_filter = {'month': current_month}
        cursor = analytics_collection.find(query_filter)
        
        outbreak_alerts = []
        
        for doc in cursor:
            region = doc['region']
            pest_occurrences = doc.get('pest_occurrences', {})
            
            for pest_type, current_count in pest_occurrences.items():
                # Calculate historical average
                historical_avg = calculate_historical_average(region, pest_type, months_back=6)
                
                # Check if outbreak threshold exceeded (1.5x historical average)
                threshold = 1.5 * historical_avg
                
                if historical_avg > 0 and current_count > threshold:
                    # Generate outbreak alert
                    threshold_exceeded = current_count / historical_avg if historical_avg > 0 else 0
                    
                    alert = {
                        'pest': pest_type,
                        'region': region,
                        'current_count': current_count,
                        'historical_average': round(historical_avg, 2),
                        'threshold_exceeded': round(threshold_exceeded, 2),
                        'alert_issued': datetime.utcnow()
                    }
                    
                    outbreak_alerts.append(alert)
                    
                    logger.warning(f"OUTBREAK DETECTED: {pest_type} in {region} - Current: {current_count}, Historical Avg: {historical_avg:.2f}, Threshold Exceeded: {threshold_exceeded:.2f}x")
                    
                    # Update analytics document with outbreak alert
                    analytics_collection.update_one(
                        {'_id': doc['_id']},
                        {
                            '$push': {
                                'outbreak_alerts': alert
                            }
                        }
                    )
        
        # Emit WebSocket notifications for all outbreak alerts
        if outbreak_alerts:
            try:
                from websocket_alerts import emit_outbreak_alerts_batch
                emit_outbreak_alerts_batch(outbreak_alerts)
            except Exception as ws_error:
                logger.error(f"Failed to emit WebSocket alerts: {ws_error}")
        
        logger.info(f"Outbreak detection complete: {len(outbreak_alerts)} alerts generated")
        
        return outbreak_alerts
        
    except Exception as e:
        logger.error(f"Error in outbreak detection: {e}", exc_info=True)
        return []


def get_active_outbreak_alerts(region=None):
    """
    Get active outbreak alerts from MongoDB
    
    Args:
        region: Optional region filter
    
    Returns:
        List of active outbreak alerts
    """
    try:
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            return []
        
        analytics_collection = mongo_db['analytics']
        
        # Get current month
        now = datetime.utcnow()
        current_month = now.strftime('%Y-%m')
        
        # Build query
        query_filter = {
            'month': current_month,
            'outbreak_alerts': {'$exists': True, '$ne': []}
        }
        
        if region:
            query_filter['region'] = region
        
        cursor = analytics_collection.find(query_filter)
        
        # Collect all alerts
        all_alerts = []
        for doc in cursor:
            alerts = doc.get('outbreak_alerts', [])
            for alert in alerts:
                # Add region to alert if not present
                if 'region' not in alert:
                    alert['region'] = doc['region']
                # Convert datetime to string for JSON serialization
                if isinstance(alert.get('alert_issued'), datetime):
                    alert['alert_issued'] = alert['alert_issued'].isoformat()
                all_alerts.append(alert)
        
        logger.info(f"Retrieved {len(all_alerts)} active outbreak alerts (region={region})")
        return all_alerts
        
    except Exception as e:
        logger.error(f"Error retrieving outbreak alerts: {e}")
        return []


def run_outbreak_detection_async():
    """
    Run outbreak detection asynchronously in background thread
    """
    thread = threading.Thread(target=detect_outbreaks)
    thread.daemon = True
    thread.start()
    logger.info("Queued outbreak detection task")
