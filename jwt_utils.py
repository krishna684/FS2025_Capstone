"""
JWT token utilities for authentication
Implements JWT token generation and validation with 24-hour expiration
Requirements: 11.2
"""
import jwt
from datetime import datetime, timedelta
from flask import current_app
import logging

logger = logging.getLogger(__name__)


def generate_jwt_token(user_id, email):
    """
    Generate JWT token with 24-hour expiration
    
    Args:
        user_id: User ID
        email: User email
        
    Returns:
        JWT token string
        
    Requirements: 11.2 - JWT token with 24-hour expiration
    """
    try:
        # Set expiration to exactly 24 hours from now
        expiration = datetime.utcnow() + timedelta(hours=24)
        
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': expiration,
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        logger.info(f"Generated JWT token for user_id={user_id}, expires at {expiration.isoformat()}")
        return token
        
    except Exception as e:
        logger.error(f"Error generating JWT token: {e}", exc_info=True)
        return None


def verify_jwt_token(token):
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dict or None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying JWT token: {e}", exc_info=True)
        return None


def refresh_jwt_token(token):
    """
    Refresh JWT token if it's still valid
    Issues a new token with fresh 24-hour expiration
    
    Args:
        token: Current JWT token
        
    Returns:
        New JWT token or None if current token is invalid
    """
    payload = verify_jwt_token(token)
    
    if not payload:
        return None
    
    # Generate new token with same user info
    return generate_jwt_token(payload['user_id'], payload['email'])
