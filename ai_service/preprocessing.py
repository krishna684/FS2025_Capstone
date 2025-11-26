"""
Image preprocessing pipeline for pest detection
Handles EXIF orientation, color space conversion, and normalization
"""
import cv2
import numpy as np
from PIL import Image
import io
from typing import Union


def preprocess_image(image_data: Union[bytes, np.ndarray]) -> np.ndarray:
    """
    Preprocess image for model inference
    
    Steps:
    1. Load image and correct EXIF orientation
    2. Convert to HSV color space
    3. Apply histogram equalization on V channel
    4. Convert back to BGR
    5. Resize to 224x224
    6. Normalize to [0, 1]
    
    Args:
        image_data: Raw image bytes or numpy array
        
    Returns:
        Preprocessed tensor in model-ready format (224x224x3, normalized)
        
    Requirements: 2.1
    """
    # Load image
    if isinstance(image_data, bytes):
        # Load from bytes with PIL to handle EXIF
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Correct EXIF orientation
        pil_image = _correct_exif_orientation(pil_image)
        
        # Convert PIL to OpenCV format (BGR)
        image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    else:
        image = image_data
    
    # Convert to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Apply histogram equalization on V (brightness) channel
    hsv_image[:, :, 2] = cv2.equalizeHist(hsv_image[:, :, 2])
    
    # Convert back to BGR
    enhanced_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
    
    # Resize to 224x224 (EfficientNet-B0 input size)
    resized_image = cv2.resize(enhanced_image, (224, 224), interpolation=cv2.INTER_AREA)
    
    # Normalize pixel values to [0, 1]
    normalized_image = resized_image.astype(np.float32) / 255.0
    
    # Add batch dimension for model input
    tensor = np.expand_dims(normalized_image, axis=0)
    
    return tensor


def _correct_exif_orientation(image: Image.Image) -> Image.Image:
    """
    Correct image orientation based on EXIF data
    
    Args:
        image: PIL Image object
        
    Returns:
        Corrected PIL Image
    """
    try:
        # Get EXIF data
        exif = image._getexif()
        if exif is None:
            return image
        
        # EXIF orientation tag
        orientation_tag = 0x0112
        
        if orientation_tag in exif:
            orientation = exif[orientation_tag]
            
            # Apply rotation based on orientation value
            if orientation == 2:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 4:
                image = image.transpose(Image.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                image = image.transpose(Image.FLIP_LEFT_RIGHT).rotate(90, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 7:
                image = image.transpose(Image.FLIP_LEFT_RIGHT).rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # If EXIF data is not available or corrupted, return original
        pass
    
    return image
