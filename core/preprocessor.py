"""
Image preprocessing system for AI Page Reordering Automation System
Handles denoising, deskewing, contrast enhancement, and watermark reduction
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import List, Optional, Tuple, Dict, Any
from skimage import transform, filters, morphology
from skimage.feature import canny
from skimage.transform import hough_line, hough_line_peaks
import math

from .input_handler import PageInfo
from utils.config import config
from .crop_validator import CropValidator
from .interactive_cropper import InteractiveCropper

class Preprocessor:
    """Image preprocessing with various enhancement options"""
    
    def __init__(self, logger):
        self.logger = logger
        self.config = config
        self.crop_validator = CropValidator(logger)
        self.interactive_cropper = InteractiveCropper(logger)
    
    def process_batch(self, pages: List[PageInfo], workers: int = 1) -> List[PageInfo]:
        """Process a batch of pages with enhanced memory management (supports multi-threading)
        
        Args:
            pages: List of pages to process
            workers: Number of worker threads (1 = sequential, 2+ = parallel)
        
        Returns:
            List of processed pages
        """
        import gc
        import psutil
        
        # Determine optimal batch size based on available memory
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        if available_memory_gb < 2:
            memory_check_interval = 10  # Check every 10 pages if low memory
        elif available_memory_gb < 4:
            memory_check_interval = 25  # Check every 25 pages if medium memory
        else:
            memory_check_interval = 50  # Check every 50 pages if high memory
        
        if workers > 1:
            # Multi-threaded processing
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            if self.logger:
                self.logger.info(f"⚡ Using {workers} workers for parallel preprocessing")
            
            processed_pages = [None] * len(pages)  # Pre-allocate results list
            
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
                            self.logger.info("Processing cancelled by user")
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    
                    idx = future_to_index[future]
                    try:
                        processed_pages[idx] = future.result()
                        completed += 1
                        if self.logger:
                            self.logger.progress("Preprocessing", completed, len(pages))
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Failed to preprocess page {idx}: {str(e)}")
                        # Keep original page if preprocessing fails
                        processed_pages[idx] = pages[idx]
                    
                    # Periodic memory check
                    if completed % memory_check_interval == 0:
                        gc.collect()
                        current_memory_gb = psutil.virtual_memory().available / (1024**3)
                        if current_memory_gb < 1:
                            if self.logger:
                                self.logger.warning(f"Low memory detected: {current_memory_gb:.1f}GB available")
            
            return processed_pages
        
        else:
            # Sequential processing (original behavior)
            processed_pages = []
            
            for i, page in enumerate(pages):
                # Check for cancellation
                if hasattr(self, 'cancel_processing') and self.cancel_processing:
                    self.logger.info("Processing cancelled by user")
                    break
                    
                self.logger.progress("Preprocessing", i + 1, len(pages))
                
                try:
                    processed_page = self.process_page(page)
                    processed_pages.append(processed_page)
                except Exception as e:
                    self.logger.error(f"Failed to preprocess {page.original_name}: {str(e)}")
                    # Keep original page if preprocessing fails
                    processed_pages.append(page)
            
            # Enhanced memory management
            if (i + 1) % memory_check_interval == 0:
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > 75:  # If using >75% RAM
                    self.logger.info(f"Memory usage high ({memory_percent:.1f}%), cleaning up...")
                    gc.collect()
                    # Force more aggressive cleanup if still high
                    if psutil.virtual_memory().percent > 85:
                        import ctypes
                        ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
        
        return processed_pages
    
    def process_page(self, page: PageInfo) -> PageInfo:
        """Process a single page with all enabled preprocessing steps"""
        if not page.image:
            self.logger.warning(f"No image data for {page.original_name}")
            return page
        
        processed_image = page.image.copy()
        
        # Optimize image size for performance (maintain quality but reduce memory)
        processed_image = self._optimize_image_size(processed_image)
        
        # Convert PIL Image to numpy array for OpenCV operations
        cv_image = cv2.cvtColor(np.array(processed_image), cv2.COLOR_RGB2BGR)
        
        processing_steps = []
        rotation_angle = 0
        
        # Step 1: Auto-rotate (fix orientation)
        if self.config.get('preprocessing.auto_rotate', False):
            cv_image, rotation_angle = self._auto_rotate_image(cv_image)
            if rotation_angle != 0:
                processing_steps.append(f"auto_rotate({rotation_angle}°)")
        
        # Auto crop if enabled with validation
        if self.config.get('preprocessing.auto_crop', False):
            original_cv_image = cv_image.copy()
            cv_image = self._auto_crop_image(cv_image)
            
            # Validate crop quality
            validation = self.crop_validator.validate_crop(
                original_cv_image, cv_image, page.original_name
            )
            
            if validation['needs_review']:
                processing_steps.append(f"auto_crop(⚠️{validation['confidence']:.0f}%)")
            else:
                processing_steps.append("auto_crop")
        
        # Clean dark circles if enabled  
        if self.config.get('preprocessing.clean_dark_circles', False):
            cv_image = self._clean_dark_circles(cv_image)
            processing_steps.append("clean_dark_circles")
        
        # Step 3: Deskewing
        if self.config.get('preprocessing.deskew', True):
            cv_image, angle = self._deskew_image(cv_image)
            if abs(angle) > 0.5:  # Only log if significant rotation
                processing_steps.append(f"deskew({angle:.1f}°)")
        
        # Step 3: Contrast Enhancement
        if self.config.get('preprocessing.contrast_enhance', False):
            cv_image = self._enhance_contrast(cv_image)
            processing_steps.append("contrast")
        
        # Step 4: Watermark Reduction
        if self.config.get('preprocessing.watermark_reduction', False):
            cv_image = self._reduce_watermarks(cv_image)
            processing_steps.append("watermark_reduction")
        
        # Convert back to PIL Image
        processed_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
        
        # Create new PageInfo with processed image
        processed_page = PageInfo(page.file_path, page.page_number, processed_image)
        processed_page.metadata = page.metadata.copy()
        processed_page.metadata['preprocessing'] = processing_steps
        processed_page.processing_history = page.processing_history + processing_steps
        
        if processing_steps:
            self.logger.debug(f"Processed {page.original_name}: {', '.join(processing_steps)}")
        
        return processed_page
    
    def _auto_rotate_image(self, image: np.ndarray) -> Tuple[np.ndarray, int]:
        """Automatically detect and fix page orientation (portrait vs landscape)"""
        height, width = image.shape[:2]
        
        # Convert to grayscale for analysis
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Detect text orientation using edge density
        # Check if image needs rotation by analyzing text direction
        
        # Calculate edge density in different orientations
        edges = cv2.Canny(gray, 50, 150)
        
        # Count horizontal and vertical edges
        horizontal_edges = np.sum(edges, axis=1)  # Sum along rows
        vertical_edges = np.sum(edges, axis=0)    # Sum along columns
        
        h_variance = np.var(horizontal_edges)
        v_variance = np.var(vertical_edges)
        
        # If image is landscape but should be portrait (or vice versa)
        # Typical document pages have more horizontal text lines
        rotation_angle = 0
        
        # Check if image is sideways (90° or 270°)
        if width > height * 1.3:  # Landscape orientation
            # Check if it should be portrait
            if h_variance < v_variance * 0.7:  # Text is vertical
                # Rotate 90° clockwise or counter-clockwise
                # Try both and pick the one with better text orientation
                rotation_angle = 270  # or 90, depending on detection
        elif height > width * 1.3:  # Portrait orientation
            # Check if it should be landscape
            if v_variance < h_variance * 0.7:  # Text is horizontal
                rotation_angle = 90
        
        # Apply rotation if needed
        if rotation_angle != 0:
            if rotation_angle == 90:
                rotated = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            elif rotation_angle == 180:
                rotated = cv2.rotate(image, cv2.ROTATE_180)
            elif rotation_angle == 270:
                rotated = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            else:
                rotated = image
            return rotated, rotation_angle
        
        return image, 0
    
    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """Remove noise from image using various denoising techniques"""
        # Use Non-local Means Denoising for colored images
        if len(image.shape) == 3:
            denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        else:
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        
        return denoised
    
    def _deskew_image(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """Detect and correct skew in the image"""
        # Convert to grayscale for skew detection
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Use Hough Line Transform to detect lines
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            # Calculate angles of detected lines
            angles = []
            for rho, theta in lines[:min(20, len(lines)), 0]:  # Use first 20 lines max
                angle = theta - np.pi/2  # Convert to rotation angle
                angle_deg = np.degrees(angle)
                
                # Filter out nearly vertical lines (likely text lines)
                if -45 <= angle_deg <= 45:
                    angles.append(angle_deg)
            
            if angles:
                # Use median angle to avoid outliers
                skew_angle = np.median(angles)
                
                # Only correct if skew is significant
                if abs(skew_angle) > 0.5:
                    # Rotate image to correct skew
                    height, width = image.shape[:2]
                    center = (width // 2, height // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, -skew_angle, 1.0)
                    
                    # Calculate new image dimensions
                    cos_angle = abs(rotation_matrix[0, 0])
                    sin_angle = abs(rotation_matrix[0, 1])
                    new_width = int((height * sin_angle) + (width * cos_angle))
                    new_height = int((height * cos_angle) + (width * sin_angle))
                    
                    # Adjust rotation matrix for new dimensions
                    rotation_matrix[0, 2] += (new_width / 2) - center[0]
                    rotation_matrix[1, 2] += (new_height / 2) - center[1]
                    
                    # Apply rotation
                    deskewed = cv2.warpAffine(image, rotation_matrix, (new_width, new_height), 
                                            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                    
                    return deskewed, skew_angle
        
        return image, 0.0
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE"""
        # Convert to LAB color space for better contrast enhancement
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l)
            
            # Merge channels back
            enhanced_lab = cv2.merge([l_enhanced, a, b])
            enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        else:
            # For grayscale images
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
        
        return enhanced
    
    def _reduce_watermarks(self, image: np.ndarray) -> np.ndarray:
        """Attempt to reduce watermarks and background patterns"""
        if len(image.shape) == 3:
            # Convert to grayscale for watermark detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Create mask for potential watermark areas (light/faded regions)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours of text regions
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create mask for main content
        content_mask = np.zeros_like(gray)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Filter small noise
                cv2.fillPoly(content_mask, [contour], 255)
        
        # Apply morphological operations to clean up mask
        kernel = np.ones((3, 3), np.uint8)
        content_mask = cv2.morphologyEx(content_mask, cv2.MORPH_CLOSE, kernel)
        content_mask = cv2.morphologyEx(content_mask, cv2.MORPH_OPEN, kernel)
        
        # Apply gentle enhancement to non-content areas (potential watermarks)
        if len(image.shape) == 3:
            result = image.copy()
            for i in range(3):  # Process each color channel
                channel = image[:, :, i]
                # Slightly brighten areas outside main content
                watermark_areas = cv2.bitwise_not(content_mask)
                enhanced_channel = cv2.addWeighted(channel, 1.0, watermark_areas, 0.1, 0)
                result[:, :, i] = enhanced_channel
        else:
            watermark_areas = cv2.bitwise_not(content_mask)
            result = cv2.addWeighted(image, 1.0, watermark_areas, 0.1, 0)
        
        return result
    
    def get_preprocessing_options(self) -> Dict[str, Any]:
        """Get current preprocessing configuration"""
        return {
            'denoise': self.config.get('preprocessing.denoise', True),
            'deskew': self.config.get('preprocessing.deskew', True),
            'contrast_enhance': self.config.get('preprocessing.contrast_enhance', False),
            'watermark_reduction': self.config.get('preprocessing.watermark_reduction', False)
        }
    
    def set_preprocessing_options(self, options: Dict[str, bool]) -> None:
        """Update preprocessing configuration"""
        for key, value in options.items():
            if key in ['denoise', 'deskew', 'contrast_enhance', 'watermark_reduction']:
                self.config.set(f'preprocessing.{key}', value)
        
        self.config.save()
    
    def analyze_image_quality(self, page: PageInfo) -> Dict[str, Any]:
        """Analyze image quality and suggest preprocessing options"""
        if not page.image:
            return {'error': 'No image data'}
        
        # Convert to numpy array
        cv_image = cv2.cvtColor(np.array(page.image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        analysis = {
            'resolution': page.image.size,
            'aspect_ratio': page.image.size[0] / page.image.size[1],
            'suggested_preprocessing': []
        }
        
        # Check for blur/noise
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        analysis['sharpness'] = laplacian_var
        if laplacian_var < 100:
            analysis['suggested_preprocessing'].append('denoise')
        
        # Check for skew
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        if lines is not None:
            angles = []
            for rho, theta in lines[:10, 0]:
                angle = np.degrees(theta - np.pi/2)
                if -45 <= angle <= 45:
                    angles.append(angle)
            
            if angles:
                skew = abs(np.median(angles))
                analysis['estimated_skew'] = skew
                if skew > 1.0:
                    analysis['suggested_preprocessing'].append('deskew')
        
        # Check contrast
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        contrast = np.std(hist)
        analysis['contrast'] = contrast
        if contrast < 50:
            analysis['suggested_preprocessing'].append('contrast_enhance')
        
        return analysis
    
    def _auto_crop_image(self, image):
        """Automatically crop image to remove borders and margins"""
        try:
            # Image is already in OpenCV format (NumPy array)
            cv_image = image if isinstance(image, np.ndarray) else cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply threshold to get binary image
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Invert if background is dark
            if np.mean(binary) < 127:
                binary = cv2.bitwise_not(binary)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Find the largest contour (main content)
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # Add generous padding to avoid cutting content (even slightly)
                padding = 50  # Increased from 20 to 50 pixels for safety
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(cv_image.shape[1] - x, w + 2 * padding)
                h = min(cv_image.shape[0] - y, h + 2 * padding)
                
                # Crop the image
                cropped = cv_image[y:y+h, x:x+w]
                
                # Return NumPy array (OpenCV format)
                return cropped
            
            return cv_image
            
        except Exception as e:
            self.logger.warning(f"Auto crop failed: {e}")
            return cv_image if isinstance(image, np.ndarray) else image
    
    def _clean_dark_circles(self, image):
        """Remove dark circles and spots from scanned pages"""
        try:
            # Image is already in OpenCV format (NumPy array)
            cv_image = image if isinstance(image, np.ndarray) else cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect dark circular regions
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=30,
                param1=50,
                param2=30,
                minRadius=5,
                maxRadius=50
            )
            
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                
                # Create mask for dark circles
                mask = np.zeros(gray.shape, dtype=np.uint8)
                
                for (x, y, r) in circles:
                    # Check if circle is dark (potential dirt/mark)
                    circle_region = gray[max(0, y-r):min(gray.shape[0], y+r), 
                                       max(0, x-r):min(gray.shape[1], x+r)]
                    
                    if circle_region.size > 0:
                        avg_intensity = np.mean(circle_region)
                        
                        # If circle is significantly darker than average
                        if avg_intensity < np.mean(gray) * 0.7:
                            cv2.circle(mask, (x, y), r, 255, -1)
                
                # Inpaint dark circles
                if np.any(mask):
                    result = cv2.inpaint(cv_image, mask, 3, cv2.INPAINT_TELEA)
                    return result
            
            # Alternative: Remove small dark spots using morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            
            # Apply threshold to find dark spots
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Invert to make dark spots white
            binary_inv = cv2.bitwise_not(binary)
            
            # Remove small components (noise/spots)
            cleaned = cv2.morphologyEx(binary_inv, cv2.MORPH_OPEN, kernel)
            
            # Create mask for spots to remove
            spots_mask = cv2.bitwise_xor(binary_inv, cleaned)
            
            # Inpaint spots
            if np.any(spots_mask):
                result = cv2.inpaint(cv_image, spots_mask, 3, cv2.INPAINT_NS)
                return result
            
            return cv_image
            
        except Exception as e:
            self.logger.warning(f"Clean dark circles failed: {e}")
            return cv_image if isinstance(image, np.ndarray) else image
    
    def _optimize_image_size(self, image, max_dimension=2500):
        """Optimize image size for better performance while maintaining quality"""
        try:
            width, height = image.size
            # Only resize if image is very large
            if max(width, height) > max_dimension:
                # Calculate new size maintaining aspect ratio
                if width > height:
                    new_width = max_dimension
                    new_height = int((height * max_dimension) / width)
                else:
                    new_height = max_dimension
                    new_width = int((width * max_dimension) / height)
                
                # Use high-quality resampling
                resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Log the optimization
                original_size = width * height
                new_size = new_width * new_height
                reduction = ((original_size - new_size) / original_size) * 100
                
                if self.logger:
                    self.logger.debug(f"Optimized image: {width}x{height} → {new_width}x{new_height} ({reduction:.1f}% reduction)")
                
                return resized_image
            
            return image
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Image optimization failed: {e}")
            return image
    
    def generate_crop_reports(self, output_dir):
        """Generate crop validation reports if auto-crop was used"""
        if self.config.get('preprocessing.auto_crop', False):
            return self.crop_validator.generate_review_report(output_dir)
    
    def handle_manual_cropping(self, pages: List[PageInfo]) -> List[PageInfo]:
        """
        Handle interactive manual cropping for problematic pages
        Pauses processing and shows GUI for user to manually crop
        """
        if not self.crop_validator.problematic_pages:
            return pages  # No problematic pages
        
        # Check if interactive mode is enabled
        if not self.config.get('preprocessing.interactive_crop', False):
            self.logger.info("ℹ️ Interactive cropping disabled - see CROP_REVIEW_NEEDED.txt for manual review")
            return pages
        
        self.logger.info(f"🔧 {len(self.crop_validator.problematic_pages)} pages need manual cropping")
        self.logger.info("⏸️ Pausing processing for manual crop...")
        
        # Prepare images dict
        images_dict = {page.original_name: page.image for page in pages if page.image}
        
        # Show interactive cropping interface
        try:
            crop_results = self.interactive_cropper.show_cropping_interface(
                self.crop_validator.problematic_pages,
                images_dict
            )
            
            if crop_results is None:
                # User cancelled
                self.logger.warning("❌ Manual cropping cancelled by user")
                return None
            
            if not crop_results:
                # User skipped all
                self.logger.info("ℹ️ All pages skipped - keeping auto-crop results")
                return pages
            
            # Apply manual crops
            self.logger.info(f"✂️ Applying manual crops to {len(crop_results)} pages")
            cropped_pages = []
            
            for page in pages:
                if page.original_name in crop_results:
                    # Apply manual crop
                    x1, y1, x2, y2 = crop_results[page.original_name]
                    cropped_image = page.image.crop((x1, y1, x2, y2))
                    
                    # Create new page with cropped image
                    cropped_page = PageInfo(page.file_path, page.page_number, cropped_image)
                    cropped_page.metadata = page.metadata.copy()
                    cropped_page.metadata['manual_crop'] = True
                    cropped_page.processing_history = page.processing_history + ['manual_crop']
                    cropped_pages.append(cropped_page)
                    
                    self.logger.debug(f"✅ {page.original_name}: Manual crop applied")
                else:
                    # Keep original
                    cropped_pages.append(page)
            
            self.logger.info("✅ Manual cropping complete - resuming processing")
            return cropped_pages
            
        except Exception as e:
            self.logger.error(f"Manual cropping failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return pages  # Return original pages on error
