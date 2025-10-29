"""
Model Manager - Handles ML model detection, loading, and lifecycle
Singleton pattern ensures model is loaded only once
"""

from pathlib import Path
from typing import Optional
import json

class ModelManager:
    """Manages ML model lifecycle"""
    
    _instance = None
    _predictor = None
    _model_available = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.model_dir = Path("ml_training/models")
        self.model_path = self.model_dir / "page_detector.h5"
        self.classes_path = self.model_dir / "class_names.json"
        self.info_path = self.model_dir / "model_info.json"
    
    def model_exists(self) -> bool:
        """Check if trained model exists"""
        return (
            self.model_path.exists() and
            self.classes_path.exists()
        )
    
    def get_model_info(self) -> Optional[dict]:
        """Get model information without loading it"""
        if not self.info_path.exists():
            return None
        
        try:
            with open(self.info_path, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def load_model(self, force_reload: bool = False):
        """
        Load ML model if available
        
        Args:
            force_reload: Force reload even if already loaded
        
        Returns:
            True if model loaded, False otherwise
        """
        # Already loaded?
        if self._predictor is not None and not force_reload:
            return True
        
        # Model exists?
        if not self.model_exists():
            self._model_available = False
            return False
        
        # Try to load
        try:
            from ml_training.model_predictor import PageNumberPredictor
            
            self._predictor = PageNumberPredictor(str(self.model_dir))
            success = self._predictor.load_model()
            
            self._model_available = success
            return success
        
        except Exception as e:
            print(f"Error loading ML model: {e}")
            self._model_available = False
            return False
    
    def get_predictor(self):
        """Get the loaded predictor (or None if not available)"""
        if not self._model_available:
            self.load_model()
        
        return self._predictor if self._model_available else None
    
    def is_model_available(self) -> bool:
        """Check if model is available and loaded"""
        return self._model_available
    
    def unload_model(self):
        """Unload model from memory"""
        self._predictor = None
        self._model_available = False
    
    def get_status(self) -> dict:
        """Get current status"""
        return {
            'model_exists': self.model_exists(),
            'model_loaded': self._model_available,
            'model_path': str(self.model_path) if self.model_exists() else None,
            'model_info': self.get_model_info()
        }


# Global instance
_manager = ModelManager()

def get_model_manager() -> ModelManager:
    """Get singleton model manager instance"""
    return _manager


def model_available() -> bool:
    """Quick check if ML model is available"""
    return _manager.model_exists()


def get_predictor():
    """Quick access to predictor"""
    return _manager.get_predictor()


def test_manager():
    """Test the model manager"""
    print("=" * 70)
    print("MODEL MANAGER STATUS")
    print("=" * 70)
    
    manager = get_model_manager()
    status = manager.get_status()
    
    print(f"\n📊 Status:")
    print(f"   Model exists: {status['model_exists']}")
    print(f"   Model loaded: {status['model_loaded']}")
    
    if status['model_path']:
        print(f"   Model path: {status['model_path']}")
    
    if status['model_info']:
        print(f"\n📈 Model Info:")
        for key, value in status['model_info'].items():
            print(f"   {key}: {value}")
    
    if not status['model_exists']:
        print(f"\n⚠️  No trained model found!")
        print(f"   To create one:")
        print(f"   1. Label training data: python ml_training/interactive_labeler.py")
        print(f"   2. Train model: python ml_training/quick_trainer.py")
    
    else:
        # Try loading
        print(f"\n🔄 Testing model load...")
        success = manager.load_model()
        
        if success:
            print(f"   ✅ Model loaded successfully!")
            predictor = manager.get_predictor()
            print(f"   Classes: {len(predictor.class_names)}")
        else:
            print(f"   ❌ Failed to load model")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_manager()
