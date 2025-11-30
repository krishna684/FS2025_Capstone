"""
AI Microservice for Pest Detection
FastAPI application for image preprocessing and pest identification
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import time
from typing import Dict, List, Optional
import logging
import asyncio

from preprocessing import preprocess_image
from models import get_model, get_scientific_name, get_model_versions
from ensemble import ensemble_predict, should_invoke_fallback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AGBOT AI Pest Detection Service", version="1.0.0")

# Timeout for internal processing (2.8 seconds, allowing 200ms buffer for network)
PROCESSING_TIMEOUT = 2.8


@app.on_event("startup")
async def startup_event():
    """Load models at startup"""
    logger.info("Starting AI service and loading models...")
    # Initialize model (loads both primary and fallback)
    get_model()
    logger.info("Models loaded successfully")


@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring"""
    return {
        "status": "healthy",
        "service": "ai-pest-detection",
        "timestamp": time.time()
    }


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "AGBOT AI Pest Detection Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "detect": "/ai/detect"
        }
    }


@app.post("/ai/detect")
async def detect_pest(image: UploadFile = File(...)):
    """
    Detect pest from uploaded image
    
    Process:
    1. Preprocess image (orientation, resize, normalize)
    2. Run primary model inference (EfficientNet-B0)
    3. If confidence < 85%, run fallback model (ResNet-50)
    4. Select prediction with highest confidence
    5. Return results with processing time
    
    Args:
        image: Uploaded image file (multipart form data)
        
    Returns:
        JSON with pest_label, scientific_name, confidence, alternatives, processing_time_ms
        
    Raises:
        408 Timeout if processing exceeds 2.8 seconds
        400 Bad Request for invalid image
        500 Internal Server Error for processing failures
        
    Requirements: 2.2, 2.5, 3.1
    """
    start_time = time.time()
    
    try:
        # Read image data
        image_data = await image.read()
        
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        # Wrap processing in timeout
        try:
            result = await asyncio.wait_for(
                _process_image(image_data, start_time),
                timeout=PROCESSING_TIMEOUT
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"Processing timeout exceeded {PROCESSING_TIMEOUT}s")
            raise HTTPException(
                status_code=408,
                detail="Analysis taking longer than expected. Please try again."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


async def _process_image(image_data: bytes, start_time: float) -> Dict:
    """
    Internal function to process image and run inference
    
    Args:
        image_data: Raw image bytes
        start_time: Request start timestamp
        
    Returns:
        Detection result dictionary
    """
    # Step 1: Preprocess image
    preprocess_start = time.time()
    try:
        image_tensor = preprocess_image(image_data)
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
    
    preprocess_time = (time.time() - preprocess_start) * 1000  # Convert to ms
    logger.info(f"Preprocessing completed in {preprocess_time:.2f}ms")
    
    # Step 2: Get model instance
    model = get_model()
    
    # Step 3: Run primary model inference
    inference_start = time.time()
    primary_label, primary_conf, primary_alts = model.predict_primary(image_tensor)
    primary_inference_time = (time.time() - inference_start) * 1000
    logger.info(f"Primary inference completed in {primary_inference_time:.2f}ms: "
                f"{primary_label} ({primary_conf:.2f})")
    
    # Step 4: Check if fallback is needed
    fallback_used = False
    fallback_inference_time = 0
    
    if should_invoke_fallback(primary_conf):
        logger.info(f"Primary confidence {primary_conf:.2f} < 0.85, invoking fallback model")
        fallback_start = time.time()
        fallback_label, fallback_conf, fallback_alts = model.predict_fallback(image_tensor)
        fallback_inference_time = (time.time() - fallback_start) * 1000
        logger.info(f"Fallback inference completed in {fallback_inference_time:.2f}ms: "
                    f"{fallback_label} ({fallback_conf:.2f})")
        
        # Step 5: Ensemble - select best prediction
        final_label, final_conf, final_alts, fallback_used = ensemble_predict(
            (primary_label, primary_conf, primary_alts),
            (fallback_label, fallback_conf, fallback_alts)
        )
    else:
        final_label = primary_label
        final_conf = primary_conf
        final_alts = primary_alts
    
    # Calculate total processing time
    total_time = (time.time() - start_time) * 1000
    
    # Get scientific name
    scientific_name = get_scientific_name(final_label)
    
    # Get model versions
    model_versions = get_model_versions()
    
    # Build response
    response = {
        "pest_label": final_label,
        "scientific_name": scientific_name,
        "confidence": round(final_conf, 4),
        "alternatives": final_alts,
        "processing_time_ms": round(total_time, 2),
        "timing_breakdown": {
            "preprocessing_ms": round(preprocess_time, 2),
            "primary_inference_ms": round(primary_inference_time, 2),
            "fallback_inference_ms": round(fallback_inference_time, 2) if fallback_used else 0,
            "total_ms": round(total_time, 2)
        },
        "fallback_used": fallback_used,
        "model_version": model_versions['primary_model_version'],
        "model_details": {
            "primary_model": "EfficientNet-B0",
            "primary_version": model_versions['primary_model_version'],
            "fallback_model": "ResNet-50",
            "fallback_version": model_versions['fallback_model_version'],
            "fallback_used": fallback_used
        }
    }
    
    logger.info(f"Detection complete: {final_label} ({final_conf:.2f}) in {total_time:.2f}ms "
                f"[Model: {model_versions['primary_model_version']}]")
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
