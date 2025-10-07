"""
AI Pattern Learning System - Adaptive Page Number Detection
Learns from previous pages to speed up detection on subsequent pages
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import time

@dataclass
class LocationPattern:
    """Tracks where page numbers are found"""
    location: str  # 'top_left', 'top_right', 'bottom_left', 'bottom_right'
    success_count: int = 0
    total_attempts: int = 0
    last_found_page: int = 0
    confidence: float = 0.0
    
    def update_success(self, page_num: int):
        """Update when page number found at this location"""
        self.success_count += 1
        self.total_attempts += 1
        self.last_found_page = page_num
        self.confidence = self.success_count / self.total_attempts
    
    def update_failure(self):
        """Update when page number NOT found at this location"""
        self.total_attempts += 1
        self.confidence = self.success_count / self.total_attempts if self.total_attempts > 0 else 0.0

@dataclass
class NumberTypePattern:
    """Tracks what type of numbers are being used"""
    type_name: str  # 'roman', 'arabic'
    count: int = 0
    last_seen_page: int = 0

class AIPatternLearning:
    """
    Intelligent learning system that adapts to page number patterns
    Gets FASTER as it processes more pages!
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        
        # Location learning
        self.location_patterns: Dict[str, LocationPattern] = {
            'top_left': LocationPattern('top_left'),
            'top_right': LocationPattern('top_right'),
            'bottom_left': LocationPattern('bottom_left'),
            'bottom_right': LocationPattern('bottom_right')
        }
        
        # Number type learning
        self.number_types: Dict[str, NumberTypePattern] = {
            'roman': NumberTypePattern('roman'),
            'arabic': NumberTypePattern('arabic')
        }
        
        # Processing stats
        self.pages_processed = 0
        self.total_corners_scanned = 0
        self.corners_skipped = 0
        self.learning_phase = True  # First 3 pages = learning
        self.dominant_location: Optional[str] = None
        self.dominant_type: Optional[str] = None
        
        # Performance tracking
        self.scan_times: List[float] = []
        
    def get_scan_order(self) -> List[str]:
        """
        SMART SCANNING: Return corners in order of likelihood
        Most likely location checked FIRST!
        """
        # Learning phase: scan all corners
        if self.pages_processed < 3:
            if self.logger:
                self.logger.debug("🎓 Learning phase: scanning all corners")
            return ['top_left', 'top_right', 'bottom_left', 'bottom_right']
        
        # Sort by confidence (highest first)
        sorted_locations = sorted(
            self.location_patterns.items(),
            key=lambda x: x[1].confidence,
            reverse=True
        )
        
        scan_order = [loc for loc, pattern in sorted_locations]
        
        if self.logger:
            top_location = scan_order[0]
            top_confidence = self.location_patterns[top_location].confidence
            self.logger.debug(f"🎯 Smart scan order: {scan_order[0]} ({top_confidence:.0%} confidence) → others")
        
        return scan_order
    
    def should_skip_remaining_corners(self, found_location: str) -> bool:
        """
        EARLY EXIT: If we found the number in the expected location,
        skip checking other corners (4x speed boost!)
        """
        if self.pages_processed < 3:
            return False  # Learning phase: always check all
        
        # If found in dominant location, skip others!
        if self.dominant_location and found_location == self.dominant_location:
            pattern = self.location_patterns[found_location]
            if pattern.confidence > 0.75:  # 75% confidence threshold
                self.corners_skipped += 3  # Would have scanned 3 more corners
                if self.logger:
                    self.logger.debug(f"⚡ FAST MODE: Found in expected location ({pattern.confidence:.0%}), skipping other corners!")
                return True
        
        return False
    
    def record_success(self, location: str, number_type: str, page_num: int):
        """
        Record successful detection - AI LEARNS!
        """
        # Update location pattern
        self.location_patterns[location].update_success(page_num)
        
        # ADAPTIVE: Detect pattern changes!
        self._detect_pattern_change(location, page_num)
        
        # Update number type pattern
        if number_type in self.number_types:
            self.number_types[number_type].count += 1
            self.number_types[number_type].last_seen_page = page_num
        
        # Update dominant patterns
        self._update_dominant_patterns()
        
        if self.logger:
            confidence = self.location_patterns[location].confidence
            self.logger.info(f"✅ AI Learning: {location} → {confidence:.0%} confidence ({self.location_patterns[location].success_count}/{self.location_patterns[location].total_attempts})")
    
    def record_failure(self, location: str):
        """Record when location didn't have page number"""
        self.location_patterns[location].update_failure()
        self._update_dominant_patterns()
    
    def _detect_pattern_change(self, current_location: str, page_num: int):
        """
        SMART ADAPTATION: Detect when page number position changes!
        Example: Pages 1-10 in top_left, then pages 11+ in top_right
        """
        if not self.dominant_location or self.pages_processed < 5:
            return  # Need at least 5 pages to detect changes
        
        # If we found number in a DIFFERENT location than dominant
        if current_location != self.dominant_location:
            # Check if this is a consistent change (found 2+ times in new location recently)
            recent_success = self.location_patterns[current_location].success_count
            
            if recent_success >= 2:
                if self.logger:
                    self.logger.warning(f"🔄 PATTERN CHANGE DETECTED! Switching from {self.dominant_location} → {current_location}")
                    self.logger.info(f"   AI is RE-LEARNING the new pattern...")
                
                # RESET learning to adapt to new pattern
                self.learning_phase = True
                self.pages_processed = 0  # Restart learning counter
                
                # Keep the data but reduce confidence of old pattern
                for loc, pattern in self.location_patterns.items():
                    if loc != current_location:
                        pattern.confidence *= 0.5  # Reduce old patterns by 50%
    
    def _update_dominant_patterns(self):
        """Determine which location and type are most common"""
        # Find dominant location
        best_location = max(
            self.location_patterns.items(),
            key=lambda x: (x[1].confidence, x[1].success_count)
        )
        
        if best_location[1].confidence > 0.6:  # 60% threshold
            self.dominant_location = best_location[0]
        
        # Find dominant number type
        best_type = max(
            self.number_types.items(),
            key=lambda x: x[1].count
        )
        
        if best_type[1].count > 2:
            self.dominant_type = best_type[0]
    
    def start_page(self):
        """Called at start of each page"""
        self.pages_processed += 1
        
        # Exit learning phase after 3 pages
        if self.pages_processed == 3:
            self.learning_phase = False
            if self.logger:
                self.logger.info(f"🎓 Learning complete! Dominant location: {self.dominant_location}, Type: {self.dominant_type}")
                self.logger.info(f"⚡ FAST MODE activated - will skip unnecessary corner scans!")
    
    def get_stats(self) -> Dict:
        """Get learning statistics"""
        total_possible_scans = self.pages_processed * 4
        actual_scans = self.total_corners_scanned
        efficiency = (1 - (actual_scans / total_possible_scans)) * 100 if total_possible_scans > 0 else 0
        
        return {
            'pages_processed': self.pages_processed,
            'total_corners_scanned': self.total_corners_scanned,
            'corners_skipped': self.corners_skipped,
            'efficiency_gain': f"{efficiency:.1f}%",
            'dominant_location': self.dominant_location,
            'dominant_type': self.dominant_type,
            'location_confidence': {
                loc: f"{pattern.confidence:.0%}" 
                for loc, pattern in self.location_patterns.items()
            }
        }
    
    def log_stats(self):
        """Log learning statistics"""
        if not self.logger:
            return
        
        stats = self.get_stats()
        self.logger.info("=" * 60)
        self.logger.info("🤖 AI LEARNING STATISTICS")
        self.logger.info("=" * 60)
        self.logger.info(f"Pages processed: {stats['pages_processed']}")
        self.logger.info(f"Corners scanned: {stats['total_corners_scanned']}")
        self.logger.info(f"Corners skipped: {stats['corners_skipped']}")
        self.logger.info(f"Efficiency gain: {stats['efficiency_gain']}")
        self.logger.info(f"Dominant location: {stats['dominant_location']}")
        self.logger.info(f"Dominant type: {stats['dominant_type']}")
        self.logger.info("Location confidence:")
        for loc, conf in stats['location_confidence'].items():
            self.logger.info(f"  {loc}: {conf}")
        self.logger.info("=" * 60)
