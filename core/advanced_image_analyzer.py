"""
Advanced Image Analysis System for Better Page Number Detection
Specifically addresses text orientation and careful analysis issues
"""

import cv2
import numpy as np
from PIL import Image
import easyocr
import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import math
from core.preprocessor import Preprocessor

@dataclass
class PageAnalysisResult:
    """Comprehensive analysis result for a page"""
    page_numbers: List[str]
    confidence_scores: List[float]
    text_orientations: List[str]  # 'horizontal', 'vertical', 'rotated'
    text_positions: List[Tuple[int, int, int, int]]
    best_page_number: Optional[str] = None
    overall_confidence: float = 0.0
    analysis_issues: List[str] = None

class AdvancedImageAnalyzer:
    """Advanced analyzer specifically for orientation and careful analysis issues - ADAPTIVE"""
    
    def __init__(self, logger, ai_learning=None):
        self.logger = logger
        
        # AUTO-DETECT GPU: Use GPU if available, CPU otherwise
        try:
            import torch
            gpu_available = torch.cuda.is_available()
            if self.logger:
                if gpu_available:
                    self.logger.info("🚀 GPU DETECTED! Using GPU acceleration (10x faster!)")
                else:
                    self.logger.info("💻 No GPU detected, using CPU")
        except:
            gpu_available = False
            if self.logger:
                self.logger.info("💻 Using CPU (no torch/GPU)")
        
        self.ocr_reader = easyocr.Reader(['en'], gpu=gpu_available)
        # Use existing preprocessor for image enhancement (avoid duplication)
        self.preprocessor = Preprocessor(logger)
        # ADAPTIVE: Use AI learning for intelligent scanning
        self.ai_learning = ai_learning
        
        # Enhanced patterns for different number types
        self.number_patterns = {
            'arabic': re.compile(r'\b\d{1,4}\b'),
            'roman_lower': re.compile(r'\b[ivxlcdm]{1,10}\b'),
            'roman_upper': re.compile(r'\b[IVXLCDM]{1,10}\b'),
            'page_prefix': re.compile(r'(?:page|p\.?)\s*(\d+)', re.IGNORECASE),
            'isolated_number': re.compile(r'^\s*(\d+)\s*$')
        }
    
    def analyze_image_comprehensively(self, image: Image.Image, 
                                    page_filename: str) -> PageAnalysisResult:
        """
        Perform comprehensive analysis addressing the specific issues:
        1. Text orientation problems (horizontal vs vertical)
        2. Insufficient careful analysis
        3. Layout complexity
        """
        self.logger.info(f"🔍 Analyzing {page_filename} with enhanced precision...")
        
        result = PageAnalysisResult(
            page_numbers=[],
            confidence_scores=[],
            text_orientations=[],
            text_positions=[],
            analysis_issues=[]
        )
        
        try:
            # Convert to OpenCV format for advanced processing
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            all_candidates = []
            
            # ═══════════════════════════════════════════════════════════
            # SUB-STAGE 5.1: REGION SCANNING (Fastest)
            # ═══════════════════════════════════════════════════════════
            self.logger.info("  🔎 Sub-Stage 5.1: Scanning key regions...")
            regions_data = self._analyze_specific_regions(cv_image)
            all_candidates.extend(regions_data)
            
            # Check if we found good candidates - STOP if yes!
            if regions_data and max([c['confidence'] for c in regions_data], default=0) > 0.8:
                self.logger.info(f"  ✅ Sub-Stage 5.1 Complete: Found page number (confidence > 80%) - skipping other steps")
            else:
                # ═══════════════════════════════════════════════════════════
                # SUB-STAGE 5.2: ORIENTATION ANALYSIS (If needed)
                # ═══════════════════════════════════════════════════════════
                self.logger.info("  📐 Sub-Stage 5.2: Checking orientations...")
                orientations_data = self._analyze_multiple_orientations(cv_image)
                all_candidates.extend(orientations_data)
                
                # Check again - STOP if found!
                if orientations_data and max([c['confidence'] for c in orientations_data], default=0) > 0.75:
                    self.logger.info(f"  ✅ Sub-Stage 5.2 Complete: Found page number (confidence > 75%) - skipping advanced detection")
                else:
                    # ═══════════════════════════════════════════════════════════
                    # SUB-STAGE 5.3: ADVANCED DETECTION (Last resort)
                    # ═══════════════════════════════════════════════════════════
                    self.logger.info("  📝 Sub-Stage 5.3: Advanced text detection...")
                    text_data = self._advanced_text_detection(cv_image)
                    all_candidates.extend(text_data)
                    self.logger.info(f"  ✅ Sub-Stage 5.3 Complete: Advanced detection finished")
            
            if all_candidates:
                # Filter and rank candidates
                best_candidates = self._rank_and_filter_candidates(all_candidates)
                
                # Populate result
                for candidate in best_candidates:
                    result.page_numbers.append(candidate['text'])
                    result.confidence_scores.append(candidate['confidence'])
                    result.text_orientations.append(candidate['orientation'])
                    result.text_positions.append(candidate['position'])
                
                # Determine best page number
                if best_candidates:
                    result.best_page_number = best_candidates[0]['text']
                    result.overall_confidence = best_candidates[0]['confidence']
                
                self.logger.info(f"  ✅ Found {len(best_candidates)} high-quality candidates")
                self.logger.info(f"  🎯 Best page number: {result.best_page_number} "
                               f"(confidence: {result.overall_confidence:.1%})")
            else:
                result.analysis_issues.append("No page numbers detected in any orientation")
                self.logger.warning(f"  ⚠️ No page numbers found in {page_filename}")
            
            return result
        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed for {page_filename}: {e}")
            result.analysis_issues.append(f"Analysis error: {str(e)}")
            return result
    
    def _analyze_multiple_orientations(self, image: np.ndarray) -> List[Dict]:
        """Analyze image at all possible orientations to catch rotated text"""
        candidates = []
        
        # memory FIX: Resize image before orientation analysis
        max_size = 1200  # Limit image size to prevent memory issues
        h, w = image.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Define all rotation angles to test
        rotations = [
            ('original', image, 0),
            ('rotated_90', cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE), 90),
            ('rotated_180', cv2.rotate(image, cv2.ROTATE_180), 180),
            ('rotated_270', cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE), 270)
        ]
        
        for orientation_name, rotated_image, angle in rotations:
            try:
                # Convert to PIL for OCR
                pil_image = Image.fromarray(cv2.cvtColor(rotated_image, cv2.COLOR_BGR2RGB))
                
                # Run OCR with memory-safe settings
                results = self.ocr_reader.readtext(np.array(pil_image), 
                                                 detail=1, 
                                                 paragraph=False,
                                                 width_ths=0.7,
                                                 height_ths=0.7,
                                                 batch_size=1)  # Process one at a time
                
                for (bbox, text, confidence) in results:
                    if confidence > 0.6:  # Lower threshold for rotated text
                        page_numbers = self._extract_page_numbers_from_text(text)
                        
                        for page_num in page_numbers:
                            candidates.append({
                                'text': page_num,
                                'confidence': confidence,
                                'orientation': f"{orientation_name}_{angle}deg",
                                'position': bbox[0] if bbox else (0, 0, 0, 0),
                                'source': 'orientation_analysis',
                                'raw_text': text
                            })
                            
            except Exception as e:
                self.logger.debug(f"Orientation analysis failed for {orientation_name}: {e}")
                continue
        
        return candidates
    
    def _analyze_specific_regions(self, image: np.ndarray) -> List[Dict]:
        """ADAPTIVE: Analyze regions based on learned patterns"""
        candidates = []
        h, w = image.shape[:2]
        
        # Define comprehensive regions for page numbers - ALL 10 POSITIONS
        all_regions = {
            # TOP POSITIONS
            'top_left': (0, 0, int(w*0.25), int(h*0.15)),
            'top_center': (int(w*0.35), 0, int(w*0.65), int(h*0.15)),
            'top_right': (int(w*0.75), 0, w, int(h*0.15)),
            
            # SIDE CENTER POSITIONS (ADAPTIVE ENHANCEMENT)
            'left_center': (0, int(h*0.4), int(w*0.15), int(h*0.6)),
            'right_center': (int(w*0.85), int(h*0.4), w, int(h*0.6)),
            
            # BOTTOM POSITIONS
            'bottom_left': (0, int(h*0.85), int(w*0.25), h),
            'bottom_center': (int(w*0.35), int(h*0.85), int(w*0.65), h),
            'bottom_right': (int(w*0.75), int(h*0.85), w, h),
            
            # EXTENDED MARGIN REGIONS (for comprehensive coverage)
            'left_margin_full': (0, int(h*0.2), int(w*0.12), int(h*0.8)),
            'right_margin_full': (int(w*0.88), int(h*0.2), w, int(h*0.8))
        }
        
        # ADAPTIVE: Get scanning priority from AI learning
        if self.ai_learning:
            scan_priority = self.ai_learning.get_adaptive_scan_priority()
            self.logger.debug(f"🤖 Using adaptive scan priority: {scan_priority[:3]}...")
        else:
            # Default priority
            scan_priority = list(all_regions.keys())
        
        # Scan regions in learned priority order
        for region_name in scan_priority:
            if region_name not in all_regions:
                continue
            
            x1, y1, x2, y2 = all_regions[region_name]
            try:
                # Extract region
                region = image[y1:y2, x1:x2]
                
                if region.size > 0:
                    # MEMORY FIX: Resize large regions to prevent memory issues
                    max_dimension = 800  # Limit region size
                    h_region, w_region = region.shape[:2]
                    if max(h_region, w_region) > max_dimension:
                        scale = max_dimension / max(h_region, w_region)
                        new_w = int(w_region * scale)
                        new_h = int(h_region * scale)
                        region = cv2.resize(region, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    
                    # Enhance region for better OCR
                    enhanced_region = self._enhance_region_for_ocr(region)
                    
                    # Convert to PIL
                    pil_region = Image.fromarray(cv2.cvtColor(enhanced_region, cv2.COLOR_BGR2RGB))
                    
                    # OCR with high precision (memory-safe)
                    results = self.ocr_reader.readtext(np.array(pil_region),
                                                     detail=1,
                                                     paragraph=False,
                                                     batch_size=1)  # Process one at a time
                    
                    for (bbox, text, confidence) in results:
                        if confidence > 0.7:  # Higher threshold for regions
                            page_numbers = self._extract_page_numbers_from_text(text)
                            
                            for page_num in page_numbers:
                                candidates.append({
                                    'text': page_num,
                                    'confidence': confidence * 1.1,  # Boost region confidence
                                    'orientation': f"region_{region_name}",
                                    'position': (x1 + bbox[0][0], y1 + bbox[0][1], 
                                               bbox[2][0] - bbox[0][0], bbox[2][1] - bbox[0][1]),
                                    'source': 'region_analysis',
                                    'raw_text': text
                                })
                                
            except Exception as e:
                self.logger.debug(f"Region analysis failed for {region_name}: {e}")
                continue
        
        return candidates
    
    def _advanced_text_detection(self, image: np.ndarray) -> List[Dict]:
        """Advanced text detection using multiple preprocessing techniques"""
        candidates = []
        
        # MEMORY FIX: Resize image before advanced processing
        max_size = 1200
        h, w = image.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Multiple preprocessing approaches for difficult text
        preprocessing_methods = [
            ('enhanced_contrast', self._enhance_contrast),
            ('denoised', self._denoise_image),
            ('sharpened', self._sharpen_image),
            ('morphological', self._morphological_operations),
            ('adaptive_threshold', self._adaptive_threshold)
        ]
        
        for method_name, preprocess_func in preprocessing_methods:
            try:
                # Apply preprocessing
                processed_image = preprocess_func(image)
                
                # Convert to PIL
                if len(processed_image.shape) == 2:  # Grayscale
                    pil_image = Image.fromarray(processed_image)
                else:  # Color
                    pil_image = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
                
                # OCR with memory-safe settings
                results = self.ocr_reader.readtext(np.array(pil_image), detail=1, batch_size=1)
                
                for (bbox, text, confidence) in results:
                    if confidence > 0.5:  # Lower threshold for processed images
                        page_numbers = self._extract_page_numbers_from_text(text)
                        
                        for page_num in page_numbers:
                            candidates.append({
                                'text': page_num,
                                'confidence': confidence,
                                'orientation': f"processed_{method_name}",
                                'position': bbox[0] if bbox else (0, 0, 0, 0),
                                'source': 'advanced_text_detection',
                                'raw_text': text
                            })
                            
            except Exception as e:
                self.logger.debug(f"Advanced text detection failed for {method_name}: {e}")
                continue
        
        return candidates
    
    def _extract_page_numbers_from_text(self, text: str) -> List[str]:
        """Extract potential page numbers from OCR text using all patterns"""
        page_numbers = []
        clean_text = text.strip()
        
        # Check each pattern
        for pattern_name, pattern in self.number_patterns.items():
            matches = pattern.findall(clean_text)
            
            for match in matches:
                # Validate the match
                if self._is_valid_page_number(match, pattern_name):
                    page_numbers.append(match)
        
        return list(set(page_numbers))  # Remove duplicates
    
    def _is_valid_page_number(self, text: str, pattern_type: str) -> bool:
        """Validate if detected text is likely a page number"""
        try:
            if pattern_type == 'arabic':
                num = int(text)
                return 1 <= num <= 9999  # Reasonable page number range
            elif 'roman' in pattern_type:
                return len(text) <= 10  # Reasonable roman numeral length
            elif pattern_type == 'page_prefix':
                return True  # Already validated by pattern
            elif pattern_type == 'isolated_number':
                num = int(text)
                return 1 <= num <= 9999
            return True
        except:
            return False
    
    def _rank_and_filter_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Rank candidates by quality and filter duplicates"""
        if not candidates:
            return []
        
        # Score each candidate
        scored_candidates = []
        for candidate in candidates:
            score = self._calculate_candidate_score(candidate)
            scored_candidates.append((score, candidate))
        
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Filter duplicates and return top candidates
        seen_numbers = set()
        filtered_candidates = []
        
        for score, candidate in scored_candidates:
            if candidate['text'] not in seen_numbers:
                seen_numbers.add(candidate['text'])
                filtered_candidates.append(candidate)
                
                # Limit to top 5 candidates
                if len(filtered_candidates) >= 5:
                    break
        
        return filtered_candidates
    
    def _calculate_candidate_score(self, candidate: Dict) -> float:
        """Calculate comprehensive quality score for page number candidate"""
        score = 0.0
        
        # Base confidence score
        score += candidate['confidence'] * 50
        
        # Bonus for specific sources
        if candidate['source'] == 'region_analysis':
            score += 20  # Regions are good places for page numbers
        elif candidate['source'] == 'orientation_analysis':
            score += 15  # Multi-orientation analysis is thorough
        
        # Bonus for reasonable page numbers
        try:
            if candidate['text'].isdigit():
                num = int(candidate['text'])
                if 1 <= num <= 500:
                    score += 15
                elif 501 <= num <= 1000:
                    score += 10
        except:
            pass
        
        # Penalty for very long text (less likely to be page number)
        if len(candidate['text']) > 4:
            score -= 10
        
        # Bonus for isolated numbers
        if len(candidate['raw_text'].strip()) <= 5:
            score += 10
        
        return score
    
    # Image enhancement methods (using existing preprocessor to avoid duplication)
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance image contrast using existing preprocessor"""
        return self.preprocessor._enhance_contrast(image)
    
    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """Remove noise from image using existing preprocessor"""
        return self.preprocessor._denoise_image(image)
    
    def _sharpen_image(self, image: np.ndarray) -> np.ndarray:
        """Sharpen image for better text recognition"""
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        return cv2.filter2D(image, -1, kernel)
    
    def _morphological_operations(self, image: np.ndarray) -> np.ndarray:
        """Apply morphological operations to clean up text"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        cleaned = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        return cleaned
    
    def _adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """Apply adaptive thresholding for better text contrast"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    def _enhance_region_for_ocr(self, region: np.ndarray) -> np.ndarray:
        """Enhance specific region for better OCR accuracy"""
        # Apply multiple enhancements using existing methods
        enhanced = self._enhance_contrast(region)
        enhanced = self._sharpen_image(enhanced)
        return enhanced

def create_advanced_analyzer(logger, ai_learning=None):
    """Factory function to create advanced analyzer with AI learning support"""
    return AdvancedImageAnalyzer(logger, ai_learning)
