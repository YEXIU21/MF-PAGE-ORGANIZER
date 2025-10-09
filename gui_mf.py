#!/usr/bin/env python3
"""
MF PAGE ORGANIZER - Standalone GUI
User-friendly interface for non-technical users
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add bundled modules to path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    bundle_dir = sys._MEIPASS
    sys.path.insert(0, bundle_dir)

try:
    from main import PageReorderCLI
    from utils.config import config
    from utils.logger import create_logger
    from splash_screen import show_splash_with_loading
except ImportError as e:
    # If splash_screen not available, continue without it
    show_splash_with_loading = None
    try:
        from main import PageReorderCLI
        from utils.config import config
        from utils.logger import create_logger
    except ImportError as e:
        messagebox.showerror("Error", f"System components not found: {e}")
        sys.exit(1)

class MFPageOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MF Page Organizer - Smart Document Organizer")
        
        # Set AppUserModelID for Windows 11 taskbar icon
        try:
            import ctypes
            myappid = 'YEXIU.MFPageOrganizer.GUI.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass  # Not on Windows or failed
        
        # Theme management (will be applied after UI is built)
        self.current_theme = "dark"  # Force dark mode for now
        self.detect_system_theme()
        
        # Set window to 80% of screen size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.resizable(True, True)
        
        # Set minimum size to prevent shrinking too much
        min_width = 800
        min_height = 600
        self.root.minsize(min_width, min_height)
        
        # Set window icon if available
        try:
            if getattr(sys, 'frozen', False):
                # Running as EXE
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
            else:
                # Running as script - convert PNG to ICO
                png_path = Path(__file__).parent / 'PageAutomationic.png'
                if png_path.exists():
                    from PIL import Image
                    img = Image.open(png_path)
                    ico_path = Path(__file__).parent / 'temp_icon.ico'
                    img.save(ico_path, format='ICO', sizes=[(32,32)])
                    self.root.iconbitmap(str(ico_path))
        except Exception as e:
            pass  # Icon not critical
        
        self.cli = PageReorderCLI()
        self.logger = create_logger()
        # Initialize variables
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.processing = False
        self.cancel_processing = False
        self.progress_value = 0
        
        self.setup_ui()
        self.center_window()
        
        # Force window update before applying theme
        self.root.update_idletasks()
        
        # Apply theme after UI is fully rendered
        self.apply_theme()
        
        # Force another update to ensure theme is applied
        self.root.update()
        
        # Close PyInstaller splash screen after GUI is fully loaded
        # This ensures smooth transition from splash to main window
        try:
            import pyi_splash
            pyi_splash.close()
        except:
            pass  # Not running as EXE with splash or already closed
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Create user-friendly interface"""
        # Main container - no scrollbar, proper grid layout
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for responsive layout
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)  # Progress section expands
        
        # Title
        title_label = ttk.Label(main_frame, text="MF Page Organizer", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, 
                                  text="Automatically organize your scanned pages in the correct order",
                                  font=("Arial", 10))
        subtitle_label.pack(pady=(0, 20))
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="📁 Select Your Pages", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Choose folder with your scanned pages or PDF file:").pack(anchor=tk.W, pady=(0, 10))
        
        input_path_frame = ttk.Frame(input_frame)
        input_path_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.input_entry = ttk.Entry(input_path_frame, textvariable=self.input_folder, 
                                    font=("Arial", 10), width=50)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Note: Drag & drop requires tkinterdnd2 (optional)
        # For now, users can paste paths or use Browse button
        
        ttk.Button(input_path_frame, text="Browse Files", 
                  command=self.browse_input).pack(side=tk.RIGHT)
        
        # Supported formats info
        ttk.Label(input_frame, text="Supported: PDF, PNG, JPG, TIFF files", 
                 font=("Arial", 9), foreground="gray").pack(anchor=tk.W)
        
        # Settings section with two-column layout
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Processing Options", padding="15")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create two columns
        left_column = ttk.Frame(settings_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_column = ttk.Frame(settings_frame)
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # LEFT COLUMN
        # Image quality enhancement
        quality_frame = ttk.Frame(left_column)
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(quality_frame, text="Image quality enhancement:").pack(side=tk.LEFT)
        self.enhance_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(quality_frame, text="Improve image quality", 
                       variable=self.enhance_var).pack(side=tk.LEFT, padx=(10, 0))
        
        # Auto-rotate feature
        rotate_frame = ttk.Frame(left_column)
        rotate_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(rotate_frame, text="Auto-rotate pages:").pack(side=tk.LEFT)
        self.auto_rotate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(rotate_frame, text="Automatically fix page orientation", 
                       variable=self.auto_rotate_var).pack(side=tk.LEFT, padx=(10, 0))
        
        # Auto crop feature
        crop_frame = ttk.Frame(left_column)
        crop_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(crop_frame, text="Auto crop pages:").pack(side=tk.LEFT)
        self.auto_crop_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(crop_frame, text="Remove borders and margins automatically", 
                       variable=self.auto_crop_var).pack(side=tk.LEFT, padx=(10, 0))
        
        # Performance mode
        perf_frame = ttk.Frame(left_column)
        perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(perf_frame, text="Performance mode:").pack(side=tk.LEFT)
        self.fast_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(perf_frame, text="Fast mode (large documents)", 
                       variable=self.fast_mode_var).pack(side=tk.LEFT, padx=(10, 0))
        
        # Accuracy level
        conf_frame = ttk.Frame(left_column)
        conf_frame.pack(fill=tk.X)
        
        ttk.Label(conf_frame, text="Accuracy level:").pack(side=tk.LEFT)
        self.accuracy_var = tk.StringVar(value="Standard")  
        accuracy_combo = ttk.Combobox(conf_frame, textvariable=self.accuracy_var, 
                                     values=["Fast", "Standard", "High Accuracy"], 
                                     state="readonly", width=15)
        accuracy_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # RIGHT COLUMN
        # Dark circle cleanup feature
        clean_frame = ttk.Frame(right_column)
        clean_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(clean_frame, text="Clean dirty pages:").pack(side=tk.LEFT)
        self.clean_circles_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(clean_frame, text="Remove dark circles and spots", 
                       variable=self.clean_circles_var).pack(side=tk.LEFT, padx=(10, 0))
        
        # Blank page removal
        blank_frame = ttk.Frame(right_column)
        blank_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(blank_frame, text="Remove blank pages:").pack(side=tk.LEFT)
        self.blank_page_var = tk.StringVar(value="None")
        blank_combo = ttk.Combobox(blank_frame, textvariable=self.blank_page_var,
                                   values=["None", "Start Only", "End Only", "Start & End", "All Blank Pages"],
                                   state="readonly", width=18)
        blank_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Blank page orientation fix
        blank_orient_frame = ttk.Frame(right_column)
        blank_orient_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(blank_orient_frame, text="Blank page orientation:").pack(side=tk.LEFT)
        self.blank_portrait_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(blank_orient_frame, text="Rotate landscape blanks to portrait", 
                       variable=self.blank_portrait_var).pack(side=tk.LEFT, padx=(10, 0))
        
        # PDF compression
        compress_frame = ttk.Frame(right_column)
        compress_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(compress_frame, text="PDF compression:").pack(side=tk.LEFT)
        self.compress_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(compress_frame, text="Compress PDF (smaller file size)", 
                       variable=self.compress_var).pack(side=tk.LEFT, padx=(10, 0))
        
        # Output format selection
        format_frame = ttk.Frame(right_column)
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(format_frame, text="Output image format:").pack(side=tk.LEFT)
        self.output_format_var = tk.StringVar(value="TIF")
        format_combo = ttk.Combobox(format_frame, textvariable=self.output_format_var,
                                    values=["TIF (300 DPI)", "JPG (300 DPI)"],
                                    state="readonly", width=15)
        format_combo.pack(side=tk.LEFT, padx=(10, 0))
        format_combo.current(0)  # Default to TIF
        
        # PDF output checkbox
        self.include_pdf_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(format_frame, text="Include PDF", 
                       variable=self.include_pdf_var).pack(side=tk.LEFT, padx=(10, 0))
        
        # Output section
        output_frame = ttk.LabelFrame(main_frame, text="💾 Save Results", padding="15")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(output_frame, text="Where to save organized pages:").pack(anchor=tk.W, pady=(0, 10))
        
        output_path_frame = ttk.Frame(output_frame)
        output_path_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.output_entry = ttk.Entry(output_path_frame, textvariable=self.output_folder, 
                                     font=("Arial", 10), width=50)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Button(output_path_frame, text="Choose Folder", 
                  command=self.browse_output).pack(side=tk.RIGHT)
        
        ttk.Label(output_frame, text="(Leave empty to save next to original files)", 
                 font=("Arial", 9), foreground="gray").pack(anchor=tk.W)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Default Settings button
        self.default_btn = ttk.Button(button_frame, text="⚙️ Use Default Settings", 
                                     command=self.apply_default_settings)
        self.default_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.process_btn = ttk.Button(button_frame, text="🚀 Organize My Pages", 
                                     command=self.start_processing)
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Cancel button (hidden initially)
        self.cancel_btn = ttk.Button(button_frame, text="❌ Cancel", 
                                    command=self.cancel_processing_action, state="disabled")
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="❓ Help", 
                  command=self.show_help).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="🎨 Theme", 
                  command=self.toggle_theme).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="ℹ️ About", 
                  command=self.show_about).pack(side=tk.RIGHT)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progress", padding="15")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.status_label = ttk.Label(progress_frame, text="Ready to organize your pages", 
                                     font=("Arial", 10))
        self.status_label.pack(anchor=tk.W, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Log display
        log_frame = ttk.Frame(progress_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, 
                               font=("Consolas", 9), state=tk.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def on_drop(self, event):
        """Handle drag & drop of files/folders"""
        try:
            # Get dropped file/folder path
            data = event.data
            # Remove curly braces if present
            if data.startswith('{') and data.endswith('}'):
                data = data[1:-1]
            
            self.input_folder.set(data)
            self.update_output_path(data)
            self.log_message(f"✅ Loaded: {Path(data).name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dropped file: {e}")
    
    def log_message(self, message):
        """Add message to log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def browse_input(self):
        """Browse for input files or folder"""
        # Ask user to choose between file or folder
        choice = messagebox.askyesnocancel("Select Input", 
                                          "Choose 'Yes' for a PDF file, 'No' for a folder of images")
        
        if choice is True:  # PDF file
            file_path = filedialog.askopenfilename(
                title="Select PDF file",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if file_path:
                self.input_folder.set(file_path)
                self.update_output_path(file_path)
                
        elif choice is False:  # Folder
            folder_path = filedialog.askdirectory(title="Select folder with image files")
            if folder_path:
                self.input_folder.set(folder_path)
                self.update_output_path(folder_path)
    
    def apply_default_settings(self):
        """Apply recommended default settings for optimal processing"""
        # DEFAULT SETTINGS FOR PAGE AUTOMATION
        self.enhance_var.set(False)          # Image quality: OFF (faster)
        self.auto_rotate_var.set(True)       # Auto-rotate: ON (essential for books)
        self.auto_crop_var.set(True)         # Auto-crop: ON (removes borders)
        self.clean_circles_var.set(True)     # Clean circles: ON (removes scan artifacts)
        self.fast_mode_var.set(False)        # Fast mode: OFF (better accuracy)
        self.accuracy_var.set("Standard")    # Accuracy: Standard (balanced)
        self.blank_page_var.set("Start & End")  # Blank pages: Remove start & end
        self.blank_portrait_var.set(True)    # Blank portrait: ON (rotate landscape blanks)
        self.compress_var.set(False)         # PDF compression: OFF (better quality)
        self.output_format_var.set("TIF (300 DPI)")  # Format: TIF with 300 DPI
        self.include_pdf_var.set(True)       # Include PDF: ON
        
        messagebox.showinfo("Default Settings Applied", 
                          "✅ Default settings have been applied:\n\n"
                          "• Auto-rotate: ON\n"
                          "• Auto-crop: ON\n"
                          "• Clean dark circles: ON\n"
                          "• Remove blank pages: Start & End\n"
                          "• Blank pages → Portrait: ON\n"
                          "• Output format: TIF (300 DPI)\n"
                          "• Include PDF: YES\n"
                          "• Accuracy: Standard\n\n"
                          "These settings work best for most books!")
    
    def browse_output(self):
        """Browse for output folder"""
        folder_path = filedialog.askdirectory(title="Choose where to save organized pages")
        if folder_path:
            self.output_folder.set(folder_path)
    
    def update_output_path(self, input_path):
        """Auto-suggest output path based on input - INSIDE the input folder"""
        if not self.output_folder.get():
            input_path_obj = Path(input_path)
            if input_path_obj.is_dir():
                # For folder: create output INSIDE the folder
                # Extract ISBN from first image file
                image_files = list(input_path_obj.glob('*.jpg')) + list(input_path_obj.glob('*.png')) + list(input_path_obj.glob('*.tif'))
                if image_files:
                    first_file = image_files[0].name
                    parts = first_file.split('_')
                    if parts and parts[0].isdigit() and len(parts[0]) >= 10:
                        isbn = parts[0]
                    else:
                        isbn = "Organized_Pages"
                else:
                    isbn = "Organized_Pages"
                suggested_output = input_path_obj / isbn
            else:
                # For file: create output in parent directory
                input_dir = input_path_obj.parent
                suggested_output = input_dir / "Organized_Pages"
            self.output_folder.set(str(suggested_output))
    
    def start_processing(self):
        """Start page processing in background thread"""
        if not self.input_folder.get():
            messagebox.showerror("Error", "Please select your pages first!")
            return
        
        if self.processing:
            messagebox.showwarning("Processing", "Already processing pages. Please wait.")
            return
        
        # Update UI for processing
        self.processing = True
        self.cancel_processing = False
        self.process_btn.config(text="⏳ Processing...", state="disabled")
        self.cancel_btn.config(state="normal")  # Enable cancel button
        self.progress_bar.start()
        self.status_label.config(text="🔄 Processing pages...")
        
        # Start processing in background thread
        thread = threading.Thread(target=self.process_pages, daemon=True)
        thread.start()
    
    def cancel_processing_action(self):
        """Cancel the current processing"""
        if self.processing:
            self.cancel_processing = True
            # Pass cancel flag to CLI components
            if hasattr(self.cli, 'cancel_processing'):
                self.cli.cancel_processing = True
            if hasattr(self.cli, 'preprocessor') and self.cli.preprocessor:
                self.cli.preprocessor.cancel_processing = True
            if hasattr(self.cli, 'ocr_engine') and self.cli.ocr_engine:
                self.cli.ocr_engine.cancel_processing = True
            
            self.status_label.config(text="🚫 Cancelling...")
            self.log_message("❌ Processing cancelled by user")
    
    def process_pages(self):
        """Process pages in background"""
        try:
            # Configure settings based on user choices
            if self.enhance_var.get():
                config.set('preprocessing.denoise', True)
                config.set('preprocessing.deskew', True)
                config.set('default_settings.enable_preprocessing', True)
            else:
                config.set('preprocessing.denoise', False)
                config.set('preprocessing.deskew', False)
                config.set('default_settings.enable_preprocessing', False)  # Disable preprocessing completely
            
            # Set auto-rotate
            config.set('preprocessing.auto_rotate', self.auto_rotate_var.get())
            
            # Set auto crop
            config.set('preprocessing.auto_crop', self.auto_crop_var.get())
            
            # Set dark circle cleanup
            config.set('preprocessing.clean_dark_circles', self.clean_circles_var.get())
            
            # Set fast mode (performance optimization)
            # Note: Fast mode now works WITH other features (no auto-disable)
            config.set('processing.fast_mode', self.fast_mode_var.get())
            config.set('preprocessing.image_optimization', self.fast_mode_var.get())
            
            # Set blank page removal mode
            blank_mode_map = {
                "None": "none",
                "Start Only": "start",
                "End Only": "end",
                "Start & End": "start_end",
                "All Blank Pages": "all"
            }
            blank_mode = blank_mode_map.get(self.blank_page_var.get(), "start_end")
            config.set('processing.blank_page_mode', blank_mode)
            
            # Set blank page portrait rotation
            config.set('processing.rotate_blank_to_portrait', self.blank_portrait_var.get())
            
            # Set PDF compression
            config.set('output.compress_pdf', self.compress_var.get())
            
            # Set output format (TIF or JPG) - both convert to 300 DPI
            output_format = self.output_format_var.get()
            if "TIF" in output_format:
                config.set('output.image_format', 'tif')
            else:  # JPG
                config.set('output.image_format', 'jpg')
            # Always convert to 300 DPI (both TIF and JPG)
            config.set('output.convert_to_300dpi', True)
            
            # Set PDF creation based on checkbox
            config.set('output.create_pdf', self.include_pdf_var.get())
            
            # Set confidence based on accuracy level
            accuracy_levels = {
                "Fast": 70,
                "Standard": 85,
                "High Accuracy": 95
            }
            confidence = accuracy_levels.get(self.accuracy_var.get(), 85)
            config.set('default_settings.ocr_confidence_threshold', confidence)
            
            # Get input and output paths
            input_path = self.input_folder.get()
            
            # Enhanced output path logic - always create INSIDE input folder
            input_path_obj = Path(input_path)
            
            # Extract ISBN/folder identifier from input folder name
            if input_path_obj.is_dir():
                input_folder_name = input_path_obj.name
            else:
                input_folder_name = input_path_obj.stem
            
            # Try to extract ISBN from folder name (look for 13-digit number)
            import re
            isbn_match = re.search(r'\d{13}', input_folder_name)
            if isbn_match:
                isbn_number = isbn_match.group()
            else:
                # If no ISBN found, use folder name or generate from first few chars
                isbn_number = input_folder_name
            
            # Set output path INSIDE the input folder
            if self.output_folder.get():
                output_path = self.output_folder.get()
            else:
                # Create output folder INSIDE the input directory
                if input_path_obj.is_dir():
                    # For folder input: create output inside the folder
                    output_path = str(input_path_obj / isbn_number)
                else:
                    # For file input: create output inside the parent directory
                    output_path = str(input_path_obj.parent / isbn_number)
            
            # Set PDF naming and file naming convention
            config.set('output.pdf_name', isbn_number)
            config.set('output.file_prefix', isbn_number)  # New setting for file naming
            
            # Create args object for CLI
            class Args:
                pass
            
            args = Args()
            args.input = input_path
            args.output = output_path
            args.verbose = True
            args.log = False
            
            # Redirect stdout to capture logs
            original_stdout = sys.stdout
            log_capture = LogCapture(self)
            sys.stdout = log_capture
            
            try:
                success = self.cli.run(args)
                
                # Restore stdout
                sys.stdout = original_stdout
                
                # Check if processing was cancelled
                if self.cancel_processing:
                    self.root.after(0, self.processing_cancelled)
                elif success:
                    self.root.after(0, self.processing_complete, True, output_path)
                else:
                    self.root.after(0, self.processing_complete, False, None)
                
            finally:
                sys.stdout = original_stdout
                
        except Exception as e:
            self.root.after(0, self.processing_error, str(e))
    
    def processing_complete(self, success, output_path):
        """Handle processing completion"""
        self.processing = False
        self.cancel_processing = False
        self.process_btn.config(text="🚀 Organize My Pages", state="normal")
        self.cancel_btn.config(state="disabled")  # Disable cancel button
        self.progress_bar.stop()
        
        if success:
            self.status_label.config(text="✅ Pages organized successfully!")
            result = messagebox.askyesno("Success!", 
                              f"Your pages have been organized successfully!\n\n"
                              f"Organized pages saved to:\n{output_path}\n\n"
                              f"Would you like to open the folder?")
            
            # Ask to open output folder
            if result:
                try:
                    os.startfile(output_path)  # Windows
                except:
                    try:
                        import subprocess
                        subprocess.run(['open', output_path])  # macOS
                    except:
                        subprocess.run(['xdg-open', output_path])  # Linux
        else:
            self.status_label.config(text="❌ Processing failed")
            messagebox.showerror("Error", 
                               "Failed to organize pages. Please check the log for details.")
    
    def processing_error(self, error_msg):
        """Handle processing error"""
        self.processing = False
        self.cancel_processing = False
        self.process_btn.config(text="🚀 Organize My Pages", state="normal")
        self.cancel_btn.config(state="disabled")  # Disable cancel button
        self.progress_bar.stop()
        self.status_label.config(text="❌ Processing failed")
        
        messagebox.showerror("Error", f"An error occurred:\n{error_msg}")
    
    def processing_cancelled(self):
        """Handle processing cancellation"""
        self.processing = False
        self.cancel_processing = False
        self.process_btn.config(text="🚀 Organize My Pages", state="normal")
        self.cancel_btn.config(state="disabled")
        self.progress_bar.stop()
        self.status_label.config(text="🚫 Processing cancelled")
        
        messagebox.showinfo("Cancelled", "Processing was cancelled by user.")
    
    def detect_system_theme(self):
        """Detect system theme (Windows 10/11)"""
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize')
            value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
            self.system_is_dark = (value == 0)
        except:
            self.system_is_dark = False  # Default to light if can't detect
    
    def apply_theme(self):
        """Apply the selected theme"""
        if self.current_theme == "system":
            is_dark = self.system_is_dark
        elif self.current_theme == "dark":
            is_dark = True
        else:  # light
            is_dark = False
        
        # Configure ttk style
        style = ttk.Style()
        
        # IMPORTANT: Use the SAME base theme for both light and dark to prevent size changes
        try:
            style.theme_use('clam')  # Use clam for both themes
        except:
            style.theme_use('default')
        
        if is_dark:
            # Dark theme colors
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            entry_bg = "#3c3c3c"
            entry_fg = "#ffffff"
            button_bg = "#404040"
            frame_bg = "#333333"
            select_bg = "#0078d7"
            select_fg = "#ffffff"
            
            # Apply dark theme to all ttk widgets with proper styling
            style.configure('.', background=bg_color, foreground=fg_color, 
                          fieldbackground=entry_bg, selectbackground=select_bg,
                          selectforeground=select_fg)
            style.configure('TFrame', background=bg_color)
            style.configure('TLabel', background=bg_color, foreground=fg_color)
            style.configure('TLabelframe', background=bg_color, foreground=fg_color, 
                          bordercolor=frame_bg, lightcolor=frame_bg, darkcolor=frame_bg)
            style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color)
            style.configure('TButton', background=button_bg, foreground=fg_color,
                          bordercolor=button_bg, lightcolor=button_bg, darkcolor=button_bg)
            style.map('TButton', background=[('active', '#505050')])
            style.configure('TEntry', fieldbackground=entry_bg, foreground=entry_fg,
                          bordercolor=entry_bg, lightcolor=entry_bg, darkcolor=entry_bg)
            style.configure('TCombobox', fieldbackground=entry_bg, foreground=entry_fg,
                          bordercolor=entry_bg, selectbackground=select_bg, selectforeground=select_fg)
            style.configure('TCheckbutton', background=bg_color, foreground=fg_color)
            style.map('TCheckbutton', background=[('active', bg_color)])
            style.configure('TProgressbar', background='#4CAF50', troughcolor=frame_bg,
                          bordercolor=frame_bg, lightcolor=frame_bg, darkcolor=frame_bg)
        else:
            # Light theme colors
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            entry_bg = "#ffffff"
            entry_fg = "#000000"
            button_bg = "#e0e0e0"
            frame_bg = "#ffffff"
            select_bg = "#0078d7"
            select_fg = "#ffffff"
            
            # Apply light theme to all ttk widgets
            style.configure('.', background=bg_color, foreground=fg_color,
                          fieldbackground=entry_bg, selectbackground=select_bg,
                          selectforeground=select_fg)
            style.configure('TFrame', background=bg_color)
            style.configure('TLabel', background=bg_color, foreground=fg_color)
            style.configure('TLabelframe', background=bg_color, foreground=fg_color)
            style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color)
            style.configure('TButton', background=button_bg, foreground=fg_color)
            style.map('TButton', background=[('active', '#d0d0d0')])
            style.configure('TEntry', fieldbackground=entry_bg, foreground=entry_fg)
            style.configure('TCombobox', fieldbackground=entry_bg, foreground=entry_fg)
            style.configure('TCheckbutton', background=bg_color, foreground=fg_color)
            style.configure('TProgressbar', background='#4CAF50', troughcolor=frame_bg)
        
        # Apply colors to root window
        self.root.configure(bg=bg_color)
        
        # Apply colors to Text widget (log area) if it exists
        if hasattr(self, 'log_text'):
            self.log_text.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        
        # Force update
        self.root.update_idletasks()
    
    def toggle_theme(self):
        """Toggle between system/light/dark themes"""
        # Save current geometry and update state
        current_geometry = self.root.geometry()
        self.root.update_idletasks()
        
        themes = ["system", "light", "dark"]
        current_index = themes.index(self.current_theme)
        self.current_theme = themes[(current_index + 1) % 3]
        
        self.detect_system_theme()
        self.apply_theme()
        
        # Force update and restore geometry multiple times to ensure it sticks
        self.root.update_idletasks()
        self.root.geometry(current_geometry)
        self.root.update()
        self.root.geometry(current_geometry)
        
        # Update window title to show current theme
        theme_names = {"system": "System", "light": "Light", "dark": "Dark"}
        self.root.title(f"MF Page Organizer - {theme_names[self.current_theme]} Mode")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
🔹 How to use MF Page Organizer:

1. SELECT YOUR PAGES:
   • Drag & drop files/folders directly into the input field
   • OR click "Browse Files" to select
   • Supported formats: PDF, PNG, JPG, TIFF

2. CONFIGURE OPTIONS:
   • Image quality enhancement: Improves unclear scans
   • Auto-rotate pages: Fixes landscape/portrait orientation
   • Auto crop pages: Remove borders and margins automatically
   • Clean dirty pages: Remove dark circles and spots
   • Remove blank pages: Choose where to remove blanks
     - None: Keep all pages
     - Start Only: Remove blank pages from beginning
     - End Only: Remove blank pages from end
     - Start & End: Remove from both (recommended)
     - All Blank Pages: Remove all blank pages
   • PDF compression: Reduce file size (optional)
   • Accuracy level: Higher = better results, slower processing

3. CHOOSE OUTPUT LOCATION:
   • Select where to save organized pages
   • Leave empty to create folder with same name as input folder
   • Output will contain: organized images + PDF file
   • Example: Input "mark" → Output "mark/mark/" with images + mark.pdf

4. CLICK "ORGANIZE MY PAGES":
   • The app will automatically detect page numbers
   • Blank pages will be removed (if enabled)
   • Pages will be arranged in correct order
   • Results saved as organized PDF

🔹 Tips:
   • Drag & drop is the easiest way to add files!
   • "Start & End" blank removal is best for scanned books
   • Auto crop removes unwanted borders automatically
   • Dark circle cleanup fixes scanner marks and spots
   • Use ❌ Cancel button to stop processing anytime
   • Enable compression for smaller PDFs (easier to email)
   • Use "High Accuracy" for difficult-to-read pages
   • The app can handle mixed numbering (1,2,3 or i,ii,iii)

🔹 Need help? The app will show recommendations if pages can't be organized automatically.
        """
        
        messagebox.showinfo("Help - MF Page Organizer", help_text)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
MF Page Organizer
Version 1.0

Automatically organizes scanned document pages using:
• Embedded OCR (no installation required)
• Artificial Intelligence
• Content Analysis
• Auto-rotation detection
• Smart blank page removal
• PDF compression

Perfect for organizing:
• Scanned book pages
• Document photocopies  
• Mixed page orders
• Multiple numbering systems
• Landscape and portrait pages

Features:
• Drag & drop support
• Auto crop borders and margins
• Clean dark circles and spots
• Remove blank pages (start/end/all)
• Auto-rotate sideways pages
• Compress PDFs for smaller files
• Cancel processing anytime
• No technical knowledge required

© 2025 MF Page Organizer
All rights reserved.
        """
        
        messagebox.showinfo("About - MF Page Organizer", about_text)

class LogCapture:
    """Capture stdout and display in GUI"""
    def __init__(self, app):
        self.app = app
        
    def write(self, text):
        if text.strip():
            self.app.root.after(0, self.update_log, text)
    
    def update_log(self, text):
        self.app.log_text.config(state=tk.NORMAL)
        self.app.log_text.insert(tk.END, text)
        self.app.log_text.see(tk.END)
        self.app.log_text.config(state=tk.DISABLED)
    
    def flush(self):
        pass

def main():
    """Main function"""
    root = tk.Tk()
    
    # Don't configure theme here - let the app handle it
    app = MFPageOrganizerApp(root)
    
    # Handle window closing
    def on_closing():
        if app.processing:
            if messagebox.askokcancel("Quit", "Processing is in progress. Are you sure you want to quit?"):
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    # Simple and reliable startup - works in both script and EXE mode
    try:
        # Try to show splash screen if available
        if show_splash_with_loading and not getattr(sys, 'frozen', False):
            # Only use splash in script mode (not in EXE)
            from splash_screen import SplashScreen
            import threading
            import time
            
            root = tk.Tk()
            root.withdraw()
            
            splash = SplashScreen(root)
            
            def load_and_show():
                time.sleep(0.8)
                splash.update_status("Loading OCR engine...")
                time.sleep(0.8)
                splash.update_status("Initializing AI models...")
                time.sleep(0.8)
                splash.update_status("Preparing interface...")
                time.sleep(0.8)
                splash.update_status("Almost ready...")
                time.sleep(0.6)
                splash.close()
                
                root.after(100, lambda: [
                    root.deiconify(),
                    MFPageOrganizerApp(root)
                ])
            
            thread = threading.Thread(target=load_and_show, daemon=True)
            thread.start()
            
            def on_closing():
                root.destroy()
            
            root.protocol("WM_DELETE_WINDOW", on_closing)
            root.mainloop()
        else:
            # In EXE mode or if splash not available, just run main()
            main()
    except Exception as e:
        # Fallback to simple main() if anything fails
        print(f"Startup error: {e}")
        main()
