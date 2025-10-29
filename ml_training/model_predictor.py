"""
Model Predictor for Page Number Detection
Loads trained model and makes fast predictions
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow import keras
import numpy as np
import cv2
import json
from pathlib import Path
from typing import Tuple, Optional

class PageNumberPredictor:
    """Fast predictor using trained ML model"""
    
    def __init__(self, model_dir: str = "ml_training/models"):
        self.model_dir = Path(model_dir)
        self.model = None
        self.class_names = []
        self.loaded = False
        
    def load_model(self) -> bool:
        """Load trained model and metadata"""
        model_path = self.model_dir / "page_detector.h5"
        classes_path = self.model_dir / "class_names.json"
        
        if not model_path.exists():
            return False
        
        try:
            # Load model
            self.model = keras.models.load_model(model_path)
            
            # Load class names
            with open(classes_path, 'r') as f:
                self.class_names = json.load(f)
            
            self.loaded = True
            return True
        
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for model input"""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Resize to model input size (100x100)
        image = cv2.resize(image, (100, 100))
        
        # Normalize
        image = image.astype('float32') / 255.0
        
        # Add batch and channel dimensions
        image = np.expand_dims(image, axis=0)  # Batch
        image = np.expand_dims(image, axis=-1)  # Channel
        
        return image
    
    def predict(self, corner_image: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Predict page number from corner image
        
        Args:
            corner_image: Corner image (numpy array)
        
        Returns:
            (predicted_number, confidence)
            e.g., ("23", 0.95) or (None, 0.0) if not confident
        """
        if not self.loaded:
            return None, 0.0
        
        # Preprocess
        processed = self.preprocess_image(corner_image)
        
        # Predict
        predictions = self.model.predict(processed, verbose=0)[0]
        
        # Get best prediction
        best_idx = np.argmax(predictions)
        confidence = float(predictions[best_idx])
        predicted_class = self.class_names[best_idx]
        
        # Return None for "none" class or low confidence
        if predicted_class == "none" or confidence < 0.5:
            return None, confidence
        
        return predicted_class, confidence
    
    def predict_batch(self, corner_images: list) -> list:
        """Predict multiple images at once (faster)"""
        if not self.loaded or not corner_images:
            return [(None, 0.0)] * len(corner_images)
        
        # Preprocess all
        processed_batch = np.array([
            self.preprocess_image(img)[0] for img in corner_images
        ])
        
        # Predict batch
        predictions = self.model.predict(processed_batch, verbose=0)
        
        # Parse results
        results = []
        for preds in predictions:
            best_idx = np.argmax(preds)
            confidence = float(preds[best_idx])
            predicted_class = self.class_names[best_idx]
            
            if predicted_class == "none" or confidence < 0.5:
                results.append((None, confidence))
            else:
                results.append((predicted_class, confidence))
        
        return results
    
    def get_model_info(self) -> dict:
        """Get information about loaded model"""
        info_path = self.model_dir / "model_info.json"
        
        if info_path.exists():
            with open(info_path, 'r') as f:
                return json.load(f)
        
        return {
            'num_classes': len(self.class_names),
            'loaded': self.loaded
        }


# Singleton instance
_predictor_instance = None

def get_predictor() -> PageNumberPredictor:
    """Get singleton predictor instance"""
    global _predictor_instance
    
    if _predictor_instance is None:
        _predictor_instance = PageNumberPredictor()
        _predictor_instance.load_model()
    
    return _predictor_instance


def test_predictor():
    """Test the predictor"""
    print("=" * 70)
    print("TESTING MODEL PREDICTOR")
    print("=" * 70)
    
    predictor = PageNumberPredictor()
    
    if not predictor.load_model():
        print("\n❌ No trained model found!")
        print("   Please train a model first:")
        print("   python ml_training/quick_trainer.py")
        return
    
    print(f"\n✅ Model loaded successfully!")
    print(f"   Classes: {len(predictor.class_names)}")
    print(f"   Sample classes: {', '.join(predictor.class_names[:10])}")
    
    # Get model info
    info = predictor.get_model_info()
    print(f"\n📊 Model Info:")
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # Test with sample image
    print(f"\n🧪 Ready for predictions!")
    print(f"   Use: predictor.predict(corner_image)")
    print(f"   Returns: (number, confidence)")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_predictor()
