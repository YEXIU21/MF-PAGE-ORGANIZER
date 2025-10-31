"""
Quick Model Trainer for Page Number Detection
Trains a lightweight CNN model from manually labeled data
Optimized for fast training (5-10 minutes on CPU)
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TensorFlow logging

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
from pathlib import Path
import json
import time
from typing import Tuple, Dict
import cv2

class QuickTrainer:
    """Fast trainer for page number detection model"""
    
    def __init__(self, data_dir: str = "ml_training/manual_training_data"):
        self.data_dir = Path(data_dir) / "corners_digits"  # Use digit-level reorganized data
        self.model = None
        self.class_names = []
        self.history = None
        
    def load_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Load and prepare training data"""
        print("📂 Loading training data...")
        
        # Get all class folders
        class_folders = [f for f in self.data_dir.iterdir() if f.is_dir()]
        self.class_names = sorted([f.name for f in class_folders])
        
        print(f"   Found {len(self.class_names)} classes: {', '.join(self.class_names[:10])}...")
        
        # Load images and labels
        images = []
        labels = []
        
        for class_idx, class_name in enumerate(self.class_names):
            class_folder = self.data_dir / class_name
            image_files = list(class_folder.glob("*.jpg")) + list(class_folder.glob("*.png"))
            
            for img_path in image_files:
                img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    # Resize to 100x100 for speed (smaller = faster training)
                    img = cv2.resize(img, (100, 100))
                    # Normalize
                    img = img.astype('float32') / 255.0
                    images.append(img)
                    labels.append(class_idx)
        
        print(f"   Loaded {len(images)} images")
        
        # Convert to numpy arrays
        X = np.array(images)
        y = np.array(labels)
        
        # Add channel dimension
        X = np.expand_dims(X, -1)
        
        # Check class distribution
        from collections import Counter
        class_counts = Counter(y)
        min_samples = min(class_counts.values())
        
        # Split into train/validation (80/20)
        from sklearn.model_selection import train_test_split
        
        # Only use stratify if all classes have at least 2 samples
        if min_samples >= 2:
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        else:
            # Some classes have only 1 sample - can't use stratify
            print(f"   ⚠ Warning: Some classes have only {min_samples} sample(s)")
            print(f"   Skipping stratified split (validation split may be unbalanced)")
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        
        print(f"   Train set: {len(X_train)} images")
        print(f"   Validation set: {len(X_val)} images")
        
        return X_train, X_val, y_train, y_val
    
    def build_model(self, num_classes: int):
        """Build lightweight CNN model"""
        print("\n🏗️  Building model...")
        
        model = keras.Sequential([
            # Input: 100x100x1 grayscale image
            layers.Input(shape=(100, 100, 1)),
            
            # Conv block 1
            layers.Conv2D(32, (3, 3), activation='relu'),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            
            # Conv block 2
            layers.Conv2D(64, (3, 3), activation='relu'),
            layers.MaxPooling2D((2, 2)),
            layers.Dropout(0.25),
            
            # Conv block 3
            layers.Conv2D(64, (3, 3), activation='relu'),
            layers.Dropout(0.25),
            
            # Dense layers
            layers.Flatten(),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # Print model summary
        total_params = model.count_params()
        print(f"   Total parameters: {total_params:,}")
        print(f"   Estimated model size: ~{total_params * 4 / 1024 / 1024:.1f}MB")
        
        self.model = model
        return model
    
    def create_data_augmentation(self):
        """Create data augmentation to improve training"""
        return keras.Sequential([
            layers.RandomRotation(0.1),  # ±10 degrees (increased)
            layers.RandomZoom(0.15),  # ±15% zoom (increased)
            layers.RandomTranslation(0.1, 0.1),  # ±10% shift (new)
            layers.RandomContrast(0.2),  # ±20% contrast (increased)
            layers.RandomBrightness(0.2)  # ±20% brightness (new)
        ])
    
    def train(self, X_train, X_val, y_train, y_val, epochs: int = 30):
        """Train the model"""
        print("\n🚀 Starting training...")
        print(f"   Epochs: {epochs}")
        print(f"   Batch size: 16")
        print()
        
        # Calculate class weights to handle imbalance
        unique, counts = np.unique(y_train, return_counts=True)
        total = len(y_train)
        class_weights = {i: total / (len(unique) * count) for i, count in zip(unique, counts)}
        
        print(f"📊 Class distribution:")
        for cls_idx, count in zip(unique, counts):
            cls_name = self.class_names[cls_idx]
            weight = class_weights[cls_idx]
            print(f"   {cls_name:15}: {count:3} samples (weight: {weight:.2f})")
        print()
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=7,  # Increased patience for better convergence
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                verbose=1
            )
        ]
        
        # Create augmentation model
        augmentation = self.create_data_augmentation()
        
        # Create training dataset with augmentation
        train_ds = tf.data.Dataset.from_tensor_slices((X_train, y_train))
        train_ds = train_ds.shuffle(1000)
        train_ds = train_ds.batch(16)
        train_ds = train_ds.map(lambda x, y: (augmentation(x, training=True), y))
        train_ds = train_ds.prefetch(tf.data.AUTOTUNE)
        
        # Create validation dataset (no augmentation)
        val_ds = tf.data.Dataset.from_tensor_slices((X_val, y_val))
        val_ds = val_ds.batch(16)
        val_ds = val_ds.prefetch(tf.data.AUTOTUNE)
        
        # Train
        start_time = time.time()
        
        self.history = self.model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=epochs,
            class_weight=class_weights,  # Apply class weighting
            callbacks=callbacks,
            verbose=1
        )
        
        training_time = time.time() - start_time
        
        print(f"\n✅ Training complete in {training_time/60:.1f} minutes")
        
        # Final accuracy
        train_acc = self.history.history['accuracy'][-1]
        val_acc = self.history.history['val_accuracy'][-1]
        
        print(f"   Final training accuracy: {train_acc*100:.1f}%")
        print(f"   Final validation accuracy: {val_acc*100:.1f}%")
        
        return self.history
    
    def save_model(self, output_dir: str = "ml_training/models"):
        """Save trained model and metadata"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n💾 Saving model...")
        
        # Save model
        model_path = output_path / "page_detector.h5"
        self.model.save(model_path)
        print(f"   Model saved: {model_path}")
        
        # Save class names
        classes_path = output_path / "class_names.json"
        with open(classes_path, 'w') as f:
            json.dump(self.class_names, f)
        print(f"   Classes saved: {classes_path}")
        
        # Save training info
        info = {
            'num_classes': len(self.class_names),
            'input_shape': [100, 100, 1],
            'trained_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'final_train_acc': float(self.history.history['accuracy'][-1]),
            'final_val_acc': float(self.history.history['val_accuracy'][-1])
        }
        
        info_path = output_path / "model_info.json"
        with open(info_path, 'w') as f:
            json.dump(info, f, indent=2)
        print(f"   Info saved: {info_path}")
        
        print(f"\n✅ Model ready for use!")
        print(f"   Location: {output_path}")
        
        return model_path
    
    def run_full_training(self, epochs: int = 30):
        """Complete training pipeline"""
        print("=" * 70)
        print("QUICK MODEL TRAINER - Page Number Detection")
        print("=" * 70)
        
        # Load data
        X_train, X_val, y_train, y_val = self.load_data()
        
        # Build model
        num_classes = len(self.class_names)
        self.build_model(num_classes)
        
        # Train
        self.train(X_train, X_val, y_train, y_val, epochs)
        
        # Save
        model_path = self.save_model()
        
        print("\n" + "=" * 70)
        print("✅ TRAINING COMPLETE!")
        print("=" * 70)
        print(f"\nYour model is ready at: {model_path}")
        print(f"Classes trained: {len(self.class_names)}")
        print(f"Validation accuracy: {self.history.history['val_accuracy'][-1]*100:.1f}%")
        print("\nNext steps:")
        print("  1. Test the model")
        print("  2. Integrate into main system")
        print("  3. Process books at lightning speed!")
        print("=" * 70)
        
        return model_path


def main():
    """Run training from command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train page number detection model')
    parser.add_argument('--data', default='ml_training/manual_training_data',
                       help='Path to training data directory')
    parser.add_argument('--epochs', type=int, default=30,
                       help='Number of training epochs')
    parser.add_argument('--output', default='ml_training/models',
                       help='Output directory for trained model')
    
    args = parser.parse_args()
    
    # Check if data exists
    data_path = Path(args.data) / "corners_digits"  # Check for reorganized digit-level data
    if not data_path.exists():
        print(f"❌ Error: Training data not found at {data_path}")
        print("\nPlease run reorganization first: python ml_training/reorganize_to_digits.py --live")
        print("  python ml_training/interactive_labeler.py <image_folder>")
        return
    
    # Check minimum examples
    class_folders = [f for f in data_path.iterdir() if f.is_dir()]
    total_images = sum(len(list(f.glob("*.jpg")) + list(f.glob("*.png"))) for f in class_folders)
    
    if total_images < 20:
        print(f"❌ Error: Not enough training data ({total_images} images)")
        print("\nMinimum required: 20 images")
        print("Recommended: 50+ images")
        return
    
    # Train
    trainer = QuickTrainer(args.data)
    trainer.run_full_training(epochs=args.epochs)


if __name__ == "__main__":
    main()
