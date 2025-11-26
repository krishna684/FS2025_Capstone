# AI Service Integration Guide

## Overview

This guide explains how to integrate the AI microservice with the Flask backend.

## Architecture

```
Flask Backend (Port 5001)
    ↓ HTTP Request
AI Microservice (Port 8000)
    ↓ JSON Response
Flask Backend
    ↓ Processed Data
Frontend
```

## Integration Steps

### 1. Install Requests Library

Add to main `requirements.txt`:
```
requests==2.31.0
```

### 2. Create AI Client Module

Create `ai_client.py` in the Flask app directory:

```python
import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# AI service configuration
AI_SERVICE_URL = "http://localhost:8000"  # Change for production
AI_DETECT_ENDPOINT = f"{AI_SERVICE_URL}/ai/detect"
AI_HEALTH_ENDPOINT = f"{AI_SERVICE_URL}/health"
REQUEST_TIMEOUT = 3.0  # 3 seconds total timeout


def call_ai_service(image_path: str) -> Optional[Dict]:
    """
    Call AI microservice for pest detection
    
    Args:
        image_path: Path to image file
        
    Returns:
        Detection result dict or None on error
    """
    try:
        # Open and send image
        with open(image_path, 'rb') as img_file:
            files = {'image': img_file}
            response = requests.post(
                AI_DETECT_ENDPOINT,
                files=files,
                timeout=REQUEST_TIMEOUT
            )
        
        # Check response
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 408:
            logger.warning("AI service timeout")
            return {
                'error': 'timeout',
                'message': 'Analysis taking longer than expected. Please try again.'
            }
        else:
            logger.error(f"AI service error: {response.status_code}")
            return {
                'error': 'service_error',
                'message': 'Unable to process image. Please try again.'
            }
    
    except requests.exceptions.Timeout:
        logger.error("Request timeout to AI service")
        return {
            'error': 'timeout',
            'message': 'Analysis taking longer than expected. Please try again.'
        }
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to AI service")
        return {
            'error': 'connection_error',
            'message': 'AI service unavailable. Please try again later.'
        }
    except Exception as e:
        logger.error(f"Unexpected error calling AI service: {e}")
        return {
            'error': 'unknown',
            'message': 'An error occurred. Please try again.'
        }


def check_ai_service_health() -> bool:
    """
    Check if AI service is healthy
    
    Returns:
        True if service is healthy, False otherwise
    """
    try:
        response = requests.get(AI_HEALTH_ENDPOINT, timeout=2.0)
        return response.status_code == 200
    except:
        return False
```

### 3. Update Flask `/analyze` Endpoint

Modify the `/analyze` route in `app.py`:

```python
from ai_client import call_ai_service

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle image upload and analysis"""
    try:
        # Handle file upload (existing code)
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Call AI service
        ai_result = call_ai_service(filepath)
        
        # Check for errors
        if ai_result and 'error' in ai_result:
            return jsonify(ai_result), 500
        
        # Extract results
        pest_label = ai_result['pest_label']
        scientific_name = ai_result['scientific_name']
        confidence = ai_result['confidence']
        
        # Look up pest details from database (if needed)
        # pest = PestDatabase.query.filter_by(common_name=pest_label).first()
        
        # Get IPM recommendations (implement in task 3)
        # recommendations = get_ipm_recommendations(pest_label)
        
        # Store in database
        scan = Scan(
            user_id=current_user.id,
            image_path=filepath,
            pest_identified=pest_label,
            pest_scientific=scientific_name,
            confidence=confidence,
            status='identified'
        )
        db.session.add(scan)
        db.session.commit()
        
        # Build response
        result = {
            'status': 'Pest Damaged' if pest_label != 'Healthy' else 'Healthy',
            'pest_identified': pest_label,
            'pest_scientific': scientific_name,
            'confidence': confidence * 100,  # Convert to percentage
            'scan_id': scan.id,
            'processing_time_ms': ai_result['processing_time_ms'],
            'alternatives': ai_result['alternatives']
        }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}")
        return jsonify({'error': str(e)}), 500
```

### 4. Environment Configuration

Create `.env` file:
```
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_TIMEOUT=3.0
```

Load in Flask app:
```python
from dotenv import load_dotenv
load_dotenv()

AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'http://localhost:8000')
```

### 5. Docker Compose Integration

Update `docker-compose.yml` to include Flask backend:

```yaml
services:
  ai-service:
    # ... existing config ...
  
  flask-backend:
    build:
      context: .
      dockerfile: Dockerfile.flask
    container_name: agbot-flask-backend
    ports:
      - "5001:5001"
    environment:
      - FLASK_ENV=development
      - AI_SERVICE_URL=http://ai-service:8000
    depends_on:
      - ai-service
    restart: unless-stopped
```

## Testing Integration

### 1. Start Both Services

Terminal 1 (AI Service):
```bash
cd ai_service
python main.py
```

Terminal 2 (Flask Backend):
```bash
python app.py
```

### 2. Test Health Check

```python
from ai_client import check_ai_service_health

if check_ai_service_health():
    print("AI service is healthy")
else:
    print("AI service is unavailable")
```

### 3. Test Detection

Upload an image through the Flask `/analyze` endpoint and verify:
- Image is sent to AI service
- Response is received within 3 seconds
- Results are stored in database
- Frontend receives formatted response

## Error Handling

The integration handles these scenarios:

1. **AI Service Unavailable**: Returns connection error message
2. **Timeout (> 3s)**: Returns timeout message
3. **Invalid Image**: AI service returns 400 error
4. **Processing Error**: Returns generic error message

## Performance Considerations

- **Timeout**: Set to 3 seconds to match requirement
- **Connection Pooling**: Use `requests.Session()` for multiple requests
- **Async Processing**: Consider Celery for background processing
- **Caching**: Cache frequent predictions (optional)

## Production Deployment

For production:

1. Update `AI_SERVICE_URL` to production endpoint
2. Use HTTPS for secure communication
3. Add authentication between services (API keys)
4. Implement retry logic with exponential backoff
5. Add circuit breaker pattern for resilience
6. Monitor service health and latency

## Next Steps

After integration:
1. Implement IPM recommendation engine (Task 3)
2. Add confidence level classification (Task 4.2)
3. Store results in hybrid database (Task 4.3)
4. Implement feedback collection (Task 6)

## Troubleshooting

### AI Service Not Responding
- Check if service is running: `curl http://localhost:8000/health`
- Check Docker logs: `docker logs agbot-ai-service`
- Verify port is not blocked by firewall

### Timeout Errors
- Check AI service logs for slow inference
- Verify GPU is being used (if available)
- Consider increasing timeout for development

### Connection Refused
- Ensure AI service is started before Flask backend
- Check `AI_SERVICE_URL` configuration
- Verify network connectivity between containers
