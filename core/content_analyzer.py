"""
Content-based ordering system for AI Page Reordering Automation System
Analyzes text continuity, headings, and references for pages without clear numbers
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
import re
from collections import defaultdict, Counter
import difflib
from statistics import mean

from .input_handler import PageInfo
from .ocr_engine import OCRResult
from .numbering_system import OrderingDecision
from utils.config import config

@dataclass
class ContentRelationship:
    """Relationship between two pages based on content analysis"""
    page_a_index: int
    page_b_index: int
    relationship_type: str  # 'continuation', 'reference', 'heading_sequence', 'similar'
    confidence: float
    evidence: str

@dataclass
class TextContinuity:
    """Information about text continuation between pages"""
    page_index: int
    last_words: List[str]
    first_words: List[str]
    sentence_completion: bool
    paragraph_break: bool
    confidence: float

class ContentAnalyzer:
    """Advanced content analysis for page ordering"""
    
    # Common words to ignore in continuity analysis
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Patterns for detecting headings and sections
    HEADING_PATTERNS = [
        r'^(?:chapter|section|part|appendix)\s+\d+',
        r'^\d+\.\s+[A-Z][a-z]+',
        r'^[A-Z][A-Z\s]+$',  # ALL CAPS headings
        r'^\d+\.\d+\s+[A-Z][a-z]+',  # Numbered subsections
        r'^[IVX]+\.\s+[A-Z][a-z]+',  # Roman numeral sections
    ]
    
    # Reference patterns
    REFERENCE_PATTERNS = [
        r'see\s+(?:page|p\.?|figure|fig\.?|table)\s+\d+',
        r'(?:page|p\.?)\s+\d+',
        r'(?:figure|fig\.?|table)\s+\d+',
        r'as\s+(?:discussed|mentioned|shown)\s+(?:above|below|earlier|later)',
        r'(?:above|below|previous|next|following)\s+(?:section|chapter|page)',
    ]
    
    def __init__(self, logger):
        self.logger = logger
        self.config = config
    
    def refine_ordering(self, initial_decisions: List[OrderingDecision], 
                       ocr_results: List[OCRResult]) -> List[OrderingDecision]:
        """Refine page ordering using content analysis"""
        self.logger.step("Analyzing content relationships")
        
        # Extract content features
        content_features = self._extract_content_features(ocr_results)
        
        # Analyze relationships between pages
        relationships = self._analyze_content_relationships(content_features, ocr_results)
        
        # Identify pages that need content-based ordering
        uncertain_pages = [d for d in initial_decisions if d.confidence < 0.7]
        
        if uncertain_pages:
            self.logger.info(f"Analyzing {len(uncertain_pages)} pages with uncertain numbering")
            
            # Apply content-based refinements
            refined_decisions = self._apply_content_refinements(
                initial_decisions, relationships, content_features, ocr_results)
        else:
            refined_decisions = initial_decisions
        
        # Final validation and adjustment
        final_decisions = self._validate_and_adjust_ordering(refined_decisions, relationships)
        
        self._log_content_analysis_summary(relationships, uncertain_pages)
        return final_decisions
    
    def _extract_content_features(self, ocr_results: List[OCRResult]) -> List[Dict[str, Any]]:
        """Extract content features from each page"""
        features = []
        
        for i, result in enumerate(ocr_results):
            page_features = {
                'index': i,
                'text': result.full_text,
                'word_count': len(result.full_text.split()) if result.full_text else 0,
                'headings': self._extract_headings(result.full_text),
                'references': self._extract_references(result.full_text),
                'first_words': self._get_first_words(result.full_text, 10),
                'last_words': self._get_last_words(result.full_text, 10),
                'sentences': self._split_sentences(result.full_text),
                'paragraphs': self._count_paragraphs(result.full_text),
                'text_density': self._calculate_text_density(result),
                'language_features': self._analyze_language_features(result.full_text)
            }
            features.append(page_features)
        
        return features
    
    def _extract_headings(self, text: str) -> List[Dict[str, Any]]:
        """Extract headings and section markers from text"""
        if not text:
            return []
        
        headings = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check against heading patterns
            for pattern in self.HEADING_PATTERNS:
                if re.match(pattern, line, re.IGNORECASE):
                    headings.append({
                        'text': line,
                        'line_number': i,
                        'pattern': pattern,
                        'type': self._classify_heading(line)
                    })
                    break
            
            # Check for other heading indicators
            if (line.isupper() and len(line.split()) <= 6 and len(line) <= 50) or \
               (line.endswith(':') and len(line.split()) <= 4):
                headings.append({
                    'text': line,
                    'line_number': i,
                    'pattern': 'structural',
                    'type': 'section_header'
                })
        
        return headings
    
    def _classify_heading(self, heading_text: str) -> str:
        """Classify the type of heading"""
        heading_lower = heading_text.lower()
        
        if 'chapter' in heading_lower:
            return 'chapter'
        elif 'section' in heading_lower:
            return 'section'
        elif 'part' in heading_lower:
            return 'part'
        elif 'appendix' in heading_lower:
            return 'appendix'
        elif re.match(r'^\d+\.', heading_text):
            return 'numbered_section'
        elif re.match(r'^[IVX]+\.', heading_text):
            return 'roman_section'
        else:
            return 'generic'
    
    def _extract_references(self, text: str) -> List[Dict[str, Any]]:
        """Extract references to other pages/sections"""
        if not text:
            return []
        
        references = []
        
        for pattern in self.REFERENCE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                ref_text = match.group()
                
                # Try to extract referenced number
                number_match = re.search(r'\d+', ref_text)
                referenced_number = int(number_match.group()) if number_match else None
                
                references.append({
                    'text': ref_text,
                    'position': match.span(),
                    'referenced_number': referenced_number,
                    'type': self._classify_reference(ref_text)
                })
        
        return references
    
    def _classify_reference(self, ref_text: str) -> str:
        """Classify the type of reference"""
        ref_lower = ref_text.lower()
        
        if 'page' in ref_lower or 'p.' in ref_lower:
            return 'page_reference'
        elif 'figure' in ref_lower or 'fig' in ref_lower:
            return 'figure_reference'
        elif 'table' in ref_lower:
            return 'table_reference'
        elif any(word in ref_lower for word in ['above', 'below', 'previous', 'next']):
            return 'positional_reference'
        else:
            return 'generic_reference'
    
    def _get_first_words(self, text: str, count: int) -> List[str]:
        """Get first N meaningful words from text"""
        if not text:
            return []
        
        words = text.split()
        meaningful_words = [w.lower().strip('.,!?;:"()[]') for w in words 
                          if w.lower().strip('.,!?;:"()[]') not in self.STOP_WORDS]
        
        return meaningful_words[:count]
    
    def _get_last_words(self, text: str, count: int) -> List[str]:
        """Get last N meaningful words from text"""
        if not text:
            return []
        
        words = text.split()
        meaningful_words = [w.lower().strip('.,!?;:"()[]') for w in words 
                          if w.lower().strip('.,!?;:"()[]') not in self.STOP_WORDS]
        
        return meaningful_words[-count:] if len(meaningful_words) >= count else meaningful_words
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        if not text:
            return []
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _count_paragraphs(self, text: str) -> int:
        """Count paragraphs in text"""
        if not text:
            return 0
        
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        return len(paragraphs)
    
    def _calculate_text_density(self, ocr_result: OCRResult) -> float:
        """Calculate text density (words per text block)"""
        if not ocr_result.text_blocks:
            return 0.0
        
        total_words = len(ocr_result.full_text.split()) if ocr_result.full_text else 0
        total_blocks = len(ocr_result.text_blocks)
        
        return total_words / total_blocks if total_blocks > 0 else 0.0
    
    def _analyze_language_features(self, text: str) -> Dict[str, Any]:
        """Analyze language features of the text"""
        if not text:
            return {'avg_word_length': 0, 'sentence_count': 0, 'avg_sentence_length': 0}
        
        words = text.split()
        sentences = self._split_sentences(text)
        
        return {
            'avg_word_length': mean([len(word) for word in words]) if words else 0,
            'sentence_count': len(sentences),
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'has_technical_terms': bool(re.search(r'\b[A-Z]{2,}\b', text)),
            'has_numbers': bool(re.search(r'\d+', text))
        }
    
    def _analyze_content_relationships(self, content_features: List[Dict[str, Any]], 
                                     ocr_results: List[OCRResult]) -> List[ContentRelationship]:
        """Analyze relationships between pages based on content"""
        relationships = []
        
        for i in range(len(content_features)):
            for j in range(i + 1, len(content_features)):
                # Analyze text continuity
                continuity_rel = self._analyze_text_continuity(
                    content_features[i], content_features[j])
                if continuity_rel:
                    relationships.append(continuity_rel)
                
                # Analyze heading sequence
                heading_rel = self._analyze_heading_sequence(
                    content_features[i], content_features[j])
                if heading_rel:
                    relationships.append(heading_rel)
                
                # Analyze references
                reference_rel = self._analyze_references(
                    content_features[i], content_features[j])
                if reference_rel:
                    relationships.append(reference_rel)
                
                # Analyze content similarity
                similarity_rel = self._analyze_content_similarity(
                    content_features[i], content_features[j])
                if similarity_rel:
                    relationships.append(similarity_rel)
        
        return relationships
    
    def _analyze_text_continuity(self, page_a: Dict, page_b: Dict) -> Optional[ContentRelationship]:
        """Analyze if text continues from one page to another"""
        if not page_a['text'] or not page_b['text']:
            return None
        
        # Check if last words of page A match first words of page B
        last_words_a = page_a['last_words']
        first_words_b = page_b['first_words']
        
        if not last_words_a or not first_words_b:
            return None
        
        # Calculate word overlap
        overlap_count = 0
        max_check = min(5, len(last_words_a), len(first_words_b))
        
        for i in range(max_check):
            if i < len(last_words_a) and i < len(first_words_b):
                if last_words_a[-(i+1)] == first_words_b[i]:
                    overlap_count += 1
        
        # Check for sentence continuation
        last_sentence_a = page_a['sentences'][-1] if page_a['sentences'] else ""
        first_sentence_b = page_b['sentences'][0] if page_b['sentences'] else ""
        
        sentence_continuation = False
        if last_sentence_a and first_sentence_b:
            # Check if last sentence doesn't end with punctuation (incomplete)
            if not last_sentence_a.rstrip().endswith(('.', '!', '?')):
                sentence_continuation = True
        
        # Calculate confidence
        confidence = 0.0
        if overlap_count > 0:
            confidence += (overlap_count / max_check) * 0.6
        
        if sentence_continuation:
            confidence += 0.4
        
        # Minimum threshold for text continuity
        if confidence >= 0.3:
            evidence = f"Word overlap: {overlap_count}/{max_check}"
            if sentence_continuation:
                evidence += ", sentence continuation detected"
            
            return ContentRelationship(
                page_a_index=page_a['index'],
                page_b_index=page_b['index'],
                relationship_type='continuation',
                confidence=confidence,
                evidence=evidence
            )
        
        return None
    
    def _analyze_heading_sequence(self, page_a: Dict, page_b: Dict) -> Optional[ContentRelationship]:
        """Analyze if headings indicate sequential order"""
        headings_a = page_a['headings']
        headings_b = page_b['headings']
        
        if not headings_a or not headings_b:
            return None
        
        # Look for sequential numbered headings
        for heading_a in headings_a:
            for heading_b in headings_b:
                if heading_a['type'] == heading_b['type']:
                    # Extract numbers from headings
                    num_a = self._extract_number_from_heading(heading_a['text'])
                    num_b = self._extract_number_from_heading(heading_b['text'])
                    
                    if num_a and num_b and num_b == num_a + 1:
                        return ContentRelationship(
                            page_a_index=page_a['index'],
                            page_b_index=page_b['index'],
                            relationship_type='heading_sequence',
                            confidence=0.8,
                            evidence=f"Sequential headings: {heading_a['text']} → {heading_b['text']}"
                        )
        
        return None
    
    def _extract_number_from_heading(self, heading: str) -> Optional[int]:
        """Extract number from heading text"""
        # Try Arabic numbers first
        arabic_match = re.search(r'\d+', heading)
        if arabic_match:
            return int(arabic_match.group())
        
        # Try Roman numerals
        roman_match = re.search(r'\b[IVXLCDMivxlcdm]+\b', heading)
        if roman_match:
            return self._roman_to_int(roman_match.group())
        
        return None
    
    def _roman_to_int(self, roman: str) -> Optional[int]:
        """Convert Roman numeral to integer (simplified)"""
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
    
    def _analyze_references(self, page_a: Dict, page_b: Dict) -> Optional[ContentRelationship]:
        """Analyze cross-references between pages"""
        refs_a = page_a['references']
        refs_b = page_b['references']
        
        # Check if page A references page B or vice versa
        for ref in refs_a:
            if ref['referenced_number'] == page_b['index'] + 1:  # Assuming 1-based page numbers
                return ContentRelationship(
                    page_a_index=page_a['index'],
                    page_b_index=page_b['index'],
                    relationship_type='reference',
                    confidence=0.7,
                    evidence=f"Page {page_a['index']+1} references {ref['text']}"
                )
        
        for ref in refs_b:
            if ref['referenced_number'] == page_a['index'] + 1:
                return ContentRelationship(
                    page_a_index=page_b['index'],
                    page_b_index=page_a['index'],
                    relationship_type='reference',
                    confidence=0.7,
                    evidence=f"Page {page_b['index']+1} references {ref['text']}"
                )
        
        return None
    
    def _analyze_content_similarity(self, page_a: Dict, page_b: Dict) -> Optional[ContentRelationship]:
        """Analyze content similarity between pages"""
        if not page_a['text'] or not page_b['text']:
            return None
        
        # Calculate text similarity using word overlap
        words_a = set(page_a['text'].lower().split())
        words_b = set(page_b['text'].lower().split())
        
        # Remove stop words
        words_a = words_a - self.STOP_WORDS
        words_b = words_b - self.STOP_WORDS
        
        if not words_a or not words_b:
            return None
        
        # Calculate Jaccard similarity
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        similarity = intersection / union if union > 0 else 0
        
        # Only consider high similarity as evidence of relationship
        if similarity >= 0.3:
            return ContentRelationship(
                page_a_index=page_a['index'],
                page_b_index=page_b['index'],
                relationship_type='similar',
                confidence=min(0.6, similarity),
                evidence=f"Content similarity: {similarity:.2f} ({intersection} common words)"
            )
        
        return None
    
    def _apply_content_refinements(self, initial_decisions: List[OrderingDecision],
                                  relationships: List[ContentRelationship],
                                  content_features: List[Dict[str, Any]],
                                  ocr_results: List[OCRResult]) -> List[OrderingDecision]:
        """Apply content-based refinements to ordering decisions"""
        refined_decisions = initial_decisions.copy()
        
        # Create relationship graph
        rel_graph = defaultdict(list)
        for rel in relationships:
            rel_graph[rel.page_a_index].append(rel)
        
        # Apply refinements for uncertain pages
        for i, decision in enumerate(refined_decisions):
            if decision.confidence < 0.7:
                # Look for strong content relationships
                strong_relationships = [rel for rel in rel_graph[i] if rel.confidence > 0.7]
                
                if strong_relationships:
                    # Use the strongest relationship to adjust position
                    best_rel = max(strong_relationships, key=lambda x: x.confidence)
                    
                    if best_rel.relationship_type == 'continuation':
                        # This page should come after the referenced page
                        ref_decision = refined_decisions[best_rel.page_b_index]
                        new_position = ref_decision.assigned_position + 1
                    elif best_rel.relationship_type == 'heading_sequence':
                        # Sequential heading relationship
                        ref_decision = refined_decisions[best_rel.page_b_index]
                        new_position = ref_decision.assigned_position + 1
                    else:
                        continue
                    
                    # Update decision
                    decision.assigned_position = new_position
                    decision.confidence = min(0.9, decision.confidence + best_rel.confidence * 0.3)
                    decision.reasoning += f" + content analysis ({best_rel.relationship_type})"
        
        return refined_decisions
    
    def _validate_and_adjust_ordering(self, decisions: List[OrderingDecision],
                                    relationships: List[ContentRelationship]) -> List[OrderingDecision]:
        """Final validation and adjustment of ordering"""
        # Sort decisions by assigned position
        decisions.sort(key=lambda x: x.assigned_position)
        
        # Check for and resolve any remaining conflicts
        position_counts = Counter(d.assigned_position for d in decisions)
        conflicts = [pos for pos, count in position_counts.items() if count > 1]
        
        if conflicts:
            self.logger.warning(f"Resolving {len(conflicts)} position conflicts after content analysis")
            
            for conflict_pos in conflicts:
                conflicted_decisions = [d for d in decisions if d.assigned_position == conflict_pos]
                
                # Sort by confidence and reassign
                conflicted_decisions.sort(key=lambda x: x.confidence, reverse=True)
                
                for i, decision in enumerate(conflicted_decisions):
                    if i > 0:  # Keep the first (highest confidence) in original position
                        decision.assigned_position = conflict_pos + i
                        decision.reasoning += " (conflict resolution)"
        
        # Final sort
        decisions.sort(key=lambda x: x.assigned_position)
        
        return decisions
    
    def _log_content_analysis_summary(self, relationships: List[ContentRelationship], 
                                    uncertain_pages: List[OrderingDecision]):
        """Log summary of content analysis"""
        if not relationships:
            self.logger.info("No strong content relationships detected")
            return
        
        rel_types = Counter(rel.relationship_type for rel in relationships)
        self.logger.info(f"Content relationships found: {dict(rel_types)}")
        
        strong_rels = [rel for rel in relationships if rel.confidence > 0.7]
        if strong_rels:
            self.logger.info(f"{len(strong_rels)} high-confidence content relationships")
        
        if uncertain_pages:
            improved = len([p for p in uncertain_pages if p.confidence > 0.7])
            if improved > 0:
                self.logger.success(f"Content analysis improved confidence for {improved} pages")
