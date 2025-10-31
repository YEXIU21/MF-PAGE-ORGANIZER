"""
Transfer Learning Trainer for Page Number Detection
Uses pretrained MobileNetV2 as feature extractor
Much better accuracy than training from scratch
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
import numpy as np
from pathlib import Path
import json
import time
from typing import Tuple
import cv2

class TransferTrainer:
    """Transfer learning trainer using MobileNetV2"""
    
    def __init__(self, data_dir: str = "ml_training/manual_training_data"):
        self.data_dir = Path(data_dir) / "corners_digits"
        self.model = None
        self.base_model = None
        self.class_names = []
        self.history = None
        
    def load_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Load and prepare training data"""
        print("📂 Loading training data...")
        
        # Get all class folders
        class_folders = [f for f in self.data_dir.iterdir() if f.is_dir()]
        self.class_names = sorted([f.name for f in class_folders])
        
        X, y = [], []
        
        for class_idx, class_name in enumerate(self.class_names):
            class_folder = self.data_dir / class_name
            images = list(class_folder.glob("*.jpg")) + list(class_folder.glob("*.png"))
            
            print(f"   {class_name:15}: {len(images)} images")
            
            for img_path in images:
                # Load and preprocess for MobileNetV2 (224x224, RGB, scaled to [-1,1])
                img = cv2.imread(str(img_path))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (224, 224))  # MobileNetV2 input size
                img = img.astype('float32')
                img = tf.keras.applications.mobilenet_v2.preprocess_input(img)
                
                X.append(img)
                y.append(class_idx)
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"\n✅ Loaded {len(X)} images across {len(self.class_names)} classes")
        
        # Split into train/validation
        from sklearn.model_selection import train_test_split
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"   Train set: {len(X_train)} images")
        print(f"   Validation set: {len(X_val)} images")
        
        return X_train, X_val, y_train, y_val
    
    def build_model(self, num_classes: int):
        """Build transfer learning model with MobileNetV2"""
        print("\n🏗️  Building transfer learning model...")
        print("   Base: MobileNetV2 (pretrained on ImageNet)")
        
        # Load pretrained MobileNetV2 (without top classification layer)
        self.base_model = MobileNetV2(
            input_shape=(224, 224, 3),
            include_top=False,
            weights='imagenet',
            pooling='avg'  # Global average pooling
        )
        
        # Freeze base model layers (use pretrained features)
        self.base_model.trainable = False
        
        # Build classification head
        inputs = keras.Input(shape=(224, 224, 3))
        
        # Base model (frozen)
        x = self.base_model(inputs, training=False)
        
        # Classification head (trainable)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(128, activation='relu')(x)
        x = layers.Dropout(0.3)(x)
        outputs = layers.Dense(num_classes, activation='softmax')(x)
        
        # Create model
        model = keras.Model(inputs, outputs)
        
        # Compile
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # Print summary
        trainable_params = sum([tf.size(var).numpy() for var in model.trainable_variables])
        total_params = sum([tf.size(var).numpy() for var in model.variables])
        
        print(f"   Trainable parameters: {trainable_params:,}")
        print(f"   Total parameters: {total_params:,}")
        print(f"   Frozen (pretrained): {total_params - trainable_params:,}")
        
        self.model = model
        return model
    
    def create_data_augmentation(self):
        """Create moderate data augmentation"""
        return keras.Sequential([
            layers.RandomRotation(0.05),  # ±5 degrees
            layers.RandomZoom(0.1),  # ±10%
            layers.RandomTranslation(0.05, 0.05),  # ±5%
            layers.RandomContrast(0.1),  # ±10%
        ])
    
    def train(self, X_train, X_val, y_train, y_val, epochs: int = 20):
        """Train the model"""
        print("\n🚀 Starting transfer learning training...")
        print(f"   Epochs: {epochs}")
        print(f"   Batch size: 32")
        print()
        
        # Calculate class weights
        unique, counts = np.unique(y_train, return_counts=True)
        total = len(y_train)
        class_weights = {i: total / (len(unique) * count) for i, count in zip(unique, counts)}
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=5,
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
        
        # Create augmentation
        augmentation = self.create_data_augmentation()
        
        # Create training dataset with augmentation
        train_ds = tf.data.Dataset.from_tensor_slices((X_train, y_train))
        train_ds = train_ds.shuffle(1000)
        train_ds = train_ds.batch(32)
        train_ds = train_ds.map(lambda x, y: (augmentation(x, training=True), y))
        train_ds = train_ds.prefetch(tf.data.AUTOTUNE)
        
        # Create validation dataset (no augmentation)
        val_ds = tf.data.Dataset.from_tensor_slices((X_val, y_val))
        val_ds = val_ds.batch(32)
        val_ds = val_ds.prefetch(tf.data.AUTOTUNE)
        
        # Train
        start_time = time.time()
        
        self.history = self.model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=epochs,
            class_weight=class_weights,
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
    
    def fine_tune(self, X_train, X_val, y_train, y_val, epochs: int = 10):
        """Fine-tune the model by unfreezing some base layers"""
        print("\n🔧 Fine-tuning model (unfreezing top layers)...")
        
        # Unfreeze the top layers of base model
        self.base_model.trainable = True
        
        # Freeze all layers except the last 30
        for layer in self.base_model.layers[:-30]:
            layer.trainable = False
        
        # Recompile with lower learning rate
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.0001),  # Lower LR
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=3,
                restore_best_weights=True,
                verbose=1
            )
        ]
        
        # Create datasets
        train_ds = tf.data.Dataset.from_tensor_slices((X_train, y_train))
        train_ds = train_ds.shuffle(1000).batch(32).prefetch(tf.data.AUTOTUNE)
        
        val_ds = tf.data.Dataset.from_tensor_slices((X_val, y_val))
        val_ds = val_ds.batch(32).prefetch(tf.data.AUTOTUNE)
        
        # Fine-tune
        start_time = time.time()
        
        history = self.model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=epochs,
            callbacks=callbacks,
            verbose=1
        )
        
        training_time = time.time() - start_time
        
        print(f"\n✅ Fine-tuning complete in {training_time/60:.1f} minutes")
        
        # Final accuracy
        val_acc = history.history['val_accuracy'][-1]
        print(f"   Final validation accuracy: {val_acc*100:.1f}%")
        
        return history
    
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
        
        # Save model info
        val_acc = self.history.history['val_accuracy'][-1]
        info = {
            'classes': len(self.class_names),
            'accuracy': val_acc * 100,
            'type': 'transfer_learning_mobilenetv2'
        }
        
        info_path = output_path / "model_info.json"
        with open(info_path, 'w') as f:
            json.dump(info, f, indent=2)
        print(f"   Info saved: {info_path}")
        
        print(f"\n✅ Model ready for use!")
        print(f"   Location: {output_path}")


def main():
    """Main training script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train page number detector using transfer learning')
    parser.add_argument('--data', default='ml_training/manual_training_data',
                       help='Path to training data directory')
    parser.add_argument('--epochs', type=int, default=20,
                       help='Number of training epochs')
    parser.add_argument('--fine-tune', type=int, default=10,
                       help='Number of fine-tuning epochs')
    parser.add_argument('--output', default='ml_training/models',
                       help='Output directory for trained model')
    
    args = parser.parse_args()
    
    # Check if data exists
    data_path = Path(args.data) / "corners_digits"
    if not data_path.exists():
        print(f"❌ Error: Training data not found at {data_path}")
        return
    
    # Create trainer
    trainer = TransferTrainer(args.data)
    
    # Load data
    X_train, X_val, y_train, y_val = trainer.load_data()
    
    # Build model
    model = trainer.build_model(len(trainer.class_names))
    
    # Train
    trainer.train(X_train, X_val, y_train, y_val, epochs=args.epochs)
    
    # Fine-tune
    if args.fine_tune > 0:
        trainer.fine_tune(X_train, X_val, y_train, y_val, epochs=args.fine_tune)
    
    # Save
    trainer.save_model(args.output)
    
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE!")
    print("="*70)
    print(f"\nYour model is ready at: {args.output}/page_detector.h5")
    print(f"Classes trained: {len(trainer.class_names)}")
    print(f"Validation accuracy: {trainer.history.history['val_accuracy'][-1]*100:.1f}%")
    print("\nNext steps:")
    print("  1. Test the model")
    print("  2. Integrate into main system")
    print("  3. Process books at lightning speed!")
    print("="*70)


if __name__ == "__main__":
    main()
