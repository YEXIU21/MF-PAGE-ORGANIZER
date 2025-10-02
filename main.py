#!/usr/bin/env python3
"""
AI Page Reordering Automation System - Command Line Interface
Main entry point for the page reordering automation system.
"""

import argparse
import sys
import traceback
from pathlib import Path
from typing import List, Optional


try:
    from utils.config import config
    from utils.logger import create_logger, ProcessLogger
    from core.input_handler import InputHandler
    from core.preprocessor import Preprocessor
    from core.ocr_engine import OCREngine
    from core.numbering_system import NumberingSystem
    from core.content_analyzer import ContentAnalyzer
    from core.confidence_system import ConfidenceSystem
    from core.output_manager import OutputManager
    from core.blank_page_detector import BlankPageDetector
    from core.performance_optimizer import PerformanceOptimizer
    from core.ai_learning import AILearningSystem
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

class PageReorderCLI:
    """Command Line Interface for Page Reordering System"""
    
    def __init__(self):
        self.logger = None
        self.input_handler = None
        self.preprocessor = None
        self.ocr_engine = None
        self.numbering_system = None
        self.content_analyzer = None
        self.confidence_system = None
        self.output_manager = None
    
    def setup_components(self, args):
        """Initialize all system components"""
        # Update config from command line arguments
        config.update_from_args(args)
        
        # Setup logger
        log_file = f"logs/page_reorder_{Path(args.input).stem}.log" if args.log else None
        self.logger = create_logger(log_file=log_file, verbose=args.verbose)
        
        # Initialize components
        self.input_handler = InputHandler(self.logger)
        self.preprocessor = Preprocessor(self.logger)
        self.ocr_engine = OCREngine(self.logger)
        self.numbering_system = NumberingSystem(self.logger)
        self.content_analyzer = ContentAnalyzer(self.logger)
        self.confidence_system = ConfidenceSystem(self.logger)
        self.output_manager = OutputManager(self.logger)
        self.blank_page_detector = BlankPageDetector(self.logger)
        self.performance_optimizer = PerformanceOptimizer(self.logger)
        self.ai_learning = AILearningSystem(self.logger)
        self.cancel_processing = False
    
    def process_pages(self, input_path: str, output_path: str) -> bool:
        """Main processing pipeline"""
        try:
            # Get folder name for PDF naming
            input_path_obj = Path(input_path)
            if input_path_obj.is_dir():
                folder_name = input_path_obj.name
            else:
                folder_name = input_path_obj.stem
            
            with ProcessLogger(self.logger, "Page Reordering Process"):
                
                # Step 1: Load input files
                self.logger.step("Loading input files")
                pages = self.input_handler.load_files(input_path)
                if not pages:
                    self.logger.failure("No valid pages found in input")
                    return False
                
                self.logger.info(f"Loaded {len(pages)} pages")
                
                # Get optimal performance settings based on system resources
                perf_settings = self.performance_optimizer.get_optimal_settings()
                
                # Estimate processing time
                features_enabled = {
                    'preprocessing': config.get('default_settings.enable_preprocessing', False),
                    'auto_crop': config.get('preprocessing.auto_crop', False),
                    'clean_circles': config.get('preprocessing.clean_dark_circles', False)
                }
                estimated_time = self.performance_optimizer.get_estimated_time(
                    len(pages), perf_settings['workers'], features_enabled
                )
                self.logger.info(f"⏱️ Estimated processing time: {estimated_time:.1f} minutes")
                
                # Step 2: Remove blank pages (if enabled)
                blank_mode = config.get('processing.blank_page_mode', 'start_end')
                if blank_mode != 'none':
                    self.logger.step(f"Removing blank pages (mode: {blank_mode})")
                    pages, num_removed = self.blank_page_detector.remove_blank_pages(pages, blank_mode)
                    if num_removed > 0:
                        self.logger.info(f"Removed {num_removed} blank pages")
                        self.logger.info(f"Remaining pages: {len(pages)}")
                
                # Step 3: Preprocessing (optional)
                if config.get('default_settings.enable_preprocessing', True):
                    # Check for cancellation
                    if self.cancel_processing:
                        self.logger.info("Processing cancelled by user")
                        return False
                        
                    self.logger.step("Preprocessing images")
                    pages = self.preprocessor.process_batch(pages)
                
                # Step 4: OCR and number extraction
                # Check for cancellation
                if self.cancel_processing:
                    self.logger.info("Processing cancelled by user")
                    return False
                    
                self.logger.step("Extracting text and numbers via OCR")
                ocr_results = self.ocr_engine.process_batch(pages)
                
                # Step 5: Detect numbering system
                # Check for cancellation
                if self.cancel_processing:
                    self.logger.info("Processing cancelled by user")
                    return False
                    
                self.logger.step("Analyzing numbering systems")
                numbering_info = self.numbering_system.analyze_numbering(ocr_results)
                
                # Step 6: Initial ordering based on detected numbers
                # Check for cancellation
                if self.cancel_processing:
                    self.logger.info("Processing cancelled by user")
                    return False
                    
                self.logger.step("Ordering pages by detected numbers")
                ordered_pages = self.numbering_system.order_by_numbers(pages, ocr_results, numbering_info)
                
                # Step 7: Content-based ordering for ambiguous cases
                # Check for cancellation
                if self.cancel_processing:
                    self.logger.info("Processing cancelled by user")
                    return False
                    
                self.logger.step("Analyzing content relationships")
                final_order = self.content_analyzer.refine_ordering(ordered_pages, ocr_results)
                
                # Step 7: Confidence assessment
                self.logger.step("Assessing ordering confidence")
                confidence_report = self.confidence_system.evaluate_ordering(final_order, ocr_results)
                
                # Step 8: Handle low-confidence cases
                if config.get('content_analysis.min_confidence_for_auto_order', 90) > confidence_report['overall_confidence']:
                    self.logger.warning(f"Low confidence ordering ({confidence_report['overall_confidence']:.1f}%)")
                    self.logger.info("Consider using GUI mode for manual review")
                
                # Step 9: Generate output
                self.logger.step("Generating output files")
                success = self.output_manager.create_output(
                    final_order, 
                    output_path, 
                    confidence_report,
                    ocr_results,
                    folder_name  # Pass folder name for PDF naming
                )
                
                if success:
                    self.logger.success(f"Successfully processed {len(final_order)} pages")
                    self.logger.info(f"Output saved to: {output_path}")
                    return True  # Return success
                else:
                    self.logger.failure("Failed to generate output")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Processing failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def _optimize_settings_for_document_size(self, page_count: int):
        """Optimize processing settings based on document size for better performance"""
        import psutil
        
        # Get available memory
        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        
        if page_count > 400:  # Very large document
            self.logger.info(f"Large document detected ({page_count} pages), optimizing for performance...")
            
            # Conservative settings for large documents
            if available_memory_gb < 4:
                self.logger.warning("Low memory detected, using conservative settings")
                # Disable memory-intensive features if low memory
                if config.get('default_settings.enable_preprocessing', False):
                    self.logger.info("Disabling preprocessing due to memory constraints")
                    config.set('default_settings.enable_preprocessing', False)
            
        elif page_count > 200:  # Medium document
            self.logger.info(f"Medium document detected ({page_count} pages), using balanced settings")
            
        else:  # Small document
            self.logger.info(f"Small document detected ({page_count} pages), using full quality settings")
        
        # Log memory status
        memory_percent = psutil.virtual_memory().percent
        self.logger.info(f"Memory usage: {memory_percent:.1f}% ({available_memory_gb:.1f}GB available)")
    
    def run(self, args):
        """Run the page reordering process with given arguments"""
        try:
            # Setup components
            self.setup_components(args)
            
            # Validate input path
            input_path = Path(args.input)
            if not input_path.exists():
                self.logger.failure(f"Input path does not exist: {input_path}")
                return False
            
            # Setup output path
            output_path = Path(args.output) if args.output else input_path.parent / "reordered"
            output_path.mkdir(parents=True, exist_ok=True)
            
            self.logger.info("🚀 AI Page Reordering Automation System")
            self.logger.info(f"Input: {input_path}")
            self.logger.info(f"Output: {output_path}")
            self.logger.info(f"Configuration: {config.config_path}")
            
            # Process pages
            success = self.process_pages(str(input_path), str(output_path))
            
            if success:
                self.logger.success("✨ Page reordering completed successfully!")
                return True
            else:
                self.logger.failure("💥 Page reordering failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Processing failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="AI Page Reordering Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --input "scanned_pages/" --output "ordered_pages/"
  python main.py --input "document.pdf" --denoise off --confidence 95
  python main.py --input "pages/" --ocr on --verbose --log
        """
    )
    
    # Required arguments
    parser.add_argument('--input', '-i', required=True,
                      help='Input path (directory with images or PDF file)')
    
    # Optional arguments
    parser.add_argument('--output', '-o',
                      help='Output directory (default: input_dir/reordered)')
    
    parser.add_argument('--denoise', choices=['on', 'off'],
                      help='Enable/disable image denoising')
    
    parser.add_argument('--deskew', choices=['on', 'off'],
                      help='Enable/disable image deskewing')
    
    parser.add_argument('--ocr', choices=['on', 'off'],
                      help='Force enable/disable OCR processing')
    
    parser.add_argument('--confidence', type=int, metavar='0-100',
                      help='Confidence threshold for auto-ordering (default: 85)')
    
    parser.add_argument('--output-format', choices=['pdf', 'images', 'both'],
                      help='Output format (default: pdf)')
    
    parser.add_argument('--preset', choices=['quick', 'deep', 'manual'],
                      help='Processing preset (quick/deep/manual)')
    
    parser.add_argument('--memory', choices=['on', 'off'], default='on',
                      help='Enable/disable learning memory (default: on)')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose logging')
    
    parser.add_argument('--log', action='store_true',
                      help='Save detailed log to file')
    
    parser.add_argument('--config', 
                      help='Path to custom configuration file')
    
    return parser

def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Load custom config if specified
    if args.config and Path(args.config).exists():
        config.config_path = Path(args.config)
        config.config = config._load_config()
    
    # Create and run CLI
    cli = PageReorderCLI()
    success = cli.run(args)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
