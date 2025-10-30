"""
Smart Cache System - AI-like memory for processed images
Remembers processed pages and skips re-processing identical images
"""

import hashlib
import pickle
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import os

class SmartCache:
    """Intelligent caching system that remembers processed images"""
    
    def __init__(self, logger=None, output_dir=None):
        self.logger = logger
        
        # IMPROVED: Store cache in output directory for easy access/deletion
        if output_dir:
            self.cache_dir = Path(output_dir) / "_cache"
            if self.logger:
                self.logger.info(f"Cache stored in output folder: {self.cache_dir}")
        else:
            # Fallback to old behavior if no output dir provided
            self.cache_dir = Path("cache")
            
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache index for fast lookups
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.total_time_saved = 0
    
    def _load_cache_index(self) -> Dict:
        """Load cache index from disk"""
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}  # Cache index missing or corrupted
        return {}
    
    def _save_cache_index(self):
        """Save cache index to disk"""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to save cache index: {e}")
    
    def get_image_hash(self, image_path: str) -> str:
        """Generate unique hash for an image file"""
        try:
            # Use file path + size + modification time for fast hashing
            stat = os.stat(image_path)
            hash_input = f"{image_path}_{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(hash_input.encode()).hexdigest()
        except OSError:
            # Fallback: hash the file path only if stat fails
            return hashlib.md5(image_path.encode()).hexdigest()
    
    def get_cached_result(self, image_hash: str, result_type: str = 'ocr') -> Optional[Any]:
        """Retrieve cached result if available"""
        cache_key = f"{image_hash}_{result_type}"
        
        if cache_key in self.cache_index:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        result = pickle.load(f)
                    
                    self.hits += 1
                    
                    if self.logger:
                        self.logger.debug(f"✅ Cache HIT: {result_type} for {image_hash[:8]}")
                    
                    return result
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Failed to load cache: {e}")
        
        self.misses += 1
        return None
    
    def save_result(self, image_hash: str, result: Any, result_type: str = 'ocr', processing_time: float = 0):
        """Save processing result to cache"""
        cache_key = f"{image_hash}_{result_type}"
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            
            # Update index
            self.cache_index[cache_key] = {
                'created': datetime.now().isoformat(),
                'type': result_type,
                'processing_time': processing_time,
                'file': str(cache_file)
            }
            
            self._save_cache_index()
            
            if self.logger:
                self.logger.debug(f"💾 Cached: {result_type} for {image_hash[:8]}")
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to save cache: {e}")
    
    def get_statistics(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'total_cached_items': len(self.cache_index),
            'time_saved_seconds': self.total_time_saved
        }
    
    def clear_old_cache(self, days: int = 30):
        """Clear cache entries older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        removed = 0
        
        for cache_key, info in list(self.cache_index.items()):
            try:
                created = datetime.fromisoformat(info['created'])
                if created < cutoff_date:
                    # Remove cache file
                    cache_file = Path(info['file'])
                    if cache_file.exists():
                        cache_file.unlink()
                    
                    # Remove from index
                    del self.cache_index[cache_key]
                    removed += 1
            except (OSError, KeyError):
                pass  # File already removed or key doesn't exist
        
        if removed > 0:
            self._save_cache_index()
            if self.logger:
                self.logger.info(f"🧹 Cleared {removed} old cache entries")
        
        return removed
    
    def get_cache_size(self) -> float:
        """Get total cache size in MB"""
        total_size = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            total_size += cache_file.stat().st_size
        return total_size / (1024 * 1024)  # Convert to MB

