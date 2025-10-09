#!/usr/bin/env python3
"""
PaddleOCR Test Script
Tests PaddleOCR functionality to ensure it works before building the executable
"""

import sys
import os
from pathlib import Path

# Add the core directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'core'))

def test_paddleocr_import():
    """Test if PaddleOCR can be imported"""
    print("🧪 Testing PaddleOCR import...")
    try:
        from paddleocr import PaddleOCR
        print("✅ PaddleOCR import successful")
        return True
    except ImportError as e:
        print(f"❌ PaddleOCR import failed: {e}")
        return False

def test_paddleocr_engine():
    """Test the custom PaddleOCR engine"""
    print("\n🧪 Testing PaddleOCR engine initialization...")
    try:
        from core.paddle_ocr_engine import PaddleOCREngine
        
        engine = PaddleOCREngine()
        print("✅ PaddleOCR engine initialization successful")
        
        # Test with a simple image
        from PIL import Image
        import numpy as np
        
        # Create a simple test image with text
        img_array = np.ones((100, 300, 3), dtype=np.uint8) * 255
        test_image = Image.fromarray(img_array)
        
        result = engine.extract_text(test_image)
        print(f"✅ Text extraction test completed (result: '{result}')")
        return True
        
    except Exception as e:
        print(f"❌ PaddleOCR engine test failed: {e}")
        return False

def test_paddle_number_detector():
    """Test the PaddleOCR number detector"""
    print("\n🧪 Testing PaddleOCR number detector...")
    try:
        from core.paddle_number_detector import PaddleNumberDetector
        
        detector = PaddleNumberDetector()
        print("✅ PaddleOCR number detector initialization successful")
        
        # Test with a simple image
        from PIL import Image
        import numpy as np
        
        # Create a simple test image
        img_array = np.ones((400, 600, 3), dtype=np.uint8) * 255
        test_image = Image.fromarray(img_array)
        
        result = detector.detect_page_number(test_image, "", "test_page.jpg")
        print(f"✅ Number detection test completed (result: {result})")
        return True
        
    except Exception as e:
        print(f"❌ PaddleOCR number detector test failed: {e}")
        return False

def check_model_directories():
    """Check if PaddleOCR model directories exist"""
    print("\n📁 Checking PaddleOCR model directories...")
    
    home = Path.home()
    directories = [
        home / ".paddlex",
        home / ".paddleocr"
    ]
    
    found_models = False
    for directory in directories:
        if directory.exists():
            file_count = len(list(directory.rglob('*')))
            print(f"✅ Found models in {directory} ({file_count} files)")
            found_models = True
        else:
            print(f"⚠️  No models found in {directory}")
    
    if not found_models:
        print("📥 Models will be downloaded on first use")
    
    return found_models

def main():
    """Run all PaddleOCR tests"""
    print("=" * 60)
    print("PADDLEOCR COMPATIBILITY TEST")
    print("=" * 60)
    
    tests = [
        test_paddleocr_import,
        check_model_directories,
        test_paddleocr_engine,
        test_paddle_number_detector
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! PaddleOCR is ready for bundling.")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    print("=" * 60)
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
