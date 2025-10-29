"""
Clean OCR Engine - ML-First Architecture
Simple: ML → User Confirmation → Learn
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import time
from PIL import Image
import cv2
import numpy as np

from utils.config import config
from utils.logger import ProcessLogger
from core.smart_cache import SmartCache
from core.input_handler import PageInfo

# ML Model Integration
try:
    from core.model_manager import get_model_manager
    from core.manual_input import ask_user_for_number
    from core.continuous_learner import add_to_training
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

@dataclass
class DetectedNumber:
    """Information about detected page number"""
    text: str
    number_type: str  # 'arabic', 'roman'
    numeric_value: Optional[int]
    confidence: float
    position: tuple
    context: str

@dataclass
class OCRResult:
    """Results from OCR processing"""
    page_info: PageInfo
    full_text: str
    detected_numbers: list
    text_blocks: list
    language_confidence: float
    processing_time: float

class CleanOCREngine:
    """
    Simplified OCR Engine
    Flow: ML Model → User Confirmation → Continuous Learning
    """
    
    def __init__(self, logger: Optional[ProcessLogger] = None, output_dir=None):
        self.logger = logger
        self.config = config
        
        # Smart cache
        self.smart_cache = SmartCache(logger, output_dir)
        
        # ML Model
        self.ml_model = None
        if ML_AVAILABLE:
            try:
                model_manager = get_model_manager()
                if model_manager.model_exists():
                    model_manager.load_model()
                    self.ml_model = model_manager.get_predictor()
                    if self.logger:
                        self.logger.info("✅ ML model loaded - fast mode enabled!")
                else:
                    if self.logger:
                        self.logger.info("📋 No ML model - using interactive mode")
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"ML model not available: {e}")
    
    def _extract_corners(self, image):
        """Extract corner regions for ML/user display"""
        if isinstance(image, Image.Image):
            img_array = np.array(image)
        else:
            img_array = image
        
        h, w = img_array.shape[:2]
        
        # Extract main corners
        corners = {
            'bottom_right': img_array[max(0, h-200):h, max(0, w-200):w],
            'bottom_left': img_array[max(0, h-200):h, 0:min(200, w)],
            'top_right': img_array[0:min(200, h), max(0, w-200):w],
            'bottom_center': img_array[max(0, h-200):h, max(0, w//2-100):min(w, w//2+100)]
        }
        
        return corners
    
    def _is_roman_numeral(self, text: str) -> bool:
        """Check if text is a roman numeral"""
        import re
        pattern = r'^[ivxlcdm]+$'
        return bool(re.match(pattern, text.lower()))
    
    def process_page(self, page_info: PageInfo, total_pages: int = None) -> OCRResult:
        """
        Process page with clean ML-first workflow
        
        Flow:
        1. Check cache
        2. Try ML model
        3. If ML confident → Done!
        4. If not confident → Ask user
        5. Add to continuous learning
        6. Return result
        """
        start_time = time.time()
        
        try:
            # 1. Check cache
            image_hash = self.smart_cache.get_image_hash(str(page_info.file_path))
            cached_result = self.smart_cache.get_cached_result(image_hash, 'ocr_v21_clean')
            
            if cached_result:
                if self.logger:
                    self.logger.debug(f"✨ Using cached result for {page_info.original_name}")
                return cached_result
            
            # 2. Load image
            image = Image.open(page_info.file_path)
            
            # 3. Extract corners
            corners = self._extract_corners(image)
            
            # 4. Try ML model first
            ml_number = None
            ml_confidence = 0
            
            if self.ml_model:
                if self.logger:
                    self.logger.debug(f"🤖 Trying ML model for {page_info.original_name}")
                
                # Try each corner
                for corner_name, corner_img in corners.items():
                    if corner_img.size > 0:
                        try:
                            predicted_number, confidence = self.ml_model.predict(corner_img)
                            
                            if predicted_number and confidence > ml_confidence:
                                ml_number = predicted_number
                                ml_confidence = confidence
                            
                            # High confidence? Use it!
                            if confidence > 0.85:
                                if self.logger:
                                    self.logger.info(f"✅ ML SUCCESS: '{predicted_number}' ({confidence:.0%}) for {page_info.original_name}")
                                
                                result = self._create_result(
                                    page_info,
                                    predicted_number,
                                    confidence * 100,
                                    'ML Model',
                                    start_time
                                )
                                
                                self.smart_cache.save_result(image_hash, result, 'ocr_v21_clean', result.processing_time)
                                return result
                        
                        except Exception as e:
                            if self.logger:
                                self.logger.debug(f"ML failed for {corner_name}: {e}")
            
            # 5. ML not confident - ask user
            if self.logger:
                if self.ml_model:
                    self.logger.info(f"❓ ML not confident ({ml_confidence:.0%}), asking user for {page_info.original_name}")
                else:
                    self.logger.info(f"❓ No ML model, asking user for {page_info.original_name}")
            
            user_number = ask_user_for_number(
                page_info.file_path,
                best_guess=ml_number,
                confidence=ml_confidence
            )
            
            if user_number:
                # 6. Add to continuous learning
                added = add_to_training(page_info.file_path, corners, user_number)
                
                if added and self.logger:
                    self.logger.debug(f"📚 Added to training: {user_number}")
                
                # 7. Create result
                result = self._create_result(
                    page_info,
                    user_number,
                    100,  # User input = 100% confident
                    'User Confirmed',
                    start_time
                )
                
                self.smart_cache.save_result(image_hash, result, 'ocr_v21_clean', result.processing_time)
                return result
            
            # User skipped - return empty result
            result = OCRResult(
                page_info=page_info,
                full_text="",
                detected_numbers=[],
                text_blocks=[],
                language_confidence=0.0,
                processing_time=time.time() - start_time
            )
            
            return result
        
        except Exception as e:
            import traceback
            if self.logger:
                self.logger.error(f"OCR failed for {page_info.original_name}: {e}")
                self.logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            return OCRResult(
                page_info=page_info,
                full_text="",
                detected_numbers=[],
                text_blocks=[],
                language_confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    def _create_result(self, page_info, number_text, confidence, method, start_time):
        """Create OCR result"""
        # Determine type
        if self._is_roman_numeral(number_text):
            number_type = 'roman'
        else:
            number_type = 'arabic'
        
        # Parse numeric value
        try:
            numeric_value = int(number_text) if number_text.isdigit() else None
        except:
            numeric_value = None
        
        detected_numbers = [DetectedNumber(
            text=number_text,
            number_type=number_type,
            numeric_value=numeric_value,
            confidence=confidence,
            position=(0, 0, 100, 30),
            context=method
        )]
        
        return OCRResult(
            page_info=page_info,
            full_text="",
            detected_numbers=detected_numbers,
            text_blocks=[],
            language_confidence=confidence / 100.0,
            processing_time=time.time() - start_time
        )
