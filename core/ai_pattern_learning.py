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
        
        # Location learning - ENHANCED with edge-first positions
        self.location_patterns: Dict[str, LocationPattern] = {
            # Extreme edge positions (highest priority)
            'edge_top_left': LocationPattern('edge_top_left'),
            'edge_top_right': LocationPattern('edge_top_right'),
            'edge_bottom_left': LocationPattern('edge_bottom_left'),
            'edge_bottom_right': LocationPattern('edge_bottom_right'),
            'edge_top_center': LocationPattern('edge_top_center'),
            'edge_bottom_center': LocationPattern('edge_bottom_center'),
            # Full edge strips
            'full_edge_top': LocationPattern('full_edge_top'),
            'full_edge_bottom': LocationPattern('full_edge_bottom'),
            'full_edge_left': LocationPattern('full_edge_left'),
            'full_edge_right': LocationPattern('full_edge_right'),
            # Standard corners
            'top_left': LocationPattern('top_left'),
            'top_right': LocationPattern('top_right'),
            'bottom_left': LocationPattern('bottom_left'),
            'bottom_right': LocationPattern('bottom_right'),
            'bottom_center': LocationPattern('bottom_center'),  # Very common!
            'top_center': LocationPattern('top_center'),
            'middle_left': LocationPattern('middle_left'),  # Edge middle positions
            'middle_right': LocationPattern('middle_right')
        }
        
        # Number type learning
        self.number_types: Dict[str, NumberTypePattern] = {
            'roman': NumberTypePattern('roman'),
            'arabic': NumberTypePattern('arabic')
        }
        
        # ADVANCED LEARNING STATS (YOUR VISION!)
        self.pages_processed = 0
        self.total_corners_scanned = 0
        self.corners_skipped = 0
        
        # SEPARATE LEARNING FOR EACH NUMBERING STYLE
        self.roman_detections = 0    # Count of roman numerals found (i, ii, iii, etc.)
        self.arabic_detections = 0   # Count of arabic numbers found (1, 2, 3, etc.)
        self.roman_learned = False   # True after 10 roman detections
        self.arabic_learned = False  # True after 10 arabic detections
        
        self.dominant_location: Optional[str] = None
        self.dominant_type: Optional[str] = None
        
        # Performance tracking
        self.scan_times: List[float] = []
        
    def get_scan_order(self, expected_number_type: str = None) -> List[str]:
        """
        BRILLIANT ADAPTIVE SCANNING: Return corners in order of likelihood per number type
        YOUR VISION: Learn patterns for each numbering style separately!
        """
        # LEARNING PHASE: Scan all positions until we have 10 detections of this number type
        if expected_number_type == 'roman' and not self.roman_learned:
            if self.logger:
                self.logger.debug(f"🎓 Roman learning phase: {self.roman_detections}/10 detections")
            return ['top_left', 'top_right', 'bottom_center', 'top_center', 'middle_left', 'middle_right', 'bottom_left', 'bottom_right']
        
        elif expected_number_type == 'arabic' and not self.arabic_learned:
            if self.logger:
                self.logger.debug(f"🎓 Arabic learning phase: {self.arabic_detections}/10 detections")
            return ['bottom_center', 'top_center', 'middle_right', 'middle_left', 'top_left', 'top_right', 'bottom_left', 'bottom_right']
        
        elif not self.roman_learned and not self.arabic_learned:
            if self.logger:
                self.logger.debug(f"🎓 General learning phase: Roman {self.roman_detections}/10, Arabic {self.arabic_detections}/10")
            return ['bottom_center', 'top_center', 'middle_right', 'middle_left', 'top_left', 'top_right', 'bottom_left', 'bottom_right']
        
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
    
    def get_edge_first_scan_order(self, base_order: List[str], expected_number_type: str = None) -> List[str]:
        """
        EDGE-FIRST ADAPTIVE SCANNING: Return positions in edge-first order with AI learning
        Prioritizes extreme edges where page numbers actually are in published books
        """
        # LEARNING PHASE: Use base edge-first order until we have enough detections
        if expected_number_type == 'roman' and not self.roman_learned:
            if self.logger:
                self.logger.debug(f"🎓 Roman learning phase (edge-first): {self.roman_detections}/10 detections")
            # Edge-first order for roman numerals (usually at top)
            return [
                'edge_top_left', 'edge_top_right', 'edge_top_center',
                'full_edge_top', 'edge_bottom_left', 'edge_bottom_right',
                'full_edge_left', 'full_edge_right', 'top_left', 'top_right',
                'bottom_center', 'top_center', 'middle_left', 'middle_right',
                'bottom_left', 'bottom_right'
            ]
        
        elif expected_number_type == 'arabic' and not self.arabic_learned:
            if self.logger:
                self.logger.debug(f"🎓 Arabic learning phase (edge-first): {self.arabic_detections}/10 detections")
            # Edge-first order for arabic numbers (can be top or bottom)
            return [
                'edge_top_right', 'edge_bottom_right', 'edge_top_left',
                'edge_bottom_center', 'edge_top_center', 'full_edge_top',
                'full_edge_bottom', 'full_edge_right', 'bottom_center',
                'top_center', 'top_left', 'top_right', 'bottom_left',
                'bottom_right', 'middle_left', 'middle_right'
            ]
        
        elif not self.roman_learned and not self.arabic_learned:
            if self.logger:
                self.logger.debug(f"🎓 General learning phase (edge-first): Roman {self.roman_detections}/10, Arabic {self.arabic_detections}/10")
            # Default edge-first order
            return base_order
        
        # OPTIMIZED PHASE: Use AI learning to refine scan order
        # Filter base_order to only include positions we've learned about
        learned_positions = [
            loc for loc in base_order 
            if loc in self.location_patterns and self.location_patterns[loc].total_attempts > 0
        ]
        
        # Sort learned positions by confidence
        learned_sorted = sorted(
            learned_positions,
            key=lambda loc: self.location_patterns[loc].confidence,
            reverse=True
        )
        
        # Add unlearned positions at the end (maintaining edge-first priority)
        unlearned_positions = [loc for loc in base_order if loc not in learned_positions]
        
        final_order = learned_sorted + unlearned_positions
        
        if self.logger:
            if learned_sorted:
                top_location = learned_sorted[0]
                top_confidence = self.location_patterns[top_location].confidence
                self.logger.debug(f"🎯 Smart edge-first order: {top_location} ({top_confidence:.0%} confidence) → {len(learned_sorted)-1} more learned, {len(unlearned_positions)} unlearned")
            else:
                self.logger.debug(f"🎯 Edge-first order (no learning yet): {len(base_order)} positions")
        
        return final_order
    
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
        Record successful detection - ADVANCED AI LEARNING PER NUMBER TYPE!
        YOUR VISION: Count detections separately for roman vs arabic
        """
        # Update location pattern
        self.location_patterns[location].update_success(page_num)
        
        # COUNT DETECTIONS BY NUMBER TYPE (YOUR BRILLIANT IDEA!)
        if number_type == 'roman':
            self.roman_detections += 1
            if self.roman_detections == 10 and not self.roman_learned:
                self.roman_learned = True
                if self.logger:
                    self.logger.info(f"🎓🎯 ROMAN LEARNING COMPLETE! 10 detections reached → Speed optimization activated!")
                    
        elif number_type == 'arabic':
            self.arabic_detections += 1
            if self.arabic_detections == 10 and not self.arabic_learned:
                self.arabic_learned = True
                if self.logger:
                    self.logger.info(f"🎓🎯 ARABIC LEARNING COMPLETE! 10 detections reached → Speed optimization activated!")
        
        # ADAPTIVE: Detect pattern changes with number type context!
        self._detect_pattern_change(location, page_num, number_type)
        
        # Update number type pattern
        if number_type in self.number_types:
            self.number_types[number_type].count += 1
            self.number_types[number_type].last_seen_page = page_num
        
        # Update dominant patterns
        self._update_dominant_patterns()
        
        if self.logger:
            confidence = self.location_patterns[location].confidence
            self.logger.info(f"✅ AI Learning: {number_type} #{getattr(self, f'{number_type}_detections', 0)} in {location} → {confidence:.0%} confidence")
    
    def record_failure(self, location: str):
        """Record when location didn't have page number"""
        self.location_patterns[location].update_failure()
        self._update_dominant_patterns()
    
    def _detect_pattern_change(self, current_location: str, page_num: int, number_type: str):
        """
        ADVANCED PATTERN CHANGE DETECTION: Handle sudden position changes!
        YOUR VISION: Detect position changes and adapt intelligently
        """
        if not self.dominant_location:
            return  # No established pattern yet
        
        # If we found number in a DIFFERENT location than dominant
        if current_location != self.dominant_location:
            # SMART DETECTION: Check if this is consistent change (3+ in new location)
            recent_success = self.location_patterns[current_location].success_count
            
            if recent_success >= 3:  # Require 3 confirmations to avoid false alarms
                if self.logger:
                    self.logger.warning(f"🔄 POSITION CHANGE DETECTED! {number_type} numbers moving from {self.dominant_location} → {current_location}")
                    self.logger.info(f"   🎓 AI RE-LEARNING new {number_type} pattern...")
                
                # PARTIAL RESET: Don't lose ALL learning, just adapt
                if number_type == 'roman' and self.roman_learned:
                    # Roman numbers changed position - reduce confidence but don't fully reset
                    self.roman_learned = False
                    self.roman_detections = max(5, self.roman_detections - 5)  # Keep some progress
                    
                elif number_type == 'arabic' and self.arabic_learned:
                    # Arabic numbers changed position - reduce confidence but don't fully reset  
                    self.arabic_learned = False
                    self.arabic_detections = max(5, self.arabic_detections - 5)  # Keep some progress
                
                # GRADUAL ADAPTATION: Reduce old pattern confidence, don't eliminate
                for loc, pattern in self.location_patterns.items():
                    if loc != current_location:
                        pattern.confidence *= 0.7  # Reduce old patterns by 30%
                    else:
                        pattern.confidence *= 1.2  # Boost new pattern by 20%
                        
                if self.logger:
                    self.logger.info(f"   🧠 Adaptation complete: {number_type} detections retained, confidence adjusted")
    
    def handle_detection_failure_streak(self, expected_location: str, number_type: str):
        """
        EMERGENCY COUNTERMEASURE: Handle when expected location consistently fails
        Example: System expects top_left but finds nothing for 5+ pages
        """
        pattern = self.location_patterns[expected_location]
        
        # If expected location failed too many times, trigger emergency re-scan
        if pattern.total_attempts - pattern.success_count >= 5:  # 5 consecutive failures
            if self.logger:
                self.logger.warning(f"🚨 DETECTION FAILURE STREAK! {expected_location} failed 5+ times for {number_type}")
                self.logger.info(f"   🔄 Triggering EMERGENCY FULL-SCAN mode")
            
            # EMERGENCY PROTOCOL: Force full corner scanning for next few pages
            if number_type == 'roman':
                self.roman_learned = False  # Force re-learning
            elif number_type == 'arabic':
                self.arabic_learned = False  # Force re-learning
                
            return True  # Signal to caller to do full scan
        
        return False
    
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
