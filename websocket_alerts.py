"""
WebSocket notification system for outbreak alerts
Requirements: 12.4
"""
import logging
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from flask import request

logger = logging.getLogger(__name__)

# SocketIO instance (will be initialized in app.py)
socketio = None


def init_socketio(app):
    """
    Initialize Flask-SocketIO with the Flask app
    
    Args:
        app: Flask application instance
    
    Returns:
        SocketIO instance
    """
    global socketio
    
    # Initialize SocketIO with Redis for production scalability
    # For development, can work without Redis (async_mode='threading')
    try:
        socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='threading',  # Use 'eventlet' or 'gevent' in production with Redis
            logger=True,
            engineio_logger=False
        )
        logger.info("Flask-SocketIO initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Flask-SocketIO: {e}")
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Register event handlers
    register_socketio_events()
    
    return socketio


def register_socketio_events():
    """
    Register WebSocket event handlers
    """
    
    @socketio.on('connect', namespace='/alerts')
    def handle_connect():
        """Handle client connection to alerts namespace"""
        if current_user.is_authenticated:
            # Join room based on user's location for region-specific alerts
            if current_user.location:
                room = f"region_{current_user.location}"
                join_room(room)
                logger.info(f"User {current_user.id} joined room: {room}")
                emit('connection_status', {
                    'status': 'connected',
                    'region': current_user.location,
                    'message': f'Connected to outbreak alerts for {current_user.location}'
                })
            else:
                emit('connection_status', {
                    'status': 'connected',
                    'region': None,
                    'message': 'Connected to outbreak alerts (no region set)'
                })
        else:
            emit('connection_status', {
                'status': 'connected',
                'authenticated': False,
                'message': 'Connected as guest'
            })
    
    @socketio.on('disconnect', namespace='/alerts')
    def handle_disconnect():
        """Handle client disconnection"""
        if current_user.is_authenticated:
            logger.info(f"User {current_user.id} disconnected from alerts")
    
    @socketio.on('subscribe_region', namespace='/alerts')
    def handle_subscribe_region(data):
        """
        Allow users to subscribe to specific region alerts
        
        Args:
            data: Dictionary with 'region' key
        """
        region = data.get('region')
        if region:
            room = f"region_{region}"
            join_room(room)
            logger.info(f"Client subscribed to region: {region}")
            emit('subscription_status', {
                'status': 'subscribed',
                'region': region,
                'message': f'Subscribed to alerts for {region}'
            })
    
    @socketio.on('unsubscribe_region', namespace='/alerts')
    def handle_unsubscribe_region(data):
        """
        Allow users to unsubscribe from specific region alerts
        
        Args:
            data: Dictionary with 'region' key
        """
        region = data.get('region')
        if region:
            room = f"region_{region}"
            leave_room(room)
            logger.info(f"Client unsubscribed from region: {region}")
            emit('subscription_status', {
                'status': 'unsubscribed',
                'region': region,
                'message': f'Unsubscribed from alerts for {region}'
            })


def emit_outbreak_alert(alert):
    """
    Emit outbreak alert to all connected clients in the affected region
    Filters recipients by user.location matching alert region
    
    Requirements: 12.4
    
    Args:
        alert: Dictionary containing outbreak alert data with keys:
            - pest: Pest type
            - region: Affected region
            - current_count: Current occurrence count
            - historical_average: Historical average
            - threshold_exceeded: Multiplier of threshold exceeded
            - alert_issued: Timestamp
    """
    if not socketio:
        logger.warning("SocketIO not initialized, cannot emit outbreak alert")
        return
    
    try:
        region = alert.get('region')
        pest = alert.get('pest')
        
        if not region or not pest:
            logger.error("Invalid alert data: missing region or pest")
            return
        
        # Prepare alert message
        alert_message = {
            'type': 'outbreak_alert',
            'pest': pest,
            'region': region,
            'current_count': alert.get('current_count'),
            'historical_average': alert.get('historical_average'),
            'threshold_exceeded': alert.get('threshold_exceeded'),
            'alert_issued': alert.get('alert_issued'),
            'severity': 'high' if alert.get('threshold_exceeded', 0) > 2.0 else 'moderate',
            'message': f"Outbreak alert: {pest} detected in {region} at {alert.get('threshold_exceeded', 0):.1f}x normal levels"
        }
        
        # Emit to region-specific room
        room = f"region_{region}"
        socketio.emit('outbreak_alert', alert_message, room=room, namespace='/alerts')
        
        logger.info(f"Emitted outbreak alert for {pest} in {region} to room: {room}")
        
    except Exception as e:
        logger.error(f"Error emitting outbreak alert: {e}", exc_info=True)


def emit_outbreak_alerts_batch(alerts):
    """
    Emit multiple outbreak alerts
    
    Args:
        alerts: List of alert dictionaries
    """
    for alert in alerts:
        emit_outbreak_alert(alert)
    
    logger.info(f"Emitted {len(alerts)} outbreak alerts")


def broadcast_system_message(message, severity='info'):
    """
    Broadcast a system message to all connected clients
    
    Args:
        message: Message text
        severity: Message severity (info, warning, error)
    """
    if not socketio:
        logger.warning("SocketIO not initialized, cannot broadcast message")
        return
    
    try:
        socketio.emit('system_message', {
            'type': 'system',
            'message': message,
            'severity': severity,
            'timestamp': None  # Will be set by client
        }, namespace='/alerts')
        
        logger.info(f"Broadcasted system message: {message}")
        
    except Exception as e:
        logger.error(f"Error broadcasting system message: {e}")
