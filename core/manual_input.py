"""
Manual Input Dialog
Shows page to user when ML is uncertain
User confirms or corrects the page number
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import numpy as np

def ask_user_for_number(image_path, best_guess=None, confidence=0):
    """
    Show page to user and ask for page number
    
    Args:
        image_path: Path to page image
        best_guess: ML's best guess (if any)
        confidence: ML's confidence (0-1)
    
    Returns:
        User's input or None if skipped
    """
    
    result = [None]
    
    def on_submit():
        user_input = entry.get().strip()
        if user_input:
            result[0] = user_input
        root.destroy()
    
    def on_skip():
        result[0] = None
        root.destroy()
    
    def on_use_guess():
        if best_guess:
            result[0] = best_guess
            root.destroy()
    
    # Create dialog
    root = tk.Tk()
    root.title("Confirm Page Number")
    
    # Calculate window size (80% of screen)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = int(screen_width * 0.6)
    window_height = int(screen_height * 0.8)
    root.geometry(f"{window_width}x{window_height}")
    
    # Main frame
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_text = "ML Model Not Confident" if best_guess else "ML Model Could Not Detect"
    ttk.Label(
        main_frame,
        text=title_text,
        font=('Arial', 16, 'bold')
    ).pack(pady=(0, 10))
    
    ttk.Label(
        main_frame,
        text="Please confirm the page number:",
        font=('Arial', 12)
    ).pack(pady=(0, 20))
    
    # Image display
    try:
        # Load and resize image
        img = cv2.imread(str(image_path))
        if img is not None:
            # Convert BGR to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Resize to fit display (max 800x800)
            h, w = img_rgb.shape[:2]
            max_size = min(window_width - 100, window_height - 300)
            
            if h > max_size or w > max_size:
                scale = min(max_size / h, max_size / w)
                new_h, new_w = int(h * scale), int(w * scale)
                img_rgb = cv2.resize(img_rgb, (new_w, new_h))
            
            # Convert to PhotoImage
            img_pil = Image.fromarray(img_rgb)
            photo = ImageTk.PhotoImage(img_pil)
            
            img_label = ttk.Label(main_frame, image=photo)
            img_label.image = photo  # Keep reference
            img_label.pack(pady=(0, 20))
    except Exception as e:
        ttk.Label(
            main_frame,
            text=f"Could not load image: {e}",
            foreground='red'
        ).pack()
    
    # ML's guess (if any)
    if best_guess:
        guess_frame = ttk.Frame(main_frame)
        guess_frame.pack(pady=(0, 10))
        
        ttk.Label(
            guess_frame,
            text=f"ML's guess: ",
            font=('Arial', 11)
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            guess_frame,
            text=f"{best_guess}",
            font=('Arial', 11, 'bold'),
            foreground='blue'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(
            guess_frame,
            text=f"(confidence: {confidence:.0%})",
            font=('Arial', 10),
            foreground='gray'
        ).pack(side=tk.LEFT)
    
    # Input frame
    input_frame = ttk.Frame(main_frame)
    input_frame.pack(pady=10)
    
    ttk.Label(
        input_frame,
        text="Page Number:",
        font=('Arial', 12, 'bold')
    ).pack(side=tk.LEFT, padx=(0, 10))
    
    entry = ttk.Entry(input_frame, font=('Arial', 14), width=15)
    entry.pack(side=tk.LEFT)
    
    if best_guess:
        entry.insert(0, best_guess)  # Pre-fill with guess
        entry.select_range(0, tk.END)
    
    entry.focus()
    entry.bind('<Return>', lambda e: on_submit())
    
    # Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=20)
    
    if best_guess:
        ttk.Button(
            button_frame,
            text=f"✓ Use '{best_guess}'",
            command=on_use_guess,
            width=15
        ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        button_frame,
        text="✓ Confirm",
        command=on_submit,
        width=12
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        button_frame,
        text="⏭ Skip Page",
        command=on_skip,
        width=12
    ).pack(side=tk.LEFT, padx=5)
    
    # Instructions
    ttk.Label(
        main_frame,
        text="Press Enter to confirm, or click Skip to leave page unnumbered",
        font=('Arial', 9),
        foreground='gray'
    ).pack(pady=(10, 0))
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (window_width // 2)
    y = (root.winfo_screenheight() // 2) - (window_height // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()
    
    return result[0]


if __name__ == "__main__":
    # Test the dialog
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        result = ask_user_for_number(image_path, best_guess="23", confidence=0.75)
        print(f"User input: {result}")
    else:
        print("Usage: python manual_input.py <image_path>")
