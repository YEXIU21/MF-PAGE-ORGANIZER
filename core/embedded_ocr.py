"""
Embedded OCR Engine - Works without external Tesseract installation
Uses EasyOCR which can be bundled with the executable
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import re

class EmbeddedOCR:
    """Standalone OCR that works without external dependencies"""
    
    def __init__(self):
        self.ocr_engine = None
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize EasyOCR engine"""
        try:
            import easyocr
            # Initialize with English language
            self.ocr_engine = easyocr.Reader(['en'], gpu=False, verbose=False)
            print("✅ EasyOCR initialized successfully")
        except ImportError:
            print("⚠️  EasyOCR not available, using fallback pattern matching")
            self.ocr_engine = None
        except Exception as e:
            print(f"⚠️  Could not initialize EasyOCR: {e}")
            self.ocr_engine = None
    
    def extract_text(self, image: Image.Image) -> str:
        """Extract text from image"""
        if self.ocr_engine:
            return self._extract_with_easyocr(image)
        else:
            return self._extract_with_fallback(image)
    
    def _extract_with_easyocr(self, image: Image.Image) -> str:
        """Extract text using EasyOCR"""
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # Run OCR
            results = self.ocr_engine.readtext(img_array)
            
            # Combine all detected text
            text_parts = [result[1] for result in results]
            full_text = ' '.join(text_parts)
            
            return full_text
            
        except Exception as e:
            print(f"EasyOCR failed: {e}, using fallback")
            return self._extract_with_fallback(image)
    
    def _extract_with_fallback(self, image: Image.Image) -> str:
        """Fallback method using image processing to detect numbers"""
        try:
            # Convert to grayscale
            img_array = np.array(image.convert('L'))
            
            # Apply thresholding
            _, thresh = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # This is a simplified fallback - just returns empty string
            # The numbering system will use pattern matching on filenames
            return ""
            
        except Exception as e:
            print(f"Fallback OCR failed: {e}")
            return ""
    
    def detect_page_numbers(self, text: str, filename: str = "") -> List[Dict[str, Any]]:
        """Detect page numbers from text or filename"""
        numbers = []
        
        # Try to extract from text first
        if text:
            numbers.extend(self._extract_numbers_from_text(text))
        
        # Try to extract from filename
        if filename:
            numbers.extend(self._extract_numbers_from_filename(filename))
        
        return numbers
    
    def _extract_numbers_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract numbers from OCR text"""
        numbers = []
        
        # Arabic numbers (1, 2, 3, etc.)
        arabic_pattern = r'\b(\d+)\b'
        for match in re.finditer(arabic_pattern, text):
            numbers.append({
                'text': match.group(1),
                'value': int(match.group(1)),
                'type': 'arabic',
                'confidence': 0.8
            })
        
        # Roman numerals
        roman_pattern = r'\b([ivxlcdm]+)\b'
        for match in re.finditer(roman_pattern, text.lower()):
            roman_value = self._roman_to_int(match.group(1))
            if roman_value:
                numbers.append({
                    'text': match.group(1),
                    'value': roman_value,
                    'type': 'roman',
                    'confidence': 0.7
                })
        
        return numbers
    
    def _extract_numbers_from_filename(self, filename: str) -> List[Dict[str, Any]]:
        """Extract numbers from filename"""
        numbers = []
        
        # Look for numbers in filename
        number_pattern = r'(\d+)'
        matches = re.findall(number_pattern, filename)
        
        if matches:
            # Use the last number found (usually the page number)
            last_number = matches[-1]
            numbers.append({
                'text': last_number,
                'value': int(last_number),
                'type': 'filename',
                'confidence': 0.9
            })
        
        return numbers
    
    def _roman_to_int(self, s: str) -> Optional[int]:
        """Convert Roman numeral to integer"""
        roman_values = {
            'i': 1, 'v': 5, 'x': 10, 'l': 50,
            'c': 100, 'd': 500, 'm': 1000
        }
        
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
        
        # Validate result (Roman numerals typically 1-3999)
        if 1 <= total <= 3999:
            return total
        return None
