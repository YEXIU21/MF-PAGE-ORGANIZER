"""
Stop Training Data Collection
Stops collection and shows results
"""

from ml_training.enable_data_collection import stop_collection

def main():
    print("=" * 70)
    print("STOPPING TRAINING DATA COLLECTION")
    print("=" * 70)
    print()
    
    collector = stop_collection()
    
    if collector:
        print()
        print("=" * 70)
        print("WHAT'S NEXT?")
        print("=" * 70)
        print()
        print("1. Review collected data:")
        print("   - Location: ml_training/training_data/corners/")
        print("   - Report: ml_training/training_data/metadata/collection_report.txt")
        print()
        print("2. If you have 1000+ images:")
        print("   - Ready for Phase 2: Model Training!")
        print("   - Check ml_training/README.md for next steps")
        print()
        print("3. If you need more data:")
        print("   - Run: python start_training_collection.py")
        print("   - Process more books")
        print("   - Run: python stop_training_collection.py")
        print()
        print("=" * 70)
    else:
        print("\n⚠️ No active collection session found")
        print("   Make sure you ran: python start_training_collection.py")

if __name__ == "__main__":
    main()
