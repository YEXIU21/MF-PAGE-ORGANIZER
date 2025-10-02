"""
Configuration management for AI Page Reordering Automation System
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    """Manages configuration settings for the application"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Return default configuration if file doesn't exist
                return self._get_default_config()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}. Using default configuration.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "default_settings": {
                "ocr_confidence_threshold": 85,
                "enable_preprocessing": True,
                "enable_memory": True,
                "output_format": "pdf",
                "temp_cleanup": True
            },
            "preprocessing": {
                "denoise": True,
                "deskew": True,
                "contrast_enhance": False,
                "watermark_reduction": False
            },
            "ocr": {
                "language": "eng",
                "engine_mode": 3,
                "page_segmentation": 6,
                "enable_handwriting": False
            },
            "numbering": {
                "detect_arabic": True,
                "detect_roman": True,
                "detect_hybrid": True,
                "detect_hierarchical": True,
                "priority_order": ["page", "chapter", "section"]
            },
            "content_analysis": {
                "text_continuity_weight": 0.4,
                "heading_sequence_weight": 0.3,
                "reference_weight": 0.3,
                "min_confidence_for_auto_order": 90
            },
            "output": {
                "create_pdf": True,
                "create_images": False,
                "create_metadata_log": True,
                "preserve_original_quality": True
            },
            "paths": {
                "temp_dir": "data/temp",
                "memory_dir": "data/memory",
                "models_dir": "data/models"
            }
        }
    
    def get(self, key_path: str, default=None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('ocr.confidence_threshold')
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        Example: config.set('ocr.confidence_threshold', 90)
        """
        keys = key_path.split('.')
        config_ref = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        # Set the final value
        config_ref[keys[-1]] = value
    
    def save(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving config: {e}")
    
    def reset_to_default(self) -> None:
        """Reset configuration to default values"""
        self.config = self._get_default_config()
        self.save()
    
    def update_from_args(self, args) -> None:
        """Update configuration from command line arguments"""
        if hasattr(args, 'denoise') and args.denoise is not None:
            self.set('preprocessing.denoise', args.denoise.lower() == 'on')
        
        if hasattr(args, 'ocr') and args.ocr is not None:
            self.set('ocr.enabled', args.ocr.lower() == 'on')
        
        if hasattr(args, 'confidence') and args.confidence is not None:
            self.set('default_settings.ocr_confidence_threshold', int(args.confidence))
        
        if hasattr(args, 'output_format') and args.output_format:
            self.set('default_settings.output_format', args.output_format)

# Global configuration instance
config = ConfigManager()
