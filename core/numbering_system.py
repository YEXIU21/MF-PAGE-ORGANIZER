"""
Numbering system detection and page ordering for AI Page Reordering Automation System
Handles Arabic, Roman, hybrid, and hierarchical numbering schemes
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict, Counter
import re
import statistics

from .input_handler import PageInfo
from .ocr_engine import OCRResult, DetectedNumber
from utils.config import config

@dataclass
class NumberingScheme:
    """Information about detected numbering scheme"""
    scheme_type: str  # 'arabic', 'roman', 'hybrid', 'hierarchical', 'mixed'
    pattern: str
    confidence: float
    start_number: Optional[int]
    detected_sequence: List[int]
    gaps: List[int]  # Missing numbers
    duplicates: List[int]  # Duplicate numbers
    total_pages: int

@dataclass
class OrderingDecision:
    """Decision information for page ordering"""
    page_info: PageInfo
    assigned_position: int
    confidence: float
    reasoning: str
    detected_numbers: List[DetectedNumber]
    alternative_positions: List[int]

class NumberingSystem:
    """Advanced numbering system detection and page ordering"""
    
    def __init__(self, logger):
        self.logger = logger
        self.config = config
    
    def analyze_numbering(self, ocr_results: List[OCRResult]) -> Dict[str, Any]:
        """Analyze the numbering system(s) used across all pages"""
        self.logger.step("Analyzing numbering patterns")
        
        # Collect all detected numbers
        all_numbers = []
        page_number_map = {}  # Map page index to detected numbers
        
        for i, result in enumerate(ocr_results):
            page_numbers = []
            for num_info in result.detected_numbers:
                if num_info.numeric_value is not None:
                    all_numbers.append(num_info)
                    page_numbers.append(num_info)
            page_number_map[i] = page_numbers
        
        if not all_numbers:
            self.logger.warning("No numbers detected in any pages")
            return self._create_empty_analysis(len(ocr_results))
        
        # Detect primary numbering scheme
        schemes = self._detect_numbering_schemes(all_numbers, page_number_map)
        primary_scheme = self._select_primary_scheme(schemes)
        
        # Analyze sequence completeness
        sequence_analysis = self._analyze_sequence(primary_scheme, ocr_results)
        
        # Detect transitions (e.g., Roman to Arabic)
        transitions = self._detect_scheme_transitions(page_number_map, ocr_results)
        
        analysis = {
            'primary_scheme': primary_scheme,
            'alternative_schemes': [s for s in schemes if s != primary_scheme],
            'sequence_analysis': sequence_analysis,
            'transitions': transitions,
            'total_pages': len(ocr_results),
            'pages_with_numbers': len([p for p in page_number_map.values() if p]),
            'pages_without_numbers': len([p for p in page_number_map.values() if not p]),
            'confidence': self._calculate_overall_confidence(primary_scheme, sequence_analysis)
        }
        
        self._log_analysis_summary(analysis)
        return analysis
    
    def order_by_numbers(self, pages: List[PageInfo], ocr_results: List[OCRResult], 
                        numbering_analysis: Dict[str, Any]) -> List[OrderingDecision]:
        """Order pages based on detected numbering system"""
        self.logger.step("Ordering pages by detected numbers")
        
        decisions = []
        primary_scheme = numbering_analysis['primary_scheme']
        
        # Create initial ordering decisions
        for i, (page, ocr_result) in enumerate(zip(pages, ocr_results)):
            decision = self._make_ordering_decision(page, ocr_result, primary_scheme, i)
            decisions.append(decision)
        
        # Handle conflicts and gaps
        decisions = self._resolve_ordering_conflicts(decisions, primary_scheme)
        
        # Sort by assigned position
        decisions.sort(key=lambda x: x.assigned_position)
        
        self._log_ordering_summary(decisions)
        return decisions
    
    def _detect_numbering_schemes(self, all_numbers: List[DetectedNumber], 
                                 page_number_map: Dict[int, List[DetectedNumber]]) -> List[NumberingScheme]:
        """Detect all possible numbering schemes"""
        schemes = []
        
        # Group numbers by type
        numbers_by_type = defaultdict(list)
        for num in all_numbers:
            numbers_by_type[num.number_type].append(num)
        
        # Analyze each number type
        for number_type, numbers in numbers_by_type.items():
            scheme = self._analyze_number_type(number_type, numbers, page_number_map)
            if scheme:
                schemes.append(scheme)
        
        return schemes
    
    def _analyze_number_type(self, number_type: str, numbers: List[DetectedNumber], 
                           page_number_map: Dict[int, List[DetectedNumber]]) -> Optional[NumberingScheme]:
        """Analyze a specific number type to detect patterns"""
        if not numbers:
            return None
        
        # Extract numeric values
        numeric_values = [num.numeric_value for num in numbers if num.numeric_value is not None]
        if not numeric_values:
            return None
        
        # Analyze sequence
        unique_values = sorted(set(numeric_values))
        value_counts = Counter(numeric_values)
        
        # Calculate confidence based on sequence properties
        confidence = self._calculate_sequence_confidence(unique_values, value_counts, number_type)
        
        # Detect pattern
        pattern = self._detect_pattern(unique_values, number_type)
        
        # Find gaps and duplicates
        if unique_values:
            min_val = min(unique_values)
            max_val = max(unique_values)
            range_size = max_val - min_val + 1
            
            # Prevent memory errors with very large ranges
            if range_size > 10000:  # Limit to reasonable range
                self.logger.warning(f"Number range too large ({range_size}), skipping gap analysis")
                gaps = []
            else:
                expected_range = range(min_val, max_val + 1)
                gaps = [x for x in expected_range if x not in unique_values]
            
            duplicates = [num for num, count in value_counts.items() if count > 1]
        else:
            gaps = []
            duplicates = []
        
        scheme = NumberingScheme(
            scheme_type=number_type,
            pattern=pattern,
            confidence=confidence,
            start_number=min(unique_values) if unique_values else None,
            detected_sequence=unique_values,
            gaps=gaps,
            duplicates=duplicates,
            total_pages=len(page_number_map)
        )
        
        return scheme
    
    def _calculate_sequence_confidence(self, unique_values: List[int], 
                                     value_counts: Counter, number_type: str) -> float:
        """Calculate confidence score for a numbering sequence"""
        if not unique_values:
            return 0.0
        
        confidence = 0.0
        
        # Base confidence by number type
        type_confidence = {
            'arabic': 0.7,
            'roman': 0.8,
            'hybrid': 0.6,
            'hierarchical': 0.5
        }
        confidence += type_confidence.get(number_type, 0.5) * 100
        
        # Sequence completeness bonus
        if len(unique_values) > 1:
            min_val, max_val = min(unique_values), max(unique_values)
            expected_count = max_val - min_val + 1
            actual_count = len(unique_values)
            completeness = actual_count / expected_count
            confidence += completeness * 20
        
        # Consecutive sequence bonus
        consecutive_pairs = 0
        for i in range(len(unique_values) - 1):
            if unique_values[i+1] - unique_values[i] == 1:
                consecutive_pairs += 1
        if len(unique_values) > 1:
            consecutiveness = consecutive_pairs / (len(unique_values) - 1)
            confidence += consecutiveness * 15
        
        # Penalty for duplicates
        duplicate_penalty = sum(count - 1 for count in value_counts.values() if count > 1)
        confidence -= duplicate_penalty * 5
        
        # Reasonable range bonus
        if unique_values and 1 <= min(unique_values) <= 10 and max(unique_values) <= 1000:
            confidence += 10
        
        return min(100.0, max(0.0, confidence))
    
    def _detect_pattern(self, unique_values: List[int], number_type: str) -> str:
        """Detect the pattern in the numbering sequence"""
        if not unique_values:
            return "unknown"
        
        if len(unique_values) == 1:
            return f"single_{number_type}"
        
        # Check for simple sequential
        if len(unique_values) > 1:
            differences = [unique_values[i+1] - unique_values[i] for i in range(len(unique_values) - 1)]
            if all(diff == 1 for diff in differences):
                return f"sequential_{number_type}"
            elif len(set(differences)) == 1:
                return f"arithmetic_{number_type}_step_{differences[0]}"
        
        # Check for specific patterns
        if number_type == 'roman':
            if max(unique_values) <= 20:
                return "roman_preface"
            else:
                return "roman_main"
        elif number_type == 'hierarchical':
            return "hierarchical_sections"
        elif number_type == 'hybrid':
            return "hybrid_format"
        
        return f"irregular_{number_type}"
    
    def _select_primary_scheme(self, schemes: List[NumberingScheme]) -> Optional[NumberingScheme]:
        """Select the primary numbering scheme based on confidence and coverage"""
        if not schemes:
            return None
        
        # Score each scheme
        scored_schemes = []
        for scheme in schemes:
            score = scheme.confidence
            
            # Bonus for better coverage
            coverage = len(scheme.detected_sequence) / scheme.total_pages
            score += coverage * 20
            
            # Bonus for starting from 1
            if scheme.start_number == 1:
                score += 10
            
            # Type preference (Arabic > Roman > others)
            type_bonus = {
                'arabic': 15,
                'roman': 10,
                'hybrid': 5,
                'hierarchical': 5
            }
            score += type_bonus.get(scheme.scheme_type, 0)
            
            scored_schemes.append((score, scheme))
        
        # Return highest scoring scheme
        return max(scored_schemes, key=lambda x: x[0])[1]
    
    def _analyze_sequence(self, primary_scheme: Optional[NumberingScheme], 
                         ocr_results: List[OCRResult]) -> Dict[str, Any]:
        """Analyze the completeness and quality of the detected sequence"""
        if not primary_scheme:
            return {
                'is_complete': False,
                'missing_pages': [],
                'extra_pages': [],
                'sequence_quality': 0.0,
                'recommendations': ['No clear numbering scheme detected']
            }
        
        sequence = primary_scheme.detected_sequence
        recommendations = []
        
        # Check sequence completeness
        if sequence:
            min_num, max_num = min(sequence), max(sequence)
            expected_pages = set(range(min_num, max_num + 1))
            actual_pages = set(sequence)
            
            missing = sorted(expected_pages - actual_pages)
            extra = [x for x in sequence if x < min_num or x > max_num]
        else:
            missing = []
            extra = []
        
        # Calculate sequence quality
        quality = primary_scheme.confidence / 100.0
        if missing:
            quality *= (1 - len(missing) / len(ocr_results))
            recommendations.append(f"Missing page numbers: {missing}")
        
        if primary_scheme.duplicates:
            quality *= 0.8
            recommendations.append(f"Duplicate page numbers found: {primary_scheme.duplicates}")
        
        if not recommendations:
            recommendations.append("Numbering sequence appears complete")
        
        return {
            'is_complete': len(missing) == 0,
            'missing_pages': missing,
            'extra_pages': extra,
            'sequence_quality': quality,
            'recommendations': recommendations
        }
    
    def _detect_scheme_transitions(self, page_number_map: Dict[int, List[DetectedNumber]], 
                                  ocr_results: List[OCRResult]) -> List[Dict[str, Any]]:
        """Detect transitions between different numbering schemes"""
        transitions = []
        
        # Analyze consecutive pages for scheme changes
        prev_types = set()
        
        for i, numbers in page_number_map.items():
            current_types = set(num.number_type for num in numbers)
            
            if i > 0 and prev_types and current_types:
                if prev_types != current_types:
                    # Detected a transition
                    transition = {
                        'page_index': i,
                        'from_types': list(prev_types),
                        'to_types': list(current_types),
                        'transition_type': self._classify_transition(prev_types, current_types)
                    }
                    transitions.append(transition)
            
            if current_types:
                prev_types = current_types
        
        return transitions
    
    def _classify_transition(self, from_types: Set[str], to_types: Set[str]) -> str:
        """Classify the type of numbering transition"""
        if 'roman' in from_types and 'arabic' in to_types:
            return 'roman_to_arabic'  # Common: preface to main content
        elif 'arabic' in from_types and 'roman' in to_types:
            return 'arabic_to_roman'  # Less common: main to appendix
        elif 'hierarchical' in from_types or 'hierarchical' in to_types:
            return 'hierarchical_change'
        else:
            return 'mixed_scheme_change'
    
    def _make_ordering_decision(self, page: PageInfo, ocr_result: OCRResult, 
                               primary_scheme: Optional[NumberingScheme], 
                               original_index: int) -> OrderingDecision:
        """Make an ordering decision for a single page"""
        detected_numbers = ocr_result.detected_numbers
        
        if not detected_numbers or not primary_scheme:
            # No numbers detected - keep original position
            return OrderingDecision(
                page_info=page,
                assigned_position=original_index + 1,
                confidence=0.1,
                reasoning="No page numbers detected - using original order",
                detected_numbers=[],
                alternative_positions=[original_index + 1]
            )
        
        # Find best matching number for primary scheme
        matching_numbers = [num for num in detected_numbers 
                          if num.number_type == primary_scheme.scheme_type]
        
        if matching_numbers:
            best_number = max(matching_numbers, key=lambda x: x.confidence)
            position = best_number.numeric_value
            confidence = min(0.95, best_number.confidence / 100.0)
            reasoning = f"Page number {best_number.text} detected ({best_number.number_type})"
        else:
            # Use highest confidence number from any type
            best_number = max(detected_numbers, key=lambda x: x.confidence)
            position = best_number.numeric_value
            confidence = min(0.7, best_number.confidence / 100.0)
            reasoning = f"Using {best_number.text} from {best_number.number_type} numbering"
        
        # Generate alternative positions
        alternatives = [num.numeric_value for num in detected_numbers 
                       if num.numeric_value != position and num.numeric_value is not None]
        alternatives.append(original_index + 1)  # Original position as fallback
        
        return OrderingDecision(
            page_info=page,
            assigned_position=position,
            confidence=confidence,
            reasoning=reasoning,
            detected_numbers=detected_numbers,
            alternative_positions=sorted(set(alternatives))
        )
    
    def _resolve_ordering_conflicts(self, decisions: List[OrderingDecision], 
                                   primary_scheme: Optional[NumberingScheme]) -> List[OrderingDecision]:
        """Resolve conflicts where multiple pages have the same position"""
        # Group decisions by assigned position
        position_groups = defaultdict(list)
        for decision in decisions:
            if decision.assigned_position is not None:
                position_groups[decision.assigned_position].append(decision)
        
        resolved_decisions = []
        
        for position, group in position_groups.items():
            if len(group) == 1:
                # No conflict
                resolved_decisions.append(group[0])
            else:
                # Resolve conflict by confidence
                self.logger.warning(f"Position conflict at {position}: {len(group)} pages")
                
                # Sort by confidence, keep highest
                group.sort(key=lambda x: x.confidence, reverse=True)
                
                # Assign the highest confidence page to the original position
                resolved_decisions.append(group[0])
                
                # Reassign others to alternative positions or sequential positions
                for i, decision in enumerate(group[1:], 1):
                    # Try alternative positions first
                    new_position = None
                    for alt_pos in decision.alternative_positions:
                        if not any(d.assigned_position == alt_pos for d in resolved_decisions):
                            new_position = alt_pos
                            break
                    
                    # If no alternative, use sequential assignment
                    if new_position is None:
                        new_position = position + i
                    
                    # Update decision
                    decision.assigned_position = new_position
                    decision.reasoning += f" (reassigned due to conflict)"
                    decision.confidence *= 0.8  # Reduce confidence
                    
                    resolved_decisions.append(decision)
        
        return resolved_decisions
    
    def _create_empty_analysis(self, total_pages: int) -> Dict[str, Any]:
        """Create empty analysis when no numbers are detected"""
        return {
            'primary_scheme': None,
            'alternative_schemes': [],
            'sequence_analysis': {
                'is_complete': False,
                'missing_pages': [],
                'extra_pages': [],
                'sequence_quality': 0.0,
                'recommendations': ['No page numbers detected - will use content analysis']
            },
            'transitions': [],
            'total_pages': total_pages,
            'pages_with_numbers': 0,
            'pages_without_numbers': total_pages,
            'confidence': 0.0
        }
    
    def _calculate_overall_confidence(self, primary_scheme: Optional[NumberingScheme], 
                                    sequence_analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence in the numbering analysis"""
        if not primary_scheme:
            return 0.0
        
        confidence = primary_scheme.confidence * 0.6  # Base confidence
        confidence += sequence_analysis['sequence_quality'] * 40  # Sequence quality
        
        return min(100.0, confidence)
    
    def _log_analysis_summary(self, analysis: Dict[str, Any]):
        """Log summary of numbering analysis"""
        primary = analysis['primary_scheme']
        
        if primary:
            self.logger.info(f"Primary numbering: {primary.scheme_type} ({primary.pattern})")
            self.logger.info(f"Sequence: {primary.start_number}-{max(primary.detected_sequence) if primary.detected_sequence else '?'}")
            self.logger.info(f"Coverage: {len(primary.detected_sequence)}/{primary.total_pages} pages")
            
            if primary.gaps:
                self.logger.warning(f"Missing numbers: {primary.gaps}")
            if primary.duplicates:
                self.logger.warning(f"Duplicate numbers: {primary.duplicates}")
        else:
            self.logger.warning("No clear numbering scheme detected")
        
        self.logger.info(f"Overall confidence: {analysis['confidence']:.1f}%")
    
    def _log_ordering_summary(self, decisions: List[OrderingDecision]):
        """Log summary of ordering decisions"""
        high_conf = len([d for d in decisions if d.confidence > 0.8])
        medium_conf = len([d for d in decisions if 0.5 <= d.confidence <= 0.8])
        low_conf = len([d for d in decisions if d.confidence < 0.5])
        
        self.logger.info(f"Ordering confidence: {high_conf} high, {medium_conf} medium, {low_conf} low")
        
        if low_conf > 0:
            self.logger.warning(f"{low_conf} pages have low ordering confidence - consider manual review")
