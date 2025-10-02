"""
Output management system for AI Page Reordering Automation System
Creates ordered PDFs, images, and metadata logs
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from PIL import Image
import cv2
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
import tempfile

from .input_handler import PageInfo
from .ocr_engine import OCRResult
from .numbering_system import OrderingDecision
from utils.config import config

class OutputManager:
    """Manages output generation for reordered pages"""
    
    def __init__(self, logger):
        self.logger = logger
        self.config = config
    
    def create_output(self, ordering_decisions: List[OrderingDecision], 
                     output_path: str, confidence_report: Dict[str, Any],
                     ocr_results: List[OCRResult], input_folder_name: str = None) -> bool:
        """Create all requested output formats"""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        success = True
        
        try:
            # Sort decisions by assigned position
            sorted_decisions = sorted(ordering_decisions, key=lambda x: x.assigned_position)
            
            # Create PDF if requested
            if self.config.get('output.create_pdf', True):
                pdf_success = self._create_pdf_output(sorted_decisions, output_path, input_folder_name)
                success = success and pdf_success
            
            # Create individual images (ALWAYS - as per user request)
            if True:  # Always save organized images
                images_success = self._create_images_output(sorted_decisions, output_path)
                success = success and images_success
            
            # Create metadata log if requested
            if self.config.get('output.create_metadata_log', True):
                log_success = self._create_metadata_log(
                    sorted_decisions, confidence_report, ocr_results, output_path)
                success = success and log_success
            
            # Create summary report
            summary_success = self._create_summary_report(
                sorted_decisions, confidence_report, output_path)
            success = success and summary_success
            
            # Create processing report for debugging
            if self.config.get('output.create_debug_info', False):
                debug_success = self._create_debug_report(
                    sorted_decisions, ocr_results, output_path)
                success = success and debug_success
            
            self.logger.info(f"Output files created in: {output_path}")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to create output: {str(e)}")
            return False
    
    def _create_pdf_output(self, sorted_decisions: List[OrderingDecision], 
                          output_path: Path, input_folder_name: str = None) -> bool:
        """Create PDF with reordered pages"""
        try:
            # Use folder name for PDF if provided
            if input_folder_name:
                pdf_filename = f"{input_folder_name}.pdf"
            else:
                pdf_filename = "reordered_pages.pdf"
            pdf_path = output_path / pdf_filename
            
            self.logger.step(f"Creating PDF: {pdf_path}")
            
            # Get page size from first image
            first_page = sorted_decisions[0].page_info
            if first_page.image:
                page_width, page_height = first_page.image.size
                # Convert pixels to points (72 DPI)
                page_size = (page_width * 72 / 300, page_height * 72 / 300)
            else:
                page_size = A4
            
            # Create PDF
            pdf_canvas = canvas.Canvas(str(pdf_path), pagesize=page_size)
            
            for i, decision in enumerate(sorted_decisions):
                self.logger.progress("Adding pages to PDF", i + 1, len(sorted_decisions))
                
                page_info = decision.page_info
                if not page_info.image:
                    self.logger.warning(f"No image data for {page_info.original_name}")
                    continue
                
                # Convert PIL Image to format suitable for ReportLab
                image_reader = ImageReader(page_info.image)
                
                # Add image to PDF (full page)
                pdf_canvas.drawImage(image_reader, 0, 0, 
                                   width=page_size[0], height=page_size[1])
                
                # Add page number annotation if requested
                if self.config.get('output.add_page_numbers', False):
                    pdf_canvas.setFont("Helvetica", 10)
                    pdf_canvas.drawString(20, 20, f"Page {decision.assigned_position}")
                
                # REMOVED: Confidence annotation - users don't need to see this
                
                # Start new page (except for last page)
                if i < len(sorted_decisions) - 1:
                    pdf_canvas.showPage()
            
            pdf_canvas.save()
            self.logger.success(f"PDF created: {pdf_path}")
            
            # Compress PDF if requested
            if self.config.get('output.compress_pdf', False):
                self.logger.info("Compressing PDF...")
                compressed_path = self._compress_pdf(pdf_path)
                if compressed_path:
                    original_size = pdf_path.stat().st_size / (1024 * 1024)
                    compressed_size = compressed_path.stat().st_size / (1024 * 1024)
                    reduction = ((original_size - compressed_size) / original_size) * 100
                    self.logger.success(f"PDF compressed: {original_size:.1f}MB → {compressed_size:.1f}MB ({reduction:.1f}% reduction)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create PDF: {str(e)}")
            return False
    
    def _create_images_output(self, sorted_decisions: List[OrderingDecision], 
                             output_path: Path) -> bool:
        """Create individual image files in correct order"""
        try:
            # Save images directly in output folder (not subfolder)
            images_dir = output_path
            images_dir.mkdir(exist_ok=True)
            
            self.logger.step(f"Creating ordered images: {images_dir}")
            
            for i, decision in enumerate(sorted_decisions):
                self.logger.progress("Saving ordered images", i + 1, len(sorted_decisions))
                
                page_info = decision.page_info
                if not page_info.image:
                    continue
                
                # Create filename with ordering position
                original_name = Path(page_info.original_name).stem
                extension = Path(page_info.original_name).suffix or '.png'
                ordered_filename = f"{decision.assigned_position:03d}_{original_name}{extension}"
                
                # Save image
                image_path = images_dir / ordered_filename
                
                # Preserve original quality if requested
                if self.config.get('output.preserve_original_quality', True):
                    # Save with high quality
                    if extension.lower() in ['.jpg', '.jpeg']:
                        page_info.image.save(image_path, quality=95, optimize=True)
                    else:
                        page_info.image.save(image_path)
                else:
                    # Standard quality
                    page_info.image.save(image_path)
            
            self.logger.success(f"Ordered images saved to: {images_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create ordered images: {str(e)}")
            return False
    
    def _create_metadata_log(self, sorted_decisions: List[OrderingDecision],
                           confidence_report: Dict[str, Any],
                           ocr_results: List[OCRResult],
                           output_path: Path) -> bool:
        """Create detailed metadata log"""
        try:
            log_path = output_path / "reordering_log.json"
            
            self.logger.step(f"Creating metadata log: {log_path}")
            
            # Build comprehensive metadata
            metadata = {
                'reordering_summary': {
                    'timestamp': datetime.now().isoformat(),
                    'total_pages': len(sorted_decisions),
                    'overall_confidence': confidence_report.get('overall_confidence', 0),
                    'pages_reviewed': len(confidence_report.get('review_pages', [])),
                    'processing_time': self._calculate_total_processing_time(ocr_results)
                },
                'configuration': {
                    'preprocessing_enabled': self.config.get('default_settings.enable_preprocessing', True),
                    'ocr_settings': {
                        'language': self.config.get('ocr.language', 'eng'),
                        'engine_mode': self.config.get('ocr.engine_mode', 3),
                        'confidence_threshold': self.config.get('default_settings.ocr_confidence_threshold', 85)
                    },
                    'numbering_detection': {
                        'arabic': self.config.get('numbering.detect_arabic', True),
                        'roman': self.config.get('numbering.detect_roman', True),
                        'hybrid': self.config.get('numbering.detect_hybrid', True),
                        'hierarchical': self.config.get('numbering.detect_hierarchical', True)
                    }
                },
                'page_details': []
            }
            
            # Add detailed information for each page
            for decision in sorted_decisions:
                # Find corresponding OCR result
                ocr_result = None
                for ocr in ocr_results:
                    if ocr.page_info == decision.page_info:
                        ocr_result = ocr
                        break
                
                page_detail = {
                    'original_filename': decision.page_info.original_name,
                    'assigned_position': decision.assigned_position,
                    'confidence': decision.confidence,
                    'reasoning': decision.reasoning,
                    'detected_numbers': [],
                    'alternative_positions': decision.alternative_positions,
                    'ocr_info': {},
                    'preprocessing_applied': decision.page_info.processing_history
                }
                
                # Add detected numbers information
                for num_info in decision.detected_numbers:
                    page_detail['detected_numbers'].append({
                        'text': num_info.text,
                        'type': num_info.number_type,
                        'numeric_value': num_info.numeric_value,
                        'confidence': num_info.confidence,
                        'context': num_info.context[:100] + '...' if len(num_info.context) > 100 else num_info.context
                    })
                
                # Add OCR information
                if ocr_result:
                    page_detail['ocr_info'] = {
                        'text_length': len(ocr_result.full_text),
                        'word_count': len(ocr_result.full_text.split()),
                        'language_confidence': ocr_result.language_confidence,
                        'processing_time': ocr_result.processing_time,
                        'text_blocks_count': len(ocr_result.text_blocks)
                    }
                
                metadata['page_details'].append(page_detail)
            
            # Add confidence report
            metadata['confidence_assessment'] = self._serialize_confidence_report(confidence_report)
            
            # Save metadata
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.success(f"Metadata log created: {log_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create metadata log: {str(e)}")
            return False
    
    def _create_summary_report(self, sorted_decisions: List[OrderingDecision],
                             confidence_report: Dict[str, Any],
                             output_path: Path) -> bool:
        """Create human-readable summary report"""
        try:
            report_path = output_path / "reordering_summary.txt"
            
            self.logger.step(f"Creating summary report: {report_path}")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("=" * 60 + "\n")
                f.write("AI PAGE REORDERING AUTOMATION - SUMMARY REPORT\n")
                f.write("=" * 60 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Overall Results
                f.write("OVERALL RESULTS\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total pages processed: {len(sorted_decisions)}\n")
                f.write(f"Overall confidence: {confidence_report.get('overall_confidence', 0):.1f}%\n")
                f.write(f"Pages needing review: {len(confidence_report.get('review_pages', []))}\n")
                
                if confidence_report.get('needs_human_review', False):
                    f.write("⚠️  HUMAN REVIEW RECOMMENDED\n")
                else:
                    f.write("✅ Automatic ordering appears reliable\n")
                f.write("\n")
                
                # Confidence Breakdown
                metrics = confidence_report.get('metrics', {})
                if metrics:
                    f.write("CONFIDENCE BREAKDOWN\n")
                    f.write("-" * 20 + "\n")
                    f.write(f"High confidence pages: {getattr(metrics, 'high_confidence_pages', 0)}\n")
                    f.write(f"Medium confidence pages: {getattr(metrics, 'medium_confidence_pages', 0)}\n")
                    f.write(f"Low confidence pages: {getattr(metrics, 'low_confidence_pages', 0)}\n")
                    f.write(f"Numbering detection: {getattr(metrics, 'numbering_confidence', 0):.1f}%\n")
                    f.write(f"Sequence quality: {getattr(metrics, 'sequence_confidence', 0):.1f}%\n")
                    f.write("\n")
                
                # Page Order
                f.write("FINAL PAGE ORDER\n")
                f.write("-" * 20 + "\n")
                for decision in sorted_decisions:
                    confidence_indicator = "✅" if decision.confidence > 0.8 else "⚠️" if decision.confidence > 0.5 else "❌"
                    f.write(f"{decision.assigned_position:3d}. {decision.page_info.original_name} "
                           f"{confidence_indicator} ({decision.confidence:.1%})\n")
                f.write("\n")
                
                # Issues and Recommendations
                recommendations = confidence_report.get('recommendations', [])
                if recommendations:
                    f.write("RECOMMENDATIONS\n")
                    f.write("-" * 20 + "\n")
                    for i, rec in enumerate(recommendations[:10], 1):  # Top 10 recommendations
                        f.write(f"{i}. {rec.get('title', 'Unknown')}\n")
                        f.write(f"   {rec.get('description', '')}\n")
                        f.write(f"   Action: {rec.get('action', '')}\n\n")
                
                # Pages Needing Review
                review_pages = confidence_report.get('review_pages', [])
                if review_pages:
                    f.write("PAGES REQUIRING REVIEW\n")
                    f.write("-" * 30 + "\n")
                    for page_idx in review_pages[:10]:  # Top 10 problematic pages
                        decision = sorted_decisions[page_idx] if page_idx < len(sorted_decisions) else None
                        if decision:
                            f.write(f"• {decision.page_info.original_name} (Position {decision.assigned_position})\n")
                            f.write(f"  Confidence: {decision.confidence:.1%}\n")
                            f.write(f"  Reason: {decision.reasoning}\n\n")
                
                # Footer
                f.write("=" * 60 + "\n")
                f.write("For detailed technical information, see reordering_log.json\n")
                f.write("=" * 60 + "\n")
            
            self.logger.success(f"Summary report created: {report_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create summary report: {str(e)}")
            return False
    
    def _create_debug_report(self, sorted_decisions: List[OrderingDecision],
                           ocr_results: List[OCRResult],
                           output_path: Path) -> bool:
        """Create detailed debug information"""
        try:
            debug_dir = output_path / "debug"
            debug_dir.mkdir(exist_ok=True)
            
            # Save OCR results for each page
            for i, ocr_result in enumerate(ocr_results):
                debug_file = debug_dir / f"page_{i+1:03d}_ocr_debug.json"
                
                debug_data = {
                    'page_info': {
                        'original_name': ocr_result.page_info.original_name,
                        'processing_history': ocr_result.page_info.processing_history,
                        'metadata': ocr_result.page_info.metadata
                    },
                    'ocr_results': {
                        'full_text': ocr_result.full_text,
                        'language_confidence': ocr_result.language_confidence,
                        'processing_time': ocr_result.processing_time,
                        'text_blocks_count': len(ocr_result.text_blocks)
                    },
                    'detected_numbers': [
                        {
                            'text': num.text,
                            'type': num.number_type,
                            'value': num.numeric_value,
                            'confidence': num.confidence,
                            'position': num.position,
                            'context': num.context
                        }
                        for num in ocr_result.detected_numbers
                    ]
                }
                
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(debug_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.success(f"Debug information saved to: {debug_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create debug report: {str(e)}")
            return False
    
    def _calculate_total_processing_time(self, ocr_results: List[OCRResult]) -> float:
        """Calculate total processing time from OCR results"""
        return sum(result.processing_time for result in ocr_results)
    
    def _serialize_confidence_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize confidence report for JSON output"""
        serialized = {}
        
        for key, value in report.items():
            if hasattr(value, '__dict__'):
                # Convert dataclass to dict
                serialized[key] = value.__dict__
            elif isinstance(value, list):
                serialized[key] = [
                    item.__dict__ if hasattr(item, '__dict__') else item 
                    for item in value
                ]
            else:
                serialized[key] = value
        
        return serialized
    
    def create_comparison_output(self, original_order: List[PageInfo], 
                               final_order: List[OrderingDecision],
                               output_path: Path) -> bool:
        """Create side-by-side comparison of original vs reordered"""
        try:
            comparison_path = output_path / "order_comparison.html"
            
            with open(comparison_path, 'w', encoding='utf-8') as f:
                f.write(self._generate_comparison_html(original_order, final_order))
            
            self.logger.success(f"Order comparison created: {comparison_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create comparison output: {str(e)}")
            return False
    
    def _generate_comparison_html(self, original_order: List[PageInfo],
                                final_order: List[OrderingDecision]) -> str:
        """Generate HTML comparison of original vs final order"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Page Order Comparison</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { display: flex; gap: 20px; }
                .column { flex: 1; }
                .page-item { padding: 8px; margin: 4px 0; border: 1px solid #ddd; border-radius: 4px; }
                .high-confidence { background-color: #d4edda; }
                .medium-confidence { background-color: #fff3cd; }
                .low-confidence { background-color: #f8d7da; }
                .page-number { font-weight: bold; }
                .confidence { font-size: 0.9em; color: #666; }
            </style>
        </head>
        <body>
            <h1>Page Order Comparison</h1>
            <div class="container">
                <div class="column">
                    <h2>Original Order</h2>
        """
        
        # Original order
        for i, page in enumerate(original_order, 1):
            html += f"""
                    <div class="page-item">
                        <span class="page-number">{i}.</span> {page.original_name}
                    </div>
            """
        
        html += """
                </div>
                <div class="column">
                    <h2>Final Order</h2>
        """
        
        # Final order
        for decision in sorted(final_order, key=lambda x: x.assigned_position):
            confidence_class = "high-confidence" if decision.confidence > 0.8 else \
                             "medium-confidence" if decision.confidence > 0.5 else "low-confidence"
            
            html += f"""
                    <div class="page-item {confidence_class}">
                        <span class="page-number">{decision.assigned_position}.</span> 
                        {decision.page_info.original_name}
                        <div class="confidence">Confidence: {decision.confidence:.1%}</div>
                    </div>
            """
        
        return html
    
    def _compress_pdf(self, pdf_path: Path) -> Optional[Path]:
        """Compress PDF file to reduce size"""
        try:
            from PyPDF2 import PdfReader, PdfWriter
            
            reader = PdfReader(str(pdf_path))
            writer = PdfWriter()
            
            # Copy pages with compression
            for page in reader.pages:
                page.compress_content_streams()
                writer.add_page(page)
            
            # Write compressed PDF
            temp_path = pdf_path.with_suffix('.tmp.pdf')
            with open(temp_path, 'wb') as f:
                writer.write(f)
            
            # Replace original with compressed
            temp_path.replace(pdf_path)
            
            return pdf_path
            
        except Exception as e:
            self.logger.warning(f"PDF compression failed: {e}")
            return None
