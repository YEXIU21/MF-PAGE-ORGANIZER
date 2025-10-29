"""
Continuous Learning
Automatically adds uncertain pages to training data
Model improves over time with user corrections
"""

import cv2
from pathlib import Path
import json
import time

class ContinuousLearner:
    """Manages continuous learning from user corrections"""
    
    def __init__(self, training_dir="ml_training/continuous_training"):
        self.training_dir = Path(training_dir)
        self.corners_dir = self.training_dir / "corners"
        self.corners_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats_file = self.training_dir / "stats.json"
        self.stats = self._load_stats()
    
    def _load_stats(self):
        """Load learning statistics"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'total_added': 0,
            'labels': {},
            'last_retrain': None
        }
    
    def _save_stats(self):
        """Save learning statistics"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save learning stats: {e}")
    
    def add_training_example(self, image_path, corners, label):
        """
        Add new training example from user confirmation
        
        Args:
            image_path: Path to full page image
            corners: Dict of corner images {name: numpy_array}
            label: Correct page number (string)
        
        Returns:
            True if added successfully
        """
        # Try all corners and save the best ones
        added = False
        
        for corner_name, corner_img in corners.items():
            if corner_img is None or corner_img.size == 0:
                continue
            
            try:
                # Create class directory
                class_dir = self.corners_dir / str(label)
                class_dir.mkdir(exist_ok=True)
                
                # Save corner image
                timestamp = str(int(time.time() * 1000))
                filename = f"{label}_{corner_name}_{timestamp}.jpg"
                save_path = class_dir / filename
                
                # Resize to 200x200 (standard training size)
                corner_resized = cv2.resize(corner_img, (200, 200))
                cv2.imwrite(str(save_path), corner_resized)
                
                added = True
                
            except Exception as e:
                print(f"Warning: Could not save corner {corner_name}: {e}")
        
        if added:
            # Update stats
            self.stats['total_added'] += 1
            if label not in self.stats['labels']:
                self.stats['labels'][label] = 0
            self.stats['labels'][label] += 1
            
            self._save_stats()
        
        return added
    
    def should_retrain(self, threshold=20):
        """
        Check if we have enough new examples to retrain
        
        Args:
            threshold: Number of new examples needed
        
        Returns:
            True if should retrain
        """
        return self.stats['total_added'] >= threshold
    
    def get_stats(self):
        """Get current learning statistics"""
        return self.stats.copy()
    
    def reset_counter(self):
        """Reset the added counter (after retraining)"""
        self.stats['total_added'] = 0
        self.stats['last_retrain'] = time.strftime('%Y-%m-%d %H:%M:%S')
        self._save_stats()


# Singleton instance
_learner = None

def get_learner():
    """Get singleton continuous learner"""
    global _learner
    if _learner is None:
        _learner = ContinuousLearner()
    return _learner

def add_to_training(image_path, corners, label):
    """
    Add example to training data
    
    Args:
        image_path: Path to page image
        corners: Dict of corner images
        label: Correct page number
    
    Returns:
        True if added successfully
    """
    learner = get_learner()
    return learner.add_training_example(image_path, corners, label)

def should_retrain():
    """Check if should trigger retraining"""
    learner = get_learner()
    return learner.should_retrain()

def get_learning_stats():
    """Get current learning stats"""
    learner = get_learner()
    return learner.get_stats()


if __name__ == "__main__":
    # Test the learner
    learner = get_learner()
    stats = learner.get_stats()
    
    print("Continuous Learning Stats:")
    print(f"  Total examples added: {stats['total_added']}")
    print(f"  Unique labels: {len(stats['labels'])}")
    print(f"  Labels: {list(stats['labels'].keys())[:10]}")
    
    if learner.should_retrain():
        print("\n✅ Ready to retrain! (20+ new examples)")
    else:
        print(f"\n📊 Need {20 - stats['total_added']} more examples for retraining")
