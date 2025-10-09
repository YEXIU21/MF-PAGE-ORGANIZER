"""
PyInstaller hook for PaddleOCR model cache
Ensures PaddleOCR models are included in the frozen EXE
"""
from PyInstaller.utils.hooks import collect_data_files, get_package_paths
from pathlib import Path
import os

# Collect all data files from paddleocr package
datas = collect_data_files('paddleocr')

# Also include the user's PaddleOCR cache if it exists
paddle_cache = Path.home() / '.paddleocr'
if paddle_cache.exists():
    print(f"[HOOK] Found PaddleOCR cache: {paddle_cache}")
    # Add all model files from cache
    for item in paddle_cache.rglob('*'):
        if item.is_file():
            rel_path = item.relative_to(paddle_cache.parent)
            # Add to datas: (source, destination_in_exe)
            datas.append((str(item), str(rel_path.parent)))
            print(f"[HOOK] Adding: {item.name}")
else:
    print("[HOOK] WARNING: PaddleOCR cache not found!")
    print("[HOOK] Models need to be downloaded before building EXE")
    print("[HOOK] Run: python -c 'from paddleocr import PaddleOCR; PaddleOCR()'")
