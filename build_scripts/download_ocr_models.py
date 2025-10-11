"""
Download PaddleOCR models before building EXE
This ensures models are available for bundling
"""
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

print("=" * 70)
print("📥 DOWNLOADING PADDLEOCR MODELS")
print("=" * 70)
print("\nThis will initialize PaddleOCR and download required models...")
print("This may take 5-10 minutes depending on your internet speed.\n")

try:
    from paddleocr import PaddleOCR
    
    print("✅ PaddleOCR imported successfully")
    print("📥 Initializing PaddleOCR (this triggers model download)...\n")
    
    # Initialize PaddleOCR - this will download models if not present
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    
    print("\n✅ PaddleOCR initialized successfully!")
    print("✅ Models downloaded to: %USERPROFILE%\\.paddleocr")
    
    # Verify models exist
    paddleocr_home = Path.home() / '.paddleocr'
    if paddleocr_home.exists():
        model_files = list(paddleocr_home.rglob('*.pdparams'))
        print(f"✅ Found {len(model_files)} model files")
        
        # Show model directories
        model_dirs = set(f.parent.name for f in model_files)
        print(f"✅ Model types: {', '.join(sorted(model_dirs))}")
    else:
        print("⚠️  Warning: .paddleocr folder not found")
    
    print("\n" + "=" * 70)
    print("✅ MODELS READY FOR BUNDLING")
    print("=" * 70)
    print("\nYou can now build the EXE with:")
    print("  python build_scripts/build_exe_onefile.py")
    
except ImportError as e:
    print(f"\n❌ Error: PaddleOCR not installed: {e}")
    print("Install with: pip install paddleocr")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error during initialization: {e}")
    print("\nThis might be normal on first run as models download.")
    print("Please try running the script again.")
    sys.exit(1)
