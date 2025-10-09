"""
Crop Validation System
Validates auto-crop results and flags problematic pages for manual review
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, List
import json

class CropValidator:
    """Validates auto-crop results and creates review list for problematic pages"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.problematic_pages = []
        
    def validate_crop(self, original_image: np.ndarray, cropped_image: np.ndarray, 
                     page_name: str) -> Dict:
        """
        Validate if auto-crop is acceptable or needs manual review
        
        Returns:
            {
                'is_valid': bool,
                'confidence': float (0-100),
                'issues': list of detected issues,
                'needs_review': bool,
                'crop_stats': dict with cropping statistics
            }
        """
        validation_result = {
            'is_valid': True,
            'confidence': 100.0,
            'issues': [],
            'needs_review': False,
            'crop_stats': {},
            'page_name': page_name
        }
        
        # Calculate crop statistics
        orig_h, orig_w = original_image.shape[:2]
        crop_h, crop_w = cropped_image.shape[:2]
        
        crop_ratio = (crop_w * crop_h) / (orig_w * orig_h)
        width_reduction = (orig_w - crop_w) / orig_w
        height_reduction = (orig_h - crop_h) / orig_h
        
        validation_result['crop_stats'] = {
            'original_size': (orig_w, orig_h),
            'cropped_size': (crop_w, crop_h),
            'crop_ratio': crop_ratio,
            'width_reduction': width_reduction,
            'height_reduction': height_reduction
        }
        
        # Issue 1: Excessive cropping (>40% area removed)
        if crop_ratio < 0.6:
            validation_result['issues'].append(
                f"Excessive cropping detected: {(1-crop_ratio)*100:.1f}% of image removed"
            )
            validation_result['confidence'] -= 30
            validation_result['needs_review'] = True
        
        # Issue 2: Minimal cropping (<5% removed) - may have failed
        if crop_ratio > 0.95:
            validation_result['issues'].append(
                "Minimal cropping: Auto-crop may have failed to detect borders"
            )
            validation_result['confidence'] -= 10
        
        # Issue 3: Asymmetric cropping (one side cropped much more than other)
        if abs(width_reduction - height_reduction) > 0.3:
            validation_result['issues'].append(
                f"Asymmetric cropping: width={width_reduction*100:.1f}%, height={height_reduction*100:.1f}%"
            )
            validation_result['confidence'] -= 15
            validation_result['needs_review'] = True
        
        # Issue 4: Check for black borders remaining in cropped image
        black_border_score = self._detect_black_borders(cropped_image)
        if black_border_score > 0.15:  # More than 15% black borders
            validation_result['issues'].append(
                f"Significant black borders remain: {black_border_score*100:.1f}% of edges are dark"
            )
            validation_result['confidence'] -= 25
            validation_result['needs_review'] = True
        
        # Issue 5: Check if content might be cut off
        edge_content_score = self._detect_edge_content(cropped_image)
        if edge_content_score > 0.3:  # Significant content at edges
            validation_result['issues'].append(
                "Potential content cut-off: Significant text/content detected at image edges"
            )
            validation_result['confidence'] -= 20
            validation_result['needs_review'] = True
        
        # Overall validation
        if validation_result['confidence'] < 70:
            validation_result['is_valid'] = False
            validation_result['needs_review'] = True
        
        # Add to problematic pages list if needs review
        if validation_result['needs_review']:
            self.problematic_pages.append(validation_result)
            if self.logger:
                self.logger.warning(
                    f"⚠️ {page_name}: Auto-crop needs review (confidence: {validation_result['confidence']:.1f}%)"
                )
        
        return validation_result
    
    def _detect_black_borders(self, image: np.ndarray) -> float:
        """Detect percentage of black/dark borders remaining"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        h, w = gray.shape
        
        # Define border regions (outer 5% of image)
        border_width = max(int(w * 0.05), 10)
        border_height = max(int(h * 0.05), 10)
        
        # Extract border regions
        top_border = gray[:border_height, :]
        bottom_border = gray[-border_height:, :]
        left_border = gray[:, :border_width]
        right_border = gray[:, -border_width:]
        
        # Calculate average intensity of borders
        borders = [top_border, bottom_border, left_border, right_border]
        dark_border_count = 0
        
        for border in borders:
            avg_intensity = np.mean(border)
            if avg_intensity < 50:  # Dark border (threshold: 50/255)
                dark_border_count += 1
        
        return dark_border_count / len(borders)
    
    def _detect_edge_content(self, image: np.ndarray) -> float:
        """Detect if significant content exists at image edges (potential cut-off)"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        h, w = gray.shape
        
        # Define edge regions (outer 3% of image)
        edge_width = max(int(w * 0.03), 5)
        edge_height = max(int(h * 0.03), 5)
        
        # Extract edges
        top_edge = gray[:edge_height, :]
        bottom_edge = gray[-edge_height:, :]
        left_edge = gray[:, :edge_width]
        right_edge = gray[:, -edge_width:]
        
        # Detect text/content using edge detection
        edges_list = [top_edge, bottom_edge, left_edge, right_edge]
        content_score = 0
        
        for edge_region in edges_list:
            # Apply Canny edge detection
            edges = cv2.Canny(edge_region, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            if edge_density > 0.05:  # More than 5% edges detected
                content_score += edge_density
        
        return content_score / len(edges_list)
    
    def generate_review_report(self, output_dir: Path) -> str:
        """Generate a text file listing pages that need manual review"""
        if not self.problematic_pages:
            if self.logger:
                self.logger.info("✅ All pages passed auto-crop validation")
            return None
        
        report_path = output_dir / "CROP_REVIEW_NEEDED.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("AUTO-CROP MANUAL REVIEW REQUIRED\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Total pages needing review: {len(self.problematic_pages)}\n\n")
            f.write("The following pages had auto-crop issues and may need manual cropping:\n\n")
            
            for idx, page_info in enumerate(self.problematic_pages, 1):
                f.write(f"{idx}. {page_info['page_name']}\n")
                f.write(f"   Confidence: {page_info['confidence']:.1f}%\n")
                f.write(f"   Crop Stats: {page_info['crop_stats']['original_size']} → {page_info['crop_stats']['cropped_size']}\n")
                f.write(f"   Crop Ratio: {page_info['crop_stats']['crop_ratio']*100:.1f}% retained\n")
                f.write("   Issues:\n")
                for issue in page_info['issues']:
                    f.write(f"      - {issue}\n")
                f.write("\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("RECOMMENDED ACTIONS:\n")
            f.write("=" * 70 + "\n")
            f.write("1. Review the listed pages in the output folder\n")
            f.write("2. For pages with excessive cropping: Check if content was cut off\n")
            f.write("3. For pages with black borders: Manually crop using image editor\n")
            f.write("4. For pages with asymmetric cropping: Check orientation and borders\n")
            f.write("5. Re-run the system after manual corrections if needed\n")
        
        if self.logger:
            self.logger.warning(f"⚠️ {len(self.problematic_pages)} pages need manual crop review")
            self.logger.info(f"📄 Review report saved to: {report_path}")
        
        return str(report_path)
    
    def generate_json_report(self, output_dir: Path) -> str:
        """Generate JSON report for programmatic access"""
        if not self.problematic_pages:
            return None
        
        report_path = output_dir / "crop_validation_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_problematic_pages': len(self.problematic_pages),
                'pages': self.problematic_pages
            }, f, indent=2)
        
        return str(report_path)
    
    def get_summary(self) -> Dict:
        """Get validation summary statistics"""
        if not self.problematic_pages:
            return {
                'total_problematic': 0,
                'needs_review': 0,
                'avg_confidence': 100.0
            }
        
        needs_review_count = sum(1 for p in self.problematic_pages if p['needs_review'])
        avg_confidence = np.mean([p['confidence'] for p in self.problematic_pages])
        
        return {
            'total_problematic': len(self.problematic_pages),
            'needs_review': needs_review_count,
            'avg_confidence': avg_confidence,
            'issues_breakdown': self._get_issues_breakdown()
        }
    
    def _get_issues_breakdown(self) -> Dict:
        """Get breakdown of issue types"""
        issue_counts = {
            'excessive_cropping': 0,
            'minimal_cropping': 0,
            'asymmetric_cropping': 0,
            'black_borders': 0,
            'content_cutoff': 0
        }
        
        for page in self.problematic_pages:
            for issue in page['issues']:
                if 'Excessive cropping' in issue:
                    issue_counts['excessive_cropping'] += 1
                elif 'Minimal cropping' in issue:
                    issue_counts['minimal_cropping'] += 1
                elif 'Asymmetric cropping' in issue:
                    issue_counts['asymmetric_cropping'] += 1
                elif 'black borders' in issue:
                    issue_counts['black_borders'] += 1
                elif 'cut-off' in issue:
                    issue_counts['content_cutoff'] += 1
        
        return issue_counts
