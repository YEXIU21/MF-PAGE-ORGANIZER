"""
Start Training Data Collection
Simple script to begin collecting corner images for ML training
"""

from ml_training.enable_data_collection import start_collection, stop_collection
import sys

def main():
    print("=" * 70)
    print("TRAINING DATA COLLECTION - STARTING")
    print("=" * 70)
    print()
    
    # Start collection with confidence filtering
    print("📊 Enabling training data collection...")
    print("   ✓ Only saving high-confidence detections (>90%)")
    print("   ✓ Corner images will be saved to: ml_training/training_data/")
    print()
    
    collector = start_collection()
    
    print("=" * 70)
    print("✅ DATA COLLECTION ACTIVE!")
    print("=" * 70)
    print()
    print("NEXT STEPS:")
    print()
    print("1. Process your book normally:")
    print("   python main.py")
    print()
    print("   OR with command line:")
    print("   python main.py --input \"C:\\path\\to\\book\" --output \"C:\\output\"")
    print()
    print("2. After processing completes, stop collection:")
    print("   python stop_training_collection.py")
    print()
    print("3. Review the collection report to see what was collected")
    print()
    print("=" * 70)
    print("⚡ COLLECTION IS RUNNING IN BACKGROUND")
    print("   Process your books normally - data collects automatically!")
    print("=" * 70)

if __name__ == "__main__":
    main()
