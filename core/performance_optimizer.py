"""
Performance Optimizer - Adaptive processing based on system resources
Automatically adjusts workers, batch sizes, and settings based on available RAM
"""

import psutil
import multiprocessing
from typing import Dict, Tuple

class PerformanceOptimizer:
    """Automatically optimize processing based on system resources"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.cpu_count = multiprocessing.cpu_count()
        
    def get_optimal_settings(self) -> Dict:
        """Get optimal processing settings based on available resources"""
        # Get system resources
        available_ram_gb = psutil.virtual_memory().available / (1024**3)
        total_ram_gb = psutil.virtual_memory().total / (1024**3)
        cpu_cores = self.cpu_count
        
        # Determine optimal workers and batch size
        workers, batch_size, mode = self._calculate_optimal_workers(available_ram_gb, cpu_cores)
        
        settings = {
            'workers': workers,
            'batch_size': batch_size,
            'mode': mode,
            'available_ram_gb': available_ram_gb,
            'total_ram_gb': total_ram_gb,
            'cpu_cores': cpu_cores,
            'memory_check_interval': self._get_memory_check_interval(available_ram_gb),
            'enable_image_optimization': available_ram_gb < 6,  # Optimize if < 6GB
            'aggressive_gc': available_ram_gb < 4  # Aggressive cleanup if < 4GB
        }
        
        if self.logger:
            self.logger.info(f"🚀 Performance Mode: {mode}")
            self.logger.info(f"💾 Available RAM: {available_ram_gb:.1f}GB / {total_ram_gb:.1f}GB")
            self.logger.info(f"🔧 Workers: {workers} | Batch Size: {batch_size}")
        
        return settings
    
    def _calculate_optimal_workers(self, available_ram_gb: float, cpu_cores: int) -> Tuple[int, int, str]:
        """Calculate optimal number of workers based on RAM and CPU
        
        Supports extreme systems: 2GB-1TB RAM, 1-1000 CPU cores
        """
        
        # Ultra-low RAM (< 2GB available)
        if available_ram_gb < 2:
            return 1, 10, "Ultra Safe Mode (Very Low RAM)"
        
        # Very low RAM (2-3GB available)
        elif available_ram_gb < 3:
            return 1, 25, "Safe Mode (Low RAM)"
        
        # Low RAM (3-4GB available)
        elif available_ram_gb < 4:
            return 1, 50, "Sequential Mode (4GB RAM)"
        
        # Medium-Low RAM (4-6GB available)
        elif available_ram_gb < 6:
            workers = min(2, cpu_cores)
            return workers, 50, f"Balanced Mode ({workers} workers)"
        
        # Medium RAM (6-8GB available)
        elif available_ram_gb < 8:
            workers = min(2, cpu_cores)
            return workers, 75, f"Parallel Mode ({workers} workers)"
        
        # Good RAM (8-12GB available)
        elif available_ram_gb < 12:
            workers = min(4, cpu_cores)
            return workers, 100, f"Fast Parallel Mode ({workers} workers)"
        
        # High RAM (12-16GB available)
        elif available_ram_gb < 16:
            workers = min(6, cpu_cores)
            return workers, 150, f"High Performance Mode ({workers} workers)"
        
        # Very High RAM (16-32GB available)
        elif available_ram_gb < 32:
            workers = min(8, cpu_cores)
            return workers, 200, f"Very High Performance ({workers} workers)"
        
        # Extreme RAM (32-64GB available)
        elif available_ram_gb < 64:
            workers = min(16, cpu_cores)
            return workers, 300, f"Extreme Performance ({workers} workers)"
        
        # Server RAM (64-128GB available)
        elif available_ram_gb < 128:
            workers = min(32, cpu_cores)
            return workers, 500, f"Server Performance ({workers} workers)"
        
        # Workstation RAM (128-256GB available)
        elif available_ram_gb < 256:
            workers = min(64, cpu_cores)
            return workers, 800, f"Workstation Performance ({workers} workers)"
        
        # Datacenter RAM (256-512GB available)
        elif available_ram_gb < 512:
            workers = min(128, cpu_cores)
            return workers, 1000, f"Datacenter Performance ({workers} workers)"
        
        # Supercomputer RAM (512GB-1TB+ available)
        else:
            # For 1TB+ systems, use up to 80% of CPU cores (leave 20% for system)
            workers = min(int(cpu_cores * 0.8), 1000)  # Cap at 1000 workers max
            batch_size = min(2000, available_ram_gb // 2)  # ~2MB per page estimate
            return workers, int(batch_size), f"Supercomputer Mode ({workers} workers)"
    
    def _calculate_memory_workers(self) -> int:
        """Calculate workers based on available RAM"""
        # EasyOCR uses ~1-2GB per worker
        # Conservative estimate: 2.5GB per worker
        if self.available_memory_gb < 4:
            return 1  # Low RAM
        elif self.available_memory_gb < 8:
            return 2  # 4-8GB RAM
        elif self.available_memory_gb < 12:
            return 3  # 8-12GB RAM
        elif self.available_memory_gb < 16:
            return 4  # 12-16GB RAM
        elif self.available_memory_gb < 32:
            return 8  # 16-32GB RAM
        elif self.available_memory_gb < 64:
            return 16  # 32-64GB RAM
        elif self.available_memory_gb < 128:
            return 32  # 64-128GB RAM
        else:
            # For extreme RAM (128GB+), calculate based on 2.5GB per worker
            return min(64, int(self.available_memory_gb / 2.5))
    def _get_memory_check_interval(self, available_ram_gb: float) -> int:
        """Get how often to check memory based on available RAM"""
        if available_ram_gb < 2:
            return 5  # Check every 5 pages
        elif available_ram_gb < 4:
            return 10  # Check every 10 pages
        elif available_ram_gb < 8:
            return 25  # Check every 25 pages
        else:
            return 50  # Check every 50 pages
    
    def should_enable_feature(self, feature: str, available_ram_gb: float = None) -> bool:
        """Determine if a feature should be enabled based on available resources"""
        if available_ram_gb is None:
            available_ram_gb = psutil.virtual_memory().available / (1024**3)
        # Feature memory requirements
        feature_requirements = {
            'preprocessing': 4.0,  # Needs 4GB+
            'auto_crop': 3.0,      # Needs 3GB+
            'clean_circles': 3.0,  # Needs 3GB+
            'parallel_processing': 6.0  # Needs 6GB+ for safety
        }
        
        required_ram = feature_requirements.get(feature, 2.0)
        return available_ram_gb >= required_ram
    
    def get_estimated_time(self, page_count: int, workers: int, features_enabled: Dict) -> float:
        """Estimate processing time in minutes"""
        # Base time per page (seconds)
        base_time_per_page = 5.0  # OCR baseline
        
        # Adjust for features
        if features_enabled.get('preprocessing', False):
            base_time_per_page += 2.0
        if features_enabled.get('auto_crop', False):
            base_time_per_page += 0.5
        if features_enabled.get('clean_circles', False):
            base_time_per_page += 1.0
        
        # Calculate total time
        total_seconds = (page_count * base_time_per_page) / workers
        
        # Add overhead (10%)
        total_seconds *= 1.1
        
        # Convert to minutes
        return total_seconds / 60
    
    def monitor_performance(self) -> Dict:
        """Get current system performance metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'available_ram_gb': psutil.virtual_memory().available / (1024**3),
            'disk_io': psutil.disk_io_counters() if hasattr(psutil, 'disk_io_counters') else None
        }

