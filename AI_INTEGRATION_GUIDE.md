# AI Service Integration Guide

## Overview

This guide explains how the Flask backend integrates with the AI microservice for pest detection. The integration implements requirements 2.2, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 5.3, and 9.4.

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │ ──────> │ Flask Backend│ ──────> │ AI Service  │
│  (Browser)  │ <────── │   (app.py)   │ <────── │  (FastAPI)  │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              ├──> PostgreSQL (scan records)
                              └──> MongoDB (detailed metadata)
```

## Components

### 1. AI Client Module (`ai_client.py`)

**Purpose**: Handles communication with the AI microservice

**Key Function**: `call_ai_service(image_path)`
- Sends image to AI service at `http://localhost:8000/ai/detect`
- Enforces 3-second timeout (ultimate enforcer)
- Handles errors: timeouts, connection errors, invalid responses
- Returns structured response with success flag

**Error Handling**:
- `timeout`: Returns "Analysis taking longer than expected. Please try again."
- `connection_error`: Returns "AI service temporarily unavailable."
- `file_not_found`: Returns "Image file not found"
- `service_error`: Returns specific error from AI service

### 2. Confidence Utilities (`confidence_utils.py`)

**Purpose**: Classifies confidence scores and determines feedback prompting

**Key Functions**:

1. `classify_confidence(score)` - Maps confidence to human-readable levels:
   - `>= 0.85`: "High Confidence"
   - `0.70 - 0.84`: "Moderate Confidence"
   - `0.50 - 0.69`: "Low Confidence"
   - `< 0.50`: "Unable to identify"

2. `should_request_feedback(confidence)` - Returns True if confidence < 0.75

3. `get_confidence_message(level)` - Returns user-friendly explanation

### 3. Updated `/analyze` Endpoint (`app.py`)

**Flow**:

1. **Image Upload**
   - Accepts file upload or base64 image
   - Validates file format (PNG, JPG, JPEG, GIF, WEBP)
   - Saves to `static/uploads/` with timestamp

2. **AI Service Call**
   - Calls `call_ai_service(filepath)`
   - Receives pest_label, scientific_name, confidence, alternatives
   - Handles errors gracefully

3. **Confidence Classification**
   - Classifies confidence level
   - Determines if feedback should be requested

4. **Pest Lookup**
   - Queries PostgreSQL `pests` table by name
   - Gets localized pest name based on user language
   - Retrieves pest_id for IPM recommendations

5. **IPM Recommendations**
   - Calls `get_recommendations(pest_id, crop, region, language)`
   - Returns ordered list of treatments (cultural/biological first)

6. **Database Storage**
   - **PostgreSQL**: Stores scan record with basic info
   - **MongoDB**: Stores detailed metadata asynchronously
   - Uses `sync_detection_metadata()` for async MongoDB write

7. **Response**
   - Returns complete JSON with:
     - scan_id (for feedback submission)
     - pest_identified, pest_scientific
     - confidence (as percentage), confidence_level
     - alternatives, recommendations
     - processing_time_ms
     - should_request_feedback flag

## API Response Format

### Success Response

```json
{
  "success": true,
  "scan_id": 101,
  "pest_identified": "Japanese Beetle",
  "pest_scientific": "Popillia japonica",
  "confidence": 92.5,
  "confidence_level": "High Confidence",
  "alternatives": [
    {"label": "Aphids", "confidence": 0.05},
    {"label": "Spider Mites", "confidence": 0.03}
  ],
  "recommendations": [
    {
      "treatment_name": "Hand-picking",
      "type": "cultural",
      "description": "Remove beetles by hand in early morning",
      "priority": "primary",
      "is_last_resort": false
    },
    {
      "treatment_name": "Neem oil spray",
      "type": "biological",
      "description": "Apply neem oil following label instructions",
      "priority": "secondary",
      "is_last_resort": false
    }
  ],
  "processing_time_ms": 1543.2,
  "should_request_feedback": false,
  "timestamp": "2025-11-25T14:30:45.123456"
}
```

### Error Response

```json
{
  "error": "Analysis taking longer than expected. Please try again."
}
```

## Database Schema

### PostgreSQL - `scans` Table

```sql
CREATE TABLE scans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    image_path VARCHAR(255),
    pest_identified VARCHAR(100),
    pest_scientific VARCHAR(100),
    confidence FLOAT,
    status VARCHAR(50),
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### MongoDB - `detection_meta` Collection

```json
{
  "_id": "scan_101",
  "user_id": 42,
  "pest_label": "Japanese Beetle",
  "confidence": 0.925,
  "alternatives": [...],
  "image_info": {
    "filename": "20251125_143022_leaf.jpg",
    "file_size_kb": 2048
  },
  "model_details": {
    "primary_model": "EfficientNet-B0",
    "primary_version": "v2.1.0",
    "fallback_used": false,
    "preprocessing_time_ms": 87.5,
    "inference_time_ms": 1455.7,
    "total_time_ms": 1543.2
  },
  "timestamp": "2025-11-25T14:30:45Z"
}
```

## Running the System

### 1. Start AI Service

```bash
cd ai_service
python main.py
```

The AI service will start on `http://localhost:8000`

### 2. Start Flask Backend

```bash
python app.py
```

The Flask backend will start on `http://localhost:5001`

### 3. Test the Integration

```bash
# Check AI service health
curl http://localhost:8000/health

# Test detection (requires image file)
curl -X POST http://localhost:5001/analyze \
  -F "image=@test_image.jpg" \
  -H "Authorization: Bearer <token>"
```

## Testing

Run the integration tests:

```bash
python -m pytest test_ai_integration.py -v
```

Tests cover:
- Confidence classification (all levels and boundaries)
- Feedback prompting logic
- AI client success scenarios
- AI client error handling (timeout, connection, file not found)

## Configuration

### AI Service URL

Default: `http://localhost:8000`

To change, edit `ai_client.py`:

```python
AI_SERVICE_URL = "http://your-ai-service-url:port"
```

### Timeout

Default: 3 seconds

To change, edit `ai_client.py`:

```python
AI_SERVICE_TIMEOUT = 3.0  # seconds
```

## Error Handling

The integration implements comprehensive error handling:

1. **Timeout Errors**: User-friendly message, retry suggested
2. **Connection Errors**: Service unavailable message
3. **File Errors**: Clear indication of missing file
4. **Service Errors**: Specific error details from AI service
5. **Unexpected Errors**: Logged with full traceback

All errors are logged for debugging and monitoring.

## Performance

- **Target**: < 3 seconds total analysis time
- **Timeout**: 3 seconds enforced at client level
- **AI Service**: 2.8 seconds internal timeout (200ms buffer)
- **Async MongoDB**: Non-blocking writes to MongoDB

## Security

- **Authentication**: `/analyze` endpoint requires login (`@login_required`)
- **File Validation**: Only allowed extensions (PNG, JPG, JPEG, GIF, WEBP)
- **Secure Filenames**: Uses `secure_filename()` to prevent path traversal
- **Timeout Protection**: Prevents long-running requests

## Monitoring

Key metrics to monitor:
- AI service response time
- Timeout frequency
- Connection error rate
- Confidence score distribution
- Feedback request rate

## Troubleshooting

### AI Service Not Reachable

**Symptom**: "AI service temporarily unavailable"

**Solution**:
1. Check if AI service is running: `curl http://localhost:8000/health`
2. Verify AI_SERVICE_URL in `ai_client.py`
3. Check firewall/network settings

### Timeout Errors

**Symptom**: "Analysis taking longer than expected"

**Solution**:
1. Check AI service performance
2. Verify GPU availability for AI service
3. Consider increasing timeout (not recommended)
4. Check image size (large images take longer)

### Missing Recommendations

**Symptom**: Empty recommendations array

**Solution**:
1. Verify pest exists in `pests` table
2. Check IPM recommendations are seeded
3. Verify `get_pest_by_name()` finds the pest

## Future Enhancements

1. **Caching**: Cache AI service responses for identical images
2. **Queue System**: Use Celery for async AI service calls
3. **Load Balancing**: Multiple AI service instances
4. **Retry Logic**: Automatic retry on transient failures
5. **Circuit Breaker**: Prevent cascading failures
