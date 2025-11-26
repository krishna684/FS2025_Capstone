"""
Model loading and inference for pest detection
Implements EfficientNet-B0 primary model and ResNet-50 fallback
"""
import tensorflow as tf
from tensorflow import keras
import numpy as np
from typing import Tuple, List, Dict
import logging
import os

logger = logging.getLogger(__name__)

# Pest class labels (in production, load from config or database)
PEST_LABELS = [
    "Fall Armyworm",
    "Aphids",
    "Tomato Leafminer",
    "Whitefly",
    "Spider Mites",
    "Japanese Beetle",
    "Cabbage Worm",
    "Corn Borer",
    "Thrips",
    "Healthy"
]

# Scientific names mapping
SCIENTIFIC_NAMES = {
    "Fall Armyworm": "Spodoptera frugiperda",
    "Aphids": "Aphidoidea",
    "Tomato Leafminer": "Tuta absoluta",
    "Whitefly": "Aleyrodidae",
    "Spider Mites": "Tetranychidae",
    "Japanese Beetle": "Popillia japonica",
    "Cabbage Worm": "Pieris rapae",
    "Corn Borer": "Ostrinia nubilalis",
    "Thrips": "Thysanoptera",
    "Healthy": "N/A"
}


class PestDetectionModel:
    """Wrapper for pest detection models with caching"""
    
    def __init__(self):
        self.primary_model = None
        self.fallback_model = None
        self._load_models()
    
    def _load_models(self):
        """Load models at startup and cache in memory"""
        logger.info("Loading EfficientNet-B0 primary model...")
        self.primary_model = self._load_efficientnet()
        logger.info("Primary model loaded successfully")
        
        logger.info("Loading ResNet-50 fallback model...")
        self.fallback_model = self._load_resnet()
        logger.info("Fallback model loaded successfully")
    
    def _load_efficientnet(self) -> keras.Model:
        """
        Load pre-trained EfficientNet-B0 model
        
        In production, this would load a fine-tuned model.
        For MVP, we use transfer learning with ImageNet weights.
        
        Returns:
            Loaded Keras model
            
        Requirements: 2.2
        """
        # Check if custom model exists
        model_path = "models/efficientnet_b0_pest_detection.h5"
        
        if os.path.exists(model_path):
            logger.info(f"Loading custom model from {model_path}")
            model = keras.models.load_model(model_path)
        else:
            logger.info("Loading EfficientNet-B0 with ImageNet weights (transfer learning)")
            # Load base model
            base_model = keras.applications.EfficientNetB0(
                include_top=False,
                weights='imagenet',
                input_shape=(224, 224, 3),
                pooling='avg'
            )
            
            # Add classification head
            inputs = keras.Input(shape=(224, 224, 3))
            x = base_model(inputs, training=False)
            x = keras.layers.Dropout(0.2)(x)
            outputs = keras.layers.Dense(len(PEST_LABELS), activation='softmax')(x)
            
            model = keras.Model(inputs, outputs)
            
            logger.warning("Using untrained model - predictions will be random until fine-tuned")
        
        return model
    
    def _load_resnet(self) -> keras.Model:
        """
        Load pre-trained ResNet-50 fallback model
        
        Returns:
            Loaded Keras model
            
        Requirements: 2.3
        """
        model_path = "models/resnet50_pest_detection.h5"
        
        if os.path.exists(model_path):
            logger.info(f"Loading custom ResNet model from {model_path}")
            model = keras.models.load_model(model_path)
        else:
            logger.info("Loading ResNet-50 with ImageNet weights (transfer learning)")
            # Load base model
            base_model = keras.applications.ResNet50(
                include_top=False,
                weights='imagenet',
                input_shape=(224, 224, 3),
                pooling='avg'
            )
            
            # Add classification head
            inputs = keras.Input(shape=(224, 224, 3))
            x = base_model(inputs, training=False)
            x = keras.layers.Dropout(0.2)(x)
            outputs = keras.layers.Dense(len(PEST_LABELS), activation='softmax')(x)
            
            model = keras.Model(inputs, outputs)
            
            logger.warning("Using untrained ResNet model - predictions will be random until fine-tuned")
        
        return model
    
    def predict_primary(self, image_tensor: np.ndarray) -> Tuple[str, float, List[Dict[str, float]]]:
        """
        Perform inference using EfficientNet-B0 primary model
        
        Args:
            image_tensor: Preprocessed image tensor (1, 224, 224, 3)
            
        Returns:
            Tuple of (pest_label, confidence, alternatives)
            - pest_label: Predicted pest name
            - confidence: Confidence score (0-1)
            - alternatives: List of top-3 alternative predictions
            
        Requirements: 2.2
        """
        # Run inference
        predictions = self.primary_model.predict(image_tensor, verbose=0)
        
        # Get top prediction
        top_idx = np.argmax(predictions[0])
        pest_label = PEST_LABELS[top_idx]
        confidence = float(predictions[0][top_idx])
        
        # Get top-N alternatives (N=3)
        alternatives = self._get_top_n_predictions(predictions[0], n=3, exclude_top=True)
        
        return pest_label, confidence, alternatives
    
    def predict_fallback(self, image_tensor: np.ndarray) -> Tuple[str, float, List[Dict[str, float]]]:
        """
        Perform inference using ResNet-50 fallback model
        
        Args:
            image_tensor: Preprocessed image tensor (1, 224, 224, 3)
            
        Returns:
            Tuple of (pest_label, confidence, alternatives)
            
        Requirements: 2.3
        """
        # Run inference
        predictions = self.fallback_model.predict(image_tensor, verbose=0)
        
        # Get top prediction
        top_idx = np.argmax(predictions[0])
        pest_label = PEST_LABELS[top_idx]
        confidence = float(predictions[0][top_idx])
        
        # Get top-N alternatives
        alternatives = self._get_top_n_predictions(predictions[0], n=3, exclude_top=True)
        
        return pest_label, confidence, alternatives
    
    def _get_top_n_predictions(self, predictions: np.ndarray, n: int = 3, 
                               exclude_top: bool = False) -> List[Dict[str, float]]:
        """
        Extract top-N predictions from model output
        
        Args:
            predictions: Model prediction array
            n: Number of top predictions to return
            exclude_top: If True, exclude the top prediction
            
        Returns:
            List of dicts with 'label' and 'confidence'
        """
        # Get indices of top predictions
        top_indices = np.argsort(predictions)[::-1]
        
        # Skip first if excluding top
        start_idx = 1 if exclude_top else 0
        
        alternatives = []
        for idx in top_indices[start_idx:start_idx + n]:
            alternatives.append({
                'label': PEST_LABELS[idx],
                'confidence': float(predictions[idx])
            })
        
        return alternatives


# Global model instance (loaded at startup)
_model_instance = None


def get_model() -> PestDetectionModel:
    """Get or create global model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = PestDetectionModel()
    return _model_instance


def get_scientific_name(pest_label: str) -> str:
    """Get scientific name for a pest label"""
    return SCIENTIFIC_NAMES.get(pest_label, "Unknown")
