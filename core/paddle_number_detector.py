"""
PaddleOCR-Based Page Number Detector
Ultra-fast, accurate corner-focused detection with PaddleOCR
"""

# ★ CRITICAL: Set environment variables BEFORE any imports!
# This prevents oneDNN parallel processing crashes
import os
os.environ['PADDLE_USE_ONEDNN'] = '0'  # Disable Intel oneDNN (fixes parallel crash)
os.environ['OMP_NUM_THREADS'] = '1'     # Single-threaded OpenMP
os.environ['PADDLE_ENABLE_INFERENCE_PROFILER'] = '0'  # Disable profiler

import re
import numpy as np
from PIL import Image
from typing import List, Optional, Tuple
from dataclasses import dataclass
import threading
from .ai_pattern_learning import AIPatternLearning

@dataclass
class NumberCandidate:
    """A potential page number with confidence score"""
    number: int
    text: str
    location: str  # 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'filename'
    confidence: float
    reasoning: List[str]
    bbox: Optional[Tuple[int, int, int, int]] = None

class PaddleNumberDetector:
    """Advanced page number detector using PaddleOCR with AI learning"""
    
    # Class-level singleton to prevent reinitialization
    _ocr_instance = None
    _initialized = False
    _lock = threading.Lock()  # Thread-safe initialization lock
    
    def __init__(self, logger=None, lang='en'):
        self.logger = logger
        self.lang = lang
        
        if self.logger:
            self.logger.info("🔧 PaddleNumberDetector.__init__() called")
        
        # Initialize BRILLIANT AI Pattern Learning (YOUR VISION!)
        self.ai_learning = AIPatternLearning(logger)
        
        # ★ CRITICAL: Thread-safe singleton pattern to prevent PDX reinitialization
        with PaddleNumberDetector._lock:
            if PaddleNumberDetector._initialized:
                # Already initialized - reuse existing OCR instance
                self.ocr = PaddleNumberDetector._ocr_instance
                if self.logger:
                    self.logger.info(f"♻️  Reusing existing PaddleOCR instance (singleton): {self.ocr}")
                return
            
            if self.logger:
                self.logger.info("🚀 First initialization - creating new PaddleOCR instance...")
            
            # Initialize PaddleOCR with fallback (singleton pattern)
            try:
                import sys
                
                # ★ CRITICAL: Create .version file if missing (fixes EXE error)
                if getattr(sys, 'frozen', False):
                    base_path = sys._MEIPASS
                    paddlex_version_file = os.path.join(base_path, 'paddlex', '.version')
                    if not os.path.exists(paddlex_version_file):
                        # Create the .version file with a default version
                        try:
                            os.makedirs(os.path.dirname(paddlex_version_file), exist_ok=True)
                            with open(paddlex_version_file, 'w') as f:
                                f.write('3.0.0')  # Default version
                        except:
                            pass  # Ignore if we can't create it
                
                from paddleocr import PaddleOCR
            
                # Set PaddleX home directory for EXE builds  
                if getattr(sys, 'frozen', False):
                    # Running as EXE - check for bundled models first
                    base_path = sys._MEIPASS
                    
                    # Try multiple possible bundled model locations
                    bundled_paths = [
                        os.path.join(base_path, '.paddlex'),
                        os.path.join(base_path, '.paddleocr'), 
                        os.path.join(base_path, 'paddleocr_models'),
                        os.path.join(base_path, '_internal', '.paddlex'),
                        os.path.join(base_path, '_internal', '.paddleocr')
                    ]
                    
                    models_found = False
                    for path in bundled_paths:
                        if os.path.exists(path):
                            os.environ['PADDLEX_HOME'] = path
                            if self.logger:
                                self.logger.info(f"Using bundled models: {path}")
                            models_found = True
                            break
                    
                    if not models_found:
                        # No bundled models - check user's home directory
                        from pathlib import Path
                        user_paths = [
                            Path.home() / '.paddlex',
                            Path.home() / '.paddleocr'
                        ]
                        
                        for user_path in user_paths:
                            if user_path.exists() and any(user_path.rglob('*.pdparams')):
                                os.environ['PADDLEX_HOME'] = str(user_path)
                                if self.logger:
                                    self.logger.info(f"Using user models: {user_path}")
                                models_found = True
                                break
                    
                    if not models_found:
                        if self.logger:
                            self.logger.info("No models found - PaddleOCR will download automatically on first use")
                        # Set a default path for model downloads
                        from pathlib import Path
                        default_path = Path.home() / '.paddlex'
                        os.environ['PADDLEX_HOME'] = str(default_path)
                
                # Initialize PaddleOCR 3.2+ with recognition enabled
                if not PaddleNumberDetector._initialized:
                    self.ocr = PaddleOCR(
                        # PaddleX PaddleOCR 3.2+ uses minimal parameters
                        # Most parameters from older versions not supported
                    )
                    # Store as singleton
                    PaddleNumberDetector._ocr_instance = self.ocr
                    PaddleNumberDetector._initialized = True
                else:
                    # Reuse existing instance
                    self.ocr = PaddleNumberDetector._ocr_instance
                
                if self.logger:
                    gpu_status = "GPU" if self._check_gpu() else "CPU"
                    self.logger.info(f"PaddleOCR initialized successfully ({gpu_status})")
                    
            except ImportError as e:
                if self.logger:
                    self.logger.warning(f"PaddleOCR not installed: {e}")
                    self.logger.warning("Install with: pip install paddleocr")
                self.ocr = None
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to initialize PaddleOCR: {e}")
                    # Log full traceback for debugging
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
                self.ocr = None
    
    def _check_gpu(self) -> bool:
        """Check if GPU is available for PaddleOCR"""
        try:
            import paddle
            return paddle.is_compiled_with_cuda()
        except:
            return False
    
    def detect_page_number(self, image: Image.Image, ocr_text: str, filename: str, position: int = None, total_pages: int = None) -> Optional[NumberCandidate]:
        """Main detection method - scans corners for page numbers"""
        if self.logger:
            self.logger.debug(f"PaddleOCR detector analyzing: {filename}")
        
        # Fallback if PaddleOCR not available
        if self.ocr is None:
            if self.logger:
                self.logger.error("❌ CRITICAL: self.ocr is None - PaddleOCR failed to initialize!")
                self.logger.error(f"   Initialized flag: {PaddleNumberDetector._initialized}")
                self.logger.error(f"   OCR instance: {PaddleNumberDetector._ocr_instance}")
                self.logger.warning("   Using filename fallback instead of OCR")
            return self._fallback_detection(filename)
        
        # Scan all 8 positions with intelligent type detection
        candidates = self._scan_corners(image, filename, position)
        
        if self.logger:
            self.logger.debug(f"Found {len(candidates)} candidates")
        
        # Return best candidate
        if candidates:
            best = max(candidates, key=lambda x: x.confidence)
            
            # ★ CRITICAL: Validate number to catch OCR errors
            validated_best = self._validate_detected_number(best, total_pages)
            
            if self.logger:
                if validated_best.number != best.number:
                    self.logger.warning(f"📝 OCR CORRECTION: '{best.text}' (num={best.number}) → '{validated_best.text}' (num={validated_best.number})")
                self.logger.info(f"Best: {validated_best.text} (conf: {validated_best.confidence:.1f}%, loc: {validated_best.location})")
            return validated_best
        
        if self.logger:
            self.logger.debug("No page number detected")
        return None
    
    def _detect_expected_number_type(self, position: int = None) -> Optional[str]:
        """
        SMART: Provide hints based on POSITION (not filename!)
        This is just a performance optimization - we ALWAYS accept whatever we find!
        
        Returns:
            'roman' - Hint to scan roman positions first (but accept arabic if found)
            'arabic' - Hint to scan arabic positions first (but accept roman if found)
            None - No hint, scan all positions equally
        """
        # Check AI learning history FIRST (most reliable!)
        if self.ai_learning.dominant_type:
            return self.ai_learning.dominant_type
        
        # No position info - no hint
        if position is None:
            return None
        
        # ★ POSITION-BASED HINTS (NOT enforcement!) ★
        # Positions 1-5: Front matter (title, copyright, contents)
        # Could have roman "v", or no numbers - no hint
        if position <= 5:
            return None
        
        # Positions 6-16: Typical front matter continuation
        # Usually roman numerals (vi, vii, viii... xv)
        elif position <= 16:
            return 'roman'  # Hint only - accept arabic if found!
        
        # Positions 17+: Main content
        # Usually arabic numbers (1, 2, 3...)
        else:
            return 'arabic'  # Hint only - accept roman if found!

    
    def _scan_corners(self, image: Image.Image, filename: str = "", position: int = None) -> List[NumberCandidate]:
        """Scan all 4 corners for page numbers"""
        candidates = []
        
        # SMART: Detect expected number type from POSITION (not filename!)
        expected_type = self._detect_expected_number_type(position)
        
        # Convert to numpy
        img_array = np.array(image)
        height, width = img_array.shape[:2]
        
        # Define scanning regions - ENLARGED for better OCR accuracy
        # CRITICAL: Larger regions capture complete page numbers (vi, vii, viii, etc.)
        corner_size = 300  # Increased from 200 to 300 pixels
        center_width = 400  # Increased from 300 to 400 pixels
        middle_height = 300  # Height for middle edge regions
        
        corners = {
            'top_left': (0, 0, corner_size, corner_size),
            'top_right': (width - corner_size, 0, width, corner_size),
            'bottom_left': (0, height - corner_size, corner_size, height),
            'bottom_right': (width - corner_size, height - corner_size, width, height),
            # ENHANCED: Add center positions (very common for page numbers!)
            'bottom_center': (width//2 - center_width//2, height - corner_size, 
                            width//2 + center_width//2, height),
            'top_center': (width//2 - center_width//2, 0, 
                          width//2 + center_width//2, corner_size),
            # NEW: Add middle edge positions (for edge-middle page numbers)
            'middle_left': (0, height//2 - middle_height//2, 
                          corner_size, height//2 + middle_height//2),
            'middle_right': (width - corner_size, height//2 - middle_height//2,
                           width, height//2 + middle_height//2)
        }
        
        # INTELLIGENT SCAN ORDER: Use AI learning with expected number type!
        scan_order = self.ai_learning.get_scan_order(expected_number_type=expected_type)
        
        if self.logger:
            expected_msg = f" (expecting {expected_type})" if expected_type else ""
            self.logger.debug(f"🧠 AI scan order{expected_msg}: {scan_order}")
        
        for corner_name in scan_order:
            (x1, y1, x2, y2) = corners[corner_name]
            
            # Extract corner region
            corner_region = img_array[y1:y2, x1:x2]
            
            # OCR the corner with PaddleOCR
            corner_candidates = self._ocr_corner(corner_region, corner_name, x1, y1)
            candidates.extend(corner_candidates)
            
            # AI LEARNING: Record detection results
            if corner_candidates:
                best_candidate = corner_candidates[0]
                # Determine number type
                number_type = 'roman' if best_candidate.text.lower() in ['i','ii','iii','iv','v','vi','vii','viii','ix','x','xi','xii'] else 'arabic'
                
                # TEACH THE AI: This location had a page number!
                self.ai_learning.record_success(corner_name, number_type, best_candidate.number)
                
                # EARLY EXIT: Skip other corners if AI is confident about this location
                if self.ai_learning.should_skip_remaining_corners(corner_name):
                    break
            else:
                # TEACH THE AI: This location had no page number
                self.ai_learning.record_failure(corner_name)
        
        return candidates
    
    def _validate_detected_number(self, candidate: NumberCandidate, total_pages: int = None) -> NumberCandidate:
        """
        ★ CRITICAL FIX: Validate detected number to catch OCR errors
        Example: OCR reads "50" but should be "4" or "5"
        """
        if candidate is None:
            return candidate
        
        # Only validate arabic numbers (roman numerals are usually correct)
        detected_text = candidate.text
        
        # Check if this is a roman numeral - don't validate these
        if detected_text.lower() in ['i','ii','iii','iv','v','vi','vii','viii','ix','x','xi','xii','xiii','xiv','xv','xvi','xvii','xviii','xix','xx']:
            return candidate  # Roman numerals are usually accurate
        
        # For arabic numbers, check if realistic
        if total_pages is None:
            total_pages = 100  # Conservative default
        
        max_realistic = total_pages * 3  # Allow 3x pages for safety
        
        # If number seems too large, likely OCR error
        if candidate.number > max_realistic:
            # Common OCR errors: "50" instead of "5" or "0"
            # Try extracting single digits
            num_str = str(candidate.number)
            
            if len(num_str) == 2:  # Two-digit number
                first_digit = int(num_str[0])
                second_digit = int(num_str[1])
                
                # Check which single digit makes more sense
                if 1 <= first_digit <= total_pages:
                    # First digit is realistic
                    if self.logger:
                        self.logger.warning(f"⚠️ OCR likely misread multi-digit as single: '{num_str}' → '{first_digit}'")
                    return NumberCandidate(
                        number=first_digit,
                        text=str(first_digit),
                        location=candidate.location,
                        confidence=candidate.confidence * 0.8,  # Reduce confidence slightly
                        reasoning=candidate.reasoning + [f"Corrected from '{num_str}' to '{first_digit}' (OCR validation)"]
                    )
                elif 1 <= second_digit <= total_pages:
                    # Second digit is realistic
                    if self.logger:
                        self.logger.warning(f"⚠️ OCR likely misread multi-digit as single: '{num_str}' → '{second_digit}'")
                    return NumberCandidate(
                        number=second_digit,
                        text=str(second_digit),
                        location=candidate.location,
                        confidence=candidate.confidence * 0.8,
                        reasoning=candidate.reasoning + [f"Corrected from '{num_str}' to '{second_digit}' (OCR validation)"]
                    )
        
        # Number seems valid, return as-is
        return candidate
    
    def _fallback_detection(self, filename: str) -> Optional[NumberCandidate]:
        """Fallback detection using filename when PaddleOCR not available"""
        # Extract number from filename like "Page_006.jpg"
        match = re.search(r'Page_(\d{3,4})', filename)
        if match:
            page_num_str = match.group(1)
            page_num = int(page_num_str)
            
            # Convert to expected format based on memory analysis
            if 1 <= page_num <= 5:
                return None  # Title/blank/copyright/contents pages
            elif 6 <= page_num <= 12:
                # Front matter - roman numerals (vi, vii, viii, ix, x, xi, xii)
                roman_text = self._int_to_roman(page_num)
                return NumberCandidate(
                    number=page_num,
                    text=roman_text,
                    location="filename",
                    confidence=60.0,  # Lower confidence for fallback
                    reasoning=["Filename fallback", "Front matter roman"],
                )
            elif page_num > 50:
                # Main content - arabic
                return NumberCandidate(
                    number=page_num - 12,  # Adjust for front matter offset
                    text=str(page_num - 12),
                    location="filename", 
                    confidence=60.0,
                    reasoning=["Filename fallback", "Main content"],
                )
        return None
    
    def _int_to_roman(self, num: int) -> str:
        """Convert integer to roman numeral"""
        values = [50, 40, 10, 9, 5, 4, 1]
        symbols = ['l', 'xl', 'x', 'ix', 'v', 'iv', 'i']
        
        result = ''
        for i in range(len(values)):
            count = num // values[i]
            if count:
                result += symbols[i] * count
                num -= values[i] * count
        return result
    
    def _ocr_corner(self, region: np.ndarray, corner_name: str, offset_x: int, offset_y: int) -> List[NumberCandidate]:
        """OCR a corner region with PaddleOCR 3.2+ API"""
        candidates = []
        
        try:
            # Save corner region as temporary file for PaddleOCR 3.2+ predict API
            # NO PREPROCESSING - it causes false positives from page content
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_path = temp_file.name
                corner_image = Image.fromarray(region)
                corner_image.save(temp_path, quality=95)  # High quality to preserve details
            
            try:
                # Use PaddleOCR ocr API (compatible with latest version)
                results = self.ocr.ocr(temp_path)
                
                # PaddleOCR processing (debug logs removed for cleaner output)
                
                if results and len(results) > 0 and results[0]:
                    result_obj = results[0]
                    
                    # PaddleX OCRResult is a dict-like object
                    
                    # Try to access as dictionary with common OCR result keys
                    if isinstance(result_obj, dict) or hasattr(result_obj, 'get'):
                        # Try multiple possible key names
                        dt_polys = result_obj.get('dt_polys', result_obj.get('boxes', []))
                        rec_texts = result_obj.get('rec_texts', result_obj.get('rec_text', result_obj.get('texts', [])))
                        rec_scores = result_obj.get('rec_scores', result_obj.get('rec_score', result_obj.get('scores', [])))
                        rec_boxes = result_obj.get('rec_boxes', [])
                        
                        # If rec_texts empty but rec_boxes has data, extract from rec_boxes
                        if not rec_texts and rec_boxes:
                            # rec_boxes might be: [[box_coords, text, score], ...] or other structure
                            # Try to extract text from rec_boxes
                            try:
                                for box_data in rec_boxes:
                                    if isinstance(box_data, (list, tuple)) and len(box_data) >= 2:
                                        # Assume format: [bbox, text] or [bbox, text, score]
                                        if len(box_data) == 2:
                                            rec_texts.append(box_data[1])
                                            rec_scores.append(1.0)  # Default score
                                        elif len(box_data) >= 3:
                                            rec_texts.append(box_data[1])
                                            rec_scores.append(box_data[2])
                                if rec_texts and self.logger:
                                    self.logger.debug(f"✅ Extracted {len(rec_texts)} texts from rec_boxes")
                            except Exception as e:
                                if self.logger:
                                    self.logger.debug(f"⚠️ Failed to extract from rec_boxes: {e}")
                        
                        # Iterate over detected text regions
                        for i, (bbox, text, score) in enumerate(zip(dt_polys, rec_texts, rec_scores)):
                            

                            if text and str(text).strip():  # Skip empty text
                                # Extract page numbers from text
                                page_numbers = self._extract_numbers(str(text), corner_name, float(score) * 100)
                                
                                for candidate in page_numbers:
                                    # Adjust bbox coordinates if available
                                    if bbox is not None and len(bbox) >= 4:
                                        x_coords = [point[0] for point in bbox]
                                        y_coords = [point[1] for point in bbox]
                                        x_min = int(min(x_coords)) + offset_x
                                        y_min = int(min(y_coords)) + offset_y
                                        x_max = int(max(x_coords)) + offset_x
                                        y_max = int(max(y_coords)) + offset_y
                                        candidate.bbox = (x_min, y_min, x_max, y_max)
                                    
                                    candidates.append(candidate)
                                    if self.logger:
                                        self.logger.debug(f"✅ {corner_name}: Found '{text}' → {candidate.number} (conf: {float(score)*100:.1f}%)")
                        
                        # Skip fallback if we processed dict successfully
                        if dt_polys or rec_texts or rec_scores:
                            pass  # Already processed above
                    else:
                        # Fallback to old iteration method
                        if self.logger:
                            self.logger.warning(f"⚠️ OCRResult doesn't have expected attributes, using fallback")
                        for line in results[0]:
                            # Handle both old and new PaddleOCR formats
                            bbox = None
                            text = None
                            score = 0.0
                            
                            try:
                                if len(line) == 2:
                                    bbox, text_info = line
                                    # text_info can be: tuple (text, score) or list [text, score]
                                    if isinstance(text_info, (tuple, list)) and len(text_info) >= 2:
                                        text, score = text_info[0], text_info[1]
                                    else:
                                        if self.logger:
                                            self.logger.debug(f"⚠️ Unexpected text_info format: {type(text_info)}, {text_info}")
                                        continue
                                else:
                                    if self.logger:
                                        self.logger.debug(f"⚠️ Unexpected line length: {len(line)}")
                                    continue
                            except Exception as e:
                                if self.logger:
                                    self.logger.error(f"❌ Failed to parse PaddleOCR result: {e}")
                                continue
                            
                            if text and str(text).strip():  # Skip empty text
                                # Extract page numbers from text
                                page_numbers = self._extract_numbers(text, corner_name, score * 100)
                                
                                for candidate in page_numbers:
                                    # Adjust bbox coordinates
                                    if bbox is not None and len(bbox) >= 4:
                                        x_coords = [point[0] for point in bbox]
                                        y_coords = [point[1] for point in bbox]
                                        x_min = int(min(x_coords)) + offset_x
                                        y_min = int(min(y_coords)) + offset_y
                                        x_max = int(max(x_coords)) + offset_x
                                        y_max = int(max(y_coords)) + offset_y
                                        candidate.bbox = (x_min, y_min, x_max, y_max)
                                    
                                    candidates.append(candidate)
                                if self.logger:
                                    self.logger.debug(f"✅ {corner_name}: Found '{text}' → {candidate.number} (conf: {score*100:.1f}%)")
                
            finally:
                # Clean up temporary file
                import os
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"OCR failed for {corner_name}: {e}")
        
        return candidates
    
    def _extract_numbers(self, text: str, location: str, ocr_confidence: float) -> List[NumberCandidate]:
        """Extract page numbers from OCR text with FALSE POSITIVE FILTERING"""
        candidates = []
        
        # Clean text
        text = text.strip()
        
        # FILTER: Reject if too many words (likely content)
        words = text.split()
        if len(words) > 5:
            return candidates
        
        # FILTER: Reject if contains common non-number words
        text_lower = text.lower()
        if any(word in text_lower for word in ['page', 'chapter', 'section', 'figure', 'table', 'the', 'and', 'of']):
            return candidates
        
        # Find ARABIC numbers (1, 2, 3, etc.) - PREVENT HUGE NUMBERS
        arabic_matches = re.findall(r'\b(\d{1,3})\b', text)  # Only 1-3 digits to prevent ISBN/years
        for num_text in arabic_matches:
            try:
                num_value = int(num_text)
                
                # FILTER: Valid page number range (realistic book pages)
                if not (1 <= num_value <= 999):
                    continue
                
                # Calculate confidence
                confidence = ocr_confidence * 100 * 0.9  # Base confidence
                reasoning = [f"Arabic in {location}"]
                
                # SMART: Penalize suspiciously high numbers in non-standard positions
                if num_value > 200 and location not in ['top_left', 'top_right', 'top_center', 'bottom_center']:
                    confidence *= 0.4  # Likely ISBN/reference, not page number
                    reasoning.append("High number in unusual position (likely reference)")
                
                # BOOST: Standard page number positions
                if location in ['top_left', 'top_right']:
                    confidence += 25
                    reasoning.append("Standard page number position")
                elif location in ['top_center', 'bottom_center']:
                    confidence += 15
                    reasoning.append("Common page number position")
                elif 'top' in location:
                    confidence += 10
                    reasoning.append("Top corner")
                
                if 'right' in location:
                    confidence += 5
                    reasoning.append("Right side")
                
                # Boost if isolated number
                if text == num_text:
                    confidence += 10
                    reasoning.append("Isolated number")
                
                candidates.append(NumberCandidate(
                    number=num_value,
                    text=num_text,
                    location=location,
                    confidence=min(confidence, 99.9),
                    reasoning=reasoning
                ))
            except ValueError:
                continue
        
        # Find ROMAN NUMERALS (vi, vii, viii, ix, x, xi, xii, etc.)
        # IMPROVED: Match longer sequences first, validate properly
        roman_pattern = r'\b([ivxlcdm]{1,10})\b'
        roman_matches = re.findall(roman_pattern, text_lower)
        
        # CRITICAL FIX: Sort by length (longest first) to prefer "vii" over "i"
        roman_matches = sorted(set(roman_matches), key=len, reverse=True)
        
        for roman_text in roman_matches:
            # FILTER: Reject ambiguous single letters unless they're valid standalone
            if len(roman_text) == 1:
                # Only accept i, v, x as standalone (common page numbers)
                if roman_text not in ['i', 'v', 'x']:
                    continue
                # EXTRA VALIDATION: Single 'i' or 'v' should be isolated in text
                if roman_text in ['i', 'v'] and len(text_lower) > 3:
                    continue  # Likely part of a word, not a page number
            
            # Validate it's a proper roman numeral
            roman_value = self._roman_to_int(roman_text)
            if not roman_value or roman_value < 1 or roman_value > 50:
                continue
            
            # ENHANCED VALIDATION: Check if this is the BEST match in the text
            # Skip shorter matches if a longer valid match exists
            is_best_match = True
            for other_match in roman_matches:
                if other_match != roman_text and len(other_match) > len(roman_text):
                    if roman_text in other_match:  # This is a substring of a longer match
                        other_value = self._roman_to_int(other_match)
                        if other_value and 1 <= other_value <= 50:
                            is_best_match = False
                            break
            
            if not is_best_match:
                continue
            
            # Calculate confidence
            confidence = ocr_confidence * 100 * 0.95
            reasoning = [f"Roman '{roman_text}' in {location}"]
            
            # BOOST: Roman numerals in front matter standard positions
            if location in ['top_left', 'top_right']:
                confidence += 30
                reasoning.append("Front matter standard position")
            elif location in ['top_center']:
                confidence += 20
                reasoning.append("Common front matter position")
            
            # Boost confidence for longer roman numerals (more reliable)
            if len(roman_text) >= 3:
                confidence += 15
                reasoning.append("Multi-character roman (high confidence)")
            elif len(roman_text) == 2:
                confidence += 10
                reasoning.append("Two-character roman")
            
            # Boost confidence based on location
            if 'top' in location:
                confidence += 10
                reasoning.append("Top corner")
            if 'left' in location:
                confidence += 5
                reasoning.append("Left side (roman standard)")
            
            # Boost if isolated
            if text_lower.strip() == roman_text:
                confidence += 15
                reasoning.append("Isolated numeral (very reliable)")
            
            candidates.append(NumberCandidate(
                number=roman_value,
                text=roman_text,
                location=location,
                confidence=min(confidence, 99.9),
                reasoning=reasoning
            ))
        
        return candidates
    
    def _preprocess_for_ocr(self, region: np.ndarray) -> np.ndarray:
        """
        Preprocess image region for better OCR accuracy
        Enhances contrast, sharpens text, reduces noise
        """
        import cv2
        
        # Convert to grayscale if needed
        if len(region.shape) == 3:
            gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
        else:
            gray = region.copy()
        
        # Apply adaptive thresholding to enhance text
        # This makes text stand out more clearly
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise to remove artifacts
        denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
        
        # Sharpen the image to make text crisper
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        
        # Convert back to RGB for PIL
        if len(region.shape) == 3:
            result = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2RGB)
        else:
            result = sharpened
        
        return result
    
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
    
    def log_stats(self):
        """Log detector statistics"""
        if self.logger:
            self.logger.info("PaddleOCR Detector Stats:")
            self.logger.info("  - Engine: PaddleOCR (ultra-fast)")
            self.logger.info("  - Corner size: 200x200 pixels")
            self.logger.info("  - Detection: Arabic (1-500), Roman (1-50)")
            self.logger.info("  - False positive filtering: Enabled")
            self.logger.info("  - Early exit: Enabled (>85% confidence)")
