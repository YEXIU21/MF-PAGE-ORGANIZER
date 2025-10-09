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

# Try to import img2pdf for fast PDF creation
try:
    import img2pdf
    HAS_IMG2PDF = True
except ImportError:
    HAS_IMG2PDF = False

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
        """Create PDF with reordered pages using optimal method"""
        try:
            # Use folder name for PDF if provided
            if input_folder_name:
                pdf_filename = f"{input_folder_name}.pdf"
            else:
                pdf_filename = "reordered_pages.pdf"
            pdf_path = output_path / pdf_filename
            
            self.logger.step(f"Creating PDF: {pdf_path}")
            
            # Check if we need page annotations
            needs_annotations = self.config.get('output.add_page_numbers', False)
            
            # Use fast img2pdf method if available and no annotations needed
            if HAS_IMG2PDF and not needs_annotations:
                try:
                    self.logger.info("Using optimized PDF creation (img2pdf)")
                    return self._create_pdf_fast(sorted_decisions, pdf_path)
                except Exception as e:
                    self.logger.warning(f"Fast PDF creation failed: {e}, falling back to standard method")
            
            # Fall back to standard ReportLab method
            self.logger.info("Using standard PDF creation (ReportLab)")
            return self._create_pdf_standard(sorted_decisions, pdf_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create PDF: {str(e)}")
            return False
    
    def _create_pdf_standard(self, sorted_decisions: List[OrderingDecision], pdf_path: Path) -> bool:
        """Create PDF using ReportLab (standard method with annotations support)"""
        try:
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
            self.logger.error(f"Failed to create standard PDF: {str(e)}")
            return False
    
    def _create_pdf_fast(self, sorted_decisions: List[OrderingDecision], pdf_path: Path) -> bool:
        """Create PDF using img2pdf (fast method for image-only PDFs)"""
        try:
            import io
            
            # Collect images in order
            image_data_list = []
            
            for i, decision in enumerate(sorted_decisions):
                self.logger.progress("Adding pages to PDF (fast)", i + 1, len(sorted_decisions))
                
                page_info = decision.page_info
                if not page_info.image:
                    self.logger.warning(f"No image data for {page_info.original_name}")
                    continue
                
                # Convert PIL Image to bytes for img2pdf
                img_bytes = io.BytesIO()
                
                # Save as JPEG for best compatibility
                if page_info.image.mode == 'RGBA':
                    # Convert RGBA to RGB (JPEG doesn't support transparency)
                    rgb_image = page_info.image.convert('RGB')
                    rgb_image.save(img_bytes, format='JPEG', quality=95)
                elif page_info.image.mode == 'P':
                    # Convert palette to RGB
                    rgb_image = page_info.image.convert('RGB')
                    rgb_image.save(img_bytes, format='JPEG', quality=95)
                else:
                    page_info.image.save(img_bytes, format='JPEG', quality=95)
                
                img_bytes.seek(0)
                image_data_list.append(img_bytes.getvalue())
            
            # Create PDF from images in one shot
            self.logger.info(f"Combining {len(image_data_list)} pages into PDF...")
            pdf_bytes = img2pdf.convert(image_data_list)
            
            # Write PDF to file
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
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
            self.logger.error(f"Failed to create fast PDF: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise  # Re-raise to trigger fallback
    
    def _create_images_output(self, sorted_decisions: List[OrderingDecision], 
                             output_path: Path) -> bool:
        """Create individual image files in correct order with ISBN naming convention"""
        try:
            # Save images directly in output folder (not subfolder)
            images_dir = output_path
            images_dir.mkdir(exist_ok=True)
            
            self.logger.step(f"Creating ordered images: {images_dir}")
            
            # Extract ISBN from first page filename (e.g., "9780632046584_Page_001.jpg" -> "9780632046584")
            if sorted_decisions and sorted_decisions[0].page_info:
                first_filename = sorted_decisions[0].page_info.original_name
                # Try to extract ISBN (numbers before first underscore)
                parts = first_filename.split('_')
                if parts and parts[0].isdigit():
                    file_prefix = parts[0]  # Use ISBN as prefix
                else:
                    file_prefix = self.config.get('output.file_prefix', 'page')
            else:
                file_prefix = self.config.get('output.file_prefix', 'page')
            
            for i, decision in enumerate(sorted_decisions):
                self.logger.progress("Saving ordered images", i + 1, len(sorted_decisions))
                
                page_info = decision.page_info
                if not page_info.image:
                    continue
                
                # Get output format from config (TIF or JPG)
                output_format = self.config.get('output.image_format', 'tif')
                convert_to_300dpi = self.config.get('output.convert_to_300dpi', True)
                
                extension = f'.{output_format}'
                # Use 5-digit padding for page numbers (00001, 00002, etc.)
                ordered_filename = f"{file_prefix}_{decision.assigned_position:05d}{extension}"
                
                # Save image
                image_path = images_dir / ordered_filename
                
                # STAGE: Process based on format selection
                if convert_to_300dpi:
                    # Convert to 300 DPI (both TIF and JPG)
                    self.logger.debug(f"Converting {page_info.original_name} to 300 DPI {output_format.upper()}...")
                    image_300dpi = self._convert_to_300dpi(page_info.image)
                    
                    if output_format == 'tif':
                        # TIF format with lossless compression
                        image_300dpi.save(image_path, 
                                         format='TIFF',
                                         compression='tiff_lzw',
                                         dpi=(300, 300))
                    else:
                        # JPG format with 300 DPI
                        image_300dpi.save(image_path, 
                                         format='JPEG',
                                         quality=95,
                                         optimize=True,
                                         dpi=(300, 300))
                else:
                    # Save with original DPI (fallback)
                    self.logger.debug(f"Saving {page_info.original_name} as {output_format.upper()} (original DPI)...")
                    if output_format == 'jpg':
                        page_info.image.save(image_path, quality=95, optimize=True)
                    else:
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
    
    def _convert_to_300dpi(self, image: Image.Image) -> Image.Image:
        """Convert image to 300 DPI regardless of original DPI"""
        try:
            # Get current DPI (default to 72 if not set)
            current_dpi = image.info.get('dpi', (72, 72))
            if isinstance(current_dpi, (int, float)):
                current_dpi = (current_dpi, current_dpi)
            
            current_dpi_x, current_dpi_y = current_dpi
            
            # If already 300 DPI, return as is
            if current_dpi_x == 300 and current_dpi_y == 300:
                return image
            
            # Calculate scaling factor to achieve 300 DPI
            scale_x = 300 / current_dpi_x
            scale_y = 300 / current_dpi_y
            
            # Get current size
            width, height = image.size
            
            # Calculate new size for 300 DPI
            new_width = int(width * scale_x)
            new_height = int(height * scale_y)
            
            # Resize image using high-quality resampling
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            self.logger.debug(f"Converted from {current_dpi_x}x{current_dpi_y} DPI to 300x300 DPI "
                            f"(size: {width}x{height} → {new_width}x{new_height})")
            
            return resized_image
            
        except Exception as e:
            self.logger.warning(f"DPI conversion failed, using original: {e}")
            return image
