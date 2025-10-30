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
            files.extend(list(self.image_folder.glob(ext)))
        return sorted(files)
    
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
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Image display
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Image label
        self.image_label = tk.Label(left_frame, bg='black')
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for selection
        self.image_label.bind('<Button-1>', self.on_mouse_down)
        self.image_label.bind('<B1-Motion>', self.on_mouse_drag)
        self.image_label.bind('<ButtonRelease-1>', self.on_mouse_up)
        
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

5. Selection box shown in RED""")
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
        
        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.save_button = ttk.Button(button_frame, text="✓ Save & Next", command=self.save_and_next)
        self.save_button.pack(fill=tk.X, pady=(0, 5))
        
        self.skip_button = ttk.Button(button_frame, text="⏭ Skip", command=self.skip_image)
        self.skip_button.pack(fill=tk.X, pady=(0, 5))
        
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
        
        # Load first image
        self.load_current_image()
        self.update_stats_display()
    
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
        self.display_scale = scale
        self.display_image = rgb_image.copy()
        
        # Convert to PIL and Tk
        # CRITICAL: Keep both PIL and PhotoImage references to prevent garbage collection
        self.pil_image = Image.fromarray(rgb_image)
        self.photo = ImageTk.PhotoImage(self.pil_image)
        self.photo.image = self.pil_image  # Keep extra reference to prevent GC
        self.image_label.config(image=self.photo)
        
        # Update info
        self.filename_label.config(text=image_path.name)
        self.progress_label.config(text=f"Image {self.current_index + 1} of {len(self.image_files)}")
        self.progress_bar['value'] = self.current_index
        
        # Reset selection
        self.start_x = self.start_y = self.end_x = self.end_y = None
        self.selection_label.config(text="No region selected", foreground='red')
        self.label_entry.delete(0, tk.END)
        self.label_entry.focus()
    
    def on_mouse_down(self, event):
        """Mouse button pressed - start selection"""
        self.start_x = event.x
        self.start_y = event.y
        self.selecting = True
    
    def on_mouse_drag(self, event):
        """Mouse dragged - update selection"""
        if self.selecting:
            self.end_x = event.x
            self.end_y = event.y
            self.draw_selection()
    
    def on_mouse_up(self, event):
        """Mouse button released - finish selection"""
        if self.selecting:
            self.end_x = event.x
            self.end_y = event.y
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
        """Draw selection rectangle on image"""
        if self.start_x is None or self.end_x is None:
            return
        
        # Redraw image
        display_copy = self.display_image.copy()
        
        # Draw rectangle
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)
        
        cv2.rectangle(display_copy, (x1, y1), (x2, y2), (255, 0, 0), 2)
        
        # Convert and display
        pil_image = Image.fromarray(display_copy)
        self.photo = ImageTk.PhotoImage(pil_image)
        self.image_label.config(image=self.photo)
    
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
            # Save stats
            stats_file = self.output_folder / "labeling_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
            
            self.root.destroy()
    
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
