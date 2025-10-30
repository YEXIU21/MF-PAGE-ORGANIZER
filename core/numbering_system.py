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
        """
        ENHANCED THREE-PHASE ORDERING:
        Phase 1: Global scan and analysis
        Phase 2: Intelligent ordering with full context
        Phase 3: Conflict resolution and validation
        """
        self.logger.step("🔍 Phase 1: Global Analysis - Scanning all pages")
        
        # PHASE 1: GLOBAL ANALYSIS
        global_context = self._perform_global_analysis(pages, ocr_results)
        self.logger.info(f"📊 Global Context: {global_context['total_pages']} pages, "
                        f"{global_context['roman_count']} roman, {global_context['arabic_count']} arabic, "
                        f"{global_context['unnumbered_count']} unnumbered")
        
        self.logger.step("🎯 Phase 2: Intelligent Ordering with Full Context")
        
        decisions = []
        primary_scheme = numbering_analysis['primary_scheme']
        
        # PHASE 2: CREATE ORDERING DECISIONS WITH GLOBAL CONTEXT
        for i, (page, ocr_result) in enumerate(zip(pages, ocr_results)):
            decision = self._make_ordering_decision_with_context(
                page, ocr_result, primary_scheme, i, global_context
            )
            decisions.append(decision)
        
        self.logger.step("🔧 Phase 3: Conflict Resolution and Validation")
        
        # PHASE 3: RESOLVE CONFLICTS WITH FULL CONTEXT
        decisions = self._resolve_ordering_conflicts_with_context(decisions, global_context)
        
        # Sort by assigned position
        decisions.sort(key=lambda x: x.assigned_position)
        
        # Validate final ordering
        self._validate_final_ordering(decisions, global_context)
        
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
            # Prevent MemoryError from huge number ranges
            if max_num - min_num > 10000:  # Reasonable page limit
                if self.logger:
                    self.logger.warning(f"Page range too large ({min_num}-{max_num}), using sample analysis")
                # Use sample analysis for very large ranges
                expected_pages = set(range(min_num, min(min_num + 1000, max_num + 1)))
            else:
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
    
    def _perform_global_analysis(self, pages: List[PageInfo], ocr_results: List[OCRResult]) -> Dict[str, Any]:
        """
        PHASE 1: Perform global analysis of ALL pages before making any decisions
        Returns complete context about the document structure
        """
        roman_pages = []
        arabic_pages = []
        unnumbered_pages = []
        
        max_roman_value = 0
        max_arabic_value = 0
        min_arabic_value = float('inf')
        
        # SMART FILTERING: Calculate realistic page number range
        total_pages = len(pages)
        max_realistic_page = total_pages * 3  # Allow 3x for safety (e.g., 25 pages → max 75)
        
        self.logger.info(f"🔍 Smart Filter: Total pages = {total_pages}, Max realistic page number = {max_realistic_page}")
        
        # Scan all pages
        for i, (page, ocr_result) in enumerate(zip(pages, ocr_results)):
            detected_numbers = ocr_result.detected_numbers
            
            if detected_numbers and detected_numbers[0].confidence >= 50.0:
                number_type = detected_numbers[0].number_type
                numeric_value = detected_numbers[0].numeric_value
                
                # CRITICAL FILTER: Reject unrealistic page numbers (likely from content)
                if number_type != 'roman' and numeric_value > max_realistic_page:
                    self.logger.warning(f"⚠️ {page.original_name}: Rejected unrealistic page number {numeric_value} (max: {max_realistic_page})")
                    unnumbered_pages.append({
                        'index': i,
                        'page': page
                    })
                    continue
                
                # SMART OUTLIER DETECTION: Reject numbers too far from expected position
                # Example: Page at index 4 (position 5) shouldn't have number 190
                expected_position = i + 1
                if number_type != 'roman' and numeric_value > expected_position * 5:
                    self.logger.warning(f"⚠️ {page.original_name}: Rejected outlier {numeric_value} (expected ~{expected_position})")
                    unnumbered_pages.append({
                        'index': i,
                        'page': page
                    })
                    continue
                
                if number_type == 'roman':
                    roman_pages.append({
                        'index': i,
                        'page': page,
                        'number': detected_numbers[0],
                        'value': numeric_value
                    })
                    max_roman_value = max(max_roman_value, numeric_value)
                else:
                    arabic_pages.append({
                        'index': i,
                        'page': page,
                        'number': detected_numbers[0],
                        'value': numeric_value
                    })
                    max_arabic_value = max(max_arabic_value, numeric_value)
                    min_arabic_value = min(min_arabic_value, numeric_value)
            else:
                unnumbered_pages.append({
                    'index': i,
                    'page': page
                })
        
        # Calculate document structure
        unnumbered_front_matter = len([p for p in unnumbered_pages if p['index'] < 5])
        
        # CRITICAL FIX: Use COUNT of roman pages, not max value!
        # Example: Roman pages vi, vii, viii, ix, x, xi, xii = 7 pages (not 12!)
        roman_page_count = len(roman_pages)
        
        # ★ CRITICAL FIX: Use COUNT of front matter pages, not max roman value!
        # This prevents false high roman numerals (e.g., "L"=50) from breaking arabic offset
        actual_front_matter_count = unnumbered_front_matter + roman_page_count
        
        context = {
            'total_pages': len(pages),
            'roman_pages': roman_pages,
            'arabic_pages': arabic_pages,
            'unnumbered_pages': unnumbered_pages,
            'roman_count': len(roman_pages),
            'arabic_count': len(arabic_pages),
            'unnumbered_count': len(unnumbered_pages),
            'max_roman_value': max_roman_value,
            'max_arabic_value': max_arabic_value,
            'min_arabic_value': min_arabic_value if min_arabic_value != float('inf') else 0,
            'min_roman_value': min([p['value'] for p in roman_pages]) if roman_pages else 0,
            'unnumbered_front_matter': unnumbered_front_matter,
            'roman_section_end': max_roman_value if max_roman_value > 0 else actual_front_matter_count,
            'arabic_section_start': actual_front_matter_count + 1  # Use COUNT, not max value!
        }
        
        self.logger.info(f"📈 Roman section: positions 1-{context['roman_section_end']} (max value: {max_roman_value})")
        self.logger.info(f"📈 Arabic section: starts at position {context['arabic_section_start']}")
        
        return context
    
    def _make_ordering_decision_with_context(self, page: PageInfo, ocr_result: OCRResult, 
                                            primary_scheme: Optional[NumberingScheme], 
                                            original_index: int,
                                            global_context: Dict[str, Any]) -> OrderingDecision:
        """Make ordering decision WITH full global context"""
        detected_numbers = ocr_result.detected_numbers
        position = original_index + 1
        
        # ★ CRITICAL FIX: Contents Page Detection ★
        # Contents pages have MANY page references that look like page numbers!
        # We must detect and ignore them BEFORE trying to order by numbers
        if detected_numbers and len(detected_numbers) >= 5:
            # Has 5+ different numbers → likely Contents/TOC page!
            unique_numbers = set(n.numeric_value for n in detected_numbers if n.numeric_value)
            if len(unique_numbers) >= 5:
                confidence = 0.99  # MAXIMUM - contents pages use scan order!
                reasoning = f"📋 CONTENTS page detected ({len(unique_numbers)} page references) - using scan order"
                self.logger.info(f"📋 {page.original_name}: CONTENTS PAGE at position {position} (ignoring {len(unique_numbers)} page references)")
                return OrderingDecision(
                    page_info=page,
                    assigned_position=position,
                    confidence=confidence,
                    reasoning=reasoning,
                    detected_numbers=[],  # Ignore page references!
                    alternative_positions=[position]
                )
        
        # ★ CRITICAL FIX: First 5 Positions ABSOLUTE Protection ★
        # Pages 1-5 are front matter - NEVER move them, regardless of detected numbers!
        if position <= 5:
            confidence = 0.99  # MAXIMUM priority!
            reasoning = f"🛡️ PROTECTED front matter (position {position}) - NEVER moves"
            self.logger.info(f"🛡️ {page.original_name}: PROTECTED front matter at position {position}")
            return OrderingDecision(
                page_info=page,
                assigned_position=position,
                confidence=confidence,
                reasoning=reasoning,
                detected_numbers=[],  # Ignore any detected numbers!
                alternative_positions=[position]
            )
        
        if not detected_numbers or detected_numbers[0].confidence < 50.0:
            # No reliable number detected
            position = original_index + 1
            
            # CRITICAL: Front matter PROTECTION
            # Pages 1-5: Title, copyright, contents - MAXIMUM protection (NEVER move!)
            # Pages 6-15: Likely front matter continuation - HIGH protection
            # Pages 16+: Blank pages - KEEP in place
            if position <= 5:
                confidence = 0.99  # MAXIMUM priority - front matter NEVER moves!
                reasoning = "Front matter (PROTECTED) - title/contents/copyright NEVER moves"
                self.logger.info(f"🛡️ {page.original_name}: PROTECTED front matter at position {position}")
            elif 6 <= position <= 15:
                confidence = 0.95  # High confidence for front matter continuation
                reasoning = "Front matter continuation - no number expected"
                self.logger.info(f"✅ {page.original_name}: Front matter continuation at position {position}")
            elif position > 15:
                # Middle/end pages without numbers are likely blank - MUST keep in place!
                # Blank pages are intentional placeholders, give them HIGHEST confidence
                confidence = 0.95  # Match numbered pages to prevent displacement
                reasoning = "Blank page detected - preserving filename position (intentional placeholder)"
                self.logger.info(f"📄 {page.original_name}: Blank page at position {position} (HIGH confidence)")
            else:
                confidence = 0.4
                reasoning = "No reliable page number detected - sequential placement"
            
            return OrderingDecision(
                page_info=page,
                assigned_position=position,
                confidence=confidence,
                reasoning=reasoning,
                detected_numbers=[],
                alternative_positions=[position]
            )
        
        # High-confidence detection found
        best_number = detected_numbers[0]
        number_type = best_number.number_type
        numeric_value = best_number.numeric_value
        
        # CRITICAL: Apply same filtering as global analysis
        total_pages = global_context['total_pages']
        max_realistic_page = total_pages * 3
        expected_position = original_index + 1
        
        # Reject unrealistic numbers (same logic as global analysis)
        if number_type != 'roman' and numeric_value > max_realistic_page:
            self.logger.warning(f"⚠️ {page.original_name}: Ordering phase rejected unrealistic {numeric_value}")
            position = original_index + 1
            confidence = 0.4
            reasoning = f"Rejected unrealistic page number {numeric_value} - sequential placement"
            return OrderingDecision(
                page_info=page,
                assigned_position=position,
                confidence=confidence,
                reasoning=reasoning,
                detected_numbers=[],
                alternative_positions=[position]
            )
        
        # Reject outliers (same logic as global analysis)
        if number_type != 'roman' and numeric_value > expected_position * 5:
            self.logger.warning(f"⚠️ {page.original_name}: Ordering phase rejected outlier {numeric_value}")
            position = original_index + 1
            confidence = 0.4
            reasoning = f"Rejected outlier {numeric_value} (expected ~{expected_position}) - sequential placement"
            return OrderingDecision(
                page_info=page,
                assigned_position=position,
                confidence=confidence,
                reasoning=reasoning,
                detected_numbers=[],
                alternative_positions=[position]
            )
        
        # Calculate position based on global context
        if number_type == 'roman':
            # FIXED: Roman numerals are ABSOLUTE positions!
            # If book has vi, vii, viii → they are pages 6, 7, 8 (NOT 1, 2, 3!)
            # Books can start at ANY roman numeral (i, v, vi, etc.)
            position = numeric_value  # Direct mapping: vi=6, vii=7, ix=9, etc.
            confidence = min(0.95, best_number.confidence / 100.0)
            reasoning = f"Roman numeral '{best_number.text}' = {numeric_value} (absolute position)"
            self.logger.info(f"✅ {page.original_name}: Roman '{best_number.text}' → Position {position} (absolute)")
        else:
            # Arabic numbers are offset to come AFTER roman section
            position = global_context['arabic_section_start'] + numeric_value - 1
            confidence = min(0.95, best_number.confidence / 100.0)
            reasoning = f"Arabic number '{best_number.text}' = {numeric_value} (offset to position {position})"
            self.logger.info(f"✅ {page.original_name}: Arabic '{best_number.text}' → Position {position}")
        
        return OrderingDecision(
            page_info=page,
            assigned_position=position,
            confidence=confidence,
            reasoning=reasoning,
            detected_numbers=detected_numbers,
            alternative_positions=[position]
        )
    
    def _resolve_ordering_conflicts_with_context(self, decisions: List[OrderingDecision],
                                                global_context: Dict[str, Any]) -> List[OrderingDecision]:
        """Resolve conflicts using global context"""
        # Separate numbered from unnumbered
        # CRITICAL: High-confidence pages (even without detected numbers) should participate in conflict resolution
        # This includes blank pages that must stay in their filename positions
        numbered = [d for d in decisions if (d.detected_numbers and d.confidence >= 0.6) or d.confidence >= 0.9]
        unnumbered = [d for d in decisions if not ((d.detected_numbers and d.confidence >= 0.6) or d.confidence >= 0.9)]
        
        self.logger.info(f"🔧 Resolving conflicts: {len(numbered)} numbered, {len(unnumbered)} unnumbered")
        
        # Resolve conflicts among numbered pages
        resolved_numbered = self._resolve_numbered_conflicts(numbered)
        
        # Insert unnumbered pages in gaps
        final_decisions = self._insert_unnumbered_pages(resolved_numbered, unnumbered)
        
        return final_decisions
    
    def _validate_final_ordering(self, decisions: List[OrderingDecision], global_context: Dict[str, Any]):
        """Validate the final ordering makes sense"""
        positions = [d.assigned_position for d in decisions]
        
        # Check for duplicates
        duplicates = [p for p in positions if positions.count(p) > 1]
        if duplicates:
            self.logger.warning(f"⚠️ Duplicate positions found: {set(duplicates)}")
        
        # Check for large gaps
        for i in range(len(positions) - 1):
            gap = positions[i+1] - positions[i]
            if gap > 5:
                self.logger.warning(f"⚠️ Large gap detected: {gap} positions between {positions[i]} and {positions[i+1]}")
        
        self.logger.info(f"✅ Final ordering validated: {len(decisions)} pages, positions {min(positions)}-{max(positions)}")
    
    def _make_ordering_decision(self, page: PageInfo, ocr_result: OCRResult, 
                               primary_scheme: Optional[NumberingScheme], 
                               original_index: int) -> OrderingDecision:
        """Make an ordering decision for a single page"""
        detected_numbers = ocr_result.detected_numbers
        
        if not detected_numbers or not primary_scheme:
            # No numbers detected - DOCUMENT STRUCTURE AWARE CONFIDENCE
            position = original_index + 1
            
            if position <= 5:
                # Title/blank/copyright/contents pages - HIGH confidence for no numbers
                confidence = 0.9
                reasoning = "No page number expected (title/front matter) - correct behavior"
                self.logger.info(f"✅ {page.original_name}: No page number expected at position {position} (title/front matter)")
            elif 6 <= position <= 50:
                # Front matter - should have roman numerals, medium confidence
                confidence = 0.6
                reasoning = "Missing expected roman numeral in front matter"
                self.logger.warning(f"⚠️ {page.original_name}: Expected roman numeral at position {position}")
            else:
                # Main content - should have arabic numbers, low confidence
                confidence = 0.3
                reasoning = "Missing expected arabic number in main content"
                self.logger.warning(f"⚠️ {page.original_name}: Expected arabic number at position {position}")
            
            return OrderingDecision(
                page_info=page,
                assigned_position=position,
                confidence=confidence,
                reasoning=reasoning,
                detected_numbers=[],
                alternative_positions=[position]
            )
        
        # DOCUMENT STRUCTURE VALIDATION: Enforce correct numbering patterns
        valid_numbers = []
        
        for num in detected_numbers:
            position = num.numeric_value
            is_valid = self._validate_number_for_position(num, position)
            
            if is_valid:
                valid_numbers.append(num)
            else:
                self.logger.warning(f"❌ {page.original_name}: Rejected '{num.text}' ({num.number_type}) at position {position} - wrong number type for document section")
        
        # NEW STRATEGY: ALWAYS USE DETECTED NUMBERS FIRST, IGNORE VALIDATION FAILURES
        if detected_numbers:
            # Get the highest confidence detection regardless of "validation"
            best_number = max(detected_numbers, key=lambda x: x.confidence)
            
            # PRIORITY 1: Use detected number if high confidence (>=95%)
            if best_number.confidence >= 95.0:
                position = best_number.numeric_value
                confidence = min(0.95, best_number.confidence / 100.0)
                reasoning = f"High-confidence page number '{best_number.text}' detected"
                self.logger.info(f"✅ {page.original_name}: HIGH-CONFIDENCE '{best_number.text}' → Position {position}")
            
            # PRIORITY 2: Use detected number if reasonable confidence (>=50%)
            elif best_number.confidence >= 50.0:
                position = best_number.numeric_value
                confidence = min(0.8, best_number.confidence / 100.0)
                reasoning = f"Page number '{best_number.text}' detected with good confidence"
                self.logger.info(f"✅ {page.original_name}: DETECTED '{best_number.text}' → Position {position}")
            
            # PRIORITY 3: Use detected number but with lower confidence
            else:
                position = best_number.numeric_value
                confidence = 0.6
                reasoning = f"Page number '{best_number.text}' detected with low confidence"
                self.logger.info(f"⚠️ {page.original_name}: LOW-CONFIDENCE '{best_number.text}' → Position {position}")
        
        else:
            # SMART FALLBACK: No page numbers detected
            # PRIORITY 4: Sequential assignment for unnumbered pages
            position = original_index + 1  # Will be reassigned in sequential processing
            confidence = 0.4
            reasoning = "No page numbers detected - will assign sequentially"
            self.logger.info(f"📄 {page.original_name}: No numbers → Sequential assignment")
        
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
        """
        SMART CONFLICT RESOLUTION WITH NUMBERING SYSTEM SEPARATION
        Separates roman numerals from arabic numbers to prevent chaos
        """
        # STEP 1: Separate by numbering system AND confidence
        roman_pages = []
        arabic_pages = []
        unnumbered_pages = []
        
        for decision in decisions:
            if decision.detected_numbers and decision.confidence >= 0.6:
                # Check the number type
                number_type = decision.detected_numbers[0].number_type
                if number_type == 'roman':
                    roman_pages.append(decision)
                else:
                    arabic_pages.append(decision)
            else:
                unnumbered_pages.append(decision)
        
        self.logger.info(f"📊 Numbering System Separation: {len(roman_pages)} roman, {len(arabic_pages)} arabic, {len(unnumbered_pages)} unnumbered")
        
        # STEP 2: Resolve conflicts within each numbering system
        resolved_roman = self._resolve_numbered_conflicts(roman_pages)
        resolved_arabic = self._resolve_numbered_conflicts(arabic_pages)
        
        # STEP 3: Arabic numbers already have correct offsets from _make_ordering_decision_with_context
        # No need to re-offset here (would cause double-offsetting)
        if resolved_roman and resolved_arabic:
            max_roman_pos = max(d.assigned_position for d in resolved_roman)
            self.logger.info(f"✅ Arabic numbers already offset correctly (max roman position: {max_roman_pos})")
        
        # STEP 4: Combine all numbered pages
        all_numbered = resolved_roman + resolved_arabic
        
        # STEP 5: Insert unnumbered pages in logical gaps
        final_decisions = self._insert_unnumbered_pages(all_numbered, unnumbered_pages)
        
        return final_decisions
    
    def _resolve_numbered_conflicts(self, numbered_pages: List[OrderingDecision]) -> List[OrderingDecision]:
        """
        BULLETPROOF CONFLICT RESOLUTION: Guarantees NO duplicate positions
        Strategy: Collect ALL desired positions first, then resolve globally
        """
        if not numbered_pages:
            return []
        
        # STEP 1: Collect all desired positions and build initial occupied set
        position_groups = defaultdict(list)
        all_desired_positions = set()
        
        for decision in numbered_pages:
            pos = decision.assigned_position
            position_groups[pos].append(decision)
            all_desired_positions.add(pos)
        
        self.logger.info(f"🔍 Found {len(position_groups)} unique positions desired by {len(numbered_pages)} pages")
        
        # STEP 2: Process each position group, resolving conflicts
        resolved = []
        occupied_positions = set()
        
        for position in sorted(position_groups.keys()):
            group = position_groups[position]
            
            if len(group) == 1:
                # No conflict - assign directly
                resolved.append(group[0])
                occupied_positions.add(position)
            else:
                # CONFLICT: Multiple pages want this position
                self.logger.warning(f"⚠️ Position {position} conflict: {len(group)} pages")
                
                # Sort by confidence (highest first), then by filename match
                # If equal confidence, prefer page whose filename position matches
                def sort_key(decision):
                    # Extract original index from filename
                    try:
                        # Get the page number from filename (e.g., Page_018 → 18)
                        filename = decision.page_info.original_name
                        if '_' in filename:
                            parts = filename.split('_')
                            for part in parts:
                                if part.isdigit() or (part[:-4].isdigit() if len(part) > 4 else False):
                                    original_pos = int(part.replace('.jpg', '').replace('.tif', '').replace('.png', ''))
                                    filename_matches = (original_pos == position)
                                    # Return tuple: (confidence, filename_match_bonus)
                                    # Higher confidence wins, then filename match wins
                                    return (-decision.confidence, not filename_matches)
                    except Exception:
                        pass  # Use default sorting
                    return (-decision.confidence, True)  # Default: just use confidence
                
                group.sort(key=sort_key)
                
                # Winner gets the original position
                winner = group[0]
                resolved.append(winner)
                occupied_positions.add(position)
                self.logger.info(f"✅ Position {position}: Winner = {winner.page_info.original_name}")
                
                # Losers need new positions - find free slots
                for loser in group[1:]:
                    # Find next available position AFTER current position
                    new_pos = position + 1
                    while new_pos in occupied_positions or new_pos in all_desired_positions:
                        new_pos += 1
                    
                    loser.assigned_position = new_pos
                    loser.reasoning += f" (conflict resolution: {position}→{new_pos})"
                    loser.confidence *= 0.7
                    resolved.append(loser)
                    occupied_positions.add(new_pos)
                    all_desired_positions.add(new_pos)  # Mark as occupied for future iterations
                    
                    self.logger.info(f"📍 Reassigned {loser.page_info.original_name}: {position} → {new_pos}")
        
        # STEP 3: Verify no duplicates
        final_positions = [d.assigned_position for d in resolved]
        if len(final_positions) != len(set(final_positions)):
            self.logger.error(f"❌ CRITICAL: Duplicate positions still exist after resolution!")
            duplicates = [p for p in final_positions if final_positions.count(p) > 1]
            self.logger.error(f"❌ Duplicates: {set(duplicates)}")
        else:
            self.logger.info(f"✅ Conflict resolution complete: {len(resolved)} pages, all unique positions")
        
        return resolved
    
    def _find_nearest_free_position(self, preferred_pos: int, occupied_positions: List[int]) -> int:
        """Find the nearest free position to the preferred position"""
        occupied = set(occupied_positions)
        
        # Try positions near the preferred position
        for offset in range(1, 100):  # Check up to 100 positions away
            # Try after preferred position first
            candidate = preferred_pos + offset
            if candidate not in occupied:
                return candidate
            
            # Try before preferred position
            candidate = preferred_pos - offset
            if candidate > 0 and candidate not in occupied:
                return candidate
        
        # Fallback: find first available position after all occupied
        return max(occupied) + 1 if occupied else preferred_pos
    
    def _insert_unnumbered_pages(self, numbered_decisions: List[OrderingDecision], 
                                unnumbered_pages: List[OrderingDecision]) -> List[OrderingDecision]:
        """Insert unnumbered pages in logical positions between numbered pages"""
        if not unnumbered_pages:
            return numbered_decisions
        
        # Get all occupied positions
        occupied = set(d.assigned_position for d in numbered_decisions)
        final_decisions = numbered_decisions.copy()
        
        self.logger.info(f"📄 Inserting {len(unnumbered_pages)} unnumbered pages into sequence")
        
        # Simple strategy: fill gaps sequentially
        next_available = 1
        for unnumbered in unnumbered_pages:
            # Find next available position
            while next_available in occupied:
                next_available += 1
            
            unnumbered.assigned_position = next_available
            unnumbered.reasoning += f" (sequential insertion at {next_available})"
            occupied.add(next_available)
            final_decisions.append(unnumbered)
            
            self.logger.info(f"📄 {unnumbered.page_info.original_name}: Inserted at position {next_available}")
            next_available += 1
        
        return final_decisions
    
    def _validate_number_for_position(self, detected_number, position: int) -> bool:
        """
        FLEXIBLE validation: Accept high-confidence detections regardless of expected section
        FIXED: Don't reject valid numbers due to rigid document structure assumptions
        """
        
        # PRIORITY 1: Accept HIGH-CONFIDENCE detections (99%+) regardless of section
        if detected_number.confidence >= 99.0:
            if self.logger:
                self.logger.debug(f"✅ Accepting high-confidence detection: '{detected_number.text}' ({detected_number.confidence:.1f}%)")
            return True
        
        # PRIORITY 2: Document structure guidance (not rigid rules)
        # These are preferences, not absolute requirements
        
        if 1 <= position <= 5:
            # Front matter - usually no numbers, but accept if found
            return True
            
        elif 6 <= position <= 20:
            # Mixed section - can have both roman and arabic
            # Accept both types but log transitions
            if detected_number.number_type != 'roman' and position <= 12:
                if self.logger:
                    self.logger.info(f"🔄 Numbering transition: Found {detected_number.number_type} '{detected_number.text}' at position {position}")
            return True
                
        elif position >= 21:
            # Main content - accept all number types
            return True
        
        return True  # ALWAYS default to acceptance for valid detections
    
    def _extract_filename_position(self, filename: str) -> Optional[int]:
        """Extract expected position from filename pattern"""
        import re
        
        # Pattern matching for different filename formats
        patterns = [
            r'Page_(\d+)',           # Page_001.jpg
            r'page_(\d+)',           # page_001.jpg  
            r'_0*(\d+)\.jpg$',       # 00023.jpg -> 23
            r'(\d+)\.jpg$',          # 123.jpg -> 123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return int(match.group(1))
                
        return None
    
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
