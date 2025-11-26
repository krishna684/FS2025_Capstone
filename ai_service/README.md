# AGBOT AI Pest Detection Microservice

FastAPI-based microservice for pest detection using deep learning models.

## Features

- Image preprocessing with EXIF orientation correction
- EfficientNet-B0 primary model for fast inference
- ResNet-50 fallback model for low-confidence predictions
- Ensemble logic for optimal accuracy
- GPU support via NVIDIA Docker runtime
- Health check endpoint for monitoring
- Timeout protection (2.8s internal processing limit)

## Architecture

```
POST /ai/detect
    ↓
Preprocess Image (< 100ms)
    ↓
EfficientNet-B0 Inference (< 2s)
    ↓
[If confidence < 85%]
    ↓
ResNet-50 Fallback
    ↓
Select Best Prediction
    ↓
Return JSON Response
```

## API Endpoints

### Health Check
```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "ai-pest-detection",
  "timestamp": 1700000000.0
}
```

### Pest Detection
```
POST /ai/detect
Content-Type: multipart/form-data
```

Request:
- `image`: Image file (PNG, JPG, JPEG, GIF, WEBP)

Response:
```json
{
  "pest_label": "Fall Armyworm",
  "scientific_name": "Spodoptera frugiperda",
  "confidence": 0.9234,
  "alternatives": [
    {"label": "Corn Borer", "confidence": 0.0543},
    {"label": "Aphids", "confidence": 0.0123}
  ],
  "processing_time_ms": 1543.21,
  "timing_breakdown": {
    "preprocessing_ms": 87.45,
    "primary_inference_ms": 1432.10,
    "fallback_inference_ms": 0,
    "total_ms": 1543.21
  },
  "fallback_used": false
}
```

Error Responses:
- `400 Bad Request`: Invalid image format
- `408 Request Timeout`: Processing exceeded 2.8 seconds
- `500 Internal Server Error`: Processing failure

## Installation

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
python main.py
```

The service will be available at `http://localhost:8000`

### Docker Deployment

1. Build the image:
```bash
docker build -t agbot-ai-service .
```

2. Run with GPU support:
```bash
docker run --gpus all -p 8000:8000 agbot-ai-service
```

3. Run without GPU (CPU only):
```bash
docker run -p 8000:8000 agbot-ai-service
```

## Model Files

Place trained model files in the `models/` directory:
- `models/efficientnet_b0_pest_detection.h5` - Primary model
- `models/resnet50_pest_detection.h5` - Fallback model

If model files are not present, the service will use transfer learning with ImageNet weights (for development/testing only).

## Configuration

Environment variables:
- `TF_CPP_MIN_LOG_LEVEL`: TensorFlow logging level (default: 2)
- `PYTHONUNBUFFERED`: Python output buffering (default: 1)

## Performance Targets

- Preprocessing: < 100ms
- Primary inference: < 2 seconds
- Total processing: < 3 seconds (including network overhead)
- Fallback threshold: 85% confidence

## Requirements

See `requirements.txt` for full dependencies:
- FastAPI
- TensorFlow 2.15
- OpenCV
- NumPy
- Pillow
- Uvicorn

## Testing

Run tests:
```bash
pytest tests/
```

## License

Copyright © 2025 AGBOT Team
