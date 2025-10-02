"""
Logging system for AI Page Reordering Automation System
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

class Logger:
    """Enhanced logging system with multiple output options"""
    
    def __init__(self, name: str = "PageReorder", log_file: Optional[str] = None, 
                 console_level: int = logging.INFO, file_level: int = logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(file_level)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        """Log debug message"""
        self.logger.debug(message)
    
    def warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message"""
        self.logger.critical(message)
    
    def progress(self, message: str, current: int, total: int) -> None:
        """Log progress message with percentage"""
        percentage = (current / total) * 100 if total > 0 else 0
        self.info(f"[{percentage:.1f}%] {message} ({current}/{total})")
    
    def step(self, step_name: str, details: str = "") -> None:
        """Log processing step"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        if details:
            self.info(f"🔄 [{timestamp}] {step_name}: {details}")
        else:
            self.info(f"🔄 [{timestamp}] {step_name}")
    
    def success(self, message: str) -> None:
        """Log success message"""
        self.info(f"✅ {message}")
    
    def failure(self, message: str) -> None:
        """Log failure message"""
        self.error(f"❌ {message}")
    
    def confidence_log(self, operation: str, confidence: float, threshold: float) -> None:
        """Log confidence-related information"""
        status = "✅ PASS" if confidence >= threshold else "⚠️  REVIEW"
        self.info(f"{status} {operation}: {confidence:.1f}% confidence (threshold: {threshold:.1f}%)")

class ProcessLogger:
    """Context manager for logging process steps"""
    
    def __init__(self, logger: Logger, process_name: str):
        self.logger = logger
        self.process_name = process_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.step(f"Starting {self.process_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time
        if exc_type is None:
            self.logger.success(f"Completed {self.process_name} in {duration.total_seconds():.2f}s")
        else:
            self.logger.failure(f"Failed {self.process_name} after {duration.total_seconds():.2f}s: {exc_val}")

# Create default logger instance
def create_logger(log_file: Optional[str] = None, verbose: bool = False) -> Logger:
    """Create logger instance with optional file output"""
    console_level = logging.DEBUG if verbose else logging.INFO
    return Logger(log_file=log_file, console_level=console_level)

# Default logger instance
logger = create_logger()
