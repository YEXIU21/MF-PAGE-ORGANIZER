"""
Interactive Training Data Labeler
GUI tool with click-and-drag region selection
User manually selects page number region and labels it
"""

import cv2
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import json
import time

# Module-level cache to prevent PhotoImage garbage collection
_IMAGE_CACHE = {}

class InteractiveLabeler:
    """GUI for interactive manual labeling with region selection"""
    
    def __init__(self, image_folder: str, output_folder: str = "ml_training/manual_training_data"):
        self.image_folder = Path(image_folder)
        self.output_folder = Path(output_folder)
        self.corners_dir = self.output_folder / "corners"
        self.corners_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all images
        self.image_files = self.get_image_files()
        self.current_index = 0
        
        # Selection state
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.selecting = False
        
        # Zoom state
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 4.0
        
        # Image reference keeper to prevent garbage collection
        self._image_keeper = []
        
        # Stats
        self.stats = {
            'total_processed': 0,
            'total_labeled': 0,
            'labels_created': {}
        }
        
        # Create GUI
        self.setup_gui()
    
    def get_image_files(self):
        """Get all image files from folder"""
        files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            matches = list(self.image_folder.glob(ext))
            files.extend(matches)
            if matches:
                print(f"[DEBUG] Found {len(matches)} files with extension {ext}")
        
        # Remove duplicates (case-insensitive filesystems might cause duplicates)
        unique_files = list(set(files))
        print(f"[DEBUG] Total files found: {len(files)}, Unique files: {len(unique_files)}")
        print(f"[DEBUG] Image folder: {self.image_folder}")
        
        return sorted(unique_files)
    
    def setup_gui(self):
        """Create the GUI interface"""
        self.root = tk.Tk()
        self.root.title(f"Interactive Page Number Labeler - {len(self.image_files)} images")
        self.root.geometry("1400x900")
        
        # Configure theme to avoid Accent.TButton pyimage1 errors
        style = ttk.Style(self.root)
        print(f"[DEBUG] Available themes: {style.theme_names()}")
        try:
            style.theme_use('clam')  # Use clam theme (no Accent image requirements)
            print(f"[DEBUG] Theme set to: {style.theme_use()}")
        except Exception as e:
            print(f"[DEBUG] Failed to set clam theme: {e}")
            style.theme_use('default')
            print(f"[DEBUG] Fallback theme set to: {style.theme_use()}")
        
        # NUCLEAR FIX: Pre-initialize tkinter's image system
        import numpy as np
        dummy_array = np.zeros((10, 10, 3), dtype=np.uint8)
        dummy_pil = Image.fromarray(dummy_array)
        self._dummy_photo = ImageTk.PhotoImage(dummy_pil)
        self.root._dummy_keep = self._dummy_photo  # Keep reference
        print("[DEBUG] Tkinter image system pre-initialized")
        
        # Initialize photo reference BEFORE any image operations
        self.photo = None
        self.pil_image = None
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Image display
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Use Canvas instead of Label for precise coordinate control
        self.image_canvas = tk.Canvas(left_frame, bg='black', highlightthickness=0)
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Track image position on canvas
        self.canvas_image_id = None
        self.image_offset_x = 0
        self.image_offset_y = 0
        
        # Bind mouse events for selection
        self.image_canvas.bind('<Button-1>', self.on_mouse_down)
        self.image_canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.image_canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        
        # Bind mouse wheel for zoom
        self.image_canvas.bind('<MouseWheel>', self.on_mouse_wheel)  # Windows/Mac
        self.image_canvas.bind('<Button-4>', self.on_mouse_wheel)    # Linux scroll up
        self.image_canvas.bind('<Button-5>', self.on_mouse_wheel)    # Linux scroll down
        
        # Right panel - Controls
        right_frame = ttk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # Instructions
        instructions = tk.Text(right_frame, height=10, wrap=tk.WORD, font=('Arial', 9))
        instructions.pack(fill=tk.X, pady=(0, 10))
        instructions.insert('1.0', """INSTRUCTIONS:

1. Click and drag on the image to select the region containing the page number

2. Type the page number in the box below

3. Click "Save & Next" or press Enter

4. Click "Skip" or press Space to skip this image

5. When done, click "Finish Labeling" button

Tip: Label 20+ images for best ML accuracy!
""") 
        instructions.config(state=tk.DISABLED)
        
        # Progress
        progress_frame = ttk.LabelFrame(right_frame, text="Progress", padding=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text=f"Image 1 of {len(self.image_files)}")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        self.progress_bar['maximum'] = len(self.image_files)
        self.progress_bar['value'] = 0
        
        # Current image info
        info_frame = ttk.LabelFrame(right_frame, text="Current Image", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.filename_label = ttk.Label(info_frame, text="", wraplength=260)
        self.filename_label.pack()
        
        # Selection info
        selection_frame = ttk.LabelFrame(right_frame, text="Selection", padding=10)
        selection_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.selection_label = ttk.Label(selection_frame, text="No region selected", foreground='red')
        self.selection_label.pack()
        
        # Label input
        label_frame = ttk.LabelFrame(right_frame, text="Page Number", padding=10)
        label_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.label_entry = ttk.Entry(label_frame, font=('Arial', 14))
        self.label_entry.pack(fill=tk.X)
        self.label_entry.bind('<Return>', lambda e: self.save_and_next())
        self.label_entry.focus()
        
        # Zoom controls
        zoom_frame = ttk.LabelFrame(right_frame, text="Zoom", padding=10)
        zoom_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.zoom_label = ttk.Label(zoom_frame, text="100%", font=('Arial', 12, 'bold'))
        self.zoom_label.pack(pady=(0, 5))
        
        zoom_buttons = ttk.Frame(zoom_frame)
        zoom_buttons.pack(fill=tk.X)
        
        ttk.Button(zoom_buttons, text="➖ Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(zoom_buttons, text="🔄 Reset", command=self.zoom_reset).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(zoom_buttons, text="➕ Zoom In", command=self.zoom_in).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        ttk.Label(zoom_frame, text="(or use mouse wheel)", font=('Arial', 8), foreground='gray').pack(pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.save_button = ttk.Button(button_frame, text="✓ Save & Next", command=self.save_and_next)
        self.save_button.pack(fill=tk.X, pady=(0, 5))
        
        self.skip_button = ttk.Button(button_frame, text="⏭ Skip", command=self.skip_image)
        self.skip_button.pack(fill=tk.X, pady=(0, 5))
        
        self.prev_button = ttk.Button(button_frame, text="⏮ Previous", command=self.previous_image)
        self.prev_button.pack(fill=tk.X, pady=(0, 5))
        
        # Separator
        ttk.Separator(button_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Finish button - allows user to stop and proceed to training
        self.finish_button = ttk.Button(
            button_frame, 
            text="✅ Finish Labeling", 
            command=self.finish_labeling,
            style='Accent.TButton'
        )
        self.finish_button.pack(fill=tk.X, pady=(0, 5))
        
        # Stats
        stats_frame = ttk.LabelFrame(right_frame, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        self.stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD, font=('Arial', 9))
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Keyboard shortcuts
        self.root.bind('<space>', lambda e: self.skip_image())
        self.root.bind('<Escape>', lambda e: self.on_close())
        
        # Ensure window is fully initialized before loading images
        self.root.update()
        
        # Schedule image loading to run AFTER mainloop starts (critical for PhotoImage)
        self.root.after(500, self._delayed_load)  # 500ms delay for stability
    
    def _delayed_load(self):
        """Load first image after mainloop has started"""
        print("[DEBUG] _delayed_load() called - loading first image...")
        try:
            # Force widget to fully initialize
            self.root.update_idletasks()
            self.image_label.update()
            
            self.load_current_image()
            print("[DEBUG] First image loaded successfully")
            self.update_stats_display()
        except Exception as e:
            print(f"[ERROR] Failed to load initial image: {e}")
            import traceback
            traceback.print_exc()
            # Try again with longer delay
            print("[DEBUG] Retrying image load in 1 second...")
            self.root.after(1000, self._retry_load)
    
    def _retry_load(self):
        """Retry loading the first image with error handling"""
        try:
            print("[DEBUG] Retry attempt...")
            self.root.update_idletasks()
            self.load_current_image()
            print("[DEBUG] Retry successful!")
            self.update_stats_display()
        except Exception as e:
            print(f"[ERROR] Retry also failed: {e}")
            messagebox.showerror(
                "Image Loading Error",
                f"Failed to load images. Please check:\n\n"
                f"1. Image folder exists and contains images\n"
                f"2. Images are valid (not corrupted)\n"
                f"3. You have permission to read the files\n\n"
                f"Error: {e}"
            )
    
    def load_current_image(self):
        """Load and display current image"""
        if self.current_index >= len(self.image_files):
            self.on_complete()
            return
        
        image_path = self.image_files[self.current_index]
        
        # Load image with OpenCV
        self.current_cv_image = cv2.imread(str(image_path))
        if self.current_cv_image is None:
            messagebox.showerror("Error", f"Could not load image: {image_path.name}")
            self.skip_image()
            return
        
        # Convert to RGB for PIL
        rgb_image = cv2.cvtColor(self.current_cv_image, cv2.COLOR_BGR2RGB)
        
        # Resize to fit display (max 1000x800)
        h, w = rgb_image.shape[:2]
        max_w, max_h = 1000, 800
        scale = min(max_w/w, max_h/h, 1.0)
        
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            rgb_image = cv2.resize(rgb_image, (new_w, new_h))
        
        # Store scale for coordinate conversion
        self.base_scale = scale  # Base scale (fit to screen)
        self.display_scale = scale  # Current display scale (base * zoom)
        self.display_image = rgb_image.copy()
        self.original_rgb = rgb_image.copy()  # Keep original for zoom
        
        # Apply zoom to image
        zoomed_rgb = self._apply_zoom(rgb_image)
        
        # Convert to PIL and Tk
        # CRITICAL FIX: Assign to self.photo BEFORE canvas display to prevent GC
        # Explicitly specify master widget to prevent reference issues
        self.pil_image = Image.fromarray(zoomed_rgb)
        self.photo = ImageTk.PhotoImage(self.pil_image, master=self.image_canvas)  # Use master parameter
        
        # Add multiple references BEFORE displaying to prevent premature GC
        self.photo.image = self.pil_image
        self._image_keeper.append(self.photo)
        _IMAGE_CACHE[f'image_{self.current_index}'] = self.photo  # Module-level cache
        
        # Calculate center position for image on canvas
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        # If canvas not yet rendered, use reasonable defaults
        if canvas_width <= 1:
            canvas_width = 1000
        if canvas_height <= 1:
            canvas_height = 800
        
        img_width, img_height = self.pil_image.size
        self.image_offset_x = max(0, (canvas_width - img_width) // 2)
        self.image_offset_y = max(0, (canvas_height - img_height) // 2)
        
        # Clear canvas and display image at calculated position
        self.image_canvas.delete("all")
        # Force canvas update before creating new image
        self.image_canvas.update_idletasks()
        self.canvas_image_id = self.image_canvas.create_image(
            self.image_offset_x, 
            self.image_offset_y,
            anchor=tk.NW,  # Northwest anchor = top-left corner at specified position
            image=self.photo
        )
        # Force canvas to redraw
        self.image_canvas.update()
        
        # Update info
        self.filename_label.config(text=image_path.name)
        self.progress_label.config(text=f"Image {self.current_index + 1} of {len(self.image_files)}")
        self.progress_bar['value'] = self.current_index
        
        # Reset selection and zoom
        self.start_x = self.start_y = self.end_x = self.end_y = None
        self.selection_label.config(text="No region selected", foreground='red')
        self.label_entry.delete(0, tk.END)
        self.label_entry.focus()
        self.zoom_level = 1.0
        self.zoom_label.config(text="100%")
    
    def _apply_zoom(self, rgb_image):
        """Apply current zoom level to image"""
        if self.zoom_level == 1.0:
            return rgb_image
        
        h, w = rgb_image.shape[:2]
        new_w = int(w * self.zoom_level)
        new_h = int(h * self.zoom_level)
        
        if self.zoom_level > 1.0:
            # Zoom in - use INTER_CUBIC for better quality
            zoomed = cv2.resize(rgb_image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        else:
            # Zoom out - use INTER_AREA for better downscaling
            zoomed = cv2.resize(rgb_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        return zoomed
    
    def zoom_in(self):
        """Zoom in by 25%"""
        if self.zoom_level < self.max_zoom:
            self.zoom_level = min(self.zoom_level * 1.25, self.max_zoom)
            self._update_zoom()
    
    def zoom_out(self):
        """Zoom out by 25%"""
        if self.zoom_level > self.min_zoom:
            self.zoom_level = max(self.zoom_level / 1.25, self.min_zoom)
            self._update_zoom()
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.zoom_level = 1.0
        self._update_zoom()
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel zoom"""
        # Determine zoom direction
        if event.num == 5 or event.delta < 0:  # Scroll down or negative delta
            self.zoom_out()
        elif event.num == 4 or event.delta > 0:  # Scroll up or positive delta
            self.zoom_in()
    
    def _update_zoom(self):
        """Update display with new zoom level"""
        if not hasattr(self, 'original_rgb'):
            return
        
        # Update zoom label
        zoom_percent = int(self.zoom_level * 100)
        self.zoom_label.config(text=f"{zoom_percent}%")
        
        # Update display scale
        self.display_scale = self.base_scale * self.zoom_level
        
        # Reapply zoom to original image
        zoomed_rgb = self._apply_zoom(self.original_rgb)
        
        # Update PIL and Tk image
        self.pil_image = Image.fromarray(zoomed_rgb)
        self.photo = ImageTk.PhotoImage(self.pil_image, master=self.image_canvas)
        
        # Keep references to prevent GC
        self.photo.image = self.pil_image
        self._image_keeper.append(self.photo)
        _IMAGE_CACHE[f'zoom_{self.current_index}_{self.zoom_level}'] = self.photo
        
        # Recalculate center position
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 1000
        if canvas_height <= 1:
            canvas_height = 800
        
        img_width, img_height = self.pil_image.size
        self.image_offset_x = max(0, (canvas_width - img_width) // 2)
        self.image_offset_y = max(0, (canvas_height - img_height) // 2)
        
        # Update canvas
        self.image_canvas.delete("all")
        self.image_canvas.update_idletasks()
        self.canvas_image_id = self.image_canvas.create_image(
            self.image_offset_x,
            self.image_offset_y,
            anchor=tk.NW,
            image=self.photo
        )
        self.image_canvas.update()
        
        # Redraw selection if exists
        if self.start_x is not None and self.end_x is not None:
            self.draw_selection()
    
    def on_mouse_down(self, event):
        """Mouse button pressed - start selection"""
        # Adjust coordinates to account for image offset on canvas
        self.start_x = event.x - self.image_offset_x
        self.start_y = event.y - self.image_offset_y
        self.selecting = True
    
    def on_mouse_drag(self, event):
        """Mouse dragged - update selection"""
        if self.selecting:
            # Adjust coordinates to account for image offset on canvas
            self.end_x = event.x - self.image_offset_x
            self.end_y = event.y - self.image_offset_y
            self.draw_selection()
    
    def on_mouse_up(self, event):
        """Mouse button released - finish selection"""
        if self.selecting:
            # Adjust coordinates to account for image offset on canvas
            self.end_x = event.x - self.image_offset_x
            self.end_y = event.y - self.image_offset_y
            self.selecting = False
            self.draw_selection()
            
            # Update selection info
            width = abs(self.end_x - self.start_x)
            height = abs(self.end_y - self.start_y)
            self.selection_label.config(
                text=f"Selected: {width}x{height}px",
                foreground='green'
            )
    
    def draw_selection(self):
        """Draw selection rectangle on canvas"""
        if self.start_x is None or self.end_x is None:
            return
        
        # Delete previous selection rectangle if it exists
        self.image_canvas.delete("selection_rect")
        
        # Calculate rectangle coordinates (relative to image, not canvas)
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)
        
        # Clamp coordinates to image bounds
        img_width, img_height = self.pil_image.size if self.pil_image else (1000, 800)
        x1 = max(0, min(x1, img_width))
        y1 = max(0, min(y1, img_height))
        x2 = max(0, min(x2, img_width))
        y2 = max(0, min(y2, img_height))
        
        # Draw rectangle on canvas (adjust back to canvas coordinates)
        self.image_canvas.create_rectangle(
            x1 + self.image_offset_x,
            y1 + self.image_offset_y,
            x2 + self.image_offset_x,
            y2 + self.image_offset_y,
            outline='red',
            width=2,
            tags="selection_rect"
        )
    
    def save_and_next(self):
        """Save current selection and move to next"""
        # Validate selection
        if self.start_x is None or self.end_x is None:
            messagebox.showwarning("No Selection", "Please select a region first!")
            return
        
        # Validate label
        label = self.label_entry.get().strip()
        if not label:
            messagebox.showwarning("No Label", "Please enter the page number!")
            self.label_entry.focus()
            return
        
        # Get crop coordinates (convert from display to original image)
        x1 = int(min(self.start_x, self.end_x) / self.display_scale)
        y1 = int(min(self.start_y, self.end_y) / self.display_scale)
        x2 = int(max(self.start_x, self.end_x) / self.display_scale)
        y2 = int(max(self.start_y, self.end_y) / self.display_scale)
        
        # Ensure coordinates are within bounds
        h, w = self.current_cv_image.shape[:2]
        x1 = max(0, min(x1, w-1))
        x2 = max(0, min(x2, w))
        y1 = max(0, min(y1, h-1))
        y2 = max(0, min(y2, h))
        
        # Crop region
        crop = self.current_cv_image[y1:y2, x1:x2]
        
        if crop.size == 0:
            messagebox.showerror("Invalid Selection", "Selected region is too small!")
            return
        
        # Resize to 200x200
        crop_resized = cv2.resize(crop, (200, 200), interpolation=cv2.INTER_AREA)
        
        # Save
        class_dir = self.corners_dir / label
        class_dir.mkdir(exist_ok=True)
        
        timestamp = str(int(time.time() * 1000))
        filename = f"{label}_{self.image_files[self.current_index].stem}_{timestamp}.jpg"
        save_path = class_dir / filename
        
        cv2.imwrite(str(save_path), crop_resized)
        
        # Update stats
        self.stats['total_labeled'] += 1
        if label not in self.stats['labels_created']:
            self.stats['labels_created'][label] = 0
        self.stats['labels_created'][label] += 1
        
        self.stats['total_processed'] += 1
        
        self.update_stats_display()
        
        # Next image
        self.current_index += 1
        self.load_current_image()
    
    def skip_image(self):
        """Skip current image"""
        self.stats['total_processed'] += 1
        self.current_index += 1
        self.load_current_image()
    
    def previous_image(self):
        """Go back to previous image"""
        if self.current_index > 0:
            self.current_index -= 1
            # Decrease processed count if we're going back
            if self.stats['total_processed'] > 0:
                self.stats['total_processed'] -= 1
            self.load_current_image()
        else:
            messagebox.showinfo("First Image", "Already at the first image!")
    
    def update_stats_display(self):
        """Update statistics display"""
        self.stats_text.delete('1.0', tk.END)
        
        stats_str = f"Processed: {self.stats['total_processed']}\n"
        stats_str += f"Labeled: {self.stats['total_labeled']}\n"
        stats_str += f"Skipped: {self.stats['total_processed'] - self.stats['total_labeled']}\n"
        stats_str += f"\nUnique labels: {len(self.stats['labels_created'])}\n"
        
        if self.stats['labels_created']:
            stats_str += "\nLabel counts:\n"
            for label, count in sorted(self.stats['labels_created'].items()):
                stats_str += f"  {label}: {count}\n"
        
        self.stats_text.insert('1.0', stats_str)
    
    def finish_labeling(self):
        """User clicks Finish & Train button - ready to proceed with training"""
        # Check if user has labeled enough images
        if self.stats['total_labeled'] < 10:
            result = messagebox.askyesno(
                "Few Training Examples",
                f"You've only labeled {self.stats['total_labeled']} images.\n\n"
                f"Recommended: 20+ images for good ML accuracy.\n\n"
                f"Continue with training anyway?"
            )
            if not result:
                return  # User wants to label more
        
        # Confirm finish
        result = messagebox.askyesno(
            "Finish Labeling?",
            f"Save and finish labeling?\n\n"
            f"✓ Labeled: {self.stats['total_labeled']} images\n"
            f"✓ Unique labels: {len(self.stats['labels_created'])}\n\n"
            f"Data will be saved to ml_training/manual_training_data/"
        )
        
        if result:
            # Save stats and close
            stats_file = self.output_folder / "labeling_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
            
            messagebox.showinfo(
                "Labeling Complete!",
                f"✅ Saved {self.stats['total_labeled']} labeled images\n\n"
                f"Data saved to: ml_training/manual_training_data/\n\n"
                f"Return to main app and processing will work!"
            )
            
            self.root.destroy()
    
    def on_complete(self):
        """All images processed"""
        # Save stats
        stats_file = self.output_folder / "labeling_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
        
        messagebox.showinfo("Complete!", 
                           f"Labeling complete!\n\n"
                           f"Total processed: {self.stats['total_processed']}\n"
                           f"Total labeled: {self.stats['total_labeled']}\n"
                           f"Unique labels: {len(self.stats['labels_created'])}\n\n"
                           f"Data saved to: {self.output_folder}")
        
        self.root.destroy()
    
    def on_close(self):
        """Window closing"""
        if messagebox.askyesno("Quit?", "Are you sure you want to quit?\nProgress will be saved."):
            try:
                # Save stats
                stats_file = self.output_folder / "labeling_stats.json"
                with open(stats_file, 'w') as f:
                    json.dump(self.stats, f, indent=2)
                print(f"[INFO] Stats saved to {stats_file}")
            except Exception as e:
                print(f"[WARNING] Failed to save stats: {e}")
            finally:
                # Ensure window closes even if stats save fails
                self.root.quit()  # Exit mainloop
                self.root.destroy()  # Destroy window
    
    def run(self):
        """Start the GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()


def main():
    import sys
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           INTERACTIVE TRAINING DATA LABELER                          ║
╚══════════════════════════════════════════════════════════════════════╝

Click and drag to select page number region!
Much easier and more flexible than predefined corners!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    
    if len(sys.argv) < 2:
        print("USAGE:")
        print("  python ml_training/interactive_labeler.py <folder_with_images>")
        print()
        folder = input("Enter path to folder with page images: ").strip().strip('"')
        if not folder:
            print("❌ No folder specified")
            return
    else:
        folder = sys.argv[1]
    
    if not os.path.exists(folder):
        print(f"❌ Folder not found: {folder}")
        return
    
    labeler = InteractiveLabeler(folder)
    labeler.run()
    
    print("\n✅ Labeling session complete!")


if __name__ == "__main__":
    main()
