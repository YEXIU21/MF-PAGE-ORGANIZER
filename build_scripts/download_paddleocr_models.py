#!/usr/bin/env python3
"""
PaddleOCR Model Pre-downloader
Downloads and prepares PaddleOCR models for bundling in standalone executable
"""

import os
import sys
from pathlib import Path

def download_paddleocr_models():
    """Download PaddleOCR models to ensure they're available for bundling"""
    print("🔧 Pre-downloading PaddleOCR models for standalone executable...")
    
    try:
        from paddleocr import PaddleOCR
        
        # Initialize PaddleOCR - this will download models if not present
        print("📥 Initializing PaddleOCR (will download models if needed)...")
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        
        # Test with a simple dummy image to trigger model initialization
        import numpy as np
        from PIL import Image
        
        # Test with dummy image to ensure models are cached
        dummy_img = np.ones((100, 300, 3), dtype=np.uint8) * 255
        test_image = Image.fromarray(dummy_img)
        result = ocr.ocr(np.array(test_image))
        
        print("🧪 Testing PaddleOCR initialization...")
        
        print("✅ PaddleOCR models successfully downloaded and cached!")
        
        # Show model locations
        home_paddlex = Path.home() / '.paddlex'
        home_paddleocr = Path.home() / '.paddleocr'
        
        if home_paddlex.exists():
            print(f"📁 Models found in: {home_paddlex}")
            model_count = len(list(home_paddlex.rglob('*')))
            print(f"   {model_count} files cached")
        
        if home_paddleocr.exists():
            print(f"📁 Models found in: {home_paddleocr}")
            model_count = len(list(home_paddleocr.rglob('*')))
            print(f"   {model_count} files cached")
            
        return True
        
    except ImportError:
        print("❌ PaddleOCR not installed. Install with: pip install paddleocr")
        return False
    except Exception as e:
        print(f"❌ Failed to download PaddleOCR models: {e}")
        return False

if __name__ == '__main__':
    success = download_paddleocr_models()
    sys.exit(0 if success else 1)
