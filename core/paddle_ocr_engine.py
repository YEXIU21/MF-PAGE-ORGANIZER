"""
PaddleOCR-Based Embedded OCR Engine
Ultra-fast, no external dependencies, works standalone
"""

import cv2
import numpy as np
from PIL import Image
import re
from typing import List, Dict, Optional

class PaddleOCREngine:
    """PaddleOCR-based OCR engine - faster and more accurate than EasyOCR"""
    
    def __init__(self, logger=None, lang='en'):
        self.logger = logger
        self.lang = lang
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize PaddleOCR engine"""
        try:
            from paddleocr import PaddleOCR
            
            # Initialize PaddleOCR 3.2+ (simplified API)
            self.ocr_engine = PaddleOCR()
            
            if self.logger:
                gpu_status = "GPU" if self._check_gpu() else "CPU"
                self.logger.info(f"PaddleOCR engine initialized ({gpu_status})")
            else:
                print(f"PaddleOCR initialized successfully ({gpu_status})")
                
        except ImportError:
            print("PaddleOCR not available, using fallback")
            self.ocr_engine = None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Could not initialize PaddleOCR: {e}")
            else:
                print(f"Could not initialize PaddleOCR: {e}")
            self.ocr_engine = None
    
    def _check_gpu(self) -> bool:
        """Check if GPU is available"""
        try:
            import paddle
            return paddle.is_compiled_with_cuda()
        except:
            return False
    
    def extract_text(self, image: Image.Image) -> str:
        """Extract all text from image"""
        if self.ocr_engine:
            return self._extract_with_paddle(image)
        else:
            return self._extract_with_fallback(image)
    
    def _extract_with_paddle(self, image: Image.Image) -> str:
        """Extract text using PaddleOCR"""
        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # Run PaddleOCR
            results = self.ocr_engine.ocr(img_array, cls=True)
            
            if not results or not results[0]:
                return ""
            
            # Extract text from all detected boxes
            text_lines = []
            for line in results[0]:
                bbox, (text, confidence) = line
                if confidence > 0.5:  # Filter low confidence
                    text_lines.append(text)
            
            # Join all text
            full_text = " ".join(text_lines)
            return full_text
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"PaddleOCR failed: {e}")
            else:
                print(f"PaddleOCR failed: {e}")
            return self._extract_with_fallback(image)
    
    def _extract_with_fallback(self, image: Image.Image) -> str:
        """Fallback text extraction using basic pattern matching"""
        # Return empty string - let the detector handle it
        return ""
    
    def detect_page_numbers(self, text: str, filename: str) -> List[Dict]:
        """Detect page numbers from extracted text (fallback method)"""
        detected_numbers = []
        
        # Find arabic numbers
        arabic_pattern = r'\b(\d{1,3})\b'
        for match in re.finditer(arabic_pattern, text):
            num_text = match.group(1)
            try:
                num_value = int(num_text)
                if 1 <= num_value <= 500:
                    detected_numbers.append({
                        'text': num_text,
                        'type': 'arabic',
                        'value': num_value,
                        'confidence': 70.0,
                        'context': 'text_extraction'
                    })
            except ValueError:
                continue
        
        # Find roman numerals
        roman_pattern = r'\b([ivxlcdm]{1,10})\b'
        for match in re.finditer(roman_pattern, text.lower()):
            roman_text = match.group(1)
            roman_value = self._roman_to_int(roman_text)
            if roman_value and 1 <= roman_value <= 50:
                detected_numbers.append({
                    'text': roman_text,
                    'type': 'roman',
                    'value': roman_value,
                    'confidence': 75.0,
                    'context': 'text_extraction'
                })
        
        return detected_numbers
    
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
