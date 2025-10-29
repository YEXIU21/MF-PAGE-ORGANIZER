"""
Training Progress Dialog
Shows training progress with live updates
"""

import tkinter as tk
from tkinter import ttk
import threading

class TrainingProgressDialog:
    """Dialog showing model training progress"""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = None
        self.progress_var = None
        self.status_var = None
        self.epoch_var = None
        self.cancelled = False
        
    def create_dialog(self):
        """Create the progress dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Training AI Model...")
        self.dialog.geometry("500x300")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (250)
        y = (self.dialog.winfo_screenheight() // 2) - (150)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="🚀 Training AI Model",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Status message
        self.status_var = tk.StringVar(value="Preparing training data...")
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=('Arial', 10)
        )
        status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate'
        )
        progress_bar.pack(pady=(0, 20))
        
        # Epoch info
        self.epoch_var = tk.StringVar(value="Epoch 0/30")
        epoch_label = ttk.Label(
            main_frame,
            textvariable=self.epoch_var,
            font=('Arial', 9)
        )
        epoch_label.pack()
        
        # Info text
        info_label = ttk.Label(
            main_frame,
            text="This may take 5-10 minutes.\nPlease be patient...",
            font=('Arial', 9),
            foreground='gray'
        )
        info_label.pack(pady=(20, 0))
        
        # Cancel button (disabled for now - training can't be safely cancelled)
        # cancel_button = ttk.Button(
        #     main_frame,
        #     text="Cancel",
        #     command=self.on_cancel,
        #     state='disabled'
        # )
        # cancel_button.pack(pady=(20, 0))
        
    def update_progress(self, percentage: float, status: str = None, epoch: str = None):
        """Update progress display"""
        if self.dialog and self.dialog.winfo_exists():
            self.progress_var.set(percentage)
            
            if status:
                self.status_var.set(status)
            
            if epoch:
                self.epoch_var.set(epoch)
            
            self.dialog.update()
    
    def on_cancel(self):
        """User wants to cancel"""
        # For now, don't allow cancellation
        # Training should complete
        pass
    
    def close(self):
        """Close the dialog"""
        if self.dialog:
            self.dialog.destroy()
    
    def show(self):
        """Show the dialog"""
        self.create_dialog()


# Simple callback-based trainer wrapper
class TrainingCallbacks:
    """Callbacks for training progress updates"""
    
    def __init__(self, progress_dialog: TrainingProgressDialog, total_epochs: int = 30):
        self.dialog = progress_dialog
        self.total_epochs = total_epochs
        self.current_epoch = 0
    
    def on_epoch_begin(self, epoch, logs=None):
        """Called at the beginning of each epoch"""
        self.current_epoch = epoch + 1
        percentage = (self.current_epoch / self.total_epochs) * 100
        
        self.dialog.update_progress(
            percentage=percentage,
            status=f"Training... Epoch {self.current_epoch}/{self.total_epochs}",
            epoch=f"Epoch {self.current_epoch}/{self.total_epochs}"
        )
    
    def on_epoch_end(self, epoch, logs=None):
        """Called at the end of each epoch"""
        acc = logs.get('accuracy', 0) if logs else 0
        val_acc = logs.get('val_accuracy', 0) if logs else 0
        
        self.dialog.update_progress(
            percentage=((epoch + 1) / self.total_epochs) * 100,
            status=f"Epoch {epoch + 1}/{self.total_epochs} - Acc: {acc:.2%}, Val: {val_acc:.2%}"
        )


def show_training_progress(parent, trainer_func, *args, **kwargs):
    """
    Show training progress while running training function
    
    Args:
        parent: Parent window
        trainer_func: Training function to run
        *args, **kwargs: Arguments for trainer function
    
    Returns:
        Result of trainer_func
    """
    dialog = TrainingProgressDialog(parent)
    dialog.show()
    
    result = [None]  # Use list to allow modification in thread
    exception = [None]
    
    def run_training():
        try:
            # Run training
            result[0] = trainer_func(*args, **kwargs)
            
            # Show completion
            dialog.update_progress(
                100,
                "Training complete! ✓",
                ""
            )
            
            # Wait a moment before closing
            import time
            time.sleep(1)
            
        except Exception as e:
            exception[0] = e
            dialog.update_progress(
                0,
                f"Error: {str(e)}",
                ""
            )
        
        finally:
            dialog.close()
    
    # Run in thread
    thread = threading.Thread(target=run_training, daemon=True)
    thread.start()
    
    # Wait for completion
    thread.join()
    
    if exception[0]:
        raise exception[0]
    
    return result[0]


if __name__ == "__main__":
    # Test the dialog
    import time
    
    root = tk.Tk()
    root.withdraw()
    
    def test_training():
        """Simulate training"""
        dialog = TrainingProgressDialog(root)
        dialog.show()
        
        # Simulate epochs
        for epoch in range(30):
            time.sleep(0.1)  # Simulate work
            percentage = ((epoch + 1) / 30) * 100
            dialog.update_progress(
                percentage,
                f"Training epoch {epoch + 1}/30...",
                f"Epoch {epoch + 1}/30"
            )
        
        dialog.update_progress(100, "Complete!", "Done")
        time.sleep(1)
        dialog.close()
    
    test_training()
    
    print("Test complete")
