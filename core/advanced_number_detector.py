"""
Advanced Number Detection - AI-like intelligence for page number detection
Uses the same cognitive process that humans use to identify page numbers
"""

import cv2
import numpy as np
from PIL import Image
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class NumberCandidate:
    """A potential page number with confidence score"""
    number: int
    text: str
    position: Tuple[int, int, int, int]  # x, y, w, h
    location: str  # 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'center'
    confidence: float
    reasoning: List[str]

class AdvancedNumberDetector:
    """AI-like page number detection using human cognitive strategies"""
    
    def __init__(self, logger=None):
        self.logger = logger
        
    def detect_page_number(self, image: Image.Image, ocr_text: str, filename: str) -> Optional[NumberCandidate]:
        """
        Main detection method - uses multiple AI strategies
        Mimics human cognitive process for finding page numbers
        """
        candidates = []
        
        # Strategy 1: Corner detection (HIGHEST PRIORITY - like humans look at corners first)
        corner_candidates = self._detect_corner_numbers(image, ocr_text)
        candidates.extend(corner_candidates)
        
        # Strategy 2: Header/Footer detection
        header_candidates = self._detect_header_footer_numbers(image, ocr_text)
        candidates.extend(header_candidates)
        
        # Strategy 3: Isolated number detection
        isolated_candidates = self._detect_isolated_numbers(ocr_text)
        candidates.extend(isolated_candidates)
        
        # Strategy 4: Filename fallback
        filename_candidates = self._detect_from_filename(filename)
        candidates.extend(filename_candidates)
        
        # AI Decision: Choose best candidate
        best_candidate = self._ai_choose_best_candidate(candidates)
        
        if best_candidate and self.logger:
            self.logger.debug(f"📍 Detected page {best_candidate.number} "
                            f"(confidence: {best_candidate.confidence:.0f}%, "
                            f"location: {best_candidate.location})")
        
        return best_candidate
    
    def _detect_corner_numbers(self, image: Image.Image, ocr_text: str) -> List[NumberCandidate]:
        """
        Strategy 1: Focus on corners (where humans look first)
        This is where page numbers are 90% of the time
        """
        candidates = []
        
        # Convert to numpy for OpenCV
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Define corner regions (like human eye focus areas)
        corners = {
            'top_left': (0, 0, min(200, width//4), min(150, height//10)),
            'top_right': (max(0, width-200), 0, width, min(150, height//10)),
            'bottom_left': (0, max(0, height-150), min(200, width//4), height),
            'bottom_right': (max(0, width-200), max(0, height-150), width, height)
        }
        
        for corner_name, (x1, y1, x2, y2) in corners.items():
            # Extract corner region
            corner_region = img_array[y1:y2, x1:x2]
            
            # Enhanced OCR on corner only (focused attention)
            corner_text = self._ocr_region(corner_region)
            
            # Find numbers in corner
            numbers = re.findall(r'\b(\d{1,4})\b', corner_text)
            
            for num_text in numbers:
                try:
                    num_value = int(num_text)
                    
                    # Skip unrealistic page numbers
                    if num_value < 1 or num_value > 9999:
                        continue
                    
                    # Calculate confidence based on corner location
                    confidence = 70  # Base confidence for corner detection
                    reasoning = [f"Found in {corner_name}"]
                    
                    # Boost confidence for top corners (most common)
                    if 'top' in corner_name:
                        confidence += 15
                        reasoning.append("Top corner (common location)")
                    
                    # Boost for right side (very common in books)
                    if 'right' in corner_name:
                        confidence += 10
                        reasoning.append("Right side (book standard)")
                    
                    candidates.append(NumberCandidate(
                        number=num_value,
                        text=num_text,
                        position=(x1, y1, x2-x1, y2-y1),
                        location=corner_name,
                        confidence=confidence,
                        reasoning=reasoning
                    ))
                    
                except ValueError:
                    continue
        
        return candidates
    
    def _detect_header_footer_numbers(self, image: Image.Image, ocr_text: str) -> List[NumberCandidate]:
        """
        Strategy 2: Analyze header and footer regions
        Like humans scanning the top and bottom of pages
        """
        candidates = []
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Header region (top 10% of page)
        header_height = height // 10
        header_region = img_array[0:header_height, :]
        header_text = self._ocr_region(header_region)
        
        # Footer region (bottom 10% of page)
        footer_region = img_array[-header_height:, :]
        footer_text = self._ocr_region(footer_region)
        
        # Analyze header
        header_numbers = self._extract_page_numbers_from_text(header_text, 'header')
        candidates.extend(header_numbers)
        
        # Analyze footer
        footer_numbers = self._extract_page_numbers_from_text(footer_text, 'footer')
        candidates.extend(footer_numbers)
        
        return candidates
    
    def _detect_isolated_numbers(self, text: str) -> List[NumberCandidate]:
        """
        Strategy 3: Find isolated numbers (not part of sentences)
        Like humans identifying standalone numbers
        """
        candidates = []
        
        # Pattern: Number at start of line or end of line (isolated)
        patterns = [
            (r'^\s*(\d{1,4})\s*$', 'line_isolated', 80),  # Alone on line
            (r'^\s*(\d{1,4})\s+\w', 'line_start', 60),    # Start of line
            (r'\w\s+(\d{1,4})\s*$', 'line_end', 60),      # End of line
        ]
        
        lines = text.split('\n')
        for line in lines:
            for pattern, location, base_confidence in patterns:
                matches = re.finditer(pattern, line, re.MULTILINE)
                for match in matches:
                    try:
                        num_value = int(match.group(1))
                        
                        if 1 <= num_value <= 9999:
                            candidates.append(NumberCandidate(
                                number=num_value,
                                text=match.group(1),
                                position=(0, 0, 0, 0),
                                location=location,
                                confidence=base_confidence,
                                reasoning=[f"Isolated number in {location}"]
                            ))
                    except ValueError:
                        continue
        
        return candidates
    
    def _detect_from_filename(self, filename: str) -> List[NumberCandidate]:
        """
        Strategy 4: Extract from filename as fallback
        Like humans reading the file name
        """
        candidates = []
        
        # Common filename patterns
        patterns = [
            r'_(\d{3,5})\.', # _00005.tif
            r'page[_-]?(\d+)', # page_5.jpg
            r'p(\d+)', # p005.jpg
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, filename, re.IGNORECASE)
            for match in matches:
                try:
                    num_value = int(match.group(1))
                    
                    if 1 <= num_value <= 9999:
                        candidates.append(NumberCandidate(
                            number=num_value,
                            text=match.group(1),
                            position=(0, 0, 0, 0),
                            location='filename',
                            confidence=50,  # Lower confidence for filename
                            reasoning=["Extracted from filename"]
                        ))
                except ValueError:
                    continue
        
        return candidates
    
    def _extract_page_numbers_from_text(self, text: str, region: str) -> List[NumberCandidate]:
        """Extract page numbers from text region with context awareness"""
        candidates = []
        
        # Remove chapter/section markers (NOT page numbers)
        text_cleaned = re.sub(r'Chapter\s+\d+', '', text, flags=re.IGNORECASE)
        text_cleaned = re.sub(r'Part\s+[IVXivx]+', '', text_cleaned, flags=re.IGNORECASE)
        text_cleaned = re.sub(r'Figure\s+\d+-\d+', '', text_cleaned, flags=re.IGNORECASE)
        text_cleaned = re.sub(r'Table\s+\d+-\d+', '', text_cleaned, flags=re.IGNORECASE)
        
        # Find remaining numbers (likely page numbers)
        numbers = re.findall(r'\b(\d{1,4})\b', text_cleaned)
        
        for num_text in numbers:
            try:
                num_value = int(num_text)
                
                if 1 <= num_value <= 9999:
                    confidence = 65 if region == 'header' else 55
                    
                    candidates.append(NumberCandidate(
                        number=num_value,
                        text=num_text,
                        position=(0, 0, 0, 0),
                        location=region,
                        confidence=confidence,
                        reasoning=[f"Found in {region} after filtering context"]
                    ))
            except ValueError:
                continue
        
        return candidates
    
    def _ocr_region(self, region_image: np.ndarray) -> str:
        """Perform OCR on a specific image region"""
        try:
            # Convert to PIL Image
            if len(region_image.shape) == 3:
                pil_image = Image.fromarray(region_image)
            else:
                pil_image = Image.fromarray(cv2.cvtColor(region_image, cv2.COLOR_GRAY2RGB))
            
            # Use embedded OCR (would be replaced with actual OCR in integration)
            # For now, return empty string (will be integrated with main OCR)
            return ""
            
        except Exception as e:
            return ""
    
    def _ai_choose_best_candidate(self, candidates: List[NumberCandidate]) -> Optional[NumberCandidate]:
        """
        AI Decision Making: Choose the most likely page number
        Uses confidence scoring like human intuition
        """
        if not candidates:
            return None
        
        # Sort by confidence (highest first)
        sorted_candidates = sorted(candidates, key=lambda x: x.confidence, reverse=True)
        
        # Get top candidate
        best = sorted_candidates[0]
        
        # Additional validation: Check if multiple candidates agree
        if len(sorted_candidates) > 1:
            # If top 2 candidates have same number, boost confidence
            if sorted_candidates[0].number == sorted_candidates[1].number:
                best.confidence = min(100, best.confidence + 10)
                best.reasoning.append("Multiple strategies agree")
        
        # Only return if confidence is reasonable
        if best.confidence >= 50:
            return best
        
        return None
    
    def analyze_page_sequence(self, detected_pages: List[NumberCandidate]) -> Dict:
        """
        Analyze if detected numbers form a logical sequence
        Like humans verifying: "5, 6, 7 - yes, this makes sense!"
        """
        if len(detected_pages) < 2:
            return {'valid': True, 'confidence': 50}
        
        numbers = [p.number for p in detected_pages]
        
        # Check if sequential
        is_sequential = all(numbers[i+1] == numbers[i] + 1 for i in range(len(numbers)-1))
        
        # Check if mostly increasing
        is_increasing = all(numbers[i+1] >= numbers[i] for i in range(len(numbers)-1))
        
        if is_sequential:
            return {
                'valid': True,
                'confidence': 100,
                'pattern': 'perfect_sequence',
                'reasoning': 'Numbers form perfect sequence (5, 6, 7...)'
            }
        elif is_increasing:
            # Find gaps
            gaps = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
            avg_gap = sum(gaps) / len(gaps)
            
            return {
                'valid': True,
                'confidence': 85,
                'pattern': 'increasing_with_gaps',
                'reasoning': f'Numbers increasing (average gap: {avg_gap:.1f})'
            }
        else:
            return {
                'valid': False,
                'confidence': 30,
                'pattern': 'inconsistent',
                'reasoning': 'Numbers not in logical order'
            }

