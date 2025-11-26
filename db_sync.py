"""
Database synchronization utilities for hybrid PostgreSQL + MongoDB architecture
Handles ID synchronization and asynchronous writes to MongoDB
"""
import threading
import logging
from datetime import datetime
from database import get_mongo_db

logger = logging.getLogger(__name__)


def sync_detection_metadata(scan_id, user_id, pest_label, confidence, alternatives=None,
                            image_info=None, model_details=None, location=None):
    """
    Synchronize detection metadata to MongoDB asynchronously
    
    Args:
        scan_id: PostgreSQL scan ID (source of truth)
        user_id: User ID
        pest_label: Identified pest label
        confidence: Confidence score (0-1)
        alternatives: List of alternative predictions
        image_info: Dictionary with image metadata
        model_details: Dictionary with model inference details
        location: GeoJSON location data
    
    Returns:
        None (writes asynchronously)
    """
    # Create background thread for MongoDB write
    thread = threading.Thread(
        target=_write_detection_to_mongodb,
        args=(scan_id, user_id, pest_label, confidence, alternatives,
              image_info, model_details, location)
    )
    thread.daemon = True
    thread.start()
    
    logger.info(f"Queued detection metadata sync for scan_id={scan_id}")


def _write_detection_to_mongodb(scan_id, user_id, pest_label, confidence, alternatives,
                                 image_info, model_details, location):
    """
    Internal function to write detection metadata to MongoDB
    Runs in background thread
    
    Args:
        scan_id: PostgreSQL scan ID
        user_id: User ID
        pest_label: Identified pest label
        confidence: Confidence score (0-1)
        alternatives: List of alternative predictions
        image_info: Dictionary with image metadata
        model_details: Dictionary with model inference details
        location: GeoJSON location data
    """
    try:
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            logger.warning(f"MongoDB not available, skipping metadata sync for scan_id={scan_id}")
            return
        
        # Create MongoDB document ID using PostgreSQL ID
        mongo_id = f"scan_{scan_id}"
        
        # Build detection metadata document
        detection_doc = {
            '_id': mongo_id,
            'user_id': user_id,
            'pest_label': pest_label,
            'confidence': float(confidence) if confidence else 0.0,
            'alternatives': alternatives or [],
            'image_info': image_info or {},
            'model_details': model_details or {},
            'location': location or {},
            'timestamp': datetime.utcnow()
        }
        
        # Insert or update in MongoDB
        collection = mongo_db['detection_meta']
        collection.replace_one(
            {'_id': mongo_id},
            detection_doc,
            upsert=True
        )
        
        logger.info(f"Successfully synced detection metadata to MongoDB: {mongo_id}")
        
    except Exception as e:
        logger.error(f"Failed to sync detection metadata to MongoDB for scan_id={scan_id}: {e}")


def sync_feedback_to_mongodb(feedback_id, detection_id, user_id, is_correct,
                             corrected_label=None, confidence_in_correction=None,
                             comments=None, image_flagged_for_retraining=False):
    """
    Synchronize feedback to MongoDB asynchronously
    
    Args:
        feedback_id: PostgreSQL feedback ID
        detection_id: PostgreSQL scan ID (references detection_meta)
        user_id: User ID
        is_correct: Boolean indicating if detection was correct
        corrected_label: Corrected pest label if is_correct is False
        confidence_in_correction: User's confidence in their correction
        comments: User comments
        image_flagged_for_retraining: Whether to flag for retraining
    
    Returns:
        None (writes asynchronously)
    """
    # Create background thread for MongoDB write
    thread = threading.Thread(
        target=_write_feedback_to_mongodb,
        args=(feedback_id, detection_id, user_id, is_correct, corrected_label,
              confidence_in_correction, comments, image_flagged_for_retraining)
    )
    thread.daemon = True
    thread.start()
    
    logger.info(f"Queued feedback sync for feedback_id={feedback_id}")


def _write_feedback_to_mongodb(feedback_id, detection_id, user_id, is_correct,
                               corrected_label, confidence_in_correction,
                               comments, image_flagged_for_retraining):
    """
    Internal function to write feedback to MongoDB
    Runs in background thread
    
    Args:
        feedback_id: PostgreSQL feedback ID
        detection_id: PostgreSQL scan ID
        user_id: User ID
        is_correct: Boolean indicating if detection was correct
        corrected_label: Corrected pest label if is_correct is False
        confidence_in_correction: User's confidence in their correction
        comments: User comments
        image_flagged_for_retraining: Whether to flag for retraining
    """
    try:
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            logger.warning(f"MongoDB not available, skipping feedback sync for feedback_id={feedback_id}")
            return
        
        # Create MongoDB document ID using PostgreSQL ID
        mongo_id = f"feedback_{feedback_id}"
        detection_mongo_id = f"scan_{detection_id}"
        
        # Build feedback document
        feedback_doc = {
            '_id': mongo_id,
            'detection_id': detection_mongo_id,
            'user_id': user_id,
            'is_correct': is_correct,
            'corrected_label': corrected_label,
            'confidence_in_correction': confidence_in_correction or 'medium',
            'comments': comments or '',
            'image_flagged_for_retraining': image_flagged_for_retraining,
            'feedback_time': datetime.utcnow()
        }
        
        # Insert or update in MongoDB
        collection = mongo_db['feedback']
        collection.replace_one(
            {'_id': mongo_id},
            feedback_doc,
            upsert=True
        )
        
        logger.info(f"Successfully synced feedback to MongoDB: {mongo_id}")
        
        # If feedback indicates incorrect detection, flag for retraining
        if not is_correct and image_flagged_for_retraining:
            _flag_detection_for_retraining(detection_mongo_id)
        
    except Exception as e:
        logger.error(f"Failed to sync feedback to MongoDB for feedback_id={feedback_id}: {e}")


def _flag_detection_for_retraining(detection_mongo_id):
    """
    Flag a detection for model retraining in MongoDB
    
    Args:
        detection_mongo_id: MongoDB detection ID (format: scan_{id})
    """
    try:
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            return
        
        collection = mongo_db['detection_meta']
        collection.update_one(
            {'_id': detection_mongo_id},
            {'$set': {'flagged_for_retraining': True}}
        )
        
        logger.info(f"Flagged detection for retraining: {detection_mongo_id}")
        
    except Exception as e:
        logger.error(f"Failed to flag detection for retraining: {e}")


def get_detection_metadata(scan_id):
    """
    Retrieve detection metadata from MongoDB
    
    Args:
        scan_id: PostgreSQL scan ID
    
    Returns:
        Dictionary with detection metadata or None if not found
    """
    try:
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            logger.warning("MongoDB not available")
            return None
        
        mongo_id = f"scan_{scan_id}"
        collection = mongo_db['detection_meta']
        
        doc = collection.find_one({'_id': mongo_id})
        
        if doc:
            # Convert ObjectId and datetime to strings for JSON serialization
            doc['_id'] = str(doc['_id'])
            if 'timestamp' in doc:
                doc['timestamp'] = doc['timestamp'].isoformat()
            return doc
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to retrieve detection metadata for scan_id={scan_id}: {e}")
        return None


def get_feedback_for_detection(scan_id):
    """
    Retrieve all feedback for a detection from MongoDB
    
    Args:
        scan_id: PostgreSQL scan ID
    
    Returns:
        List of feedback documents or empty list
    """
    try:
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            logger.warning("MongoDB not available")
            return []
        
        detection_mongo_id = f"scan_{scan_id}"
        collection = mongo_db['feedback']
        
        cursor = collection.find({'detection_id': detection_mongo_id})
        
        feedback_list = []
        for doc in cursor:
            # Convert ObjectId and datetime to strings
            doc['_id'] = str(doc['_id'])
            if 'feedback_time' in doc:
                doc['feedback_time'] = doc['feedback_time'].isoformat()
            feedback_list.append(doc)
        
        return feedback_list
        
    except Exception as e:
        logger.error(f"Failed to retrieve feedback for scan_id={scan_id}: {e}")
        return []


def aggregate_feedback_for_retraining():
    """
    Aggregate feedback data to identify pests needing model retraining
    
    Returns:
        Dictionary with pest types and their correction counts
    """
    try:
        mongo_db = get_mongo_db()
        
        if not mongo_db:
            logger.warning("MongoDB not available")
            return {}
        
        collection = mongo_db['feedback']
        
        # Aggregate corrections by pest type
        pipeline = [
            {'$match': {'is_correct': False, 'image_flagged_for_retraining': True}},
            {'$group': {
                '_id': '$corrected_label',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        
        results = collection.aggregate(pipeline)
        
        aggregation = {}
        for result in results:
            pest_label = result['_id']
            count = result['count']
            aggregation[pest_label] = count
            
            # Log if threshold reached (100 corrections)
            if count >= 100:
                logger.warning(f"RETRAINING THRESHOLD REACHED: {pest_label} has {count} corrections - Model retraining recommended")
        
        return aggregation
        
    except Exception as e:
        logger.error(f"Failed to aggregate feedback for retraining: {e}")
        return {}


def run_feedback_aggregation_task():
    """
    Background task to aggregate feedback and check retraining thresholds
    This should be called periodically (e.g., daily via cron job or scheduler)
    
    Returns:
        Dictionary with aggregation results
    """
    logger.info("Starting feedback aggregation task for model retraining")
    
    try:
        # Run aggregation
        aggregation = aggregate_feedback_for_retraining()
        
        # Log summary
        total_corrections = sum(aggregation.values())
        logger.info(f"Feedback aggregation complete: {total_corrections} total corrections across {len(aggregation)} pest types")
        
        # Check for pests that need retraining
        pests_needing_retraining = {pest: count for pest, count in aggregation.items() if count >= 100}
        
        if pests_needing_retraining:
            logger.warning(f"Pests requiring model retraining: {pests_needing_retraining}")
        else:
            logger.info("No pests have reached the retraining threshold (100 corrections)")
        
        return {
            'total_corrections': total_corrections,
            'pest_counts': aggregation,
            'pests_needing_retraining': pests_needing_retraining,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in feedback aggregation task: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
