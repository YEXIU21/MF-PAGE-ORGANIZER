"""
Confidence system and error handling for AI Page Reordering Automation System
Evaluates ordering decisions and provides recommendations for human review
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from statistics import mean, stdev
from collections import Counter
import json

from .input_handler import PageInfo
from .ocr_engine import OCRResult
from .numbering_system import OrderingDecision
from utils.config import config

@dataclass
class ConfidenceMetrics:
    """Detailed confidence metrics for ordering decisions"""
    overall_confidence: float
    numbering_confidence: float
    content_confidence: float
    sequence_confidence: float
    ocr_confidence: float
    page_count: int
    high_confidence_pages: int
    medium_confidence_pages: int
    low_confidence_pages: int
    problematic_pages: List[int]
    recommendations: List[str]

@dataclass
class PageAssessment:
    """Assessment of individual page ordering confidence"""
    page_index: int
    page_name: str
    assigned_position: int
    confidence_score: float
    confidence_level: str  # 'high', 'medium', 'low'
    issues: List[str]
    evidence: List[str]
    needs_review: bool

class ConfidenceSystem:
    """System for evaluating and scoring ordering confidence"""
    
    def __init__(self, logger):
        self.logger = logger
        self.config = config
        self.confidence_threshold = self.config.get('content_analysis.min_confidence_for_auto_order', 90)
    
    def evaluate_ordering(self, ordering_decisions: List[OrderingDecision], 
                         ocr_results: List[OCRResult]) -> Dict[str, Any]:
        """Evaluate the confidence of ordering decisions"""
        self.logger.step("Evaluating ordering confidence")
        
        # Assess individual pages
        page_assessments = []
        for decision in ordering_decisions:
            assessment = self._assess_page_confidence(decision, ocr_results)
            page_assessments.append(assessment)
        
        # Calculate overall metrics
        confidence_metrics = self._calculate_confidence_metrics(page_assessments, ordering_decisions)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(confidence_metrics, page_assessments)
        
        # Create comprehensive report
        confidence_report = {
            'overall_confidence': confidence_metrics.overall_confidence,
            'metrics': confidence_metrics,
            'page_assessments': page_assessments,
            'recommendations': recommendations,
            'needs_human_review': confidence_metrics.overall_confidence < self.confidence_threshold,
            'review_pages': [a.page_index for a in page_assessments if a.needs_review],
            'summary': self._create_confidence_summary(confidence_metrics)
        }
        
        self._log_confidence_report(confidence_report)
        return confidence_report
    
    def _assess_page_confidence(self, decision: OrderingDecision, 
                               ocr_results: List[OCRResult]) -> PageAssessment:
        """Assess confidence for a single page ordering decision"""
        issues = []
        evidence = []
        
        # Base confidence from decision
        confidence = decision.confidence
        
        # Get OCR result for this page
        page_ocr = None
        for ocr_result in ocr_results:
            if ocr_result.page_info == decision.page_info:
                page_ocr = ocr_result
                break
        
        # Factor 1: OCR quality assessment
        if page_ocr:
            ocr_confidence = page_ocr.language_confidence / 100.0
            confidence = (confidence + ocr_confidence) / 2
            
            if ocr_confidence < 0.6:
                issues.append("Low OCR quality")
            else:
                evidence.append(f"Good OCR quality ({ocr_confidence:.1%})")
            
            # Check for text content
            if not page_ocr.full_text.strip():
                issues.append("No text detected")
                confidence *= 0.5
            elif len(page_ocr.full_text.split()) < 10:
                issues.append("Very little text content")
                confidence *= 0.8
            else:
                evidence.append(f"{len(page_ocr.full_text.split())} words detected")
        
        # Factor 2: Number detection assessment
        if decision.detected_numbers:
            num_confidences = [num.confidence for num in decision.detected_numbers]
            avg_num_confidence = mean(num_confidences) / 100.0
            
            if avg_num_confidence > 0.8:
                evidence.append(f"Strong number detection ({avg_num_confidence:.1%})")
            elif avg_num_confidence < 0.5:
                issues.append("Weak number detection")
                confidence *= 0.8
            
            # Check for conflicting numbers
            unique_positions = set(num.numeric_value for num in decision.detected_numbers 
                                 if num.numeric_value is not None)
            if len(unique_positions) > 1:
                issues.append(f"Conflicting page numbers: {sorted(unique_positions)}")
                confidence *= 0.7
        else:
            issues.append("No page numbers detected")
            confidence *= 0.6
        
        # Factor 3: Position reasonableness
        if decision.assigned_position <= 0:
            issues.append("Invalid position assigned")
            confidence = 0.1
        elif decision.assigned_position > len(ocr_results) * 2:  # Unreasonably high
            issues.append("Position seems too high")
            confidence *= 0.7
        
        # Factor 4: Alternative positions availability
        if len(decision.alternative_positions) > 3:
            issues.append("Many alternative positions suggest uncertainty")
            confidence *= 0.9
        elif len(decision.alternative_positions) == 0:
            issues.append("No alternative positions available")
            confidence *= 0.8
        
        # Determine confidence level
        if confidence >= 0.8:
            confidence_level = 'high'
            needs_review = False
        elif confidence >= 0.5:
            confidence_level = 'medium'
            needs_review = confidence < 0.7
        else:
            confidence_level = 'low'
            needs_review = True
        
        return PageAssessment(
            page_index=ocr_results.index(page_ocr) if page_ocr else -1,
            page_name=decision.page_info.original_name,
            assigned_position=decision.assigned_position,
            confidence_score=confidence,
            confidence_level=confidence_level,
            issues=issues,
            evidence=evidence,
            needs_review=needs_review
        )
    
    def _calculate_confidence_metrics(self, assessments: List[PageAssessment], 
                                    decisions: List[OrderingDecision]) -> ConfidenceMetrics:
        """Calculate overall confidence metrics"""
        if not assessments:
            return ConfidenceMetrics(
                overall_confidence=0.0,
                numbering_confidence=0.0,
                content_confidence=0.0,
                sequence_confidence=0.0,
                ocr_confidence=0.0,
                page_count=0,
                high_confidence_pages=0,
                medium_confidence_pages=0,
                low_confidence_pages=0,
                problematic_pages=[],
                recommendations=["No pages to assess"]
            )
        
        # Overall confidence (weighted average)
        confidences = [a.confidence_score for a in assessments]
        overall_confidence = mean(confidences) * 100
        
        # Confidence level counts
        level_counts = Counter(a.confidence_level for a in assessments)
        high_conf = level_counts.get('high', 0)
        medium_conf = level_counts.get('medium', 0)
        low_conf = level_counts.get('low', 0)
        
        # Numbering confidence (based on detected numbers)
        pages_with_numbers = len([d for d in decisions if d.detected_numbers])
        numbering_confidence = (pages_with_numbers / len(decisions)) * 100 if decisions else 0
        
        # Content confidence (based on reasoning)
        content_enhanced = len([d for d in decisions if 'content analysis' in d.reasoning])
        content_confidence = min(100, overall_confidence + (content_enhanced / len(decisions)) * 20)
        
        # Sequence confidence (how well ordered the positions are)
        positions = [a.assigned_position for a in assessments]
        positions.sort()
        gaps = sum(1 for i in range(len(positions)-1) if positions[i+1] - positions[i] > 1)
        sequence_confidence = max(0, 100 - (gaps * 10))  # Penalize gaps
        
        # OCR confidence (would need OCR results to calculate properly)
        ocr_confidence = overall_confidence  # Simplified for now
        
        # Problematic pages
        problematic_pages = [a.page_index for a in assessments if a.needs_review]
        
        # Basic recommendations
        recommendations = []
        if low_conf > 0:
            recommendations.append(f"{low_conf} pages need manual review")
        if gaps > len(positions) * 0.2:
            recommendations.append("Many gaps in sequence - check for missing pages")
        if overall_confidence < 70:
            recommendations.append("Consider using GUI mode for interactive review")
        
        return ConfidenceMetrics(
            overall_confidence=overall_confidence,
            numbering_confidence=numbering_confidence,
            content_confidence=content_confidence,
            sequence_confidence=sequence_confidence,
            ocr_confidence=ocr_confidence,
            page_count=len(assessments),
            high_confidence_pages=high_conf,
            medium_confidence_pages=medium_conf,
            low_confidence_pages=low_conf,
            problematic_pages=problematic_pages,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, metrics: ConfidenceMetrics, 
                                 assessments: List[PageAssessment]) -> List[Dict[str, Any]]:
        """Generate detailed recommendations based on assessment"""
        recommendations = []
        
        # Overall confidence recommendations
        if metrics.overall_confidence < 50:
            recommendations.append({
                'type': 'critical',
                'title': 'Very Low Confidence',
                'description': 'The ordering has very low confidence. Manual review is strongly recommended.',
                'action': 'Use GUI mode or manually verify page order',
                'priority': 'high'
            })
        elif metrics.overall_confidence < 70:
            recommendations.append({
                'type': 'warning',
                'title': 'Low Confidence',
                'description': 'The ordering has low confidence. Review recommended.',
                'action': 'Check pages marked for review',
                'priority': 'medium'
            })
        
        # Numbering-specific recommendations
        if metrics.numbering_confidence < 50:
            recommendations.append({
                'type': 'info',
                'title': 'Poor Number Detection',
                'description': 'Few pages have detectable page numbers.',
                'action': 'Consider preprocessing options or manual numbering',
                'priority': 'medium'
            })
        
        # Sequence-specific recommendations
        if metrics.sequence_confidence < 70:
            recommendations.append({
                'type': 'warning',
                'title': 'Sequence Gaps',
                'description': 'There are gaps in the page sequence.',
                'action': 'Check for missing pages or numbering issues',
                'priority': 'medium'
            })
        
        # Page-specific recommendations
        problematic_assessments = [a for a in assessments if a.needs_review]
        if problematic_assessments:
            for assessment in problematic_assessments[:5]:  # Top 5 most problematic
                recommendations.append({
                    'type': 'page_review',
                    'title': f'Review Page: {assessment.page_name}',
                    'description': f'Issues: {", ".join(assessment.issues)}',
                    'action': f'Manually verify position {assessment.assigned_position}',
                    'priority': 'low' if assessment.confidence_score > 0.3 else 'medium',
                    'page_index': assessment.page_index
                })
        
        # Processing recommendations
        if metrics.ocr_confidence < 60:
            recommendations.append({
                'type': 'processing',
                'title': 'Poor OCR Quality',
                'description': 'OCR results are of poor quality.',
                'action': 'Try preprocessing options: denoise, deskew, contrast enhancement',
                'priority': 'low'
            })
        
        return recommendations
    
    def _create_confidence_summary(self, metrics: ConfidenceMetrics) -> str:
        """Create a human-readable confidence summary"""
        if metrics.overall_confidence >= 85:
            quality = "Excellent"
        elif metrics.overall_confidence >= 70:
            quality = "Good"
        elif metrics.overall_confidence >= 50:
            quality = "Fair"
        else:
            quality = "Poor"
        
        summary = f"{quality} ordering confidence ({metrics.overall_confidence:.1f}%). "
        summary += f"{metrics.high_confidence_pages} high, {metrics.medium_confidence_pages} medium, "
        summary += f"{metrics.low_confidence_pages} low confidence pages."
        
        if metrics.problematic_pages:
            summary += f" {len(metrics.problematic_pages)} pages need review."
        
        return summary
    
    def _log_confidence_report(self, report: Dict[str, Any]):
        """Log confidence assessment results"""
        metrics = report['metrics']
        
        self.logger.info(f"Confidence Assessment Results:")
        self.logger.info(f"  Overall: {metrics.overall_confidence:.1f}%")
        self.logger.info(f"  Numbering: {metrics.numbering_confidence:.1f}%")
        self.logger.info(f"  Sequence: {metrics.sequence_confidence:.1f}%")
        
        self.logger.info(f"  Page Breakdown:")
        self.logger.info(f"    High confidence: {metrics.high_confidence_pages}")
        self.logger.info(f"    Medium confidence: {metrics.medium_confidence_pages}")
        self.logger.info(f"    Low confidence: {metrics.low_confidence_pages}")
        
        if report['needs_human_review']:
            self.logger.warning("⚠️  Human review recommended")
            self.logger.info(f"Pages needing review: {report['review_pages']}")
        else:
            self.logger.success("✅ Automatic ordering appears reliable")
        
        # Log top recommendations
        high_priority_recs = [r for r in report['recommendations'] if r.get('priority') == 'high']
        if high_priority_recs:
            self.logger.warning("High priority recommendations:")
            for rec in high_priority_recs[:3]:
                self.logger.warning(f"  • {rec['title']}: {rec['action']}")
    
    def save_confidence_report(self, report: Dict[str, Any], output_path: str) -> bool:
        """Save detailed confidence report to file"""
        try:
            # Convert dataclasses to dictionaries for JSON serialization
            serializable_report = self._make_serializable(report)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_report, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Confidence report saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save confidence report: {e}")
            return False
    
    def _make_serializable(self, obj) -> Any:
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (ConfidenceMetrics, PageAssessment)):
            return self._make_serializable(obj.__dict__)
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        else:
            return obj
    
    def create_review_interface_data(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Create data structure suitable for GUI review interface"""
        pages_for_review = []
        
        for assessment in report['page_assessments']:
            if assessment.needs_review:
                page_data = {
                    'index': assessment.page_index,
                    'name': assessment.page_name,
                    'current_position': assessment.assigned_position,
                    'confidence': assessment.confidence_score,
                    'issues': assessment.issues,
                    'evidence': assessment.evidence,
                    'suggested_actions': []
                }
                
                # Add suggested actions based on issues
                if "No page numbers detected" in assessment.issues:
                    page_data['suggested_actions'].append("Check for page numbers in margins or headers")
                if "Low OCR quality" in assessment.issues:
                    page_data['suggested_actions'].append("Try image preprocessing options")
                if "Conflicting page numbers" in assessment.issues:
                    page_data['suggested_actions'].append("Manually select the correct page number")
                
                pages_for_review.append(page_data)
        
        return {
            'summary': report['summary'],
            'overall_confidence': report['overall_confidence'],
            'needs_review': report['needs_human_review'],
            'total_pages': len(report['page_assessments']),
            'pages_for_review': pages_for_review,
            'recommendations': [r for r in report['recommendations'] if r.get('priority') in ['high', 'medium']],
            'auto_suggestions': self._generate_auto_suggestions(report)
        }
    
    def _generate_auto_suggestions(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate automatic suggestions for common issues"""
        suggestions = []
        metrics = report['metrics']
        
        if metrics.numbering_confidence < 40:
            suggestions.append({
                'type': 'preprocessing',
                'title': 'Enable OCR Enhancement',
                'description': 'Try enabling denoising and contrast enhancement',
                'settings': {'denoise': True, 'contrast_enhance': True}
            })
        
        if metrics.sequence_confidence < 60:
            suggestions.append({
                'type': 'ordering',
                'title': 'Use Content Analysis',
                'description': 'Enable content-based ordering for missing numbers',
                'settings': {'content_analysis_weight': 0.6}
            })
        
        low_conf_pages = [a for a in report['page_assessments'] if a.confidence_level == 'low']
        if len(low_conf_pages) > len(report['page_assessments']) * 0.3:
            suggestions.append({
                'type': 'processing',
                'title': 'Try Different OCR Settings',
                'description': 'Experiment with different OCR engine modes',
                'settings': {'ocr_engine_mode': 1, 'page_segmentation': 3}
            })
        
        return suggestions
