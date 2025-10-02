"""
Learning memory system for AI Page Reordering Automation System
Stores user corrections and preferences for future improvements
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter

from utils.config import config

class MemorySystem:
    """Manages learning from user corrections and preferences"""
    
    def __init__(self, logger, memory_dir: Optional[str] = None):
        self.logger = logger
        self.memory_dir = Path(memory_dir) if memory_dir else Path(config.get('paths.memory_dir', 'data/memory'))
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory files
        self.corrections_file = self.memory_dir / 'user_corrections.json'
        self.patterns_file = self.memory_dir / 'learned_patterns.json'
        self.preferences_file = self.memory_dir / 'user_preferences.json'
        self.statistics_file = self.memory_dir / 'usage_statistics.json'
        
        # Load existing memory
        self.corrections = self._load_corrections()
        self.patterns = self._load_patterns()
        self.preferences = self._load_preferences()
        self.statistics = self._load_statistics()
    
    def record_correction(self, original_position: int, corrected_position: int, 
                         page_name: str, reason: str, confidence: float) -> None:
        """Record a user correction for learning"""
        if not config.get('default_settings.enable_memory', True):
            return
        
        correction = {
            'timestamp': datetime.now().isoformat(),
            'page_name': page_name,
            'original_position': original_position,
            'corrected_position': corrected_position,
            'position_change': corrected_position - original_position,
            'reason': reason,
            'original_confidence': confidence,
            'correction_type': self._classify_correction(original_position, corrected_position)
        }
        
        self.corrections.append(correction)
        self._save_corrections()
        
        # Update learned patterns
        self._update_patterns_from_correction(correction)
        
        # Update statistics
        self._update_statistics('corrections', 1)
        
        self.logger.debug(f"Recorded correction: {page_name} {original_position} → {corrected_position}")
    
    def record_numbering_pattern(self, pattern_type: str, pattern_details: Dict[str, Any],
                               success_rate: float) -> None:
        """Record a successful numbering pattern for future use"""
        pattern_key = f"{pattern_type}_{pattern_details.get('scheme', 'unknown')}"
        
        if pattern_key not in self.patterns['numbering_patterns']:
            self.patterns['numbering_patterns'][pattern_key] = {
                'pattern_type': pattern_type,
                'details': pattern_details,
                'success_count': 0,
                'total_count': 0,
                'success_rate': 0.0,
                'first_seen': datetime.now().isoformat(),
                'last_used': datetime.now().isoformat()
            }
        
        pattern = self.patterns['numbering_patterns'][pattern_key]
        pattern['total_count'] += 1
        if success_rate > 0.7:  # Consider successful if > 70%
            pattern['success_count'] += 1
        pattern['success_rate'] = pattern['success_count'] / pattern['total_count']
        pattern['last_used'] = datetime.now().isoformat()
        
        self._save_patterns()
    
    def record_preprocessing_effectiveness(self, preprocessing_options: Dict[str, bool],
                                        ocr_improvement: float) -> None:
        """Record effectiveness of preprocessing options"""
        key = '_'.join([k for k, v in preprocessing_options.items() if v])
        
        if key not in self.patterns['preprocessing_effectiveness']:
            self.patterns['preprocessing_effectiveness'][key] = {
                'options': preprocessing_options,
                'improvement_scores': [],
                'average_improvement': 0.0,
                'usage_count': 0
            }
        
        pattern = self.patterns['preprocessing_effectiveness'][key]
        pattern['improvement_scores'].append(ocr_improvement)
        pattern['average_improvement'] = sum(pattern['improvement_scores']) / len(pattern['improvement_scores'])
        pattern['usage_count'] += 1
        
        self._save_patterns()
    
    def get_suggested_position(self, page_name: str, detected_position: int,
                             confidence: float) -> Optional[int]:
        """Get suggested position based on learned patterns"""
        if not self.corrections:
            return None
        
        # Look for similar corrections
        similar_corrections = []
        
        for correction in self.corrections:
            # Check for similar page names or patterns
            if self._pages_are_similar(page_name, correction['page_name']):
                similar_corrections.append(correction)
            # Check for similar position patterns
            elif abs(correction['original_position'] - detected_position) <= 2:
                similar_corrections.append(correction)
        
        if not similar_corrections:
            return None
        
        # Analyze correction patterns
        position_adjustments = [c['position_change'] for c in similar_corrections]
        
        if len(position_adjustments) >= 3:  # Need multiple examples
            # Use most common adjustment
            adjustment_counts = Counter(position_adjustments)
            most_common_adjustment = adjustment_counts.most_common(1)[0][0]
            
            suggested_position = detected_position + most_common_adjustment
            
            self.logger.debug(f"Memory suggests position {suggested_position} for {page_name} "
                            f"(adjustment: {most_common_adjustment})")
            
            return suggested_position
        
        return None
    
    def get_preferred_preprocessing(self) -> Dict[str, bool]:
        """Get user's preferred preprocessing options based on history"""
        if not self.patterns['preprocessing_effectiveness']:
            return {}
        
        # Find most effective preprocessing combination
        best_combo = None
        best_score = -1
        
        for key, data in self.patterns['preprocessing_effectiveness'].items():
            if data['usage_count'] >= 3 and data['average_improvement'] > best_score:
                best_score = data['average_improvement']
                best_combo = data['options']
        
        return best_combo if best_combo else {}
    
    def get_numbering_pattern_preferences(self) -> List[str]:
        """Get preferred numbering pattern types based on success rate"""
        if not self.patterns['numbering_patterns']:
            return []
        
        # Sort patterns by success rate and usage
        sorted_patterns = sorted(
            self.patterns['numbering_patterns'].items(),
            key=lambda x: (x[1]['success_rate'], x[1]['total_count']),
            reverse=True
        )
        
        # Return top patterns that have been used at least 3 times
        preferred = [pattern[1]['pattern_type'] for pattern in sorted_patterns[:5]
                    if pattern[1]['total_count'] >= 3]
        
        return preferred
    
    def update_user_preference(self, preference_key: str, value: Any) -> None:
        """Update user preference"""
        self.preferences[preference_key] = {
            'value': value,
            'updated': datetime.now().isoformat()
        }
        self._save_preferences()
    
    def get_user_preference(self, preference_key: str, default: Any = None) -> Any:
        """Get user preference"""
        if preference_key in self.preferences:
            return self.preferences[preference_key]['value']
        return default
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        stats = {
            'total_corrections': len(self.corrections),
            'learned_patterns': len(self.patterns['numbering_patterns']),
            'preprocessing_combinations_tried': len(self.patterns['preprocessing_effectiveness']),
            'user_preferences': len(self.preferences),
            'memory_age_days': (datetime.now() - datetime.fromisoformat(
                self.statistics.get('first_use', datetime.now().isoformat())
            )).days,
            'most_common_corrections': self._get_most_common_corrections(),
            'success_rates': self._calculate_success_rates()
        }
        
        return stats
    
    def clear_memory(self, memory_type: str = 'all') -> None:
        """Clear memory data"""
        if memory_type in ['all', 'corrections']:
            self.corrections = []
            self._save_corrections()
        
        if memory_type in ['all', 'patterns']:
            self.patterns = {'numbering_patterns': {}, 'preprocessing_effectiveness': {}}
            self._save_patterns()
        
        if memory_type in ['all', 'preferences']:
            self.preferences = {}
            self._save_preferences()
        
        self.logger.info(f"Cleared {memory_type} memory data")
    
    def export_memory(self, export_path: str) -> bool:
        """Export memory data to file"""
        try:
            export_data = {
                'corrections': self.corrections,
                'patterns': self.patterns,
                'preferences': self.preferences,
                'statistics': self.statistics,
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Memory data exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export memory: {e}")
            return False
    
    def import_memory(self, import_path: str, merge: bool = True) -> bool:
        """Import memory data from file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if merge:
                # Merge with existing data
                self.corrections.extend(import_data.get('corrections', []))
                
                for pattern_type, patterns in import_data.get('patterns', {}).items():
                    if pattern_type not in self.patterns:
                        self.patterns[pattern_type] = {}
                    self.patterns[pattern_type].update(patterns)
                
                self.preferences.update(import_data.get('preferences', {}))
            else:
                # Replace existing data
                self.corrections = import_data.get('corrections', [])
                self.patterns = import_data.get('patterns', {'numbering_patterns': {}, 'preprocessing_effectiveness': {}})
                self.preferences = import_data.get('preferences', {})
            
            # Save imported data
            self._save_corrections()
            self._save_patterns()
            self._save_preferences()
            
            self.logger.info(f"Memory data imported from {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import memory: {e}")
            return False
    
    def _load_corrections(self) -> List[Dict[str, Any]]:
        """Load user corrections from file"""
        if self.corrections_file.exists():
            try:
                with open(self.corrections_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load corrections: {e}")
        return []
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load learned patterns from file"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load patterns: {e}")
        return {'numbering_patterns': {}, 'preprocessing_effectiveness': {}}
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load user preferences from file"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load preferences: {e}")
        return {}
    
    def _load_statistics(self) -> Dict[str, Any]:
        """Load usage statistics from file"""
        if self.statistics_file.exists():
            try:
                with open(self.statistics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load statistics: {e}")
        
        # Initialize with current timestamp
        return {
            'first_use': datetime.now().isoformat(),
            'total_runs': 0,
            'corrections': 0,
            'successful_runs': 0
        }
    
    def _save_corrections(self) -> None:
        """Save corrections to file"""
        try:
            with open(self.corrections_file, 'w', encoding='utf-8') as f:
                json.dump(self.corrections, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save corrections: {e}")
    
    def _save_patterns(self) -> None:
        """Save patterns to file"""
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save patterns: {e}")
    
    def _save_preferences(self) -> None:
        """Save preferences to file"""
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save preferences: {e}")
    
    def _save_statistics(self) -> None:
        """Save statistics to file"""
        try:
            with open(self.statistics_file, 'w', encoding='utf-8') as f:
                json.dump(self.statistics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")
    
    def _classify_correction(self, original: int, corrected: int) -> str:
        """Classify the type of correction"""
        diff = corrected - original
        
        if diff == 0:
            return 'no_change'
        elif abs(diff) == 1:
            return 'minor_adjustment'
        elif abs(diff) <= 5:
            return 'moderate_adjustment'
        else:
            return 'major_adjustment'
    
    def _pages_are_similar(self, page1: str, page2: str) -> bool:
        """Check if two page names are similar"""
        # Simple similarity check based on common prefixes/suffixes
        page1_base = Path(page1).stem.lower()
        page2_base = Path(page2).stem.lower()
        
        # Check for common patterns
        if page1_base.startswith(page2_base[:5]) or page2_base.startswith(page1_base[:5]):
            return True
        
        # Check for similar numbering patterns
        import re
        nums1 = re.findall(r'\d+', page1_base)
        nums2 = re.findall(r'\d+', page2_base)
        
        if nums1 and nums2:
            # Similar if numbers are close
            try:
                return abs(int(nums1[0]) - int(nums2[0])) <= 3
            except:
                pass
        
        return False
    
    def _update_patterns_from_correction(self, correction: Dict[str, Any]) -> None:
        """Update learned patterns based on correction"""
        correction_type = correction['correction_type']
        
        if correction_type not in self.patterns:
            self.patterns[correction_type] = {'count': 0, 'examples': []}
        
        self.patterns[correction_type]['count'] += 1
        self.patterns[correction_type]['examples'].append({
            'change': correction['position_change'],
            'confidence': correction['original_confidence'],
            'timestamp': correction['timestamp']
        })
        
        # Keep only recent examples (last 50)
        if len(self.patterns[correction_type]['examples']) > 50:
            self.patterns[correction_type]['examples'] = \
                self.patterns[correction_type]['examples'][-50:]
    
    def _update_statistics(self, stat_key: str, increment: int = 1) -> None:
        """Update usage statistics"""
        if stat_key not in self.statistics:
            self.statistics[stat_key] = 0
        
        self.statistics[stat_key] += increment
        self.statistics['last_update'] = datetime.now().isoformat()
        self._save_statistics()
    
    def _get_most_common_corrections(self) -> List[Dict[str, Any]]:
        """Get most common correction patterns"""
        if not self.corrections:
            return []
        
        # Group by position change
        changes = Counter(c['position_change'] for c in self.corrections)
        return [{'change': change, 'count': count} 
                for change, count in changes.most_common(5)]
    
    def _calculate_success_rates(self) -> Dict[str, float]:
        """Calculate success rates for different patterns"""
        rates = {}
        
        for pattern_type, patterns in self.patterns.get('numbering_patterns', {}).items():
            if patterns.get('total_count', 0) > 0:
                rates[pattern_type] = patterns.get('success_rate', 0.0)
        
        return rates

# Global memory instance
memory_system = None

def get_memory_system(logger) -> MemorySystem:
    """Get global memory system instance"""
    global memory_system
    if memory_system is None:
        memory_system = MemorySystem(logger)
    return memory_system
