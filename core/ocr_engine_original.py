"""
OCR and number extraction system for AI Page Reordering Automation System
Supports various numbering formats: Arabic, Roman, hybrid, hierarchical
"""

import re
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from PIL import Image
import pytesseract
from dataclasses import dataclass

from .input_handler import PageInfo
from utils.config import config

@dataclass
class NumberInfo:
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
    detected_numbers: List[NumberInfo]
    text_blocks: List[Dict[str, Any]]
    language_confidence: float
    processing_time: float

class OCREngine:
    """Advanced OCR system with number detection capabilities"""
    
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
    
    # Hybrid patterns (e.g., 1-a, 2-b, Chapter 1, etc.)
    HYBRID_PATTERNS = {
        'number_letter': r'\b\d+[-\s]*[a-z]\b',
        'chapter_number': r'\b(?:chapter|ch|section|sec|part|pt)[\s\-\.]*\d+\b',
        'page_number': r'\b(?:page|p|pg)[\s\-\.]*\d+\b',
        'appendix': r'\b(?:appendix|app)[\s\-\.]*[a-z]\b'
    }
    
    # Hierarchical patterns (e.g., 10.1, 2.3.4, etc.)
    HIERARCHICAL_PATTERNS = {
        'two_level': r'\b\d+\.\d+\b',
        'three_level': r'\b\d+\.\d+\.\d+\b',
        'four_level': r'\b\d+\.\d+\.\d+\.\d+\b'
    }
    
    def __init__(self, logger):
        self.logger = logger
        self.config = config
        self._setup_tesseract()
    
    def _setup_tesseract(self):
        """Configure Tesseract OCR settings"""
        # Try to set Tesseract path if needed (Windows)
        try:
            tesseract_cmd = self.config.get('ocr.tesseract_path')
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        except:
            pass  # Use default path
    
    def process_batch(self, pages: List[PageInfo]) -> List[OCRResult]:
        """Process multiple pages with OCR"""
        results = []
        
        for i, page in enumerate(pages):
            self.logger.progress("OCR Processing", i + 1, len(pages))
            
            try:
                result = self.process_page(page)
                results.append(result)
            except Exception as e:
                self.logger.error(f"OCR failed for {page.original_name}: {str(e)}")
                # Create empty result for failed pages
                empty_result = OCRResult(
                    page_info=page,
                    full_text="",
                    detected_numbers=[],
                    text_blocks=[],
                    language_confidence=0.0,
                    processing_time=0.0
                )
                results.append(empty_result)
        
        return results
    
    def process_page(self, page: PageInfo) -> OCRResult:
        """Process a single page with OCR and extract numbers"""
        import time
        start_time = time.time()
        
        if not page.image:
            raise ValueError("No image data available")
        
        # Convert PIL Image to numpy array for OCR
        cv_image = cv2.cvtColor(np.array(page.image), cv2.COLOR_RGB2BGR)
        
        # Perform OCR with detailed data
        ocr_config = self._get_tesseract_config()
        
        # Get full text
        full_text = pytesseract.image_to_string(cv_image, config=ocr_config)
        
        # Get detailed OCR data (words with positions and confidence)
        ocr_data = pytesseract.image_to_data(cv_image, config=ocr_config, output_type=pytesseract.Output.DICT)
        
        # Extract text blocks with positions
        text_blocks = self._extract_text_blocks(ocr_data)
        
        # Detect and classify numbers
        detected_numbers = self._detect_numbers(full_text, text_blocks)
        
        # Calculate average confidence
        confidences = [float(conf) for conf in ocr_data['conf'] if int(conf) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        processing_time = time.time() - start_time
        
        result = OCRResult(
            page_info=page,
            full_text=full_text.strip(),
            detected_numbers=detected_numbers,
            text_blocks=text_blocks,
            language_confidence=avg_confidence,
            processing_time=processing_time
        )
        
        self.logger.debug(f"OCR completed for {page.original_name}: "
                         f"{len(detected_numbers)} numbers found, "
                         f"{avg_confidence:.1f}% confidence")
        
        return result
    
    def _get_tesseract_config(self) -> str:
        """Get Tesseract configuration string"""
        lang = self.config.get('ocr.language', 'eng')
        engine_mode = self.config.get('ocr.engine_mode', 3)
        page_seg = self.config.get('ocr.page_segmentation', 6)
        
        config_str = f'--oem {engine_mode} --psm {page_seg} -l {lang}'
        
        # Add whitelist for better number detection if needed
        if self.config.get('ocr.numbers_only', False):
            config_str += ' -c tessedit_char_whitelist=0123456789IVXLCDMivxlcdm.-'
        
        return config_str
    
    def _extract_text_blocks(self, ocr_data: Dict) -> List[Dict[str, Any]]:
        """Extract text blocks with position and confidence information"""
        text_blocks = []
        
        for i in range(len(ocr_data['text'])):
            if int(ocr_data['conf'][i]) > 30:  # Filter low confidence text
                block = {
                    'text': ocr_data['text'][i].strip(),
                    'confidence': float(ocr_data['conf'][i]),
                    'position': (
                        int(ocr_data['left'][i]),
                        int(ocr_data['top'][i]),
                        int(ocr_data['width'][i]),
                        int(ocr_data['height'][i])
                    ),
                    'block_num': int(ocr_data['block_num'][i]),
                    'par_num': int(ocr_data['par_num'][i]),
                    'line_num': int(ocr_data['line_num'][i]),
                    'word_num': int(ocr_data['word_num'][i])
                }
                if block['text']:  # Only add non-empty text
                    text_blocks.append(block)
        
        return text_blocks
    
    def _detect_numbers(self, full_text: str, text_blocks: List[Dict]) -> List[NumberInfo]:
        """Detect and classify various types of numbers"""
        numbers = []
        
        # Create combined text with position mapping for context
        text_with_positions = [(block['text'], block['position'], block['confidence']) 
                              for block in text_blocks]
        
        # Detect Arabic numbers
        if self.config.get('numbering.detect_arabic', True):
            numbers.extend(self._find_arabic_numbers(full_text, text_with_positions))
        
        # Detect Roman numerals
        if self.config.get('numbering.detect_roman', True):
            numbers.extend(self._find_roman_numerals(full_text, text_with_positions))
        
        # Detect hybrid formats
        if self.config.get('numbering.detect_hybrid', True):
            numbers.extend(self._find_hybrid_numbers(full_text, text_with_positions))
        
        # Detect hierarchical numbers
        if self.config.get('numbering.detect_hierarchical', True):
            numbers.extend(self._find_hierarchical_numbers(full_text, text_with_positions))
        
        # Sort by confidence and remove duplicates
        numbers = self._deduplicate_numbers(numbers)
        
        return numbers
    
    def _find_arabic_numbers(self, text: str, text_with_positions: List) -> List[NumberInfo]:
        """Find Arabic numbers (1, 2, 3, etc.)"""
        numbers = []
        
        for pattern_name, pattern in self.ARABIC_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                number_text = match.group()
                try:
                    numeric_value = int(number_text.replace(',', '').replace('.', ''))
                    if 1 <= numeric_value <= 9999:  # Reasonable page number range
                        # Find position and context
                        position, context, confidence = self._find_number_context(
                            number_text, match.start(), text_with_positions, text)
                        
                        numbers.append(NumberInfo(
                            text=number_text,
                            number_type='arabic',
                            numeric_value=numeric_value,
                            confidence=confidence * 0.9,  # Slightly lower confidence for simple numbers
                            position=position,
                            context=context
                        ))
                except ValueError:
                    continue
        
        return numbers
    
    def _find_roman_numerals(self, text: str, text_with_positions: List) -> List[NumberInfo]:
        """Find Roman numerals (i, ii, iii, I, II, III, etc.)"""
        numbers = []
        
        for case, pattern in self.ROMAN_PATTERNS.items():
            matches = re.finditer(pattern, text)
            
            for match in matches:
                roman_text = match.group()
                numeric_value = self._roman_to_int(roman_text)
                
                if numeric_value and 1 <= numeric_value <= 100:  # Reasonable range
                    position, context, confidence = self._find_number_context(
                        roman_text, match.start(), text_with_positions, text)
                    
                    numbers.append(NumberInfo(
                        text=roman_text,
                        number_type='roman',
                        numeric_value=numeric_value,
                        confidence=confidence * 0.95,  # High confidence for Roman numerals
                        position=position,
                        context=context
                    ))
        
        return numbers
    
    def _find_hybrid_numbers(self, text: str, text_with_positions: List) -> List[NumberInfo]:
        """Find hybrid format numbers (1-a, Chapter 2, etc.)"""
        numbers = []
        
        for pattern_name, pattern in self.HYBRID_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                hybrid_text = match.group()
                
                # Extract numeric part
                numeric_match = re.search(r'\d+', hybrid_text)
                if numeric_match:
                    try:
                        numeric_value = int(numeric_match.group())
                        if 1 <= numeric_value <= 9999:
                            position, context, confidence = self._find_number_context(
                                hybrid_text, match.start(), text_with_positions, text)
                            
                            # Higher confidence for structured formats
                            conf_multiplier = 1.0 if 'chapter' in pattern_name else 0.8
                            
                            numbers.append(NumberInfo(
                                text=hybrid_text,
                                number_type='hybrid',
                                numeric_value=numeric_value,
                                confidence=confidence * conf_multiplier,
                                position=position,
                                context=context
                            ))
                    except ValueError:
                        continue
        
        return numbers
    
    def _find_hierarchical_numbers(self, text: str, text_with_positions: List) -> List[NumberInfo]:
        """Find hierarchical numbers (1.1, 2.3.4, etc.)"""
        numbers = []
        
        for pattern_name, pattern in self.HIERARCHICAL_PATTERNS.items():
            matches = re.finditer(pattern, text)
            
            for match in matches:
                hierarchical_text = match.group()
                
                # Extract main number (first part)
                parts = hierarchical_text.split('.')
                try:
                    numeric_value = int(parts[0])
                    if 1 <= numeric_value <= 999:
                        position, context, confidence = self._find_number_context(
                            hierarchical_text, match.start(), text_with_positions, text)
                        
                        numbers.append(NumberInfo(
                            text=hierarchical_text,
                            number_type='hierarchical',
                            numeric_value=numeric_value,
                            confidence=confidence * 0.85,
                            position=position,
                            context=context
                        ))
                except ValueError:
                    continue
        
        return numbers
    
    def _find_number_context(self, number_text: str, text_position: int, 
                           text_with_positions: List, full_text: str) -> Tuple[Tuple[int, int, int, int], str, float]:
        """Find the position and context of a number in the text blocks"""
        # Default values
        default_position = (0, 0, 0, 0)
        default_confidence = 50.0
        
        # Extract context from full text
        context_start = max(0, text_position - 50)
        context_end = min(len(full_text), text_position + len(number_text) + 50)
        context = full_text[context_start:context_end].strip()
        
        # Find matching text block
        for text, position, confidence in text_with_positions:
            if number_text in text:
                return position, context, confidence
        
        return default_position, context, default_confidence
    
    def _roman_to_int(self, roman: str) -> Optional[int]:
        """Convert Roman numeral to integer"""
        roman = roman.upper()
        values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        
        try:
            total = 0
            prev_value = 0
            
            for char in reversed(roman):
                if char not in values:
                    return None
                
                value = values[char]
                if value >= prev_value:
                    total += value
                else:
                    total -= value
                prev_value = value
            
            return total if total > 0 else None
        except:
            return None
    
    def _deduplicate_numbers(self, numbers: List[NumberInfo]) -> List[NumberInfo]:
        """Remove duplicate numbers and keep the highest confidence ones"""
        # Group by numeric value and position proximity
        groups = {}
        
        for num in numbers:
            key = (num.numeric_value, num.position[0] // 50, num.position[1] // 50)  # Group by 50px grid
            if key not in groups:
                groups[key] = []
            groups[key].append(num)
        
        # Keep highest confidence number from each group
        deduplicated = []
        for group in groups.values():
            best_number = max(group, key=lambda x: x.confidence)
            deduplicated.append(best_number)
        
        # Sort by confidence (highest first)
        return sorted(deduplicated, key=lambda x: x.confidence, reverse=True)
    
    def get_page_numbers(self, ocr_result: OCRResult) -> List[int]:
        """Extract the most likely page numbers from OCR result"""
        if not ocr_result.detected_numbers:
            return []
        
        # Filter numbers by confidence and type priority
        priority_order = self.config.get('numbering.priority_order', ['page', 'chapter', 'section'])
        
        # Group numbers by type
        numbers_by_type = {}
        for num in ocr_result.detected_numbers:
            if num.number_type not in numbers_by_type:
                numbers_by_type[num.number_type] = []
            numbers_by_type[num.number_type].append(num)
        
        # Get best candidates based on priority
        best_numbers = []
        for priority in priority_order:
            if priority in numbers_by_type:
                # Sort by confidence and take top candidates
                candidates = sorted(numbers_by_type[priority], 
                                  key=lambda x: x.confidence, reverse=True)
                best_numbers.extend(candidates[:3])  # Top 3 from each type
                break
        
        # If no priority matches, use all high-confidence numbers
        if not best_numbers:
            best_numbers = [num for num in ocr_result.detected_numbers if num.confidence > 70]
        
        # Extract numeric values
        page_numbers = [num.numeric_value for num in best_numbers if num.numeric_value is not None]
        
        return sorted(list(set(page_numbers)))  # Remove duplicates and sort
