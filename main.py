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


# ML Training imports (optional)
try:
    from core.model_manager import get_model_manager
    from ml_training.interactive_labeler import InteractiveLabeler
    from ml_training.quick_trainer import QuickTrainer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

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
        self.model_manager = None
    
    def setup_components(self, args, output_dir=None):
        """Initialize all system components"""
        # Update config from command line arguments
        config.update_from_args(args)
        
        # Setup logger (store log in output directory if available)
        log_file = None
        if output_dir:
            log_file = Path(output_dir) / "process.log"
        self.logger = create_logger(log_file=log_file, verbose=args.verbose)
        
        # ═══════════════════════════════════════════════════════════
        # STARTUP DIAGNOSTICS - Check everything before processing
        # ═══════════════════════════════════════════════════════════
        self._run_startup_diagnostics()
        
        # Initialize AI learning system FIRST (for adaptive behavior)
        self.ai_learning = AILearningSystem(self.logger)
        
        self.performance_optimizer = PerformanceOptimizer(self.logger)
        self.input_handler = InputHandler(self.logger)  # FIXED: Missing input handler
        self.preprocessor = Preprocessor(self.logger)   # FIXED: Missing preprocessor 
        self.ocr_engine = OCREngine(self.logger, self.ai_learning, output_dir)  # IMPROVED: Pass output dir for cache
        self.numbering_system = NumberingSystem(self.logger)
        self.content_analyzer = ContentAnalyzer(self.logger)
        self.confidence_system = ConfidenceSystem(self.logger)
        self.output_manager = OutputManager(self.logger)
        self.blank_page_detector = BlankPageDetector(self.logger)
        self.cancel_processing = False
        
        # ═══════════════════════════════════════════════════════════
        # ML MODEL CHECK - Prompt user about teaching if no model
        # ═══════════════════════════════════════════════════════════
        if ML_AVAILABLE and not args.skip_ml_prompt:
            try:
                self.model_manager = get_model_manager()
                
                if not self.model_manager.model_exists():
                    self._prompt_ml_teaching()
                else:
                    self.model_manager.load_model()
                    if self.logger:
                        self.logger.info("✅ ML model loaded - fast mode enabled!")
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"ML model check failed: {e}")
                pass  # ML not critical
    
    def process_pages(self, input_path: str, output_path: str) -> bool:
        """Main processing pipeline"""
        try:
            # Get folder name for PDF naming
            input_path_obj = Path(input_path)
            if input_path_obj.is_dir():
                folder_name = input_path_obj.name
            else:
                folder_name = input_path_obj.stem
            
            import time
            start_time = time.time()
            
            with ProcessLogger(self.logger, "Page Reordering Process"):
                
                # ═══════════════════════════════════════════════════════════
                # STAGE 1: LOAD INPUT FILES
                # ═══════════════════════════════════════════════════════════
                self.logger.step("STAGE 1: Loading input files")
                pages = self.input_handler.load_files(input_path)
                if not pages:
                    self.logger.failure("No valid pages found in input")
                    return False
                
                self.logger.info(f"✅ Stage 1 Complete: Loaded {len(pages)} pages")
                
                # ═══════════════════════════════════════════════════════════
                # STAGE 2: AI OPTIMIZATION
                # ═══════════════════════════════════════════════════════════
                self.logger.step("STAGE 2: AI Optimization")
                import psutil
                available_ram_gb = psutil.virtual_memory().available / (1024**3)
                
                # Get AI recommendations based on document size and system resources
                ai_recommendations = self.ai_learning.get_recommended_settings(
                    len(pages), available_ram_gb)
                
                # Apply AI recommendations to config
                self.logger.info("🤖 Applying AI-optimized settings...")
                for setting, value in ai_recommendations.items():
                    if setting != 'reasoning':
                        if setting == 'preprocessing':
                            config.set('default_settings.enable_preprocessing', value)
                        elif setting == 'auto_rotate':
                            config.set('preprocessing.auto_rotate', value)
                        elif setting == 'auto_crop':
                            config.set('preprocessing.auto_crop', value)
                        elif setting == 'clean_circles':
                            config.set('preprocessing.clean_dark_circles', value)
                        elif setting == 'blank_removal':
                            config.set('processing.blank_page_mode', value)
                        elif setting == 'advanced_analysis':
                            config.set('ocr.use_advanced_analysis', value)
                
                # Show AI reasoning
                for reason in ai_recommendations.get('reasoning', []):
                    self.logger.info(f"   • {reason}")
                
                # Get optimization suggestions
                suggestions = self.ai_learning.suggest_optimization(len(pages), available_ram_gb)
                for suggestion in suggestions:
                    self.logger.info(suggestion)
                
                # Get optimal performance settings based on AI + system resources
                perf_settings = self.performance_optimizer.get_optimal_settings()
                workers = perf_settings['workers']
                
                self.logger.info("=" * 70)
                self.logger.info(f"🎯 SYSTEM OPTIMIZATION:")
                self.logger.info(f"  CPU Cores: {perf_settings['cpu_cores']}")
                self.logger.info(f"  Available RAM: {perf_settings['available_ram_gb']:.1f}GB / {perf_settings['total_ram_gb']:.1f}GB")
                self.logger.info(f"  Performance Mode: {perf_settings['mode']}")
                self.logger.info(f"  Worker Threads: {workers}")
                self.logger.info(f"  Batch Size: {perf_settings['batch_size']}")
                self.logger.info("=" * 70)
                
                # Estimate processing time with AI predictions
                features_enabled = {
                    'preprocessing': config.get('default_settings.enable_preprocessing', False),
                    'auto_crop': config.get('preprocessing.auto_crop', False),
                    'clean_circles': config.get('preprocessing.clean_dark_circles', False)
                }
                estimated_time = self.ai_learning.predict_processing_time(len(pages), features_enabled)
                # Adjust estimate based on workers
                estimated_time_parallel = estimated_time / max(1, workers * 0.7)  # 70% efficiency factor
                self.logger.info(f"⏱️ AI estimated time (sequential): {estimated_time:.1f} minutes")
                self.logger.info(f"⏱️ Estimated time ({workers} workers): {estimated_time_parallel:.1f} minutes")
                self.logger.info(f"✅ Stage 2 Complete: AI optimization applied")
                
                # ═══════════════════════════════════════════════════════════
                # STAGE 3: BLANK PAGE REMOVAL
                # ═══════════════════════════════════════════════════════════
                blank_mode = config.get('processing.blank_page_mode', 'start_end')
                if blank_mode != 'none':
                    self.logger.step(f"STAGE 3: Removing blank pages (mode: {blank_mode})")
                    pages, num_removed = self.blank_page_detector.remove_blank_pages(pages, blank_mode)
                    if num_removed > 0:
                        self.logger.info(f"Removed {num_removed} blank pages")
                        self.logger.info(f"Remaining pages: {len(pages)}")
                
                # STAGE 3B: BLANK PAGE ORIENTATION FIX (Portrait)
                # Rotate blank landscape pages to portrait (default orientation)
                rotate_blank_portrait = config.get('processing.rotate_blank_to_portrait', True)
                if rotate_blank_portrait:
                    self.logger.info(f"🔄 Checking blank page orientation...")
                    pages, num_rotated = self.blank_page_detector.rotate_blank_landscape_to_portrait(pages)
                    if num_rotated > 0:
                        self.logger.info(f"📄 Rotated {num_rotated} blank landscape pages to portrait")
                
                self.logger.info(f"✅ Stage 3 Complete: Blank page processing done")
                
                # ═══════════════════════════════════════════════════════════
                # STAGE 4: PREPROCESSING
                # ═══════════════════════════════════════════════════════════
                if config.get('default_settings.enable_preprocessing', True):
                    # Check for cancellation
                    if self.cancel_processing:
                        self.logger.info("Processing cancelled by user")
                        return False
                        
                    self.logger.step("STAGE 4: Preprocessing images")
                    pages = self.preprocessor.process_batch(pages, workers=workers)
                
                # Generate crop validation report if auto-crop was used
                if config.get('preprocessing.auto_crop', False):
                    crop_report = self.preprocessor.generate_crop_reports(Path(output_path))
                    if crop_report:
                        self.logger.info(f"📋 Crop review report: {crop_report}")
                    
                    # Handle interactive manual cropping if enabled
                    if config.get('preprocessing.interactive_crop', False):
                        pages = self.preprocessor.handle_manual_cropping(pages)
                        if pages is None:
                            # User cancelled during manual cropping
                            self.logger.info("Processing cancelled during manual cropping")
                            return False
                
                self.logger.info(f"✅ Stage 4 Complete: Preprocessing done")
                
                # ═══════════════════════════════════════════════════════════
                # STAGE 5: OCR & PAGE DETECTION
                # ═══════════════════════════════════════════════════════════
                if self.cancel_processing:
                    self.logger.info("Processing cancelled by user")
                    return False
                    
                self.logger.step("STAGE 5: Extracting text and numbers via OCR")
                ocr_results = self.ocr_engine.process_batch(pages, workers=workers)
                self.logger.info(f"✅ Stage 5 Complete: OCR processing done")
                
                # ═══════════════════════════════════════════════════════════
                # STAGE 6: NUMBERING ANALYSIS
                # ═══════════════════════════════════════════════════════════
                if self.cancel_processing:
                    self.logger.info("Processing cancelled by user")
                    return False
                    
                self.logger.step("STAGE 6: Analyzing numbering systems")
                numbering_info = self.numbering_system.analyze_numbering(ocr_results)
                self.logger.info(f"✅ Stage 6 Complete: Numbering analysis done")
                
                # ═══════════════════════════════════════════════════════════
                # STAGE 7: PAGE ORDERING
                # ═══════════════════════════════════════════════════════════
                if self.cancel_processing:
                    self.logger.info("Processing cancelled by user")
                    return False
                    
                self.logger.step("STAGE 7: Ordering pages by detected numbers")
                ordered_pages = self.numbering_system.order_by_numbers(pages, ocr_results, numbering_info)
                self.logger.info(f"✅ Stage 7 Complete: Page ordering done")
                
                # ═══════════════════════════════════════════════════════════
                # STAGE 8: CONTENT ANALYSIS
                # ═══════════════════════════════════════════════════════════
                if self.cancel_processing:
                    self.logger.info("Processing cancelled by user")
                    return False
                    
                self.logger.step("STAGE 8: Analyzing content relationships")
                final_order = self.content_analyzer.refine_ordering(ordered_pages, ocr_results)
                self.logger.info(f"✅ Stage 8 Complete: Content analysis done")
                
                # ═══════════════════════════════════════════════════════════
                # STAGE 9: CONFIDENCE ASSESSMENT
                # ═══════════════════════════════════════════════════════════
                self.logger.step("STAGE 9: Assessing ordering confidence")
                confidence_report = self.confidence_system.evaluate_ordering(final_order, ocr_results)
                self.logger.info(f"✅ Stage 9 Complete: Confidence assessment done")
                
                # Handle low-confidence cases
                if config.get('content_analysis.min_confidence_for_auto_order', 90) > confidence_report['overall_confidence']:
                    self.logger.warning(f"Low confidence ordering ({confidence_report['overall_confidence']:.1f}%)")
                    self.logger.info("Consider using GUI mode for manual review")
                
                # ═══════════════════════════════════════════════════════════
                # STAGE 10 & 11: OUTPUT GENERATION (DPI + Format)
                # ═══════════════════════════════════════════════════════════
                self.logger.step("STAGE 10-11: Generating output files (DPI conversion + Format)")
                success = self.output_manager.create_output(
                    final_order, 
                    output_path, 
                    confidence_report,
                    ocr_results,
                    folder_name  # Pass folder name for PDF naming
                )
                
                if success:
                    self.logger.info(f"✅ Stage 10-11 Complete: Output generation done")
                    self.logger.success(f"Successfully processed {len(final_order)} pages")
                    self.logger.info(f"Output saved to: {output_path}")
                    
                    # Show AI Learning Statistics (SPEED IMPROVEMENTS!)
                    if hasattr(self.ocr_engine, 'advanced_detector'):
                        self.logger.info("")
                        self.ocr_engine.advanced_detector.log_learning_stats()
                    
                    # Record processing session for AI learning
                    import time
                    processing_time = time.time() - start_time if 'start_time' in locals() else 0
                    
                    document_info = {
                        'page_count': len(pages),
                        'file_type': 'images',
                        'size_mb': sum(p.file_path.stat().st_size for p in pages if p.file_path.exists()) / (1024*1024)
                    }
                    
                    result_info = {
                        'success': True,
                        'processing_time': processing_time,
                        'pages_processed': len(final_order),
                        'confidence': confidence_report.get('overall_confidence', 0)
                    }
                    
                    # Learn from this processing session
                    self.ai_learning.record_processing(document_info, features_enabled, result_info)
                    
                    return True  # Return success
                else:
                    self.logger.failure("Failed to generate output")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Processing failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    
    def run(self, args):
        """Run the page reordering process with given arguments"""
        try:            
            # Validate input path
            input_path = Path(args.input)
            if not input_path.exists():
                self.logger.failure(f"Input path does not exist: {input_path}")
                return False
            
            # Setup output path
            if args.output:
                output_path = Path(args.output)
                output_path.mkdir(parents=True, exist_ok=True)
            else:
                # Create output folder INSIDE input folder
                if input_path.is_dir():
                    # Extract ISBN from first image file in folder
                    image_files = list(input_path.glob('*.jpg')) + list(input_path.glob('*.png')) + list(input_path.glob('*.tif')) + list(input_path.glob('*.tiff'))
                    if image_files:
                        first_file = image_files[0].name
                        # Extract ISBN (numbers before first underscore)
                        parts = first_file.split('_')
                        if parts and parts[0].isdigit() and len(parts[0]) >= 10:
                            isbn = parts[0]  # Use ISBN as folder name
                        else:
                            isbn = "Organized_Pages"  # Default name
                    else:
                        isbn = "Organized_Pages"
                    
                    # Create output INSIDE the input folder
                    output_path = input_path / isbn
                    output_path.mkdir(parents=True, exist_ok=True)
                else:
                    # For single file, use parent folder
                    output_path = input_path.parent / "reordered"
                    output_path.mkdir(parents=True, exist_ok=True)
            
            # Setup components with output directory for cache
            self.setup_components(args, str(output_path))
            
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
    
    def _prompt_ml_teaching(self):
        """Prompt user about ML teaching in CLI mode"""
        print()
        print("=" * 70)
        print("🤖 ML MODEL NOT FOUND")
        print("=" * 70)
        print()
        print("Would you like to teach the AI to recognize page numbers?")
        print()
        print("Benefits:")
        print("  • 10x faster processing (0.5s vs 5-8s per page)")
        print("  • 97-99% accuracy")
        print("  • One-time setup (15-20 minutes)")
        print()
        print("Options:")
        print("  [1] Teach the AI now (recommended)")
        print("  [2] Skip and use PaddleOCR (slower)")
        print("  [3] Cancel processing")
        print()
        
        while True:
            try:
                choice = input("Enter choice (1/2/3): ").strip()
                
                if choice == '1':
                    print("\n✅ Starting teaching mode...")
                    self._run_cli_teaching_mode()
                    break
                elif choice == '2':
                    print("\n⏭ Skipping ML teaching - using PaddleOCR mode")
                    if self.logger:
                        self.logger.info("User skipped ML teaching - using PaddleOCR only")
                    break
                elif choice == '3':
                    print("\n❌ Processing cancelled")
                    sys.exit(0)
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")
            except KeyboardInterrupt:
                print("\n\n❌ Cancelled by user")
                sys.exit(0)
    
    def _run_cli_teaching_mode(self):
        """Run teaching mode in CLI"""
        print()
        print("📁 Please select a folder with sample page images (20-50 pages):")
        
        # Simple folder selection
        sample_folder = input("Enter path to sample folder: ").strip()
        
        # Remove quotes if user wrapped path in quotes
        sample_folder = sample_folder.strip('"').strip("'")
        
        if not Path(sample_folder).exists():
            print(f"❌ Folder not found: {sample_folder}")
            print("Continuing with PaddleOCR mode...")
            return
        
        print()
        print("🎓 Launching interactive labeler...")
        print("   - Click & drag to select page number regions")
        print("   - Type the number you see")
        print("   - Press Enter to save")
        print("   - Repeat for 20-50 pages")
        print()
        
        try:
            labeler = InteractiveLabeler(sample_folder)
            labeler.run()  # Opens GUI window for labeling
            
            if labeler.stats['total_labeled'] < 10:
                print(f"\n⚠️  Only {labeler.stats['total_labeled']} images labeled")
                print("Recommended: 20+ for good accuracy")
                
                cont = input("Continue with training anyway? (y/n): ").strip().lower()
                if cont != 'y':
                    print("Skipping training...")
                    return
            
            # Train model
            print("\n🚀 Training model (this may take 5-10 minutes)...")
            print("Please be patient...\n")
            
            trainer = QuickTrainer()
            trainer.run_full_training(epochs=30)
            
            print("\n✅ Training complete!")
            
            # Get accuracy if available
            if hasattr(trainer, 'history') and trainer.history:
                val_acc = trainer.history.history.get('val_accuracy', [0])[-1]
                print(f"   Validation Accuracy: {val_acc*100:.1f}%")
            
            print("   Model saved. Future processing will be 10x faster!")
            
            # Reload model
            if self.model_manager:
                self.model_manager.load_model(force_reload=True)
                if self.logger:
                    self.logger.info("✅ ML model trained and loaded successfully!")
            
        except KeyboardInterrupt:
            print("\n\n❌ Teaching cancelled by user")
            print("Continuing with PaddleOCR mode...")
        except Exception as e:
            print(f"\n❌ Teaching failed: {e}")
            print("Continuing with PaddleOCR mode...")
            if self.logger:
                self.logger.error(f"ML teaching failed: {e}")
    
    def _run_startup_diagnostics(self):
        """Run comprehensive startup diagnostics - checks ALL dependencies"""
        import os
        
        self.logger.info("=" * 70)
        self.logger.info("🔍 COMPREHENSIVE STARTUP DIAGNOSTICS")
        self.logger.info("=" * 70)
        
        errors = []
        warnings = []
        
        # Check 1: Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.logger.info(f"✓ Python Version: {python_version}")
        
        # Check 2: Running mode (Script vs EXE)
        is_frozen = getattr(sys, 'frozen', False)
        if is_frozen:
            self.logger.info(f"✓ Running Mode: EXE (Standalone)")
            base_path = sys._MEIPASS
            self.logger.info(f"  Base Path: {base_path}")
        else:
            self.logger.info(f"✓ Running Mode: Script")
        
        # Check 3: PaddleX models
        if is_frozen:
            paddlex_path = os.path.join(sys._MEIPASS, '.paddlex')
            if os.path.exists(paddlex_path):
                model_count = len([f for f in Path(paddlex_path).rglob('*') if f.is_file()])
                self.logger.info(f"✓ PaddleX Models: Found ({model_count} files)")
                self.logger.info(f"  Location: {paddlex_path}")
                
                # Check for specific models
                models_dir = Path(paddlex_path) / 'official_models'
                if models_dir.exists():
                    models = [d.name for d in models_dir.iterdir() if d.is_dir()]
                    self.logger.info(f"  Models: {', '.join(models[:3])}...")
                else:
                    warnings.append("official_models directory not found")
            else:
                errors.append("PaddleX Models NOT FOUND - PaddleOCR will fail!")
                self.logger.error(f"❌ PaddleX Models: NOT FOUND")
                self.logger.error(f"  Expected: {paddlex_path}")
        else:
            # Script mode - check user directory
            paddlex_path = Path.home() / '.paddlex'
            if paddlex_path.exists():
                model_count = len([f for f in paddlex_path.rglob('*') if f.is_file()])
                self.logger.info(f"✓ PaddleX Models: Found ({model_count} files)")
            else:
                warnings.append("PaddleX Models not downloaded yet")
        
        self.logger.info("")
        self.logger.info("📦 CHECKING CRITICAL DEPENDENCIES:")
        self.logger.info("-" * 70)
        
        # Check 4: Core image processing libraries
        critical_deps = {
            'paddleocr': 'PaddleOCR',
            'paddlex': 'PaddleX',
            'paddle': 'PaddlePaddle',  # Imports as 'paddle', not 'paddlepaddle'
            'cv2': 'OpenCV',
            'PIL': 'Pillow',
            'numpy': 'NumPy',
        }
        
        for module, name in critical_deps.items():
            try:
                __import__(module)
                self.logger.info(f"✓ {name}")
            except ImportError as e:
                errors.append(f"{name} NOT INSTALLED")
                self.logger.error(f"❌ {name}: NOT INSTALLED - {e}")
        
        # Check 5: PaddleX[ocr] extra dependencies
        self.logger.info("")
        self.logger.info("🔧 CHECKING PADDLEX[OCR] DEPENDENCIES:")
        self.logger.info("-" * 70)
        
        ocr_deps = {
            'einops': 'einops',
            'ftfy': 'ftfy',
            'imagesize': 'imagesize',
            'jinja2': 'Jinja2',
            'lxml': 'lxml',
            'openpyxl': 'openpyxl',
            'premailer': 'premailer',
            'pypdfium2': 'pypdfium2',
            'regex': 'regex',
            'sklearn': 'scikit-learn',
            'tiktoken': 'tiktoken',
            'tokenizers': 'tokenizers',
        }
        
        missing_ocr_deps = []
        for module, name in ocr_deps.items():
            try:
                __import__(module)
                self.logger.info(f"✓ {name}")
            except ImportError:
                missing_ocr_deps.append(name)
                self.logger.error(f"❌ {name}: MISSING")
        
        if missing_ocr_deps:
            errors.append(f"Missing {len(missing_ocr_deps)} paddlex[ocr] dependencies")
        
        # Check 6: PDF processing libraries
        self.logger.info("")
        self.logger.info("📄 CHECKING PDF LIBRARIES:")
        self.logger.info("-" * 70)
        
        pdf_deps = {
            'img2pdf': ('img2pdf', False),
            'PyPDF2': ('PyPDF2', False),
            'reportlab': ('reportlab', False),
        }
        
        for module, (name, required) in pdf_deps.items():
            try:
                __import__(module)
                self.logger.info(f"✓ {name}")
            except ImportError:
                if required:
                    errors.append(f"{name} NOT INSTALLED")
                    self.logger.error(f"❌ {name}: NOT INSTALLED")
                else:
                    warnings.append(f"{name} not installed (optional)")
                    self.logger.warning(f"⚠ {name}: Not installed (slower PDF generation)")
        
        # Check 7: Additional processing libraries
        self.logger.info("")
        self.logger.info("🛠️ CHECKING PROCESSING LIBRARIES:")
        self.logger.info("-" * 70)
        
        processing_deps = {
            'scipy': 'SciPy',
            'yaml': 'PyYAML',
            'psutil': 'psutil',
        }
        
        for module, name in processing_deps.items():
            try:
                __import__(module)
                self.logger.info(f"✓ {name}")
            except ImportError:
                warnings.append(f"{name} not installed")
                self.logger.warning(f"⚠ {name}: Not installed")
        
        # Check 8: Test PaddleOCR initialization
        self.logger.info("")
        self.logger.info("🧪 TESTING PADDLEOCR INITIALIZATION:")
        self.logger.info("-" * 70)
        
        try:
            from paddleocr import PaddleOCR
            # Try to create instance without actually using it
            self.logger.info(f"✓ PaddleOCR class importable")
            
            # Check if paddlex dependency checker is working
            try:
                from paddlex.utils import deps
                self.logger.info(f"✓ paddlex.utils.deps accessible")
                
                # Check if it's been patched (in frozen mode)
                if is_frozen:
                    if hasattr(deps, 'require_extra'):
                        self.logger.info(f"✓ paddlex.utils.deps.require_extra available")
                    else:
                        warnings.append("paddlex.utils.deps.require_extra not found")
            except ImportError as e:
                errors.append(f"paddlex.utils.deps import failed: {e}")
                self.logger.error(f"❌ paddlex.utils.deps: {e}")
                
        except Exception as e:
            errors.append(f"PaddleOCR initialization test failed: {e}")
            self.logger.error(f"❌ PaddleOCR initialization test failed: {e}")
        
        # Check 9: System resources
        self.logger.info("")
        self.logger.info("💻 SYSTEM RESOURCES:")
        self.logger.info("-" * 70)
        
        try:
            import psutil
            ram_gb = psutil.virtual_memory().total / (1024**3)
            available_ram_gb = psutil.virtual_memory().available / (1024**3)
            cpu_cores = psutil.cpu_count()
            self.logger.info(f"✓ System RAM: {ram_gb:.1f} GB ({available_ram_gb:.1f} GB available)")
            self.logger.info(f"✓ CPU Cores: {cpu_cores}")
            
            if available_ram_gb < 2:
                warnings.append(f"Low available RAM ({available_ram_gb:.1f} GB)")
        except Exception as e:
            warnings.append(f"Could not detect system resources: {e}")
        
        # Final summary
        self.logger.info("")
        self.logger.info("=" * 70)
        
        if errors:
            self.logger.error(f"❌ DIAGNOSTICS FAILED - {len(errors)} CRITICAL ERRORS:")
            for error in errors:
                self.logger.error(f"   • {error}")
            self.logger.error("")
            self.logger.error("⚠️  APPLICATION MAY NOT FUNCTION CORRECTLY!")
            self.logger.error("   Please fix the errors above before processing.")
        elif warnings:
            self.logger.warning(f"⚠️  DIAGNOSTICS PASSED WITH {len(warnings)} WARNINGS:")
            for warning in warnings:
                self.logger.warning(f"   • {warning}")
            self.logger.info("")
            self.logger.info("✅ System ready - but some features may be limited")
        else:
            self.logger.info("✅ ALL DIAGNOSTICS PASSED - SYSTEM FULLY READY!")
        
        self.logger.info("=" * 70)
        
        # Pause if there are errors (give user time to read)
        if errors and is_frozen:
            import time
            self.logger.error("\n⏸️  Pausing for 10 seconds - please review errors above...")
            time.sleep(10)

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
    
    parser.add_argument('--skip-ml-prompt', action='store_true',
                      help='Skip ML teaching prompt (use PaddleOCR only)')
    
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
