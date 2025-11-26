"""
Background task for feedback aggregation and retraining threshold monitoring

This script can be run:
1. As a standalone script via cron job (e.g., daily at midnight)
2. As a background task in a task queue (e.g., Celery)
3. Manually for testing/debugging

Usage:
    python feedback_aggregation_task.py

Requirements: 9.1, 9.2
"""
import sys
import os
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from db_sync import run_feedback_aggregation_task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('feedback_aggregation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """
    Main function to run feedback aggregation task
    """
    logger.info("=" * 80)
    logger.info("Starting feedback aggregation task")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)
    
    try:
        # Run within Flask app context to access database connections
        with app.app_context():
            result = run_feedback_aggregation_task()
            
            # Log results
            if 'error' in result:
                logger.error(f"Task failed: {result['error']}")
                return 1
            
            logger.info(f"Task completed successfully")
            logger.info(f"Total corrections: {result.get('total_corrections', 0)}")
            logger.info(f"Pest types with corrections: {len(result.get('pest_counts', {}))}")
            
            # Log pests needing retraining
            pests_needing_retraining = result.get('pests_needing_retraining', {})
            if pests_needing_retraining:
                logger.warning("=" * 80)
                logger.warning("PESTS REQUIRING MODEL RETRAINING:")
                for pest, count in pests_needing_retraining.items():
                    logger.warning(f"  - {pest}: {count} corrections")
                logger.warning("=" * 80)
            
            return 0
            
    except Exception as e:
        logger.error(f"Unexpected error in feedback aggregation task: {e}", exc_info=True)
        return 1
    
    finally:
        logger.info("=" * 80)
        logger.info("Feedback aggregation task finished")
        logger.info("=" * 80)


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
