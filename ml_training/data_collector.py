"""
Data Collector for Page Number Detection Model
Automatically extracts corner images and labels from OCR results
Creates training dataset for custom ML model
"""

import os
import cv2
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np


class TrainingDataCollector:
    """Collects and organizes training data from OCR processing"""
    
    def __init__(self, output_dir: str = "ml_training/training_data"):
        self.output_dir = Path(output_dir)
        self.dataset_info = {
            'created': datetime.now().isoformat(),
            'total_images': 0,
            'classes': {},
            'metadata': []
        }
        
        # Create directory structure
        self.setup_directories()
    
    def setup_directories(self):
        """Create organized directory structure"""
        print(f"📁 Setting up training data directories...")
        
        # Main directories
        self.corners_dir = self.output_dir / "corners"
        self.metadata_dir = self.output_dir / "metadata"
        
        # Create directories
        self.corners_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Class directories (will be created as needed)
        print(f"✅ Directories ready at: {self.output_dir}")
    
    def collect_from_page(self, 
                          page_image_path: str, 
                          detected_number: str or None,
                          corner_name: str,
                          corner_region: np.ndarray,
                          confidence: float,
                          book_name: str = "unknown"):
        """
        Collect single training sample
        
        Args:
            page_image_path: Original page image path
            detected_number: The number found ("1", "i", None for blank)
            corner_name: Which corner this is from
            corner_region: The actual corner image (numpy array)
            confidence: Detection confidence
            book_name: Name of source book
        """
        # Determine class label
        if detected_number is None or detected_number.strip() == "":
            class_label = "none"
        else:
            # Clean label (remove spaces, special chars)
            class_label = detected_number.strip().lower()
        
        # Create class directory if doesn't exist
        class_dir = self.corners_dir / class_label
        class_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        image_filename = f"{class_label}_{corner_name}_{timestamp}.jpg"
        image_path = class_dir / image_filename
        
        # Resize to standard size (200x200)
        standardized = cv2.resize(corner_region, (200, 200), interpolation=cv2.INTER_AREA)
        
        # Save image
        cv2.imwrite(str(image_path), standardized, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        # Save metadata
        metadata = {
            'image_path': str(image_path.relative_to(self.output_dir)),
            'class_label': class_label,
            'corner_name': corner_name,
            'confidence': confidence,
            'source_page': page_image_path,
            'book_name': book_name,
            'timestamp': timestamp,
            'image_size': (200, 200)
        }
        
        self.dataset_info['metadata'].append(metadata)
        
        # Update class count
        if class_label not in self.dataset_info['classes']:
            self.dataset_info['classes'][class_label] = 0
        self.dataset_info['classes'][class_label] += 1
        self.dataset_info['total_images'] += 1
    
    def collect_from_ocr_result(self,
                                 page_image_path: str,
                                 detected_number: str or None,
                                 all_corner_regions: Dict[str, np.ndarray],
                                 best_corner: str,
                                 confidence: float,
                                 book_name: str = "unknown"):
        """
        Collect training data from complete OCR result
        
        Args:
            page_image_path: Path to original page image
            detected_number: Best detected number
            all_corner_regions: Dict of {corner_name: corner_image}
            best_corner: Name of corner where number was found
            confidence: Detection confidence
            book_name: Source book name
        """
        # Collect POSITIVE example (where number was found)
        if best_corner in all_corner_regions and detected_number:
            self.collect_from_page(
                page_image_path=page_image_path,
                detected_number=detected_number,
                corner_name=best_corner,
                corner_region=all_corner_regions[best_corner],
                confidence=confidence,
                book_name=book_name
            )
        
        # Collect NEGATIVE examples (where number was NOT found)
        # This helps model learn what "no number" looks like
        for corner_name, corner_image in all_corner_regions.items():
            if corner_name != best_corner:
                # These corners don't have page numbers
                self.collect_from_page(
                    page_image_path=page_image_path,
                    detected_number=None,  # No number in this corner
                    corner_name=corner_name,
                    corner_region=corner_image,
                    confidence=0.0,
                    book_name=book_name
                )
    
    def save_dataset_info(self):
        """Save dataset metadata to JSON"""
        info_path = self.metadata_dir / "dataset_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset_info, f, indent=2)
        print(f"💾 Dataset info saved to: {info_path}")
    
    def generate_report(self) -> str:
        """Generate human-readable collection report"""
        report = []
        report.append("=" * 70)
        report.append("TRAINING DATA COLLECTION REPORT")
        report.append("=" * 70)
        report.append(f"📅 Created: {self.dataset_info['created']}")
        report.append(f"📊 Total Images: {self.dataset_info['total_images']}")
        report.append(f"🏷️ Total Classes: {len(self.dataset_info['classes'])}")
        report.append("")
        report.append("CLASS DISTRIBUTION:")
        report.append("-" * 70)
        
        # Sort classes by count
        sorted_classes = sorted(
            self.dataset_info['classes'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for class_label, count in sorted_classes[:20]:  # Top 20
            bar = "█" * (count // 10)
            report.append(f"  {class_label:>10s} : {count:>4d} images {bar}")
        
        if len(sorted_classes) > 20:
            report.append(f"  ... and {len(sorted_classes) - 20} more classes")
        
        report.append("=" * 70)
        
        report_text = "\n".join(report)
        
        # Save to file
        report_path = self.metadata_dir / "collection_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        return report_text
    
    def verify_dataset(self) -> Tuple[bool, List[str]]:
        """Verify dataset quality and completeness"""
        issues = []
        
        # Check minimum samples per class
        min_samples = 10
        for class_label, count in self.dataset_info['classes'].items():
            if count < min_samples and class_label != "none":
                issues.append(f"⚠️ Class '{class_label}' has only {count} samples (need {min_samples}+)")
        
        # Check for balanced classes
        if self.dataset_info['classes']:
            counts = list(self.dataset_info['classes'].values())
            max_count = max(counts)
            min_count = min(counts)
            if max_count > min_count * 10:
                issues.append(f"⚠️ Class imbalance: max={max_count}, min={min_count}")
        
        # Check total images
        if self.dataset_info['total_images'] < 500:
            issues.append(f"⚠️ Only {self.dataset_info['total_images']} images (recommend 1000+)")
        
        is_valid = len(issues) == 0
        return is_valid, issues


def collect_data_from_book(book_path: str, 
                            ocr_results: List[Dict],
                            collector: TrainingDataCollector,
                            book_name: str = None):
    """
    Helper function to collect data from entire book processing
    
    Args:
        book_path: Path to book directory
        ocr_results: List of OCR result dictionaries
        collector: TrainingDataCollector instance
        book_name: Optional book identifier
    """
    if book_name is None:
        book_name = Path(book_path).name
    
    print(f"📖 Collecting training data from: {book_name}")
    
    for result in ocr_results:
        # Extract info from result
        # (This will be called from OCR engine during processing)
        pass


if __name__ == "__main__":
    # Test the collector
    print("Training Data Collector - Test Mode")
    print("=" * 70)
    
    collector = TrainingDataCollector()
    
    # Create dummy test data
    print("\n📝 Creating test samples...")
    test_corner = np.random.randint(0, 255, (200, 200), dtype=np.uint8)
    
    for i in range(1, 11):
        collector.collect_from_page(
            page_image_path=f"test/page_{i}.jpg",
            detected_number=str(i),
            corner_name="bottom_right",
            corner_region=test_corner,
            confidence=0.95,
            book_name="test_book"
        )
    
    # Save and report
    collector.save_dataset_info()
    print("\n" + collector.generate_report())
    
    # Verify
    is_valid, issues = collector.verify_dataset()
    if is_valid:
        print("\n✅ Dataset is valid and ready for training!")
    else:
        print("\n⚠️ Dataset has issues:")
        for issue in issues:
            print(f"  {issue}")
