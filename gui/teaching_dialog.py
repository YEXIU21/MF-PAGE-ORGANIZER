"""
Teaching Mode Dialog
Shown to first-time users to introduce the teaching process
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

class TeachingDialog:
    """Dialog for introducing teaching mode to users"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = None  # 'teach', 'skip', or None (cancelled)
        
        # Create dialog first
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Welcome to Page Automation!")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Create dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Welcome message
        welcome_label = ttk.Label(
            main_frame,
            text="🤖 Welcome to Page Automation!",
            font=('Arial', 16, 'bold')
        )
        welcome_label.pack(pady=(0, 20))
        
        # Info text
        info_text = tk.Text(
            main_frame,
            wrap=tk.WORD,
            height=15,
            font=('Arial', 10)
        )
        info_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        info_content = """
No trained model found. Let's teach the AI to recognize page numbers!

WHY TEACH THE AI?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• First time: Takes 15-20 minutes to teach
• After that: Process books 10x faster forever!
• Customized: Learns YOUR specific book styles
• Accurate: 97-99% accuracy after teaching

HOW IT WORKS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. You'll see sample pages
2. Click & drag to select page numbers
3. Type the number you see
4. Repeat for 20-50 pages
5. AI trains for 5-10 minutes
6. Done! Ready for ultra-fast processing

WHAT TO EXPECT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current speed: 5-8 seconds per page
After teaching: 0.5 seconds per page
        
That's 10x faster! Worth the 20 minutes setup.

SKIP TEACHING?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You can skip and use the slower PaddleOCR method.
But we recommend teaching the AI first!
        """
        
        info_text.insert('1.0', info_content)
        info_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        teach_button = ttk.Button(
            button_frame,
            text="🎓 Teach the AI Now (Recommended)",
            command=self.on_teach
            # Removed style='Accent.TButton' - caused pyimage1 error
        )
        teach_button.pack(fill=tk.X, pady=(0, 10))
        
        skip_button = ttk.Button(
            button_frame,
            text="⏭ Skip (Use Slower Mode)",
            command=self.on_skip
        )
        skip_button.pack(fill=tk.X)
        
        # Make teach button default
        teach_button.focus()
    
    def on_teach(self):
        """User chose to teach"""
        self.result = 'teach'
        self.dialog.destroy()
    
    def on_skip(self):
        """User chose to skip"""
        if messagebox.askyesno(
            "Skip Teaching?",
            "Are you sure? Teaching the AI will make processing much faster.\n\n"
            "You can always teach it later from the Settings menu.",
            parent=self.dialog
        ):
            self.result = 'skip'
            self.dialog.destroy()
    
    def show(self):
        """Show dialog and return result"""
        self.dialog.wait_window()
        return self.result


def show_teaching_dialog(parent=None) -> str:
    """
    Show teaching dialog
    
    Returns:
        'teach', 'skip', or None
    """
    if parent is None:
        # Create temporary root if needed
        root = tk.Tk()
        root.withdraw()
        
        # Configure theme for standalone root to avoid Accent.TButton errors
        style = ttk.Style(root)
        try:
            style.theme_use('clam')
        except tk.TclError:
            style.theme_use('default')
        
        parent = root
    
    dialog = TeachingDialog(parent)
    result = dialog.show()
    
    return result


if __name__ == "__main__":
    # Test the dialog
    root = tk.Tk()
    root.withdraw()
    
    result = show_teaching_dialog(root)
    
    print(f"User choice: {result}")
    
    root.destroy()
