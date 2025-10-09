"""
Prepare PaddleOCR models before building EXE
Downloads and caches all required models
"""
import sys
from pathlib import Path

print("=" * 70)
print("PADDLEOCR MODEL PREPARATION")
print("=" * 70)

# Check if PaddleOCR is installed
try:
    import paddleocr
    print(f"✓ PaddleOCR installed: {paddleocr.__version__}")
except ImportError:
    print("✗ PaddleOCR not installed!")
    print("  Run: pip install -r requirements.txt")
    sys.exit(1)

# Check if models cache exists
paddle_cache = Path.home() / '.paddleocr'
print(f"\nChecking cache: {paddle_cache}")

if paddle_cache.exists():
    items = list(paddle_cache.rglob('*'))
    file_count = sum(1 for item in items if item.is_file())
    print(f"✓ Cache exists with {file_count} files")
    
    # Show some cache contents
    model_files = [f for f in paddle_cache.rglob('*.pdparams')]
    print(f"  Found {len(model_files)} model files (.pdparams)")
    
    if len(model_files) == 0:
        print("  ⚠️  No model files found - initializing PaddleOCR...")
        needs_init = True
    else:
        print("  ✓ Models already downloaded")
        needs_init = False
else:
    print("✗ Cache does NOT exist")
    print("  Initializing PaddleOCR to download models...")
    needs_init = True

# Initialize PaddleOCR if needed (downloads models)
if needs_init:
    print("\n" + "=" * 70)
    print("DOWNLOADING MODELS (This may take a few minutes)")
    print("=" * 70)
    
    try:
        from paddleocr import PaddleOCR
        print("\nInitializing OCR (English)...")
        ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=True)
        print("\n✓ Models downloaded successfully!")
        
        # Verify cache now exists
        if paddle_cache.exists():
            items = list(paddle_cache.rglob('*'))
            file_count = sum(1 for item in items if item.is_file())
            print(f"✓ Cache now has {file_count} files")
        
    except Exception as e:
        print(f"\n✗ Failed to initialize PaddleOCR: {e}")
        print("\n  This will cause OCR to fail in the built EXE!")
        sys.exit(1)

print("\n" + "=" * 70)
print("✅ PADDLEOCR MODELS READY FOR BUILD")
print("=" * 70)
print("\nYou can now run:")
print("  - python build_exe.py")
print("  - python build_exe_with_splash.py")
print("\nThe built EXE will include all PaddleOCR models.")
