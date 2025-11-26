"""
Ensemble logic for combining primary and fallback model predictions
Implements confidence-based fallback strategy
"""
import numpy as np
from typing import Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)

# Confidence threshold for invoking fallback model
FALLBACK_THRESHOLD = 0.85


def ensemble_predict(primary_result: Tuple[str, float, List[Dict]], 
                     fallback_result: Tuple[str, float, List[Dict]] = None,
                     threshold: float = FALLBACK_THRESHOLD) -> Tuple[str, float, List[Dict], bool]:
    """
    Combine predictions from primary and fallback models using ensemble logic
    
    Strategy:
    1. If primary confidence >= threshold, use primary prediction
    2. If primary confidence < threshold, invoke fallback
    3. Select prediction with highest confidence between primary and fallback
    
    Args:
        primary_result: Tuple of (pest_label, confidence, alternatives) from primary model
        fallback_result: Optional tuple from fallback model (None if not invoked)
        threshold: Confidence threshold for invoking fallback (default 0.85)
        
    Returns:
        Tuple of (pest_label, confidence, alternatives, fallback_used)
        - pest_label: Final predicted pest name
        - confidence: Final confidence score
        - alternatives: List of alternative predictions
        - fallback_used: Boolean indicating if fallback was used
        
    Requirements: 2.3, 2.4
    """
    primary_label, primary_conf, primary_alts = primary_result
    
    # Check if fallback should be invoked
    if primary_conf >= threshold:
        logger.info(f"Primary confidence {primary_conf:.2f} >= {threshold}, using primary prediction")
        return primary_label, primary_conf, primary_alts, False
    
    # If fallback not provided but needed, return primary with warning
    if fallback_result is None:
        logger.warning(f"Primary confidence {primary_conf:.2f} < {threshold} but no fallback provided")
        return primary_label, primary_conf, primary_alts, False
    
    # Compare primary and fallback predictions
    fallback_label, fallback_conf, fallback_alts = fallback_result
    
    logger.info(f"Comparing predictions - Primary: {primary_label} ({primary_conf:.2f}), "
                f"Fallback: {fallback_label} ({fallback_conf:.2f})")
    
    # Select prediction with highest confidence
    if fallback_conf > primary_conf:
        logger.info(f"Using fallback prediction (confidence {fallback_conf:.2f} > {primary_conf:.2f})")
        return fallback_label, fallback_conf, fallback_alts, True
    else:
        logger.info(f"Using primary prediction (confidence {primary_conf:.2f} >= {fallback_conf:.2f})")
        return primary_label, primary_conf, primary_alts, True


def should_invoke_fallback(confidence: float, threshold: float = FALLBACK_THRESHOLD) -> bool:
    """
    Determine if fallback model should be invoked based on confidence
    
    Args:
        confidence: Primary model confidence score
        threshold: Confidence threshold (default 0.85)
        
    Returns:
        True if fallback should be invoked, False otherwise
        
    Requirements: 2.3
    """
    return confidence < threshold
