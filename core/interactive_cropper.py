"""
Interactive Manual Cropping System
Multi-page selection with batch apply functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class InteractiveCropper:
    """GUI tool for batch manual cropping with multi-page selection"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.root = None
        self.problematic_pages = []
        self.images = {}
        self.page_checkboxes = {}
        self.page_vars = {}
        self.current_image = None
        self.current_page_name = None
        self.crop_coordinates = None
        self.scale_factor = 1.0
        
    def show_cropping_interface(self, problematic_pages: List[Dict], 
                                images: Dict[str, Image.Image]) -> Dict[str, Tuple]:
        """
        Show multi-page selection interface for batch cropping
        
        Args:
            problematic_pages: List of page validation results from CropValidator
            images: Dict mapping page names to PIL Images
            
        Returns:
            Dict mapping page names to crop coordinates (x1, y1, x2, y2)
            None if user cancelled
        """
        if not problematic_pages:
            return {}
        
        self.problematic_pages = problematic_pages
        self.images = images
        
        # Create main window
        self.root = tk.Tk()
        self.root.title(f"Manual Crop Required - {len(problematic_pages)} Pages Need Review")
        self.root.geometry("1400x900")
        
        # Create UI
        self._create_ui()
        
        # Wait for user
        self.root.mainloop()
        
        # Return results
        if hasattr(self, 'crop_results'):
            return self.crop_results
        return None
    
    def _create_ui(self):
        """Create the main UI layout"""
        # Main container with 3 panels
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # LEFT PANEL: Page list with checkboxes
        left_frame = ttk.Frame(main_pane, width=350)
        main_pane.add(left_frame, weight=1)
        
        self._create_page_list_panel(left_frame)
        
        # CENTER PANEL: Image display and cropping
        center_frame = ttk.Frame(main_pane)
        main_pane.add(center_frame, weight=3)
        
        self._create_image_panel(center_frame)
        
        # RIGHT PANEL: Instructions and actions
        right_frame = ttk.Frame(main_pane, width=300)
        main_pane.add(right_frame, weight=1)
        
        self._create_instructions_panel(right_frame)
    
    def _create_page_list_panel(self, parent):
        """Create left panel with page list and selection"""
        ttk.Label(parent, text="Pages Needing Manual Crop", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # Select all / None buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="✓ Select All", 
                  command=self._select_all_pages).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✗ Select None", 
                  command=self._select_no_pages).pack(side=tk.LEFT, padx=2)
        
        # Scrollable list of pages
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add checkboxes for each page
        for idx, page_info in enumerate(self.problematic_pages):
            page_name = page_info['page_name']
            
            # Create frame for this page
            page_frame = ttk.LabelFrame(scrollable_frame, text=f"Page {idx+1}", padding=5)
            page_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Checkbox variable
            var = tk.BooleanVar(value=True)  # Default: all selected
            self.page_vars[page_name] = var
            
            # Checkbox
            chk = ttk.Checkbutton(page_frame, text=page_name, variable=var)
            chk.pack(anchor=tk.W)
            self.page_checkboxes[page_name] = chk
            
            # Show confidence
            conf_color = "red" if page_info['confidence'] < 70 else "orange"
            ttk.Label(page_frame, text=f"Confidence: {page_info['confidence']:.0f}%", 
                     foreground=conf_color, font=("Arial", 9)).pack(anchor=tk.W)
            
            # Show issues
            for issue in page_info['issues'][:2]:  # Show first 2 issues
                ttk.Label(page_frame, text=f"• {issue[:50]}...", 
                         font=("Arial", 8), foreground="darkred").pack(anchor=tk.W, padx=10)
            
            # Preview button
            ttk.Button(page_frame, text="👁 Preview", 
                      command=lambda pn=page_name: self._show_preview(pn)).pack(anchor=tk.W, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Info label
        ttk.Label(parent, text=f"Total: {len(self.problematic_pages)} pages", 
                 font=("Arial", 10)).pack(pady=5)
    
    def _create_image_panel(self, parent):
        """Create center panel for image display and cropping"""
        ttk.Label(parent, text="Crop Area", 
                 font=("Arial", 12, "bold")).pack(pady=5)
        
        # Current page name
        self.current_page_label = ttk.Label(parent, text="Select a page to preview", 
                                           font=("Arial", 10))
        self.current_page_label.pack(pady=5)
        
        # Canvas for image display
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg="gray", cursor="cross")
        v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind mouse events for drawing crop rectangle
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_press)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        
        # Reset crop button
        ttk.Button(parent, text="↺ Reset Crop Rectangle", 
                  command=self._reset_crop).pack(pady=5)
    
    def _create_instructions_panel(self, parent):
        """Create right panel with instructions and action buttons"""
        ttk.Label(parent, text="Instructions", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        instructions = """
1. SELECT PAGES:
   ☑ Check/uncheck pages in left panel
   ☑ Select all pages you want to crop

2. PREVIEW IMAGE:
   👁 Click "Preview" to see any page
   
3. DRAW CROP AREA:
   🖱 Click and drag on image
   🖱 Draw rectangle around content
   
4. APPLY CROP:
   ✓ Crop applies to ALL SELECTED pages
   ✓ Same crop rectangle for all
   
5. CONFIRM:
   Click "Apply Crop to Selected"
        """
        
        text_widget = tk.Text(parent, wrap=tk.WORD, height=20, width=35, 
                             font=("Arial", 9), bg="#f0f0f0")
        text_widget.insert("1.0", instructions)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # Status
        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(parent, text="No crop defined yet", 
                                     font=("Arial", 9), foreground="gray")
        self.status_label.pack(pady=5)
        
        # Action buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="✓ Apply Crop to Selected Pages", 
                  command=self._apply_crop,
                  style="Accent.TButton").pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="⊗ Skip All (Use Auto-Crop)", 
                  command=self._skip_all).pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="✕ Cancel Processing", 
                  command=self._cancel).pack(fill=tk.X, pady=5)
    
    def _select_all_pages(self):
        """Select all pages"""
        for var in self.page_vars.values():
            var.set(True)
        if self.logger:
            self.logger.info(f"Selected all {len(self.page_vars)} pages")
    
    def _select_no_pages(self):
        """Deselect all pages"""
        for var in self.page_vars.values():
            var.set(False)
    
    def _show_preview(self, page_name):
        """Show preview of a page"""
        if page_name not in self.images:
            messagebox.showerror("Error", f"Image not found: {page_name}")
            return
        
        self.current_page_name = page_name
        self.current_page_label.config(text=f"Previewing: {page_name}")
        
        # Display image
        image = self.images[page_name]
        self._display_image(image)
    
    def _display_image(self, image: Image.Image):
        """Display image on canvas"""
        self.current_image = image
        
        # Calculate scale
        canvas_width = 800
        canvas_height = 600
        img_width, img_height = image.size
        
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.scale_factor = min(scale_x, scale_y, 1.0)
        
        new_width = int(img_width * self.scale_factor)
        new_height = int(img_height * self.scale_factor)
        
        # Resize for display
        display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.current_image_tk = ImageTk.PhotoImage(display_image)
        
        # Clear canvas
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image_tk)
    
    def _on_mouse_press(self, event):
        """Mouse press to start crop rectangle"""
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        if hasattr(self, 'rect_id') and self.rect_id:
            self.canvas.delete(self.rect_id)
    
    def _on_mouse_drag(self, event):
        """Mouse drag to draw crop rectangle"""
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        
        if hasattr(self, 'rect_id') and self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, cur_x, cur_y,
            outline="red", width=3, dash=(5, 5)
        )
    
    def _on_mouse_release(self, event):
        """Mouse release to finalize crop"""
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # Normalize coordinates
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        # Convert to original image coordinates
        orig_x1 = int(x1 / self.scale_factor)
        orig_y1 = int(y1 / self.scale_factor)
        orig_x2 = int(x2 / self.scale_factor)
        orig_y2 = int(y2 / self.scale_factor)
        
        self.crop_coordinates = (orig_x1, orig_y1, orig_x2, orig_y2)
        
        # Redraw with final style
        if hasattr(self, 'rect_id') and self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="green", width=3
        )
        
        # Update status
        width = orig_x2 - orig_x1
        height = orig_y2 - orig_y1
        self.status_label.config(
            text=f"✓ Crop defined: {width}x{height}px",
            foreground="green"
        )
    
    def _reset_crop(self):
        """Reset crop rectangle"""
        if hasattr(self, 'rect_id') and self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        
        self.crop_coordinates = None
        self.status_label.config(text="No crop defined yet", foreground="gray")
    
    def _apply_crop(self):
        """Apply crop to all selected pages"""
        if not self.crop_coordinates:
            messagebox.showwarning("No Crop Defined", 
                                 "Please draw a crop rectangle first!")
            return
        
        # Get selected pages
        selected_pages = [name for name, var in self.page_vars.items() if var.get()]
        
        if not selected_pages:
            messagebox.showwarning("No Pages Selected", 
                                 "Please select at least one page to crop!")
            return
        
        # Confirm
        if not messagebox.askyesno("Confirm Crop", 
                                  f"Apply this crop to {len(selected_pages)} selected page(s)?"):
            return
        
        # Create results
        self.crop_results = {}
        for page_name in selected_pages:
            self.crop_results[page_name] = self.crop_coordinates
        
        if self.logger:
            self.logger.info(f"✂️ Applying crop to {len(selected_pages)} pages")
        
        self.root.destroy()
    
    def _skip_all(self):
        """Skip all pages - use auto-crop results"""
        if messagebox.askyesno("Skip Manual Crop", 
                              "Skip manual cropping for all pages and use auto-crop results?"):
            self.crop_results = {}
            self.root.destroy()
    
    def _cancel(self):
        """Cancel entire processing"""
        if messagebox.askyesno("Cancel Processing", 
                              "Cancel the entire document processing?"):
            self.crop_results = None
            self.root.destroy()
