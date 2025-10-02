"""
AI Learning System - Learns from processing patterns and adapts
Intelligent system that improves over time based on usage patterns
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict

class AILearningSystem:
    """AI-like learning system that adapts based on processing history"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.learning_file = Path("cache/ai_learning.json")
        self.learning_file.parent.mkdir(exist_ok=True)
        
        # Load learning data
        self.learning_data = self._load_learning_data()
        
    def _load_learning_data(self) -> Dict:
        """Load AI learning data"""
        if self.learning_file.exists():
            try:
                with open(self.learning_file, 'r') as f:
                    return json.load(f)
            except:
                return self._create_default_learning_data()
        return self._create_default_learning_data()
    
    def _create_default_learning_data(self) -> Dict:
        """Create default learning data structure"""
        return {
            'processing_history': [],
            'document_patterns': {},
            'optimal_settings': {},
            'user_preferences': {},
            'performance_metrics': {
                'total_documents': 0,
                'total_pages': 0,
                'total_time_seconds': 0,
                'average_time_per_page': 0
            },
            'feature_usage': {
                'preprocessing': 0,
                'auto_rotate': 0,
                'auto_crop': 0,
                'clean_circles': 0,
                'blank_removal': 0,
                'compression': 0
            },
            'error_patterns': [],
            'success_rate': 100.0
        }
    
    def _save_learning_data(self):
        """Save learning data to disk"""
        try:
            with open(self.learning_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to save learning data: {e}")
    
    def record_processing(self, document_info: Dict, settings: Dict, result: Dict):
        """Record processing session for learning"""
        session = {
            'timestamp': datetime.now().isoformat(),
            'document': {
                'page_count': document_info.get('page_count', 0),
                'file_type': document_info.get('file_type', 'unknown'),
                'size_mb': document_info.get('size_mb', 0)
            },
            'settings': settings,
            'result': {
                'success': result.get('success', False),
                'processing_time': result.get('processing_time', 0),
                'pages_processed': result.get('pages_processed', 0)
            }
        }
        
        # Add to history
        self.learning_data['processing_history'].append(session)
        
        # Keep only last 100 sessions
        if len(self.learning_data['processing_history']) > 100:
            self.learning_data['processing_history'] = self.learning_data['processing_history'][-100:]
        
        # Update metrics
        self._update_metrics(session)
        
        # Update feature usage
        self._update_feature_usage(settings)
        
        # Learn patterns
        self._learn_from_session(session)
        
        # Save
        self._save_learning_data()
    
    def _update_metrics(self, session: Dict):
        """Update performance metrics"""
        metrics = self.learning_data['performance_metrics']
        
        if session['result']['success']:
            metrics['total_documents'] += 1
            metrics['total_pages'] += session['document']['page_count']
            metrics['total_time_seconds'] += session['result']['processing_time']
            
            if metrics['total_pages'] > 0:
                metrics['average_time_per_page'] = metrics['total_time_seconds'] / metrics['total_pages']
    
    def _update_feature_usage(self, settings: Dict):
        """Track which features users actually use"""
        usage = self.learning_data['feature_usage']
        
        if settings.get('preprocessing', False):
            usage['preprocessing'] += 1
        if settings.get('auto_rotate', False):
            usage['auto_rotate'] += 1
        if settings.get('auto_crop', False):
            usage['auto_crop'] += 1
        if settings.get('clean_circles', False):
            usage['clean_circles'] += 1
        if settings.get('blank_removal', 'none') != 'none':
            usage['blank_removal'] += 1
        if settings.get('compression', False):
            usage['compression'] += 1
    
    def _learn_from_session(self, session: Dict):
        """Learn patterns from processing session"""
        page_count = session['document']['page_count']
        
        # Categorize document size
        if page_count < 50:
            category = 'small'
        elif page_count < 200:
            category = 'medium'
        elif page_count < 500:
            category = 'large'
        else:
            category = 'very_large'
        
        # Store optimal settings for this category
        if session['result']['success']:
            if category not in self.learning_data['document_patterns']:
                self.learning_data['document_patterns'][category] = {
                    'count': 0,
                    'avg_time': 0,
                    'best_settings': {}
                }
            
            pattern = self.learning_data['document_patterns'][category]
            pattern['count'] += 1
            
            # Update average time
            current_time = session['result']['processing_time']
            pattern['avg_time'] = (pattern['avg_time'] * (pattern['count'] - 1) + current_time) / pattern['count']
    
    def get_recommended_settings(self, page_count: int, available_ram_gb: float) -> Dict:
        """AI recommendation for optimal settings based on learning"""
        # Categorize document
        if page_count < 50:
            category = 'small'
        elif page_count < 200:
            category = 'medium'
        elif page_count < 500:
            category = 'large'
        else:
            category = 'very_large'
        
        # Get learned patterns
        pattern = self.learning_data['document_patterns'].get(category, {})
        
        # AI-based recommendations
        recommendations = {
            'preprocessing': False,  # Default OFF for speed
            'auto_rotate': True,     # Usually helpful
            'auto_crop': False,      # Optional
            'clean_circles': False,  # Optional
            'blank_removal': 'start_end',  # Usually good
            'compression': page_count > 100,  # For larger docs
            'fast_mode': page_count > 200,  # For large docs
            'reasoning': []
        }
        
        # Learn from feature usage patterns
        usage = self.learning_data['feature_usage']
        total_sessions = max(sum(usage.values()), 1)
        
        # If users frequently enable preprocessing, recommend it
        if usage.get('preprocessing', 0) / total_sessions > 0.5:
            recommendations['preprocessing'] = True
            recommendations['reasoning'].append("Users often enable preprocessing")
        
        # RAM-based adjustments
        if available_ram_gb < 4:
            recommendations['preprocessing'] = False
            recommendations['fast_mode'] = True
            recommendations['reasoning'].append("Low RAM detected, optimizing for safety")
        
        # Document size adjustments
        if page_count > 400:
            recommendations['fast_mode'] = True
            recommendations['reasoning'].append("Large document, enabling fast mode")
        
        if self.logger:
            self.logger.info(f"🤖 AI Recommendations for {page_count} pages:")
            for reason in recommendations['reasoning']:
                self.logger.info(f"   • {reason}")
        
        return recommendations
    
    def detect_duplicate_pages(self, pages: List) -> Dict:
        """Detect if pages are duplicates (already processed)"""
        duplicates = {}
        seen_hashes = {}
        
        for i, page in enumerate(pages):
            page_hash = self.get_image_hash(str(page.file_path))
            
            if page_hash in seen_hashes:
                duplicates[i] = seen_hashes[page_hash]
                if self.logger:
                    self.logger.info(f"🔍 Duplicate detected: Page {i+1} same as Page {seen_hashes[page_hash]+1}")
            else:
                seen_hashes[page_hash] = i
        
        return duplicates
    
    def get_cache_statistics(self) -> str:
        """Get human-readable cache statistics"""
        stats = []
        stats.append(f"📊 AI Learning Statistics:")
        stats.append(f"   • Total documents processed: {self.learning_data['performance_metrics']['total_documents']}")
        stats.append(f"   • Total pages processed: {self.learning_data['performance_metrics']['total_pages']}")
        
        avg_time = self.learning_data['performance_metrics'].get('average_time_per_page', 0)
        if avg_time > 0:
            stats.append(f"   • Average time per page: {avg_time:.2f}s")
        
        # Cache hit rate
        total_requests = self.hits + self.misses
        if total_requests > 0:
            hit_rate = (self.hits / total_requests) * 100
            stats.append(f"   • Cache hit rate: {hit_rate:.1f}%")
            stats.append(f"   • Time saved by caching: {self.total_time_saved:.1f}s")
        
        # Feature usage insights
        usage = self.learning_data['feature_usage']
        most_used = max(usage, key=usage.get) if usage else None
        if most_used:
            stats.append(f"   • Most used feature: {most_used}")
        
        return "\n".join(stats)
    
    def predict_processing_time(self, page_count: int, settings: Dict) -> float:
        """AI prediction of processing time based on historical data"""
        # Get average time per page from history
        avg_time_per_page = self.learning_data['performance_metrics'].get('average_time_per_page', 5.0)
        
        # Adjust based on settings
        multiplier = 1.0
        if settings.get('preprocessing', False):
            multiplier *= 1.4
        if settings.get('auto_crop', False):
            multiplier *= 1.1
        if settings.get('clean_circles', False):
            multiplier *= 1.2
        
        # Calculate estimated time
        estimated_seconds = page_count * avg_time_per_page * multiplier
        
        return estimated_seconds / 60  # Return in minutes
    
    def suggest_optimization(self, page_count: int, available_ram_gb: float) -> List[str]:
        """AI suggestions for optimization"""
        suggestions = []
        
        # Based on document size
        if page_count > 400:
            suggestions.append("💡 Large document detected. Enable 'Fast mode' for 2-3x speed improvement")
            suggestions.append("💡 Consider disabling 'Image quality enhancement' to save time")
        
        # Based on RAM
        if available_ram_gb < 4:
            suggestions.append("⚠️ Low RAM detected. Disable 'Image quality enhancement' to prevent errors")
            suggestions.append("💡 Enable 'Fast mode' for better memory management")
        
        # Based on learning
        usage = self.learning_data['feature_usage']
        total = max(sum(usage.values()), 1)
        
        # If users rarely use preprocessing, suggest disabling it
        if usage.get('preprocessing', 0) / total < 0.2:
            suggestions.append("💡 Most users disable preprocessing for faster results")
        
        # If users frequently enable compression
        if usage.get('compression', 0) / total > 0.6:
            suggestions.append("💡 Consider enabling 'PDF compression' (popular feature)")
        
        return suggestions

