"""Check PaddleOCR installation and models"""
from pathlib import Path
import os

# Check PaddleOCR installation
try:
    import paddleocr
    print(f"✓ PaddleOCR installed: {paddleocr.__version__}")
    print(f"  Location: {paddleocr.__file__}")
except ImportError as e:
    print(f"✗ PaddleOCR not installed: {e}")
    exit(1)

# Check Paddle
try:
    import paddle
    print(f"✓ PaddlePaddle installed: {paddle.__version__}")
except ImportError as e:
    print(f"✗ PaddlePaddle not installed: {e}")

# Check models cache
home = Path.home()
paddle_cache = home / '.paddleocr'

print(f"\nPaddleOCR cache directory: {paddle_cache}")
if paddle_cache.exists():
    print("✓ Cache exists!")
    
    # List subdirectories
    items = list(paddle_cache.rglob('*'))
    print(f"  Total items: {len(items)}")
    
    # Show first 20 items
    print("\n  Contents (first 20):")
    for item in items[:20]:
        rel_path = item.relative_to(paddle_cache)
        item_type = "[DIR]" if item.is_dir() else "[FILE]"
        size = f"({item.stat().st_size // 1024} KB)" if item.is_file() else ""
        print(f"    {item_type} {rel_path} {size}")
else:
    print("✗ Cache does NOT exist - Models not downloaded!")
    print("\n  This means PaddleOCR has never been run successfully")
    print("  Models need to be downloaded before building EXE")

# Check if we can initialize PaddleOCR
print("\nTrying to initialize PaddleOCR...")
try:
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    print("✓ PaddleOCR initialized successfully!")
    print("  Models have been downloaded")
except Exception as e:
    print(f"✗ Failed to initialize PaddleOCR: {e}")
    print("  This is the problem with the EXE!")
