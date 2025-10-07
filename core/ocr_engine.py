"""
Standalone OCR engine that works without external Tesseract installation
Includes fallback methods for non-technical users
"""

import re
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from PIL import Image
import os
import sys
import tempfile
import subprocess
from dataclasses import dataclass

from utils.config import config
from utils.logger import ProcessLogger
from core.smart_cache import SmartCache
from core.input_handler import PageInfo
from core.advanced_number_detector import AdvancedNumberDetector
from core.advanced_image_analyzer import AdvancedImageAnalyzer

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
    
    def __init__(self, logger: Optional[ProcessLogger] = None, ai_learning=None):
        self.logger = logger
        self.config = config
        self.tesseract_available = self._check_tesseract()
        
        # Initialize smart cache
        self.smart_cache = SmartCache(logger)
        
        # Initialize advanced image analyzer with AI learning (ADAPTIVE)
        # This creates the EasyOCR reader
        self.advanced_analyzer = AdvancedImageAnalyzer(logger, ai_learning)
        
        # Initialize advanced number detector with EasyOCR from analyzer (AI-like intelligence)
        self.advanced_detector = AdvancedNumberDetector(logger, self.advanced_analyzer.ocr_reader)
        
        # Initialize embedded OCR
        self.embedded_ocr = None
        if not self.tesseract_available:
            from core.embedded_ocr import EmbeddedOCR
            self.embedded_ocr = EmbeddedOCR()
        
        # Check for bundled Tesseract or system Tesseract
        self._initialize_tesseract()
        
        # If no Tesseract, use embedded OCR
        if not self.tesseract_available:
            self._log_info("Using embedded OCR engine (no external installation required)")
    
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
    
    def process_batch(self, pages: List[PageInfo]) -> List[OCRResult]:
        """Process multiple pages with OCR"""
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
                self.logger.info(f"   Advanced detector exists: {self.advanced_detector is not None}")
                self.logger.info(f"   Image loaded: {image.size}")
            
            # PRIORITY FIX: Use advanced AI detector FIRST (corner/margin detection)
            # This prevents content numbers from polluting the results
            ai_candidate = self.advanced_detector.detect_page_number(
                image, "", str(page_info.file_path)
            )
            
            if self.logger:
                self.logger.info(f"✅ ADVANCED DETECTOR RETURNED: {ai_candidate}")
            
            if self.logger:
                if ai_candidate:
                    self.logger.debug(f"🎯 Advanced detector found: {ai_candidate.number} (confidence: {ai_candidate.confidence}%)")
                else:
                    self.logger.debug(f"❌ Advanced detector found nothing")
            
            if ai_candidate and ai_candidate.confidence > 50:  # Lowered from 60 to 50
                # AI found page number in corners/margins - USE IT!
                if self.logger:
                    self.logger.info(f"🤖 AI detected page {ai_candidate.number} in {ai_candidate.location}")
                
                # Create result with ONLY the AI-detected number (ignore content numbers)
                ai_detected_number = DetectedNumber(
                    text=ai_candidate.text,
                    number_type='roman' if any(c in ai_candidate.text.lower() for c in 'ivxlcdm') else 'arabic',
                    numeric_value=ai_candidate.number,
                    confidence=ai_candidate.confidence,
                    position=(0, 0, 0, 0),  # Position not used in numbering system
                    context=f"AI: {', '.join(ai_candidate.reasoning)}"
                )
                
                result = OCRResult(
                    page_info=page_info,
                    full_text="",  # Don't need full text if we found page number
                    detected_numbers=[ai_detected_number],
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
        """Process with embedded OCR (no external dependencies)"""
        try:
            # Use embedded OCR engine
            full_text = self.embedded_ocr.extract_text(image)
            
            # Use advanced analyzer for challenging images
            if self.config.get('ocr.use_advanced_analysis', True):
                advanced_result = self.advanced_analyzer.analyze_image_comprehensively(
                    image, page_info.original_name)
                
                if advanced_result.best_page_number and advanced_result.overall_confidence > 0.6:
                    self._log_info(f"✨ Advanced analysis found: {advanced_result.best_page_number} "
                                 f"(confidence: {advanced_result.overall_confidence:.1%})")
                    
                    # Convert advanced results to DetectedNumber objects
                    detected_numbers = []
                    for i, page_num in enumerate(advanced_result.page_numbers):
                        detected_numbers.append(DetectedNumber(
                            text=page_num,
                            number_type='arabic' if page_num.isdigit() else 'mixed',
                            numeric_value=int(page_num) if page_num.isdigit() else None,
                            confidence=advanced_result.confidence_scores[i] * 100,
                            position=advanced_result.text_positions[i] if i < len(advanced_result.text_positions) else (0, 0, 100, 30),
                            context=f"Advanced analysis: {advanced_result.text_orientations[i] if i < len(advanced_result.text_orientations) else 'unknown'}"
                        ))
                else:
                    # Fallback to standard embedded OCR
                    detected_numbers_data = self.embedded_ocr.detect_page_numbers(full_text, page_info.original_name)
                    
                    # Convert to DetectedNumber objects
                    detected_numbers = []
                    for num_data in detected_numbers_data:
                        detected_numbers.append(DetectedNumber(
                            text=num_data['text'],
                            number_type=num_data['type'],
                            numeric_value=num_data.get('value'),
                            confidence=num_data['confidence'],
                            position=(0, 0, 100, 30),  # Dummy position
                            context=num_data.get('context', '')
                        ))
            else:
                # Standard embedded OCR
                detected_numbers_data = self.embedded_ocr.detect_page_numbers(full_text, page_info.original_name)
                
                # Convert to DetectedNumber objects
                detected_numbers = []
                for num_data in detected_numbers_data:
                    detected_numbers.append(DetectedNumber(
                        text=num_data['text'],
                        number_type=num_data['type'],
                        numeric_value=num_data.get('value'),
                        confidence=num_data['confidence'],
                        position=(0, 0, 100, 30),  # Dummy position
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
