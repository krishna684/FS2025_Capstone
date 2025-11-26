# Quick Start Guide - AI Microservice

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- (Optional) Docker with NVIDIA runtime for GPU support

## Option 1: Local Development (Fastest)

### Windows

1. Open Command Prompt or PowerShell
2. Navigate to the ai_service directory:
   ```cmd
   cd ai_service
   ```
3. Run the startup script:
   ```cmd
   start_service.bat
   ```

### Linux/Mac

1. Open Terminal
2. Navigate to the ai_service directory:
   ```bash
   cd ai_service
   ```
3. Make the script executable and run:
   ```bash
   chmod +x start_service.sh
   ./start_service.sh
   ```

The service will be available at: **http://localhost:8000**

## Option 2: Docker (Recommended for Production)

### Build and Run

```bash
# Build the Docker image
docker build -t agbot-ai-service ./ai_service

# Run with GPU support (if available)
docker run --gpus all -p 8000:8000 agbot-ai-service

# Or run without GPU (CPU only)
docker run -p 8000:8000 agbot-ai-service
```

### Using Docker Compose

```bash
# Start the AI service
docker-compose up ai-service

# Run in background
docker-compose up -d ai-service

# Stop the service
docker-compose down
```

## Verify Installation

### Check Health

Open your browser and visit:
```
http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "service": "ai-pest-detection",
  "timestamp": 1700000000.0
}
```

### Run Test Script

```bash
cd ai_service
python test_service.py
```

Expected output:
```
============================================================
AGBOT AI Service Test Suite
============================================================
Testing health check endpoint...
Status: 200
Response: {'status': 'healthy', ...}

Testing pest detection endpoint...
Status: 200
Pest detected: Fall Armyworm
Scientific name: Spodoptera frugiperda
Confidence: 92.34%
Processing time: 1543.21ms
Fallback used: False

============================================================
Test Results:
  Health Check: ✓ PASS
  Detection:    ✓ PASS
============================================================

✓ All tests passed!
```

## Test with cURL

### Health Check
```bash
curl http://localhost:8000/health
```

### Pest Detection
```bash
curl -X POST http://localhost:8000/ai/detect \
  -F "image=@/path/to/your/image.jpg"
```

## Test with Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Pest detection
with open("test_image.jpg", "rb") as f:
    files = {"image": f}
    response = requests.post("http://localhost:8000/ai/detect", files=files)
    print(response.json())
```

## Common Issues

### Port Already in Use

If port 8000 is already in use:

**Option 1**: Stop the process using port 8000
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Option 2**: Use a different port
```bash
# Edit main.py and change:
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Module Not Found Errors

Install dependencies manually:
```bash
pip install -r ai_service/requirements.txt
```

### TensorFlow GPU Issues

If you see GPU-related errors but want to use CPU:
```bash
export CUDA_VISIBLE_DEVICES=""  # Linux/Mac
set CUDA_VISIBLE_DEVICES=       # Windows
```

### Docker GPU Not Working

Ensure NVIDIA Docker runtime is installed:
```bash
# Check if GPU is available
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## Next Steps

1. **Add Trained Models**: Place your trained models in `ai_service/models/`
   - `efficientnet_b0_pest_detection.h5`
   - `resnet50_pest_detection.h5`

2. **Integrate with Flask**: Follow the `INTEGRATION_GUIDE.md`

3. **Configure for Production**: Update environment variables and security settings

4. **Monitor Performance**: Check logs and timing metrics

## API Documentation

Once the service is running, visit:
```
http://localhost:8000/docs
```

This provides interactive API documentation (Swagger UI).

## Support

For issues or questions:
1. Check the logs: `docker logs agbot-ai-service`
2. Review `AI_SERVICE_IMPLEMENTATION.md` for details
3. See `INTEGRATION_GUIDE.md` for Flask integration

## Performance Notes

- **First Request**: May take 10-30 seconds (model loading)
- **Subsequent Requests**: Should complete in < 3 seconds
- **With GPU**: Inference time ~1-2 seconds
- **Without GPU**: Inference time ~3-5 seconds

Models are cached in memory after first load for optimal performance.
