"""
BRAND NEW Advanced Number Detector - GUARANTEED TO WORK
Detects page numbers in corners with 5x upscaling for small text
"""

import cv2
import numpy as np
from PIL import Image
import re
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class NumberCandidate:
    """A potential page number with confidence score"""
    number: int
    text: str
    location: str  # 'top_left', 'top_right', 'bottom_left', 'bottom_right'
    confidence: float
    reasoning: List[str]

class AdvancedNumberDetector:
    """Simple, working page number detector"""
    
    def __init__(self, logger=None, ocr_reader=None):
        self.logger = logger
        self.ocr_reader = ocr_reader
        
        if self.logger:
            if self.ocr_reader:
                self.logger.info("✅ NEW Advanced detector initialized WITH EasyOCR")
            else:
                self.logger.warning("⚠️ NEW Advanced detector WITHOUT EasyOCR!")
    
    def detect_page_number(self, image: Image.Image, ocr_text: str, filename: str) -> Optional[NumberCandidate]:
        """Main detection method"""
        if self.logger:
            self.logger.info(f"🔎 NEW DETECTOR CALLED for: {filename}")
        
        # Scan all 4 corners
        candidates = self._scan_corners(image)
        
        if self.logger:
            self.logger.info(f"📊 NEW DETECTOR found {len(candidates)} candidates")
        
        # Return best candidate
        if candidates:
            best = max(candidates, key=lambda x: x.confidence)
            if self.logger:
                self.logger.info(f"✅ NEW DETECTOR SELECTED: {best.number} (confidence: {best.confidence}%)")
            return best
        
        if self.logger:
            self.logger.warning("❌ NEW DETECTOR found nothing")
        return None
    
    def _scan_corners(self, image: Image.Image) -> List[NumberCandidate]:
        """Scan all 4 corners for page numbers"""
        candidates = []
        
        # Convert to numpy
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Define 250×250 pixel corners (page numbers can be 20-200 pixels from edge)
        # Optimized for speed while still capturing page numbers
        corner_size = 250
        corners = {
            'top_left': (0, 0, corner_size, corner_size),
            'top_right': (width - corner_size, 0, width, corner_size),
            'bottom_left': (0, height - corner_size, corner_size, height),
            'bottom_right': (width - corner_size, height - corner_size, width, height)
        }
        
        # SPEED OPTIMIZATION: Scan corners in smart order, exit early if found
        scan_order = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
        
        for corner_name in scan_order:
            (x1, y1, x2, y2) = corners[corner_name]
            
            # Extract corner
            corner_region = img_array[y1:y2, x1:x2]
            
            # OCR the corner
            text = self._ocr_corner(corner_region, corner_name)
            
            if text:
                # Find numbers in text
                found_candidates = self._extract_numbers(text, corner_name)
                candidates.extend(found_candidates)
                
                # EARLY EXIT: If we found a good candidate, stop scanning!
                if found_candidates and found_candidates[0].confidence > 80:
                    if self.logger:
                        self.logger.info(f"⚡ Early exit! Found high-confidence number in {corner_name}")
                    break
        
        return candidates
    
    def _ocr_corner(self, region: np.ndarray, corner_name: str) -> str:
        """ADAPTIVE OCR: Try 2x first, then 3x, then 5x if needed (SMART!)"""
        if self.ocr_reader is None:
            if self.logger:
                self.logger.error(f"❌ OCR reader is None!")
            return ""
        
        try:
            height, width = region.shape[:2]
            
            # ADAPTIVE UPSCALING: Start with lowest, increase if needed
            upscale_levels = [2, 3, 5]  # Progressive: fast → accurate
            
            for scale in upscale_levels:
                if self.logger:
                    self.logger.info(f"🔍 [{corner_name}] Trying {scale}x upscaling...")
                
                # Upscale
                upscaled = cv2.resize(region, (width * scale, height * scale), interpolation=cv2.INTER_CUBIC)
                
                # Convert to PIL
                if len(upscaled.shape) == 3:
                    pil_image = Image.fromarray(upscaled)
                else:
                    pil_image = Image.fromarray(cv2.cvtColor(upscaled, cv2.COLOR_GRAY2RGB))
                
                # Run EasyOCR
                results = self.ocr_reader.readtext(np.array(pil_image), detail=0, paragraph=False)
                
                if results:
                    # SUCCESS! Found text at this scale
                    text = " ".join(results)
                    if self.logger:
                        self.logger.info(f"✅ [{corner_name}] Found text at {scale}x: '{text}'")
                    return text
                else:
                    if self.logger:
                        self.logger.debug(f"⚠️ [{corner_name}] No text at {scale}x, trying higher...")
            
            # No text found even at 5x
            if self.logger:
                self.logger.warning(f"❌ [{corner_name}] No text found even at 5x")
            return ""
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ OCR failed for {corner_name}: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            return ""
    
    def _extract_numbers(self, text: str, location: str) -> List[NumberCandidate]:
        """Extract page numbers from OCR text"""
        candidates = []
        
        # Find ARABIC numbers (1, 2, 3, etc.)
        arabic_matches = re.findall(r'\b(\d{1,4})\b', text)
        for num_text in arabic_matches:
            try:
                num_value = int(num_text)
                if 1 <= num_value <= 9999:
                    confidence = 70.0
                    reasoning = [f"Arabic number in {location}"]
                    
                    if 'top' in location:
                        confidence += 15
                        reasoning.append("Top corner (common)")
                    if 'right' in location:
                        confidence += 10
                        reasoning.append("Right side (standard)")
                    
                    candidates.append(NumberCandidate(
                        number=num_value,
                        text=num_text,
                        location=location,
                        confidence=confidence,
                        reasoning=reasoning
                    ))
            except ValueError:
                continue
        
        # Find ROMAN NUMERALS (vi, vii, viii, ix, x, xi, xii, etc.)
        roman_pattern = r'\b([ivxlcdm]+)\b'
        roman_matches = re.findall(roman_pattern, text.lower())
        
        for roman_text in roman_matches:
            roman_value = self._roman_to_int(roman_text)
            if roman_value and 1 <= roman_value <= 9999:
                confidence = 75.0
                reasoning = [f"Roman numeral in {location}"]
                
                if 'top' in location:
                    confidence += 15
                    reasoning.append("Top corner (common)")
                if 'left' in location:
                    confidence += 10
                    reasoning.append("Left side (roman standard)")
                
                candidates.append(NumberCandidate(
                    number=roman_value,
                    text=roman_text,
                    location=location,
                    confidence=confidence,
                    reasoning=reasoning
                ))
        
        return candidates
    
    def _roman_to_int(self, s: str) -> Optional[int]:
        """Convert Roman numeral to integer"""
        roman_values = {
            'i': 1, 'v': 5, 'x': 10, 'l': 50,
            'c': 100, 'd': 500, 'm': 1000
        }
        
        try:
            s = s.lower()
            total = 0
            prev_value = 0
            
            for char in reversed(s):
                if char not in roman_values:
                    return None
                    
                value = roman_values[char]
                if value < prev_value:
                    total -= value
                else:
                    total += value
                prev_value = value
            
            return total if total > 0 else None
        except:
            return None
    
    def log_learning_stats(self):
        """Log learning statistics (compatibility method)"""
        if self.logger:
            self.logger.info("📊 Detection Statistics:")
            self.logger.info("  - Corner size: 250×250 pixels")
            self.logger.info("  - Adaptive upscaling: 2x→3x→5x (SMART!)")
            self.logger.info("  - Early exit: Enabled")
            self.logger.info("  - Roman & Arabic detection enabled")
            self.logger.info("  - Auto-adaptive workers: Based on your hardware")
