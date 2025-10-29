"""
Enable Training Data Collection Mode
Patches the OCR engine to automatically collect training data
Run this before processing books to build your training dataset!
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_training.data_collector import TrainingDataCollector
import cv2
import numpy as np


class DataCollectionMode:
    """Singleton to enable/disable data collection globally"""
    _instance = None
    _enabled = False
    _collector = None
    
    @classmethod
    def enable(cls, output_dir: str = "ml_training/training_data"):
        """Enable data collection mode"""
        if cls._collector is None:
            cls._collector = TrainingDataCollector(output_dir)
            cls._enabled = True
            print("✅ Training data collection ENABLED")
            print(f"📁 Data will be saved to: {output_dir}")
        return cls._collector
    
    @classmethod
    def disable(cls):
        """Disable data collection and save results"""
        if cls._collector is not None:
            cls._collector.save_dataset_info()
            report = cls._collector.generate_report()
            print("\n" + report)
            
            is_valid, issues = cls._collector.verify_dataset()
            if is_valid:
                print("\n✅ Dataset is valid and ready for training!")
            else:
                print("\n⚠️ Dataset has issues:")
                for issue in issues:
                    print(f"  {issue}")
            
            cls._enabled = False
            print("\n✅ Training data collection DISABLED")
        return cls._collector
    
    @classmethod
    def is_enabled(cls):
        """Check if collection is enabled"""
        return cls._enabled
    
    @classmethod
    def get_collector(cls):
        """Get the collector instance"""
        return cls._collector


def patch_paddle_detector():
    """
    Monkey patch the PaddleNumberDetector to collect training data
    This adds data collection WITHOUT modifying the original code
    """
    from core.paddle_number_detector import PaddleNumberDetector
    
    # Store original method
    original_ocr_corner = PaddleNumberDetector._ocr_corner
    
    def patched_ocr_corner(self, region: np.ndarray, corner_name: str, offset_x: int, offset_y: int):
        """Patched version that collects training data"""
        # Call original method
        candidates = original_ocr_corner(self, region, corner_name, offset_x, offset_y)
        
        # Collect training data if enabled
        if DataCollectionMode.is_enabled():
            collector = DataCollectionMode.get_collector()
            
            if collector and candidates:
                # Get best candidate from this corner
                best_candidate = max(candidates, key=lambda x: x.confidence)
                
                # Collect the corner image + label
                collector.collect_from_page(
                    page_image_path=getattr(self, '_current_page_path', 'unknown'),
                    detected_number=best_candidate.text,
                    corner_name=corner_name,
                    corner_region=region.copy(),
                    confidence=best_candidate.confidence,
                    book_name=getattr(self, '_current_book_name', 'unknown')
                )
            elif collector:
                # No number found in this corner (negative example)
                collector.collect_from_page(
                    page_image_path=getattr(self, '_current_page_path', 'unknown'),
                    detected_number=None,
                    corner_name=corner_name,
                    corner_region=region.copy(),
                    confidence=0.0,
                    book_name=getattr(self, '_current_book_name', 'unknown')
                )
        
        return candidates
    
    # Replace method
    PaddleNumberDetector._ocr_corner = patched_ocr_corner
    print("✅ PaddleNumberDetector patched for data collection")


def patch_ocr_engine():
    """Patch OCR engine to track current page being processed"""
    from core.ocr_engine import OCREngine
    
    # Store original method
    original_process_page = OCREngine.process_page
    
    def patched_process_page(self, page_info, total_pages: int = 0):
        """Patched version that tracks current page"""
        # Set current page info for data collector
        if hasattr(self, 'number_detector'):
            self.number_detector._current_page_path = page_info.path
            self.number_detector._current_book_name = Path(page_info.path).parent.name
        
        # Call original method
        result = original_process_page(self, page_info, total_pages)
        
        return result
    
    # Replace method
    OCREngine.process_page = patched_process_page
    print("✅ OCREngine patched for page tracking")


def start_collection(output_dir: str = "ml_training/training_data"):
    """
    Start collecting training data
    Call this BEFORE running your book processing
    """
    print("=" * 70)
    print("TRAINING DATA COLLECTION MODE")
    print("=" * 70)
    
    # Enable collection
    collector = DataCollectionMode.enable(output_dir)
    
    # Patch components
    patch_paddle_detector()
    patch_ocr_engine()
    
    print("\n🚀 Ready to collect training data!")
    print("   Process books normally - data will be collected automatically")
    print("   After processing, call stop_collection() to save results")
    print("=" * 70)
    
    return collector


def stop_collection():
    """
    Stop collecting training data and save results
    Call this AFTER processing books
    """
    print("\n" + "=" * 70)
    print("STOPPING DATA COLLECTION")
    print("=" * 70)
    
    collector = DataCollectionMode.disable()
    
    return collector


# Simple usage example
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                  TRAINING DATA COLLECTION MODE                       ║
╚══════════════════════════════════════════════════════════════════════╝

This script enables automatic training data collection while you process
books with the normal page automation system.

USAGE:
------

1. Start collection:
   >>> from ml_training.enable_data_collection import start_collection, stop_collection
   >>> start_collection()

2. Run your normal book processing:
   >>> python main.py --input "path/to/books" --output "path/to/output"

3. Stop collection and save results:
   >>> stop_collection()

4. View collected data:
   >>> ls ml_training/training_data/corners/

That's it! You'll have thousands of labeled corner images ready for training.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUICK TEST:
-----------
    """)
    
    # Demo
    print("Running quick test...")
    collector = start_collection("ml_training/test_data")
    
    # Simulate some data collection
    print("\n📝 Simulating data collection...")
    test_image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    
    for i in range(5):
        collector.collect_from_page(
            page_image_path=f"test/page_{i+1}.jpg",
            detected_number=str(i+1),
            corner_name="bottom_right",
            corner_region=test_image,
            confidence=95.0,
            book_name="test_book"
        )
    
    # Stop and show results
    stop_collection()
    
    print("\n✅ Test complete! Check ml_training/test_data/ for results")
