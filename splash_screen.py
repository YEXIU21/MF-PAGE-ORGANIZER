"""
Splash Screen for MF Page Organizer
Shows loading screen while application initializes
"""

import tkinter as tk
from tkinter import ttk
import threading
import time

class SplashScreen:
    """Display splash screen during application startup"""
    
    def __init__(self, parent=None):
        if parent is None:
            # Create root if no parent provided
            self.root = tk.Tk()
            self.is_root = True
        else:
            # Use Toplevel if parent provided
            self.root = tk.Toplevel(parent)
            self.is_root = False
        
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Splash dimensions
        splash_width = 500
        splash_height = 300
        
        # Center splash screen
        x = (screen_width - splash_width) // 2
        y = (screen_height - splash_height) // 2
        
        self.root.geometry(f"{splash_width}x{splash_height}+{x}+{y}")
        
        # Create main frame with border
        main_frame = tk.Frame(self.root, bg='#2c3e50', bd=2, relief='raised')
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="MF PAGE ORGANIZER",
            font=('Arial', 24, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=(40, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_frame,
            text="Smart Document Organizer",
            font=('Arial', 12),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Loading message
        self.loading_label = tk.Label(
            main_frame,
            text="Loading...",
            font=('Arial', 10),
            bg='#2c3e50',
            fg='#3498db'
        )
        self.loading_label.pack(pady=(20, 10))
        
        # Progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Splash.Horizontal.TProgressbar",
            troughcolor='#34495e',
            background='#3498db',
            bordercolor='#2c3e50',
            lightcolor='#3498db',
            darkcolor='#3498db'
        )
        
        self.progress = ttk.Progressbar(
            main_frame,
            style="Splash.Horizontal.TProgressbar",
            length=400,
            mode='indeterminate'
        )
        self.progress.pack(pady=(10, 20))
        self.progress.start(10)  # Start animation
        
        # Developer info
        developer_label = tk.Label(
            main_frame,
            text="Developed by Mark & Franzel",
            font=('Arial', 9, 'bold'),
            bg='#2c3e50',
            fg='#3498db'
        )
        developer_label.pack(side='bottom', pady=(0, 5))
        
        # Version info
        version_label = tk.Label(
            main_frame,
            text="Version 2.0 | 100% Accurate",
            font=('Arial', 8),
            bg='#2c3e50',
            fg='#95a5a6'
        )
        version_label.pack(side='bottom', pady=(0, 10))
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Initializing AI engine...",
            font=('Arial', 9, 'italic'),
            bg='#2c3e50',
            fg='#95a5a6'
        )
        self.status_label.pack(side='bottom', pady=(0, 5))
        
        self.root.update()
    
    def update_status(self, message):
        """Update status message"""
        self.status_label.config(text=message)
        self.root.update()
    
    def close(self):
        """Close splash screen"""
        try:
            self.progress.stop()
            if self.is_root:
                self.root.quit()  # Exit mainloop if this is root
            self.root.destroy()  # Destroy window
        except:
            pass
    
    def show(self):
        """Show splash screen"""
        self.root.update()

def show_splash_with_loading(callback, *args, **kwargs):
    """
    Show splash screen while loading application
    
    Args:
        callback: Function to call after splash (main app initialization)
        *args, **kwargs: Arguments to pass to callback
    """
    splash = SplashScreen()
    
    def load_app():
        """Load application in background"""
        try:
            # Show loading steps with proper timing (4 seconds total)
            time.sleep(0.8)
            splash.update_status("Loading OCR engine...")
            time.sleep(0.8)
            splash.update_status("Initializing AI models...")
            time.sleep(0.8)
            splash.update_status("Preparing interface...")
            time.sleep(0.8)
            splash.update_status("Almost ready...")
            time.sleep(0.8)
            # Total: 0.8 * 5 = 4.0 seconds ✅
            
            # Close splash - this will exit the mainloop
            splash.close()
                
        except Exception as e:
            splash.close()
            raise e
    
    # Start loading in background thread
    loading_thread = threading.Thread(target=load_app, daemon=True)
    loading_thread.start()
    
    # Show splash screen (blocks until closed)
    splash.root.mainloop()
    
    # After splash closes and mainloop exits, launch main application
    if callback:
        callback(*args, **kwargs)

if __name__ == '__main__':
    # Test splash screen
    def test_callback():
        print("Main application would start here")
    
    show_splash_with_loading(test_callback)
