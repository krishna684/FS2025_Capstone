"""
AI Client Module
Handles communication with the AI microservice for pest detection
"""
import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# AI Service configuration
AI_SERVICE_URL = "http://localhost:8000"
AI_DETECT_ENDPOINT = f"{AI_SERVICE_URL}/ai/detect"
AI_SERVICE_TIMEOUT = 3.0  # 3 seconds timeout (ultimate enforcer)


def call_ai_service(image_path: str) -> Dict:
    """
    Call AI microservice to detect pest from image
    
    This function sends an image to the AI microservice and returns the detection results.
    It enforces a strict 3-second timeout as the ultimate enforcer of the timeout requirement.
    
    Args:
        image_path: Path to the image file to analyze
        
    Returns:
        Dictionary with detection results:
        {
            'success': bool,
            'pest_label': str,
            'scientific_name': str,
            'confidence': float,
            'alternatives': list,
            'processing_time_ms': float,
            'timing_breakdown': dict,
            'fallback_used': bool,
            'error': str (only if success=False)
        }
        
    Requirements: 2.2, 2.5
    """
    try:
        # Open and read the image file
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            
            logger.info(f"Calling AI service for image: {image_path}")
            
            # Make POST request to AI service with timeout
            response = requests.post(
                AI_DETECT_ENDPOINT,
                files=files,
                timeout=AI_SERVICE_TIMEOUT
            )
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                logger.info(f"AI service returned: {result.get('pest_label')} "
                           f"({result.get('confidence'):.2f}) in "
                           f"{result.get('processing_time_ms'):.2f}ms")
                
                # Add success flag
                result['success'] = True
                return result
            
            elif response.status_code == 408:
                # Timeout from AI service
                logger.warning(f"AI service timeout (408) for image: {image_path}")
                return {
                    'success': False,
                    'error': 'Analysis taking longer than expected. Please try again.',
                    'error_type': 'timeout'
                }
            
            else:
                # Other error from AI service
                error_detail = response.json().get('detail', 'Unknown error') if response.text else 'Unknown error'
                logger.error(f"AI service error ({response.status_code}): {error_detail}")
                return {
                    'success': False,
                    'error': f'AI service error: {error_detail}',
                    'error_type': 'service_error',
                    'status_code': response.status_code
                }
    
    except requests.exceptions.Timeout:
        # Request timeout (3 seconds exceeded)
        logger.error(f"Request timeout after {AI_SERVICE_TIMEOUT}s for image: {image_path}")
        return {
            'success': False,
            'error': 'Analysis taking longer than expected. Please try again.',
            'error_type': 'timeout'
        }
    
    except requests.exceptions.ConnectionError as e:
        # AI service not reachable
        logger.error(f"Connection error to AI service: {e}")
        return {
            'success': False,
            'error': 'AI service temporarily unavailable. Please try again in a few moments.',
            'error_type': 'connection_error'
        }
    
    except FileNotFoundError:
        # Image file not found
        logger.error(f"Image file not found: {image_path}")
        return {
            'success': False,
            'error': 'Image file not found',
            'error_type': 'file_not_found'
        }
    
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error calling AI service: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'error_type': 'unexpected_error'
        }


def check_ai_service_health() -> bool:
    """
    Check if AI service is healthy and reachable
    
    Returns:
        True if service is healthy, False otherwise
    """
    try:
        health_url = f"{AI_SERVICE_URL}/health"
        response = requests.get(health_url, timeout=2.0)
        
        if response.status_code == 200:
            logger.info("AI service health check passed")
            return True
        else:
            logger.warning(f"AI service health check failed with status {response.status_code}")
            return False
    
    except Exception as e:
        logger.error(f"AI service health check failed: {e}")
        return False
