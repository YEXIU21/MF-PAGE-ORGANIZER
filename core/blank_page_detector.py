"""
Blank Page Detection System
Detects and removes blank pages from scanned documents
"""

import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class BlankPageAnalysis:
    """Analysis result for a page"""
    page_index: int
    is_blank: bool
    confidence: float
    white_percentage: float
    edge_density: float
    text_detected: bool

class BlankPageDetector:
    """Detects blank pages in scanned documents"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.blank_threshold = 0.95  # 95% white = blank
        self.edge_threshold = 0.01   # Very few edges = blank
    
    def analyze_page(self, image: Image.Image) -> BlankPageAnalysis:
        """Analyze if a page is blank"""
        try:
            # Convert to grayscale
            gray = np.array(image.convert('L'))
            
            # Calculate white percentage
            white_pixels = np.sum(gray > 240)
            total_pixels = gray.size
            white_percentage = white_pixels / total_pixels
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / total_pixels
            
            # Check for text (any significant dark regions)
            dark_pixels = np.sum(gray < 100)
            text_detected = (dark_pixels / total_pixels) > 0.01
            
            # Determine if blank
            is_blank = (
                white_percentage > self.blank_threshold and
                edge_density < self.edge_threshold and
                not text_detected
            )
            
            # Calculate confidence
            confidence = white_percentage if is_blank else (1 - white_percentage)
            
            return BlankPageAnalysis(
                page_index=0,  # Will be set by caller
                is_blank=is_blank,
                confidence=confidence,
                white_percentage=white_percentage,
                edge_density=edge_density,
                text_detected=text_detected
            )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to analyze page: {e}")
            
            # Return safe default (not blank)
            return BlankPageAnalysis(
                page_index=0,
                is_blank=False,
                confidence=0.5,
                white_percentage=0.5,
                edge_density=0.5,
                text_detected=True
            )
    
    def find_blank_pages(self, pages: List, mode: str = "all") -> List[int]:
        """
        Find blank pages based on mode
        
        Args:
            pages: List of PageInfo objects
            mode: "start", "end", "middle", "all", "none"
        
        Returns:
            List of indices of blank pages to remove
        """
        if mode == "none":
            return []
        
        # Analyze all pages
        analyses = []
        for i, page in enumerate(pages):
            if not page.image:
                continue
            
            analysis = self.analyze_page(page.image)
            analysis.page_index = i
            analyses.append(analysis)
            
            if self.logger and analysis.is_blank:
                self.logger.debug(
                    f"Page {i+1}: Blank detected "
                    f"(white: {analysis.white_percentage:.1%}, "
                    f"edges: {analysis.edge_density:.3f})"
                )
        
        # Find blank pages based on mode
        blank_indices = []
        
        if mode == "all":
            # Remove all blank pages
            blank_indices = [a.page_index for a in analyses if a.is_blank]
        
        elif mode == "start":
            # Remove blank pages from start only
            for a in analyses:
                if a.is_blank:
                    blank_indices.append(a.page_index)
                else:
                    break  # Stop at first non-blank page
        
        elif mode == "end":
            # Remove blank pages from end only
            for a in reversed(analyses):
                if a.is_blank:
                    blank_indices.insert(0, a.page_index)
                else:
                    break  # Stop at first non-blank page
        
        elif mode == "start_end":
            # Remove from both start and end
            # Start
            for a in analyses:
                if a.is_blank:
                    blank_indices.append(a.page_index)
                else:
                    break
            
            # End
            for a in reversed(analyses):
                if a.is_blank and a.page_index not in blank_indices:
                    blank_indices.insert(0, a.page_index)
                else:
                    break
        
        elif mode == "middle":
            # Remove blank pages only from middle (keep start/end)
            first_content = None
            last_content = None
            
            # Find first and last content pages
            for a in analyses:
                if not a.is_blank:
                    if first_content is None:
                        first_content = a.page_index
                    last_content = a.page_index
            
            # Remove blanks between first and last content
            if first_content is not None and last_content is not None:
                for a in analyses:
                    if (a.is_blank and 
                        first_content < a.page_index < last_content):
                        blank_indices.append(a.page_index)
        
        if self.logger and blank_indices:
            self.logger.info(
                f"Found {len(blank_indices)} blank pages to remove "
                f"(mode: {mode})"
            )
        
        return blank_indices
    
    def remove_blank_pages(self, pages: List, mode: str = "start_end") -> Tuple[List, int]:
        """
        Remove blank pages from list
        
        Returns:
            (filtered_pages, num_removed)
        """
        blank_indices = self.find_blank_pages(pages, mode)
        
        if not blank_indices:
            return pages, 0
        
        # Filter out blank pages
        filtered_pages = [
            page for i, page in enumerate(pages)
            if i not in blank_indices
        ]
        
        return filtered_pages, len(blank_indices)
