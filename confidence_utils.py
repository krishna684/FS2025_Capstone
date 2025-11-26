"""
Confidence Utilities
Helper functions for confidence level classification and feedback prompting
"""


def classify_confidence(score: float) -> str:
    """
    Classify confidence score into human-readable levels
    
    This function maps numerical confidence scores to descriptive levels
    that help farmers understand the reliability of the pest identification.
    
    Args:
        score: Confidence score as a float (0.0 to 1.0)
        
    Returns:
        String describing confidence level:
        - "High Confidence" for score >= 0.85
        - "Moderate Confidence" for 0.70 <= score < 0.85
        - "Low Confidence" for 0.50 <= score < 0.70
        - "Unable to identify" for score < 0.50
        
    Requirements: 3.2, 3.3, 3.4, 3.5
    """
    if score >= 0.85:
        return "High Confidence"
    elif score >= 0.70:
        return "Moderate Confidence"
    elif score >= 0.50:
        return "Low Confidence"
    else:
        return "Unable to identify"


def should_request_feedback(confidence: float) -> bool:
    """
    Determine if proactive feedback should be requested
    
    According to requirement 5.5, feedback should be proactively requested
    when confidence is below 75%.
    
    Args:
        confidence: Confidence score as a float (0.0 to 1.0)
        
    Returns:
        True if feedback should be requested, False otherwise
        
    Requirements: 5.5
    """
    return confidence < 0.75


def get_confidence_message(confidence_level: str) -> str:
    """
    Get user-friendly message for confidence level
    
    Args:
        confidence_level: Confidence level string from classify_confidence()
        
    Returns:
        User-friendly message explaining the confidence level
    """
    messages = {
        "High Confidence": "The AI is highly confident in this identification.",
        "Moderate Confidence": "The AI has moderate confidence. Please verify the identification and provide feedback if incorrect.",
        "Low Confidence": "The AI has low confidence. Please verify carefully and consider consulting an expert.",
        "Unable to identify": "The AI cannot identify this pest with sufficient confidence. Please retake the image or consult an expert."
    }
    
    return messages.get(confidence_level, "")
