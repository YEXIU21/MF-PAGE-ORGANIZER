"""
Standalone OCR engine that works without external Tesseract installation
Includes fallback methods for non-technical users
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import tempfile
import subprocess
from dataclasses import dataclass
import cv2
import numpy as np

from utils.config import config
from utils.logger import ProcessLogger
from core.smart_cache import SmartCache
from core.input_handler import PageInfo
from core.paddle_number_detector import PaddleNumberDetector
from core.paddle_ocr_engine import PaddleOCREngine

@dataclass
class DetectedNumber:
    """Information about detected numbers on a page"""
    text: str
    number_type: str  # 'arabic', 'roman', 'hybrid', 'hierarchical'
    numeric_value: Optional[int]
    confidence: float
    position: Tuple[int, int, int, int]  # x, y, width, height
    context: str  # surrounding text

@dataclass
class OCRResult:
    """Results from OCR processing of a page"""
    page_info: PageInfo
    full_text: str
    detected_numbers: List[DetectedNumber]
    text_blocks: List[Dict[str, Any]]
    language_confidence: float
    processing_time: float

class OCREngine:
    """OCR engine that works standalone without external dependencies"""
    
    # Roman numeral patterns
    ROMAN_PATTERNS = {
        'lowercase': r'\b(?=[mdclxvi])m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\b',
        'uppercase': r'\b(?=[MDCLXVI])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b'
    }
    
    # Arabic number patterns
    ARABIC_PATTERNS = {
        'simple': r'\b\d+\b',
        'with_separators': r'\b\d{1,3}(?:[,\.]\d{3})*\b',
        'decimal': r'\b\d+\.\d+\b'
    }
    
    # Hybrid patterns (combining letters and numbers)
    HYBRID_PATTERNS = {
        'chapter_page': r'\b(?:Chapter|Ch\.?)\s*(\d+)[,\s]+(?:Page|p\.?)\s*(\d+)\b',
        'section_number': r'\b(\d+)\.(\d+)\b'
    }
    
    def __init__(self, logger: Optional[ProcessLogger] = None, ai_learning=None, output_dir=None):
        self.logger = logger
        self.config = config
        self.tesseract_available = self._check_tesseract()
        
        # Initialize smart cache with output directory
        self.smart_cache = SmartCache(logger, output_dir)
        
        # Initialize PaddleOCR-based detector (BRILLIANT AI with existing modules)
        self.paddle_detector = PaddleNumberDetector(logger, lang='en')
        
        # Initialize PaddleOCR engine for full text extraction
        self.paddle_ocr = PaddleOCREngine(logger, lang='en')
        
        # Keep embedded OCR as fallback
        self.embedded_ocr = self.paddle_ocr
        
        # Check for bundled Tesseract or system Tesseract
        self._initialize_tesseract()
        
        # If no Tesseract, use embedded OCR
        if not self.tesseract_available:
            self._log_info("Using embedded OCR engine (no external installation required)")
    
    def _is_roman_numeral(self, text: str) -> bool:
        """Check if text is a valid roman numeral"""
        pattern = r'^[ivxlcdm]+$'
        return bool(re.match(pattern, text.lower()))
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            import pytesseract
            # Try to get version
            pytesseract.get_tesseract_version()
            return True
        except:
            return False
    
    def _initialize_tesseract(self):
        """Initialize Tesseract OCR with bundled or system installation"""
        try:
            # First, try to find bundled Tesseract (for standalone)
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                bundle_dir = sys._MEIPASS
                tesseract_path = os.path.join(bundle_dir, 'tesseract', 'tesseract.exe')
                if os.path.exists(tesseract_path):
                    self.tesseract_path = tesseract_path
                    self.tesseract_available = True
                    self._log_info(f"Using bundled Tesseract: {tesseract_path}")
                    return
            
            # Try system Tesseract
            import pytesseract
            try:
                # Test if Tesseract works
                pytesseract.get_tesseract_version()
                self.tesseract_available = True
                self._log_info("Using system Tesseract installation")
                return
            except:
                pass
            
            # Try common installation paths
            common_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Tools\tesseract\tesseract.exe"
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    try:
                        pytesseract.get_tesseract_version()
                        self.tesseract_available = True
                        self.tesseract_path = path
                        self._log_info(f"Found Tesseract at: {path}")
                        return
                    except:
                        continue
                        
        except Exception as e:
            self._log_warning(f"Could not initialize Tesseract: {e}")
    
    def _log_info(self, message):
        if self.logger:
            self.logger.info(message)
        else:
            print(f"INFO: {message}")
    
    def _log_warning(self, message):
        if self.logger:
            self.logger.warning(message)
        else:
            print(f"WARNING: {message}")
    
    def _log_error(self, message):
        if self.logger:
            self.logger.error(message)
        else:
            print(f"ERROR: {message}")
    
    def process_batch(self, pages: List[PageInfo], workers: int = 1) -> List[OCRResult]:
        """Process multiple pages with OCR (supports multi-threading)
        
        Args:
            pages: List of pages to process
            workers: Number of worker threads (1 = sequential, 2+ = parallel)
        
        Returns:
            List of OCR results
        """
        if workers > 1:
            # Multi-threaded processing
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            if self.logger:
                self.logger.info(f"⚡ Using {workers} workers for parallel OCR processing")
            
            results = [None] * len(pages)  # Pre-allocate results list
            
            with ThreadPoolExecutor(max_workers=workers) as executor:
                # Submit all tasks
                future_to_index = {
                    executor.submit(self.process_page, page): i 
                    for i, page in enumerate(pages)
                }
                
                # Collect results as they complete
                completed = 0
                for future in as_completed(future_to_index):
                    if hasattr(self, 'cancel_processing') and self.cancel_processing:
                        if self.logger:
                            self.logger.info("OCR processing cancelled by user")
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    
                    idx = future_to_index[future]
                    try:
                        results[idx] = future.result()
                        completed += 1
                        if self.logger:
                            self.logger.progress("OCR Processing", completed, len(pages))
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"OCR failed for page {idx}: {e}")
                        # Create empty result as fallback
                        results[idx] = OCRResult(
                            page_info=pages[idx],
                            full_text="",
                            detected_number=None,
                            confidence=0.0,
                            processing_time=0.0
                        )
            
            return results
        
        else:
            # Sequential processing (original behavior)
            results = []
            for i, page in enumerate(pages):
                # Check for cancellation
                if hasattr(self, 'cancel_processing') and self.cancel_processing:
                    if self.logger:
                        self.logger.info("OCR processing cancelled by user")
                    break
                    
                if self.logger:
                    self.logger.progress("OCR Processing", i + 1, len(pages))
                result = self.process_page(page)
                results.append(result)
            return results
    
    def process_page(self, page_info: PageInfo) -> OCRResult:
        """Process a page with OCR and number detection"""
        import time
        start_time = time.time()
        
        try:
            # Check cache first (AI memory)
            # CACHE KEY: v20_adaptive - SMART adaptive upscaling (2x→3x→5x)
            image_hash = self.smart_cache.get_image_hash(str(page_info.file_path))
            cached_result = self.smart_cache.get_cached_result(image_hash, 'ocr_v20_adaptive')
            
            if cached_result:
                if self.logger:
                    self.logger.debug(f"✨ Using cached OCR for {page_info.original_name}")
                return cached_result
            
            # Load image
            image = Image.open(page_info.file_path)
            
            # CRITICAL DEBUG: Log that we're about to call advanced detector
            if self.logger:
                self.logger.info(f"🚀 ABOUT TO CALL ADVANCED DETECTOR for {page_info.original_name}")
                self.logger.info(f"   Paddle detector exists: {self.paddle_detector is not None}")
                self.logger.info(f"   Image loaded: {image.size}")
            
            # PRIORITY FIX: Use EXISTING paddle detector (already has API fix)
            # This prevents content numbers from polluting the results
            ai_candidate = self.paddle_detector.detect_page_number(
                image, "", str(page_info.file_path), total_pages=len(pages)
            )
            
            if self.logger:
                self.logger.info(f"✅ ADVANCED DETECTOR RETURNED: {ai_candidate}")
            
            if self.logger:
                if ai_candidate:
                    self.logger.debug(f"🎯 Advanced detector found: {ai_candidate.number} (confidence: {ai_candidate.confidence}%)")
                else:
                    self.logger.debug(f"❌ Advanced detector found nothing")
            
            if ai_candidate and ai_candidate.confidence > 50:
                # Convert AI candidate to DetectedNumber format
                
                # Determine number type
                if ai_candidate.text.lower() in ['i','ii','iii','iv','v','vi','vii','viii','ix','x','xi','xii','xiii','xiv','xv']:
                    number_type = 'roman'
                else:
                    number_type = 'arabic'
                
                # Create DetectedNumber
                detected_numbers = [DetectedNumber(
                    text=ai_candidate.text,
                    number_type=number_type,
                    numeric_value=ai_candidate.number,
                    confidence=ai_candidate.confidence,
                    position=ai_candidate.bbox if hasattr(ai_candidate, 'bbox') and ai_candidate.bbox else (0, 0, 100, 30),
                    context=f"AI: {ai_candidate.reasoning[0] if ai_candidate.reasoning else 'AI detected'}"
                )]
                
                result = OCRResult(
                    page_info=page_info,
                    full_text="",  # Don't need full text if we found page number
                    detected_numbers=detected_numbers,
                    text_blocks=[],
                    language_confidence=ai_candidate.confidence / 100.0,
                    processing_time=0
                )
            else:
                # Fallback to basic OCR only if AI didn't find anything
                if self.tesseract_available:
                    result = self._process_with_tesseract(image, page_info)
                else:
                    result = self._process_with_embedded_ocr(image, page_info)
            
            result.processing_time = time.time() - start_time
            
            # Save to cache for future use (AI memory) - using new cache key
            self.smart_cache.save_result(image_hash, result, 'ocr_v20_adaptive', result.processing_time)
            
            return result
            
        except Exception as e:
            import traceback
            self._log_error(f"OCR failed for {page_info.original_name}: {e}")
            if self.logger:
                self.logger.error(f"Full traceback:\n{traceback.format_exc()}")
            
            # Return empty result
            return OCRResult(
                page_info=page_info,
                full_text="",
                detected_numbers=[],
                text_blocks=[],
                language_confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    def _process_with_tesseract(self, image: Image.Image, page_info: PageInfo) -> OCRResult:
        """Process with Tesseract OCR"""
        try:
            import pytesseract
            
            if self.tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # OCR configuration
            ocr_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,;:!?()-'
            
            # Get full text
            full_text = pytesseract.image_to_string(cv_image, config=ocr_config)
            
            # Get detailed OCR data
            ocr_data = pytesseract.image_to_data(cv_image, config=ocr_config, output_type=pytesseract.Output.DICT)
            
            # Extract text blocks
            text_blocks = self._extract_text_blocks(ocr_data)
            
            # Detect numbers
            detected_numbers = self._detect_numbers(full_text, text_blocks)
            
            return OCRResult(
                page_info=page_info,
                full_text=full_text,
                detected_numbers=detected_numbers,
                text_blocks=text_blocks,
                language_confidence=85.0,  # Assume good confidence with Tesseract
                processing_time=0.0
            )
            
        except Exception as e:
            self._log_error(f"Tesseract OCR failed: {e}")
            # Fall back to basic methods
            return self._process_with_fallback(image, page_info)
    
    def _process_with_embedded_ocr(self, image: Image.Image, page_info: PageInfo) -> OCRResult:
        """Process with PaddleOCR (ultra-fast, no external dependencies)"""
        try:
            # Use PaddleOCR engine for full text
            full_text = self.paddle_ocr.extract_text(image)
            
            # Use PADDLE CORNER-FOCUSED detector (ULTRA-FAST, ACCURATE)
            if self.config.get('ocr.use_advanced_analysis', True):
                self._log_info(f"Using PaddleOCR detector for {page_info.original_name}")
                
                # Use PaddleOCR number detector (corner-focused)
                # Pass position hint (page_number from PageInfo, or None)
                position_hint = page_info.page_number if page_info.page_number > 0 else None
                detected_candidate = self.paddle_detector.detect_page_number(
                    image, full_text, page_info.original_name, position=position_hint, total_pages=len(pages))
                
                if detected_candidate and detected_candidate.confidence > 70:
                    self._log_info(f"PaddleOCR found: {detected_candidate.text} "
                                 f"(conf: {detected_candidate.confidence:.1f}%, loc: {detected_candidate.location})")
                    
                    # Convert to DetectedNumber object
                    detected_numbers = [DetectedNumber(
                        text=detected_candidate.text,
                        number_type='roman' if detected_candidate.text.lower() in ['i','ii','iii','iv','v','vi','vii','viii','ix','x','xi','xii'] else 'arabic',
                        numeric_value=detected_candidate.number,
                        confidence=detected_candidate.confidence,
                        position=detected_candidate.bbox if detected_candidate.bbox else (0, 0, 100, 30),
                        context=f"PaddleOCR: {detected_candidate.location}"
                    )]
                else:
                    # No corner number found - likely blank/title page
                    self._log_info(f"No corner number (blank/title page)")
                    detected_numbers = []
            else:
                # Standard PaddleOCR fallback
                detected_numbers_data = self.paddle_ocr.detect_page_numbers(full_text, page_info.original_name)
                
                # Convert to DetectedNumber objects
                detected_numbers = []
                for num_data in detected_numbers_data:
                    detected_numbers.append(DetectedNumber(
                        text=num_data['text'],
                        number_type=num_data['type'],
                        numeric_value=num_data.get('value'),
                        confidence=num_data['confidence'],
                        position=(0, 0, 100, 30),
                        context=num_data.get('context', '')
                    ))
            
            # Create basic text blocks
            text_blocks = [{
                'text': full_text,
                'conf': 75,
                'left': 0,
                'top': 0,
                'width': image.width,
                'height': image.height
            }]
            
            return OCRResult(
                page_info=page_info,
                full_text=full_text,
                detected_numbers=detected_numbers,
                text_blocks=text_blocks,
                language_confidence=75.0,
                processing_time=0.0
            )
            
        except Exception as e:
            self._log_error(f"Embedded OCR failed: {e}")
            return self._process_with_fallback(image, page_info)
    
    def _process_with_fallback(self, image: Image.Image, page_info: PageInfo) -> OCRResult:
        """Process with fallback methods when all OCR fails"""
        self._log_info(f"Using basic fallback for {page_info.original_name}")
        
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Basic image processing to extract potential numbers
        processed_text = self._extract_text_basic(cv_image)
        
        # Look for numbers in filename as additional source
        filename_numbers = self._extract_numbers_from_filename(page_info.original_name)
        
        # Combine text sources
        combined_text = f"{processed_text} {page_info.original_name}"
        
        # Create basic text blocks
        text_blocks = [
            {
                'text': processed_text,
                'conf': 60,
                'left': 0,
                'top': 0,
                'width': image.width,
                'height': image.height
            }
        ]
        
        # Detect numbers
        detected_numbers = self._detect_numbers(combined_text, text_blocks)
        
        # Add filename-based numbers
        detected_numbers.extend(filename_numbers)
        
        return OCRResult(
            page_info=page_info,
            full_text=combined_text,
            detected_numbers=detected_numbers,
            text_blocks=text_blocks,
            language_confidence=40.0,  # Lower confidence for fallback
            processing_time=0.0
        )
    
    def _extract_text_basic(self, cv_image) -> str:
        """Basic text extraction using image processing (no OCR)"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply basic image processing to highlight text
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Find contours that might be text
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Very basic attempt to identify number-like regions
            # This is a simplified approach for when OCR is not available
            potential_numbers = []
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Look for rectangular regions that might contain numbers
                if 10 < w < 100 and 10 < h < 50:  # Reasonable size for page numbers
                    aspect_ratio = w / h
                    if 0.2 < aspect_ratio < 5:  # Reasonable aspect ratio
                        potential_numbers.append(f"[number_region_{len(potential_numbers)}]")
            
            return " ".join(potential_numbers)
            
        except Exception as e:
            self._log_warning(f"Basic text extraction failed: {e}")
            return ""
    
    def _extract_numbers_from_filename(self, filename: str) -> List[DetectedNumber]:
        """Extract numbers from filename as fallback"""
        numbers = []
        
        # Look for numbers in filename
        number_matches = re.finditer(r'\d+', filename)
        
        for match in number_matches:
            number_text = match.group()
            try:
                numeric_value = int(number_text)
                
                number_info = DetectedNumber(
                    text=number_text,
                    number_type='arabic',
                    numeric_value=numeric_value,
                    confidence=70.0,  # Medium confidence for filename
                    position=(0, 0, 100, 30),  # Dummy position
                    context=f"filename: {filename}"
                )
                numbers.append(number_info)
                
            except ValueError:
                continue
        
        return numbers
    
    def _extract_text_blocks(self, ocr_data) -> List[Dict[str, Any]]:
        """Extract text blocks from Tesseract OCR data"""
        blocks = []
        
        try:
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                if text and int(ocr_data['conf'][i]) > 30:  # Confidence threshold
                    block = {
                        'text': text,
                        'conf': int(ocr_data['conf'][i]),
                        'left': ocr_data['left'][i],
                        'top': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i]
                    }
                    blocks.append(block)
        except Exception as e:
            self._log_warning(f"Could not extract text blocks: {e}")
        
        return blocks
    
    def _detect_numbers(self, text: str, text_blocks: List[Dict]) -> List[DetectedNumber]:
        """Detect and classify numbers in text"""
        detected_numbers = []
        
        # Arabic numbers
        for match in re.finditer(self.ARABIC_PATTERNS['simple'], text, re.IGNORECASE):
            number_text = match.group()
            try:
                numeric_value = int(number_text)
                
                # Find position in text blocks
                position = self._find_number_position(number_text, text_blocks)
                
                number_info = DetectedNumber(
                    text=number_text,
                    number_type='arabic',
                    numeric_value=numeric_value,
                    confidence=80.0,
                    position=position,
                    context=self._get_context(text, match.start(), match.end())
                )
                detected_numbers.append(number_info)
                
            except ValueError:
                continue
        
        # Roman numerals
        for pattern_name, pattern in self.ROMAN_PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                roman_text = match.group()
                numeric_value = self._roman_to_int(roman_text)
                
                if numeric_value is not None:
                    position = self._find_number_position(roman_text, text_blocks)
                    
                    number_info = DetectedNumber(
                        text=roman_text,
                        number_type='roman',
                        numeric_value=numeric_value,
                        confidence=75.0,
                        position=position,
                        context=self._get_context(text, match.start(), match.end())
                    )
                    detected_numbers.append(number_info)
        
        return detected_numbers
    
    def _find_number_position(self, number_text: str, text_blocks: List[Dict]) -> Tuple[int, int, int, int]:
        """Find position of number in text blocks"""
        for block in text_blocks:
            if number_text in block['text']:
                return (block['left'], block['top'], block['width'], block['height'])
        
        return (0, 0, 50, 20)  # Default position
    
    def _get_context(self, text: str, start: int, end: int, context_length: int = 20) -> str:
        """Get surrounding context for a number"""
        context_start = max(0, start - context_length)
        context_end = min(len(text), end + context_length)
        return text[context_start:context_end].strip()
    
    def _roman_to_int(self, roman: str) -> Optional[int]:
        """Convert Roman numeral to integer"""
        if not roman:
            return None
            
        roman = roman.upper()
        values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        
        try:
            total = 0
            prev_value = 0
            
            for char in reversed(roman):
                if char not in values:
                    return None
                    
                value = values[char]
                if value < prev_value:
                    total -= value
                else:
                    total += value
                prev_value = value
            
            return total if total > 0 else None
            
        except:
            return None

# OCREngine class is defined above - no alias needed
